"""
VOYNICH DEEP RESEARCH ENGINE v2.0
FULL SINGLE-FILE SCRIPT
SAVE AS:
voynich_deep_research_engine_v2.py
"""

import os
import json
import gzip
import random
from collections import Counter

import numpy as np
import pandas as pd

from scipy.stats import poisson
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import mutual_info_score

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

import matplotlib.pyplot as plt

try:
    import umap
    UMAP_AVAILABLE = True
except:
    UMAP_AVAILABLE = False

# =====================================================
# CONFIG
# =====================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_deep_outputs_v2"

FIGDIR = os.path.join(OUTDIR, "figures")

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

RANDOM_SEED = 42
N_NULLS = 100
MAX_MI_DISTANCE = 15
MIN_LINE_LEN = 2

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# =====================================================
# HELPERS
# =====================================================

def savefig(name):

    path = os.path.join(FIGDIR, name)

    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    print(f"WROTE FIGURE: {path}")

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

def conditional_entropy(seq):

    if len(seq) < 10:
        return np.nan

    pairs = list(zip(seq[:-1], seq[1:]))

    pair_counts = Counter(pairs)

    prev_counts = Counter()

    for a, b in pairs:
        prev_counts[a] += 1

    H = 0

    total = len(pairs)

    for (a, b), c in pair_counts.items():

        p_ab = c / total

        p_b_given_a = c / prev_counts[a]

        H -= p_ab * np.log2(p_b_given_a)

    return H

def gzip_complexity(text):

    raw = text.encode("utf-8")

    compressed = gzip.compress(raw)

    return len(compressed) / max(len(raw), 1)

def sequence_mutual_information(seq, k=1):

    if len(seq) <= k:
        return np.nan

    a = seq[:-k]
    b = seq[k:]

    return mutual_info_score(a, b)

# =====================================================
# LOAD
# =====================================================

print("\n=== LOAD ===")

raw = pd.read_excel(
    INPUT_XLSX,
    sheet_name="tokens_atomic"
)

print(f"TOTAL ROWS: {len(raw):,}")

# =====================================================
# PARSER DISCLOSURE
# =====================================================

print("\n=== PARSER DISCLOSURE ===")

raw["parsed"] = raw["parsed"].fillna(False)

raw["node"] = np.where(
    raw["parsed"] == True,
    raw["cell_id"],
    "FUNC"
)

parsed_pct = raw["parsed"].mean()

print(f"PARSED PERCENT: {parsed_pct:.4f}")

# =====================================================
# BUILD LINE SEQUENCES
# =====================================================

print("\n=== BUILD LINE SEQUENCES ===")

line_records = []
all_sequences = []

for (folio, locus), group in raw.groupby(["folio", "locus"]):

    group = group.sort_values("line_token_index")

    seq = (
        group["node"]
        .dropna()
        .tolist()
    )

    if len(seq) < MIN_LINE_LEN:
        continue

    rec = {
        "folio": folio,
        "locus": locus,
        "section": group["section"].iloc[0],
        "length": len(seq),
        "sequence": seq
    }

    line_records.append(rec)

    all_sequences.append(seq)

line_df = pd.DataFrame(line_records)

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

transition_df = pd.DataFrame(
    transitions,
    columns=["from", "to"]
)

transition_df.to_csv(
    os.path.join(OUTDIR, "transitions.csv"),
    index=False
)

# =====================================================
# GRAPH + COMMUNITIES
# =====================================================

print("\n=== GRAPH + COMMUNITIES ===")

G = build_graph(transitions)

Q, comms = modularity_score(G)

print(f"NODES: {G.number_of_nodes()}")
print(f"EDGES: {G.number_of_edges()}")
print(f"Q: {Q:.6f}")
print(f"COMMUNITIES: {len(comms)}")

community_map = {}

for idx, comm in enumerate(comms):

    for node in comm:

        community_map[node] = f"C{idx}"

comm_rows = []

for node, comm in community_map.items():

    comm_rows.append({
        "node": node,
        "community": comm
    })

comm_df = pd.DataFrame(comm_rows)

comm_df.to_csv(
    os.path.join(OUTDIR, "communities.csv"),
    index=False
)

# =====================================================
# SECTION LOADINGS
# =====================================================

print("\n=== SECTION LOADINGS ===")

load_rows = []

for sec, sub in line_df.groupby("section"):

    counts = Counter()
    total = 0

    for seq in sub["sequence"]:

        for node in seq:

            comm = community_map.get(node)

            if comm is None:
                continue

            counts[comm] += 1
            total += 1

    for comm, c in counts.items():

        load_rows.append({
            "section": sec,
            "community": comm,
            "count": c,
            "pct": c / total
        })

load_df = pd.DataFrame(load_rows)

load_df.to_csv(
    os.path.join(OUTDIR, "section_loadings.csv"),
    index=False
)

# =====================================================
# MI DECAY
# =====================================================

print("\n=== MI DECAY ===")

flat_seq = []

for seq in all_sequences:
    flat_seq.extend(seq)

mi_rows = []

for k in range(1, MAX_MI_DISTANCE + 1):

    real_mi = sequence_mutual_information(
        flat_seq,
        k=k
    )

    nulls = []

    for _ in range(N_NULLS):

        shuffled = flat_seq.copy()

        random.shuffle(shuffled)

        nulls.append(
            sequence_mutual_information(
                shuffled,
                k=k
            )
        )

    null_mean = np.mean(nulls)
    null_std = np.std(nulls)

    z = (
        (real_mi - null_mean) / null_std
        if null_std > 0
        else np.nan
    )

    mi_rows.append({
        "distance": k,
        "real_mi": real_mi,
        "null_mean": null_mean,
        "null_std": null_std,
        "z": z
    })

mi_df = pd.DataFrame(mi_rows)

mi_df.to_csv(
    os.path.join(OUTDIR, "mi_decay.csv"),
    index=False
)

plt.figure(figsize=(10,6))

plt.plot(
    mi_df["distance"],
    mi_df["real_mi"],
    label="real"
)

plt.plot(
    mi_df["distance"],
    mi_df["null_mean"],
    label="null"
)

plt.xlabel("distance")
plt.ylabel("mutual information")
plt.title("MI Decay")
plt.legend()

savefig("mi_decay.png")

# =====================================================
# CONSTRAINT FIELD
# =====================================================

print("\n=== CONSTRAINT FIELD ===")

nodes = sorted(set(flat_seq))

freq = Counter(flat_seq)

observed = Counter(transitions)

N = len(transitions)

constraint_rows = []

for a in nodes:

    for b in nodes:

        expected = (
            (freq[a] / len(flat_seq))
            *
            (freq[b] / len(flat_seq))
            *
            N
        )

        obs = observed.get((a, b), 0)

        constraint_rows.append({
            "from": a,
            "to": b,
            "expected": expected,
            "observed": obs,
            "delta": obs - expected,
            "forbidden_candidate": int(
                expected > 5 and obs == 0
            )
        })

constraint_df = pd.DataFrame(constraint_rows)

constraint_df["poisson_p"] = (
    constraint_df.apply(
        lambda r:
        poisson.pmf(
            r["observed"],
            r["expected"]
        ),
        axis=1
    )
)

constraint_df.to_csv(
    os.path.join(OUTDIR, "constraint_field.csv"),
    index=False
)

pivot = constraint_df.pivot(
    index="from",
    columns="to",
    values="delta"
)

plt.figure(figsize=(18,16))

plt.imshow(
    pivot.fillna(0).values,
    aspect="auto"
)

plt.colorbar()

plt.title("Constraint Field Delta")

savefig("constraint_field_heatmap.png")

# =====================================================
# FOLIO FEATURES
# =====================================================

print("\n=== FOLIO FEATURES ===")

folio_rows = []

for folio, sub in line_df.groupby("folio"):

    counts = Counter()
    total = 0

    for seq in sub["sequence"]:

        for node in seq:

            comm = community_map.get(node)

            if comm is None:
                continue

            counts[comm] += 1
            total += 1

    rec = {
        "folio": folio,
        "section": sub["section"].iloc[0],
        "n_tokens": total
    }

    for comm in sorted(set(community_map.values())):

        rec[f"pct_{comm}"] = (
            counts[comm] / total
            if total else np.nan
        )

    folio_rows.append(rec)

folio_df = pd.DataFrame(folio_rows)

folio_df.to_csv(
    os.path.join(OUTDIR, "folio_features.csv"),
    index=False
)

# =====================================================
# FOLIO MANIFOLD
# =====================================================

print("\n=== FOLIO MANIFOLD ===")

feature_cols = [
    c for c in folio_df.columns
    if c.startswith("pct_")
]

X = (
    folio_df[feature_cols]
    .fillna(0)
    .astype(float)
)

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

print("RUNNING PCA...")

pca = PCA(
    n_components=2,
    random_state=RANDOM_SEED
)

pca_coords = pca.fit_transform(X_scaled)

folio_df["pca_x"] = pca_coords[:,0]
folio_df["pca_y"] = pca_coords[:,1]

print("RUNNING TSNE...")

tsne = TSNE(
    n_components=2,
    perplexity=20,
    learning_rate="auto",
    init="random",
    random_state=RANDOM_SEED
)

tsne_coords = tsne.fit_transform(X_scaled)

folio_df["tsne_x"] = tsne_coords[:,0]
folio_df["tsne_y"] = tsne_coords[:,1]

if UMAP_AVAILABLE:

    print("RUNNING UMAP...")

    reducer = umap.UMAP(
        n_components=2,
        random_state=RANDOM_SEED
    )

    umap_coords = reducer.fit_transform(X_scaled)

    folio_df["umap_x"] = umap_coords[:,0]
    folio_df["umap_y"] = umap_coords[:,1]

else:

    folio_df["umap_x"] = np.nan
    folio_df["umap_y"] = np.nan

folio_df.to_csv(
    os.path.join(OUTDIR, "folio_manifold.csv"),
    index=False
)

plt.figure(figsize=(12,10))

sections = sorted(
    folio_df["section"]
    .dropna()
    .unique()
)

for sec in sections:

    sub = folio_df[
        folio_df["section"] == sec
    ]

    plt.scatter(
        sub["pca_x"],
        sub["pca_y"],
        label=sec,
        alpha=0.8,
        s=40
    )

plt.xlabel(
    f"PC1 ({pca.explained_variance_ratio_[0]:.2%})"
)

plt.ylabel(
    f"PC2 ({pca.explained_variance_ratio_[1]:.2%})"
)

plt.title("Folio Manifold PCA")

plt.legend()

savefig("folio_manifold_pca.png")

plt.figure(figsize=(12,10))

for sec in sections:

    sub = folio_df[
        folio_df["section"] == sec
    ]

    plt.scatter(
        sub["tsne_x"],
        sub["tsne_y"],
        label=sec,
        alpha=0.8,
        s=40
    )

plt.title("Folio Manifold TSNE")

plt.legend()

savefig("folio_manifold_tsne.png")

if UMAP_AVAILABLE:

    plt.figure(figsize=(12,10))

    for sec in sections:

        sub = folio_df[
            folio_df["section"] == sec
        ]

        plt.scatter(
            sub["umap_x"],
            sub["umap_y"],
            label=sec,
            alpha=0.8,
            s=40
        )

    plt.title("Folio Manifold UMAP")

    plt.legend()

    savefig("folio_manifold_umap.png")

# =====================================================
# NULL MODULARITY
# =====================================================

print("\n=== NULL MODULARITY ===")

real_Q = Q

null_Qs = []

for n in range(N_NULLS):

    shuffled = flat_seq.copy()

    random.shuffle(shuffled)

    st = []

    for i in range(len(shuffled)-1):

        st.append((
            shuffled[i],
            shuffled[i+1]
        ))

    NG = build_graph(st)

    try:

        nQ, _ = modularity_score(NG)

        null_Qs.append(nQ)

    except:
        continue

null_mean = np.mean(null_Qs)
null_std = np.std(null_Qs)

Q_z = (
    (real_Q - null_mean) / null_std
    if null_std > 0
    else np.nan
)

null_summary = {
    "real_Q": real_Q,
    "null_mean": float(null_mean),
    "null_std": float(null_std),
    "z": float(Q_z)
}

with open(
    os.path.join(
        OUTDIR,
        "null_modularity_summary.json"
    ),
    "w"
) as f:

    json.dump(
        null_summary,
        f,
        indent=2
    )

plt.figure(figsize=(8,6))

plt.hist(
    null_Qs,
    bins=20,
    alpha=0.7
)

plt.axvline(
    real_Q,
    linestyle="--"
)

plt.title("Null Modularity Distribution")

savefig("null_modularity_distribution.png")

# =====================================================
# CHECKSUMS
# =====================================================

print("\n=== CHECKSUMS ===")

checksums = {
    "rows": int(len(raw)),
    "parsed_pct": float(parsed_pct),
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

print(f"OUTPUTS WRITTEN TO: {OUTDIR}")