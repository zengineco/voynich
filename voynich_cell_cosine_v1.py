#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 3: Cell × Cell Cosine Matrix with Hierarchical Clustering

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Evaluate whether productive register cells form statistically
non-random clusters based on their section-distribution profiles.

NULL HYPOTHESIS
===============
Observed clustering structure among productive cells does not
exceed what would be expected from random reassignment of
cell→section distributions while preserving cell marginal
frequencies.

ANALYSIS OVERVIEW
=================
1. Construct folio × cell matrix from MASTER_TOKEN_MATRIX.xlsx
2. Aggregate productive cells by section
3. Build cell × section normalized profile matrix
4. Compute 130 × 130 cosine similarity matrix
5. Perform Ward hierarchical clustering
6. Bootstrap folios within sections 1,000 times
7. Select cluster count maximizing bootstrap stability
8. Compute observed modularity
9. Compare against null distribution from shuffled
   cell→section assignments preserving cell marginals

BOOTSTRAP PRESERVES
===================
- Section membership
- Folio-level feature covariance
- Cell marginal frequencies
- Section sizes

BOOTSTRAP DESTROYS
==================
- Dependence on specific folios
- Exact folio composition per section

NULL SHUFFLE PRESERVES
======================
- Cell marginal totals
- Section marginal totals

NULL SHUFFLE DESTROYS
=====================
- Structured cell→section association

WHAT THIS SCRIPT DOES TEST
==========================
- Stability of productive-cell clustering
- Whether observed modularity exceeds frequency-matched nulls

WHAT THIS SCRIPT DOES NOT TEST
==============================
- Semantics
- Decipherment
- Causal interpretation
- Alternative tokenizers

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
    voynich_cell_cosine_v1/

Artifacts:
- cell_cosine_matrix.csv
- cluster_assignments.csv
- modularity_null.csv
- summary.json
- checksums.json
- figures/dendrogram.png
- figures/cosine_heatmap.png
- figures/modularity_null.png

DEPENDENCIES
============
- pandas
- numpy
- scipy
- scikit-learn
- matplotlib
- seaborn
- networkx
- openpyxl

USAGE
=====
Run locally from directory containing required input files:

    python voynich_cell_cosine_v1.py
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
import networkx as nx

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

from networkx.algorithms.community import modularity


# ============================================================
# Constants
# ============================================================

SEED = 42

N_BOOTSTRAPS = 1000
N_NULLS = 1000

MIN_CLUSTERS = 2
MAX_CLUSTERS = 20

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_cell_cosine_v1"
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


def compute_section_profiles(
    folio_cell,
    folio_sections,
    sections
):
    """
    Build cell × section normalized matrix.
    """

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


def cluster_labels_from_k(linkage_matrix, k):

    return fcluster(
        linkage_matrix,
        k,
        criterion="maxclust"
    )


def labels_to_communities(labels, items):

    communities = {}

    for item, label in zip(items, labels):

        communities.setdefault(
            label,
            set()
        ).add(item)

    return list(communities.values())


def compute_graph_modularity(
    cosine_matrix,
    labels,
    nodes
):
    """
    Weighted graph modularity.
    """

    G = nx.Graph()

    for node in nodes:
        G.add_node(node)

    for i in range(len(nodes)):

        for j in range(i + 1, len(nodes)):

            weight = cosine_matrix[i, j]

            if weight > 0:

                G.add_edge(
                    nodes[i],
                    nodes[j],
                    weight=float(weight)
                )

    communities = labels_to_communities(
        labels,
        nodes
    )

    return modularity(
        G,
        communities,
        weight="weight"
    )


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH CELL COSINE CLUSTERING V1")
print("====================================================\n")

ensure_dirs()


# ============================================================
# Load Data
# ============================================================

INPUT_FILES = [
    "MASTER_TOKEN_MATRIX.xlsx"
]

print("[1/11] Loading input file...")

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

print("\n[2/11] Detecting required columns...")

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

print("\n[3/11] Filtering productive cells...")

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
# Construct Folio × Cell Matrix
# ============================================================

print("\n[4/11] Constructing folio × cell matrix...")

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

print(
    f"Final matrix shape: "
    f"{folio_cell.shape}"
)

print(
    f"Detected sections: "
    f"{sections}"
)


# ============================================================
# Compute Cell Profiles
# ============================================================

print("\n[5/11] Computing section-distribution profiles...")

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
# Cosine Matrix
# ============================================================

print("\n[6/11] Computing cell cosine matrix...")

cos_matrix = cosine_similarity(
    cell_profiles.values
)

# Numerical stabilization

cos_matrix = np.clip(
    cos_matrix,
    -1.0,
    1.0
)

cos_df = pd.DataFrame(
    cos_matrix,
    index=cell_names,
    columns=cell_names
)

cosine_csv_path = os.path.join(
    OUTPUT_DIR,
    "cell_cosine_matrix.csv"
)

cos_df.to_csv(cosine_csv_path)

print(
    f"Cosine matrix shape: "
    f"{cos_df.shape}"
)


# ============================================================
# Hierarchical Clustering
# ============================================================

print("\n[7/11] Running Ward clustering...")

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


# ============================================================
# Bootstrap Stability
# ============================================================

print("\n[8/11] Estimating bootstrap stability...")

stability_scores = {}

for k in range(
    MIN_CLUSTERS,
    MAX_CLUSTERS + 1
):

    observed_labels = cluster_labels_from_k(
        linkage_matrix,
        k
    )

    ari_scores = []

    for b in range(N_BOOTSTRAPS):

        sampled_folios = []

        for sec in sections:

            sec_folios = folio_sections[
                folio_sections == sec
            ].index.tolist()

            sampled = np.random.choice(
                sec_folios,
                size=len(sec_folios),
                replace=True
            )

            sampled_folios.extend(sampled)

        boot_folio_cell = folio_cell.loc[
            sampled_folios
        ]

        boot_sections = folio_sections.loc[
            sampled_folios
        ]

        boot_profiles = compute_section_profiles(
            boot_folio_cell,
            boot_sections,
            sections
        )

        boot_cos = cosine_similarity(
            boot_profiles.values
        )

        # Numerical stabilization

        boot_cos = np.clip(
            boot_cos,
            -1.0,
            1.0
        )

        boot_dist = 1 - boot_cos

        boot_dist = np.clip(
            boot_dist,
            0.0,
            None
        )

        np.fill_diagonal(
            boot_dist,
            0
        )

        boot_condensed = squareform(
            boot_dist,
            checks=False
        )

        boot_linkage = linkage(
            boot_condensed,
            method="ward"
        )

        boot_labels = cluster_labels_from_k(
            boot_linkage,
            k
        )

        ari = adjusted_rand_score(
            observed_labels,
            boot_labels
        )

        ari_scores.append(ari)

        if (
            k == MIN_CLUSTERS
            and
            (b + 1) % 100 == 0
        ):

            print(
                f"Bootstrap "
                f"{b + 1}/{N_BOOTSTRAPS}"
            )

    stability_scores[k] = float(
        np.mean(ari_scores)
    )

best_k = max(
    stability_scores,
    key=stability_scores.get
)

stability_score = stability_scores[best_k]

print(
    f"Chosen cluster count: {best_k}"
)

print(
    f"Stability score: "
    f"{stability_score:.4f}"
)

observed_labels = cluster_labels_from_k(
    linkage_matrix,
    best_k
)


# ============================================================
# Cluster Assignments
# ============================================================

print("\n[9/11] Writing cluster assignments...")

cluster_df = pd.DataFrame({
    "cell_id": cell_names,
    "cluster": observed_labels
})

cluster_csv_path = os.path.join(
    OUTPUT_DIR,
    "cluster_assignments.csv"
)

cluster_df.to_csv(
    cluster_csv_path,
    index=False
)


# ============================================================
# Observed Modularity
# ============================================================

print("\n[10/11] Computing modularity null...")

observed_modularity = compute_graph_modularity(
    cos_matrix,
    observed_labels,
    cell_names
)

null_modularities = []

cell_totals = (
    cell_profiles.sum(axis=1)
)

section_totals = (
    cell_profiles.sum(axis=0)
)

for i in range(N_NULLS):

    shuffled_profiles = []

    for total in cell_totals:

        probs = (
            section_totals
            / section_totals.sum()
        )

        shuffled = np.random.multinomial(
            int(total),
            probs
        )

        shuffled_profiles.append(shuffled)

    shuffled_profiles = np.array(
        shuffled_profiles
    )

    null_cos = cosine_similarity(
        shuffled_profiles
    )

    null_cos = np.clip(
        null_cos,
        -1.0,
        1.0
    )

    null_mod = compute_graph_modularity(
        null_cos,
        observed_labels,
        cell_names
    )

    null_modularities.append(
        null_mod
    )

    if (i + 1) % 100 == 0:

        print(
            f"Null "
            f"{i + 1}/{N_NULLS}"
        )

null_modularities = np.array(
    null_modularities
)

null_mean = float(
    np.mean(null_modularities)
)

null_std = float(
    np.std(null_modularities)
)

z_score = float(
    (
        observed_modularity
        - null_mean
    ) / null_std
)

p_value = float(
    (
        np.sum(
            null_modularities
            >= observed_modularity
        ) + 1
    ) / (N_NULLS + 1)
)

modularity_df = pd.DataFrame({
    "iteration": np.arange(
        1,
        N_NULLS + 1
    ),
    "modularity": null_modularities
})

modularity_csv_path = os.path.join(
    OUTPUT_DIR,
    "modularity_null.csv"
)

modularity_df.to_csv(
    modularity_csv_path,
    index=False
)


# ============================================================
# Figures
# ============================================================

print("\n[11/11] Writing figures...")

# Dendrogram

plt.figure(figsize=(18, 8))

dendrogram(
    linkage_matrix,
    labels=cell_names,
    leaf_rotation=90,
    leaf_font_size=6
)

plt.title(
    "Ward Hierarchical Clustering "
    "of Productive Cells"
)

plt.tight_layout()

dendrogram_path = os.path.join(
    FIG_DIR,
    "dendrogram.png"
)

plt.savefig(
    dendrogram_path,
    dpi=300
)

plt.close()

# Heatmap

plt.figure(figsize=(14, 12))

sns.heatmap(
    cos_df,
    cmap="viridis",
    square=True
)

plt.title(
    "Cell × Cell Cosine Similarity Matrix"
)

plt.tight_layout()

heatmap_path = os.path.join(
    FIG_DIR,
    "cosine_heatmap.png"
)

plt.savefig(
    heatmap_path,
    dpi=300
)

plt.close()

# Modularity Null

plt.figure(figsize=(10, 6))

plt.hist(
    null_modularities,
    bins=40,
    alpha=0.8
)

plt.axvline(
    observed_modularity,
    linestyle="--",
    linewidth=3,
    label=(
        f"Observed = "
        f"{observed_modularity:.3f}"
    )
)

plt.xlabel("Modularity")
plt.ylabel("Frequency")

plt.title(
    "Null Distribution of Cluster Modularity"
)

plt.legend()

plt.tight_layout()

modularity_fig_path = os.path.join(
    FIG_DIR,
    "modularity_null.png"
)

plt.savefig(
    modularity_fig_path,
    dpi=300
)

plt.close()


# ============================================================
# Summary JSON
# ============================================================

summary = {

    "test_name":
        "Cell Cosine Clustering",

    "version":
        "v1",

    "null_hypothesis": (
        "Observed clustering structure "
        "does not exceed random "
        "cell→section organization."
    ),

    "n_clusters_chosen":
        int(best_k),

    "observed_modularity":
        float(observed_modularity),

    "null_mean":
        null_mean,

    "null_std":
        null_std,

    "z_score":
        z_score,

    "p_value":
        p_value,

    "stability_score":
        stability_score,

    "bootstrap_stability_by_k":
        stability_scores,

    "n_bootstraps":
        N_BOOTSTRAPS,

    "n_nulls":
        N_NULLS,

    "n_cells":
        int(len(cell_names)),

    "n_sections":
        int(len(sections)),

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
        "seaborn": sns.__version__,
        "networkx": nx.__version__
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
    cosine_csv_path,
    cluster_csv_path,
    modularity_csv_path,
    summary_path,
    dendrogram_path,
    heatmap_path,
    modularity_fig_path
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
print("  - cell_cosine_matrix.csv")
print("  - cluster_assignments.csv")
print("  - modularity_null.csv")
print("  - summary.json")
print("  - checksums.json")
print("  - figures/dendrogram.png")
print("  - figures/cosine_heatmap.png")
print("  - figures/modularity_null.png")

print("====================================================\n")