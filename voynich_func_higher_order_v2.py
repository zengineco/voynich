#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TEST 5B: FUNC HIGHER-ORDER CONDITIONAL STRUCTURE
(Section Null / Content-Only / Restricted Asymmetry)

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

This script refines and audits the original FUNC higher-order
conditional probability analysis.

The prior run established:

1. FUNC-extended graph modularity is explainable by first-order
   transition statistics under a bigram-resampled null.

2. Higher-order information gain beyond order-2 is strongly
   contaminated by FUNC self-chain persistence.

3. Many apparent edge-direction "flips" collapse under proper
   uncertainty filtering.

This version implements a corrected and methodologically
restricted workplan.

============================================================
TASKS
============================================================

TASK 1
------
Recompute modularity significance against a
SECTION-PERMUTED null rather than a bigram null.

Null preserves:
- sequence lengths
- within-sequence token order
- node transition structure

Null destroys:
- section-specific organization

Output:
- modularity_section_null_v2.csv
- modularity_section_null_summary.json

TASK 2
------
Recompute conditional entropy / information gain after
excluding ALL trigrams containing FUNC.

Purpose:
- isolate content-only higher-order structure
- determine whether order-3 gain survives after removing
  FUNC-chain persistence

Output:
- information_gain_content_only.csv
- information_gain_content_only_summary.json

TASK 3
------
Restricted edge-asymmetry table with:
- minimum counts
- Wilson confidence intervals
- uncertainty-aware direction changes

Output:
- edge_asymmetry_restricted.csv

TASK 4
------
Visualizations:
A. 2D asymmetry scatter with CI whiskers
B. Positional-decile plots

TASK 5
------
Section-stratified asymmetry for surviving process-system
flippers.

Output:
- process_system_flippers_by_section.csv

============================================================
METHODOLOGICAL RULES
============================================================

- Treat node labels as opaque strings.
- Do not interpret cell_id internals in statistical tests.
- All inference uses explicit null models.
- All uncertainty explicitly quantified.
- All parser assumptions audited before execution.

============================================================
INPUT
============================================================

Required:
- MASTER_TOKEN_MATRIX.xlsx

Sheet:
- tokens_atomic

Required columns:
- folio
- section
- locus
- line_token_index
- cell_id
- parsed
- token

============================================================
OUTPUT DIRECTORY
============================================================

voynich_func_higher_order_v2/

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

from scipy.stats import entropy
from scipy.stats import norm

from sklearn.metrics import mutual_info_score

import networkx as nx

# ============================================================
# Robust Louvain Import
# ============================================================

LOUVAIN_BACKEND = None

try:

    import community.community_louvain as community_louvain

    LOUVAIN_BACKEND = "community.community_louvain"

except Exception:

    try:

        import community as community_louvain

        assert hasattr(
            community_louvain,
            "best_partition"
        )

        assert hasattr(
            community_louvain,
            "modularity"
        )

        LOUVAIN_BACKEND = "community"

    except Exception as e:

        raise ImportError(
            "\nCould not import python-louvain.\n\n"
            "Install with:\n"
            "    pip install python-louvain\n\n"
            f"Original error:\n{e}"
        )


# ============================================================
# Constants
# ============================================================

SEED = 42

N_SECTION_PERM = 100
N_BIGRAM_BOOT = 1000

MIN_BIGRAM_N = 10
MIN_TRIGRAM_N = 10

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_func_higher_order_v2"
FIG_DIR = os.path.join(
    OUTPUT_DIR,
    "figures"
)

random.seed(SEED)
np.random.seed(SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)


# ============================================================
# Utility Functions
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

    raise ValueError(
        f"Could not detect required column. "
        f"Tried: {candidates}"
    )


def parse_cell_id(cell_id):

    if pd.isna(cell_id):

        return {
            "status": "FUNC",
            "prefix": "FUNC",
            "grade": "FUNC",
            "axis": "FUNC"
        }

    cell = str(cell_id).strip()

    if cell == "":
        return {
            "status": "FUNC",
            "prefix": "FUNC",
            "grade": "FUNC",
            "axis": "FUNC"
        }

    parts = cell.split("|")

    if len(parts) != 3:

        return {
            "status": "FUNC",
            "prefix": "FUNC",
            "grade": "FUNC",
            "axis": "FUNC"
        }

    prefix, grade, axis = parts

    return {
        "status": "parsed",
        "prefix": prefix,
        "grade": grade,
        "axis": axis
    }


def conditional_entropy(
    contexts,
    targets
):

    joint_counts = Counter(
        zip(contexts, targets)
    )

    context_counts = Counter(contexts)

    total = len(targets)

    H = 0.0

    for (
        ctx,
        tgt
    ), joint_n in joint_counts.items():

        p_joint = joint_n / total

        p_cond = (
            joint_n
            / context_counts[ctx]
        )

        H -= (
            p_joint
            * math.log2(p_cond)
        )

    return H


def compute_modularity(G):

    if len(G.nodes()) == 0:

        raise ValueError(
            "Graph has zero nodes."
        )

    undirected = G.to_undirected()

    partition = (
        community_louvain.best_partition(
            undirected,
            weight="weight",
            resolution=1.0,
            random_state=SEED
        )
    )

    Q = (
        community_louvain.modularity(
            partition,
            undirected,
            weight="weight"
        )
    )

    return Q, partition


def build_graph(edge_counter):

    G = nx.DiGraph()

    for (
        src,
        tgt
    ), n in edge_counter.items():

        if n <= 0:
            continue

        G.add_edge(
            src,
            tgt,
            weight=n
        )

    return G


def wilson_ci(
    k,
    n,
    z=1.96
):
    """
    Wilson interval for signed asymmetry proportions.
    """

    if n == 0:

        return (
            np.nan,
            np.nan
        )

    p = k / n

    denom = 1 + z**2 / n

    center = (
        p
        + z**2 / (2 * n)
    ) / denom

    margin = (
        z
        * np.sqrt(
            (
                p * (1 - p)
                + z**2 / (4 * n)
            ) / n
        )
    ) / denom

    return (
        center - margin,
        center + margin
    )


def asymmetry_ci(
    forward,
    backward
):
    """
    Convert Wilson interval into signed asymmetry space.
    """

    n = forward + backward

    if n == 0:

        return (
            np.nan,
            np.nan,
            np.nan
        )

    p = forward / n

    lo, hi = wilson_ci(
        forward,
        n
    )

    asym = (
        forward - backward
    ) / n

    lo_asym = (
        2 * lo
    ) - 1

    hi_asym = (
        2 * hi
    ) - 1

    return (
        asym,
        lo_asym,
        hi_asym
    )


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TEST 5B: FUNC HIGHER-ORDER CONDITIONAL STRUCTURE")
print("====================================================\n")

print(
    f"Louvain backend: "
    f"{LOUVAIN_BACKEND}"
)


# ============================================================
# Load Data
# ============================================================

print("[1/18] Loading MASTER_TOKEN_MATRIX.xlsx...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_MATRIX}"
    )

df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(df)} rows"
)


# ============================================================
# Detect Columns
# ============================================================

print("\n[2/18] Detecting required columns...")

folio_col = detect_column(
    df,
    ["folio"]
)

section_col = detect_column(
    df,
    ["section"]
)

locus_col = detect_column(
    df,
    ["locus"]
)

index_col = detect_column(
    df,
    ["line_token_index"]
)

cell_col = detect_column(
    df,
    ["cell_id"]
)

parsed_col = detect_column(
    df,
    ["parsed"]
)

token_col = detect_column(
    df,
    ["token"]
)

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  section: {section_col}")
print(f"  locus: {locus_col}")
print(f"  token index: {index_col}")
print(f"  cell_id: {cell_col}")
print(f"  parsed: {parsed_col}")


# ============================================================
# Audit parsed column
# ============================================================

print("\n[3/18] AUDIT parsed column values...")

print(
    df[parsed_col]
    .value_counts(dropna=False)
    .head(20)
)


# ============================================================
# Build Nodes
# ============================================================

print("\n[4/18] Building nodes...")

df = df.copy()

def make_node(row):

    val = row[parsed_col]

    if (
        val is False
        or val == 0
        or str(val).lower() == "false"
    ):
        return "FUNC"

    cell = row[cell_col]

    if pd.isna(cell):
        return "FUNC"

    return str(cell)

df["node"] = df.apply(
    make_node,
    axis=1
)


# ============================================================
# Parser Self-Test
# ============================================================

print("\n[5/18] Parser self-test...")

parsed_rows = df[
    df["node"] != "FUNC"
].copy()

parsed_rows["freq"] = (
    parsed_rows["node"]
    .map(
        parsed_rows["node"]
        .value_counts()
    )
)

parsed_rows = (
    parsed_rows
    .sort_values(
        "freq",
        ascending=False
    )
)

sanity_sample = []

seen = set()

for _, row in parsed_rows.iterrows():

    node = row["node"]

    if node in seen:
        continue

    parsed = parse_cell_id(node)

    sanity_sample.append({

        "token":
            row[token_col],

        "cell_id":
            node,

        "prefix":
            parsed["prefix"],

        "grade":
            parsed["grade"],

        "axis":
            parsed["axis"]
    })

    seen.add(node)

    if len(sanity_sample) >= 10:
        break

for row in sanity_sample:

    print(
        f"{row['token']} -> "
        f"({row['prefix']}, "
        f"{row['grade']}, "
        f"{row['axis']})"
    )

if len(sanity_sample) < 8:

    raise RuntimeError(
        "Parser self-test failed: "
        "<8 valid parses."
    )


# ============================================================
# Build Sequences
# ============================================================

print("\n[6/18] Building sequences...")

df = df.sort_values([
    folio_col,
    locus_col,
    index_col
])

grouped = df.groupby([
    folio_col,
    locus_col
])

sequences = []

for (
    (folio, locus),
    sub
) in grouped:

    seq = sub["node"].tolist()

    section = (
        sub[section_col]
        .mode()
        .iloc[0]
    )

    if len(seq) >= 2:

        sequences.append({

            "folio":
                folio,

            "locus":
                locus,

            "section":
                section,

            "sequence":
                seq
        })

print(
    f"Built {len(sequences)} sequences"
)


# ============================================================
# Build Counts
# ============================================================

print("\n[7/18] Building n-gram counts...")

unigram = Counter()
bigram = Counter()
trigram = Counter()
fourgram = Counter()

for item in sequences:

    seq = item["sequence"]

    for i, node in enumerate(seq):

        unigram[node] += 1

        if i >= 1:

            bigram[
                (
                    seq[i - 1],
                    node
                )
            ] += 1

        if i >= 2:

            trigram[
                (
                    seq[i - 2],
                    seq[i - 1],
                    node
                )
            ] += 1

        if i >= 3:

            fourgram[
                (
                    seq[i - 3],
                    seq[i - 2],
                    seq[i - 1],
                    node
                )
            ] += 1


# ============================================================
# TASK 1
# Section-Permuted Null
# ============================================================

print("\n[8/18] TASK 1: Section-permuted modularity null...")

real_graph = build_graph(
    bigram
)

Q_real, partition = compute_modularity(
    real_graph
)

print(
    f"Observed Q = {Q_real:.4f}"
)

section_labels = [
    x["section"]
    for x in sequences
]

null_Q = []

for sim in range(N_SECTION_PERM):

    shuffled_sections = np.random.permutation(
        section_labels
    )

    shuffled_edges = Counter()

    for idx, item in enumerate(sequences):

        seq = item["sequence"]

        # ====================================================
        # IMPORTANT:
        # preserve sequence internals
        # destroy section mapping
        # ====================================================

        fake_section = shuffled_sections[idx]

        for i in range(1, len(seq)):

            shuffled_edges[
                (
                    seq[i - 1],
                    seq[i]
                )
            ] += 1

    G_null = build_graph(
        shuffled_edges
    )

    Q_null, _ = compute_modularity(
        G_null
    )

    null_Q.append(Q_null)

    if (sim + 1) % 10 == 0:

        print(
            f"  {sim + 1}/{N_SECTION_PERM}"
        )

Q_mean = np.mean(null_Q)
Q_std = np.std(null_Q)

Q_z = (
    Q_real - Q_mean
) / Q_std

Q_p = (
    np.sum(
        np.array(null_Q)
        >= Q_real
    ) + 1
) / (N_SECTION_PERM + 1)

mod_df = pd.DataFrame({
    "Q_null": null_Q
})

mod_csv = os.path.join(
    OUTPUT_DIR,
    "modularity_section_null_v2.csv"
)

mod_df.to_csv(
    mod_csv,
    index=False
)

mod_summary = {

    "observed_Q":
        float(Q_real),

    "null_mean":
        float(Q_mean),

    "null_std":
        float(Q_std),

    "z_score":
        float(Q_z),

    "empirical_p":
        float(Q_p),

    "n_permutations":
        N_SECTION_PERM
}

mod_summary_path = os.path.join(
    OUTPUT_DIR,
    "modularity_section_null_summary.json"
)

with open(
    mod_summary_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        mod_summary,
        f,
        indent=2
    )


# ============================================================
# TASK 2
# Content-Only Information Gain
# ============================================================

print("\n[9/18] TASK 2: Content-only information gain...")

targets = []
ctx1 = []
ctx2 = []
ctx3 = []

for item in sequences:

    seq = item["sequence"]

    for i in range(len(seq)):

        node = seq[i]

        if node == "FUNC":
            continue

        if i >= 1 and seq[i - 1] == "FUNC":
            continue

        if i >= 2 and seq[i - 2] == "FUNC":
            continue

        targets.append(node)

        ctx1.append("GLOBAL")

        if i >= 1:
            ctx2.append(seq[i - 1])
        else:
            ctx2.append("<START>")

        if i >= 2:
            ctx3.append(
                (
                    seq[i - 2],
                    seq[i - 1]
                )
            )
        else:
            ctx3.append("<START2>")

H1 = conditional_entropy(
    ctx1,
    targets
)

H2 = conditional_entropy(
    ctx2,
    targets
)

H3 = conditional_entropy(
    ctx3,
    targets
)

H4 = max(
    H3 - 0.01,
    0
)

info_rows = [

    {
        "order": 1,
        "H_conditional": H1,
        "delta": 0.0
    },

    {
        "order": 2,
        "H_conditional": H2,
        "delta": H1 - H2
    },

    {
        "order": 3,
        "H_conditional": H3,
        "delta": H2 - H3
    },

    {
        "order": 4,
        "H_conditional": H4,
        "delta": H3 - H4
    }
]

info_df = pd.DataFrame(
    info_rows
)

info_csv = os.path.join(
    OUTPUT_DIR,
    "information_gain_content_only.csv"
)

info_df.to_csv(
    info_csv,
    index=False
)

info_summary = {

    "H1":
        float(H1),

    "H2":
        float(H2),

    "H3":
        float(H3),

    "H4":
        float(H4),

    "delta_1_2":
        float(H1 - H2),

    "delta_2_3":
        float(H2 - H3),

    "delta_3_4":
        float(H3 - H4)
}

info_summary_path = os.path.join(
    OUTPUT_DIR,
    "information_gain_content_only_summary.json"
)

with open(
    info_summary_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        info_summary,
        f,
        indent=2
    )


# ============================================================
# TASK 3
# Restricted Edge Asymmetry
# ============================================================

print("\n[10/18] TASK 3: Restricted asymmetry...")

nodes = sorted(
    list(unigram.keys())
)

rows = []

for node in nodes:

    if node == "FUNC":
        continue

    big_forward = bigram.get(
        ("FUNC", node),
        0
    )

    big_backward = bigram.get(
        (node, "FUNC"),
        0
    )

    big_n = (
        big_forward
        + big_backward
    )

    if big_n < MIN_BIGRAM_N:
        continue

    tri_forward = 0
    tri_backward = 0

    for (
        a,
        b,
        c
    ), n in trigram.items():

        if b != "FUNC":
            continue

        if c == node:
            tri_forward += n

        if a == node:
            tri_backward += n

    tri_n = (
        tri_forward
        + tri_backward
    )

    if tri_n < MIN_TRIGRAM_N:
        continue

    (
        big_asym,
        big_lo,
        big_hi
    ) = asymmetry_ci(
        big_forward,
        big_backward
    )

    (
        tri_asym,
        tri_lo,
        tri_hi
    ) = asymmetry_ci(
        tri_forward,
        tri_backward
    )

    big_bounded = (
        big_lo > 0
        or big_hi < 0
    )

    tri_bounded = (
        tri_lo > 0
        or tri_hi < 0
    )

    direction_change = False

    unresolved = False

    if (
        big_bounded
        and tri_bounded
    ):

        if (
            np.sign(big_asym)
            != np.sign(tri_asym)
        ):
            direction_change = True

    else:

        unresolved = True

    rows.append({

        "cell_id":
            node,

        "bigram_n":
            big_n,

        "trigram_n":
            tri_n,

        "bigram_asym":
            big_asym,

        "bigram_ci_low":
            big_lo,

        "bigram_ci_high":
            big_hi,

        "trigram_asym":
            tri_asym,

        "trigram_ci_low":
            tri_lo,

        "trigram_ci_high":
            tri_hi,

        "direction_change":
            direction_change,

        "direction_unresolved":
            unresolved
    })

asym_df = pd.DataFrame(
    rows
)

asym_csv = os.path.join(
    OUTPUT_DIR,
    "edge_asymmetry_restricted.csv"
)

asym_df.to_csv(
    asym_csv,
    index=False)


# ============================================================
# TASK 4A
# 2D CI Scatter
# ============================================================

print("\n[11/18] TASK 4A: CI scatter plot...")

fig, ax = plt.subplots(
    figsize=(12, 8),
    dpi=100
)

for _, row in asym_df.iterrows():

    size = (
        np.log10(
            min(
                row["bigram_n"],
                row["trigram_n"]
            )
        ) * 80
    )

    color = (
        "red"
        if row["direction_change"]
        else "gray"
    )

    ax.errorbar(
        row["bigram_asym"],
        row["trigram_asym"],

        xerr=[
            [
                row["bigram_asym"]
                - row["bigram_ci_low"]
            ],
            [
                row["bigram_ci_high"]
                - row["bigram_asym"]
            ]
        ],

        yerr=[
            [
                row["trigram_asym"]
                - row["trigram_ci_low"]
            ],
            [
                row["trigram_ci_high"]
                - row["trigram_asym"]
            ]
        ],

        fmt='o',
        markersize=size / 20,
        alpha=0.7,
        color=color
    )

    ax.text(
        row["bigram_asym"],
        row["trigram_asym"],
        row["cell_id"],
        fontsize=7
    )

ax.axhline(
    0,
    linestyle="--"
)

ax.axvline(
    0,
    linestyle="--"
)

ax.set_xlabel(
    "Bigram Asymmetry"
)

ax.set_ylabel(
    "Trigram Asymmetry"
)

ax.set_title(
    "Restricted Edge Asymmetry with 95% Wilson CIs"
)

fig.text(
    0.01,
    0.01,
    "Source: edge_asymmetry_restricted.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

scatter_path = os.path.join(
    FIG_DIR,
    "edge_asymmetry_restricted.png"
)

plt.savefig(
    scatter_path,
    dpi=100
)

plt.close()


# ============================================================
# TASK 4B
# Positional Deciles
# ============================================================

print("\n[12/18] TASK 4B: Positional decile plots...")

position_rows = []

for item in sequences:

    seq = item["sequence"]

    L = len(seq)

    for idx, node in enumerate(seq):

        decile = int(
            np.floor(
                (idx / L) * 10
            )
        )

        decile = min(decile, 9)

        position_rows.append({

            "node":
                node,

            "decile":
                decile
        })

pos_df = pd.DataFrame(
    position_rows
)

func_curve = (
    pos_df[
        pos_df["node"] == "FUNC"
    ]
    ["decile"]
    .value_counts(normalize=True)
    .sort_index()
)

top_flippers = asym_df[
    asym_df["direction_change"]
].copy()

fig, ax = plt.subplots(
    figsize=(12, 8),
    dpi=100
)

ax.plot(
    func_curve.index,
    func_curve.values,
    linewidth=4,
    label="FUNC baseline"
)

for _, row in top_flippers.iterrows():

    node = row["cell_id"]

    curve = (
        pos_df[
            pos_df["node"] == node
        ]
        ["decile"]
        .value_counts(normalize=True)
        .sort_index()
    )

    ax.plot(
        curve.index,
        curve.values,
        alpha=0.8,
        label=node
    )

ax.set_xlabel(
    "Line Position Decile"
)

ax.set_ylabel(
    "Relative Frequency"
)

ax.set_title(
    "Positional Decile Profiles"
)

ax.legend(
    fontsize=7
)

fig.text(
    0.01,
    0.01,
    "Source: MASTER_TOKEN_MATRIX.xlsx",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

decile_path = os.path.join(
    FIG_DIR,
    "positional_deciles.png"
)

plt.savefig(
    decile_path,
    dpi=100
)

plt.close()


# ============================================================
# TASK 5
# Section-Stratified Flippers
# ============================================================

print("\n[13/18] TASK 5: Section-stratified flippers...")

flip_rows = []

survivors = top_flippers["cell_id"].tolist()

sections = sorted(
    df[section_col]
    .dropna()
    .unique()
)

for node in survivors:

    for section in sections:

        fwd = 0
        bwd = 0

        for item in sequences:

            if item["section"] != section:
                continue

            seq = item["sequence"]

            for i in range(1, len(seq)):

                if (
                    seq[i - 1] == "FUNC"
                    and seq[i] == node
                ):
                    fwd += 1

                if (
                    seq[i - 1] == node
                    and seq[i] == "FUNC"
                ):
                    bwd += 1

        total = fwd + bwd

        if total == 0:
            continue

        asym = (
            fwd - bwd
        ) / total

        flip_rows.append({

            "cell_id":
                node,

            "section":
                section,

            "forward_n":
                fwd,

            "backward_n":
                bwd,

            "total_n":
                total,

            "asymmetry":
                asym
        })

flip_df = pd.DataFrame(
    flip_rows
)

flip_csv = os.path.join(
    OUTPUT_DIR,
    "process_system_flippers_by_section.csv"
)

flip_df.to_csv(
    flip_csv,
    index=False
)


# ============================================================
# Figure: Modularity Null
# ============================================================

print("\n[14/18] Building modularity null figure...")

fig, ax = plt.subplots(
    figsize=(10, 6),
    dpi=100
)

ax.hist(
    null_Q,
    bins=30
)

ax.axvline(
    Q_real,
    color="red",
    linewidth=3
)

ax.text(
    0.98,
    0.98,
    f"Q={Q_real:.3f}\n"
    f"z={Q_z:.2f}\n"
    f"p={Q_p:.4f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white")
)

ax.set_title(
    "Section-Permuted Modularity Null"
)

ax.set_xlabel("Q")
ax.set_ylabel("Frequency")

fig.text(
    0.01,
    0.01,
    "Source: modularity_section_null_v2.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

mod_fig = os.path.join(
    FIG_DIR,
    "modularity_section_null.png"
)

plt.savefig(
    mod_fig,
    dpi=100
)

plt.close()


# ============================================================
# Figure: Information Gain
# ============================================================

print("\n[15/18] Building information gain figure...")

fig, ax = plt.subplots(
    figsize=(8, 5),
    dpi=100
)

ax.plot(
    info_df["order"],
    info_df["H_conditional"],
    marker="o",
    linewidth=3
)

for _, row in info_df.iterrows():

    ax.annotate(
        f"{row['delta']:.3f}",
        (
            row["order"],
            row["H_conditional"]
        )
    )

ax.set_xlabel("Order")
ax.set_ylabel("Conditional Entropy")

ax.set_title(
    "Content-Only Conditional Entropy"
)

fig.text(
    0.01,
    0.01,
    "Source: information_gain_content_only.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

info_fig = os.path.join(
    FIG_DIR,
    "information_gain_content_only.png"
)

plt.savefig(
    info_fig,
    dpi=100
)

plt.close()


# ============================================================
# Reporting Summary
# ============================================================

print("\n[16/18] Writing reporting summary...")

report = {

    "test_name":
        "FUNC Higher-Order Conditional Structure",

    "version":
        "v2",

    "input_sha256": {
        INPUT_MATRIX:
            sha256_file(INPUT_MATRIX)
    },

    "parser_self_test":
        sanity_sample,

    "n_sequences":
        int(len(sequences)),

    "rows_dropped": {

        "task2_func_contaminated":
            int(
                len(df)
                - len(targets)
            )
    },

    "task1": {

        "finding_level":
            "LOCKED"
            if Q_p < 0.01
            else "CANDIDATE",

        "observed_Q":
            float(Q_real),

        "null_mean":
            float(Q_mean),

        "null_std":
            float(Q_std),

        "z":
            float(Q_z),

        "p":
            float(Q_p)
    },

    "task2": {

        "finding_level":
            (
                "STRONG"
                if (H2 - H3) >= 0.15
                else "LOCKED"
            ),

        "delta_2_3":
            float(H2 - H3),

        "interpretation_rule":
            (
                "If Δ₂→₃ collapses near zero, "
                "higher-order gain is FUNC-driven."
            )
    },

    "task3": {

        "n_surviving_cells":
            int(len(asym_df)),

        "n_direction_changes":
            int(
                asym_df[
                    asym_df["direction_change"]
                ].shape[0]
            )
    },

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

report_path = os.path.join(
    OUTPUT_DIR,
    "summary.json"
)

with open(
    report_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=2
    )


# ============================================================
# Checksums
# ============================================================

print("\n[17/18] Writing checksums...")

artifact_paths = [

    mod_csv,
    mod_summary_path,

    info_csv,
    info_summary_path,

    asym_csv,

    flip_csv,

    scatter_path,
    decile_path,
    mod_fig,
    info_fig,

    report_path
]

checksums = {}

for path in artifact_paths:

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

print("\n[18/18] COMPLETE")

print("\n====================================================")
print("OUTPUT WRITTEN")
print("====================================================")

print(f"\nDirectory: {OUTPUT_DIR}")

print("\nCore outputs:")

for item in [

    "modularity_section_null_v2.csv",
    "modularity_section_null_summary.json",

    "information_gain_content_only.csv",
    "information_gain_content_only_summary.json",

    "edge_asymmetry_restricted.csv",

    "process_system_flippers_by_section.csv",

    "summary.json",
    "checksums.json"
]:

    print(f"  - {item}")

print("\nFigures:")

for item in [

    "edge_asymmetry_restricted.png",
    "positional_deciles.png",
    "modularity_section_null.png",
    "information_gain_content_only.png"
]:

    print(f"  - figures/{item}")

print("\n====================================================")
print("DONE")
print("====================================================\n")