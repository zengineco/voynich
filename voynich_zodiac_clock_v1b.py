#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 4B: Zodiac Clock × REGISTER-GRAMMAR Morphology

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Re-run Test 4 using the LOCKED register grammar parse
(cell_id from tokenizer v4 / MASTER_TOKEN_MATRIX.xlsx)
instead of ad-hoc morphology heuristics.

RATIONALE
=========
Test 4 produced null results across all morphology-clock
association tests, but morphology assignment used:
    - ad-hoc prefix parsing
    - ad-hoc suffix extraction

This audit replaces those with the locked register grammar.

CORE QUESTION
=============
Do zodiac labels participate in the productive register grammar?

Possible outcomes:

1. Most labels parse outside grammar
   -> zodiac labels are a distinct subsystem

2. Labels parse inside grammar but clock remains null
   -> Test 4 null stands

3. Labels parse and clock predicts morphology
   -> new structural finding

INPUTS
======
Required files:
- zl3b-n.txt
- MASTER_TOKEN_MATRIX.xlsx

Required sheet:
- tokens_atomic

REQUIRED COLUMNS
================
MASTER_TOKEN_MATRIX.xlsx:
- token
- cell_id

zl3b-n.txt:
    <folio.line,@Lz> <!HH:MM>token

CLOCK PARSING
=============
Clock annotation parsed from:
    <!HH:MM>

Missing annotations assigned:
    "unannotated"

COARSE CLOCK SECTORS
====================
early:
    08:45
    09:00
    09:30

middle:
    10:00
    10:30

late:
    11:00
    11:15
    11:30

unannotated:
    missing labels

STATISTICS
==========
Permutation chi-square tests:
    - clock × grammar prefix
    - clock × grammar grade
    - clock × grammar axis

Both:
    - fine clock bins
    - coarse sectors

Null:
    shuffle clock labels 1000×

Inference:
    empirical p-values only

OUTPUTS
=======
Creates:
    voynich_zodiac_clock_v1b/

Artifacts:
- extracted_labels.csv
- grammar_lookup.csv
- fine_prefix_contingency.csv
- fine_grade_contingency.csv
- fine_axis_contingency.csv
- coarse_prefix_contingency.csv
- coarse_grade_contingency.csv
- coarse_axis_contingency.csv
- permutation_results.csv
- summary.json
- checksums.json
- figures/*.png
"""

import os
import re
import json
import hashlib
import random
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import chi2_contingency


# ============================================================
# Constants
# ============================================================

SEED = 42
N_PERMUTATIONS = 1000

random.seed(SEED)
np.random.seed(SEED)

OUTPUT_DIR = "voynich_zodiac_clock_v1b"
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")

INPUT_ZL3 = "ZL3b-n"
INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"


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


def ensure_dirs():

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


def detect_column(df, candidates):

    lower_map = {
        c.lower(): c
        for c in df.columns
    }

    for cand in candidates:

        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    raise ValueError(
        f"Could not detect required column. "
        f"Tried candidates: {candidates}"
    )


def coarse_sector(clock):

    if clock == "unannotated":
        return "unannotated"

    early = {
        "08:45",
        "09:00",
        "09:30"
    }

    middle = {
        "10:00",
        "10:30"
    }

    late = {
        "11:00",
        "11:15",
        "11:30"
    }

    if clock in early:
        return "early"

    if clock in middle:
        return "middle"

    if clock in late:
        return "late"

    return "other"


def parse_cell_id(cell_id):
    """
    Parse locked register grammar cell_id.

    Expected:
        prefix_grade_axis

    If malformed:
        mark as outside_grammar
    """

    if pd.isna(cell_id):
        return {
            "grammar_status":
                "outside_grammar",
            "prefix":
                "outside_grammar",
            "grade":
                "outside_grammar",
            "axis":
                "outside_grammar"
        }

    cell = str(cell_id).strip()

    if (
        cell == ""
        or cell.upper() == "FUNC"
    ):

        return {
            "grammar_status":
                "outside_grammar",
            "prefix":
                "outside_grammar",
            "grade":
                "outside_grammar",
            "axis":
                "outside_grammar"
        }

    parts = re.split(
        r"[_\-\s]+",
        cell
    )

    if len(parts) < 3:

        return {
            "grammar_status":
                "outside_grammar",
            "prefix":
                "outside_grammar",
            "grade":
                "outside_grammar",
            "axis":
                "outside_grammar"
        }

    return {
        "grammar_status":
            "inside_grammar",

        "prefix":
            parts[0],

        "grade":
            parts[1],

        "axis":
            parts[2]
    }


def cramers_v(table):

    chi2, _, _, _ = chi2_contingency(
        table,
        correction=False
    )

    n = table.values.sum()

    r, k = table.shape

    denom = min(
        r - 1,
        k - 1
    )

    if denom <= 0:
        return np.nan

    return np.sqrt(
        chi2 / (n * denom)
    )


def run_permutation_test(
    df,
    morph_var,
    clock_var,
    n_perm=1000
):

    table = pd.crosstab(
        df[morph_var],
        df[clock_var]
    )

    chi2, _, _, _ = chi2_contingency(
        table,
        correction=False
    )

    null_stats = []

    for _ in range(n_perm):

        shuffled = df.copy()

        shuffled[clock_var] = np.random.permutation(
            shuffled[clock_var].values
        )

        null_table = pd.crosstab(
            shuffled[morph_var],
            shuffled[clock_var]
        )

        null_chi2, _, _, _ = chi2_contingency(
            null_table,
            correction=False
        )

        null_stats.append(null_chi2)

    null_stats = np.array(
        null_stats
    )

    empirical_p = (
        np.sum(
            null_stats >= chi2
        ) + 1
    ) / (n_perm + 1)

    z_score = (
        chi2
        - np.mean(null_stats)
    ) / np.std(null_stats)

    return {

        "chi2":
            float(chi2),

        "df":
            int(
                (
                    table.shape[0] - 1
                )
                *
                (
                    table.shape[1] - 1
                )
            ),

        "cramers_v":
            float(
                cramers_v(table)
            ),

        "null_mean":
            float(
                np.mean(null_stats)
            ),

        "null_std":
            float(
                np.std(null_stats)
            ),

        "z_score":
            float(z_score),

        "empirical_p":
            float(empirical_p),

        "table":
            table,

        "null_distribution":
            null_stats
    }


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH ZODIAC CLOCK TEST V1B")
print("====================================================\n")

ensure_dirs()


# ============================================================
# Load Files
# ============================================================

print("[1/10] Loading files...")

for f in [
    INPUT_ZL3,
    INPUT_MATRIX
]:

    if not os.path.exists(f):

        raise FileNotFoundError(
            f"Missing required file: {f}"
        )

with open(
    INPUT_ZL3,
    "r",
    encoding="utf-8"
) as f:

    zl3_lines = f.readlines()

token_df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded zl3b-n.txt "
    f"({len(zl3_lines)} lines)"
)

print(
    f"Loaded MASTER_TOKEN_MATRIX.xlsx "
    f"({len(token_df)} rows)"
)


# ============================================================
# Detect Columns
# ============================================================

print("\n[2/10] Detecting columns...")

token_col = detect_column(
    token_df,
    ["token"]
)

cell_col = detect_column(
    token_df,
    ["cell_id"]
)

print(
    f"Detected token column: {token_col}"
)

print(
    f"Detected cell column: {cell_col}"
)


# ============================================================
# Extract Zodiac Labels
# ============================================================

print("\n[3/10] Extracting @Lz labels...")

pattern = re.compile(
    r"<([^>]+),@Lz>\s*(?:<!([0-9]{2}:[0-9]{2})>)?([A-Za-z]+)"
)

rows = []

for line in zl3_lines:

    match = pattern.search(line)

    if not match:
        continue

    locus = match.group(1)

    clock = match.group(2)

    token = match.group(3)

    if clock is None:
        clock = "unannotated"

    rows.append({

        "locus":
            locus,

        "clock":
            clock,

        "coarse_sector":
            coarse_sector(clock),

        "token":
            token.lower()
    })

lz_df = pd.DataFrame(rows)

print(
    f"Extracted {len(lz_df)} Lz labels"
)

print(
    "\nClock distribution:"
)

print(
    lz_df["clock"]
    .value_counts()
    .sort_index()
)


# ============================================================
# Build Grammar Lookup
# ============================================================

print("\n[4/10] Building grammar lookup...")

lookup = (
    token_df[
        [token_col, cell_col]
    ]
    .dropna()
    .copy()
)

lookup[token_col] = (
    lookup[token_col]
    .astype(str)
    .str.lower()
    .str.strip()
)

lookup = (
    lookup
    .drop_duplicates(
        subset=[token_col]
    )
)

lookup_map = dict(
    zip(
        lookup[token_col],
        lookup[cell_col]
    )
)

print(
    f"Lookup vocabulary size: "
    f"{len(lookup_map)}"
)


# ============================================================
# Apply Grammar Parse
# ============================================================

print("\n[5/10] Applying locked grammar parse...")

grammar_rows = []

for _, row in lz_df.iterrows():

    token = row["token"]

    cell_id = lookup_map.get(
        token,
        np.nan
    )

    parsed = parse_cell_id(
        cell_id
    )

    grammar_rows.append({

        "locus":
            row["locus"],

        "clock":
            row["clock"],

        "coarse_sector":
            row["coarse_sector"],

        "token":
            token,

        "cell_id":
            cell_id,

        "grammar_status":
            parsed["grammar_status"],

        "prefix":
            parsed["prefix"],

        "grade":
            parsed["grade"],

        "axis":
            parsed["axis"]
    })

grammar_df = pd.DataFrame(
    grammar_rows
)

lookup_csv_path = os.path.join(
    OUTPUT_DIR,
    "grammar_lookup.csv"
)

grammar_df.to_csv(
    lookup_csv_path,
    index=False
)

inside_n = int(
    np.sum(
        grammar_df["grammar_status"]
        == "inside_grammar"
    )
)

outside_n = int(
    np.sum(
        grammar_df["grammar_status"]
        == "outside_grammar"
    )
)

print(
    f"\nInside grammar: {inside_n}"
)

print(
    f"Outside grammar: {outside_n}"
)


# ============================================================
# Save Extracted Labels
# ============================================================

print("\n[6/10] Saving extracted labels...")

labels_csv_path = os.path.join(
    OUTPUT_DIR,
    "extracted_labels.csv"
)

grammar_df.to_csv(
    labels_csv_path,
    index=False
)


# ============================================================
# Run Tests
# ============================================================

print("\n[7/10] Running permutation tests...")

tests = {}

for morphology in [
    "prefix",
    "grade",
    "axis"
]:

    tests[f"fine_{morphology}"] = (
        run_permutation_test(
            grammar_df,
            morphology,
            "clock",
            N_PERMUTATIONS
        )
    )

    tests[f"coarse_{morphology}"] = (
        run_permutation_test(
            grammar_df,
            morphology,
            "coarse_sector",
            N_PERMUTATIONS
        )
    )


# ============================================================
# Save Contingencies
# ============================================================

print("\n[8/10] Writing contingency tables...")

artifact_paths = [
    labels_csv_path,
    lookup_csv_path
]

for name, result in tests.items():

    out_csv = os.path.join(
        OUTPUT_DIR,
        f"{name}_contingency.csv"
    )

    result["table"].to_csv(
        out_csv
    )

    artifact_paths.append(
        out_csv
    )


# ============================================================
# Permutation Results Table
# ============================================================

results_rows = []

for name, result in tests.items():

    results_rows.append({

        "test":
            name,

        "chi2":
            result["chi2"],

        "df":
            result["df"],

        "cramers_v":
            result["cramers_v"],

        "null_mean":
            result["null_mean"],

        "null_std":
            result["null_std"],

        "z_score":
            result["z_score"],

        "empirical_p":
            result["empirical_p"]
    })

results_df = pd.DataFrame(
    results_rows
)

results_csv_path = os.path.join(
    OUTPUT_DIR,
    "permutation_results.csv"
)

results_df.to_csv(
    results_csv_path,
    index=False
)

artifact_paths.append(
    results_csv_path
)


# ============================================================
# Figures
# ============================================================

print("\n[9/10] Writing figures...")

for name, result in tests.items():

    plt.figure(figsize=(10, 6))

    sns.heatmap(
        result["table"],
        annot=True,
        fmt="d",
        cmap="viridis"
    )

    plt.title(name)

    plt.tight_layout()

    fig_path = os.path.join(
        FIG_DIR,
        f"{name}.png"
    )

    plt.savefig(
        fig_path,
        dpi=300
    )

    plt.close()

    artifact_paths.append(
        fig_path
    )

# Null distribution panel

fig, axes = plt.subplots(
    3,
    2,
    figsize=(14, 14)
)

for ax, (name, result) in zip(
    axes.flatten(),
    tests.items()
):

    ax.hist(
        result["null_distribution"],
        bins=30,
        alpha=0.8
    )

    ax.axvline(
        result["chi2"],
        linestyle="--",
        linewidth=3
    )

    ax.set_title(name)

plt.tight_layout()

null_panel = os.path.join(
    FIG_DIR,
    "permutation_nulls.png"
)

plt.savefig(
    null_panel,
    dpi=300
)

plt.close()

artifact_paths.append(
    null_panel
)


# ============================================================
# Summary JSON
# ============================================================

print("\n[10/10] Writing summary...")

summary = {

    "test_name":
        "Zodiac Clock × Register Grammar",

    "version":
        "v1b",

    "clock_parsing_description": (
        "Clock annotations parsed from "
        "IVTFF inline comments <!HH:MM>. "
        "Missing values assigned "
        "'unannotated'."
    ),

    "grammar_parse_description": (
        "Morphology derived from locked "
        "register grammar tokenizer "
        "(cell_id from MASTER_TOKEN_MATRIX.xlsx). "
        "Tokens absent from grammar vocabulary "
        "classified as outside_grammar."
    ),

    "n_labels":
        int(len(grammar_df)),

    "inside_grammar":
        inside_n,

    "outside_grammar":
        outside_n,

    "outside_grammar_rate":
        float(
            outside_n
            / len(grammar_df)
        ),

    "clock_distribution":
        (
            grammar_df["clock"]
            .value_counts()
            .sort_index()
            .to_dict()
        ),

    "tests": {

        name: {

            "chi2":
                result["chi2"],

            "df":
                result["df"],

            "cramers_v":
                result["cramers_v"],

            "null_mean":
                result["null_mean"],

            "null_std":
                result["null_std"],

            "z_score":
                result["z_score"],

            "empirical_p":
                result["empirical_p"]
        }

        for name, result in tests.items()
    },

    "n_permutations":
        N_PERMUTATIONS,

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "input_files": {

        INPUT_ZL3:
            sha256_file(INPUT_ZL3),

        INPUT_MATRIX:
            sha256_file(INPUT_MATRIX)
    },

    "library_versions": {

        "numpy":
            np.__version__,

        "pandas":
            pd.__version__,

        "matplotlib":
            plt.matplotlib.__version__,

        "seaborn":
            sns.__version__
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

artifact_paths.append(
    summary_path
)


# ============================================================
# Checksums
# ============================================================

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
    f"Output directory: "
    f"{OUTPUT_DIR}"
)

print("\nKey diagnostics:")

print(
    f"  Labels inside grammar: "
    f"{inside_n}"
)

print(
    f"  Labels outside grammar: "
    f"{outside_n}"
)

print(
    f"  Outside-grammar rate: "
    f"{outside_n / len(grammar_df):.3f}"
)

print("\n====================================================\n")