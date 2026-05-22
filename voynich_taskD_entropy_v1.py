#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK D v1
ENTROPY + CROSS-ENTROPY ANALYSIS

============================================================
PURPOSE
============================================================

Estimate entropy structure of Voynich content-only trigrams
using multiple estimators and held-out predictive evaluation.

This task explicitly separates:

1. IN-SAMPLE ENTROPY
   - Shannon MLE
   - Miller-Madow correction
   - Chao-Shen correction

2. HELD-OUT PREDICTIVE CROSS-ENTROPY
   - train/test split
   - smoothed trigram LM
   - perplexity evaluation

============================================================
IMPORTANT
============================================================

This task uses ONLY content tokens.

Excluded:
- FUNC
- unparsed
- grammar metadata

The goal is to estimate symbolic predictability
of the content layer independently of the register grammar.

============================================================
OUTPUT
============================================================

voynich_taskD_entropy_v1/

FILES
=====

entropy_summary.json
trigram_counts.csv
cross_entropy_results.csv
checksums.json

FIGURES
=======

trigram_rank_frequency.png
cross_entropy_distribution.png

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

from sklearn.model_selection import train_test_split

# ============================================================
# Constants
# ============================================================

SEED = 42

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskD_entropy_v1"

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


# ============================================================
# Entropy Estimators
# ============================================================

def shannon_entropy(counts):

    total = sum(counts)

    H = 0.0

    for c in counts:

        p = c / total

        H -= p * math.log2(p)

    return H


def miller_madow_entropy(counts):

    counts = np.array(counts)

    N = counts.sum()

    K = np.sum(counts > 0)

    H_mle = shannon_entropy(counts)

    correction = (
        (K - 1)
        / (2 * N * math.log(2))
    )

    return H_mle + correction


def chao_shen_entropy(counts):

    counts = np.array(counts)

    N = counts.sum()

    f1 = np.sum(counts == 1)

    coverage = 1.0 - (f1 / N)

    if coverage <= 0:
        coverage = 1e-12

    probs = counts / N

    adjusted = coverage * probs

    adjusted = adjusted[adjusted > 0]

    H = -np.sum(
        adjusted * np.log2(adjusted)
    )

    return float(H)


# ============================================================
# Cross Entropy
# ============================================================

def build_trigram_model(tokens):

    trigram_counts = Counter()
    context_counts = Counter()

    for i in range(len(tokens) - 2):

        context = (
            tokens[i],
            tokens[i + 1]
        )

        target = tokens[i + 2]

        trigram_counts[
            (context, target)
        ] += 1

        context_counts[
            context
        ] += 1

    vocab = set(tokens)

    V = len(vocab)

    return trigram_counts, context_counts, vocab, V


def cross_entropy(
    test_tokens,
    trigram_counts,
    context_counts,
    V
):

    logprob = 0.0
    n = 0

    for i in range(len(test_tokens) - 2):

        context = (
            test_tokens[i],
            test_tokens[i + 1]
        )

        target = test_tokens[i + 2]

        c_xy = trigram_counts[
            (context, target)
        ]

        c_x = context_counts[
            context
        ]

        # Laplace smoothing
        p = (
            c_xy + 1
        ) / (
            c_x + V
        )

        logprob += -math.log2(p)

        n += 1

    return logprob / n


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK D v1")
print("ENTROPY + CROSS-ENTROPY")
print("====================================================\n")

# ============================================================
# Load
# ============================================================

print("[1/10] Loading MASTER_TOKEN_MATRIX.xlsx...")

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

print("\n[2/10] SHA-256 verification...")

matrix_sha = sha256_file(INPUT_MATRIX)

print(
    f"SHA = {matrix_sha}"
)

# ============================================================
# Detect Columns
# ============================================================

print("\n[3/10] Detecting columns...")

token_col = detect_column(
    raw_df,
    ["token"]
)

parsed_col = detect_column(
    raw_df,
    ["parsed"]
)

print(f"token: {token_col}")
print(f"parsed: {parsed_col}")

# ============================================================
# Content Tokens
# ============================================================

print("\n[4/10] Filtering content tokens...")

content_df = raw_df[
    raw_df[parsed_col] == True
].copy()

tokens = (
    content_df[token_col]
    .astype(str)
    .tolist()
)

print(
    f"Content tokens: {len(tokens)}"
)

# ============================================================
# Trigrams
# ============================================================

print("\n[5/10] Building trigram counts...")

trigrams = Counter()

for i in range(len(tokens) - 2):

    tri = (
        tokens[i],
        tokens[i + 1],
        tokens[i + 2]
    )

    trigrams[tri] += 1

print(
    f"Unique trigrams: {len(trigrams)}"
)

# ============================================================
# Entropy
# ============================================================

print("\n[6/10] Computing entropy estimates...")

counts = list(
    trigrams.values()
)

H_shannon = shannon_entropy(counts)

H_mm = miller_madow_entropy(counts)

H_cs = chao_shen_entropy(counts)

print(f"Shannon H = {H_shannon:.6f}")
print(f"Miller-Madow H = {H_mm:.6f}")
print(f"Chao-Shen H = {H_cs:.6f}")

# ============================================================
# Held-Out Cross Entropy
# ============================================================

print("\n[7/10] Held-out cross-entropy...")

train_tokens, test_tokens = train_test_split(
    tokens,
    test_size=0.2,
    random_state=SEED,
    shuffle=True
)

(
    trigram_counts,
    context_counts,
    vocab,
    V
) = build_trigram_model(train_tokens)

H_cross = cross_entropy(

    test_tokens,

    trigram_counts,

    context_counts,

    V
)

perplexity = 2 ** H_cross

print(
    f"Cross entropy = {H_cross:.6f}"
)

print(
    f"Perplexity = {perplexity:.6f}"
)

# ============================================================
# Write Trigrams
# ============================================================

print("\n[8/10] Writing outputs...")

tri_df = pd.DataFrame({

    "trigram":
        [
            " ".join(t)
            for t in trigrams.keys()
        ],

    "count":
        list(trigrams.values())
})

tri_df = tri_df.sort_values(
    "count",
    ascending=False
)

tri_path = os.path.join(
    OUTPUT_DIR,
    "trigram_counts.csv"
)

tri_df.to_csv(
    tri_path,
    index=False
)

# ============================================================
# Cross Entropy CSV
# ============================================================

cross_df = pd.DataFrame([{

    "cross_entropy":
        H_cross,

    "perplexity":
        perplexity
}])

cross_path = os.path.join(
    OUTPUT_DIR,
    "cross_entropy_results.csv"
)

cross_df.to_csv(
    cross_path,
    index=False
)

# ============================================================
# Figures
# ============================================================

print("\n[9/10] Writing figures...")

# ------------------------------------------------------------
# Rank-frequency
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ranked = sorted(
    trigrams.values(),
    reverse=True
)

ax.plot(ranked)

ax.set_xscale("log")
ax.set_yscale("log")

ax.set_title(
    "Trigram Rank-Frequency"
)

plt.tight_layout()

rank_fig = os.path.join(
    FIG_DIR,
    "trigram_rank_frequency.png"
)

plt.savefig(
    rank_fig,
    dpi=200
)

plt.close()

# ------------------------------------------------------------
# Cross entropy
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(6, 6)
)

ax.hist(
    [H_cross],
    bins=10
)

ax.set_title(
    "Cross Entropy"
)

cross_fig = os.path.join(
    FIG_DIR,
    "cross_entropy_distribution.png"
)

plt.tight_layout()

plt.savefig(
    cross_fig,
    dpi=200
)

plt.close()

# ============================================================
# Summary
# ============================================================

summary = {

    "task":
        "D_v1",

    "entropy": {

        "shannon":
            H_shannon,

        "miller_madow":
            H_mm,

        "chao_shen":
            H_cs
    },

    "cross_entropy": {

        "heldout_cross_entropy":
            H_cross,

        "perplexity":
            perplexity
    },

    "input_sha256": {

        INPUT_MATRIX:
            matrix_sha
    },

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

summary_path = os.path.join(
    OUTPUT_DIR,
    "entropy_summary.json"
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

    tri_path,
    cross_path,
    summary_path,
    rank_fig,
    cross_fig
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

print("\n[10/10] COMPLETE")

print("\n====================================================")
print("TASK D COMPLETE")
print("====================================================")

print(f"Shannon H = {H_shannon:.6f}")
print(f"Miller-Madow H = {H_mm:.6f}")
print(f"Chao-Shen H = {H_cs:.6f}")
print(f"Cross Entropy = {H_cross:.6f}")
print(f"Perplexity = {perplexity:.6f}")

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")