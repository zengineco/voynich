#!/usr/bin/env python3
"""
Voynich Manuscript Research Program
TEST 4: Zodiac Clock-Position Correlation with Label Morphology

Author: OpenAI GPT-5.5
Seed: 42

PURPOSE
=======
Test whether Voynich zodiac-label morphology correlates with
clock-position annotations embedded in ZL3b locus markup.

This is one of the few externally anchored spatial structures
in the corpus and therefore represents a high-value structural
test.

BACKGROUND
==========
ZL3b zodiac-label syntax:

    <folio.line,@Lz>    <!HH:MM>token

Example:

    <f72r3.15,@Lz>    <!11:00>oralkam

Interpretation:
- @Lz marks zodiac-label entries
- <!HH:MM> is IVTFF inline clock-position annotation
- HH:MM values represent literal clock-face orientation
  around zodiac figures
- values occur in 15-minute increments

DATASET
=======
- Total labels: 29
- Annotated labels: 26
- Unannotated labels: 3

Observed clock values:
    08:45
    09:00
    09:30
    10:00
    10:30
    11:00
    11:15
    11:30
    unannotated

STATISTICAL ISSUE
=================
Observed contingency tables are sparse.

Therefore:
- asymptotic chi-square p-values are NOT trusted
- chi-square is treated as a descriptive divergence statistic
- inference comes from permutation nulls

TESTS
=====
1. Fine-grained clock-bin × prefix-family
2. Fine-grained clock-bin × suffix-axis
3. Coarse-sector × prefix-family
4. Coarse-sector × suffix-axis

Permutation null:
- shuffle clock labels 1000×
- recompute chi-square
- empirical p-value from null distribution

EFFECT SIZE
===========
Cramer's V reported descriptively.

CLOCK PARSING
=============
Parsed from IVTFF inline comments:

    <!HH:MM>

Unannotated labels assigned synthetic category:
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
    missing clock labels

INPUTS
======
Required file:
- zl3b-n.txt

OUTPUTS
=======
Creates:
    voynich_zodiac_clock_v1/

Artifacts:
- extracted_labels.csv
- fine_prefix_contingency.csv
- fine_suffix_contingency.csv
- coarse_prefix_contingency.csv
- coarse_suffix_contingency.csv
- permutation_results.csv
- summary.json
- checksums.json
- figures/fine_prefix_heatmap.png
- figures/fine_suffix_heatmap.png
- figures/coarse_prefix_heatmap.png
- figures/coarse_suffix_heatmap.png
- figures/permutation_nulls.png

DEPENDENCIES
============
- pandas
- numpy
- scipy
- matplotlib
- seaborn
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

OUTPUT_DIR = "voynich_zodiac_clock_v1"
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")

INPUT_FILE = "zl3b-n.txt"


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


def cramers_v(table):
    """
    Bias-uncorrected descriptive Cramer's V.
    """

    chi2, _, _, _ = chi2_contingency(
        table,
        correction=False
    )

    n = table.values.sum()

    r, k = table.shape

    denom = min(
        k - 1,
        r - 1
    )

    if denom <= 0:
        return np.nan

    return np.sqrt(
        chi2 / (n * denom)
    )


def parse_prefix_family(token):
    """
    Prefix-family classification.
    """

    token = token.lower()

    if token.startswith("ota"):
        return "ota"

    if token.startswith("oka"):
        return "oka"

    return "other"


def parse_suffix_axis(token):
    """
    Conservative suffix-axis extraction.

    Uses final 2-3 chars as axis proxy.
    """

    token = token.lower()

    if len(token) >= 3:
        return token[-3:]

    if len(token) >= 2:
        return token[-2:]

    return token


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


def run_permutation_test(
    df,
    row_var,
    col_var,
    n_perm=1000
):
    """
    Permutation chi-square test.
    """

    observed_table = pd.crosstab(
        df[row_var],
        df[col_var]
    )

    observed_chi2, _, _, _ = (
        chi2_contingency(
            observed_table,
            correction=False
        )
    )

    null_stats = []

    for _ in range(n_perm):

        shuffled = df.copy()

        shuffled[col_var] = np.random.permutation(
            shuffled[col_var].values
        )

        table = pd.crosstab(
            shuffled[row_var],
            shuffled[col_var]
        )

        chi2, _, _, _ = chi2_contingency(
            table,
            correction=False
        )

        null_stats.append(chi2)

    null_stats = np.array(null_stats)

    empirical_p = (
        np.sum(
            null_stats >= observed_chi2
        ) + 1
    ) / (n_perm + 1)

    z_score = (
        observed_chi2
        - np.mean(null_stats)
    ) / np.std(null_stats)

    return {
        "observed_chi2":
            float(observed_chi2),

        "df":
            int(
                (
                    observed_table.shape[0] - 1
                )
                *
                (
                    observed_table.shape[1] - 1
                )
            ),

        "cramers_v":
            float(
                cramers_v(
                    observed_table
                )
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
            observed_table,

        "null_distribution":
            null_stats
    }


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("VOYNICH ZODIAC CLOCK TEST V1")
print("====================================================\n")

ensure_dirs()


# ============================================================
# Load File
# ============================================================

print("[1/8] Loading ZL3b-n...")

if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_FILE}"
    )

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    lines = f.readlines()

print(
    f"Loaded {len(lines)} lines"
)


# ============================================================
# Parse Zodiac Labels
# ============================================================

print("\n[2/8] Extracting @Lz labels...")

pattern = re.compile(
    r"<([^>]+),@Lz>\s*(?:<!([0-9]{2}:[0-9]{2})>)?([A-Za-z]+)"
)

rows = []

for line in lines:

    match = pattern.search(line)

    if not match:
        continue

    locus = match.group(1)

    clock = match.group(2)

    token = match.group(3)

    if clock is None:
        clock = "unannotated"

    rows.append({
        "locus": locus,
        "clock":
            clock,
        "coarse_sector":
            coarse_sector(clock),
        "token":
            token,
        "prefix_family":
            parse_prefix_family(token),
        "suffix_axis":
            parse_suffix_axis(token)
    })

df = pd.DataFrame(rows)

print(
    f"Extracted {len(df)} labels"
)

print(
    "\nClock distribution:"
)

print(
    df["clock"]
    .value_counts()
    .sort_index()
)


# ============================================================
# Save Extracted Labels
# ============================================================

labels_csv_path = os.path.join(
    OUTPUT_DIR,
    "extracted_labels.csv"
)

df.to_csv(
    labels_csv_path,
    index=False
)


# ============================================================
# Fine-Grained Tests
# ============================================================

print("\n[3/8] Fine-grained tests...")

fine_prefix = run_permutation_test(
    df,
    "prefix_family",
    "clock",
    N_PERMUTATIONS
)

fine_suffix = run_permutation_test(
    df,
    "suffix_axis",
    "clock",
    N_PERMUTATIONS
)

fine_prefix_csv = os.path.join(
    OUTPUT_DIR,
    "fine_prefix_contingency.csv"
)

fine_suffix_csv = os.path.join(
    OUTPUT_DIR,
    "fine_suffix_contingency.csv"
)

fine_prefix["table"].to_csv(
    fine_prefix_csv
)

fine_suffix["table"].to_csv(
    fine_suffix_csv
)


# ============================================================
# Coarse Tests
# ============================================================

print("\n[4/8] Coarse-sector tests...")

coarse_prefix = run_permutation_test(
    df,
    "prefix_family",
    "coarse_sector",
    N_PERMUTATIONS
)

coarse_suffix = run_permutation_test(
    df,
    "suffix_axis",
    "coarse_sector",
    N_PERMUTATIONS
)

coarse_prefix_csv = os.path.join(
    OUTPUT_DIR,
    "coarse_prefix_contingency.csv"
)

coarse_suffix_csv = os.path.join(
    OUTPUT_DIR,
    "coarse_suffix_contingency.csv"
)

coarse_prefix["table"].to_csv(
    coarse_prefix_csv
)

coarse_suffix["table"].to_csv(
    coarse_suffix_csv
)


# ============================================================
# Permutation Results Table
# ============================================================

print("\n[5/8] Writing permutation results...")

results_rows = []

for name, result in [

    ("fine_prefix", fine_prefix),
    ("fine_suffix", fine_suffix),
    ("coarse_prefix", coarse_prefix),
    ("coarse_suffix", coarse_suffix)

]:

    results_rows.append({

        "test":
            name,

        "chi2":
            result["observed_chi2"],

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


# ============================================================
# Figures
# ============================================================

print("\n[6/8] Writing figures...")

# Fine prefix heatmap

plt.figure(figsize=(10, 4))

sns.heatmap(
    fine_prefix["table"],
    annot=True,
    fmt="d",
    cmap="viridis"
)

plt.title(
    "Fine Clock Bin × Prefix Family"
)

plt.tight_layout()

fine_prefix_fig = os.path.join(
    FIG_DIR,
    "fine_prefix_heatmap.png"
)

plt.savefig(
    fine_prefix_fig,
    dpi=300
)

plt.close()

# Fine suffix heatmap

plt.figure(figsize=(12, 8))

sns.heatmap(
    fine_suffix["table"],
    annot=True,
    fmt="d",
    cmap="viridis"
)

plt.title(
    "Fine Clock Bin × Suffix Axis"
)

plt.tight_layout()

fine_suffix_fig = os.path.join(
    FIG_DIR,
    "fine_suffix_heatmap.png"
)

plt.savefig(
    fine_suffix_fig,
    dpi=300
)

plt.close()

# Coarse prefix heatmap

plt.figure(figsize=(8, 4))

sns.heatmap(
    coarse_prefix["table"],
    annot=True,
    fmt="d",
    cmap="viridis"
)

plt.title(
    "Coarse Sector × Prefix Family"
)

plt.tight_layout()

coarse_prefix_fig = os.path.join(
    FIG_DIR,
    "coarse_prefix_heatmap.png"
)

plt.savefig(
    coarse_prefix_fig,
    dpi=300
)

plt.close()

# Coarse suffix heatmap

plt.figure(figsize=(10, 6))

sns.heatmap(
    coarse_suffix["table"],
    annot=True,
    fmt="d",
    cmap="viridis"
)

plt.title(
    "Coarse Sector × Suffix Axis"
)

plt.tight_layout()

coarse_suffix_fig = os.path.join(
    FIG_DIR,
    "coarse_suffix_heatmap.png"
)

plt.savefig(
    coarse_suffix_fig,
    dpi=300
)

plt.close()

# Null distributions

fig, axes = plt.subplots(
    2,
    2,
    figsize=(12, 10)
)

tests = [

    ("fine_prefix", fine_prefix),
    ("fine_suffix", fine_suffix),
    ("coarse_prefix", coarse_prefix),
    ("coarse_suffix", coarse_suffix)
]

for ax, (name, result) in zip(
    axes.flatten(),
    tests
):

    ax.hist(
        result["null_distribution"],
        bins=30,
        alpha=0.8
    )

    ax.axvline(
        result["observed_chi2"],
        linestyle="--",
        linewidth=3
    )

    ax.set_title(name)

plt.tight_layout()

null_fig = os.path.join(
    FIG_DIR,
    "permutation_nulls.png"
)

plt.savefig(
    null_fig,
    dpi=300
)

plt.close()


# ============================================================
# Summary JSON
# ============================================================

print("\n[7/8] Writing summary...")

summary = {

    "test_name":
        "Zodiac Clock-Position Correlation",

    "version":
        "v1",

    "clock_parsing_description": (
        "Clock annotations parsed from "
        "IVTFF inline comments of form "
        "<!HH:MM>. "
        "Missing annotations assigned "
        "synthetic category "
        "'unannotated'."
    ),

    "n_labels":
        int(len(df)),

    "clock_distribution":
        (
            df["clock"]
            .value_counts()
            .sort_index()
            .to_dict()
        ),

    "fine_prefix_test": {

        "chi2":
            fine_prefix["observed_chi2"],

        "df":
            fine_prefix["df"],

        "cramers_v":
            fine_prefix["cramers_v"],

        "null_mean":
            fine_prefix["null_mean"],

        "null_std":
            fine_prefix["null_std"],

        "z_score":
            fine_prefix["z_score"],

        "empirical_p":
            fine_prefix["empirical_p"]
    },

    "fine_suffix_test": {

        "chi2":
            fine_suffix["observed_chi2"],

        "df":
            fine_suffix["df"],

        "cramers_v":
            fine_suffix["cramers_v"],

        "null_mean":
            fine_suffix["null_mean"],

        "null_std":
            fine_suffix["null_std"],

        "z_score":
            fine_suffix["z_score"],

        "empirical_p":
            fine_suffix["empirical_p"]
    },

    "coarse_prefix_test": {

        "chi2":
            coarse_prefix["observed_chi2"],

        "df":
            coarse_prefix["df"],

        "cramers_v":
            coarse_prefix["cramers_v"],

        "null_mean":
            coarse_prefix["null_mean"],

        "null_std":
            coarse_prefix["null_std"],

        "z_score":
            coarse_prefix["z_score"],

        "empirical_p":
            coarse_prefix["empirical_p"]
    },

    "coarse_suffix_test": {

        "chi2":
            coarse_suffix["observed_chi2"],

        "df":
            coarse_suffix["df"],

        "cramers_v":
            coarse_suffix["cramers_v"],

        "null_mean":
            coarse_suffix["null_mean"],

        "null_std":
            coarse_suffix["null_std"],

        "z_score":
            coarse_suffix["z_score"],

        "empirical_p":
            coarse_suffix["empirical_p"]
    },

    "n_permutations":
        N_PERMUTATIONS,

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "input_files": {
        INPUT_FILE:
            sha256_file(INPUT_FILE)
    },

    "library_versions": {
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "matplotlib": plt.matplotlib.__version__,
        "seaborn": sns.__version__
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

print("\n[8/8] Writing checksums...")

artifact_paths = [

    labels_csv_path,
    fine_prefix_csv,
    fine_suffix_csv,
    coarse_prefix_csv,
    coarse_suffix_csv,
    results_csv_path,
    summary_path,

    fine_prefix_fig,
    fine_suffix_fig,
    coarse_prefix_fig,
    coarse_suffix_fig,
    null_fig
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


# ============================================================
# Complete
# ============================================================

print("\n====================================================")
print("COMPLETE")
print("====================================================")

print(
    f"Output directory: "
    f"{OUTPUT_DIR}"
)

print("\nArtifacts written:")

for item in [
    "extracted_labels.csv",
    "fine_prefix_contingency.csv",
    "fine_suffix_contingency.csv",
    "coarse_prefix_contingency.csv",
    "coarse_suffix_contingency.csv",
    "permutation_results.csv",
    "summary.json",
    "checksums.json",
    "figures/fine_prefix_heatmap.png",
    "figures/fine_suffix_heatmap.png",
    "figures/coarse_prefix_heatmap.png",
    "figures/coarse_suffix_heatmap.png",
    "figures/permutation_nulls.png"
]:

    print(f"  - {item}")

print("\n====================================================\n")