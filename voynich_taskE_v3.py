#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK E v3b
DIRECTED FUNC-EXTENDED MODULARITY
WITH REVISED NULL MODELS

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

Run reproducible modularity-vs-null testing on the
a-priori specified directed weighted FUNC-extended graph.

This version replaces the failed degree-preserving null
with two structurally appropriate null models.

============================================================
IMPORTANT
============================================================

The historical May-18 z=9.59 claim remains:

    NON-REPRODUCIBLE

This script establishes NEW findings only.

============================================================
OBSERVED GRAPH
============================================================

Directed weighted FUNC-extended transition graph

Nodes:
- 130 productive cells
- FUNC

Edges:
- weighted by transition count
- no thresholding
- no normalization
- FUNC-FUNC retained

============================================================
NULL MODELS
============================================================

NULL ER
-------
Erdos-Renyi density-matched null

Preserves:
- node count
- edge count
- approximate density

Destroys:
- topology
- degree structure
- communities
- weight organization

Question:
    does modularity exceed what density alone explains?

------------------------------------------------------------

NULL WEIGHT
-----------
Edge-weight shuffle null

Preserves:
- topology
- edge existence
- total weight distribution

Destroys:
- alignment between heavy weights and communities

Question:
    is modularity driven by weight organization?

------------------------------------------------------------

NULL SECTION
------------
Sequence-section permutation

Expected possibility:
- degenerate variance

Question:
    does section linkage contribute structure?

============================================================
INTERPRETATION
============================================================

z >= 9
-------
STRONG

5 <= z < 9
-----------
CANDIDATE

z < 5
------
NOT_ABOVE_CHANCE

============================================================
GUARDRAILS
============================================================

1. >=50 distinct null values
2. std(Q) > 1e-6
3. parser self-test
4. deterministic seeds
5. audit rows
6. halt on degenerate variance

============================================================
OUTPUT
============================================================

voynich_taskE_v3b/

FILES
=====

taskE_v3_sensitivity_sweep.csv
taskE_v3_directed_observed.json
taskE_v3_null_ER.csv
taskE_v3_null_weight_shuffle.csv
taskE_v3_null_section.csv
taskE_v3_summary.json
checksums.json

FIGURES
=======

null_ER_histogram.png
null_weight_histogram.png
null_section_histogram.png

============================================================
"""

# ============================================================
# Imports
# ============================================================

import os
import json
import hashlib
import random
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import networkx as nx

import matplotlib.pyplot as plt

from community import community_louvain

# ============================================================
# Constants
# ============================================================

SEED = 42

N_NULL_ER = 1000
N_NULL_WEIGHT = 1000
N_NULL_SECTION = 1000

LOUVAIN_RESOLUTION = 1.0

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskE_v3b"

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

    raise RuntimeError(
        f"Could not detect column from: {candidates}"
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

    return parts


def canonical_node(cell_id):

    parsed = parse_cell_id(cell_id)

    if parsed is None:
        return "FUNC"

    prefix, grade, axis = parsed

    return f"{prefix}|{grade}|{axis}"


def build_sequences(
    df,
    locus_col,
    token_idx_col,
    cell_col
):

    grouped = defaultdict(list)

    for _, row in df.iterrows():

        grouped[
            row[locus_col]
        ].append((

            row[token_idx_col],

            canonical_node(
                row[cell_col]
            )
        ))

    sequences = {}

    for locus, vals in grouped.items():

        vals = sorted(vals)

        sequences[locus] = [
            v[1]
            for v in vals
        ]

    return sequences


# ============================================================
# Graph Builder
# ============================================================

def build_directed_weighted_graph(
    sequences
):

    G = nx.DiGraph()

    for locus, seq in sequences.items():

        for i in range(len(seq) - 1):

            a = seq[i]
            b = seq[i + 1]

            if G.has_edge(a, b):

                G[a][b]["weight"] += 1.0

            else:

                G.add_edge(
                    a,
                    b,
                    weight=1.0
                )

    return G


# ============================================================
# Louvain Approximation
# ============================================================

def compute_modularity(G):

    # --------------------------------------------------------
    # Weighted undirected projection
    # for stable Louvain computation
    # --------------------------------------------------------

    H = nx.Graph()

    for u, v, d in G.edges(data=True):

        w = d["weight"]

        if H.has_edge(u, v):

            H[u][v]["weight"] += w

        else:

            H.add_edge(
                u,
                v,
                weight=w
            )

    partition = community_louvain.best_partition(
        H,
        weight="weight",
        resolution=LOUVAIN_RESOLUTION,
        random_state=SEED
    )

    Q = community_louvain.modularity(
        partition,
        H,
        weight="weight"
    )

    return Q, partition


# ============================================================
# Null Builders
# ============================================================

def build_er_null_graph(
    n_nodes,
    n_edges
):

    p = (
        n_edges /
        (n_nodes * (n_nodes - 1))
    )

    G = nx.gnp_random_graph(
        n=n_nodes,
        p=p,
        directed=True,
        seed=random.randint(0, 10**9)
    )

    # --------------------------------------------------------
    # Assign random unit weights
    # --------------------------------------------------------

    for u, v in G.edges():

        G[u][v]["weight"] = 1.0

    return G


def build_weight_shuffle_null(
    G
):

    H = G.copy()

    weights = [
        d["weight"]
        for _, _, d
        in H.edges(data=True)
    ]

    random.shuffle(weights)

    for (
        (u, v, d),
        w
    ) in zip(
        H.edges(data=True),
        weights
    ):

        d["weight"] = w

    return H


# ============================================================
# Guardrail
# ============================================================

def validate_null_distribution(
    values,
    label
):

    n_unique = len(set(
        np.round(values, 12)
    ))

    std = float(np.std(values))

    print(
        f"{label}: distinct={n_unique}, "
        f"std={std:.12f}"
    )

    if n_unique < 50:

        raise RuntimeError(
            f"{label} guardrail failure: "
            "<50 distinct values."
        )

    if std <= 1e-6:

        raise RuntimeError(
            f"{label} guardrail failure: "
            "std(Q)<=1e-6"
        )

    return n_unique, std


# ============================================================
# Statistics
# ============================================================

def compute_null_stats(
    observed_Q,
    null_values
):

    mean = float(
        np.mean(null_values)
    )

    std = float(
        np.std(null_values)
    )

    z = (
        observed_Q - mean
    ) / std

    p = (
        np.sum(
            np.array(null_values) >= observed_Q
        ) + 1
    ) / (
        len(null_values) + 1
    )

    return {

        "mean": mean,
        "std": std,
        "z": z,
        "p": p
    }


def interpret_z(z):

    if z >= 9:
        return "STRONG"

    elif z >= 5:
        return "CANDIDATE"

    return "NOT_ABOVE_CHANCE"


# ============================================================
# Write Null CSV
# ============================================================

def write_null_csv(
    path,
    audit_rows,
    values
):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("# AUDIT_ROWS\n")

        for row in audit_rows:

            items = [
                f"{k}={v}"
                for k, v in row.items()
            ]

            f.write(
                ",".join(items) + "\n"
            )

        f.write("simulation,Q\n")

        for i, q in enumerate(values):

            f.write(
                f"{i + 1},{q}\n"
            )


# ============================================================
# Histogram
# ============================================================

def write_histogram(
    values,
    observed_Q,
    z,
    p,
    title,
    outpath
):

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.hist(
        values,
        bins=40
    )

    ax.axvline(
        observed_Q,
        linewidth=3,
        color="red"
    )

    ax.text(
        0.98,
        0.98,
        f"Observed Q={observed_Q:.4f}\n"
        f"z={z:.2f}\n"
        f"p={p:.6f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        bbox=dict(facecolor="white")
    )

    ax.set_title(title)

    plt.tight_layout()

    plt.savefig(
        outpath,
        dpi=200
    )

    plt.close()


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK E v3b")
print("REVISED MODULARITY NULLS")
print("====================================================\n")

# ============================================================
# File Audit
# ============================================================

print("[1/17] Auditing required files...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_MATRIX}"
    )

print("Input file present.")

# ============================================================
# Load Data
# ============================================================

print("\n[2/17] Loading MASTER_TOKEN_MATRIX.xlsx...")

raw_df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(raw_df)} rows"
)

# ============================================================
# SHA Verification
# ============================================================

print("\n[3/17] SHA-256 verification...")

matrix_sha = sha256_file(INPUT_MATRIX)

print(
    f"MASTER_TOKEN_MATRIX.xlsx = {matrix_sha}"
)

# ============================================================
# Detect Columns
# ============================================================

print("\n[4/17] Detecting required columns...")

folio_col = detect_column(
    raw_df,
    ["folio"]
)

section_col = detect_column(
    raw_df,
    ["section"]
)

locus_col = detect_column(
    raw_df,
    ["locus"]
)

token_idx_col = detect_column(
    raw_df,
    ["line_token_index"]
)

cell_col = detect_column(
    raw_df,
    ["cell_id"]
)

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  section: {section_col}")
print(f"  locus: {locus_col}")
print(f"  token index: {token_idx_col}")
print(f"  cell_id: {cell_col}")

# ============================================================
# Parser Self-Test
# ============================================================

print("\n[5/17] Parser self-test...")

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

        print(
            f"{cell} -> "
            f"({parsed[0]}, "
            f"{parsed[1]}, "
            f"{parsed[2]})"
        )

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

print("\n[6/17] Building corpus...")

rows = []

for _, row in raw_df.iterrows():

    rows.append({

        "folio":
            row[folio_col],

        "section":
            row[section_col],

        "locus":
            row[locus_col],

        "token_index":
            row[token_idx_col],

        "cell_id":
            row[cell_col]
    })

full_df = pd.DataFrame(rows)

# ============================================================
# Sequences
# ============================================================

print("\n[7/17] Building sequences...")

sequences = build_sequences(
    full_df,
    "locus",
    "token_index",
    "cell_id"
)

print(
    f"Built {len(sequences)} sequences"
)

# ============================================================
# Section Map
# ============================================================

section_map = (
    full_df
    .groupby("locus")["section"]
    .agg(lambda x: x.mode().iloc[0])
    .to_dict()
)

sequence_ids = list(
    sequences.keys()
)

section_labels = [
    section_map[s]
    for s in sequence_ids
]

# ============================================================
# Directed Observed Graph
# ============================================================

print("\n[8/17] Building observed graph...")

G_obs = build_directed_weighted_graph(
    sequences
)

Q_obs, partition_obs = compute_modularity(
    G_obs
)

print(
    f"Observed Q = {Q_obs:.6f}"
)

observed_json = {

    "construction":
        "directed_weighted_FUNC_extended",

    "nodes":
        G_obs.number_of_nodes(),

    "edges":
        G_obs.number_of_edges(),

    "density":
        nx.density(G_obs),

    "Q":
        Q_obs
}

observed_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_directed_observed.json"
)

with open(
    observed_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        observed_json,
        f,
        indent=2
    )

# ============================================================
# Confirm Sweep Exists
# ============================================================

print("\n[9/17] Checking sensitivity sweep...")

sweep_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_sensitivity_sweep.csv"
)

if os.path.exists(sweep_path):

    print(
        "Sensitivity sweep already exists."
    )

else:

    print(
        "WARNING: sensitivity sweep missing."
    )

# ============================================================
# NULL ER
# ============================================================

print("\n[10/17] NULL ER...")

null_ER = []
audit_ER = []

for sim in range(N_NULL_ER):

    H = build_er_null_graph(

        n_nodes=G_obs.number_of_nodes(),

        n_edges=G_obs.number_of_edges()
    )

    Q_null, _ = compute_modularity(H)

    null_ER.append(Q_null)

    if sim < 3:

        audit_ER.append({

            "simulation":
                sim + 1,

            "nodes":
                H.number_of_nodes(),

            "edges":
                H.number_of_edges()
        })

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_NULL_ER}"
        )

ER_unique, ER_std = validate_null_distribution(
    null_ER,
    "NULL_ER"
)

ER_stats = compute_null_stats(
    Q_obs,
    null_ER
)

ER_verdict = interpret_z(
    ER_stats["z"]
)

# ============================================================
# NULL WEIGHT
# ============================================================

print("\n[11/17] NULL WEIGHT SHUFFLE...")

null_weight = []
audit_weight = []

for sim in range(N_NULL_WEIGHT):

    H = build_weight_shuffle_null(
        G_obs
    )

    Q_null, _ = compute_modularity(H)

    null_weight.append(Q_null)

    if sim < 3:

        audit_weight.append({

            "simulation":
                sim + 1,

            "edges":
                H.number_of_edges()
        })

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_NULL_WEIGHT}"
        )

W_unique, W_std = validate_null_distribution(
    null_weight,
    "NULL_WEIGHT"
)

W_stats = compute_null_stats(
    Q_obs,
    null_weight
)

W_verdict = interpret_z(
    W_stats["z"]
)

# ============================================================
# NULL SECTION
# ============================================================

print("\n[12/17] NULL SECTION...")

null_section = []
audit_section = []

for sim in range(N_NULL_SECTION):

    shuffled_sections = np.random.permutation(
        section_labels
    )

    shuffled_map = {

        seq: sec

        for seq, sec in zip(
            sequence_ids,
            shuffled_sections
        )
    }

    if sim < 3:

        audit_section.append({

            "simulation":
                sim + 1,

            "first_10_assignments":
                ",".join(
                    shuffled_sections[:10]
                )
        })

    # --------------------------------------------------------
    # Aggregate graph ignores section labels.
    # This null may degenerate by construction.
    # --------------------------------------------------------

    H = build_directed_weighted_graph(
        sequences
    )

    Q_null, _ = compute_modularity(H)

    null_section.append(Q_null)

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_NULL_SECTION}"
        )

section_std = float(
    np.std(null_section)
)

section_unique = len(set(
    np.round(null_section, 12)
))

section_degenerate = (
    section_std <= 1e-6
)

if section_degenerate:

    print(
        "\nNULL SECTION degenerate by construction."
    )

# ============================================================
# Write CSVs
# ============================================================

print("\n[13/17] Writing CSVs...")

ER_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_null_ER.csv"
)

write_null_csv(
    ER_path,
    audit_ER,
    null_ER
)

weight_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_null_weight_shuffle.csv"
)

write_null_csv(
    weight_path,
    audit_weight,
    null_weight
)

section_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_null_section.csv"
)

write_null_csv(
    section_path,
    audit_section,
    null_section
)

# ============================================================
# Figures
# ============================================================

print("\n[14/17] Writing figures...")

fig_ER = os.path.join(
    FIG_DIR,
    "null_ER_histogram.png"
)

write_histogram(
    null_ER,
    Q_obs,
    ER_stats["z"],
    ER_stats["p"],
    "NULL ER\nDensity-Matched Random Graph",
    fig_ER
)

fig_weight = os.path.join(
    FIG_DIR,
    "null_weight_histogram.png"
)

write_histogram(
    null_weight,
    Q_obs,
    W_stats["z"],
    W_stats["p"],
    "NULL WEIGHT\nEdge-Weight Shuffle",
    fig_weight
)

if not section_degenerate:

    S_stats = compute_null_stats(
        Q_obs,
        null_section
    )

    fig_section = os.path.join(
        FIG_DIR,
        "null_section_histogram.png"
    )

    write_histogram(
        null_section,
        Q_obs,
        S_stats["z"],
        S_stats["p"],
        "NULL SECTION\nSequence-Section Permutation",
        fig_section
    )

else:

    S_stats = None
    fig_section = None

# ============================================================
# Summary
# ============================================================

print("\n[15/17] Writing summary...")

summary = {

    "task":
        "E_v3b",

    "historical_claim_status":
        "NON_REPRODUCIBLE",

    "observed_graph":
        observed_json,

    "sensitivity_sweep_exists":
        os.path.exists(
            sweep_path
        ),

    "null_ER": {

        "description":
            "Erdos-Renyi density-matched",

        "distinct_values":
            ER_unique,

        "std":
            ER_std,

        "stats":
            ER_stats,

        "verdict":
            ER_verdict
    },

    "null_weight_shuffle": {

        "description":
            "Edge-weight shuffle",

        "distinct_values":
            W_unique,

        "std":
            W_std,

        "stats":
            W_stats,

        "verdict":
            W_verdict
    },

    "null_section": {

        "description":
            "Sequence-section permutation",

        "distinct_values":
            section_unique,

        "std":
            section_std,

        "degenerate":
            section_degenerate,

        "stats":
            S_stats
    },

    "interpretation_rules": {

        "STRONG":
            "z >= 9",

        "CANDIDATE":
            "5 <= z < 9",

        "NOT_ABOVE_CHANCE":
            "z < 5"
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
    "taskE_v3_summary.json"
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

print("\n[16/17] Writing checksums...")

artifact_paths = [

    observed_path,
    ER_path,
    weight_path,
    section_path,
    summary_path,
    fig_ER,
    fig_weight
]

if fig_section is not None:

    artifact_paths.append(
        fig_section
    )

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

print("\n[17/17] COMPLETE")

print("\n====================================================")
print("TASK E v3b COMPLETE")
print("====================================================")

print(
    f"Observed Q = {Q_obs:.6f}"
)

print()

print(
    f"NULL ER z = {ER_stats['z']:.4f}"
)

print(
    f"NULL ER p = {ER_stats['p']:.6f}"
)

print(
    f"NULL ER verdict = {ER_verdict}"
)

print()

print(
    f"NULL WEIGHT z = {W_stats['z']:.4f}"
)

print(
    f"NULL WEIGHT p = {W_stats['p']:.6f}"
)

print(
    f"NULL WEIGHT verdict = {W_verdict}"
)

print()

if section_degenerate:

    print(
        "NULL SECTION degenerate."
    )

else:

    print(
        f"NULL SECTION z = {S_stats['z']:.4f}"
    )

    print(
        f"NULL SECTION p = {S_stats['p']:.6f}"
    )

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")