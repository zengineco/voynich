"""
VOYNICH ADVERSARIAL ENGINE v3
=====================================

PURPOSE:
Adversarial falsification + higher-order structure testing.

Implements:
1. Bigram-preserving nulls
2. Higher-order MI decay
3. Dwell-time dynamics
4. Constraint persistence
5. Compression hierarchy
6. Attractor persistence
7. Community recurrence
8. Dynamical stability
9. Null-vs-real topology tests

INPUT:
MASTER_TOKEN_MATRIX.xlsx

OUTPUT:
voynich_adversarial_outputs_v3/

ACADEMIC PRINCIPLES:
- deterministic
- versioned
- adversarial
- reproducible
- explicitly falsifiable
"""

# =====================================================
# IMPORTS
# =====================================================

import os
import json
import gzip
import random
import itertools

from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from scipy.stats import entropy
from scipy.stats import zscore
from scipy.spatial.distance import cosine

from sklearn.metrics import mutual_info_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import networkx as nx

from networkx.algorithms.community import (
    greedy_modularity_communities
)

import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================
# CONFIG
# =====================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_adversarial_outputs_v3"

FIGDIR = os.path.join(OUTDIR, "figures")

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

N_NULLS = 100

MAX_MI_DISTANCE = 20

# =====================================================
# HELPERS
# =====================================================

def savefig(name):

    path = os.path.join(FIGDIR, name)

    plt.tight_layout()

    plt.savefig(path, dpi=300)

    plt.close()

    print(f"WROTE FIGURE: {path}")

def flatten(seqs):

    out = []

    for s in seqs:
        out.extend(s)

    return out

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

def modularity_score(G):

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

def seq_mi(seq, k=1):

    if len(seq) <= k:
        return np.nan

    a = seq[:-k]
    b = seq[k:]

    return mutual_info_score(a, b)

def order2_mi(seq, k=1):

    if len(seq) <= k + 1:
        return np.nan

    prev = [
        f"{seq[i]}|||{seq[i+1]}"
        for i in range(len(seq)-k-1)
    ]

    nxt = seq[k+1:]

    return mutual_info_score(prev, nxt)


def order3_mi(seq, k=1):

    if len(seq) <= k + 2:
        return np.nan

    prev = [
        f"{seq[i]}|||{seq[i+1]}|||{seq[i+2]}"
        for i in range(len(seq)-k-2)
    ]

    nxt = seq[k+2:]

    return mutual_info_score(prev, nxt)

def gzip_ratio(tokens):

    txt = " ".join(tokens)

    raw = txt.encode("utf-8")

    comp = gzip.compress(raw)

    return len(comp) / max(len(raw), 1)

# =====================================================
# BIGRAM-PRESERVING NULL
# =====================================================

def build_bigram_chain(seq):

    chain = defaultdict(list)

    for a, b in zip(seq[:-1], seq[1:]):
        chain[a].append(b)

    return chain

def generate_bigram_null(seq):

    chain = build_bigram_chain(seq)

    current = random.choice(seq)

    out = [current]

    for _ in range(len(seq)-1):

        nxts = chain.get(current)

        if not nxts:
            current = random.choice(seq)
        else:
            current = random.choice(nxts)

        out.append(current)

    return out

# =====================================================
# LOAD
# =====================================================

print("\n=== LOAD ===")

raw = pd.read_excel(
    INPUT_XLSX,
    sheet_name="tokens_atomic"
)

print(f"ROWS: {len(raw):,}")

raw["parsed"] = raw["parsed"].fillna(False)

raw["node"] = np.where(
    raw["parsed"] == True,
    raw["cell_id"],
    "FUNC"
)

# =====================================================
# BUILD SEQUENCES
# =====================================================

print("\n=== BUILD SEQUENCES ===")

line_records = []

for (folio, locus), group in raw.groupby([
    "folio",
    "locus"
]):

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

    line_records.append({
        "folio": folio,
        "locus": locus,
        "section": group["section"].iloc[0],
        "sequence": seq
    })

line_df = pd.DataFrame(line_records)

all_sequences = line_df["sequence"].tolist()

flat_seq = flatten(all_sequences)

print(f"LINES: {len(line_df):,}")

# =====================================================
# TRANSITIONS
# =====================================================

print("\n=== TRANSITIONS ===")

transitions = []

for seq in all_sequences:

    for i in range(len(seq)-1):

        transitions.append((
            seq[i],
            seq[i+1]
        ))

print(f"TRANSITIONS: {len(transitions):,}")

# =====================================================
# GRAPH + COMMUNITIES
# =====================================================

print("\n=== COMMUNITIES ===")

G = build_graph(transitions)

Q, comms = modularity_score(G)

print(f"Q: {Q:.6f}")
print(f"COMMUNITIES: {len(comms)}")

community_map = {}

for idx, comm in enumerate(comms):

    for node in comm:

        community_map[node] = f"C{idx}"

# =====================================================
# BIGRAM NULL MI
# =====================================================

print("\n=== BIGRAM NULL MI ===")

mi_rows = []

for k in range(1, MAX_MI_DISTANCE + 1):

    real = seq_mi(flat_seq, k=k)

    unigram_nulls = []
    bigram_nulls = []

    for _ in range(N_NULLS):

        # unigram shuffle

        s1 = flat_seq.copy()

        random.shuffle(s1)

        unigram_nulls.append(
            seq_mi(s1, k=k)
        )

        # bigram-preserving

        s2 = generate_bigram_null(flat_seq)

        bigram_nulls.append(
            seq_mi(s2, k=k)
        )

    uni_mean = np.mean(unigram_nulls)
    uni_std = np.std(unigram_nulls)

    bi_mean = np.mean(bigram_nulls)
    bi_std = np.std(bigram_nulls)

    uni_z = (
        (real - uni_mean) / uni_std
        if uni_std > 0 else np.nan
    )

    bi_z = (
        (real - bi_mean) / bi_std
        if bi_std > 0 else np.nan
    )

    mi_rows.append({
        "distance": k,
        "real_mi": real,
        "unigram_null_mean": uni_mean,
        "bigram_null_mean": bi_mean,
        "unigram_z": uni_z,
        "bigram_z": bi_z
    })

mi_df = pd.DataFrame(mi_rows)

mi_df.to_csv(
    os.path.join(
        OUTDIR,
        "mi_bigram_null.csv"
    ),
    index=False
)

# =====================================================
# HIGHER-ORDER MI
# =====================================================

print("\n=== HIGHER ORDER MI ===")

ho_rows = []

for k in range(1, MAX_MI_DISTANCE + 1):

    o1 = seq_mi(flat_seq, k=k)

    o2 = order2_mi(flat_seq, k=k)

    o3 = order3_mi(flat_seq, k=k)

    ho_rows.append({
        "distance": k,
        "order1_mi": o1,
        "order2_mi": o2,
        "order3_mi": o3
    })

ho_df = pd.DataFrame(ho_rows)

ho_df.to_csv(
    os.path.join(
        OUTDIR,
        "higher_order_mi.csv"
    ),
    index=False
)

# =====================================================
# DWELL TIMES
# =====================================================

print("\n=== DWELL TIMES ===")

dwell_rows = []

for seq in all_sequences:

    cseq = [
        community_map.get(x, "NA")
        for x in seq
    ]

    current = cseq[0]
    run = 1

    for tok in cseq[1:]:

        if tok == current:

            run += 1

        else:

            dwell_rows.append({
                "community": current,
                "dwell": run
            })

            current = tok
            run = 1

    dwell_rows.append({
        "community": current,
        "dwell": run
    })

dwell_df = pd.DataFrame(dwell_rows)

dwell_df.to_csv(
    os.path.join(
        OUTDIR,
        "dwell_times.csv"
    ),
    index=False
)

# =====================================================
# ATTRACTOR STATES
# =====================================================

print("\n=== ATTRACTOR STATES ===")

self_loops = Counter()

for a, b in transitions:

    if a == b:
        self_loops[a] += 1

loop_df = pd.DataFrame([
    {
        "node": k,
        "self_loops": v
    }
    for k, v in self_loops.items()
])

loop_df = loop_df.sort_values(
    "self_loops",
    ascending=False
)

loop_df.to_csv(
    os.path.join(
        OUTDIR,
        "self_loops.csv"
    ),
    index=False
)

# =====================================================
# CONSTRAINT PERSISTENCE
# =====================================================

print("\n=== CONSTRAINT PERSISTENCE ===")

nodes = sorted(set(flat_seq))

freq = Counter(flat_seq)

N = len(transitions)

obs = Counter(transitions)

constraint_rows = []

for a in nodes:

    for b in nodes:

        expected = (
            (freq[a]/len(flat_seq))
            *
            (freq[b]/len(flat_seq))
            *
            N
        )

        observed = obs.get((a,b), 0)

        constraint_rows.append({
            "from": a,
            "to": b,
            "expected": expected,
            "observed": observed,
            "forbidden_candidate":
                int(expected > 5 and observed == 0)
        })

constraint_df = pd.DataFrame(
    constraint_rows
)

constraint_df.to_csv(
    os.path.join(
        OUTDIR,
        "constraint_persistence.csv"
    ),
    index=False
)

# =====================================================
# COMPRESSION HIERARCHY
# =====================================================

print("\n=== COMPRESSION HIERARCHY ===")

community_seq = [
    community_map.get(x, "NA")
    for x in flat_seq
]

compression_rows = []

compression_rows.append({
    "representation": "raw",
    "gzip_ratio": gzip_ratio(flat_seq)
})

compression_rows.append({
    "representation": "community",
    "gzip_ratio": gzip_ratio(community_seq)
})

compression_df = pd.DataFrame(
    compression_rows
)

compression_df.to_csv(
    os.path.join(
        OUTDIR,
        "compression_hierarchy.csv"
    ),
    index=False
)

# =====================================================
# RECURRENCE
# =====================================================

print("\n=== RECURRENCE ===")

recurrence_rows = []

for seq in all_sequences:

    seen = {}

    for i, tok in enumerate(seq):

        if tok in seen:

            recurrence_rows.append({
                "token": tok,
                "distance": i - seen[tok]
            })

        seen[tok] = i

recurrence_df = pd.DataFrame(
    recurrence_rows
)

recurrence_df.to_csv(
    os.path.join(
        OUTDIR,
        "recurrence.csv"
    ),
    index=False
)

# =====================================================
# VISUALIZATIONS
# =====================================================

print("\n=== VISUALIZATIONS ===")

# MI

plt.figure(figsize=(10,6))

plt.plot(
    mi_df["distance"],
    mi_df["real_mi"],
    label="real"
)

plt.plot(
    mi_df["distance"],
    mi_df["bigram_null_mean"],
    label="bigram_null"
)

plt.xlabel("distance")
plt.ylabel("MI")
plt.title("MI Decay vs Bigram Null")

plt.legend()

savefig("mi_vs_bigram_null.png")

# Higher-order MI

plt.figure(figsize=(10,6))

plt.plot(
    ho_df["distance"],
    ho_df["order1_mi"],
    label="order1"
)

plt.plot(
    ho_df["distance"],
    ho_df["order2_mi"],
    label="order2"
)

plt.plot(
    ho_df["distance"],
    ho_df["order3_mi"],
    label="order3"
)

plt.xlabel("distance")
plt.ylabel("MI")
plt.title("Higher Order MI")

plt.legend()

savefig("higher_order_mi.png")

# Dwell

plt.figure(figsize=(10,6))

sns.boxplot(
    data=dwell_df,
    x="community",
    y="dwell"
)

plt.title("Community Dwell Times")

savefig("dwell_times.png")

# Constraint heatmap

pivot = constraint_df.pivot(
    index="from",
    columns="to",
    values="forbidden_candidate"
)

plt.figure(figsize=(16,14))

sns.heatmap(
    pivot.fillna(0),
    cmap="viridis"
)

plt.title("Forbidden Transition Candidates")

savefig("forbidden_transition_candidates.png")

# Compression

plt.figure(figsize=(6,5))

plt.bar(
    compression_df["representation"],
    compression_df["gzip_ratio"]
)

plt.title("Compression Hierarchy")

savefig("compression_hierarchy.png")

# =====================================================
# CHECKSUMS
# =====================================================

print("\n=== CHECKSUMS ===")

checksums = {
    "rows": int(len(raw)),
    "lines": int(len(line_df)),
    "transitions": int(len(transitions)),
    "nodes": int(G.number_of_nodes()),
    "edges": int(G.number_of_edges()),
    "Q": float(Q),
    "communities": int(len(comms))
}

with open(
    os.path.join(
        OUTDIR,
        "checksums.json"
    ),
    "w"
) as f:

    json.dump(
        checksums,
        f,
        indent=2
    )

print(json.dumps(
    checksums,
    indent=2
))

print("\n=== COMPLETE ===")

print(
    f"OUTPUTS WRITTEN TO: {OUTDIR}"
)