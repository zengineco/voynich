"""
VOYNICH RESEARCH ENGINE v1.0
Canonical Multi-Layer Extraction System

Outputs:
- matrices
- tensors
- trajectories
- permission geometry
- topology
- embeddings
- falsification scaffolds

REQUIRES:
pip install pandas numpy networkx scikit-learn openpyxl umap-learn

INPUT:
MASTER_TOKEN_MATRIX.xlsx

AUTHOR:
Canonical research pipeline
"""

# =========================================================
# IMPORTS
# =========================================================

import os
import math
import json
import random

import numpy as np
import pandas as pd

from collections import Counter, defaultdict

import networkx as nx

from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

import umap

from networkx.algorithms.community import (
    greedy_modularity_communities
)

# =========================================================
# CONFIG
# =========================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_outputs_v1"

PARSED_ONLY = True

MIN_LINE_LEN = 2

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

os.makedirs(OUTDIR, exist_ok=True)

# =========================================================
# LOAD
# =========================================================

print("=== LOADING CORPUS ===")

df = pd.read_excel(
    INPUT_XLSX,
    sheet_name="tokens_atomic"
)

print(f"TOTAL ROWS: {len(df):,}")

if PARSED_ONLY:
    df = df[df["parsed"] == True].copy()

print(f"PARSED ROWS: {len(df):,}")

# =========================================================
# BASIC CHECKSUMS
# =========================================================

checksums = {}

checksums["parsed_rows"] = int(len(df))
checksums["folios"] = int(df["folio"].nunique())
checksums["sections"] = int(df["section"].nunique())

# =========================================================
# TRANSITION EXTRACTION
# =========================================================

print("\n=== TRANSITIONS ===")

transitions = []

line_sequences = []

for (folio, locus), group in df.groupby(
    ["folio", "locus"]
):

    group = group.sort_values(
        "line_token_index"
    )

    cells = group["cell_id"].dropna().tolist()

    toks = group["token"].tolist()

    section = group["section"].iloc[0]

    if len(cells) < MIN_LINE_LEN:
        continue

    line_sequences.append({
        "folio": folio,
        "locus": locus,
        "section": section,
        "cells": cells,
        "tokens": toks
    })

    for i in range(len(cells)-1):

        transitions.append((
            cells[i],
            cells[i+1],
            section
        ))

print(f"TRANSITIONS: {len(transitions):,}")

checksums["transitions"] = int(len(transitions))

# =========================================================
# TRANSITION COUNTS
# =========================================================

transition_counter = Counter()

for u, v, s in transitions:
    transition_counter[(u, v)] += 1

transition_rows = []

for (u, v), c in transition_counter.items():

    transition_rows.append({
        "from_cell": u,
        "to_cell": v,
        "count": c
    })

transition_df = pd.DataFrame(transition_rows)

transition_df.to_csv(
    f"{OUTDIR}/transitions.csv",
    index=False
)

# =========================================================
# GRAPH BUILD
# =========================================================

print("\n=== GRAPH BUILD ===")

G = nx.Graph()

for (u, v), w in transition_counter.items():

    if G.has_edge(u, v):
        G[u][v]["weight"] += w
    else:
        G.add_edge(u, v, weight=w)

print(f"NODES: {G.number_of_nodes()}")
print(f"EDGES: {G.number_of_edges()}")

checksums["graph_nodes"] = int(G.number_of_nodes())
checksums["graph_edges"] = int(G.number_of_edges())

# =========================================================
# COMMUNITIES
# =========================================================

print("\n=== COMMUNITIES ===")

communities = greedy_modularity_communities(
    G,
    weight="weight"
)

community_map = {}

for idx, comm in enumerate(communities):

    for node in comm:
        community_map[node] = f"C{idx}"

community_rows = []

for node, comm in community_map.items():

    community_rows.append({
        "cell_id": node,
        "community": comm
    })

community_df = pd.DataFrame(community_rows)

community_df.to_csv(
    f"{OUTDIR}/community_assignments.csv",
    index=False
)

print(f"COMMUNITIES: {len(communities)}")

checksums["communities"] = int(len(communities))

# =========================================================
# ASSIGN COMMUNITIES
# =========================================================

df["community"] = df["cell_id"].map(
    community_map
)

# =========================================================
# SELF LOOPS
# =========================================================

print("\n=== SELF LOOPS ===")

loops = []

for (u, v), c in transition_counter.items():

    if u == v:

        loops.append({
            "cell": u,
            "count": c
        })

loops_df = (
    pd.DataFrame(loops)
    .sort_values("count", ascending=False)
)

loops_df.to_csv(
    f"{OUTDIR}/self_loops.csv",
    index=False
)

print(loops_df.head(10))

# =========================================================
# CONDITIONAL ENTROPY
# =========================================================

print("\n=== CONDITIONAL ENTROPY ===")

def conditional_entropy(group):

    seq = group["cell_id"].tolist()

    if len(seq) < 10:
        return np.nan

    pairs = list(zip(seq[:-1], seq[1:]))

    counts = Counter(pairs)

    prev_counts = Counter()

    for a, b in pairs:
        prev_counts[a] += 1

    H = 0

    for (a, b), c in counts.items():

        p_ab = c / len(pairs)

        p_b_given_a = c / prev_counts[a]

        H -= p_ab * math.log2(p_b_given_a)

    return H

entropy_rows = []

for sec, g in df.groupby("section"):

    H = conditional_entropy(g)

    entropy_rows.append({
        "section": sec,
        "conditional_entropy": H
    })

entropy_df = pd.DataFrame(entropy_rows)

entropy_df.to_csv(
    f"{OUTDIR}/section_entropy.csv",
    index=False
)

print(entropy_df)

# =========================================================
# TRAJECTORIES
# =========================================================

print("\n=== TRAJECTORIES ===")

trajectory_rows = []

for row in line_sequences:

    comms = [
        community_map.get(x, "UNK")
        for x in row["cells"]
    ]

    trajectory_rows.append({
        "folio": row["folio"],
        "section": row["section"],
        "locus": row["locus"],
        "length": len(comms),
        "trajectory":
            " -> ".join(comms),

        "cell_path":
            " -> ".join(row["cells"]),

        "token_path":
            " ".join(row["tokens"])
    })

trajectory_df = pd.DataFrame(
    trajectory_rows
)

trajectory_df.to_csv(
    f"{OUTDIR}/trajectory_lines.csv",
    index=False
)

print(
    f"TRAJECTORIES: {len(trajectory_df):,}"
)

# =========================================================
# TRAJECTORY COUNTS
# =========================================================

traj_counts = (
    trajectory_df
    .groupby(
        ["section", "trajectory"]
    )
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

traj_counts.to_csv(
    f"{OUTDIR}/trajectory_counts.csv",
    index=False
)

# =========================================================
# GLOBAL TRAJECTORIES
# =========================================================

global_traj = (
    trajectory_df
    .groupby("trajectory")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

global_traj.to_csv(
    f"{OUTDIR}/trajectory_global_counts.csv",
    index=False
)

# =========================================================
# COMMUNITY LOADINGS
# =========================================================

print("\n=== COMMUNITY LOADINGS ===")

loadings = (
    df.groupby(
        ["section", "community"]
    )
    .size()
    .reset_index(name="count")
)

loadings["pct"] = (
    loadings.groupby("section")["count"]
    .transform(lambda x: x / x.sum())
)

loadings.to_csv(
    f"{OUTDIR}/section_community_loadings.csv",
    index=False
)

print(loadings.head(20))

# =========================================================
# COMMUNITY TRANSITION MATRIX
# =========================================================

print("\n=== COMMUNITY TRANSITIONS ===")

comm_trans = []

for row in line_sequences:

    comms = [
        community_map.get(x, "UNK")
        for x in row["cells"]
    ]

    for i in range(len(comms)-1):

        comm_trans.append({
            "section": row["section"],
            "from_comm": comms[i],
            "to_comm": comms[i+1]
        })

comm_df = pd.DataFrame(comm_trans)

comm_matrix = (
    comm_df.groupby(
        ["section", "from_comm", "to_comm"]
    )
    .size()
    .reset_index(name="count")
)

comm_matrix["probability"] = (
    comm_matrix.groupby(
        ["section", "from_comm"]
    )["count"]
    .transform(lambda x: x / x.sum())
)

comm_matrix.to_csv(
    f"{OUTDIR}/community_transition_matrix.csv",
    index=False
)

# =========================================================
# PERMISSION MATRIX
# =========================================================

print("\n=== PERMISSION MATRIX ===")

all_cells = sorted(
    df["cell_id"].dropna().unique()
)

perm_rows = []

observed = set()

for u, v, s in transitions:
    observed.add((u, v))

for u in all_cells:
    for v in all_cells:

        allowed = (
            1 if (u, v) in observed else 0
        )

        perm_rows.append({
            "from_cell": u,
            "to_cell": v,
            "allowed": allowed
        })

perm_df = pd.DataFrame(perm_rows)

perm_df.to_csv(
    f"{OUTDIR}/permission_matrix.csv",
    index=False
)

# =========================================================
# POSITIONAL TENSOR
# =========================================================

print("\n=== POSITIONAL TENSOR ===")

pos_rows = []

for row in line_sequences:

    n = len(row["cells"])

    for i, cell in enumerate(row["cells"]):

        pos_rows.append({
            "section": row["section"],
            "cell_id": cell,
            "community":
                community_map.get(cell, "UNK"),

            "relative_pos":
                round(i / max(n-1, 1), 2)
        })

pos_df = pd.DataFrame(pos_rows)

pos_tensor = (
    pos_df.groupby(
        [
            "section",
            "community",
            "relative_pos"
        ]
    )
    .size()
    .reset_index(name="count")
)

pos_tensor["probability"] = (
    pos_tensor.groupby(
        ["section", "relative_pos"]
    )["count"]
    .transform(lambda x: x / x.sum())
)

pos_tensor.to_csv(
    f"{OUTDIR}/positional_tensor.csv",
    index=False
)

# =========================================================
# ABLAUT MATRIX
# =========================================================

print("\n=== ABLAUT MATRIX ===")

ablaut = (
    df.groupby(
        ["base", "grade", "section"]
    )
    .size()
    .reset_index(name="count")
)

ablaut["probability"] = (
    ablaut.groupby(
        ["base", "section"]
    )["count"]
    .transform(lambda x: x / x.sum())
)

ablaut.to_csv(
    f"{OUTDIR}/ablaut_matrix.csv",
    index=False
)

# =========================================================
# D-FAMILY ROUTING
# =========================================================

print("\n=== D-FAMILY ROUTING ===")

d_rows = []

for row in line_sequences:

    toks = row["tokens"]
    cells = row["cells"]

    for i, tok in enumerate(toks):

        if tok.startswith("d"):

            prev_cell = (
                cells[i-1]
                if i > 0 else None
            )

            next_cell = (
                cells[i+1]
                if i < len(cells)-1 else None
            )

            d_rows.append({
                "token": tok,
                "section": row["section"],
                "position": i,
                "relative_position":
                    round(
                        i / max(len(toks)-1,1),
                        2
                    ),

                "prev_cell": prev_cell,
                "next_cell": next_cell,

                "prev_comm":
                    community_map.get(
                        prev_cell,
                        "UNK"
                    ),

                "next_comm":
                    community_map.get(
                        next_cell,
                        "UNK"
                    )
            })

d_df = pd.DataFrame(d_rows)

d_df.to_csv(
    f"{OUTDIR}/d_family_routes.csv",
    index=False
)

# =========================================================
# EXECUTION COMPLEXITY
# =========================================================

print("\n=== EXECUTION COMPLEXITY ===")

complexity_rows = []

for row in trajectory_rows:

    traj = row["trajectory"].split(
        " -> "
    )

    uniq = len(set(traj))

    switches = sum(
        traj[i] != traj[i+1]
        for i in range(len(traj)-1)
    )

    complexity_rows.append({
        "folio": row["folio"],
        "section": row["section"],
        "trajectory": row["trajectory"],
        "community_diversity": uniq,
        "switches": switches,
        "length": row["length"]
    })

complexity_df = pd.DataFrame(
    complexity_rows
)

complexity_df.to_csv(
    f"{OUTDIR}/execution_complexity.csv",
    index=False
)

# =========================================================
# RECURSION DETECTION
# =========================================================

print("\n=== RECURSION DETECTION ===")

recur_rows = []

for row in trajectory_rows:

    traj = row["trajectory"].split(
        " -> "
    )

    for i in range(len(traj)-2):

        if traj[i] == traj[i+2]:

            recur_rows.append({
                "folio": row["folio"],
                "section": row["section"],
                "pattern":
                    f"{traj[i]}->{traj[i+1]}->{traj[i+2]}"
            })

recur_df = pd.DataFrame(recur_rows)

recur_df.to_csv(
    f"{OUTDIR}/recursion_patterns.csv",
    index=False
)

# =========================================================
# TRAJECTORY EMBEDDINGS
# =========================================================

print("\n=== TRAJECTORY EMBEDDINGS ===")

traj_strings = (
    trajectory_df["trajectory"]
    .tolist()
)

vocab = sorted(
    list(set(traj_strings))
)

traj_to_idx = {
    x:i for i,x in enumerate(vocab)
}

X = np.zeros((len(traj_strings), len(vocab)))

for i, t in enumerate(traj_strings):
    X[i, traj_to_idx[t]] = 1

reducer = umap.UMAP(
    random_state=RANDOM_SEED
)

embedding = reducer.fit_transform(X)

embed_df = pd.DataFrame({
    "x": embedding[:,0],
    "y": embedding[:,1],
    "section":
        trajectory_df["section"].values,

    "trajectory":
        trajectory_df["trajectory"].values
})

embed_df.to_csv(
    f"{OUTDIR}/trajectory_embeddings.csv",
    index=False
)

# =========================================================
# INVARIANTS
# =========================================================

print("\n=== INVARIANTS ===")

section_sets = {}

for sec in trajectory_df["section"].unique():

    section_sets[sec] = set(
        trajectory_df[
            trajectory_df["section"] == sec
        ]["trajectory"]
    )

common = set.intersection(
    *section_sets.values()
)

invariants_df = pd.DataFrame({
    "trajectory": list(common)
})

invariants_df.to_csv(
    f"{OUTDIR}/invariants.csv",
    index=False
)

# =========================================================
# CHECKSUMS
# =========================================================

print("\n=== CHECKSUMS ===")

with open(
    f"{OUTDIR}/checksums.json",
    "w"
) as f:

    json.dump(
        checksums,
        f,
        indent=2
    )

print(json.dumps(checksums, indent=2))

# =========================================================
# COMPLETE
# =========================================================

print("\n=== COMPLETE ===")

print(f"OUTPUT DIRECTORY: {OUTDIR}")

print("""
GENERATED:

- transitions.csv
- self_loops.csv
- community_assignments.csv
- section_entropy.csv
- trajectory_lines.csv
- trajectory_counts.csv
- trajectory_global_counts.csv
- section_community_loadings.csv
- community_transition_matrix.csv
- permission_matrix.csv
- positional_tensor.csv
- ablaut_matrix.csv
- d_family_routes.csv
- execution_complexity.csv
- recursion_patterns.csv
- trajectory_embeddings.csv
- invariants.csv
- checksums.json
""")