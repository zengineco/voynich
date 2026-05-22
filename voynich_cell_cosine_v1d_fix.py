#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 3D FIX: eo-Stratum Confirmatory Audit

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Correct Test 3D eo-cluster detection and test whether the
eo-dominant TF-IDF cluster preferentially loads on the
May-18 "function+eo-recipe stratum":

    - pharm-herbal
    - stars
    - cosmo/zodiac

BACKGROUND
==========
Original Test 3D contained two bugs:

BUG 1
-----
eo-cluster detection selected the wrong cluster due to
broken grade parsing / proportion logic.

BUG 2
-----
eo_grade_proportions incorrectly returned zeros.

Correct observed proportions:
    cluster 1: 10% eo
    cluster 2: 10% eo
    cluster 3: 44% eo

This audit fixes:
    - grade parsing
    - eo proportion computation
    - eo-cluster identification

UPDATED PREDICTION
==================
The narrow prediction:
    eo → pharm-herbal

was falsified.

The broader prediction under test:

    eo-cluster preferentially loads on the
    May-18 eo-recipe stratum:
        {pharm-herbal, stars, cosmo/zodiac}

NULL HYPOTHESIS
===============
Observed eo-stratum loading is achievable by random
cell→cluster assignment.

PERMUTATION NULL
================
Preserves:
    - cluster sizes
    - section profile geometry
    - section totals

Destroys:
    - mapping between cells and cluster identity

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
    voynich_cell_cosine_v1d_fix/

Artifacts:
- tfidf_cluster_assignments.csv
- cluster_section_loadings.csv
- permutation_null.csv
- summary.json
- checksums.json
- figures/section_loading_heatmap.png
- figures/permutation_null.png
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

from scipy.cluster.hierarchy import (
    linkage,
    fcluster
)

from scipy.spatial.distance import squareform

from sklearn.metrics.pairwise import (
    cosine_similarity
)

from sklearn.feature_extraction.text import (
    TfidfTransformer
)


# ============================================================
# Constants
# ============================================================

SEED = 42
N_NULLS = 1000

TARGET_SECTIONS = [
    "pharm-herbal",
    "stars",
    "cosmo/zodiac"
]

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_cell_cosine_v1d_fix"
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


def parse_grade(cell):
    """
    Robust grade extraction.

    Expected patterns:
        prefix_grade_axis
    """

    parts = str(cell).split("_")

    if len(parts) >= 2:

        grade = parts[1].strip().lower()

        return grade

    return "unknown"


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


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH CELL COSINE V1D FIX")
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
# TF-IDF Clustering
# ============================================================

print("\n[5/9] Computing TF-IDF k=3 partition...")

section_cell = cell_profiles.T.values

tfidf = TfidfTransformer()

tfidf_matrix = tfidf.fit_transform(
    section_cell
)

tfidf_profiles = tfidf_matrix.T.toarray()

cos_matrix = cosine_similarity(
    tfidf_profiles
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

labels = fcluster(
    linkage_matrix,
    3,
    criterion="maxclust"
)

cluster_df = pd.DataFrame({
    "cell_id": cell_names,
    "cluster": labels
})

cluster_df["grade"] = (
    cluster_df["cell_id"]
    .apply(parse_grade)
)

cluster_csv_path = os.path.join(
    OUTPUT_DIR,
    "tfidf_cluster_assignments.csv"
)

cluster_df.to_csv(
    cluster_csv_path,
    index=False
)


# ============================================================
# Compute Correct eo Proportions
# ============================================================

print("\n[6/9] Computing eo proportions...")

grade_rows = []

for cluster in sorted(
    cluster_df["cluster"].unique()
):

    subset = cluster_df[
        cluster_df["cluster"] == cluster
    ]

    total = len(subset)

    eo_count = int(
        np.sum(
            subset["grade"] == "eo"
        )
    )

    eo_prop = eo_count / total

    grade_rows.append({
        "cluster": int(cluster),
        "n_cells": total,
        "eo_count": eo_count,
        "eo_prop": eo_prop
    })

grade_df = pd.DataFrame(
    grade_rows
)

eo_cluster = int(
    grade_df.sort_values(
        "eo_prop",
        ascending=False
    ).iloc[0]["cluster"]
)

print("\nCorrected eo proportions:")

for _, row in grade_df.iterrows():

    print(
        f"Cluster {int(row['cluster'])}: "
        f"{row['eo_prop']:.3f}"
    )

print(
    f"\nDetected eo-cluster: "
    f"{eo_cluster}"
)


# ============================================================
# Section Loadings
# ============================================================

print("\n[7/9] Computing section loadings...")

loading_rows = []

cluster_loadings = {}

for cluster in sorted(
    cluster_df["cluster"].unique()
):

    cells = cluster_df[
        cluster_df["cluster"] == cluster
    ]["cell_id"]

    subset = cell_profiles.loc[cells]

    mean_vector = subset.mean(axis=0)

    cluster_loadings[cluster] = mean_vector

    top_sections = (
        mean_vector
        .sort_values(ascending=False)
        .head(2)
        .index
        .tolist()
    )

    for sec in sections:

        loading_rows.append({
            "cluster": cluster,
            "section": sec,
            "mean_loading": float(
                mean_vector[sec]
            ),
            "top2":
                sec in top_sections
        })

loading_df = pd.DataFrame(
    loading_rows
)

loading_csv_path = os.path.join(
    OUTPUT_DIR,
    "cluster_section_loadings.csv"
)

loading_df.to_csv(
    loading_csv_path,
    index=False
)

eo_vector = cluster_loadings[
    eo_cluster
]

target_loading_sum = float(
    eo_vector[
        TARGET_SECTIONS
    ].sum()
)

target_breakdown = {
    sec: float(eo_vector[sec])
    for sec in TARGET_SECTIONS
}

print(
    "\nObserved eo-stratum loadings:"
)

for sec, val in target_breakdown.items():

    print(
        f"  {sec}: {val:.6f}"
    )

print(
    f"\nCombined loading sum: "
    f"{target_loading_sum:.6f}"
)


# ============================================================
# Permutation Null
# ============================================================

print("\n[8/9] Running permutation null...")

null_sums = []

for i in range(N_NULLS):

    shuffled = np.random.permutation(
        labels
    )

    shuffled_df = pd.DataFrame({
        "cell_id": cell_names,
        "cluster": shuffled
    })

    shuffled_cells = shuffled_df[
        shuffled_df["cluster"] == eo_cluster
    ]["cell_id"]

    subset = cell_profiles.loc[
        shuffled_cells
    ]

    mean_vector = subset.mean(axis=0)

    score = float(
        mean_vector[
            TARGET_SECTIONS
        ].sum()
    )

    null_sums.append(score)

    if (i + 1) % 100 == 0:

        print(
            f"Null "
            f"{i + 1}/{N_NULLS}"
        )

null_sums = np.array(
    null_sums
)

null_mean = float(
    np.mean(null_sums)
)

null_std = float(
    np.std(null_sums)
)

z_score = float(
    (
        target_loading_sum
        - null_mean
    ) / null_std
)

p_value = float(
    (
        np.sum(
            null_sums >= target_loading_sum
        ) + 1
    ) / (N_NULLS + 1)
)

robust = (
    p_value < 0.05
)

finding_strength = (
    "STRONG"
    if robust
    else "noted CANDIDATE"
)

null_df = pd.DataFrame({
    "iteration": np.arange(
        1,
        N_NULLS + 1
    ),
    "target_loading_sum":
        null_sums
})

null_csv_path = os.path.join(
    OUTPUT_DIR,
    "permutation_null.csv"
)

null_df.to_csv(
    null_csv_path,
    index=False
)


# ============================================================
# Figures
# ============================================================

print("\n[9/9] Writing figures...")

# Heatmap

heatmap_matrix = loading_df.pivot(
    index="cluster",
    columns="section",
    values="mean_loading"
)

plt.figure(figsize=(12, 6))

sns.heatmap(
    heatmap_matrix,
    annot=True,
    fmt=".3f",
    cmap="viridis"
)

plt.title(
    "Cluster × Section Mean Loadings"
)

plt.tight_layout()

heatmap_path = os.path.join(
    FIG_DIR,
    "section_loading_heatmap.png"
)

plt.savefig(
    heatmap_path,
    dpi=300
)

plt.close()

# Permutation Null

plt.figure(figsize=(10, 6))

plt.hist(
    null_sums,
    bins=40,
    alpha=0.8
)

plt.axvline(
    target_loading_sum,
    linestyle="--",
    linewidth=3,
    label=(
        f"Observed = "
        f"{target_loading_sum:.3f}"
    )
)

plt.xlabel(
    "Combined eo-Stratum Loading"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Permutation Null:\n"
    "eo-cluster → "
    "{pharm-herbal, stars, cosmo/zodiac}"
)

plt.legend()

plt.tight_layout()

null_fig_path = os.path.join(
    FIG_DIR,
    "permutation_null.png"
)

plt.savefig(
    null_fig_path,
    dpi=300
)

plt.close()


# ============================================================
# Summary JSON
# ============================================================

summary = {

    "test_name":
        "eo-Stratum Confirmatory Audit",

    "version":
        "v1d_fix",

    "eo_cluster":
        eo_cluster,

    "eo_grade_proportions": {
        str(int(row["cluster"])):
            float(row["eo_prop"])
        for _, row in grade_df.iterrows()
    },

    "target_sections":
        TARGET_SECTIONS,

    "target_loading_sum":
        target_loading_sum,

    "target_breakdown":
        target_breakdown,

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

    "cluster_sizes": (
        cluster_df["cluster"]
        .value_counts()
        .sort_index()
        .to_dict()
    ),

    "top_sections_by_cluster": {
        str(cluster): (
            cluster_loadings[cluster]
            .sort_values(ascending=False)
            .head(2)
            .index
            .tolist()
        )
        for cluster in cluster_loadings
    },

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
    cluster_csv_path,
    loading_csv_path,
    null_csv_path,
    summary_path,
    heatmap_path,
    null_fig_path
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
print("  - tfidf_cluster_assignments.csv")
print("  - cluster_section_loadings.csv")
print("  - permutation_null.csv")
print("  - summary.json")
print("  - checksums.json")
print("  - figures/section_loading_heatmap.png")
print("  - figures/permutation_null.png")

print("====================================================\n")