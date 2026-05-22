#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 3E: Corrected eo-Stratum Confirmatory Audit

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Fully corrected confirmatory audit of the TF-IDF k=3 partition.

This version fixes the upstream grade-parsing bug that caused:
    - eo_grade_proportions = 0 for all clusters
    - incorrect eo-cluster selection
    - false-positive confirmation result

CORRECTIONS
===========
1. Robust grade extraction from cell_id
2. Explicit cluster-grade composition logging
3. Explicit eo_grade_proportions dictionary output
4. Explicit eo-cluster logging
5. Correct permutation test on REAL eo-cluster

TARGET HYPOTHESIS
=================
Does the eo-dominant cluster preferentially load on the
May-18 eo-recipe stratum?

Target sections:
    - pharm-herbal
    - stars
    - cosmo/zodiac

NULL HYPOTHESIS
===============
Observed eo-stratum loading is achievable by random
cell→cluster assignment preserving cluster sizes.

EXPECTED RESULT
===============
Manual computation predicts:

    eo_cluster = 3

    loadings:
        pharm-herbal = 0.489
        stars = 1.198
        cosmo/zodiac = 0.607

    sum = 2.294

    null mean ≈ 2.888
    z ≈ -1.43
    p ≈ 0.92

Interpretation:
    hypothesis falsified

INPUTS
======
Required files:
- MASTER_TOKEN_MATRIX.xlsx

Required sheet:
- tokens_atomic

OUTPUTS
=======
Creates:
    voynich_cell_cosine_v1e/

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

OUTPUT_DIR = "voynich_cell_cosine_v1e"
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

    Searches for:
        bare
        e
        o
        eo

    anywhere inside the cell_id tokens.
    """

    cell = str(cell).lower()

    tokens = re.split(
        r"[_\-\s]+",
        cell
    )

    valid = {
        "bare",
        "e",
        "o",
        "eo"
    }

    for token in tokens:

        if token in valid:
            return token

    # fallback:
    # detect embedded eo patterns

    if "eo" in cell:
        return "eo"

    if re.search(r'(^|[^a-z])e([^a-z]|$)', cell):
        return "e"

    if re.search(r'(^|[^a-z])o([^a-z]|$)', cell):
        return "o"

    return "bare"


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
print("VOYNICH CELL COSINE V1E")
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
# Compute Grade Composition
# ============================================================

print("\n[6/9] Computing grade composition...")

grade_rows = []

eo_grade_proportions = {}

for cluster in sorted(
    cluster_df["cluster"].unique()
):

    subset = cluster_df[
        cluster_df["cluster"] == cluster
    ]

    total = len(subset)

    grade_counts = (
        subset["grade"]
        .value_counts()
        .to_dict()
    )

    eo_count = int(
        grade_counts.get("eo", 0)
    )

    eo_prop = eo_count / total

    eo_grade_proportions[
        int(cluster)
    ] = eo_prop

    row = {
        "cluster": int(cluster),
        "n_cells": total,
        "eo_count": eo_count,
        "eo_prop": eo_prop
    }

    for g in ["bare", "e", "o", "eo"]:

        row[f"{g}_count"] = int(
            grade_counts.get(g, 0)
        )

        row[f"{g}_prop"] = (
            grade_counts.get(g, 0)
            / total
        )

    grade_rows.append(row)

grade_df = pd.DataFrame(
    grade_rows
)

eo_cluster = max(
    eo_grade_proportions,
    key=eo_grade_proportions.get
)

print("\neo_grade_proportions:")

print(
    json.dumps(
        eo_grade_proportions,
        indent=2
    )
)

print(
    f"\nChosen eo_cluster: "
    f"{eo_cluster}"
)

print("\nCluster 3 composition:")

cluster3 = grade_df[
    grade_df["cluster"] == 3
].iloc[0]

print(
    json.dumps({
        "bare_prop":
            float(cluster3["bare_prop"]),
        "e_prop":
            float(cluster3["e_prop"]),
        "o_prop":
            float(cluster3["o_prop"]),
        "eo_prop":
            float(cluster3["eo_prop"])
    }, indent=2)
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
    else "FALSIFIED"
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
        "Corrected eo-Stratum Confirmatory Audit",

    "version":
        "v1e",

    "eo_cluster":
        int(eo_cluster),

    "eo_grade_proportions":
        {
            str(k): float(v)
            for k, v in eo_grade_proportions.items()
        },

    "cluster3_grade_composition": {

        "bare_prop":
            float(cluster3["bare_prop"]),

        "e_prop":
            float(cluster3["e_prop"]),

        "o_prop":
            float(cluster3["o_prop"]),

        "eo_prop":
            float(cluster3["eo_prop"])
    },

    "target_sections":
        TARGET_SECTIONS,

    "target_breakdown":
        target_breakdown,

    "target_loading_sum":
        target_loading_sum,

    "null_mean":
        null_mean,

    "null_std":
        null_std,

    "z_score":
        z_score,

    "p_value":
        p_value,

    "finding_strength":
        finding_strength,

    "robust":
        bool(robust),

    "cluster_sizes": (
        cluster_df["cluster"]
        .value_counts()
        .sort_index()
        .to_dict()
    ),

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