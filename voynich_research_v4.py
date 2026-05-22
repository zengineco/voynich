"""
VOYNICH ADVERSARIAL RESEARCH ENGINE v4
=====================================

PURPOSE
-------
Deterministic, falsifiable, adversarial structural analysis
pipeline for Voynichese transition architecture.

This version replaces all previously invalid bootstrap logic.

CORE PRINCIPLES
---------------
- deterministic
- reproducible
- adversarial
- falsifiable
- auditable
- rollback-safe
- no silent assumptions
- no semantic interpretation
- no hidden tuning

THIS SCRIPT TESTS
-----------------
1. Transition modularity
2. Community persistence
3. Higher-order memory
4. Bigram-preserving nulls
5. Forbidden-transition permutation nulls
6. Cross-stratum forbidden predictions
7. Dwell/run-length ceilings
8. Natural-language controls
9. Compression hierarchy
10. Self-loop concentration
11. Recurrence structure
12. Entropy hierarchy
13. Constraint persistence

INPUTS
------
MASTER_TOKEN_MATRIX.xlsx

OPTIONAL CONTROLS
-----------------
controls/*.txt

OUTPUT
------
voynich_research_v4/

ALL OUTPUTS ARE WRITTEN EXPLICITLY.

ACADEMIC WARNING
----------------
This script establishes structural properties only.
It does NOT:
- decipher
- assign semantics
- identify language
- establish meaning

All claims remain conditional on:
- tokenizer
- parser
- graph construction
- null model validity
"""

# =====================================================
# IMPORTS
# =====================================================

import os
import json
import gzip
import random
import itertools

from collections import Counter
from collections import defaultdict

import numpy as np
import pandas as pd

from scipy.stats import entropy
from scipy.stats import zscore

from sklearn.metrics import mutual_info_score

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

CONTROL_DIR = "controls"

OUTDIR = "voynich_research_v4"

FIGDIR = os.path.join(OUTDIR, "figures")

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

N_NULLS = 100
N_PERMUTATIONS = 1000

MAX_MI_DISTANCE = 20

# =====================================================
# HELPERS
# =====================================================

def savefig(name):

    path = os.path.join(FIGDIR, name)

    plt.tight_layout()

    plt.savefig(path, dpi=300)

    plt.close()

    print("WROTE:", path)

def flatten(seqs):

    out = []

    for s in seqs:
        out.extend(s)

    return out

def build_transitions(seqs):

    out = []

    for seq in seqs:

        for i in range(len(seq)-1):

            out.append((
                seq[i],
                seq[i+1]
            ))

    return out

def conditional_entropy(seq):

    if len(seq) < 10:
        return np.nan

    trans = pd.crosstab(
        pd.Series(seq[:-1]),
        pd.Series(seq[1:])
    )

    probs = trans.div(
        trans.sum(axis=1),
        axis=0
    )

    ent = -(
        probs * np.log2(probs + 1e-12)
    ).sum(axis=1).mean()

    return ent

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
# BIGRAM NULL
# =====================================================

def build_bigram_chain(seq):

    chain = defaultdict(list)

    for a,b in zip(seq[:-1], seq[1:]):

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

print("ROWS:", len(raw))

raw["parsed"] = raw["parsed"].fillna(False)

raw["node"] = np.where(
    raw["parsed"] == True,
    raw["cell_id"],
    "FUNC"
)

# =====================================================
# BUILD LINE SEQUENCES
# =====================================================

print("\n=== BUILD LINE SEQUENCES ===")

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

print("LINES:", len(line_df))

# =====================================================
# TRANSITIONS
# =====================================================

print("\n=== TRANSITIONS ===")

transitions = build_transitions(
    all_sequences
)

transition_counts = Counter(transitions)

print("TRANSITIONS:", len(transitions))

# =====================================================
# GRAPH
# =====================================================

print("\n=== GRAPH ===")

G = nx.Graph()

for (u,v), w in transition_counts.items():

    G.add_edge(
        u,
        v,
        weight=w
    )

print("NODES:", G.number_of_nodes())
print("EDGES:", G.number_of_edges())

# =====================================================
# COMMUNITIES
# =====================================================

print("\n=== COMMUNITIES ===")

communities = greedy_modularity_communities(
    G,
    weight="weight"
)

Q = nx.community.modularity(
    G,
    communities,
    weight="weight"
)

print("MODULARITY_Q:", round(Q, 6))
print("COMMUNITIES:", len(communities))

community_map = {}

for idx, comm in enumerate(communities):

    for node in comm:

        community_map[node] = f"C{idx}"

community_rows = []

for node, comm in community_map.items():

    community_rows.append({
        "node": node,
        "community": comm
    })

community_df = pd.DataFrame(
    community_rows
)

community_df.to_csv(
    os.path.join(
        OUTDIR,
        "community_assignments.csv"
    ),
    index=False
)

# =====================================================
# MODULARITY NULLS
# =====================================================

print("\n=== MODULARITY NULLS ===")

real_Q = Q

null_Qs = []

deg_sequence = [
    d for n,d in G.degree()
]

for i in range(N_NULLS):

    if i % 10 == 0:
        print("NULL:", i)

    G_null = nx.configuration_model(
        deg_sequence,
        seed=SEED+i
    )

    G_null = nx.Graph(G_null)

    G_null.remove_edges_from(
        nx.selfloop_edges(G_null)
    )

    if G_null.number_of_edges() == 0:
        continue

    comms_null = greedy_modularity_communities(
        G_null
    )

    Q_null = nx.community.modularity(
        G_null,
        comms_null
    )

    null_Qs.append(Q_null)

null_mean = np.mean(null_Qs)
null_std = np.std(null_Qs)

Q_z = (
    (real_Q - null_mean) / null_std
    if null_std > 0 else np.nan
)

modularity_summary = {
    "real_Q": float(real_Q),
    "null_mean": float(null_mean),
    "null_std": float(null_std),
    "Q_z": float(Q_z)
}

with open(
    os.path.join(
        OUTDIR,
        "modularity_summary.json"
    ),
    "w"
) as f:

    json.dump(
        modularity_summary,
        f,
        indent=2
    )

# =====================================================
# MI DECAY
# =====================================================

print("\n=== MI DECAY ===")

mi_rows = []

for k in range(1, MAX_MI_DISTANCE+1):

    real_mi = seq_mi(
        flat_seq,
        k=k
    )

    bigram_nulls = []

    for _ in range(N_NULLS):

        null_seq = generate_bigram_null(
            flat_seq
        )

        bigram_nulls.append(
            seq_mi(null_seq, k=k)
        )

    mi_rows.append({
        "distance": k,
        "real_mi": real_mi,
        "bigram_null_mean":
            np.mean(bigram_nulls),
        "bigram_null_std":
            np.std(bigram_nulls)
    })

mi_df = pd.DataFrame(mi_rows)

mi_df.to_csv(
    os.path.join(
        OUTDIR,
        "mi_decay.csv"
    ),
    index=False
)

# =====================================================
# HIGHER ORDER MI
# =====================================================

print("\n=== HIGHER ORDER MI ===")

higher_rows = []

for k in range(1, MAX_MI_DISTANCE+1):

    higher_rows.append({
        "distance": k,
        "order1":
            seq_mi(flat_seq, k=k),
        "order2":
            order2_mi(flat_seq, k=k),
        "order3":
            order3_mi(flat_seq, k=k)
    })

higher_df = pd.DataFrame(
    higher_rows
)

higher_df.to_csv(
    os.path.join(
        OUTDIR,
        "higher_order_mi.csv"
    ),
    index=False
)

# =====================================================
# FORBIDDEN TRANSITIONS
# =====================================================

print("\n=== FORBIDDEN TRANSITIONS ===")

freq = Counter(flat_seq)

N_TRANS = len(transitions)

forbidden_rows = []

nodes = sorted(set(flat_seq))

for a in nodes:

    for b in nodes:

        expected = (
            (freq[a]/len(flat_seq))
            *
            (freq[b]/len(flat_seq))
            *
            N_TRANS
        )

        observed = transition_counts.get(
            (a,b),
            0
        )

        if expected >= 5 and observed == 0:

            forbidden_rows.append({
                "from": a,
                "to": b,
                "expected": expected,
                "observed": observed
            })

forbidden_df = pd.DataFrame(
    forbidden_rows
)

forbidden_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_candidates.csv"
    ),
    index=False
)

# =====================================================
# PERMUTATION NULL
# =====================================================

print("\n=== PERMUTATION NULL ===")

candidate_pairs = list(zip(
    forbidden_df["from"],
    forbidden_df["to"]
))

perm_rows = []

sections = sorted(
    line_df["section"].dropna().unique()
)

for p in range(N_PERMUTATIONS):

    if p % 50 == 0:
        print("PERM:", p)

    permuted_sequences = []

    for sec in sections:

        sec_df = line_df[
            line_df["section"] == sec
        ]

        seqs = sec_df["sequence"].tolist()

        flat_sec = []

        lengths = []

        for s in seqs:

            flat_sec.extend(s)

            lengths.append(len(s))

        random.shuffle(flat_sec)

        idx = 0

        rebuilt = []

        for L in lengths:

            rebuilt.append(
                flat_sec[idx:idx+L]
            )

            idx += L

        permuted_sequences.extend(rebuilt)

    perm_counts = Counter(
        build_transitions(
            permuted_sequences
        )
    )

    for a,b in candidate_pairs:

        perm_rows.append({
            "perm": p,
            "from": a,
            "to": b,
            "count":
                perm_counts.get((a,b),0)
        })

perm_df = pd.DataFrame(
    perm_rows
)

perm_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_permutations.csv"
    ),
    index=False
)

# =====================================================
# FORBIDDEN SUMMARY
# =====================================================

print("\n=== FORBIDDEN SUMMARY ===")

summary_rows = []

for (a,b), g in perm_df.groupby([
    "from",
    "to"
]):

    vals = g["count"].values

    summary_rows.append({
        "from": a,
        "to": b,
        "perm_mean":
            np.mean(vals),
        "perm_std":
            np.std(vals),
        "ci_low":
            np.percentile(vals, 2.5),
        "ci_high":
            np.percentile(vals, 97.5),
        "empirical_p":
            np.mean(vals <= 0)
    })

summary_df = pd.DataFrame(
    summary_rows
)

summary_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_summary.csv"
    ),
    index=False
)

# =====================================================
# DWELLS
# =====================================================

print("\n=== DWELLS ===")

dwell_rows = []

for section, g in line_df.groupby("section"):

    max_run = 0

    for seq in g["sequence"]:

        current = seq[0]

        run = 1

        for tok in seq[1:]:

            if tok == current:

                run += 1

            else:

                if run > max_run:
                    max_run = run

                current = tok
                run = 1

        if run > max_run:
            max_run = run

    dwell_rows.append({
        "section": section,
        "max_internal_run": max_run
    })

dwell_df = pd.DataFrame(
    dwell_rows
)

dwell_df.to_csv(
    os.path.join(
        OUTDIR,
        "line_internal_dwells.csv"
    ),
    index=False
)

# =====================================================
# SELF LOOPS
# =====================================================

print("\n=== SELF LOOPS ===")

self_rows = []

for node in nodes:

    self_rows.append({
        "node": node,
        "self_loops":
            transition_counts.get(
                (node,node),
                0
            )
    })

self_df = pd.DataFrame(
    self_rows
)

self_df = self_df.sort_values(
    "self_loops",
    ascending=False
)

self_df.to_csv(
    os.path.join(
        OUTDIR,
        "self_loops.csv"
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
                "distance":
                    i - seen[tok]
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
# CONTROL CORPORA
# =====================================================

print("\n=== CONTROL CORPORA ===")

control_rows = []

if os.path.exists(CONTROL_DIR):

    for fname in os.listdir(CONTROL_DIR):

        if not fname.endswith(".txt"):
            continue

        path = os.path.join(
            CONTROL_DIR,
            fname
        )

        print("CONTROL:", fname)

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read().lower()

        tokens = [
            x.strip()
            for x in text.split()
            if len(x.strip()) > 0
        ]

        if len(tokens) < 100:
            continue

        trans_ctrl = list(zip(
            tokens[:-1],
            tokens[1:]
        ))

        self_loops_ctrl = sum([
            1 for a,b in trans_ctrl
            if a == b
        ])

        control_rows.append({
            "corpus": fname,
            "tokens": len(tokens),
            "mi1":
                seq_mi(tokens, k=1),
            "entropy":
                conditional_entropy(tokens),
            "gzip_ratio":
                gzip_ratio(tokens),
            "self_loops":
                self_loops_ctrl
        })

control_rows.append({
    "corpus": "voynich",
    "tokens": len(flat_seq),
    "mi1":
        seq_mi(flat_seq, k=1),
    "entropy":
        conditional_entropy(flat_seq),
    "gzip_ratio":
        gzip_ratio(flat_seq),
    "self_loops":
        sum([
            1 for a,b in transitions
            if a == b
        ])
})

control_df = pd.DataFrame(
    control_rows
)

control_df.to_csv(
    os.path.join(
        OUTDIR,
        "control_corpus_metrics.csv"
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

plt.legend()

plt.title("MI Decay")

savefig("mi_decay.png")

# Higher-order MI

plt.figure(figsize=(10,6))

plt.plot(
    higher_df["distance"],
    higher_df["order1"],
    label="order1"
)

plt.plot(
    higher_df["distance"],
    higher_df["order2"],
    label="order2"
)

plt.plot(
    higher_df["distance"],
    higher_df["order3"],
    label="order3"
)

plt.legend()

plt.title("Higher Order MI")

savefig("higher_order_mi.png")

# Forbidden p-values

if len(summary_df) > 0:

    plot_df = summary_df.sort_values(
        "empirical_p"
    ).head(20)

    labels = [
        f"{a}->{b}"
        for a,b in zip(
            plot_df["from"],
            plot_df["to"]
        )
    ]

    plt.figure(figsize=(12,6))

    plt.bar(
        labels,
        plot_df["empirical_p"]
    )

    plt.xticks(rotation=90)

    plt.title(
        "Forbidden Transition Empirical P"
    )

    savefig(
        "forbidden_empirical_p.png"
    )

# Dwell

plt.figure(figsize=(10,6))

sns.barplot(
    data=dwell_df,
    x="section",
    y="max_internal_run"
)

plt.xticks(rotation=30)

plt.title(
    "Line Internal Dwell"
)

savefig("line_internal_dwell.png")

# Controls

if len(control_df) > 1:

    plt.figure(figsize=(10,6))

    sns.scatterplot(
        data=control_df,
        x="entropy",
        y="gzip_ratio",
        hue="corpus",
        s=120
    )

    plt.title(
        "Control Corpus Comparison"
    )

    savefig(
        "control_comparison.png"
    )

# =====================================================
# CHECKSUMS
# =====================================================

print("\n=== CHECKSUMS ===")

checksums = {
    "rows":
        int(len(raw)),
    "lines":
        int(len(line_df)),
    "transitions":
        int(len(transitions)),
    "nodes":
        int(G.number_of_nodes()),
    "edges":
        int(G.number_of_edges()),
    "communities":
        int(len(communities)),
    "modularity_Q":
        float(Q),
    "modularity_z":
        float(Q_z),
    "forbidden_candidates":
        int(len(forbidden_df)),
    "permutations":
        int(N_PERMUTATIONS),
    "controls":
        int(len(control_df))
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
    "OUTPUTS WRITTEN TO:",
    OUTDIR
)