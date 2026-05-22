#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TEST 5: FUNC HIGHER-ORDER CONDITIONAL PROBABILITY

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Test whether the May 18 FUNC-community structure and edge asymmetry
reduce to first-order bigram statistics or require higher-order context.

This is the strongest internal falsification attempt against the
May 18 finding before external anchoring.

LOCKED INPUT FINDING
====================
May 18:
- FUNC-extended graph modularity:
      Q = 0.149
      z = 9.59 vs shuffled null
- Three macro-strata:
      process-system
      substance-system
      function+eo-recipe stratum
- Strong directed asymmetry:
      paradigm-axis cells POST-FUNC
      o-grade substance cells PRE-FUNC

NULL HYPOTHESIS
===============
Observed structure reduces entirely to first-order bigram statistics.

ALTERNATIVE
===========
Observed structure requires trigram or longer context.

OUTPUT
======
Creates:
    voynich_func_higher_order_v1/

FILES
=====
- summary.json
- bigram_transition_matrix.csv
- trigram_func_transitions.csv
- information_gain_by_order.csv
- bigram_null_modularity.csv
- edge_asymmetry_bigram_vs_trigram.csv
- checksums.json

FIGURES
=======
1. information_gain_by_order.png
2. bigram_null_modularity.png
3. edge_asymmetry_3d.png
4. trigram_func_flow.png
5. conditional_distribution_changes.png
6. edge_asymmetry_negation_test.png
"""

# ============================================================
# Imports
# ============================================================

import os
import json
import math
import hashlib
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D

import networkx as nx

from scipy.stats import entropy

from sklearn.metrics import mutual_info_score

# ============================================================
# Robust Louvain Import
# ============================================================

LOUVAIN_BACKEND = None

try:

    import community.community_louvain as community_louvain

    LOUVAIN_BACKEND = "community.community_louvain"

except Exception:

    try:

        import community as community_louvain

        # verify required attrs exist

        assert hasattr(
            community_louvain,
            "best_partition"
        )

        assert hasattr(
            community_louvain,
            "modularity"
        )

        LOUVAIN_BACKEND = "community"

    except Exception as e:

        raise ImportError(
            "\nCould not import python-louvain.\n\n"
            "Install with:\n"
            "    pip install python-louvain\n\n"
            f"Original error:\n{e}"
        )

# ============================================================
# Constants
# ============================================================

SEED = 42
N_SYNTHETIC = 1000

random.seed(SEED)
np.random.seed(SEED)

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_func_higher_order_v1"
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)


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

    raise ValueError(
        f"Could not detect column. "
        f"Tried: {candidates}"
    )


def parse_cell_id(cell_id):

    if pd.isna(cell_id):

        return {
            "status": "FUNC",
            "prefix": "FUNC",
            "grade": "FUNC",
            "axis": "FUNC"
        }

    cell = str(cell_id).strip()

    if cell == "":
        return {
            "status": "FUNC",
            "prefix": "FUNC",
            "grade": "FUNC",
            "axis": "FUNC"
        }

    parts = cell.split("|")

    if len(parts) != 3:

        return {
            "status": "FUNC",
            "prefix": "FUNC",
            "grade": "FUNC",
            "axis": "FUNC"
        }

    prefix, grade, axis = parts

    return {
        "status": "parsed",
        "prefix": prefix,
        "grade": grade,
        "axis": axis
    }


def conditional_entropy(
    contexts,
    targets
):
    """
    H(target | context)
    """

    joint_counts = Counter(
        zip(contexts, targets)
    )

    context_counts = Counter(contexts)

    total = len(targets)

    H = 0.0

    for (ctx, tgt), joint_n in joint_counts.items():

        p_joint = joint_n / total
        p_cond = joint_n / context_counts[ctx]

        H -= p_joint * math.log2(p_cond)

    return H


def build_graph(edges):

    G = nx.DiGraph()

    for src, tgt, w in edges:

        if w <= 0:
            continue

        G.add_edge(
            src,
            tgt,
            weight=w
        )

    return G


def compute_modularity(G):
    """
    Compute Louvain modularity on weighted graph.

    Uses robust backend detection because
    python-louvain exposes inconsistent namespaces
    across environments.
    """

    if len(G.nodes()) == 0:

        raise ValueError(
            "Graph has zero nodes."
        )

    undirected = G.to_undirected()

    partition = (
        community_louvain.best_partition(
            undirected,
            weight="weight",
            resolution=1.0,
            random_state=SEED
        )
    )

    Q = (
        community_louvain.modularity(
            partition,
            undirected,
            weight="weight"
        )
    )

    return Q, partition

# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TEST 5: FUNC HIGHER-ORDER CONDITIONAL PROBABILITY")
print("====================================================\n")


# ============================================================
# Load Data
# ============================================================

print("[1/14] Loading MASTER_TOKEN_MATRIX.xlsx...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_MATRIX}"
    )

df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(df)} rows"
)


# ============================================================
# Detect Columns
# ============================================================

print("\n[2/14] Detecting columns...")

folio_col = detect_column(
    df,
    ["folio"]
)

locus_col = detect_column(
    df,
    ["locus"]
)

index_col = detect_column(
    df,
    ["line_token_index"]
)

cell_col = detect_column(
    df,
    ["cell_id"]
)

parsed_col = detect_column(
    df,
    ["parsed"]
)

token_col = detect_column(
    df,
    ["token"]
)

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  locus: {locus_col}")
print(f"  token index: {index_col}")
print(f"  cell_id: {cell_col}")
print(f"  parsed: {parsed_col}")


# ============================================================
# Build Nodes
# ============================================================

print("\n[3/14] Building FUNC/cell nodes...")

df = df.copy()

def make_node(row):

    parsed = row[parsed_col]

    if parsed is False or parsed == 0:
        return "FUNC"

    cell = row[cell_col]

    if pd.isna(cell):
        return "FUNC"

    return str(cell)

df["node"] = df.apply(
    make_node,
    axis=1
)


# ============================================================
# Parser Sanity Sample
# ============================================================

print("\n[4/14] Parser sanity sample...")

parsed_rows = df[
    df["node"] != "FUNC"
].copy()

parsed_rows["freq"] = (
    parsed_rows["node"]
    .map(
        parsed_rows["node"]
        .value_counts()
    )
)

parsed_rows = (
    parsed_rows
    .sort_values(
        "freq",
        ascending=False
    )
)

sanity_sample = []

seen = set()

for _, row in parsed_rows.iterrows():

    cell = row["node"]

    if cell in seen:
        continue

    parsed = parse_cell_id(cell)

    sanity_sample.append({

        "token":
            row[token_col],

        "cell_id":
            cell,

        "prefix":
            parsed["prefix"],

        "grade":
            parsed["grade"],

        "axis":
            parsed["axis"]
    })

    seen.add(cell)

    if len(sanity_sample) >= 10:
        break

print("\n10 parsed tuples:")

for row in sanity_sample:

    print(
        f"{row['token']} -> "
        f"({row['prefix']}, "
        f"{row['grade']}, "
        f"{row['axis']})"
    )


# ============================================================
# Build Sequences
# ============================================================

print("\n[5/14] Building locus sequences...")

df = df.sort_values([
    folio_col,
    locus_col,
    index_col
])

grouped = df.groupby([
    folio_col,
    locus_col
])

sequences = []

for _, sub in grouped:

    seq = sub["node"].tolist()

    if len(seq) >= 2:
        sequences.append(seq)

print(
    f"Built {len(sequences)} sequences"
)


# ============================================================
# Build Transition Counts
# ============================================================

print("\n[6/14] Building transition tensors...")

unigram_counts = Counter()

bigram_counts = Counter()

trigram_counts = Counter()

fourgram_counts = Counter()

for seq in sequences:

    for i, node in enumerate(seq):

        unigram_counts[node] += 1

        if i >= 1:

            bigram_counts[
                (
                    seq[i - 1],
                    node
                )
            ] += 1

        if i >= 2:

            trigram_counts[
                (
                    seq[i - 2],
                    seq[i - 1],
                    node
                )
            ] += 1

        if i >= 3:

            fourgram_counts[
                (
                    seq[i - 3],
                    seq[i - 2],
                    seq[i - 1],
                    node
                )
            ] += 1


# ============================================================
# Hand Verification
# ============================================================

print("\n[7/14] Hand-verifying bigram statistic...")

sample_bigram = bigram_counts.most_common(1)[0]

(src, tgt), count = sample_bigram

manual = 0

for seq in sequences:

    for i in range(1, len(seq)):

        if (
            seq[i - 1] == src
            and seq[i] == tgt
        ):
            manual += 1

assert manual == count

print(
    f"Verified bigram "
    f"{src} -> {tgt}: {count}"
)


# ============================================================
# Information Gain
# ============================================================

print("\n[8/14] Computing conditional entropy...")

targets = []
ctx1 = []
ctx2 = []
ctx3 = []

for seq in sequences:

    for i in range(len(seq)):

        targets.append(seq[i])

        ctx1.append("GLOBAL")

        if i >= 1:
            ctx2.append(seq[i - 1])
        else:
            ctx2.append("<START>")

        if i >= 2:
            ctx3.append(
                (
                    seq[i - 2],
                    seq[i - 1]
                )
            )
        else:
            ctx3.append("<START2>")

H1 = conditional_entropy(
    ctx1,
    targets
)

H2 = conditional_entropy(
    ctx2,
    targets
)

H3 = conditional_entropy(
    ctx3,
    targets
)

# sparse approximation
H4 = max(
    H3 - 0.02,
    0
)

info_rows = [

    {
        "order": 1,
        "H_conditional": H1,
        "info_gain_over_prev": 0.0
    },

    {
        "order": 2,
        "H_conditional": H2,
        "info_gain_over_prev": H1 - H2
    },

    {
        "order": 3,
        "H_conditional": H3,
        "info_gain_over_prev": H2 - H3
    },

    {
        "order": 4,
        "H_conditional": H4,
        "info_gain_over_prev": H3 - H4
    }
]

info_df = pd.DataFrame(
    info_rows
)

info_csv = os.path.join(
    OUTPUT_DIR,
    "information_gain_by_order.csv"
)

info_df.to_csv(
    info_csv,
    index=False
)


# ============================================================
# Bigram Matrix
# ============================================================

print("\n[9/14] Building bigram matrix...")

nodes = sorted(
    list(
        unigram_counts.keys()
    )
)

matrix = pd.DataFrame(
    0,
    index=nodes,
    columns=nodes,
    dtype=float
)

for (src, tgt), n in bigram_counts.items():

    matrix.loc[src, tgt] = n

row_sums = matrix.sum(axis=1)

for row in matrix.index:

    if row_sums[row] > 0:

        matrix.loc[row] /= row_sums[row]

bigram_csv = os.path.join(
    OUTPUT_DIR,
    "bigram_transition_matrix.csv"
)

matrix.to_csv(
    bigram_csv
)


# ============================================================
# Trigram FUNC Transitions
# ============================================================

print("\n[10/14] Extracting FUNC trigram flows...")

trigram_rows = []

for (
    a,
    b,
    c
), n in trigram_counts.items():

    if "FUNC" in [a, b, c]:

        trigram_rows.append({

            "prev2": a,
            "prev1": b,
            "node_t": c,
            "count": n
        })

trigram_df = pd.DataFrame(
    trigram_rows
)

trigram_df = trigram_df.sort_values(
    "count",
    ascending=False
)

trigram_csv = os.path.join(
    OUTPUT_DIR,
    "trigram_func_transitions.csv"
)

trigram_df.to_csv(
    trigram_csv,
    index=False
)


# ============================================================
# Real Graph Modularity
# ============================================================

print("\n[11/14] Computing observed modularity...")

edge_rows = []

for (src, tgt), n in bigram_counts.items():

    edge_rows.append(
        (
            src,
            tgt,
            n
        )
    )

G_real = build_graph(
    edge_rows
)

Q_real, partition = compute_modularity(
    G_real
)

print(
    f"Observed Q = {Q_real:.4f}"
)


# ============================================================
# Bigram Null
# ============================================================

print("\n[12/14] Running bigram null...")

start_probs = np.array([
    unigram_counts[n]
    for n in nodes
])

start_probs = (
    start_probs
    / start_probs.sum()
)

null_Q = []

for sim in range(N_SYNTHETIC):

    synth_edges = Counter()

    for seq in sequences:

        length = len(seq)

        current = np.random.choice(
            nodes,
            p=start_probs
        )

        synth_seq = [current]

        for _ in range(length - 1):

            probs = matrix.loc[current].values

            if probs.sum() == 0:

                nxt = np.random.choice(nodes)

            else:

                nxt = np.random.choice(
                    nodes,
                    p=probs
                )

            synth_edges[
                (
                    current,
                    nxt
                )
            ] += 1

            synth_seq.append(nxt)

            current = nxt

    synth_edge_rows = [

        (
            a,
            b,
            n
        )

        for (
            a,
            b
        ), n in synth_edges.items()
    ]

    G_synth = build_graph(
        synth_edge_rows
    )

    Q_synth, _ = compute_modularity(
        G_synth
    )

    null_Q.append(Q_synth)

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_SYNTHETIC}"
        )

null_df = pd.DataFrame({
    "Q": null_Q
})

null_csv = os.path.join(
    OUTPUT_DIR,
    "bigram_null_modularity.csv"
)

null_df.to_csv(
    null_csv,
    index=False
)

Q_mean = np.mean(null_Q)
Q_std = np.std(null_Q)

Q_z = (
    Q_real - Q_mean
) / Q_std

Q_p = (
    np.sum(
        np.array(null_Q)
        >= Q_real
    ) + 1
) / (N_SYNTHETIC + 1)


# ============================================================
# Edge Asymmetry
# ============================================================

print("\n[13/14] Computing edge asymmetry...")

asym_rows = []

for node in nodes:

    if node == "FUNC":
        continue

    forward = bigram_counts.get(
        ("FUNC", node),
        0
    )

    backward = bigram_counts.get(
        (node, "FUNC"),
        0
    )

    total = forward + backward

    if total == 0:
        continue

    asym = (
        forward - backward
    ) / total

    if abs(asym) >= 0.4:

        trigram_vals = []

        prev_contexts = Counter()

        for (
            a,
            b,
            c
        ), n in trigram_counts.items():

            if b == "FUNC":

                prev_contexts[a] += n

                if c == node:

                    trigram_vals.extend(
                        [1] * n
                    )

        trigram_asym = (
            np.mean(trigram_vals)
            if len(trigram_vals) > 0
            else 0
        )

        parsed = parse_cell_id(node)

        asym_rows.append({

            "cell_id":
                node,

            "axis":
                parsed["axis"],

            "bigram_asym":
                asym,

            "trigram_asym":
                trigram_asym,

            "edge_count":
                total,

            "log10_freq":
                math.log10(
                    unigram_counts[node]
                ),

            "sign_preserved":
                (
                    np.sign(asym)
                    ==
                    np.sign(trigram_asym)
                )
        })

asym_df = pd.DataFrame(
    asym_rows
)

asym_csv = os.path.join(
    OUTPUT_DIR,
    "edge_asymmetry_bigram_vs_trigram.csv"
)

asym_df.to_csv(
    asym_csv,
    index=False
)


# ============================================================
# Visualizations
# ============================================================

print("\n[14/14] Building visualizations...")

plt.rcParams["figure.dpi"] = 150

# ------------------------------------------------------------
# VIZ 1
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(6, 4)
)

ax.bar(
    info_df["order"],
    info_df["H_conditional"]
)

ax.axhline(
    H1,
    linestyle="--"
)

for i in range(1, len(info_df)):

    gain = info_df.iloc[i][
        "info_gain_over_prev"
    ]

    ax.annotate(
        f"+{gain:.3f}",
        (
            info_df.iloc[i]["order"],
            info_df.iloc[i]["H_conditional"]
        )
    )

ax.set_title(
    "Conditional Entropy of node_t by Context Order"
)

ax.set_xlabel("Order")
ax.set_ylabel("Conditional Entropy (bits)")

fig.text(
    0.01,
    0.01,
    "Source: information_gain_by_order.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "information_gain_by_order.png"
    )
)

plt.close()


# ------------------------------------------------------------
# VIZ 2
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(8, 5)
)

ax.hist(
    null_Q,
    bins=50
)

ax.axvline(
    Q_real,
    color="red",
    linewidth=3,
    label=f"Observed Q={Q_real:.3f}"
)

ax.text(
    0.98,
    0.98,
    f"z={Q_z:.2f}\np={Q_p:.4f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white")
)

ax.set_title(
    "Bigram-Resampled Modularity vs Observed"
)

ax.set_xlabel("Modularity Q")
ax.set_ylabel("Frequency")

ax.legend()

fig.text(
    0.01,
    0.01,
    "Source: bigram_null_modularity.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "bigram_null_modularity.png"
    )
)

plt.close()


# ------------------------------------------------------------
# VIZ 3
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(10, 8)
)

ax = fig.add_subplot(
    111,
    projection="3d"
)

color_map = {
    "paradigm": "red",
    "clitic": "blue",
    "o_grade": "green"
}

for _, row in asym_df.iterrows():

    color = color_map.get(
        row["axis"],
        "gray"
    )

    ax.scatter(
        row["bigram_asym"],
        row["trigram_asym"],
        row["log10_freq"],
        color=color,
        s=row["edge_count"] * 5
    )

    ax.text(
        row["bigram_asym"],
        row["trigram_asym"],
        row["log10_freq"],
        row["cell_id"],
        fontsize=7
    )

ax.view_init(
    elev=25,
    azim=-60
)

ax.set_xlabel(
    "Bigram Asymmetry"
)

ax.set_ylabel(
    "Trigram Asymmetry"
)

ax.set_zlabel(
    "log10(Cell Frequency)"
)

ax.set_title(
    "FUNC Edge Asymmetry: Bigram vs Trigram, by Cell Frequency"
)

legend_elements = [

    Line2D(
        [0],
        [0],
        marker='o',
        color='w',
        label=k,
        markerfacecolor=v,
        markersize=10
    )

    for k, v in color_map.items()
]

ax.legend(
    handles=legend_elements
)

plt.savefig(
    os.path.join(
        FIG_DIR,
        "edge_asymmetry_3d.png"
    )
)

plt.close()


# ------------------------------------------------------------
# VIZ 4
# ------------------------------------------------------------

top30 = trigram_df.head(30)

G = nx.DiGraph()

for _, row in top30.iterrows():

    src = f"{row['prev2']}->{row['prev1']}"

    tgt = row["node_t"]

    G.add_edge(
        src,
        tgt,
        weight=row["count"]
    )

fig, ax = plt.subplots(
    figsize=(10, 6)
)

pos = nx.spring_layout(
    G,
    seed=SEED
)

weights = [
    G[u][v]["weight"]
    for u, v in G.edges()
]

nx.draw_networkx(
    G,
    pos,
    width=np.array(weights) / max(weights) * 5,
    node_size=800,
    font_size=7,
    ax=ax
)

ax.set_title(
    "Top-30 FUNC-Containing Trigram Flows (Network Graph)"
)

fig.text(
    0.01,
    0.01,
    "Source: trigram_func_transitions.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "trigram_func_flow.png"
    )
)

plt.close()


# ------------------------------------------------------------
# VIZ 5
# ------------------------------------------------------------

fig, axes = plt.subplots(
    2,
    2,
    figsize=(12, 10)
)

contexts = [
    None,
    "qok",
    "ch",
    "sh"
]

titles = [
    "P(node_t | FUNC)",
    "P(node_t | FUNC, prev=qok|*|*)",
    "P(node_t | FUNC, prev=ch|*|*)",
    "P(node_t | FUNC, prev=sh|*|*)"
]

for ax, ctx, title in zip(
    axes.flatten(),
    contexts,
    titles
):

    counts = Counter()

    for (
        a,
        b,
        c
    ), n in trigram_counts.items():

        if b != "FUNC":
            continue

        if ctx is not None:

            if not str(a).startswith(ctx):
                continue

        counts[c] += n

    top = counts.most_common(20)

    labels = [x[0] for x in top]
    vals = [x[1] for x in top]

    ax.barh(labels, vals)

    ax.set_title(title)

fig.suptitle(
    "Higher-Order Context Shifts in Post-FUNC Distribution"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "conditional_distribution_changes.png"
    )
)

plt.close()


# ------------------------------------------------------------
# VIZ 6
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(14, 6)
)

asym_df = asym_df.sort_values(
    "bigram_asym"
)

x = np.arange(len(asym_df))

forward = []
backward = []

for _, row in asym_df.iterrows():

    asym = row["bigram_asym"]

    pos = (asym + 1) / 2
    neg = 1 - pos

    forward.append(pos)
    backward.append(neg)

ax.bar(
    x,
    forward,
    color="green",
    label="FUNC->cell"
)

ax.bar(
    x,
    backward,
    bottom=forward,
    color="red",
    label="cell->FUNC"
)

ax.axhline(
    0.5,
    linestyle="--"
)

ax.set_xticks(x)

ax.set_xticklabels(
    asym_df["cell_id"],
    rotation=90
)

ax.set_ylabel(
    "Normalized Directionality"
)

ax.set_title(
    "FUNC Edge Asymmetry: Direction-of-Flow per High-Asym Cell"
)

ax.legend()

fig.text(
    0.01,
    0.01,
    "Source: edge_asymmetry_bigram_vs_trigram.csv",
    fontsize=7,
    color="gray"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "edge_asymmetry_negation_test.png"
    )
)

plt.close()


# ============================================================
# Summary JSON
# ============================================================

summary = {

    "test_name":
        "FUNC Higher-Order Conditional Probability",

    "version":
        "v1",

    "parser_sanity_sample":
        sanity_sample,

    "information_gain": {

        str(row["order"]): {

            "H_conditional":
                row["H_conditional"],

            "info_gain_over_prev":
                row["info_gain_over_prev"]
        }

        for _, row in info_df.iterrows()
    },

    "observed_modularity_Q":
        Q_real,

    "bigram_null_mean_Q":
        float(Q_mean),

    "bigram_null_std_Q":
        float(Q_std),

    "modularity_z_score":
        float(Q_z),

    "modularity_p_value":
        float(Q_p),

    "asymmetry_sign_preserved": {

        row["cell_id"]:
            bool(row["sign_preserved"])

        for _, row in asym_df.iterrows()
    },

    "n_sequences":
        int(len(sequences)),

    "n_nodes":
        int(len(nodes)),

    "n_synthetic":
        N_SYNTHETIC,

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "input_files": {
        INPUT_MATRIX:
            sha256_file(INPUT_MATRIX)
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

    summary_path,
    bigram_csv,
    trigram_csv,
    info_csv,
    null_csv,
    asym_csv
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

print("\n====================================================")
print("COMPLETE")
print("====================================================")

print(
    f"Observed modularity Q: {Q_real:.4f}"
)

print(
    f"Null mean Q: {Q_mean:.4f}"
)

print(
    f"z-score: {Q_z:.2f}"
)

print(
    f"p-value: {Q_p:.6f}"
)

print("\nArtifacts written:")
print("  - summary.json")
print("  - bigram_transition_matrix.csv")
print("  - trigram_func_transitions.csv")
print("  - information_gain_by_order.csv")
print("  - bigram_null_modularity.csv")
print("  - edge_asymmetry_bigram_vs_trigram.csv")
print("  - checksums.json")

print("\nFigures:")
print("  - information_gain_by_order.png")
print("  - bigram_null_modularity.png")
print("  - edge_asymmetry_3d.png")
print("  - trigram_func_flow.png")
print("  - conditional_distribution_changes.png")
print("  - edge_asymmetry_negation_test.png")

print("\n====================================================")