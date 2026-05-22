#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 2: Bootstrap Confidence Intervals on Section Cosine Matrix

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Estimate bootstrap confidence intervals for the section-section
cosine similarity matrix derived from the productive register-cell
grammar.

NULL HYPOTHESIS
===============
Observed section-section cosine similarities are unstable under
folio resampling and may reflect sampling variance rather than
persistent structural relationships.

BOOTSTRAP DESIGN
================
- Construct folio × cell matrix from MASTER_TOKEN_MATRIX.xlsx
- Productive cells derived from cell_id
- Aggregate cell counts to folio level
- Assign section label via modal token-section per folio
- Within each section:
    bootstrap-resample folios WITH replacement
- Recompute section centroid vectors
- Compute 6×6 cosine matrix
- Repeat 1,000 times

BOOTSTRAP PRESERVES
===================
- Section membership
- Folio-level feature covariance
- Register-cell inventory
- Relative within-section feature structure

BOOTSTRAP DESTROYS
==================
- Exact folio composition per section
- Dependence on any single folio

WHAT THIS SCRIPT DOES TEST
==========================
- Stability of section cosine relationships under folio resampling
- Confidence intervals for each section pair

WHAT THIS SCRIPT DOES NOT TEST
==============================
- Semantic interpretation
- Decipherment
- Causal explanation
- Alternative tokenizers or corpora

INPUTS
======
Required files:
- MASTER_TOKEN_MATRIX.xlsx

Required sheet:
- tokens_atomic

REQUIRED COLUMNS
================
- folio
- section
- cell_id

OUTPUTS
=======
Creates:
    voynich_section_cosine_bootstrap_v1/

Artifacts:
- bootstrap_cosines.csv
- summary.json
- checksums.json
- figures/cosine_heatmap_with_CI.png

DEPENDENCIES
============
- pandas
- numpy
- scipy
- scikit-learn
- matplotlib
- seaborn
- openpyxl

USAGE
=====
Run locally from directory containing required input files:

    python voynich_section_cosine_bootstrap_v1.py
"""

import os
import json
import hashlib
import random
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# Constants
# ============================================================

SEED = 42
N_BOOTSTRAPS = 1000

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_section_cosine_bootstrap_v1"
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")


# ============================================================
# Utility Functions
# ============================================================

def sha256_file(path):
    """
    Compute SHA-256 hash of file.
    """

    sha = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            sha.update(chunk)

    return sha.hexdigest()


def ensure_dirs():
    """
    Create output directories.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def detect_column(df, candidates):
    """
    Detect first matching column.
    """

    lower_map = {
        c.lower(): c
        for c in df.columns
    }

    for cand in candidates:

        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    raise ValueError(
        f"Could not detect required column. "
        f"Tried candidates: {candidates}"
    )


def modal_value(series):
    """
    Return modal value from series.
    """

    counts = Counter(series.dropna())

    if len(counts) == 0:
        return np.nan

    return counts.most_common(1)[0][0]


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH SECTION COSINE BOOTSTRAP V1")
print("====================================================\n")

ensure_dirs()


# ============================================================
# Load Input
# ============================================================

INPUT_FILES = [
    "MASTER_TOKEN_MATRIX.xlsx"
]

print("[1/9] Loading input file...")

for f in INPUT_FILES:

    if not os.path.exists(f):

        raise FileNotFoundError(
            f"Missing required input file: {f}"
        )

token_df = pd.read_excel(
    "MASTER_TOKEN_MATRIX.xlsx",
    sheet_name="tokens_atomic"
)

print(
    f"Loaded MASTER_TOKEN_MATRIX.xlsx "
    f"({len(token_df)} rows)"
)


# ============================================================
# Detect Columns
# ============================================================

print("\n[2/9] Detecting required columns...")

folio_col = detect_column(
    token_df,
    ["folio"]
)

section_col = detect_column(
    token_df,
    ["section"]
)

cell_col = detect_column(
    token_df,
    ["cell_id"]
)

print(f"Detected folio column: {folio_col}")
print(f"Detected section column: {section_col}")
print(f"Detected cell column: {cell_col}")


# ============================================================
# Filter Productive Cells
# ============================================================

print("\n[3/9] Filtering productive register cells...")

token_df = token_df.copy()

token_df[cell_col] = (
    token_df[cell_col]
    .astype(str)
    .str.strip()
)

exclude_values = {
    "",
    "nan",
    "NaN",
    "NONE",
    "None",
    "FUNC"
}

token_df = token_df[
    ~token_df[cell_col].isin(exclude_values)
]

print(
    f"Remaining token rows after filtering: "
    f"{len(token_df)}"
)


# ============================================================
# Construct Folio × Cell Matrix
# ============================================================

print("\n[4/9] Constructing folio × cell matrix...")

folio_cell = pd.crosstab(
    token_df[folio_col],
    token_df[cell_col]
)

print(
    f"Folio × cell matrix shape: "
    f"{folio_cell.shape}"
)


# ============================================================
# Compute Modal Section Labels
# ============================================================

print("\n[5/9] Computing modal section labels...")

folio_sections = (
    token_df
    .groupby(folio_col)[section_col]
    .agg(modal_value)
)

common_folios = (
    folio_cell.index
    .intersection(folio_sections.index)
)

folio_cell = folio_cell.loc[common_folios]
folio_sections = folio_sections.loc[common_folios]

print(
    f"Final folio count: "
    f"{len(common_folios)}"
)

sections = sorted(
    folio_sections.unique()
)

print(f"Detected sections: {sections}")


# ============================================================
# Prepare Section Data
# ============================================================

print("\n[6/9] Preparing section bootstrap pools...")

section_folios = {}

for sec in sections:

    folios = folio_sections[
        folio_sections == sec
    ].index.tolist()

    section_folios[sec] = folios

    print(
        f"Section {sec}: "
        f"{len(folios)} folios"
    )


# ============================================================
# Bootstrap Cosine Matrices
# ============================================================

print("\n[7/9] Running bootstrap resampling...")
print(f"Bootstraps: {N_BOOTSTRAPS}\n")

bootstrap_results = {}

for s1 in sections:
    for s2 in sections:
        bootstrap_results[(s1, s2)] = []

for i in range(N_BOOTSTRAPS):

    section_centroids = []

    for sec in sections:

        folios = section_folios[sec]

        sampled = np.random.choice(
            folios,
            size=len(folios),
            replace=True
        )

        sampled_matrix = folio_cell.loc[sampled]

        centroid = sampled_matrix.mean(axis=0).values

        section_centroids.append(centroid)

    section_centroids = np.vstack(section_centroids)

    cosine_matrix = cosine_similarity(
        section_centroids
    )

    for r, s1 in enumerate(sections):
        for c, s2 in enumerate(sections):

            bootstrap_results[(s1, s2)].append(
                cosine_matrix[r, c]
            )

    if (i + 1) % 50 == 0:

        print(
            f"Completed "
            f"{i + 1}/{N_BOOTSTRAPS}"
        )


# ============================================================
# Compute Summary Statistics
# ============================================================

print("\n[8/9] Computing confidence intervals...")

summary_rows = []

ci_excludes_zero = []
non_overlapping_pairs = []

cell_stats = {}

for s1 in sections:

    for s2 in sections:

        vals = np.array(
            bootstrap_results[(s1, s2)]
        )

        mean_val = float(np.mean(vals))

        ci_low = float(
            np.percentile(vals, 2.5)
        )

        ci_high = float(
            np.percentile(vals, 97.5)
        )

        cell_stats[(s1, s2)] = {
            "mean": mean_val,
            "ci_low": ci_low,
            "ci_high": ci_high
        }

        if ci_low > 0 or ci_high < 0:

            ci_excludes_zero.append(
                [s1, s2]
            )

        summary_rows.append({
            "section_1": s1,
            "section_2": s2,
            "mean_cosine": mean_val,
            "ci_2.5": ci_low,
            "ci_97.5": ci_high
        })

# Non-overlapping CI detection

pairs = list(cell_stats.keys())

for i in range(len(pairs)):

    for j in range(i + 1, len(pairs)):

        p1 = pairs[i]
        p2 = pairs[j]

        a = cell_stats[p1]
        b = cell_stats[p2]

        overlap = not (
            a["ci_high"] < b["ci_low"]
            or
            b["ci_high"] < a["ci_low"]
        )

        if not overlap:

            non_overlapping_pairs.append({
                "pair_1": list(p1),
                "pair_2": list(p2)
            })

bootstrap_df = pd.DataFrame(
    summary_rows
)

bootstrap_csv_path = os.path.join(
    OUTPUT_DIR,
    "bootstrap_cosines.csv"
)

bootstrap_df.to_csv(
    bootstrap_csv_path,
    index=False
)


# ============================================================
# Build Display Matrix
# ============================================================

display_matrix = pd.DataFrame(
    index=sections,
    columns=sections
)

heatmap_matrix = pd.DataFrame(
    index=sections,
    columns=sections,
    dtype=float
)

for s1 in sections:

    for s2 in sections:

        stats = cell_stats[(s1, s2)]

        display_matrix.loc[s1, s2] = (
            f"{stats['mean']:.3f}\n"
            f"[{stats['ci_low']:.3f}, "
            f"{stats['ci_high']:.3f}]"
        )

        heatmap_matrix.loc[s1, s2] = (
            stats["mean"]
        )


# ============================================================
# Plot Heatmap
# ============================================================

print("\n[9/9] Writing outputs...")

plt.figure(figsize=(12, 10))

sns.heatmap(
    heatmap_matrix,
    annot=display_matrix,
    fmt="",
    square=True,
    cbar=True
)

plt.title(
    "Section Cosine Similarity Matrix\n"
    "Mean Bootstrap Cosines with 95% CI"
)

heatmap_path = os.path.join(
    FIG_DIR,
    "cosine_heatmap_with_CI.png"
)

plt.tight_layout()

plt.savefig(
    heatmap_path,
    dpi=300
)

plt.close()


# ============================================================
# Summary JSON
# ============================================================

summary = {

    "test_name":
        "Section Cosine Bootstrap",

    "version":
        "v1",

    "null_hypothesis": (
        "Observed section-section cosine "
        "similarities are unstable under "
        "folio resampling."
    ),

    "bootstrap_preserves": [
        "section membership",
        "folio-level feature covariance",
        "register-cell inventory",
        "within-section structure"
    ],

    "bootstrap_destroys": [
        "exact folio composition",
        "dependence on any single folio"
    ],

    "n_bootstraps":
        N_BOOTSTRAPS,

    "seed":
        SEED,

    "n_sections":
        len(sections),

    "n_folios":
        int(folio_cell.shape[0]),

    "n_cells":
        int(folio_cell.shape[1]),

    "ci_excluding_zero":
        ci_excludes_zero,

    "non_overlapping_ci_pairs":
        non_overlapping_pairs,

    "cell_statistics":
        {
            f"{s1}__{s2}": {
                "mean":
                    cell_stats[(s1, s2)]["mean"],
                "ci_low":
                    cell_stats[(s1, s2)]["ci_low"],
                "ci_high":
                    cell_stats[(s1, s2)]["ci_high"]
            }
            for (s1, s2) in cell_stats
        },

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "input_files": {
        f: sha256_file(f)
        for f in INPUT_FILES
    },

    "library_versions": {
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "matplotlib": plt.matplotlib.__version__,
        "seaborn": sns.__version__
    }
}

summary_path = os.path.join(
    OUTPUT_DIR,
    "summary.json"
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

artifact_paths = [
    bootstrap_csv_path,
    summary_path,
    heatmap_path
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

print("\n====================================================")
print("COMPLETE")
print("====================================================")

print(
    f"Output directory: "
    f"{OUTPUT_DIR}"
)

print("Artifacts written:")
print("  - bootstrap_cosines.csv")
print("  - summary.json")
print("  - checksums.json")
print("  - figures/cosine_heatmap_with_CI.png")

print("====================================================\n")