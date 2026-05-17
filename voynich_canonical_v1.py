import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

print("=== Voynich Trajectory Pipeline v1 ===")

# =====================================================
# LOAD
# =====================================================

df = pd.read_excel(
    "MASTER_TOKEN_MATRIX.xlsx",
    sheet_name="tokens_atomic"
)

parsed_df = df[df["parsed"] == True].copy()

print(f"Parsed rows: {len(parsed_df):,}")

# =====================================================
# BUILD TRANSITION GRAPH
# =====================================================

transitions = []

for (folio, locus), group in parsed_df.groupby(["folio", "locus"]):

    group = group.sort_values("line_token_index")

    cells = group["cell_id"].dropna().tolist()

    if len(cells) < 2:
        continue

    for i in range(len(cells)-1):
        transitions.append((cells[i], cells[i+1]))

print(f"Transitions: {len(transitions):,}")

# =====================================================
# GRAPH
# =====================================================

G = nx.Graph()

for (u, v), w in Counter(transitions).items():

    if G.has_edge(u, v):
        G[u][v]["weight"] += w
    else:
        G.add_edge(u, v, weight=w)

communities = greedy_modularity_communities(G, weight="weight")

comm_map = {}

for idx, comm in enumerate(communities):
    for node in comm:
        comm_map[node] = f"C{idx}"

print(f"Communities: {len(communities)}")

# =====================================================
# ASSIGN COMMUNITIES
# =====================================================

parsed_df["community"] = parsed_df["cell_id"].map(comm_map)

# =====================================================
# EXTRACT LINE TRAJECTORIES
# =====================================================

trajectory_rows = []

for (folio, locus), group in parsed_df.groupby(["folio", "locus"]):

    group = group.sort_values("line_token_index")

    comms = group["community"].dropna().tolist()

    cells = group["cell_id"].dropna().tolist()

    toks = group["token"].tolist()

    if len(comms) < 2:
        continue

    trajectory_rows.append({
        "folio": folio,
        "section": group["section"].iloc[0],
        "locus": locus,
        "length": len(comms),
        "trajectory": " -> ".join(comms),
        "cell_path": " -> ".join(cells),
        "token_path": " ".join(toks)
    })

traj_df = pd.DataFrame(trajectory_rows)

print(f"Trajectories extracted: {len(traj_df):,}")

# =====================================================
# TRAJECTORY FREQUENCIES
# =====================================================

traj_counts = (
    traj_df.groupby(["section", "trajectory"])
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

# =====================================================
# TRAJECTORY SIGNATURES
# =====================================================

global_counts = (
    traj_df.groupby("trajectory")
    .size()
    .reset_index(name="global_count")
    .sort_values("global_count", ascending=False)
)

# =====================================================
# SECTION × COMMUNITY LOADINGS
# =====================================================

loadings = (
    parsed_df.groupby(["section", "community"])
    .size()
    .reset_index(name="count")
)

loadings["pct"] = (
    loadings.groupby("section")["count"]
    .transform(lambda x: x / x.sum())
)

# =====================================================
# POSITIONAL COMMUNITY MATRIX
# =====================================================

pos_rows = []

for (folio, locus), group in parsed_df.groupby(["folio", "locus"]):

    group = group.sort_values("line_token_index")

    n = len(group)

    if n < 2:
        continue

    for i, row in group.iterrows():

        rel = round(row["line_token_index"] / max(n-1,1), 2)

        pos_rows.append({
            "section": row["section"],
            "community": row["community"],
            "relative_pos": rel
        })

pos_df = pd.DataFrame(pos_rows)

# =====================================================
# ROSETTES SUBGRAPH
# =====================================================

rosettes = traj_df[traj_df["section"] == "rosettes"]

rosettes_counts = (
    rosettes.groupby("trajectory")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

# =====================================================
# SAVE EVERYTHING
# =====================================================

traj_df.to_csv("trajectory_lines.csv", index=False)

traj_counts.to_csv("trajectory_counts.csv", index=False)

global_counts.to_csv("trajectory_global_counts.csv", index=False)

loadings.to_csv("section_community_loadings.csv", index=False)

pos_df.to_csv("positional_community_matrix.csv", index=False)

rosettes_counts.to_csv("rosettes_trajectories.csv", index=False)

# =====================================================
# SUMMARY
# =====================================================

print()
print("=== TOP GLOBAL TRAJECTORIES ===")

print(global_counts.head(20))

print()
print("=== ROSETTES TOP TRAJECTORIES ===")

print(rosettes_counts.head(20))

print()
print("=== SECTION COMMUNITY LOADINGS ===")

print(loadings.sort_values(
    ["section", "pct"],
    ascending=[True, False]
).head(30))

print()
print("FILES WRITTEN:")
print("- trajectory_lines.csv")
print("- trajectory_counts.csv")
print("- trajectory_global_counts.csv")
print("- section_community_loadings.csv")
print("- positional_community_matrix.csv")
print("- rosettes_trajectories.csv")

print()
print("=== COMPLETE ===")