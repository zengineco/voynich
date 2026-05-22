#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK D v2
BIAS-CORRECTED N-GRAM ENTROPY
+ HELD-OUT CROSS-ENTROPY

============================================================
PURPOSE
============================================================

Re-evaluate the previously reported Δ₂→₃ entropy jump
using the LOCKED register grammar cell space.

This task operates on:
    cell_id sequences
NOT:
    raw token strings

============================================================
CORE QUESTIONS
============================================================

1. Does Δ₂→₃ survive bias correction?
2. Does order-3 improve held-out prediction?
3. Are higher-order dependencies genuine or sampling artifacts?

============================================================
ENTROPY ESTIMATORS
============================================================

For orders 1–4 compute:

1. Plug-in entropy
2. Miller-Madow bias correction
3. Chao-Shen coverage-adjusted entropy

============================================================
HELD-OUT CROSS-ENTROPY
============================================================

50/50 split by SOURCE SEQUENCE.

Fit:
    A -> B
    B -> A

Orders:
    1–4

============================================================
OUTPUT
============================================================

voynich_taskD_entropy_v2/

FILES
=====

taskD_corrected_entropy.csv
taskD_heldout_xent.csv
taskD_summary.json
checksums.json

FIGURES
=======

entropy_and_xent.png

============================================================
INTERPRETATION
============================================================

If:
- bias-corrected Δ₂→₃ > 0.5 bits
AND
- order3 xent < order2 xent in both directions

=> STRONG

Else if:
- Δ₂→₃ < 0.3
OR
- order3 xent >= order2

=> FALSIFIED

============================================================
"""

# ============================================================
# Imports
# ============================================================

import os
import json
import math
import hashlib
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

# ============================================================
# Constants
# ============================================================

SEED = 42

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskD_entropy_v2"

FIG_DIR = os.path.join(
    OUTPUT_DIR,
    "figures"
)

random.seed(SEED)
np.random.seed(SEED)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    FIG_DIR,
    exist_ok=True
)

# ============================================================
# Utilities
# ============================================================

def sha256_file(path):

    sha = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            sha.update(chunk)

    return sha.hexdigest()


def detect_column(df, candidates):

    lower_map = {
        c.lower(): c
        for c in df.columns
    }

    for cand in candidates:

        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    raise RuntimeError(
        f"Could not detect column from: {candidates}"
    )


def parse_cell_id(cell_id):

    if pd.isna(cell_id):
        return None

    cell = str(cell_id).strip()

    if (
        cell == ""
        or cell.upper() == "FUNC"
    ):
        return None

    parts = cell.split("|")

    if len(parts) != 3:
        return None

    return cell


# ============================================================
# Entropy Estimators
# ============================================================

def plugin_entropy(counts):

    counts = np.array(counts)

    N = counts.sum()

    probs = counts / N

    probs = probs[probs > 0]

    H = -np.sum(
        probs * np.log2(probs)
    )

    return float(H)


def miller_madow_entropy(counts):

    counts = np.array(counts)

    N = counts.sum()

    K = np.sum(counts > 0)

    H_plugin = plugin_entropy(counts)

    correction = (
        (K - 1)
        / (2 * N * math.log(2))
    )

    return float(
        H_plugin + correction
    )


def chao_shen_entropy(counts):

    """
    Chao & Shen 2003
    Biometrika 90(2):277-293
    """

    counts = np.array(counts)

    N = counts.sum()

    freqs = Counter(counts)

    f1 = freqs.get(1, 0)

    C_hat = 1.0 - (f1 / N)

    if C_hat <= 0:
        C_hat = 1e-12

    probs = counts / N

    adjusted_probs = C_hat * probs

    adjusted_probs = adjusted_probs[
        adjusted_probs > 0
    ]

    H = 0.0

    for p in adjusted_probs:

        denom = (
            1.0 -
            (1.0 - p) ** N
        )

        if denom <= 0:
            continue

        H -= (
            (p * np.log2(p))
            / denom
        )

    return float(H)


# ============================================================
# Chao-Shen Unit Test
# ============================================================

def chao_shen_unit_test():

    np.random.seed(SEED)

    uniform = np.random.choice(
        np.arange(100),
        size=1000,
        replace=True
    )

    counts = Counter(uniform)

    values = list(counts.values())

    H_plugin = plugin_entropy(values)

    H_cs = chao_shen_entropy(values)

    target = math.log2(100)

    print("\nChao-Shen unit test:")
    print(f"  target ~ {target:.4f}")
    print(f"  plugin = {H_plugin:.4f}")
    print(f"  chao_shen = {H_cs:.4f}")

    if H_cs < H_plugin:

        raise RuntimeError(
            "Chao-Shen failed sanity check: "
            "returned below plug-in entropy."
        )

# ============================================================
# N-grams
# ============================================================

def extract_ngrams(
    sequences,
    order
):

    ngrams = []

    for seq in sequences:

        if len(seq) < order:
            continue

        for i in range(
            len(seq) - order + 1
        ):

            gram = tuple(
                seq[i:i + order]
            )

            ngrams.append(gram)

    return ngrams


# ============================================================
# Cross Entropy
# ============================================================

def fit_ngram_model(
    sequences,
    order
):

    context_counts = Counter()
    ngram_counts = Counter()

    for seq in sequences:

        if len(seq) < order:
            continue

        for i in range(
            len(seq) - order + 1
        ):

            gram = tuple(
                seq[i:i + order]
            )

            context = gram[:-1]

            target = gram[-1]

            ngram_counts[
                (context, target)
            ] += 1

            context_counts[
                context
            ] += 1

    vocab = set()

    for seq in sequences:

        vocab.update(seq)

    V = len(vocab)

    return (
        ngram_counts,
        context_counts,
        V
    )


def evaluate_cross_entropy(
    sequences,
    order,
    model
):

    (
        ngram_counts,
        context_counts,
        V
    ) = model

    total_logprob = 0.0
    total_n = 0

    for seq in sequences:

        if len(seq) < order:
            continue

        for i in range(
            len(seq) - order + 1
        ):

            gram = tuple(
                seq[i:i + order]
            )

            context = gram[:-1]

            target = gram[-1]

            c_ngram = ngram_counts[
                (context, target)
            ]

            c_context = context_counts[
                context
            ]

            # Laplace smoothing
            p = (
                c_ngram + 1
            ) / (
                c_context + V
            )

            total_logprob += -math.log2(p)

            total_n += 1

    return (
        total_logprob / total_n
    )


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK D v2")
print("BIAS-CORRECTED ENTROPY")
print("====================================================\n")

# ============================================================
# Load
# ============================================================

print("[1/12] Loading MASTER_TOKEN_MATRIX.xlsx...")

raw_df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(raw_df)} rows"
)

# ============================================================
# SHA
# ============================================================

print("\n[2/12] SHA-256 verification...")

matrix_sha = sha256_file(INPUT_MATRIX)

print(
    f"SHA = {matrix_sha}"
)

# ============================================================
# Detect Columns
# ============================================================

print("\n[3/12] Detecting columns...")

cell_col = detect_column(
    raw_df,
    ["cell_id"]
)

parsed_col = detect_column(
    raw_df,
    ["parsed"]
)

locus_col = detect_column(
    raw_df,
    ["locus"]
)

token_idx_col = detect_column(
    raw_df,
    ["line_token_index"]
)

print(f"cell_id: {cell_col}")
print(f"parsed: {parsed_col}")
print(f"locus: {locus_col}")
print(f"token_idx: {token_idx_col}")

# ============================================================
# Parser Self-Test
# ============================================================

print("\n[4/12] Parser self-test...")

sample_cells = (
    raw_df[cell_col]
    .dropna()
    .astype(str)
    .value_counts()
    .head(10)
    .index
)

success = 0

for cell in sample_cells:

    parsed = parse_cell_id(cell)

    if parsed is not None:

        success += 1

        print(f"{cell} -> OK")

if success < 8:

    raise RuntimeError(
        "Parser self-test failed."
    )

print(
    f"\nParser self-test passed: {success}/10"
)

# ============================================================
# Chao-Shen Unit Test
# ============================================================

print("\n[5/12] Chao-Shen unit test...")

chao_shen_unit_test()

# ============================================================
# Build Sequences
# ============================================================

print("\n[6/12] Building cell sequences...")

df = raw_df.copy()

df = df[
    df[parsed_col] == True
].copy()

df["parsed_cell"] = df[cell_col].apply(
    parse_cell_id
)

df = df[
    df["parsed_cell"].notna()
].copy()

grouped = defaultdict(list)

for _, row in df.iterrows():

    grouped[
        row[locus_col]
    ].append((

        row[token_idx_col],

        row["parsed_cell"]
    ))

sequences = []

for locus, vals in grouped.items():

    vals = sorted(vals)

    seq = [
        x[1]
        for x in vals
    ]

    sequences.append(seq)

print(
    f"Built {len(sequences)} sequences"
)

# ============================================================
# Entropy by Order
# ============================================================

print("\n[7/12] Computing entropy...")

entropy_rows = []

for order in [1, 2, 3, 4]:

    print(f"  order={order}")

    ngrams = extract_ngrams(
        sequences,
        order
    )

    counts = Counter(ngrams)

    count_values = list(
        counts.values()
    )

    H_plugin = plugin_entropy(
        count_values
    )

    H_mm = miller_madow_entropy(
        count_values
    )

    H_cs = chao_shen_entropy(
        count_values
    )

    entropy_rows.append({

        "order":
            order,

        "H_plugin":
            H_plugin,

        "H_miller_madow":
            H_mm,

        "H_chao_shen":
            H_cs,

        "K_observed":
            len(counts),

        "N":
            sum(count_values)
    })

entropy_df = pd.DataFrame(
    entropy_rows
)

entropy_path = os.path.join(
    OUTPUT_DIR,
    "taskD_corrected_entropy.csv"
)

entropy_df.to_csv(
    entropy_path,
    index=False
)

# ============================================================
# Delta
# ============================================================

delta_23 = (
    entropy_df.loc[
        entropy_df["order"] == 3,
        "H_miller_madow"
    ].iloc[0]
    -
    entropy_df.loc[
        entropy_df["order"] == 2,
        "H_miller_madow"
    ].iloc[0]
)

# ============================================================
# Held-Out Split
# ============================================================

print("\n[8/12] Held-out cross entropy...")

random.shuffle(sequences)

mid = len(sequences) // 2

A = sequences[:mid]
B = sequences[mid:]

xent_rows = []

for order in [1, 2, 3, 4]:

    print(f"  order={order}")

    model_A = fit_ngram_model(
        A,
        order
    )

    xent_AB = evaluate_cross_entropy(
        B,
        order,
        model_A
    )

    xent_rows.append({

        "order":
            order,

        "direction":
            "A->B",

        "cross_entropy":
            xent_AB
    })

    model_B = fit_ngram_model(
        B,
        order
    )

    xent_BA = evaluate_cross_entropy(
        A,
        order,
        model_B
    )

    xent_rows.append({

        "order":
            order,

        "direction":
            "B->A",

        "cross_entropy":
            xent_BA
    })

xent_df = pd.DataFrame(
    xent_rows
)

xent_path = os.path.join(
    OUTPUT_DIR,
    "taskD_heldout_xent.csv"
)

xent_df.to_csv(
    xent_path,
    index=False
)

# ============================================================
# Interpretation
# ============================================================

print("\n[9/12] Interpretation...")

order2_A = xent_df[
    (xent_df["order"] == 2)
    &
    (xent_df["direction"] == "A->B")
]["cross_entropy"].iloc[0]

order3_A = xent_df[
    (xent_df["order"] == 3)
    &
    (xent_df["direction"] == "A->B")
]["cross_entropy"].iloc[0]

order2_B = xent_df[
    (xent_df["order"] == 2)
    &
    (xent_df["direction"] == "B->A")
]["cross_entropy"].iloc[0]

order3_B = xent_df[
    (xent_df["order"] == 3)
    &
    (xent_df["direction"] == "B->A")
]["cross_entropy"].iloc[0]

if (
    delta_23 > 0.5
    and
    order3_A < order2_A
    and
    order3_B < order2_B
):

    verdict = "STRONG"

elif (
    delta_23 < 0.3
    or
    order3_A >= order2_A
    or
    order3_B >= order2_B
):

    verdict = "FALSIFIED"

else:

    verdict = "CANDIDATE"

print(
    f"Delta 2->3 = {delta_23:.6f}"
)

print(
    f"Verdict = {verdict}"
)

# ============================================================
# Figure
# ============================================================

print("\n[10/12] Writing figure...")

fig, axes = plt.subplots(
    1,
    2,
    figsize=(12, 8)
)

# ------------------------------------------------------------
# Left
# ------------------------------------------------------------

ax = axes[0]

ax.plot(
    entropy_df["order"],
    entropy_df["H_plugin"],
    marker="o",
    label="Plugin"
)

ax.plot(
    entropy_df["order"],
    entropy_df["H_miller_madow"],
    marker="o",
    label="Miller-Madow"
)

ax.plot(
    entropy_df["order"],
    entropy_df["H_chao_shen"],
    marker="o",
    label="Chao-Shen"
)

ax.set_title(
    "Entropy vs Order"
)

ax.set_xlabel("Order")
ax.set_ylabel("Entropy (bits)")

ax.legend()

# ------------------------------------------------------------
# Right
# ------------------------------------------------------------

ax = axes[1]

for direction in ["A->B", "B->A"]:

    subset = xent_df[
        xent_df["direction"] == direction
    ]

    ax.plot(
        subset["order"],
        subset["cross_entropy"],
        marker="o",
        label=direction
    )

ax.set_title(
    "Held-Out Cross Entropy"
)

ax.set_xlabel("Order")
ax.set_ylabel("Cross Entropy")

ax.legend()

fig.suptitle(
    "Task D v2\n"
    "Bias-Corrected Entropy + Held-Out Prediction"
)

plt.tight_layout()

fig_path = os.path.join(
    FIG_DIR,
    "entropy_and_xent.png"
)

plt.savefig(
    fig_path,
    dpi=200
)

plt.close()

# ============================================================
# Summary
# ============================================================

print("\n[11/12] Writing summary...")

summary = {

    "task":
        "D_v2",

    "delta_2_to_3":
        float(delta_23),

    "verdict":
        verdict,

    "entropy_csv":
        os.path.basename(
            entropy_path
        ),

    "heldout_xent_csv":
        os.path.basename(
            xent_path
        ),

    "input_sha256": {

        INPUT_MATRIX:
            matrix_sha
    },

    "seed":
        SEED,

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

summary_path = os.path.join(
    OUTPUT_DIR,
    "taskD_summary.json"
)

with open(
    summary_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=2
    )

# ============================================================
# Checksums
# ============================================================

checksums = {}

for path in [

    entropy_path,
    xent_path,
    summary_path,
    fig_path
]:

    checksums[
        os.path.basename(path)
    ] = sha256_file(path)

checksums_path = os.path.join(
    OUTPUT_DIR,
    "checksums.json"
)

with open(
    checksums_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        checksums,
        f,
        indent=2
    )

# ============================================================
# Complete
# ============================================================

print("\n[12/12] COMPLETE")

print("\n====================================================")
print("TASK D v2 COMPLETE")
print("====================================================")

print(
    f"Delta 2->3 = {delta_23:.6f}"
)

print(
    f"Verdict = {verdict}"
)

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")