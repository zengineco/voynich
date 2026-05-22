#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 3D: TF-IDF Grade-Stratum Confirmatory Test

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Test whether the eo-dominant TF-IDF cluster loads preferentially
onto pharm-herbal beyond chance expectation.

BACKGROUND
==========
Test 3C found:
    - cross-normalization instability between L2 and TF-IDF
    - but a potentially meaningful TF-IDF grade partition:
        * bare/e-dominant
        * o-dominant
        * eo-dominant

This test evaluates whether the eo-dominant cluster preferentially
loads on pharm-herbal, corroborating:
    - May 18 function+eo-recipe stratum
    - Battery D pharm finding:
        eo-grade is recipe-exclusive

NULL HYPOTHESIS
===============
Observed eo-cluster loading on pharm-herbal is achievable by
random assignment of cells to clusters.

PERMUTATION NULL
================
Preserves:
    - cluster sizes
    - section profile structure
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
    voynich_cell_cosine_v1d/

Artifacts:
- tfidf_cluster_assignments.csv
- cluster_section_loadings.csv
- permutation_null.csv
- summary.json
- checksums.json
- figures/section_loading_heatmap.png
- figures/permutation_null.png

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

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_cell_cosine_v1d"
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

    parts = str(cell).split("_")

    if len(parts) >= 2:
        return parts[1]

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
print("VOYNICH CELL COSINE V1D")
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
# Identify eo-dominant Cluster
# ============================================================

print("\n[6/9] Identifying eo-dominant cluster...")

grade_props = []

for cluster in sorted(cluster_df["cluster"].unique()):

    subset = cluster_df[
        cluster_df["cluster"] == cluster
    ]

    eo_prop = np.mean(
        subset["grade"] == "eo"
    )

    grade_props.append({
        "cluster": cluster,
        "eo_prop": eo_prop
    })

grade_props = pd.DataFrame(
    grade_props
)

eo_cluster = int(
    grade_props.sort_values(
        "eo_prop",
        ascending=False
    ).iloc[0]["cluster"]
)

print(
    f"Detected eo-dominant cluster: "
    f"{eo_cluster}"
)


# ============================================================
# Section Loadings
# ============================================================

print("\n[7/9] Computing section loadings...")

loading_rows = []

cluster_loadings = {}

for cluster in sorted(cluster_df["cluster"].unique()):

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

eo_pharm_loading = float(
    cluster_loadings[eo_cluster][
        "pharm-herbal"
    ]
)

print(
    f"eo-cluster pharm-herbal loading: "
    f"{eo_pharm_loading:.6f}"
)


# ============================================================
# Permutation Null
# ============================================================

print("\n[8/9] Running permutation null...")

null_loadings = []

cluster_sizes = (
    cluster_df["cluster"]
    .value_counts()
    .sort_index()
)

cell_array = np.array(
    cell_names
)

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

    loading = float(
        mean_vector["pharm-herbal"]
    )

    null_loadings.append(loading)

    if (i + 1) % 100 == 0:

        print(
            f"Null "
            f"{i + 1}/{N_NULLS}"
        )

null_loadings = np.array(
    null_loadings
)

null_mean = float(
    np.mean(null_loadings)
)

null_std = float(
    np.std(null_loadings)
)

z_score = float(
    (
        eo_pharm_loading
        - null_mean
    ) / null_std
)

p_value = float(
    (
        np.sum(
            null_loadings >= eo_pharm_loading
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
    "pharm_loading":
        null_loadings
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

# Section loading heatmap

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

# Permutation null

plt.figure(figsize=(10, 6))

plt.hist(
    null_loadings,
    bins=40,
    alpha=0.8
)

plt.axvline(
    eo_pharm_loading,
    linestyle="--",
    linewidth=3,
    label=(
        f"Observed = "
        f"{eo_pharm_loading:.3f}"
    )
)

plt.xlabel(
    "pharm-herbal Loading"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Permutation Null: eo-cluster "
    "→ pharm-herbal Loading"
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
        "TF-IDF Grade-Stratum Confirmatory Test",

    "version":
        "v1d",

    "eo_cluster":
        eo_cluster,

    "eo_cluster_pharm_loading":
        eo_pharm_loading,

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

    "cluster_sizes": (
        cluster_df["cluster"]
        .value_counts()
        .sort_index()
        .to_dict()
    ),

    "eo_grade_proportions": {
        str(row["cluster"]):
            float(row["eo_prop"])
        for _, row in grade_props.iterrows()
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