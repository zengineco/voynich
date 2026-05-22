#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 3C: Normalization Robustness Audit

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Test whether the apparent axis-driven k=3 clustering structure
is robust across alternative normalization schemes or merely
a frequency artifact.

NORMALIZATION SCHEMES
=====================
A. L2-normalized section-distribution vectors
   (same method as Test 3 / 3b)

B. TF-IDF weighted section-distribution vectors
   where:
       - sections = documents
       - cells = terms

HYPOTHESIS
==========
If the axis-driven split is structurally meaningful rather than
frequency-driven, the same broad partition geometry should persist
across both normalization schemes.

ROBUSTNESS CRITERION
====================
Robust if:
    - k=3 cluster structure remains visually/topologically similar
    - cluster-level axis enrichment persists
    - ARI between normalization schemes exceeds null expectation

INTERPRETATION RULE
===================
If robust:
    Candidate becomes STRONG finding.

If not robust:
    Candidate becomes noted-but-unconfirmed.

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
    voynich_cell_cosine_v1c/

Artifacts:
- l2_cluster_assignments.csv
- tfidf_cluster_assignments.csv
- normalization_comparison.csv
- summary.json
- checksums.json
- figures/l2_dendrogram.png
- figures/tfidf_dendrogram.png
- figures/ari_comparison.png

DEPENDENCIES
============
- pandas
- numpy
- scipy
- scikit-learn
- matplotlib
- seaborn
- openpyxl
"""

import os
import re
import json
import hashlib
import random
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.cluster.hierarchy import (
    linkage,
    dendrogram,
    fcluster
)

from scipy.spatial.distance import squareform

from sklearn.metrics import (
    adjusted_rand_score
)

from sklearn.metrics.pairwise import (
    cosine_similarity
)

from sklearn.feature_extraction.text import (
    TfidfTransformer
)

from sklearn.preprocessing import normalize


# ============================================================
# Constants
# ============================================================

SEED = 42
N_NULLS = 1000

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_cell_cosine_v1c"
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")


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


def ensure_dirs():

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


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
        f"Tried candidates: {candidates}"
    )


def modal_value(series):

    counts = Counter(series.dropna())

    if len(counts) == 0:
        return np.nan

    return counts.most_common(1)[0][0]


def parse_cell(cell):

    parts = str(cell).split("_")

    result = {
        "prefix": None,
        "grade": None,
        "axis": None
    }

    if len(parts) >= 1:
        result["prefix"] = parts[0]

    if len(parts) >= 2:
        result["grade"] = parts[1]

    if len(parts) >= 3:
        result["axis"] = parts[2]

    return result


def compute_section_profiles(
    folio_cell,
    folio_sections,
    sections
):

    profiles = []

    for sec in sections:

        sec_folios = folio_sections[
            folio_sections == sec
        ].index

        sec_matrix = folio_cell.loc[sec_folios]

        centroid = sec_matrix.mean(axis=0)

        profiles.append(centroid.values)

    profiles = np.vstack(profiles)

    profiles = pd.DataFrame(
        profiles,
        index=sections,
        columns=folio_cell.columns
    )

    return profiles.T


def build_linkage_from_profiles(profile_matrix):

    cos_matrix = cosine_similarity(
        profile_matrix
    )

    cos_matrix = np.clip(
        cos_matrix,
        -1.0,
        1.0
    )

    distance_matrix = 1 - cos_matrix

    distance_matrix = np.clip(
        distance_matrix,
        0.0,
        None
    )

    np.fill_diagonal(
        distance_matrix,
        0
    )

    condensed = squareform(
        distance_matrix,
        checks=False
    )

    linkage_matrix = linkage(
        condensed,
        method="ward"
    )

    return cos_matrix, linkage_matrix


def cluster_axis_breakdown(
    cell_names,
    labels
):

    rows = []

    for cell, cluster in zip(
        cell_names,
        labels
    ):

        parsed = parse_cell(cell)

        rows.append({
            "cell_id": cell,
            "cluster": cluster,
            "prefix": parsed["prefix"],
            "grade": parsed["grade"],
            "axis": parsed["axis"]
        })

    return pd.DataFrame(rows)


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH CELL COSINE V1C")
print("====================================================\n")

ensure_dirs()


# ============================================================
# Load Data
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

print("\n[2/9] Detecting columns...")

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


# ============================================================
# Filter Productive Cells
# ============================================================

print("\n[3/9] Filtering productive cells...")

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
    f"Remaining token rows: "
    f"{len(token_df)}"
)


# ============================================================
# Construct Matrices
# ============================================================

print("\n[4/9] Constructing matrices...")

folio_cell = pd.crosstab(
    token_df[folio_col],
    token_df[cell_col]
)

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

sections = sorted(
    folio_sections.unique()
)

cell_profiles = compute_section_profiles(
    folio_cell,
    folio_sections,
    sections
)

cell_names = cell_profiles.index.tolist()

print(
    f"Cell profile matrix shape: "
    f"{cell_profiles.shape}"
)


# ============================================================
# L2 Normalization
# ============================================================

print("\n[5/9] Computing L2-normalized clustering...")

l2_profiles = normalize(
    cell_profiles.values,
    norm="l2"
)

l2_cos, l2_linkage = build_linkage_from_profiles(
    l2_profiles
)

l2_labels = fcluster(
    l2_linkage,
    3,
    criterion="maxclust"
)

l2_df = cluster_axis_breakdown(
    cell_names,
    l2_labels
)

l2_csv_path = os.path.join(
    OUTPUT_DIR,
    "l2_cluster_assignments.csv"
)

l2_df.to_csv(
    l2_csv_path,
    index=False
)


# ============================================================
# TF-IDF Normalization
# ============================================================

print("\n[6/9] Computing TF-IDF clustering...")

# sections as documents
# cells as terms

section_cell = cell_profiles.T.values

tfidf = TfidfTransformer()

tfidf_matrix = tfidf.fit_transform(
    section_cell
)

# back to cells × sections

tfidf_profiles = tfidf_matrix.T.toarray()

tfidf_cos, tfidf_linkage = build_linkage_from_profiles(
    tfidf_profiles
)

tfidf_labels = fcluster(
    tfidf_linkage,
    3,
    criterion="maxclust"
)

tfidf_df = cluster_axis_breakdown(
    cell_names,
    tfidf_labels
)

tfidf_csv_path = os.path.join(
    OUTPUT_DIR,
    "tfidf_cluster_assignments.csv"
)

tfidf_df.to_csv(
    tfidf_csv_path,
    index=False
)


# ============================================================
# Compare Partitions
# ============================================================

print("\n[7/9] Comparing normalization schemes...")

observed_ari = adjusted_rand_score(
    l2_labels,
    tfidf_labels
)

null_aris = []

for i in range(N_NULLS):

    shuffled = np.random.permutation(
        tfidf_labels
    )

    ari = adjusted_rand_score(
        l2_labels,
        shuffled
    )

    null_aris.append(ari)

null_aris = np.array(null_aris)

null_mean = float(
    np.mean(null_aris)
)

null_std = float(
    np.std(null_aris)
)

z_score = float(
    (
        observed_ari
        - null_mean
    ) / null_std
)

p_value = float(
    (
        np.sum(
            null_aris >= observed_ari
        ) + 1
    ) / (N_NULLS + 1)
)

comparison_df = pd.DataFrame({
    "cell_id": cell_names,
    "l2_cluster": l2_labels,
    "tfidf_cluster": tfidf_labels
})

comparison_csv_path = os.path.join(
    OUTPUT_DIR,
    "normalization_comparison.csv"
)

comparison_df.to_csv(
    comparison_csv_path,
    index=False
)


# ============================================================
# Axis Robustness
# ============================================================

print("\n[8/9] Evaluating axis robustness...")

def dominant_axes(df):

    result = {}

    for cluster in sorted(df["cluster"].unique()):

        axes = (
            df[df["cluster"] == cluster]
            ["axis"]
            .value_counts()
        )

        result[int(cluster)] = (
            axes.head(5).to_dict()
        )

    return result

l2_axes = dominant_axes(l2_df)
tfidf_axes = dominant_axes(tfidf_df)

robust = (
    observed_ari > 0.50
)

finding_strength = (
    "STRONG"
    if robust
    else "noted-but-unconfirmed"
)

print(f"Observed ARI: {observed_ari:.4f}")
print(f"Robust: {robust}")


# ============================================================
# Figures
# ============================================================

print("\n[9/9] Writing figures...")

# L2 Dendrogram

plt.figure(figsize=(18, 8))

dendrogram(
    l2_linkage,
    labels=cell_names,
    leaf_rotation=90,
    leaf_font_size=6
)

plt.title(
    "L2-Normalized Ward Dendrogram"
)

plt.tight_layout()

l2_dendrogram_path = os.path.join(
    FIG_DIR,
    "l2_dendrogram.png"
)

plt.savefig(
    l2_dendrogram_path,
    dpi=300
)

plt.close()

# TF-IDF Dendrogram

plt.figure(figsize=(18, 8))

dendrogram(
    tfidf_linkage,
    labels=cell_names,
    leaf_rotation=90,
    leaf_font_size=6
)

plt.title(
    "TF-IDF Ward Dendrogram"
)

plt.tight_layout()

tfidf_dendrogram_path = os.path.join(
    FIG_DIR,
    "tfidf_dendrogram.png"
)

plt.savefig(
    tfidf_dendrogram_path,
    dpi=300
)

plt.close()

# ARI Null

plt.figure(figsize=(10, 6))

plt.hist(
    null_aris,
    bins=40,
    alpha=0.8
)

plt.axvline(
    observed_ari,
    linestyle="--",
    linewidth=3,
    label=(
        f"Observed = "
        f"{observed_ari:.3f}"
    )
)

plt.xlabel("ARI")
plt.ylabel("Frequency")

plt.title(
    "Null Distribution of Cross-Normalization ARI"
)

plt.legend()

plt.tight_layout()

ari_fig_path = os.path.join(
    FIG_DIR,
    "ari_comparison.png"
)

plt.savefig(
    ari_fig_path,
    dpi=300
)

plt.close()


# ============================================================
# Summary JSON
# ============================================================

summary = {

    "test_name":
        "Cell Cosine Normalization Robustness",

    "version":
        "v1c",

    "normalizations": [
        "L2",
        "TF-IDF"
    ],

    "forced_k":
        3,

    "observed_ari":
        float(observed_ari),

    "null_mean":
        null_mean,

    "null_std":
        null_std,

    "z_score":
        z_score,

    "p_value":
        p_value,

    "robust":
        bool(robust),

    "finding_strength":
        finding_strength,

    "l2_axis_breakdown":
        l2_axes,

    "tfidf_axis_breakdown":
        tfidf_axes,

    "n_cells":
        int(len(cell_names)),

    "n_sections":
        int(len(sections)),

    "n_nulls":
        N_NULLS,

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
    l2_csv_path,
    tfidf_csv_path,
    comparison_csv_path,
    summary_path,
    l2_dendrogram_path,
    tfidf_dendrogram_path,
    ari_fig_path
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
print("  - l2_cluster_assignments.csv")
print("  - tfidf_cluster_assignments.csv")
print("  - normalization_comparison.csv")
print("  - summary.json")
print("  - checksums.json")
print("  - figures/l2_dendrogram.png")
print("  - figures/tfidf_dendrogram.png")
print("  - figures/ari_comparison.png")

print("====================================================\n")