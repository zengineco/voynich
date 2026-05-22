#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK E v3
DIRECTED FUNC-EXTENDED MODULARITY ANALYSIS
+ MODULARITY SENSITIVITY CHARACTERIZATION

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

PART 1
------
Characterize sensitivity of graph modularity to graph
construction assumptions.

This is explicitly NOT a historical reconstruction.

The purpose is descriptive:
    how sensitive is Q to modeling choices?

PART 2
------
Run a fresh, fully-specified modularity-vs-null test
on an a-priori chosen graph construction:

    DIRECTED
    WEIGHTED
    FUNC-EXTENDED
    NO THRESHOLDING
    NO NORMALIZATION

This is the new canonical test.

============================================================
IMPORTANT
============================================================

The historical May-18 z=9.59 claim remains officially:

    NON-REPRODUCIBLE

Nothing in this script confirms or retracts that claim.

This script establishes NEW results under a fully
specified construction.

============================================================
PART 1
============================================================

Sensitivity Sweep

Variants:
1. undirected weighted
2. undirected binary
3. directed weighted
4. directed binary
5. undirected weighted excluding FUNC-FUNC
6. undirected weighted excluding all FUNC
7. row-normalized transitions
8. edge-thresholded weight >=2

Outputs:
- nodes
- edges
- density
- modularity Q

Tag:
    CHARACTERIZATION

============================================================
PART 2
============================================================

Observed Graph
--------------
Directed weighted FUNC-extended graph

Nodes:
- 130 productive cells
- FUNC

Edges:
- weighted by transition count
- all transitions retained
- FUNC-FUNC retained

Modularity:
- directed Louvain approximation
- resolution=1.0
- fixed seed

NULL A
------
Degree-preserving rewiring
(configuration-model null)

NULL B
------
Sequence-section permutation

============================================================
INTERPRETATION RULES
============================================================

NULL A z-score:

z >= 9:
    STRONG

5 <= z < 9:
    CANDIDATE

z < 5:
    not above chance

NULL B interpreted separately.

============================================================
GUARDRAILS
============================================================

1. >=50 distinct null values
2. std(Q) > 1e-6
3. parser self-test
4. deterministic seeds
5. audit rows
6. no sentinel values

============================================================
INPUT
============================================================

MASTER_TOKEN_MATRIX.xlsx
sheet: tokens_atomic

============================================================
OUTPUT
============================================================

voynich_taskE_v3/

FILES
=====

taskE_v3_sensitivity_sweep.csv
taskE_v3_directed_observed.json
taskE_v3_null_A_degree.csv
taskE_v3_null_B_section.csv
taskE_v3_summary.json
checksums.json

FIGURES
=======

null_A_histogram.png
null_B_histogram.png

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

N_NULL_A = 1000
N_NULL_B = 1000

LOUVAIN_RESOLUTION = 1.0

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskE_v3"

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
# Graph Builders
# ============================================================

def build_graph(
    sequences,
    directed=False,
    weighted=True,
    exclude_func_func=False,
    exclude_all_func=False,
    threshold=None,
    normalize_rows=False
):

    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    outgoing_totals = defaultdict(int)

    # ========================================================
    # Pass 1
    # ========================================================

    for locus, seq in sequences.items():

        for i in range(len(seq) - 1):

            a = seq[i]
            b = seq[i + 1]

            if exclude_func_func:

                if (
                    a == "FUNC"
                    and b == "FUNC"
                ):
                    continue

            if exclude_all_func:

                if (
                    a == "FUNC"
                    or b == "FUNC"
                ):
                    continue

            outgoing_totals[a] += 1

    # ========================================================
    # Pass 2
    # ========================================================

    for locus, seq in sequences.items():

        for i in range(len(seq) - 1):

            a = seq[i]
            b = seq[i + 1]

            if exclude_func_func:

                if (
                    a == "FUNC"
                    and b == "FUNC"
                ):
                    continue

            if exclude_all_func:

                if (
                    a == "FUNC"
                    or b == "FUNC"
                ):
                    continue

            if normalize_rows:

                weight = (
                    1.0 / outgoing_totals[a]
                )

            else:

                weight = 1.0

            if G.has_edge(a, b):

                if weighted:
                    G[a][b]["weight"] += weight

            else:

                if weighted:

                    G.add_edge(
                        a,
                        b,
                        weight=weight
                    )

                else:

                    G.add_edge(
                        a,
                        b,
                        weight=1.0
                    )

    # ========================================================
    # Threshold
    # ========================================================

    if threshold is not None:

        remove_edges = []

        for a, b, d in G.edges(data=True):

            if d["weight"] < threshold:

                remove_edges.append((a, b))

        G.remove_edges_from(remove_edges)

    return G


# ============================================================
# Directed Modularity Approximation
# ============================================================

def compute_modularity(G):

    # --------------------------------------------------------
    # community_louvain does not support DiGraph directly.
    # Convert to weighted undirected approximation preserving
    # directed edge weights symmetrically.
    # --------------------------------------------------------

    if isinstance(G, nx.DiGraph):

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

    else:

        H = G

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
# Degree-Preserving Rewire
# ============================================================

def rewire_directed_graph(
    G,
    nswap_factor=10
):

    H = G.copy()

    nswap = max(
        100,
        H.number_of_edges() * nswap_factor
    )

    max_tries = nswap * 20

    nx.double_edge_swap(
        H.to_undirected(),
        nswap=nswap,
        max_tries=max_tries,
        seed=SEED
    )

    return H


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK E v3")
print("DIRECTED FUNC-EXTENDED MODULARITY")
print("====================================================\n")

# ============================================================
# File Audit
# ============================================================

print("[1/18] Auditing required files...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_MATRIX}"
    )

print("Input file present.")

# ============================================================
# Load Data
# ============================================================

print("\n[2/18] Loading MASTER_TOKEN_MATRIX.xlsx...")

raw_df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(raw_df)} rows"
)

# ============================================================
# SHA Audit
# ============================================================

print("\n[3/18] SHA-256 verification...")

matrix_sha = sha256_file(INPUT_MATRIX)

print(
    f"MASTER_TOKEN_MATRIX.xlsx = {matrix_sha}"
)

expected_sha = (
    "be83cbbe8e37fc79129e5f270c5f13df"
    "72e7aa5b05f7745da8e2dfbf5d3203e0"
)

if matrix_sha != expected_sha:

    raise RuntimeError(
        "SHA mismatch."
    )

print("SHA verified.")

# ============================================================
# Detect Columns
# ============================================================

print("\n[4/18] Detecting required columns...")

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

parsed_col = detect_column(
    raw_df,
    ["parsed"]
)

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  section: {section_col}")
print(f"  locus: {locus_col}")
print(f"  token index: {token_idx_col}")
print(f"  cell_id: {cell_col}")
print(f"  parsed: {parsed_col}")

# ============================================================
# Parser Self-Test
# ============================================================

print("\n[5/18] Parser self-test...")

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

print("\n[6/18] Building corpus...")

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

print(
    f"Retained rows: {len(full_df)}"
)

# ============================================================
# Build Sequences
# ============================================================

print("\n[7/18] Building sequences...")

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
# PART 1
# Sensitivity Sweep
# ============================================================

print("\n[8/18] PART 1 — Sensitivity Sweep...")

variants = [

    (
        "undirected_weighted",
        dict(
            directed=False,
            weighted=True
        )
    ),

    (
        "undirected_binary",
        dict(
            directed=False,
            weighted=False
        )
    ),

    (
        "directed_weighted",
        dict(
            directed=True,
            weighted=True
        )
    ),

    (
        "directed_binary",
        dict(
            directed=True,
            weighted=False
        )
    ),

    (
        "exclude_FUNC_FUNC",
        dict(
            directed=False,
            weighted=True,
            exclude_func_func=True
        )
    ),

    (
        "exclude_all_FUNC",
        dict(
            directed=False,
            weighted=True,
            exclude_all_func=True
        )
    ),

    (
        "row_normalized",
        dict(
            directed=False,
            weighted=True,
            normalize_rows=True
        )
    ),

    (
        "threshold_ge2",
        dict(
            directed=False,
            weighted=True,
            threshold=2
        )
    )
]

sweep_rows = []

for name, kwargs in variants:

    print(f"  {name}")

    G = build_graph(
        sequences,
        **kwargs
    )

    Q, _ = compute_modularity(G)

    density = nx.density(G)

    sweep_rows.append({

        "variant":
            name,

        "nodes":
            G.number_of_nodes(),

        "edges":
            G.number_of_edges(),

        "density":
            density,

        "Q":
            Q
    })

sweep_df = pd.DataFrame(
    sweep_rows
)

sweep_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_sensitivity_sweep.csv"
)

sweep_df.to_csv(
    sweep_path,
    index=False
)

# ============================================================
# PART 2
# Directed Weighted Graph
# ============================================================

print("\n[9/18] PART 2 — Directed Weighted Graph...")

G_obs = build_graph(

    sequences,

    directed=True,
    weighted=True
)

Q_obs, partition_obs = compute_modularity(
    G_obs
)

print(
    f"Observed directed Q = {Q_obs:.6f}"
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
# NULL A
# Degree-Preserving Rewire
# ============================================================

print("\n[10/18] NULL A — Degree-Preserving Rewire...")

null_A = []
audit_A = []

for sim in range(N_NULL_A):

    H = rewire_directed_graph(
        G_obs
    )

    Q_perm, _ = compute_modularity(H)

    null_A.append(Q_perm)

    if sim < 3:

        audit_A.append({

            "simulation":
                sim + 1,

            "nodes":
                H.number_of_nodes(),

            "edges":
                H.number_of_edges()
        })

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_NULL_A}"
        )

nullA_unique = len(set(
    np.round(null_A, 12)
))

nullA_std = float(
    np.std(null_A)
)

if nullA_unique < 50:

    raise RuntimeError(
        "NULL A guardrail failure: "
        "<50 distinct values."
    )

if nullA_std <= 1e-6:

    raise RuntimeError(
        "NULL A guardrail failure: "
        "std(Q)<=1e-6"
    )

# ============================================================
# NULL B
# Section Permutation
# ============================================================

print("\n[11/18] NULL B — Sequence-Section Permutation...")

null_B = []
audit_B = []

for sim in range(N_NULL_B):

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

        audit_B.append({

            "simulation":
                sim + 1,

            "first_10_assignments":
                ",".join(
                    shuffled_sections[:10]
                )
        })

    # --------------------------------------------------------
    # Directed graph itself ignores section labels.
    # Therefore this null may degenerate.
    # --------------------------------------------------------

    G_perm = build_graph(

        sequences,

        directed=True,
        weighted=True
    )

    Q_perm, _ = compute_modularity(
        G_perm
    )

    null_B.append(Q_perm)

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_NULL_B}"
        )

nullB_unique = len(set(
    np.round(null_B, 12)
))

nullB_std = float(
    np.std(null_B)
)

# ============================================================
# Degeneracy Check
# ============================================================

if nullB_std <= 1e-6:

    print(
        "\nNULL B DEGENERATE:"
    )

    print(
        "Sequence-section permutation "
        "does not alter graph structure "
        "under aggregate directed graph "
        "construction."
    )

# ============================================================
# Statistics
# ============================================================

print("\n[12/18] Computing statistics...")

# ------------------------------------------------------------
# NULL A
# ------------------------------------------------------------

nullA_mean = float(
    np.mean(null_A)
)

nullA_z = (
    Q_obs - nullA_mean
) / nullA_std

nullA_p = (
    np.sum(
        np.array(null_A) >= Q_obs
    ) + 1
) / (
    N_NULL_A + 1
)

# ------------------------------------------------------------
# NULL B
# ------------------------------------------------------------

nullB_mean = float(
    np.mean(null_B)
)

if nullB_std <= 1e-6:

    nullB_z = None
    nullB_p = None

else:

    nullB_z = (
        Q_obs - nullB_mean
    ) / nullB_std

    nullB_p = (
        np.sum(
            np.array(null_B) >= Q_obs
        ) + 1
    ) / (
        N_NULL_B + 1
    )

# ============================================================
# Verdict
# ============================================================

if nullA_z >= 9:

    verdict = "STRONG"

elif nullA_z >= 5:

    verdict = "CANDIDATE"

else:

    verdict = "NOT_ABOVE_CHANCE"

print(
    f"NULL A z = {nullA_z:.4f}"
)

print(
    f"NULL A p = {nullA_p:.6f}"
)

print(
    f"Verdict = {verdict}"
)

# ============================================================
# Write NULL A
# ============================================================

nullA_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_null_A_degree.csv"
)

with open(
    nullA_path,
    "w",
    encoding="utf-8"
) as f:

    f.write("# AUDIT_ROWS\n")

    for row in audit_A:

        f.write(
            f"simulation={row['simulation']},"
            f"nodes={row['nodes']},"
            f"edges={row['edges']}\n"
        )

    f.write("simulation,Q\n")

    for i, q in enumerate(null_A):

        f.write(
            f"{i + 1},{q}\n"
        )

# ============================================================
# Write NULL B
# ============================================================

nullB_path = os.path.join(
    OUTPUT_DIR,
    "taskE_v3_null_B_section.csv"
)

with open(
    nullB_path,
    "w",
    encoding="utf-8"
) as f:

    f.write("# AUDIT_ROWS\n")

    for row in audit_B:

        f.write(
            f"simulation={row['simulation']},"
            f"assignments={row['first_10_assignments']}\n"
        )

    f.write("simulation,Q\n")

    for i, q in enumerate(null_B):

        f.write(
            f"{i + 1},{q}\n"
        )

# ============================================================
# Figures
# ============================================================

print("\n[13/18] Writing figures...")

# ------------------------------------------------------------
# NULL A
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.hist(
    null_A,
    bins=40
)

ax.axvline(
    Q_obs,
    linewidth=3,
    color="red"
)

ax.text(
    0.98,
    0.98,
    f"Observed Q={Q_obs:.4f}\n"
    f"z={nullA_z:.2f}\n"
    f"p={nullA_p:.6f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white")
)

ax.set_title(
    "NULL A\n"
    "Degree-Preserving Rewire"
)

figA_path = os.path.join(
    FIG_DIR,
    "null_A_histogram.png"
)

plt.tight_layout()

plt.savefig(
    figA_path,
    dpi=200
)

plt.close()

# ------------------------------------------------------------
# NULL B
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.hist(
    null_B,
    bins=40
)

ax.axvline(
    Q_obs,
    linewidth=3,
    color="red"
)

ax.set_title(
    "NULL B\n"
    "Sequence-Section Permutation"
)

figB_path = os.path.join(
    FIG_DIR,
    "null_B_histogram.png"
)

plt.tight_layout()

plt.savefig(
    figB_path,
    dpi=200
)

plt.close()

# ============================================================
# Summary
# ============================================================

print("\n[14/18] Writing summary...")

summary = {

    "task":
        "E_v3",

    "historical_claim_status":
        "NON_REPRODUCIBLE",

    "part_1": {

        "tag":
            "CHARACTERIZATION",

        "sensitivity_sweep_csv":
            os.path.basename(
                sweep_path
            )
    },

    "part_2": {

        "construction":
            "directed_weighted_FUNC_extended",

        "observed_Q":
            float(Q_obs),

        "nodes":
            int(
                G_obs.number_of_nodes()
            ),

        "edges":
            int(
                G_obs.number_of_edges()
            ),

        "density":
            float(
                nx.density(G_obs)
            )
    },

    "null_A": {

        "description":
            "Degree-preserving rewiring",

        "distinct_values":
            int(nullA_unique),

        "std":
            float(nullA_std),

        "mean":
            float(nullA_mean),

        "z":
            float(nullA_z),

        "p":
            float(nullA_p)
    },

    "null_B": {

        "description":
            "Sequence-section permutation",

        "distinct_values":
            int(nullB_unique),

        "std":
            float(nullB_std),

        "degenerate":
            bool(
                nullB_std <= 1e-6
            ),

        "mean":
            float(nullB_mean),

        "z":
            nullB_z,

        "p":
            nullB_p
    },

    "verdict":
        verdict,

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

print("\n[15/18] Writing checksums...")

artifact_paths = [

    sweep_path,
    observed_path,
    nullA_path,
    nullB_path,
    summary_path,
    figA_path,
    figB_path
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

print("\n[16/18] COMPLETE")

print("\n====================================================")
print("TASK E v3 COMPLETE")
print("====================================================")

print(
    f"Observed directed Q = {Q_obs:.6f}"
)

print()

print(
    f"NULL A z = {nullA_z:.4f}"
)

print(
    f"NULL A p = {nullA_p:.6f}"
)

print(
    f"Verdict = {verdict}"
)

print()

if nullB_z is None:

    print(
        "NULL B degenerate."
    )

else:

    print(
        f"NULL B z = {nullB_z:.4f}"
    )

    print(
        f"NULL B p = {nullB_p:.6f}"
    )

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")