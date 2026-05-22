"""
VOYNICH FUNC FOLLOW-UP ANALYSIS
===============================

Outputs:
- func_resolution_sweep.csv
- func_edge_asymmetry.csv
- func_position_by_section.csv
- func_bigram_backoff.csv
- func_top_selectors.csv

"""

# =====================================================
# IMPORTS
# =====================================================

import os
import json
import random

import numpy as np
import pandas as pd

from collections import Counter, defaultdict

import networkx as nx

from networkx.algorithms.community import (
    louvain_communities
)

# =====================================================
# CONFIG
# =====================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_func_followup_v1"

os.makedirs(OUTDIR, exist_ok=True)

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# =====================================================
# LOAD
# =====================================================

print("=== LOAD ===")

df = pd.read_excel(
    INPUT_XLSX,
    sheet_name="tokens_atomic"
)

# =====================================================
# FUNC COLLAPSE
# =====================================================

df["node"] = np.where(
    df["parsed"] == True,
    df["cell_id"],
    "FUNC"
)

# =====================================================
# BUILD TRANSITIONS
# =====================================================

print("\n=== BUILD TRANSITIONS ===")

transitions = []

directed_transitions = []

line_sequences = []

for (folio, locus), group in df.groupby(
    ["folio", "locus"]
):

    group = group.sort_values(
        "line_token_index"
    )

    seq = (
        group["node"]
        .dropna()
        .tolist()
    )

    if len(seq) < 2:
        continue

    line_sequences.append((
        seq,
        group["section"].iloc[0]
    ))

    for i in range(len(seq)-1):

        a = seq[i]
        b = seq[i+1]

        transitions.append((a, b))

        directed_transitions.append((a, b))

# =====================================================
# UNDIRECTED GRAPH
# =====================================================

print("\n=== UNDIRECTED GRAPH ===")

G = nx.Graph()

cc = Counter(transitions)

for (u, v), w in cc.items():

    G.add_edge(
        u,
        v,
        weight=w
    )

# =====================================================
# RESOLUTION SWEEP
# =====================================================

print("\n=== RESOLUTION SWEEP ===")

sweep_rows = []

for res in [0.5, 0.75, 1.0, 1.25, 1.5]:

    comms = louvain_communities(
        G,
        weight="weight",
        resolution=res,
        seed=RANDOM_SEED
    )

    Q = nx.community.modularity(
        G,
        comms,
        weight="weight"
    )

    sweep_rows.append({
        "resolution": res,
        "Q": Q,
        "n_communities": len(comms)
    })

    print(
        f"RES={res} "
        f"Q={Q:.6f} "
        f"K={len(comms)}"
    )

sweep_df = pd.DataFrame(sweep_rows)

sweep_df.to_csv(
    f"{OUTDIR}/func_resolution_sweep.csv",
    index=False
)

# =====================================================
# THREE-COMMUNITY SPLIT
# =====================================================

print("\n=== THREE-COMMUNITY SPLIT ===")

best = louvain_communities(
    G,
    weight="weight",
    resolution=0.5,
    seed=RANDOM_SEED
)

best = sorted(
    best,
    key=len,
    reverse=True
)

best = best[:3]

community_map = {}

for idx, comm in enumerate(best):

    for node in comm:

        community_map[node] = f"C{idx}"

# =====================================================
# DIRECTED GRAPH
# =====================================================

print("\n=== DIRECTED GRAPH ===")

DG = nx.DiGraph()

dcc = Counter(directed_transitions)

for (u, v), w in dcc.items():

    DG.add_edge(
        u,
        v,
        weight=w
    )

# =====================================================
# EDGE ASYMMETRY
# =====================================================

print("\n=== EDGE ASYMMETRY ===")

asym_rows = []

targets = []

for node, comm in community_map.items():

    if comm in ["C0", "C1"]:

        targets.append(node)

for cell in targets:

    w1 = DG.get_edge_data(
        "FUNC",
        cell,
        default={"weight": 0}
    )["weight"]

    w2 = DG.get_edge_data(
        cell,
        "FUNC",
        default={"weight": 0}
    )["weight"]

    denom = w1 + w2

    if denom == 0:
        continue

    asym = (w1 - w2) / denom

    if abs(asym) > 0.3:

        asym_rows.append({
            "cell": cell,
            "community":
                community_map[cell],

            "func_to_cell": w1,
            "cell_to_func": w2,
            "asymmetry_index": asym
        })

asym_df = pd.DataFrame(asym_rows)

asym_df.to_csv(
    f"{OUTDIR}/func_edge_asymmetry.csv",
    index=False
)

# =====================================================
# FUNC POSITION DISTRIBUTION
# =====================================================

print("\n=== FUNC POSITION DISTRIBUTION ===")

pos_rows = []

for seq, section in line_sequences:

    if len(seq) < 3:
        continue

    n = len(seq)

    for i, tok in enumerate(seq):

        if tok != "FUNC":
            continue

        rel = i / (n - 1)

        decile = min(
            int(rel * 10),
            9
        )

        pos_rows.append({
            "section": section,
            "relative_position": rel,
            "decile": decile
        })

pos_df = pd.DataFrame(pos_rows)

summary = (
    pos_df
    .groupby(
        ["section", "decile"]
    )
    .size()
    .reset_index(name="count")
)

summary["pct"] = (
    summary["count"]
    /
    summary.groupby("section")[
        "count"
    ].transform("sum")
)

summary.to_csv(
    f"{OUTDIR}/func_position_by_section.csv",
    index=False
)

# =====================================================
# BIGRAM BACKOFF
# =====================================================

print("\n=== BIGRAM BACKOFF ===")

node_freq = Counter()

for a, b in directed_transitions:

    node_freq[a] += 1
    node_freq[b] += 1

top50 = [
    x for x, c
    in node_freq.most_common(50)
]

forward_counts = Counter()

backward_counts = Counter()

total_after = Counter()

total_before = Counter()

for a, b in directed_transitions:

    total_after[a] += 1

    total_before[b] += 1

    if b == "FUNC":

        forward_counts[a] += 1

    if a == "FUNC":

        backward_counts[b] += 1

backoff_rows = []

for cell in top50:

    p1 = (
        forward_counts[cell]
        /
        total_after[cell]
        if total_after[cell]
        else np.nan
    )

    p2 = (
        backward_counts[cell]
        /
        total_before[cell]
        if total_before[cell]
        else np.nan
    )

    backoff_rows.append({
        "cell": cell,
        "p_func_given_cell": p1,
        "p_cell_given_func": p2
    })

backoff_df = pd.DataFrame(
    backoff_rows
)

backoff_df = backoff_df.sort_values(
    "p_func_given_cell",
    ascending=False
)

backoff_df.to_csv(
    f"{OUTDIR}/func_bigram_backoff.csv",
    index=False
)

# =====================================================
# TOP SELECTORS
# =====================================================

top_selectors = backoff_df.head(10)

top_selectors.to_csv(
    f"{OUTDIR}/func_top_selectors.csv",
    index=False
)

print("\n=== TOP 10 SELECTORS ===")

print(
    top_selectors[
        [
            "cell",
            "p_func_given_cell",
            "p_cell_given_func"
        ]
    ]
)

# =====================================================
# COMPLETE
# =====================================================

print("\n=== COMPLETE ===")

print("WRITTEN:")

print("- func_resolution_sweep.csv")
print("- func_edge_asymmetry.csv")
print("- func_position_by_section.csv")
print("- func_bigram_backoff.csv")
print("- func_top_selectors.csv")