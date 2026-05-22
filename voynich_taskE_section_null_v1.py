#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK E v1: SECTION-PERMUTED MODULARITY NULL

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

Re-run the original 18 May modularity-null test under
strictly corrected methodology.

This task repairs a critical flaw in the original null:

- the previous null produced degenerate variance
- std(Q) == 0
- z=1.0 and p=1.0 were sentinel outputs
  from divide-by-zero handling

This rerun imposes hard methodological guardrails.

============================================================
CORE QUESTION
============================================================

Does the observed FUNC-extended transition graph possess
higher modularity than expected under section-label
permutation?

============================================================
NULL MODEL
============================================================

Shuffle section labels across sequences while preserving:

- sequence lengths
- token order within sequences
- transition structure
- node frequencies

Destroy:

- section ↔ sequence linkage

Then:

1. rebuild FUNC-extended graph
2. recompute Louvain modularity
3. repeat 1,000 times

============================================================
MANDATORY GUARDRAILS
============================================================

1. Null distribution must contain >=50 distinct Q values.
   Otherwise:
       HARD FAIL

2. std(Q) must exceed 1e-6.
   Otherwise:
       HARD FAIL

3. First three shuffled section-label sequences written
   to top of CSV audit block.

4. Deterministic seeds.

5. Parser self-test required.

============================================================
INPUT
============================================================

Required:
- MASTER_TOKEN_MATRIX.xlsx

Sheet:
- tokens_atomic

Required columns:
- folio
- section
- locus
- line_token_index
- cell_id
- parsed

============================================================
OUTPUT
============================================================

voynich_taskE_section_null_v1/

FILES
=====

- taskE_section_null.csv
- taskE_summary.json
- checksums.json

FIGURES
=======

- modularity_null_histogram.png

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

import matplotlib.pyplot as plt

import networkx as nx

from community import community_louvain

# ============================================================
# Constants
# ============================================================

SEED = 42
N_PERMUTATIONS = 1000
LOUVAIN_RESOLUTION = 1.0

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"
OUTPUT_DIR = "voynich_taskE_section_null_v1"
FIG_DIR = os.path.join(
    OUTPUT_DIR,
    "figures"
)

random.seed(SEED)
np.random.seed(SEED)

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



def build_sequences(df, locus_col, token_idx_col, cell_col):

    grouped = defaultdict(list)

    for _, row in df.iterrows():

        locus = row[locus_col]

        token_idx = row[token_idx_col]

        cell = canonical_node(
            row[cell_col]
        )

        grouped[locus].append((
            token_idx,
            cell
        ))

    sequences = {}

    for locus, vals in grouped.items():

        vals = sorted(vals)

        sequences[locus] = [
            v[1]
            for v in vals
        ]

    return sequences



def build_graph(
    sequences,
    section_map
):

    G = nx.Graph()

    for locus, seq in sequences.items():

        section = section_map[locus]

        for i in range(len(seq) - 1):

            a = seq[i]
            b = seq[i + 1]

            if a == b:
                continue

            section_edge = f"{a}::{b}::{section}"

if G.has_edge(a, b):

    G[a][b]["weight"] += SECTION_WEIGHTS[section]

else:

    G.add_edge(
        a,
        b,
        weight=SECTION_WEIGHTS[section]
    )
                G[a][b]["sections"].append(section)

            else:

                G.add_edge(
                    a,
                    b,
                    weight=1,
                    sections=[section]
                )

    return G



def compute_modularity(G):

    partition = community_louvain.best_partition(
        G,
        weight="weight",
        resolution=LOUVAIN_RESOLUTION,
        random_state=SEED
    )

    modularity = community_louvain.modularity(
        partition,
        G,
        weight="weight"
    )

    return modularity, partition


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK E v1")
print("SECTION-PERMUTED MODULARITY NULL")
print("====================================================\n")

# ============================================================
# File Audit
# ============================================================

print("[1/14] Auditing required files...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_MATRIX}"
    )

print("Input file present.")

# ============================================================
# Load Data
# ============================================================

print("\n[2/14] Loading MASTER_TOKEN_MATRIX.xlsx...")

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

print("\n[3/14] SHA-256 verification...")

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
        "MASTER_TOKEN_MATRIX.xlsx SHA mismatch."
    )

print("SHA verified.")

# ============================================================
# Detect Columns
# ============================================================

print("\n[4/14] Detecting required columns...")

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

print("\n[5/14] Parser self-test...")

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
        "Parser self-test failed (<8/10)."
    )

print(
    f"\nParser self-test passed: {success}/10"
)

# ============================================================
# Build Productive Corpus
# ============================================================

print("\n[6/14] Building productive corpus...")

productive_rows = []

for _, row in raw_df.iterrows():

    val = row[parsed_col]

    parsed_flag = (
        val is True
        or val == 1
        or str(val).lower() == "true"
    )

    if not parsed_flag:
        continue

    productive_rows.append({

        "folio": row[folio_col],
        "section": row[section_col],
        "locus": row[locus_col],
        "token_index": row[token_idx_col],
        "cell_id": row[cell_col]
    })

prod_df = pd.DataFrame(
    productive_rows
)

print(
    f"Retained productive rows: {len(prod_df)}"
)

# ============================================================
# Build Sequences
# ============================================================

print("\n[7/14] Building sequences...")

sequences = build_sequences(
    prod_df,
    "locus",
    "token_index",
    "cell_id"
)

print(
    f"Built {len(sequences)} sequences"
)

# ============================================================
# Build Section Map
# ============================================================

section_map = (
    prod_df
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
# Observed Graph
# ============================================================

print("\n[8/14] Computing observed modularity...")

G_real = build_graph(
    sequences,
    section_map
)

Q_real, partition_real = compute_modularity(
    G_real
)

print(
    f"Observed modularity Q = {Q_real:.6f}"
)

# ============================================================
# Permutation Null
# ============================================================

print("\n[9/14] Running section-permuted null...")

null_Q = []
audit_rows = []

for sim in range(N_PERMUTATIONS):

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

    # ========================================================
    # Audit first three shuffles
    # ========================================================

    if sim < 3:

        audit_rows.append({

            "simulation": sim + 1,

            "first_10_labels": ",".join(
                shuffled_sections[:10]
            )
        })

    G_perm = build_graph(
        sequences,
        shuffled_map
    )

    Q_perm, _ = compute_modularity(
        G_perm
    )

    null_Q.append(Q_perm)

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_PERMUTATIONS}"
        )

# ============================================================
# Guardrails
# ============================================================

print("\n[10/14] Guardrail audit...")

n_unique = len(set(
    np.round(null_Q, 12)
))

print(
    f"Distinct null Q values: {n_unique}"
)

if n_unique < 50:

    raise RuntimeError(
        "Guardrail failure: <50 distinct null values."
    )

null_std = float(np.std(null_Q))

print(
    f"Null std(Q): {null_std:.12f}"
)

if null_std <= 1e-6:

    raise RuntimeError(
        "Guardrail failure: std(Q) <= 1e-6"
    )

# ============================================================
# Statistics
# ============================================================

null_mean = float(np.mean(null_Q))

z_score = (
    Q_real - null_mean
) / null_std

p_value = (
    np.sum(
        np.array(null_Q) >= Q_real
    ) + 1
) / (
    N_PERMUTATIONS + 1
)

print(
    f"Observed Q: {Q_real:.6f}"
)

print(
    f"Null mean: {null_mean:.6f}"
)

print(
    f"Null std: {null_std:.6f}"
)

print(
    f"z-score: {z_score:.4f}"
)

print(
    f"p-value: {p_value:.6f}"
)

# ============================================================
# Write Null CSV
# ============================================================

print("\n[11/14] Writing null distribution...")

null_path = os.path.join(
    OUTPUT_DIR,
    "taskE_section_null.csv"
)

with open(
    null_path,
    "w",
    encoding="utf-8"
) as f:

    f.write("# AUDIT_ROWS\n")

    for row in audit_rows:

        f.write(
            f"simulation={row['simulation']}"
            f",labels={row['first_10_labels']}\n"
        )

    f.write("simulation,Q\n")

    for i, q in enumerate(null_Q):

        f.write(
            f"{i + 1},{q}\n"
        )

# ============================================================
# Figure
# ============================================================

print("\n[12/14] Writing histogram...")

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.hist(
    null_Q,
    bins=40
)

ax.axvline(
    Q_real,
    linewidth=3,
    color="red"
)

ax.text(
    0.98,
    0.98,
    f"Observed Q = {Q_real:.4f}\n"
    f"z = {z_score:.2f}\n"
    f"p = {p_value:.6f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white")
)

ax.set_title(
    "TASK E\n"
    "Section-Permuted Modularity Null"
)

ax.set_xlabel(
    "Louvain Modularity Q"
)

ax.set_ylabel(
    "Frequency"
)

caption = (
    "Null preserves sequence structure and transition topology; "
    "destroys section ↔ sequence linkage."
)

fig.text(
    0.01,
    0.01,
    caption,
    fontsize=8
)

plt.tight_layout()

fig_path = os.path.join(
    FIG_DIR,
    "modularity_null_histogram.png"
)

plt.savefig(
    fig_path,
    dpi=200
)

plt.close()

# ============================================================
# Summary
# ============================================================

print("\n[13/14] Writing summary...")

finding_level = "NULL"

if z_score >= 9:
    finding_level = "LOCKED"

elif z_score >= 5:
    finding_level = "STRONG"

summary = {

    "task": "E",

    "version": "v1",

    "finding_level": finding_level,

    "observed_modularity": float(Q_real),

    "null_mean": float(null_mean),

    "null_std": float(null_std),

    "z_score": float(z_score),

    "empirical_p": float(p_value),

    "n_permutations": N_PERMUTATIONS,

    "distinct_null_values": int(n_unique),

    "guardrails": {

        "distinct_values_ge_50": bool(
            n_unique >= 50
        ),

        "std_gt_1e6": bool(
            null_std > 1e-6
        )
    },

    "null_preserves": [

        "sequence lengths",
        "token order within sequences",
        "transition topology",
        "node frequencies"
    ],

    "null_destroys": [

        "section-sequence linkage"
    ],

    "input_sha256": {

        INPUT_MATRIX: matrix_sha
    },

    "timestamp_utc": datetime.now(
        timezone.utc
    ).isoformat()
}

summary_path = os.path.join(
    OUTPUT_DIR,
    "taskE_summary.json"
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

print("\n[14/14] Writing checksums...")

artifact_paths = [

    null_path,
    summary_path,
    fig_path
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
print("TASK E COMPLETE")
print("====================================================")

print(
    f"Observed Q = {Q_real:.6f}"
)

print(
    f"Null mean = {null_mean:.6f}"
)

print(
    f"Null std = {null_std:.6f}"
)

print(
    f"z-score = {z_score:.4f}"
)

print(
    f"p-value = {p_value:.6f}"
)

print(
    f"Finding level = {finding_level}"
)

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")
