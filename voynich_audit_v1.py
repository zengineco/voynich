"""
VOYNICH FULL AUDIT ENGINE v1.0
=================================

Purpose:
--------
Rigorous falsification + reproducibility audit for the
Voynich structural morphology research pipeline.

This script is NOT an exploratory analysis layer.

It is:
- a methodological audit,
- a null-model challenge suite,
- a parser-bias detector,
- a robustness tester,
- and a reproducibility lock.

Core Philosophy:
----------------
Every strong claim must survive:
- parser perturbation,
- randomization,
- resampling,
- sparsity controls,
- topology perturbation,
- and disclosure analysis.

This script intentionally attempts to BREAK the findings.

Outputs:
--------
voynich_audit_v1/

Requirements:
-------------
pip install pandas numpy scipy networkx scikit-learn openpyxl

"""

# =========================================================
# IMPORTS
# =========================================================

import os
import json
import math
import random

import numpy as np
import pandas as pd

from collections import Counter, defaultdict

from scipy.stats import entropy
from scipy.stats import chisquare
from scipy.stats import poisson

import networkx as nx

from networkx.algorithms.community import (
    greedy_modularity_communities
)

# =========================================================
# CONFIG
# =========================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_audit_v1"

os.makedirs(OUTDIR, exist_ok=True)

RANDOM_SEED = 42

N_BOOTSTRAPS = 100

N_SHUFFLES = 100

MIN_LINE_LEN = 2

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# =========================================================
# HELPERS
# =========================================================

def safe_div(a, b):
    return a / b if b else np.nan

def conditional_entropy(seq):

    if len(seq) < 10:
        return np.nan

    pairs = list(zip(seq[:-1], seq[1:]))

    pair_counts = Counter(pairs)

    prev_counts = Counter()

    for a, b in pairs:
        prev_counts[a] += 1

    H = 0

    for (a, b), c in pair_counts.items():

        p_ab = c / len(pairs)

        p_b_given_a = c / prev_counts[a]

        H -= p_ab * math.log2(
            p_b_given_a
        )

    return H

def modularity_score(G):

    comms = greedy_modularity_communities(
        G,
        weight="weight"
    )

    return nx.community.modularity(
        G,
        comms,
        weight="weight"
    )

# =========================================================
# LOAD
# =========================================================

print("=== LOAD ===")

df = pd.read_excel(
    INPUT_XLSX,
    sheet_name="tokens_atomic"
)

print(f"TOTAL ROWS: {len(df):,}")

# =========================================================
# TOKENIZER / PARSER DISCLOSURE
# =========================================================

print("\n=== PARSER DISCLOSURE ===")

df["parsed"] = (
    df["parsed"]
    .fillna(False)
)

parsed = df[df["parsed"] == True]

unparsed = df[df["parsed"] != True]

summary = []

summary.append({
    "metric": "total_rows",
    "value": len(df)
})

summary.append({
    "metric": "parsed_rows",
    "value": len(parsed)
})

summary.append({
    "metric": "unparsed_rows",
    "value": len(unparsed)
})

summary.append({
    "metric": "parsed_pct",
    "value":
        round(
            len(parsed) / len(df),
            4
        )
})

audit_summary = pd.DataFrame(summary)

audit_summary.to_csv(
    f"{OUTDIR}/audit_summary.csv",
    index=False
)

# =========================================================
# PARSE BIAS AUDIT
# =========================================================

print("\n=== PARSE BIAS AUDIT ===")

parse_bias_rows = []

for sec in sorted(df["section"].dropna().unique()):

    sec_df = df[df["section"] == sec]

    sec_parsed = sec_df[
        sec_df["parsed"] == True
    ]

    parse_bias_rows.append({
        "section": sec,
        "total": len(sec_df),
        "parsed": len(sec_parsed),
        "parsed_pct":
            safe_div(
                len(sec_parsed),
                len(sec_df)
            ),

        "mean_token_len_total":
            sec_df["token"]
            .astype(str)
            .str.len()
            .mean(),

        "mean_token_len_parsed":
            sec_parsed["token"]
            .astype(str)
            .str.len()
            .mean()
    })

parse_bias_df = pd.DataFrame(
    parse_bias_rows
)

parse_bias_df.to_csv(
    f"{OUTDIR}/parse_bias_by_section.csv",
    index=False
)

# =========================================================
# TOKEN LENGTH BIAS
# =========================================================

print("\n=== TOKEN LENGTH BIAS ===")

length_rows = []

for parsed_state in [True, False]:

    sub = df[df["parsed"] == parsed_state]

    lengths = (
        sub["token"]
        .astype(str)
        .str.len()
    )

    for L, c in (
        lengths.value_counts()
        .sort_index()
        .items()
    ):

        length_rows.append({
            "parsed": parsed_state,
            "token_length": L,
            "count": c
        })

length_df = pd.DataFrame(length_rows)

length_df.to_csv(
    f"{OUTDIR}/token_length_bias.csv",
    index=False
)

# =========================================================
# FOLIO RECONCILIATION
# =========================================================

print("\n=== FOLIO RECONCILIATION ===")

folio_rows = []

for fol in sorted(
    df["folio"].dropna().unique()
):

    sub = df[df["folio"] == fol]

    folio_rows.append({
        "folio": fol,
        "rows": len(sub),
        "sections":
            ";".join(
                sorted(
                    sub["section"]
                    .dropna()
                    .astype(str)
                    .unique()
                )
            )
    })

folio_df = pd.DataFrame(folio_rows)

folio_df.to_csv(
    f"{OUTDIR}/folio_reconciliation.csv",
    index=False
)

# =========================================================
# BUILD CANONICAL TRANSITIONS
# =========================================================

print("\n=== BUILD TRANSITIONS ===")

parsed = parsed.copy()

transitions = []

line_sequences = []

for (folio, locus), group in parsed.groupby(
    ["folio", "locus"]
):

    group = group.sort_values(
        "line_token_index"
    )

    cells = (
        group["cell_id"]
        .dropna()
        .tolist()
    )

    if len(cells) < MIN_LINE_LEN:
        continue

    line_sequences.append(cells)

    for i in range(len(cells)-1):

        transitions.append((
            cells[i],
            cells[i+1]
        ))

print(f"TRANSITIONS: {len(transitions):,}")

# =========================================================
# CANONICAL GRAPH
# =========================================================

print("\n=== CANONICAL GRAPH ===")

G = nx.Graph()

counts = Counter(transitions)

for (u, v), w in counts.items():

    G.add_edge(
        u,
        v,
        weight=w
    )

canonical_modularity = modularity_score(G)

print(
    f"MODULARITY: {canonical_modularity:.4f}"
)

# =========================================================
# COMMUNITY STABILITY BOOTSTRAP
# =========================================================

print("\n=== BOOTSTRAP MODULARITY ===")

boot_rows = []

for i in range(N_BOOTSTRAPS):

    sampled = random.choices(
        line_sequences,
        k=len(line_sequences)
    )

    trans = []

    for seq in sampled:

        for j in range(len(seq)-1):

            trans.append((
                seq[j],
                seq[j+1]
            ))

    G_boot = nx.Graph()

    cc = Counter(trans)

    for (u, v), w in cc.items():

        G_boot.add_edge(
            u,
            v,
            weight=w
        )

    mod = modularity_score(G_boot)

    boot_rows.append({
        "bootstrap": i,
        "modularity": mod
    })

boot_df = pd.DataFrame(boot_rows)

boot_df.to_csv(
    f"{OUTDIR}/bootstrap_modularity.csv",
    index=False
)

# =========================================================
# NULL MODEL SHUFFLES
# =========================================================

print("\n=== NULL MODEL SHUFFLES ===")

shuffle_rows = []

for i in range(N_SHUFFLES):

    shuffled_trans = []

    for seq in line_sequences:

        s = seq.copy()

        random.shuffle(s)

        for j in range(len(s)-1):

            shuffled_trans.append((
                s[j],
                s[j+1]
            ))

    G_null = nx.Graph()

    cc = Counter(shuffled_trans)

    for (u, v), w in cc.items():

        G_null.add_edge(
            u,
            v,
            weight=w
        )

    mod = modularity_score(G_null)

    shuffle_rows.append({
        "shuffle": i,
        "modularity": mod
    })

shuffle_df = pd.DataFrame(
    shuffle_rows
)

shuffle_df.to_csv(
    f"{OUTDIR}/null_model_modularity.csv",
    index=False
)

# =========================================================
# ENTROPY NULL COMPARISON
# =========================================================

print("\n=== ENTROPY NULLS ===")

entropy_rows = []

for sec, sub in parsed.groupby("section"):

    seq = (
        sub["cell_id"]
        .dropna()
        .tolist()
    )

    real_H = conditional_entropy(seq)

    null_H = []

    for _ in range(50):

        s = seq.copy()

        random.shuffle(s)

        null_H.append(
            conditional_entropy(s)
        )

    entropy_rows.append({
        "section": sec,
        "real_entropy": real_H,
        "null_mean":
            np.mean(null_H),

        "null_std":
            np.std(null_H),

        "z_score":
            safe_div(
                real_H - np.mean(null_H),
                np.std(null_H)
            )
    })

entropy_df = pd.DataFrame(
    entropy_rows
)

entropy_df.to_csv(
    f"{OUTDIR}/entropy_null_comparison.csv",
    index=False
)

# =========================================================
# SPARSITY / FORBIDDENNESS AUDIT
# =========================================================

print("\n=== SPARSITY AUDIT ===")

all_cells = sorted(
    parsed["cell_id"]
    .dropna()
    .unique()
)

cell_freq = (
    parsed["cell_id"]
    .value_counts()
)

N = len(transitions)

observed_pairs = Counter(transitions)

sparse_rows = []

for a in all_cells:

    for b in all_cells:

        expected = (
            safe_div(
                cell_freq.get(a, 0),
                len(parsed)
            )
            *
            safe_div(
                cell_freq.get(b, 0),
                len(parsed)
            )
            *
            N
        )

        observed = observed_pairs.get(
            (a, b),
            0
        )

        sparse_rows.append({
            "from_cell": a,
            "to_cell": b,
            "expected": expected,
            "observed": observed,
            "gap":
                expected - observed,

            "forbidden_candidate":
                int(
                    expected > 5
                    and observed == 0
                )
        })

sparse_df = pd.DataFrame(
    sparse_rows
)

sparse_df.to_csv(
    f"{OUTDIR}/forbiddenness_audit.csv",
    index=False
)

# =========================================================
# SELF LOOP SIGNIFICANCE
# =========================================================

print("\n=== SELF LOOP SIGNIFICANCE ===")

loop_rows = []

for cell in all_cells:

    observed = observed_pairs.get(
        (cell, cell),
        0
    )

    p = safe_div(
        cell_freq.get(cell, 0),
        len(parsed)
    )

    expected = p * p * N

    loop_rows.append({
        "cell": cell,
        "observed_self_loop": observed,
        "expected_self_loop": expected,
        "ratio":
            safe_div(
                observed,
                expected
            )
    })

loop_df = pd.DataFrame(loop_rows)

loop_df.to_csv(
    f"{OUTDIR}/self_loop_significance.csv",
    index=False
)

# =========================================================
# TRANSITION ASYMMETRY
# =========================================================

print("\n=== TRANSITION ASYMMETRY ===")

asym_rows = []

for (a, b), c1 in observed_pairs.items():

    c2 = observed_pairs.get(
        (b, a),
        0
    )

    asym_rows.append({
        "a": a,
        "b": b,
        "ab": c1,
        "ba": c2,
        "asymmetry":
            abs(c1 - c2)
    })

asym_df = pd.DataFrame(asym_rows)

asym_df.to_csv(
    f"{OUTDIR}/transition_asymmetry.csv",
    index=False
)

# =========================================================
# D-FAMILY DISCLOSURE
# =========================================================

print("\n=== D-FAMILY DISCLOSURE ===")

d_rows = []

for tok, c in (
    parsed["token"]
    .value_counts()
    .items()
):

    if str(tok).startswith("d"):

        d_rows.append({
            "token": tok,
            "count": c
        })

d_df = pd.DataFrame(d_rows)

d_df.to_csv(
    f"{OUTDIR}/d_family_inventory.csv",
    index=False
)

# =========================================================
# INVARIANT TRANSITIONS
# =========================================================

print("\n=== INVARIANT TRANSITIONS ===")

section_sets = {}

for sec, sub in parsed.groupby("section"):

    trans = set()

    for (folio, locus), g in sub.groupby(
        ["folio", "locus"]
    ):

        g = g.sort_values(
            "line_token_index"
        )

        cells = (
            g["cell_id"]
            .dropna()
            .tolist()
        )

        for i in range(len(cells)-1):

            trans.add((
                cells[i],
                cells[i+1]
            ))

    section_sets[sec] = trans

common = set.intersection(
    *section_sets.values()
)

inv_rows = []

for a, b in common:

    inv_rows.append({
        "from_cell": a,
        "to_cell": b
    })

inv_df = pd.DataFrame(inv_rows)

inv_df.to_csv(
    f"{OUTDIR}/invariant_transitions.csv",
    index=False
)

# =========================================================
# PARSER PERTURBATION TEST
# =========================================================

print("\n=== PARSER PERTURBATION ===")

perturb_rows = []

for frac in [0.05, 0.10, 0.20]:

    keep = parsed.sample(
        frac=(1-frac),
        random_state=RANDOM_SEED
    )

    trans = []

    for (folio, locus), g in keep.groupby(
        ["folio", "locus"]
    ):

        g = g.sort_values(
            "line_token_index"
        )

        cells = (
            g["cell_id"]
            .dropna()
            .tolist()
        )

        for i in range(len(cells)-1):

            trans.append((
                cells[i],
                cells[i+1]
            ))

    Gp = nx.Graph()

    cc = Counter(trans)

    for (u, v), w in cc.items():

        Gp.add_edge(
            u,
            v,
            weight=w
        )

    mod = modularity_score(Gp)

    perturb_rows.append({
        "drop_fraction": frac,
        "modularity": mod
    })

perturb_df = pd.DataFrame(
    perturb_rows
)

perturb_df.to_csv(
    f"{OUTDIR}/parser_perturbation.csv",
    index=False
)

# =========================================================
# FINAL REPORT
# =========================================================

print("\n=== FINAL REPORT ===")

report = {
    "canonical_modularity":
        canonical_modularity,

    "parsed_pct":
        round(
            len(parsed) / len(df),
            4
        ),

    "folios":
        int(
            df["folio"].nunique()
        ),

    "sections":
        int(
            df["section"].nunique()
        ),

    "transitions":
        int(len(transitions))
}

with open(
    f"{OUTDIR}/final_report.json",
    "w"
) as f:

    json.dump(
        report,
        f,
        indent=2
    )

print(json.dumps(report, indent=2))

print("\n=== COMPLETE ===")

print(f"AUDIT OUTPUTS WRITTEN TO:\n{OUTDIR}")