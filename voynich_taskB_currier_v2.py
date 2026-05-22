#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK B v2: CURRIER EXTERNAL VALIDATION
(Section-Controlled Paleographic Prediction)

Author: OpenAI GPT-5.5
Seed: 42

============================================================
OVERVIEW
============================================================

This task tests whether the locked productive register grammar
captures independently-derived Currier paleographic structure.

The crucial methodological issue is section confounding:

- herbal-A is mostly Currier-A
- balneo is almost entirely Currier-B
- stars is almost entirely Currier-B

A naive global A/B classifier would mostly relearn section identity.

Therefore:

B1:
    Predict Currier-A vs Currier-B
    WITHIN herbal-A ONLY.

B2:
    Predict Currier hands (2/3/4)
    WITHIN Currier-B ONLY.

============================================================
INPUT FILES
============================================================

Required:
- MASTER_TOKEN_MATRIX.xlsx
- currier_labels.csv

Optional:
- voynich_folio_profile.csv

============================================================
OUTPUT
============================================================

voynich_taskB_currier_v2/

B1
--
- taskB1_herbal_currier_metrics.json
- taskB1_discriminative_cells.csv
- taskB1_summary.json

B2
--
- taskB2_hand_metrics.json
- taskB2_summary.json

GENERAL
-------
- checksums.json
- summary_v7.json
- taskB_brief.md

FIGURES
-------
- taskB1_roc_curve.png
- taskB1_top_cells.png
- taskB2_confusion_matrix.png
- taskB2_f1_scores.png

============================================================
INTERPRETATION RULES
============================================================

B1
--
AUC > 0.80:
    LOCKED

0.65–0.80:
    STRONG

0.55–0.65:
    CANDIDATE

<0.55:
    NULL

B2
--
macro-F1 > 0.70
AND > section baseline:
    STRONG

otherwise:
    SECTION-CONFOUNDED

============================================================
"""

# ============================================================
# Imports
# ============================================================

import os
import json
import hashlib
import random
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from sklearn.model_selection import (
    train_test_split
)

from sklearn.preprocessing import (
    StandardScaler,
    LabelEncoder
)

from sklearn.linear_model import (
    LogisticRegression
)

from sklearn.metrics import (

    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,

    roc_auc_score,
    roc_curve,

    confusion_matrix,
    classification_report
)

from sklearn.calibration import (
    calibration_curve
)

# ============================================================
# Constants
# ============================================================

SEED = 42

N_PERMUTATIONS = 1000
N_BOOTSTRAPS = 1000

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"
INPUT_CURRIER = "currier_labels.csv"

OUTPUT_DIR = "voynich_taskB_currier_v2"

FIG_DIR = os.path.join(
    OUTPUT_DIR,
    "figures"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    FIG_DIR,
    exist_ok=True
)

random.seed(SEED)
np.random.seed(SEED)

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
        f"Could not detect column from: "
        f"{candidates}"
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


def bootstrap_ci(
    values,
    alpha=0.05
):

    lo = np.percentile(
        values,
        100 * (alpha / 2)
    )

    hi = np.percentile(
        values,
        100 * (1 - alpha / 2)
    )

    return lo, hi


def metric_summary(values):

    lo, hi = bootstrap_ci(values)

    return {

        "mean":
            float(np.mean(values)),

        "lower_95":
            float(lo),

        "upper_95":
            float(hi)
    }


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK B v2")
print("CURRIER EXTERNAL VALIDATION")
print("====================================================\n")


# ============================================================
# File Audit
# ============================================================

print("[1/18] Auditing required files...")

required_files = [
    INPUT_MATRIX,
    INPUT_CURRIER
]

for path in required_files:

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"Missing required file: {path}"
        )

print("All required files present.")


# ============================================================
# Load Inputs
# ============================================================

print("\n[2/18] Loading inputs...")

token_df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

currier_df = pd.read_csv(
    INPUT_CURRIER
)

print(
    f"Loaded token rows: {len(token_df)}"
)

print(
    f"Loaded Currier rows: {len(currier_df)}"
)


# ============================================================
# SHA-256 Audit
# ============================================================

print("\n[3/18] SHA-256 audit...")

matrix_sha = sha256_file(
    INPUT_MATRIX
)

print(
    f"MASTER_TOKEN_MATRIX.xlsx = "
    f"{matrix_sha}"
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
# Currier Provenance Audit
# ============================================================

print("\n[4/18] Currier provenance audit...")

required_currier_cols = [

    "folio",
    "currier_lang",
    "currier_hand",
    "page_type",
    "quire"
]

for col in required_currier_cols:

    if col not in currier_df.columns:

        raise RuntimeError(
            f"Missing Currier column: {col}"
        )

print("Currier schema verified.")


# ============================================================
# Detect Token Columns
# ============================================================

print("\n[5/18] Detecting token columns...")

folio_col = detect_column(
    token_df,
    ["folio"]
)

section_col = detect_column(
    token_df,
    ["section"]
)

cell_col = detect_column(
    token_df,
    ["cell_id"]
)

parsed_col = detect_column(
    token_df,
    ["parsed"]
)

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  section: {section_col}")
print(f"  cell_id: {cell_col}")
print(f"  parsed: {parsed_col}")


# ============================================================
# Parser Self-Test
# ============================================================

print("\n[6/18] Parser self-test...")

parsed_ok = []

sample_cells = (
    token_df[cell_col]
    .dropna()
    .astype(str)
    .value_counts()
    .head(10)
    .index
)

for cell in sample_cells:

    parsed = parse_cell_id(cell)

    if parsed is not None:

        parsed_ok.append(parsed)

        print(
            f"{cell} -> "
            f"({parsed[0]}, "
            f"{parsed[1]}, "
            f"{parsed[2]})"
        )

if len(parsed_ok) < 8:

    raise RuntimeError(
        "Parser self-test failed (<8/10)."
    )

print(
    f"\nParser self-test passed: "
    f"{len(parsed_ok)}/10"
)


# ============================================================
# Build Productive Matrix
# ============================================================

print("\n[7/18] Building productive matrix...")

productive_rows = []

n_dropped_unparsed = 0
n_dropped_func = 0

for _, row in token_df.iterrows():

    val = row[parsed_col]

    parsed_flag = (
        val is True
        or val == 1
        or str(val).lower() == "true"
    )

    if not parsed_flag:

        n_dropped_unparsed += 1
        continue

    cell = row[cell_col]

    parsed = parse_cell_id(cell)

    if parsed is None:

        n_dropped_func += 1
        continue

    productive_rows.append({

        "folio":
            row[folio_col],

        "section":
            row[section_col],

        "cell_id":
            str(cell)
    })

prod_df = pd.DataFrame(
    productive_rows
)

print(
    f"Retained productive rows: "
    f"{len(prod_df)}"
)

print(
    f"Dropped unparsed: "
    f"{n_dropped_unparsed}"
)

print(
    f"Dropped FUNC/invalid: "
    f"{n_dropped_func}"
)

matrix = pd.crosstab(

    prod_df["folio"],
    prod_df["cell_id"]
)

matrix = matrix.sort_index()

section_labels = (
    prod_df
    .groupby("folio")["section"]
    .agg(lambda x: x.mode().iloc[0])
)

section_labels = section_labels.loc[
    matrix.index
]

print(
    f"Matrix shape: {matrix.shape}"
)


# ============================================================
# Merge Currier Metadata
# ============================================================

print("\n[8/18] Merging Currier metadata...")

meta = pd.DataFrame({
    "folio":
        matrix.index,

    "section":
        section_labels.values
})

meta = meta.merge(
    currier_df,
    on="folio",
    how="left"
)

print(
    meta["currier_lang"]
    .value_counts(dropna=False)
)

# ============================================================
# B1
# ============================================================

print("\n====================================================")
print("B1: HERBAL-A INTERNAL CURRIER SPLIT")
print("====================================================")

b1 = meta[
    meta["section"] == "herbal-A"
].copy()

b1 = b1[
    b1["currier_lang"]
    .isin(["A", "B"])
]

print(
    f"Herbal-A folios with Currier labels: "
    f"{len(b1)}"
)

print(
    b1["currier_lang"]
    .value_counts()
)

X_b1 = matrix.loc[
    b1["folio"]
].values

y_b1 = (
    b1["currier_lang"]
    .values
)

# ============================================================
# Train/Test Split
# ============================================================

print("\n[9/18] B1 train/test split...")

(
    X_train,
    X_test,

    y_train,
    y_test,

    folio_train,
    folio_test

) = train_test_split(

    X_b1,
    y_b1,
    b1["folio"].values,

    test_size=0.30,

    stratify=y_b1,

    random_state=SEED
)

print(
    f"Train n = {len(y_train)}"
)

print(
    f"Test n = {len(y_test)}"
)

# ============================================================
# Scaling
# ============================================================

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(
    X_train
)

X_test_scaled = scaler.transform(
    X_test
)

# ============================================================
# Model
# ============================================================

print("\n[10/18] B1 logistic regression...")

clf = LogisticRegression(
    max_iter=5000,
    random_state=SEED
)

clf.fit(
    X_train_scaled,
    y_train
)

pred = clf.predict(
    X_test_scaled
)

prob = clf.predict_proba(
    X_test_scaled
)[:, 1]

y_binary = np.array([
    1 if x == "B" else 0
    for x in y_test
])

# ============================================================
# Metrics
# ============================================================

accuracy = accuracy_score(
    y_test,
    pred
)

balanced_acc = balanced_accuracy_score(
    y_test,
    pred
)

precision = precision_score(
    y_test,
    pred,
    pos_label="B",
    zero_division=0
)

recall = recall_score(
    y_test,
    pred,
    pos_label="B",
    zero_division=0
)

f1 = f1_score(
    y_test,
    pred,
    pos_label="B",
    zero_division=0
)

auc = roc_auc_score(
    y_binary,
    prob
)

print(
    f"AUC = {auc:.4f}"
)

# ============================================================
# Bootstrap Metrics
# ============================================================

print("\n[11/18] B1 bootstrap metrics...")

boot_metrics = {

    "accuracy": [],
    "balanced_accuracy": [],
    "precision": [],
    "recall": [],
    "f1": [],
    "auc": []
}

for _ in range(N_BOOTSTRAPS):

    idx = np.random.choice(
        len(y_test),
        size=len(y_test),
        replace=True
    )

    y_t = np.array(y_test)[idx]
    p_t = np.array(pred)[idx]
    pr_t = np.array(prob)[idx]

    yb_t = np.array([
        1 if x == "B" else 0
        for x in y_t
    ])

    # ========================================================
    # AUC undefined if bootstrap sample has one class only
    # ========================================================

    if len(np.unique(yb_t)) < 2:
        continue

    try:

        boot_metrics["accuracy"].append(
            accuracy_score(y_t, p_t)
        )

        boot_metrics["balanced_accuracy"].append(
            balanced_accuracy_score(y_t, p_t)
        )

        boot_metrics["precision"].append(
            precision_score(
                y_t,
                p_t,
                pos_label="B",
                zero_division=0
            )
        )

        boot_metrics["recall"].append(
            recall_score(
                y_t,
                p_t,
                pos_label="B",
                zero_division=0
            )
        )

        boot_metrics["f1"].append(
            f1_score(
                y_t,
                p_t,
                pos_label="B",
                zero_division=0
            )
        )

        boot_metrics["auc"].append(
            roc_auc_score(
                yb_t,
                pr_t
            )
        )

    except Exception:
        continue

# ============================================================
# Permutation Null
# ============================================================

print("\n[12/18] B1 permutation null...")

perm_aucs = []

for sim in range(N_PERMUTATIONS):

    y_perm = np.random.permutation(
        y_train
    )

    perm_clf = LogisticRegression(
        max_iter=5000,
        random_state=SEED
    )

    perm_clf.fit(
        X_train_scaled,
        y_perm
    )

    perm_prob = perm_clf.predict_proba(
        X_test_scaled
    )[:, 1]

    perm_auc = roc_auc_score(
        y_binary,
        perm_prob
    )

    perm_aucs.append(
        perm_auc
    )

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_PERMUTATIONS}"
        )

perm_mean = np.mean(
    perm_aucs
)

perm_std = np.std(
    perm_aucs
)

if perm_std <= 1e-6:

    raise RuntimeError(
        "Degenerate permutation null."
    )

perm_z = (
    auc - perm_mean
) / perm_std

perm_p = (
    np.sum(
        np.array(perm_aucs)
        >= auc
    ) + 1
) / (
    N_PERMUTATIONS + 1
)

# ============================================================
# Discriminative Cells
# ============================================================

coef = clf.coef_[0]

coef_df = pd.DataFrame({

    "cell_id":
        matrix.columns,

    "coefficient":
        coef,

    "abs_coefficient":
        np.abs(coef)
})

coef_df = coef_df.sort_values(
    "abs_coefficient",
    ascending=False
)

top10 = coef_df.head(10)

coef_path = os.path.join(
    OUTPUT_DIR,
    "taskB1_discriminative_cells.csv"
)

coef_df.to_csv(
    coef_path,
    index=False
)

# ============================================================
# B1 Metrics JSON
# ============================================================

b1_metrics = {

    "accuracy":
        metric_summary(
            boot_metrics["accuracy"]
        ),

    "balanced_accuracy":
        metric_summary(
            boot_metrics["balanced_accuracy"]
        ),

    "precision":
        metric_summary(
            boot_metrics["precision"]
        ),

    "recall":
        metric_summary(
            boot_metrics["recall"]
        ),

    "f1":
        metric_summary(
            boot_metrics["f1"]
        ),

    "auc":
        metric_summary(
            boot_metrics["auc"]
        )
}

b1_metrics_path = os.path.join(
    OUTPUT_DIR,
    "taskB1_herbal_currier_metrics.json"
)

with open(
    b1_metrics_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        b1_metrics,
        f,
        indent=2
    )

# ============================================================
# B1 Interpretation
# ============================================================

finding_level = "NULL"

if auc > 0.80:
    finding_level = "LOCKED"

elif auc > 0.65:
    finding_level = "STRONG"

elif auc > 0.55:
    finding_level = "CANDIDATE"

# ============================================================
# B1 Summary
# ============================================================

b1_summary = {

    "task":
        "B1",

    "finding_level":
        finding_level,

    "n":
        int(len(b1)),

    "train_n":
        int(len(y_train)),

    "test_n":
        int(len(y_test)),

    "class_distribution": {

        "A":
            int(np.sum(y_b1 == "A")),

        "B":
            int(np.sum(y_b1 == "B"))
    },

    "metrics": {

        "accuracy":
            float(accuracy),

        "balanced_accuracy":
            float(balanced_acc),

        "precision":
            float(precision),

        "recall":
            float(recall),

        "f1":
            float(f1),

        "auc":
            float(auc)
    },

    "bootstrap_metrics":
        b1_metrics,

    "permutation_null": {

        "mean":
            float(perm_mean),

        "std":
            float(perm_std),

        "z":
            float(perm_z),

        "p":
            float(perm_p)
    },

    "top_discriminative_cells":
        top10.to_dict(orient="records"),

    "interpretation_rule": {

        "AUC_gt_0_80":
            "LOCKED",

        "AUC_0_65_to_0_80":
            "STRONG",

        "AUC_0_55_to_0_65":
            "CANDIDATE",

        "AUC_lt_0_55":
            "NULL"
    },

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

b1_summary_path = os.path.join(
    OUTPUT_DIR,
    "taskB1_summary.json"
)

with open(
    b1_summary_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        b1_summary,
        f,
        indent=2
    )

# ============================================================
# FIGURE: B1 ROC
# ============================================================

print("\n[13/18] Writing B1 figures...")

fpr, tpr, _ = roc_curve(
    y_binary,
    prob
)

fig, ax = plt.subplots(
    figsize=(12, 8)
)

ax.plot(
    fpr,
    tpr,
    linewidth=3,
    label=f"AUC = {auc:.3f}"
)

ax.plot(
    [0, 1],
    [0, 1],
    linestyle="--"
)

ax.set_xlabel(
    "False Positive Rate"
)

ax.set_ylabel(
    "True Positive Rate"
)

ax.set_title(
    "TASK B1\n"
    "Herbal-A Currier Prediction"
)

caption = (
    "Source: MASTER_TOKEN_MATRIX.xlsx "
    "+ currier_labels.csv"
)

fig.text(
    0.01,
    0.01,
    caption,
    fontsize=8
)

ax.legend()

plt.tight_layout()

plt.savefig(

    os.path.join(
        FIG_DIR,
        "taskB1_roc_curve.png"
    ),

    dpi=150
)

plt.close()

# ============================================================
# FIGURE: TOP CELLS
# ============================================================

fig, ax = plt.subplots(
    figsize=(12, 8)
)

plot_df = top10.iloc[::-1]

bars = ax.barh(
    plot_df["cell_id"],
    plot_df["coefficient"]
)

for bar, coefv in zip(
    bars,
    plot_df["coefficient"]
):

    ax.text(
        coefv,
        bar.get_y() + bar.get_height()/2,
        f"{coefv:.3f}",
        va="center"
    )

ax.set_title(
    "TASK B1\n"
    "Top 10 Discriminative Cells"
)

ax.set_xlabel(
    "Logistic Coefficient"
)

fig.text(
    0.01,
    0.01,
    caption,
    fontsize=8
)

plt.tight_layout()

plt.savefig(

    os.path.join(
        FIG_DIR,
        "taskB1_top_cells.png"
    ),

    dpi=150
)

plt.close()

# ============================================================
# B2
# ============================================================

print("\n====================================================")
print("B2: CURRIER-B HAND PREDICTION")
print("====================================================")

b2 = meta[
    meta["currier_lang"] == "B"
].copy()

# ============================================================
# Normalize hand labels
# ============================================================

b2["currier_hand"] = (
    b2["currier_hand"]
    .astype(str)
    .str.strip()
)

b2 = b2[
    b2["currier_hand"]
    .isin(["2", "3", "4"])
]

print(
    b2["currier_hand"]
    .value_counts()
)

X_b2 = matrix.loc[
    b2["folio"]
].values

y_b2 = (
    b2["currier_hand"]
    .astype(str)
    .values
)

# ============================================================
# Split
# ============================================================

(
    X2_train,
    X2_test,

    y2_train,
    y2_test

) = train_test_split(

    X_b2,
    y_b2,

    test_size=0.30,

    stratify=y_b2,

    random_state=SEED
)

# ============================================================
# Scale
# ============================================================

scaler2 = StandardScaler()

X2_train_scaled = scaler2.fit_transform(
    X2_train
)

X2_test_scaled = scaler2.transform(
    X2_test
)

# ============================================================
# Multinomial Model
# ============================================================

print("\n[14/18] B2 multinomial logistic regression...")

clf2 = LogisticRegression(

    max_iter=5000,
    random_state=SEED
)

clf2.fit(
    X2_train_scaled,
    y2_train
)

pred2 = clf2.predict(
    X2_test_scaled
)

# ============================================================
# Metrics
# ============================================================

macro_f1 = f1_score(
    y2_test,
    pred2,
    average="macro",
    zero_division=0
)

balanced2 = balanced_accuracy_score(
    y2_test,
    pred2
)

report2 = classification_report(
    y2_test,
    pred2,
    output_dict=True,
    zero_division=0
)

# ============================================================
# Section Baseline
# ============================================================

print("\n[15/18] Computing section baseline...")

baseline_table = pd.crosstab(

    b2["section"],
    b2["currier_hand"]
)

section_pred = []

for _, row in b2.iterrows():

    sec = row["section"]

    pred_hand = (
        baseline_table.loc[sec]
        .idxmax()
    )

    section_pred.append(
        str(pred_hand)
    )

section_macro_f1 = f1_score(

    y_b2,
    section_pred,

    average="macro",
    zero_division=0
)

# ============================================================
# B2 Summary
# ============================================================

b2_level = "SECTION-CONFOUNDED"

if (
    macro_f1 > 0.70
    and macro_f1 > section_macro_f1
):
    b2_level = "STRONG"

b2_summary = {

    "task":
        "B2",

    "finding_level":
        b2_level,

    "n":
        int(len(b2)),

    "macro_f1":
        float(macro_f1),

    "balanced_accuracy":
        float(balanced2),

    "section_baseline_macro_f1":
        float(section_macro_f1),

    "per_hand_metrics":
        report2,

    "section_confound_warning": (
        "hand-2 dominated by balneo/rosettes/herbal-B; "
        "hand-3 dominated by stars; "
        "hand-4 dominated by cosmo/zodiac."
    ),

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

b2_summary_path = os.path.join(
    OUTPUT_DIR,
    "taskB2_summary.json"
)

with open(
    b2_summary_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        b2_summary,
        f,
        indent=2
    )

# ============================================================
# B2 Metrics JSON
# ============================================================

b2_metrics_path = os.path.join(
    OUTPUT_DIR,
    "taskB2_hand_metrics.json"
)

with open(
    b2_metrics_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report2,
        f,
        indent=2
    )

# ============================================================
# FIGURE: CONFUSION MATRIX
# ============================================================

print("\n[16/18] Writing B2 figures...")

labels_b2 = sorted(
    list(set(y2_test))
)

cm2 = confusion_matrix(
    y2_test,
    pred2,
    labels=labels_b2
)

fig, ax = plt.subplots(
    figsize=(12, 8)
)

im = ax.imshow(cm2)

ax.set_xticks(
    np.arange(len(labels_b2))
)

ax.set_yticks(
    np.arange(len(labels_b2))
)

ax.set_xticklabels(
    labels_b2
)

ax.set_yticklabels(
    labels_b2
)

for i in range(len(labels_b2)):

    for j in range(len(labels_b2)):

        ax.text(
            j,
            i,
            cm2[i, j],
            ha="center",
            va="center"
        )

ax.set_title(
    "TASK B2\n"
    "Currier Hand Prediction"
)

ax.set_xlabel(
    "Predicted"
)

ax.set_ylabel(
    "True"
)

fig.colorbar(im)

fig.text(
    0.01,
    0.01,
    caption,
    fontsize=8
)

plt.tight_layout()

plt.savefig(

    os.path.join(
        FIG_DIR,
        "taskB2_confusion_matrix.png"
    ),

    dpi=150
)

plt.close()

# ============================================================
# FIGURE: PER-HAND F1
# ============================================================

f1_rows = []

for hand in labels_b2:

    if hand in report2:

        f1_rows.append({

            "hand":
                hand,

            "f1":
                report2[hand]["f1-score"]
        })

f1_df = pd.DataFrame(
    f1_rows
)

fig, ax = plt.subplots(
    figsize=(12, 8)
)

bars = ax.bar(
    f1_df["hand"],
    f1_df["f1"]
)

ax.axhline(
    section_macro_f1,
    linestyle="--",
    linewidth=2,
    label="Section baseline"
)

ax.set_ylim(0, 1)

ax.set_title(
    "TASK B2\n"
    "Per-Hand F1 Scores"
)

ax.set_ylabel(
    "F1 Score"
)

ax.legend()

fig.text(
    0.01,
    0.01,
    caption,
    fontsize=8
)

plt.tight_layout()

plt.savefig(

    os.path.join(
        FIG_DIR,
        "taskB2_f1_scores.png"
    ),

    dpi=150
)

plt.close()

# ============================================================
# Master Summary
# ============================================================

print("\n[17/18] Writing master summary...")

master_summary = {

    "task":
        "B",

    "B1": {

        "finding_level":
            finding_level,

        "auc":
            float(auc),

        "z":
            float(perm_z),

        "p":
            float(perm_p)
    },

    "B2": {

        "finding_level":
            b2_level,

        "macro_f1":
            float(macro_f1),

        "section_baseline":
            float(section_macro_f1)
    },

    "input_sha256": {

        INPUT_MATRIX:
            matrix_sha,

        INPUT_CURRIER:
            sha256_file(INPUT_CURRIER)
    },

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

master_summary_path = os.path.join(
    OUTPUT_DIR,
    "summary_v7.json"
)

with open(
    master_summary_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        master_summary,
        f,
        indent=2
    )

# ============================================================
# Markdown Brief
# ============================================================

print("\n[18/18] Writing markdown brief...")

brief = f"""
# TASK B v2 — Currier External Validation

## B1 — Herbal-A Internal Currier Split

Finding level:
**{finding_level}**

AUC:
**{auc:.4f}**

Permutation z:
**{perm_z:.2f}**

Empirical p:
**{perm_p:.6f}**

Interpretation:
This test controls for illustration type by restricting
classification to herbal-A folios only.

A successful result indicates that the productive register
grammar captures variation correlated with Currier's
independent paleographic judgment within the same visual
genre.

---

## B2 — Currier-B Hand Prediction

Finding level:
**{b2_level}**

Macro-F1:
**{macro_f1:.4f}**

Section baseline:
**{section_macro_f1:.4f}**

Interpretation:
This test is heavily section-confounded.

hand-2:
balneo/rosettes/herbal-B dominant

hand-3:
stars dominant

hand-4:
cosmo/zodiac dominant

The critical comparison is whether morphology predicts
hand better than section identity alone.

---

## Input Integrity

MASTER_TOKEN_MATRIX.xlsx SHA-256:

{matrix_sha}

Verified against locked audit value.

"""

brief_path = os.path.join(
    OUTPUT_DIR,
    "taskB_brief.md"
)

with open(
    brief_path,
    "w",
    encoding="utf-8"
) as f:

    f.write(brief)

# ============================================================
# Checksums
# ============================================================

artifact_paths = [

    b1_metrics_path,
    coef_path,
    b1_summary_path,

    b2_metrics_path,
    b2_summary_path,

    master_summary_path,
    brief_path
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
print("TASK B COMPLETE")
print("====================================================")

print(
    f"B1 AUC = {auc:.4f}"
)

print(
    f"B1 z = {perm_z:.2f}"
)

print(
    f"B1 p = {perm_p:.6f}"
)

print(
    f"B1 finding = {finding_level}"
)

print()

print(
    f"B2 macro-F1 = {macro_f1:.4f}"
)

print(
    f"B2 section baseline = "
    f"{section_macro_f1:.4f}"
)

print(
    f"B2 finding = {b2_level}"
)

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")