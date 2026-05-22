"""
VOYNICH FORBIDDEN TRANSITION PERMUTATION ENGINE v2
==================================================

CORRECTED VERSION

This script performs a REAL null test.

It DOES:
- preserve section token inventories
- destroy observed adjacency structure
- allow forbidden transitions to emerge under null
- compute empirical p-values

It DOES NOT:
- bootstrap folios
- preserve observed zeroes trivially
- silently preserve adjacency structure

OUTPUTS
-------
voynich_forbidden_permutation_v2/

FILES
-----
forbidden_candidates.csv
forbidden_permutations.csv
forbidden_summary.csv
line_internal_dwells.csv
checksums.json

FIGURES
-------
forbidden_empirical_pvalues.png
dwell_distributions.png
"""

import os
import json
import random

from collections import Counter

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================
# CONFIG
# =====================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_forbidden_permutation_v2"

FIGDIR = os.path.join(OUTDIR, "figures")

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

SEED = 42

N_PERMUTATIONS = 1000

random.seed(SEED)
np.random.seed(SEED)

# =====================================================
# HELPERS
# =====================================================

def savefig(name):

    path = os.path.join(FIGDIR, name)

    plt.tight_layout()

    plt.savefig(path, dpi=300)

    plt.close()

    print("WROTE:", path)

def build_transitions(seqs):

    out = []

    for seq in seqs:

        for i in range(len(seq)-1):

            out.append((
                seq[i],
                seq[i+1]
            ))

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

print("LINES:", len(line_df))

# =====================================================
# REAL TRANSITIONS
# =====================================================

print("\n=== REAL TRANSITIONS ===")

all_sequences = line_df["sequence"].tolist()

transitions = build_transitions(all_sequences)

transition_counts = Counter(transitions)

flat = []

for s in all_sequences:
    flat.extend(s)

freq = Counter(flat)

N_TRANS = len(transitions)

print("TRANSITIONS:", N_TRANS)

# =====================================================
# FORBIDDEN CANDIDATES
# =====================================================

print("\n=== FORBIDDEN CANDIDATES ===")

rows = []

nodes = sorted(set(flat))

for a in nodes:

    for b in nodes:

        expected = (
            (freq[a] / len(flat))
            *
            (freq[b] / len(flat))
            *
            N_TRANS
        )

        observed = transition_counts.get((a,b), 0)

        if expected >= 5 and observed == 0:

            rows.append({
                "from": a,
                "to": b,
                "expected": expected,
                "observed": observed
            })

forbidden_df = pd.DataFrame(rows)

forbidden_df = forbidden_df.sort_values(
    "expected",
    ascending=False
)

print("CANDIDATES:", len(forbidden_df))

forbidden_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_candidates.csv"
    ),
    index=False
)

candidate_pairs = list(zip(
    forbidden_df["from"],
    forbidden_df["to"]
))

# =====================================================
# TRUE PERMUTATION NULL
# =====================================================

print("\n=== TRUE PERMUTATION NULL ===")

perm_rows = []

sections = sorted(
    line_df["section"].dropna().unique()
)

for p in range(N_PERMUTATIONS):

    if p % 50 == 0:
        print("PERMUTATION:", p)

    permuted_sequences = []

    # preserve section vocabularies
    # destroy adjacency structure

    for sec in sections:

        sec_df = line_df[
            line_df["section"] == sec
        ]

        sec_sequences = sec_df["sequence"].tolist()

        flat_sec = []

        lengths = []

        for s in sec_sequences:

            flat_sec.extend(s)

            lengths.append(len(s))

        # shuffle token order
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
        build_transitions(permuted_sequences)
    )

    for a,b in candidate_pairs:

        perm_rows.append({
            "perm": p,
            "from": a,
            "to": b,
            "count":
                perm_counts.get((a,b), 0)
        })

perm_df = pd.DataFrame(perm_rows)

perm_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_permutations.csv"
    ),
    index=False
)

# =====================================================
# EMPIRICAL PVALUES
# =====================================================

print("\n=== EMPIRICAL PVALUES ===")

summary_rows = []

for (a,b), g in perm_df.groupby([
    "from",
    "to"
]):

    vals = g["count"].values

    observed = 0

    p_empirical = np.mean(
        vals <= observed
    )

    summary_rows.append({
        "from": a,
        "to": b,
        "perm_mean": np.mean(vals),
        "perm_std": np.std(vals),
        "perm_min": np.min(vals),
        "perm_max": np.max(vals),
        "ci_low":
            np.percentile(vals, 2.5),
        "ci_high":
            np.percentile(vals, 97.5),
        "empirical_p":
            p_empirical
    })

summary_df = pd.DataFrame(summary_rows)

summary_df = summary_df.sort_values(
    "empirical_p"
)

summary_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_summary.csv"
    ),
    index=False
)

# =====================================================
# LINE-INTERNAL DWELLS
# =====================================================

print("\n=== LINE INTERNAL DWELLS ===")

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

dwell_df = pd.DataFrame(dwell_rows)

dwell_df.to_csv(
    os.path.join(
        OUTDIR,
        "line_internal_dwells.csv"
    ),
    index=False
)

# =====================================================
# VISUALIZATIONS
# =====================================================

print("\n=== VISUALIZATIONS ===")

# empirical p

plt.figure(figsize=(12,6))

plot_df = summary_df.head(20)

labels = [
    f"{a}->{b}"
    for a,b in zip(
        plot_df["from"],
        plot_df["to"]
    )
]

plt.bar(
    labels,
    plot_df["empirical_p"]
)

plt.xticks(rotation=90)

plt.ylabel("empirical p")

plt.title(
    "Forbidden Transition Empirical P-values"
)

savefig(
    "forbidden_empirical_pvalues.png"
)

# dwell

plt.figure(figsize=(10,6))

sns.barplot(
    data=dwell_df,
    x="section",
    y="max_internal_run"
)

plt.xticks(rotation=30)

plt.title(
    "Line Internal Dwell Constraints"
)

savefig(
    "dwell_distributions.png"
)

# =====================================================
# CHECKSUMS
# =====================================================

print("\n=== CHECKSUMS ===")

checksums = {
    "rows": int(len(raw)),
    "lines": int(len(line_df)),
    "transitions": int(N_TRANS),
    "candidates": int(len(forbidden_df)),
    "permutations": int(N_PERMUTATIONS)
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