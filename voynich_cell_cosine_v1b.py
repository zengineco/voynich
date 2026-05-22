#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 3B: Forced k=3 Cell Clustering Audit

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Audit the visually apparent 3-branch structure in the productive
cell cosine dendrogram and compare it against the independently
derived May-18 macro-strata partition.

RATIONALE
=========
Test 3 selected k=2 under self-bootstrap ARI optimization.
However, self-bootstrap ARI penalizes continuous-with-poles
structure because broad continua are artificially favored over
meaningful mesoscopic partitions.

This audit:
    - forces k=3 from the original Ward linkage,
    - evaluates correspondence to the independent May-18 partition,
    - compares k=2 vs k=3 using external-ground-truth ARI,
    - reruns modularity null tests on the k=3 partition.

NULL HYPOTHESIS
===============
The observed k=3 partition does not exceed random modularity
expectations and does not meaningfully correspond to the
May-18 macro-strata partition.

INPUTS
======
Required files:
- MASTER_TOKEN_MATRIX.xlsx
- func_extended_communities.csv

Required sheet:
- tokens_atomic

REQUIRED COLUMNS
================
MASTER_TOKEN_MATRIX.xlsx:
- folio
- section
- cell_id

func_extended_communities.csv:
- node
- community

OUTPUTS
=======
Creates:
    voynich_cell_cosine_v1b/

Artifacts:
- cluster_assignments.csv
- branch_breakdown.csv
- modularity_null.csv
- summary.json
- checksums.json
- figures/dendrogram_k3.png
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

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_cell_cosine_v1b"
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


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH CELL COSINE CLUSTERING V1B")
print("====================================================\n")

ensure_dirs()


# ============================================================
# Load Inputs
# ============================================================

INPUT_FILES = [
    "MASTER_TOKEN_MATRIX.xlsx",
    "func_extended_communities.csv"
]

print("[1/10] Loading input files...")

for f in INPUT_FILES:

    if not os.path.exists(f):

        raise FileNotFoundError(
            f"Missing required input file: {f}"
        )

token_df = pd.read_excel(
    "MASTER_TOKEN_MATRIX.xlsx",
    sheet_name="tokens_atomic"
)

community_df = pd.read_csv(
    "func_extended_communities.csv"
)

print(
    f"Loaded MASTER_TOKEN_MATRIX.xlsx "
    f"({len(token_df)} rows)"
)

print(
    f"Loaded func_extended_communities.csv "
    f"({len(community_df)} rows)"
)


# ============================================================
# Detect Columns
# ============================================================

print("\n[2/10] Detecting columns...")

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

node_col = detect_column(
    community_df,
    ["node"]
)

community_col = detect_column(
    community_df,
    ["community"]
)

print(f"Detected folio column: {folio_col}")
print(f"Detected section column: {section_col}")
print(f"Detected cell column: {cell_col}")


# ============================================================
# Filter Productive Cells
# ============================================================

print("\n[3/10] Filtering productive cells...")

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

print("\n[4/10] Constructing matrices...")

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
# Cosine + Linkage
# ============================================================

print("\n[5/10] Computing linkage...")

cos_matrix = cosine_similarity(
    cell_profiles.values
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


# ============================================================
# Force k=3
# ============================================================

print("\n[6/10] Forcing k=3 partition...")

labels_k3 = fcluster(
    linkage_matrix,
    3,
    criterion="maxclust"
)

labels_k2 = fcluster(
    linkage_matrix,
    2,
    criterion="maxclust"
)

cluster_df = pd.DataFrame({
    "cell_id": cell_names,
    "cluster_k3": labels_k3,
    "cluster_k2": labels_k2
})

cluster_csv_path = os.path.join(
    OUTPUT_DIR,
    "cluster_assignments.csv"
)

cluster_df.to_csv(
    cluster_csv_path,
    index=False
)

print(
    "Cluster sizes k=3:"
)

print(
    cluster_df["cluster_k3"]
    .value_counts()
    .sort_index()
)


# ============================================================
# Branch Breakdown
# ============================================================

print("\n[7/10] Computing branch breakdown...")

rows = []

for cell, cluster in zip(
    cell_names,
    labels_k3
):

    parsed = parse_cell(cell)

    rows.append({
        "cell_id": cell,
        "cluster": cluster,
        "prefix": parsed["prefix"],
        "grade": parsed["grade"],
        "axis": parsed["axis"]
    })

branch_df = pd.DataFrame(rows)

branch_csv_path = os.path.join(
    OUTPUT_DIR,
    "branch_breakdown.csv"
)

branch_df.to_csv(
    branch_csv_path,
    index=False
)


# ============================================================
# Compare to May-18 Partition
# ============================================================

print("\n[8/10] Comparing to May-18 partition...")

community_map = dict(
    zip(
        community_df[node_col],
        community_df[community_col]
    )
)

shared_cells = [
    c for c in cell_names
    if c in community_map
]

shared_idx = [
    i for i, c in enumerate(cell_names)
    if c in shared_cells
]

truth_labels = [
    community_map[c]
    for c in shared_cells
]

k2_labels_shared = [
    labels_k2[i]
    for i in shared_idx
]

k3_labels_shared = [
    labels_k3[i]
    for i in shared_idx
]

ari_k2 = adjusted_rand_score(
    truth_labels,
    k2_labels_shared
)

ari_k3 = adjusted_rand_score(
    truth_labels,
    k3_labels_shared
)

print(f"ARI k=2 vs May-18: {ari_k2:.4f}")
print(f"ARI k=3 vs May-18: {ari_k3:.4f}")


# ============================================================
# Modularity Null
# ============================================================

print("\n[9/10] Running modularity null...")

observed_modularity = compute_graph_modularity(
    cos_matrix,
    labels_k3,
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
        labels_k3,
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

print("\n[10/10] Writing figures...")

# Dendrogram

plt.figure(figsize=(18, 8))

dendrogram(
    linkage_matrix,
    labels=cell_names,
    leaf_rotation=90,
    leaf_font_size=6,
    color_threshold=None
)

plt.title(
    "Forced k=3 Ward Dendrogram"
)

plt.tight_layout()

dendrogram_path = os.path.join(
    FIG_DIR,
    "dendrogram_k3.png"
)

plt.savefig(
    dendrogram_path,
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
    "Null Distribution of k=3 Modularity"
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
        "Cell Cosine Clustering v1b",

    "version":
        "v1b",

    "forced_k":
        3,

    "cluster_sizes_k3":
        (
            cluster_df["cluster_k3"]
            .value_counts()
            .sort_index()
            .to_dict()
        ),

    "ari_k2_vs_may18":
        float(ari_k2),

    "ari_k3_vs_may18":
        float(ari_k3),

    "stability_k3_materially_higher":
        bool(ari_k3 > ari_k2),

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
    cluster_csv_path,
    branch_csv_path,
    modularity_csv_path,
    summary_path,
    dendrogram_path,
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
print("  - cluster_assignments.csv")
print("  - branch_breakdown.csv")
print("  - modularity_null.csv")
print("  - summary.json")
print("  - checksums.json")
print("  - figures/dendrogram_k3.png")
print("  - figures/modularity_null.png")

print("====================================================\n")