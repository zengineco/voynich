"""
VOYNICH FORBIDDEN-TRANSITION BOOTSTRAP ENGINE v1
=================================================

PURPOSE
-------
1. Bootstrap-test forbidden transition candidates
2. Compare against natural-language controls
3. Measure section-specific dwell constraints
4. Produce deterministic audit artifacts

ACADEMIC POLICY
---------------
- no interpretive language
- no semantic assumptions
- deterministic seeds
- explicit falsification criteria
- all intermediate outputs written
- no silent failures

INPUTS
------
MASTER_TOKEN_MATRIX.xlsx

OPTIONAL CONTROLS
-----------------
Place any UTF-8 txt files into:

controls/

Examples:
- pliny.txt
- avicenna.txt
- dioscorides.txt

OUTPUTS
-------
voynich_forbidden_bootstrap_v1/

FILES
-----
forbidden_pairs_bootstrap.csv
forbidden_pairs_summary.csv
control_corpus_metrics.csv
section_dwell_constraints.csv
bootstrap_null_distributions.csv
checksums.json

FIGURES
-------
forbidden_pair_bootstrap.png
control_corpus_comparison.png
dwell_constraint_sections.png
"""

# =====================================================
# IMPORTS
# =====================================================

import os
import json
import random
import gzip

from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from scipy.stats import entropy

from sklearn.metrics import mutual_info_score

import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================
# CONFIG
# =====================================================

INPUT_XLSX = "MASTER_TOKEN_MATRIX.xlsx"

OUTDIR = "voynich_forbidden_bootstrap_v1"

FIGDIR = os.path.join(OUTDIR, "figures")

CONTROLDIR = "controls"

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

N_BOOTSTRAPS = 1000

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

def seq_mi(seq, k=1):

    if len(seq) <= k:
        return np.nan

    a = seq[:-k]
    b = seq[k:]

    return mutual_info_score(a, b)

def gzip_ratio(tokens):

    txt = " ".join(tokens)

    raw = txt.encode("utf-8")

    comp = gzip.compress(raw)

    return len(comp) / max(len(raw), 1)

def build_transitions(seqs):

    transitions = []

    for seq in seqs:

        for i in range(len(seq)-1):

            transitions.append((
                seq[i],
                seq[i+1]
            ))

    return transitions

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

# =====================================================
# LOAD CORPUS
# =====================================================

print("\n=== LOAD VOYNICH CORPUS ===")

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

print("LINES:", len(all_sequences))

# =====================================================
# BUILD TRANSITIONS
# =====================================================

print("\n=== BUILD TRANSITIONS ===")

transitions = build_transitions(all_sequences)

transition_counts = Counter(transitions)

node_freq = Counter(flat_seq)

N_TRANS = len(transitions)

print("TRANSITIONS:", N_TRANS)

# =====================================================
# IDENTIFY FORBIDDEN CANDIDATES
# =====================================================

print("\n=== IDENTIFY FORBIDDEN CANDIDATES ===")

nodes = sorted(set(flat_seq))

forbidden_rows = []

for a in nodes:

    for b in nodes:

        expected = (
            (node_freq[a] / len(flat_seq))
            *
            (node_freq[b] / len(flat_seq))
            *
            N_TRANS
        )

        observed = transition_counts.get((a,b), 0)

        if expected >= 5 and observed == 0:

            forbidden_rows.append({
                "from": a,
                "to": b,
                "expected": expected,
                "observed": observed
            })

forbidden_df = pd.DataFrame(forbidden_rows)

forbidden_df = forbidden_df.sort_values(
    "expected",
    ascending=False
)

print("FORBIDDEN CANDIDATES:", len(forbidden_df))

forbidden_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_pairs_summary.csv"
    ),
    index=False
)

# =====================================================
# BOOTSTRAP TEST
# =====================================================

print("\n=== BOOTSTRAP TEST ===")

candidate_pairs = list(zip(
    forbidden_df["from"],
    forbidden_df["to"]
))

bootstrap_results = []

folios = list(
    line_df["folio"].unique()
)

for i in range(N_BOOTSTRAPS):

    if i % 50 == 0:
        print("BOOTSTRAP:", i)

    sampled_folios = np.random.choice(
        folios,
        size=len(folios),
        replace=True
    )

    sampled = line_df[
        line_df["folio"].isin(sampled_folios)
    ]

    seqs = sampled["sequence"].tolist()

    bt = Counter(
        build_transitions(seqs)
    )

    for a, b in candidate_pairs:

        bootstrap_results.append({
            "bootstrap": i,
            "from": a,
            "to": b,
            "count": bt.get((a,b), 0)
        })

bootstrap_df = pd.DataFrame(
    bootstrap_results
)

bootstrap_df.to_csv(
    os.path.join(
        OUTDIR,
        "forbidden_pairs_bootstrap.csv"
    ),
    index=False
)

# =====================================================
# BOOTSTRAP SUMMARY
# =====================================================

print("\n=== BOOTSTRAP SUMMARY ===")

summary_rows = []

for (a,b), g in bootstrap_df.groupby([
    "from",
    "to"
]):

    vals = g["count"].values

    summary_rows.append({
        "from": a,
        "to": b,
        "bootstrap_mean": np.mean(vals),
        "bootstrap_std": np.std(vals),
        "ci_low": np.percentile(vals, 2.5),
        "ci_high": np.percentile(vals, 97.5),
        "all_zero":
            int(np.all(vals == 0))
    })

summary_df = pd.DataFrame(summary_rows)

summary_df.to_csv(
    os.path.join(
        OUTDIR,
        "bootstrap_null_distributions.csv"
    ),
    index=False
)

# =====================================================
# CONTROL CORPORA
# =====================================================

print("\n=== CONTROL CORPORA ===")

control_rows = []

if os.path.exists(CONTROLDIR):

    for fname in os.listdir(CONTROLDIR):

        if not fname.endswith(".txt"):
            continue

        path = os.path.join(
            CONTROLDIR,
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

        transitions_ctrl = list(zip(
            tokens[:-1],
            tokens[1:]
        ))

        self_loops = sum([
            1 for a,b in transitions_ctrl
            if a == b
        ])

        mi1 = seq_mi(tokens, k=1)

        gz = gzip_ratio(tokens)

        ent = conditional_entropy(tokens)

        control_rows.append({
            "corpus": fname,
            "tokens": len(tokens),
            "mi1": mi1,
            "gzip_ratio": gz,
            "conditional_entropy": ent,
            "self_loops": self_loops
        })

# add Voynich baseline

voy_self = sum([
    1 for a,b in transitions
    if a == b
])

control_rows.append({
    "corpus": "voynich",
    "tokens": len(flat_seq),
    "mi1": seq_mi(flat_seq, k=1),
    "gzip_ratio": gzip_ratio(flat_seq),
    "conditional_entropy":
        conditional_entropy(flat_seq),
    "self_loops": voy_self
})

control_df = pd.DataFrame(control_rows)

control_df.to_csv(
    os.path.join(
        OUTDIR,
        "control_corpus_metrics.csv"
    ),
    index=False
)

# =====================================================
# DWELL CONSTRAINT TEST
# =====================================================

print("\n=== DWELL CONSTRAINT TEST ===")

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

                run = 1
                current = tok

        if run > max_run:
            max_run = run

    dwell_rows.append({
        "section": section,
        "max_repeat_run": max_run
    })

dwell_df = pd.DataFrame(dwell_rows)

dwell_df.to_csv(
    os.path.join(
        OUTDIR,
        "section_dwell_constraints.csv"
    ),
    index=False
)

# =====================================================
# VISUALIZATION
# =====================================================

print("\n=== VISUALIZATION ===")

# forbidden bootstrap

if len(summary_df) > 0:

    plt.figure(figsize=(12,6))

    plot_df = summary_df.sort_values(
        "bootstrap_mean",
        ascending=False
    ).head(20)

    labels = [
        f"{a}->{b}"
        for a,b in zip(
            plot_df["from"],
            plot_df["to"]
        )
    ]

    plt.bar(
        labels,
        plot_df["bootstrap_mean"]
    )

    plt.xticks(rotation=90)

    plt.ylabel("bootstrap mean")

    plt.title(
        "Forbidden Pair Bootstrap Means"
    )

    savefig(
        "forbidden_pair_bootstrap.png"
    )

# controls

if len(control_df) > 0:

    plt.figure(figsize=(10,6))

    sns.scatterplot(
        data=control_df,
        x="conditional_entropy",
        y="gzip_ratio",
        hue="corpus",
        s=120
    )

    plt.title(
        "Control Corpus Comparison"
    )

    savefig(
        "control_corpus_comparison.png"
    )

# dwell

plt.figure(figsize=(10,6))

sns.barplot(
    data=dwell_df,
    x="section",
    y="max_repeat_run"
)

plt.xticks(rotation=30)

plt.title(
    "Section Max Repeat Runs"
)

savefig(
    "dwell_constraint_sections.png"
)

# =====================================================
# CHECKSUMS
# =====================================================

print("\n=== CHECKSUMS ===")

checksums = {
    "rows": int(len(raw)),
    "lines": int(len(all_sequences)),
    "transitions": int(N_TRANS),
    "forbidden_candidates":
        int(len(forbidden_df)),
    "bootstraps": int(N_BOOTSTRAPS),
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