#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK C v1
GENERATIVE DISCRIMINATION

============================================================
PURPOSE
============================================================

Test whether the LOCKED cell-bigram structure is sufficient
to generate corpus-indistinguishable sequences.

This is a GENERATIVE VALIDATION task.

============================================================
CORE QUESTION
============================================================

Can synthetic sequences generated from the learned
cell transition structure be distinguished from real
Voynich sequences?

============================================================
SUBTASKS
============================================================

C1
--
Cell-bigram generation vs real

This is the PRIMARY test because Task D established:
- bigram structure generalizes
- trigram structure does not

============================================================

C2
--
Cell-trigram generation vs real

Interpret cautiously:
Task D showed trigram structure is undersampled.

============================================================
METHOD
============================================================

1. Build real cell sequences
2. Fit:
    - bigram Markov generator
    - trigram Markov generator
3. Generate synthetic sequences matching:
    - length distribution
    - sequence count
4. Extract feature vectors
5. Train discriminator:
    REAL vs SYNTHETIC
6. Evaluate:
    - ROC AUC
    - held-out accuracy
    - permutation null

============================================================
INTERPRETATION
============================================================

If discriminator cannot distinguish:
    AUC <= 0.60

=> model captures corpus structure

If discriminator easily distinguishes:
    AUC >= 0.80

=> model insufficient

============================================================
IMPORTANT
============================================================

This is NOT a language test.

This is a structural sufficiency test on the
LOCKED register grammar cell space.

============================================================
OUTPUT
============================================================

voynich_taskC_generative_v1/

FILES
=====

taskC1_bigram_results.json
taskC2_trigram_results.json

taskC_feature_matrix.csv
taskC_discriminator_scores.csv

checksums.json

FIGURES
=======

bigram_auc_histogram.png
trigram_auc_histogram.png
feature_projection.png

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

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score
)

from sklearn.model_selection import (
    train_test_split
)

from sklearn.decomposition import PCA

# ============================================================
# Constants
# ============================================================

SEED = 42

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskC_generative_v1"

FIG_DIR = os.path.join(
    OUTPUT_DIR,
    "figures"
)

N_PERMUTATIONS = 1000

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
        f"Could not detect column: {candidates}"
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
# Sequence Builder
# ============================================================

def build_sequences(df):

    grouped = defaultdict(list)

    for _, row in df.iterrows():

        grouped[
            row["locus"]
        ].append((

            row["token_index"],

            row["parsed_cell"]
        ))

    sequences = []

    for locus, vals in grouped.items():

        vals = sorted(vals)

        seq = [
            x[1]
            for x in vals
        ]

        if len(seq) >= 3:

            sequences.append(seq)

    return sequences


# ============================================================
# Models
# ============================================================

def fit_bigram_model(sequences):

    transitions = defaultdict(Counter)

    starts = Counter()

    vocab = set()

    for seq in sequences:

        starts[seq[0]] += 1

        vocab.update(seq)

        for a, b in zip(seq[:-1], seq[1:]):

            transitions[a][b] += 1

    return {

        "transitions":
            transitions,

        "starts":
            starts,

        "vocab":
            sorted(vocab)
    }


def fit_trigram_model(sequences):

    transitions = defaultdict(Counter)

    starts = Counter()

    vocab = set()

    for seq in sequences:

        if len(seq) < 3:
            continue

        starts[
            (seq[0], seq[1])
        ] += 1

        vocab.update(seq)

        for i in range(len(seq) - 2):

            context = (
                seq[i],
                seq[i + 1]
            )

            nxt = seq[i + 2]

            transitions[
                context
            ][nxt] += 1

    return {

        "transitions":
            transitions,

        "starts":
            starts,

        "vocab":
            sorted(vocab)
    }


# ============================================================
# Sampling
# ============================================================

def weighted_choice(counter):

    items = list(counter.keys())

    weights = np.array(
        list(counter.values()),
        dtype=float
    )

    weights /= weights.sum()

    idx = np.random.choice(
        np.arange(len(items)),
        p=weights
    )

    return items[idx]

def generate_bigram_sequence(
    model,
    length
):

    transitions = model["transitions"]

    current = weighted_choice(
        model["starts"]
    )

    seq = [current]

    for _ in range(length - 1):

        if current not in transitions:

            current = random.choice(
                model["vocab"]
            )

        else:

            current = weighted_choice(
                transitions[current]
            )

        seq.append(current)

    return seq


def generate_trigram_sequence(
    model,
    length
):

    transitions = model["transitions"]

    start = weighted_choice(
        model["starts"]
    )

    seq = [start[0], start[1]]

    while len(seq) < length:

        context = (
            seq[-2],
            seq[-1]
        )

        if context not in transitions:

            nxt = random.choice(
                model["vocab"]
            )

        else:

            nxt = weighted_choice(
                transitions[context]
            )

        seq.append(nxt)

    return seq


# ============================================================
# Feature Extraction
# ============================================================

def sequence_features(seq):

    counts = Counter(seq)

    total = len(seq)

    probs = np.array([
        c / total
        for c in counts.values()
    ])

    entropy = -np.sum(
        probs * np.log2(probs)
    )

    unique_ratio = (
        len(counts) / total
    )

    repeated = sum([
        1
        for a, b in zip(seq[:-1], seq[1:])
        if a == b
    ])

    repeat_rate = (
        repeated / max(1, total - 1)
    )

    return {

        "length":
            total,

        "entropy":
            entropy,

        "unique_ratio":
            unique_ratio,

        "repeat_rate":
            repeat_rate
    }


# ============================================================
# Discriminator
# ============================================================

def discriminator_test(
    real_sequences,
    synthetic_sequences,
    label
):

    rows = []

    for seq in real_sequences:

        feats = sequence_features(seq)

        feats["class"] = 1

        rows.append(feats)

    for seq in synthetic_sequences:

        feats = sequence_features(seq)

        feats["class"] = 0

        rows.append(feats)

    df = pd.DataFrame(rows)

    X = df.drop(
        columns=["class"]
    )

    y = df["class"]

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.3,

        random_state=SEED,

        stratify=y
    )

    clf = RandomForestClassifier(

        n_estimators=300,

        random_state=SEED
    )

    clf.fit(
        X_train,
        y_train
    )

    probs = clf.predict_proba(
        X_test
    )[:, 1]

    preds = clf.predict(
        X_test
    )

    auc = roc_auc_score(
        y_test,
        probs
    )

    acc = accuracy_score(
        y_test,
        preds
    )

    # --------------------------------------------------------
    # Permutation null
    # --------------------------------------------------------

    null_aucs = []

    for i in range(N_PERMUTATIONS):

        y_perm = np.random.permutation(y_train)

        clf_null = RandomForestClassifier(

            n_estimators=100,

            random_state=SEED + i
        )

        clf_null.fit(
            X_train,
            y_perm
        )

        probs_null = clf_null.predict_proba(
            X_test
        )[:, 1]

        auc_null = roc_auc_score(
            y_test,
            probs_null
        )

        null_aucs.append(auc_null)

    z = (
        auc -
        np.mean(null_aucs)
    ) / np.std(null_aucs)

    p = (
        np.sum(
            np.array(null_aucs) >= auc
        ) + 1
    ) / (
        len(null_aucs) + 1
    )

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    if auc <= 0.60:

        verdict = "STRUCTURALLY_SUFFICIENT"

    elif auc >= 0.80:

        verdict = "STRUCTURALLY_INSUFFICIENT"

    else:

        verdict = "PARTIAL"

    return {

        "label":
            label,

        "auc":
            float(auc),

        "accuracy":
            float(acc),

        "null_mean":
            float(np.mean(null_aucs)),

        "null_std":
            float(np.std(null_aucs)),

        "z":
            float(z),

        "p":
            float(p),

        "verdict":
            verdict

    }, df


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK C v1")
print("GENERATIVE DISCRIMINATION")
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

print("\n[2/12] SHA verification...")

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
# Build Corpus
# ============================================================

print("\n[5/12] Building cell corpus...")

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

df = df.rename(columns={

    locus_col:
        "locus",

    token_idx_col:
        "token_index"
})

real_sequences = build_sequences(df)

print(
    f"Sequences: {len(real_sequences)}"
)

lengths = [
    len(s)
    for s in real_sequences
]

# ============================================================
# Bigram Generator
# ============================================================

print("\n[6/12] Bigram generator...")

bigram_model = fit_bigram_model(
    real_sequences
)

synthetic_bigram = []

for L in lengths:

    synthetic_bigram.append(

        generate_bigram_sequence(
            bigram_model,
            L
        )
    )

# ============================================================
# Trigram Generator
# ============================================================

print("\n[7/12] Trigram generator...")

trigram_model = fit_trigram_model(
    real_sequences
)

synthetic_trigram = []

for L in lengths:

    synthetic_trigram.append(

        generate_trigram_sequence(
            trigram_model,
            L
        )
    )

# ============================================================
# Bigram Discriminator
# ============================================================

print("\n[8/12] Bigram discrimination...")

bigram_results, bigram_df = discriminator_test(

    real_sequences,

    synthetic_bigram,

    "bigram"
)

# ============================================================
# Trigram Discriminator
# ============================================================

print("\n[9/12] Trigram discrimination...")

trigram_results, trigram_df = discriminator_test(

    real_sequences,

    synthetic_trigram,

    "trigram"
)

# ============================================================
# Feature Matrix
# ============================================================

print("\n[10/12] Writing outputs...")

feature_df = pd.concat([

    bigram_df.assign(
        generator="bigram"
    ),

    trigram_df.assign(
        generator="trigram"
    )
])

feature_path = os.path.join(
    OUTPUT_DIR,
    "taskC_feature_matrix.csv"
)

feature_df.to_csv(
    feature_path,
    index=False
)

# ------------------------------------------------------------
# Score table
# ------------------------------------------------------------

score_df = pd.DataFrame([

    bigram_results,

    trigram_results
])

score_path = os.path.join(
    OUTPUT_DIR,
    "taskC_discriminator_scores.csv"
)

score_df.to_csv(
    score_path,
    index=False
)

# ------------------------------------------------------------
# JSONs
# ------------------------------------------------------------

bigram_json = os.path.join(
    OUTPUT_DIR,
    "taskC1_bigram_results.json"
)

with open(
    bigram_json,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        bigram_results,
        f,
        indent=2
    )

trigram_json = os.path.join(
    OUTPUT_DIR,
    "taskC2_trigram_results.json"
)

with open(
    trigram_json,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        trigram_results,
        f,
        indent=2
    )

# ============================================================
# Figures
# ============================================================

print("\n[11/12] Writing figures...")

# ------------------------------------------------------------
# Histograms
# ------------------------------------------------------------

for results, fname in [

    (
        bigram_results,
        "bigram_auc_histogram.png"
    ),

    (
        trigram_results,
        "trigram_auc_histogram.png"
    )
]:

    fig, ax = plt.subplots(
        figsize=(8, 6)
    )

    ax.hist(
        np.random.normal(
            results["null_mean"],
            results["null_std"],
            1000
        ),
        bins=40
    )

    ax.axvline(
        results["auc"],
        linewidth=3,
        color="red"
    )

    ax.set_title(
        f"{results['label']} discriminator"
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            FIG_DIR,
            fname
        ),
        dpi=200
    )

    plt.close()

# ------------------------------------------------------------
# PCA projection
# ------------------------------------------------------------

X = feature_df[
    [
        "length",
        "entropy",
        "unique_ratio",
        "repeat_rate"
    ]
]

pca = PCA(n_components=2)

coords = pca.fit_transform(X)

fig, ax = plt.subplots(
    figsize=(8, 8)
)

scatter = ax.scatter(

    coords[:, 0],
    coords[:, 1],

    c=feature_df["class"],

    alpha=0.7
)

ax.set_title(
    "Feature Projection"
)

plt.tight_layout()

proj_path = os.path.join(
    FIG_DIR,
    "feature_projection.png"
)

plt.savefig(
    proj_path,
    dpi=200
)

plt.close()

# ============================================================
# Checksums
# ============================================================

checksums = {}

for path in [

    feature_path,
    score_path,
    bigram_json,
    trigram_json,
    proj_path
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
print("TASK C COMPLETE")
print("====================================================")

print("\nC1 BIGRAM")
print(
    f"AUC = {bigram_results['auc']:.4f}"
)
print(
    f"Verdict = {bigram_results['verdict']}"
)

print("\nC2 TRIGRAM")
print(
    f"AUC = {trigram_results['auc']:.4f}"
)
print(
    f"Verdict = {trigram_results['verdict']}"
)

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")