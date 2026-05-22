"""
VOYNICH FUNC-EXTENDED COMMUNITY AUDIT
====================================

Rebuilds the transition graph on the full token corpus:
- parsed tokens retain cell_id
- unparsed tokens collapse to FUNC

Outputs:
- func_extended_communities.csv
- func_extended_modularity.json
- func_jaccard_overlap.csv
- func_section_loadings.csv
- func_directional_bias.csv

Assumes:
- MASTER_TOKEN_MATRIX.xlsx
- canonical community assignments:
    voynich_outputs_v1/community_assignments.csv

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
    greedy_modularity_communities
)

# =====================================================
# CONFIG
# =====================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

CANONICAL_COMMUNITIES = (
    "voynich_outputs_v1/"
    "community_assignments.csv"
)

OUTDIR = "voynich_func_audit_v1"

os.makedirs(OUTDIR, exist_ok=True)

RANDOM_SEED = 42

N_NULLS = 100

MIN_LINE_LEN = 2

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# =====================================================
# HELPERS
# =====================================================

def build_graph(transitions):

    G = nx.Graph()

    cc = Counter(transitions)

    for (u, v), w in cc.items():

        G.add_edge(
            u,
            v,
            weight=w
        )

    return G

def modularity_and_comms(G):

    comms = greedy_modularity_communities(
        G,
        weight="weight"
    )

    Q = nx.community.modularity(
        G,
        comms,
        weight="weight"
    )

    return Q, comms

def jaccard(a, b):

    a = set(a)
    b = set(b)

    if len(a | b) == 0:
        return 0

    return len(a & b) / len(a | b)

# =====================================================
# LOAD
# =====================================================

print("=== LOAD ===")

df = pd.read_excel(
    INPUT_XLSX,
    sheet_name="tokens_atomic"
)

canon = pd.read_csv(
    CANONICAL_COMMUNITIES
)

canonical_map = dict(
    zip(
        canon["cell_id"],
        canon["community"]
    )
)

# =====================================================
# BUILD FUNC-EXTENDED TOKENS
# =====================================================

print("\n=== FUNC COLLAPSE ===")

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

line_sequences = []

section_sequences = defaultdict(list)

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

    if len(seq) < MIN_LINE_LEN:
        continue

    section = group["section"].iloc[0]

    line_sequences.append(seq)

    section_sequences[section].append(seq)

    for i in range(len(seq)-1):

        transitions.append((
            seq[i],
            seq[i+1]
        ))

print(f"TRANSITIONS: {len(transitions):,}")

# =====================================================
# BUILD GRAPH
# =====================================================

print("\n=== GRAPH ===")

G = build_graph(transitions)

print(
    f"NODES: {G.number_of_nodes()}"
)

print(
    f"EDGES: {G.number_of_edges()}"
)

# =====================================================
# COMMUNITY DETECTION
# =====================================================

print("\n=== COMMUNITIES ===")

Q, comms = modularity_and_comms(G)

print(f"Q = {Q:.6f}")

print(
    f"N_COMMUNITIES = {len(comms)}"
)

# =====================================================
# COMMUNITY MAP
# =====================================================

community_map = {}

for idx, comm in enumerate(comms):

    for node in comm:

        community_map[node] = f"C{idx}"

# =====================================================
# SAVE COMMUNITY ASSIGNMENTS
# =====================================================

rows = []

for node, comm in community_map.items():

    rows.append({
        "node": node,
        "community": comm
    })

comm_df = pd.DataFrame(rows)

comm_df.to_csv(
    f"{OUTDIR}/func_extended_communities.csv",
    index=False
)

# =====================================================
# NULL SHUFFLES
# =====================================================

print("\n=== NULL SHUFFLES ===")

null_Q = []

for i in range(N_NULLS):

    shuffled = []

    for seq in line_sequences:

        s = seq.copy()

        random.shuffle(s)

        for j in range(len(s)-1):

            shuffled.append((
                s[j],
                s[j+1]
            ))

    G_null = build_graph(shuffled)

    q_null, _ = modularity_and_comms(
        G_null
    )

    null_Q.append(q_null)

null_mean = np.mean(null_Q)

null_std = np.std(null_Q)

z = (Q - null_mean) / null_std

p = (
    sum(q >= Q for q in null_Q)
    / len(null_Q)
)

print(f"NULL_MEAN = {null_mean:.6f}")
print(f"NULL_STD  = {null_std:.6f}")
print(f"Z         = {z:.4f}")
print(f"P         = {p:.4f}")

# =====================================================
# SAVE MODULARITY REPORT
# =====================================================

mod_report = {
    "Q": Q,
    "z": z,
    "p": p,
    "n_communities": len(comms)
}

with open(
    f"{OUTDIR}/func_extended_modularity.json",
    "w"
) as f:

    json.dump(
        mod_report,
        f,
        indent=2
    )

# =====================================================
# FUNC COMMUNITY MEMBERSHIP
# =====================================================

print("\n=== FUNC COMMUNITY ===")

func_comm = community_map["FUNC"]

func_edges = 0

total_edges = 0

for u, v, d in G.edges(data=True):

    cu = community_map[u]
    cv = community_map[v]

    if cu == func_comm and cv == func_comm:

        total_edges += d["weight"]

        if u == "FUNC" or v == "FUNC":

            func_edges += d["weight"]

func_share = (
    func_edges / total_edges
    if total_edges else np.nan
)

print(f"FUNC COMMUNITY: {func_comm}")
print(f"FUNC SHARE: {func_share:.6f}")

# =====================================================
# JACCARD OVERLAP
# =====================================================

print("\n=== JACCARD OVERLAP ===")

old_sets = defaultdict(set)

for node, comm in canonical_map.items():

    old_sets[comm].add(node)

new_sets = defaultdict(set)

for node, comm in community_map.items():

    if node != "FUNC":

        new_sets[comm].add(node)

jacc_rows = []

for old_comm, old_nodes in old_sets.items():

    for new_comm, new_nodes in new_sets.items():

        j = jaccard(
            old_nodes,
            new_nodes
        )

        jacc_rows.append({
            "old_comm": old_comm,
            "new_comm": new_comm,
            "jaccard": j
        })

jacc_df = pd.DataFrame(jacc_rows)

jacc_df.to_csv(
    f"{OUTDIR}/func_jaccard_overlap.csv",
    index=False
)

# =====================================================
# SECTION LOADINGS
# =====================================================

print("\n=== SECTION LOADINGS ===")

canonical_loadings = pd.read_csv(
    "voynich_outputs_v1/"
    "section_community_loadings.csv"
)

section_rows = []

for sec, seqs in section_sequences.items():

    counts = Counter()

    total = 0

    for seq in seqs:

        for node in seq:

            comm = community_map[node]

            counts[comm] += 1

            total += 1

    for comm, c in counts.items():

        pct = c / total

        old = canonical_loadings[
            (canonical_loadings["section"] == sec)
            &
            (canonical_loadings["community"] == comm)
        ]

        old_pct = (
            old["pct"].iloc[0]
            if len(old) else 0
        )

        section_rows.append({
            "section": sec,
            "community": comm,
            "pct": pct,
            "delta_from_canonical":
                pct - old_pct
        })

section_df = pd.DataFrame(section_rows)

section_df.to_csv(
    f"{OUTDIR}/func_section_loadings.csv",
    index=False
)

# =====================================================
# DIRECTIONAL BIAS
# =====================================================

print("\n=== DIRECTIONAL BIAS ===")

prev_counts = Counter()

next_counts = Counter()

func_prev_total = 0

func_next_total = 0

for seq in line_sequences:

    for i in range(len(seq)-1):

        a = seq[i]
        b = seq[i+1]

        if b == "FUNC":

            if a != "FUNC":

                prev_counts[
                    community_map[a]
                ] += 1

                func_prev_total += 1

        if a == "FUNC":

            if b != "FUNC":

                next_counts[
                    community_map[b]
                ] += 1

                func_next_total += 1

bias_rows = []

all_comms = sorted(
    set(
        community_map.values()
    )
)

for comm in all_comms:

    bias_rows.append({
        "community": comm,

        "p_func_given_prev":
            (
                prev_counts[comm]
                / func_prev_total
                if func_prev_total
                else np.nan
            ),

        "p_next_given_func":
            (
                next_counts[comm]
                / func_next_total
                if func_next_total
                else np.nan
            )
    })

bias_df = pd.DataFrame(
    bias_rows
)

bias_df.to_csv(
    f"{OUTDIR}/func_directional_bias.csv",
    index=False
)

# =====================================================
# FUNC SELF LOOPS
# =====================================================

print("\n=== FUNC SELF LOOPS ===")

func_self = 0

for seq in line_sequences:

    for i in range(len(seq)-1):

        if (
            seq[i] == "FUNC"
            and
            seq[i+1] == "FUNC"
        ):

            func_self += 1

print(f"FUNC_SELF_LOOPS = {func_self}")

# =====================================================
# FINAL STDOUT
# =====================================================

print("\n=== FINAL ===")

print(json.dumps(mod_report, indent=2))

print(f"FUNC_COMMUNITY = {func_comm}")
print(f"FUNC_SHARE     = {func_share:.6f}")
print(f"FUNC_SELF      = {func_self}")

print("\nWRITTEN:")
print("- func_extended_communities.csv")
print("- func_extended_modularity.json")
print("- func_jaccard_overlap.csv")
print("- func_section_loadings.csv")
print("- func_directional_bias.csv")