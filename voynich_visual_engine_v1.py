"""
VOYNICH VISUAL ENGINE v1.1
Canonical Visualization Layer

Generates:
- permission heatmaps
- community flow maps
- positional tensors
- divergence topology
- trajectory embeddings
- recursion landscapes
- invariant maps
- execution complexity distributions

INPUT:
voynich_outputs_v1/

OUTPUT:
voynich_outputs_v1/visualizations/
"""

# =====================================================
# IMPORTS
# =====================================================

import os

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# =====================================================
# PATHS
# =====================================================

OUT = "voynich_outputs_v1"

VIZ = f"{OUT}/visualizations"

os.makedirs(VIZ, exist_ok=True)

# =====================================================
# SAFE FILENAMES
# =====================================================

def safe_filename(x):

    return (
        str(x)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )

# =====================================================
# SAVE HELPER
# =====================================================

def savefig(name):

    filename = f"{VIZ}/{name}"

    plt.tight_layout()

    plt.savefig(
        filename,
        dpi=300
    )

    plt.close()

    print(f"WROTE: {filename}")

# =====================================================
# LOAD DATA
# =====================================================

print("=== LOADING OUTPUTS ===")

perm = pd.read_csv(
    f"{OUT}/permission_matrix.csv"
)

comm = pd.read_csv(
    f"{OUT}/community_transition_matrix.csv"
)

pos = pd.read_csv(
    f"{OUT}/positional_tensor.csv"
)

entropy = pd.read_csv(
    f"{OUT}/section_entropy.csv"
)

loops = pd.read_csv(
    f"{OUT}/self_loops.csv"
)

complexity = pd.read_csv(
    f"{OUT}/execution_complexity.csv"
)

embed = pd.read_csv(
    f"{OUT}/trajectory_embeddings.csv"
)

loadings = pd.read_csv(
    f"{OUT}/section_community_loadings.csv"
)

recur = pd.read_csv(
    f"{OUT}/recursion_patterns.csv"
)

inv = pd.read_csv(
    f"{OUT}/invariants.csv"
)

# =====================================================
# PERMISSION HEATMAP
# =====================================================

print("\n=== PERMISSION HEATMAP ===")

pivot = perm.pivot_table(
    index="from_cell",
    columns="to_cell",
    values="allowed",
    fill_value=0
)

plt.figure(figsize=(14, 12))

plt.imshow(
    pivot.values,
    aspect='auto'
)

plt.colorbar()

plt.title("Permission Matrix")

plt.xlabel("TO")

plt.ylabel("FROM")

savefig("permission_heatmap.png")

# =====================================================
# FORBIDDEN SPACE MASK
# =====================================================

print("\n=== FORBIDDEN SPACE ===")

forbidden = 1 - pivot.values

plt.figure(figsize=(14, 12))

plt.imshow(
    forbidden,
    aspect='auto'
)

plt.colorbar()

plt.title("Forbidden Transition Space")

plt.xlabel("TO")

plt.ylabel("FROM")

savefig("forbidden_space_mask.png")

# =====================================================
# COMMUNITY FLOW HEATMAP
# =====================================================

print("\n=== COMMUNITY FLOW ===")

comm_pivot = comm.pivot_table(
    index="from_comm",
    columns="to_comm",
    values="probability",
    aggfunc="mean",
    fill_value=0
)

plt.figure(figsize=(8, 6))

plt.imshow(
    comm_pivot.values,
    aspect='auto'
)

plt.colorbar()

plt.xticks(
    range(len(comm_pivot.columns)),
    comm_pivot.columns
)

plt.yticks(
    range(len(comm_pivot.index)),
    comm_pivot.index
)

plt.title(
    "Community Transition Probabilities"
)

savefig("community_flow_heatmap.png")

# =====================================================
# POSITIONAL TENSORS
# =====================================================

print("\n=== POSITIONAL TENSORS ===")

for sec in pos["section"].dropna().unique():

    safe_sec = safe_filename(sec)

    sub = pos[
        pos["section"] == sec
    ]

    piv = sub.pivot_table(
        index="community",
        columns="relative_pos",
        values="probability",
        aggfunc="mean",
        fill_value=0
    )

    plt.figure(figsize=(14, 5))

    plt.imshow(
        piv.values,
        aspect='auto'
    )

    plt.colorbar()

    plt.xticks(
        range(len(piv.columns)),
        piv.columns,
        rotation=90
    )

    plt.yticks(
        range(len(piv.index)),
        piv.index
    )

    plt.title(
        f"Positional Tensor: {sec}"
    )

    plt.xlabel("Relative Line Position")

    plt.ylabel("Community")

    savefig(
        f"positional_tensor_{safe_sec}.png"
    )

# =====================================================
# SECTION DIVERGENCE MAP
# =====================================================

print("\n=== SECTION DIVERGENCE ===")

div = loadings.pivot_table(
    index="section",
    columns="community",
    values="pct",
    fill_value=0
)

plt.figure(figsize=(8, 5))

plt.imshow(
    div.values,
    aspect='auto'
)

plt.colorbar()

plt.xticks(
    range(len(div.columns)),
    div.columns
)

plt.yticks(
    range(len(div.index)),
    div.index
)

plt.title(
    "Section Community Divergence"
)

savefig("section_divergence.png")

# =====================================================
# ENTROPY LANDSCAPE
# =====================================================

print("\n=== ENTROPY LANDSCAPE ===")

entropy = entropy.dropna()

entropy = entropy.sort_values(
    "conditional_entropy"
)

plt.figure(figsize=(10, 5))

plt.bar(
    entropy["section"],
    entropy["conditional_entropy"]
)

plt.xticks(rotation=45)

plt.ylabel("Conditional Entropy")

plt.title("Operational Freedom by Section")

savefig("section_entropy.png")

# =====================================================
# SELF LOOP LANDSCAPE
# =====================================================

print("\n=== SELF LOOP LANDSCAPE ===")

top = loops.head(20)

plt.figure(figsize=(12, 7))

plt.barh(
    top["cell"],
    top["count"]
)

plt.xlabel("Self-Loop Count")

plt.title("Attractor States")

savefig("self_loops.png")

# =====================================================
# EXECUTION COMPLEXITY
# =====================================================

print("\n=== EXECUTION COMPLEXITY ===")

plt.figure(figsize=(12, 7))

for sec in complexity["section"].dropna().unique():

    sub = complexity[
        complexity["section"] == sec
    ]

    plt.hist(
        sub["switches"],
        bins=20,
        alpha=0.4,
        label=sec
    )

plt.legend()

plt.xlabel("Community Switches")

plt.ylabel("Frequency")

plt.title(
    "Execution Complexity Distribution"
)

savefig("execution_complexity.png")

# =====================================================
# TRAJECTORY EMBEDDINGS
# =====================================================

print("\n=== TRAJECTORY EMBEDDINGS ===")

sections = (
    embed["section"]
    .dropna()
    .unique()
)

plt.figure(figsize=(12, 10))

for sec in sections:

    sub = embed[
        embed["section"] == sec
    ]

    plt.scatter(
        sub["x"],
        sub["y"],
        s=6,
        alpha=0.5,
        label=sec
    )

plt.legend(markerscale=3)

plt.title(
    "Trajectory Embedding Space"
)

plt.xlabel("Embedding X")

plt.ylabel("Embedding Y")

savefig("trajectory_embedding_space.png")

# =====================================================
# RECURSION LANDSCAPE
# =====================================================

print("\n=== RECURSION LANDSCAPE ===")

top_rec = (
    recur["pattern"]
    .value_counts()
    .head(20)
)

plt.figure(figsize=(14, 8))

top_rec.plot(kind="bar")

plt.ylabel("Occurrences")

plt.title("Top Recursive Motifs")

savefig("recursion_landscape.png")

# =====================================================
# INVARIANT TRAJECTORIES
# =====================================================

print("\n=== INVARIANT TRAJECTORIES ===")

inv_counts = (
    inv["trajectory"]
    .value_counts()
    .head(20)
)

plt.figure(figsize=(14, 8))

inv_counts.plot(kind="bar")

plt.ylabel("Occurrences")

plt.title(
    "Invariant Backbone Trajectories"
)

savefig("invariant_trajectories.png")

# =====================================================
# COMMUNITY LOADINGS
# =====================================================

print("\n=== COMMUNITY LOADINGS ===")

for sec in (
    loadings["section"]
    .dropna()
    .unique()
):

    safe_sec = safe_filename(sec)

    sub = loadings[
        loadings["section"] == sec
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(
        sub["community"],
        sub["pct"]
    )

    plt.ylim(0, 1)

    plt.ylabel("Probability")

    plt.title(
        f"Community Loadings: {sec}"
    )

    savefig(
        f"community_loadings_{safe_sec}.png"
    )

# =====================================================
# COMPLETE
# =====================================================

print("\n=== COMPLETE ===")

print(
    f"VISUALIZATIONS WRITTEN TO:\n{VIZ}"
)