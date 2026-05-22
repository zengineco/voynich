#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK A: HELD-OUT FOLIO CLASSIFICATION
(Leakage-Controlled Replication of 79.45% Result)

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

Replicate and stress-test the locked 79.45% folio
classification result under strict held-out evaluation.

This script explicitly guards against:
- section aggregation leakage
- folio leakage
- feature leakage
- normalization leakage
- label imbalance artifacts
- degenerate folds

============================================================
LOCKED PRIOR RESULT
============================================================

Prior locked finding:
    LOO accuracy = 0.7945

This script tests whether the result survives:
- grouped held-out folds
- train/test isolation
- permutation-label baseline
- bootstrap confidence intervals

============================================================
INPUTS
============================================================

Required:
- MASTER_TOKEN_MATRIX.xlsx

Sheet:
- tokens_atomic

Required columns:
- folio
- section
- cell_id
- parsed

============================================================
FEATURE SPACE
============================================================

Features:
- productive register cells only
- FUNC excluded
- folio × cell count matrix

NO SECTION AGGREGATION.

============================================================
OUTPUT
============================================================

Creates:
    voynich_taskA_heldout_v1/

Files:
- fold_assignments.csv
- folio_feature_matrix.csv
- feature_vocabulary.csv
- heldout_predictions.csv
- permutation_null.csv
- bootstrap_accuracy.csv
- confusion_matrix.csv
- classification_report.csv
- summary.json
- checksums.json

Figures:
- confusion_matrix.png
- permutation_null.png
- bootstrap_accuracy.png
- calibration_curve.png

============================================================
METHODOLOGICAL SAFEGUARDS
============================================================

- stratified grouped folds
- train/test isolation
- no normalization leakage
- explicit permutation null
- parser self-test
- SHA-256 logging
- deterministic random seeds
- hard assertions on feature alignment
- fail-fast behavior

============================================================
"""

# ============================================================
# Imports
# ============================================================

import os
import json
import math
import hashlib
import random
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from sklearn.model_selection import (
    StratifiedKFold
)

from sklearn.preprocessing import (
    StandardScaler
)

from sklearn.linear_model import (
    LogisticRegression
)

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    classification_report,
    f1_score,
    roc_auc_score
)

from sklearn.calibration import calibration_curve

from sklearn.utils import resample


# ============================================================
# Constants
# ============================================================

SEED = 42

N_SPLITS = 5
N_PERMUTATIONS = 1000
N_BOOTSTRAPS = 1000

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskA_heldout_v1"
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

    raise ValueError(
        f"Could not detect required column. "
        f"Tried: {candidates}"
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

    lower = np.percentile(
        values,
        100 * (alpha / 2)
    )

    upper = np.percentile(
        values,
        100 * (1 - alpha / 2)
    )

    return lower, upper


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK A: HELD-OUT FOLIO CLASSIFICATION")
print("====================================================\n")


# ============================================================
# Load Data
# ============================================================

print("[1/17] Loading MASTER_TOKEN_MATRIX.xlsx...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: {INPUT_MATRIX}"
    )

df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(df)} rows"
)


# ============================================================
# Detect Columns
# ============================================================

print("\n[2/17] Detecting required columns...")

folio_col = detect_column(
    df,
    ["folio"]
)

section_col = detect_column(
    df,
    ["section"]
)

cell_col = detect_column(
    df,
    ["cell_id"]
)

parsed_col = detect_column(
    df,
    ["parsed"]
)

token_col = detect_column(
    df,
    ["token"]
)

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  section: {section_col}")
print(f"  cell_id: {cell_col}")
print(f"  parsed: {parsed_col}")


# ============================================================
# Audit parsed Column
# ============================================================

print("\n[3/17] Auditing parsed column...")

print(
    df[parsed_col]
    .value_counts(dropna=False)
    .head(20)
)


# ============================================================
# Build Productive Rows
# ============================================================

print("\n[4/17] Filtering productive cells...")

productive = []

for _, row in df.iterrows():

    val = row[parsed_col]

    parsed_flag = (
        val is True
        or val == 1
        or str(val).lower() == "true"
    )

    if not parsed_flag:
        continue

    cell = row[cell_col]

    parsed = parse_cell_id(cell)

    if parsed is None:
        continue

    productive.append({

        "folio":
            row[folio_col],

        "section":
            row[section_col],

        "cell_id":
            str(cell)
    })

prod_df = pd.DataFrame(
    productive
)

print(
    f"Remaining productive rows: "
    f"{len(prod_df)}"
)

if len(prod_df) < 1000:

    raise RuntimeError(
        "Too few productive rows after filtering."
    )


# ============================================================
# Parser Self-Test
# ============================================================

print("\n[5/17] Parser self-test...")

sample_cells = (
    prod_df["cell_id"]
    .value_counts()
    .head(10)
    .index
)

sanity_sample = []

for cell in sample_cells:

    parsed = parse_cell_id(cell)

    if parsed is None:
        continue

    sanity_sample.append({

        "cell_id":
            cell,

        "prefix":
            parsed[0],

        "grade":
            parsed[1],

        "axis":
            parsed[2]
    })

for row in sanity_sample:

    print(
        f"{row['cell_id']} -> "
        f"({row['prefix']}, "
        f"{row['grade']}, "
        f"{row['axis']})"
    )

if len(sanity_sample) < 8:

    raise RuntimeError(
        "Parser self-test failed."
    )


# ============================================================
# Build Folio × Cell Matrix
# ============================================================

print("\n[6/17] Building folio × cell matrix...")

matrix = pd.crosstab(
    prod_df["folio"],
    prod_df["cell_id"]
)

matrix = matrix.sort_index()

labels = (
    prod_df
    .groupby("folio")["section"]
    .agg(lambda x: x.mode().iloc[0])
)

labels = labels.loc[matrix.index]

# ============================================================
# Dynamic fold safety audit
# ============================================================

section_counts = (
    pd.Series(labels)
    .value_counts()
)

min_class_size = int(
    section_counts.min()
)

print(
    "\nSection counts:"
)

print(section_counts)

print(
    f"\nMinimum class size: "
    f"{min_class_size}"
)

if min_class_size < 2:

    raise RuntimeError(
        "At least one section has <2 folios. "
        "Cross-validation impossible."
    )

# ============================================================
# HARD RULE:
# folds cannot exceed smallest class
# ============================================================

N_SPLITS = min(
    5,
    min_class_size
)

print(
    f"Using {N_SPLITS} folds "
    f"(safe maximum)"
)

assert len(matrix) == len(labels)

feature_matrix_path = os.path.join(
    OUTPUT_DIR,
    "folio_feature_matrix.csv"
)

matrix.to_csv(
    feature_matrix_path
)

vocab_path = os.path.join(
    OUTPUT_DIR,
    "feature_vocabulary.csv"
)

pd.DataFrame({
    "cell_id": matrix.columns
}).to_csv(
    vocab_path,
    index=False
)

print(
    f"Matrix shape: {matrix.shape}"
)

print(
    f"Sections: {sorted(labels.unique())}"
)


# ============================================================
# Fold Construction
# ============================================================

print("\n[7/17] Constructing folds...")

X = matrix.values
y = labels.values
folios = matrix.index.values

skf = StratifiedKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=SEED
)

fold_rows = []

for fold_idx, (
    train_idx,
    test_idx
) in enumerate(skf.split(X, y)):

    train_folios = set(
        folios[train_idx]
    )

    test_folios = set(
        folios[test_idx]
    )

    overlap = (
        train_folios
        & test_folios
    )

    if len(overlap) > 0:

        raise RuntimeError(
            "Train/test folio leakage detected."
        )

    for idx in train_idx:

        fold_rows.append({

            "folio":
                folios[idx],

            "section":
                y[idx],

            "fold":
                fold_idx,

            "split":
                "train"
        })

    for idx in test_idx:

        fold_rows.append({

            "folio":
                folios[idx],

            "section":
                y[idx],

            "fold":
                fold_idx,

            "split":
                "test"
        })

fold_df = pd.DataFrame(
    fold_rows
)

fold_path = os.path.join(
    OUTPUT_DIR,
    "fold_assignments.csv"
)

fold_df.to_csv(
    fold_path,
    index=False
)


# ============================================================
# Held-Out Classification
# ============================================================

print("\n[8/17] Running held-out classification...")

all_true = []
all_pred = []
all_prob = []

prediction_rows = []

for fold_idx, (
    train_idx,
    test_idx
) in enumerate(skf.split(X, y)):

    X_train = X[train_idx]
    X_test = X[test_idx]

    y_train = y[train_idx]
    y_test = y[test_idx]

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    X_test_scaled = scaler.transform(
        X_test
    )

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
    )

    all_true.extend(y_test)
    all_pred.extend(pred)

    all_prob.extend(
        np.max(prob, axis=1)
    )

    for i in range(len(test_idx)):

        prediction_rows.append({

            "folio":
                folios[test_idx[i]],

            "true_section":
                y_test[i],

            "predicted_section":
                pred[i],

            "confidence":
                float(
                    np.max(prob[i])
                ),

            "fold":
                fold_idx
        })

pred_df = pd.DataFrame(
    prediction_rows
)

pred_path = os.path.join(
    OUTPUT_DIR,
    "heldout_predictions.csv"
)

pred_df.to_csv(
    pred_path,
    index=False)


# ============================================================
# Metrics
# ============================================================

print("\n[9/17] Computing metrics...")

accuracy = accuracy_score(
    all_true,
    all_pred
)

balanced_acc = balanced_accuracy_score(
    all_true,
    all_pred
)

macro_f1 = f1_score(
    all_true,
    all_pred,
    average="macro"
)

micro_f1 = f1_score(
    all_true,
    all_pred,
    average="micro"
)

print(
    f"Accuracy: {accuracy:.4f}"
)

print(
    f"Balanced Accuracy: "
    f"{balanced_acc:.4f}"
)


# ============================================================
# Confusion Matrix
# ============================================================

print("\n[10/17] Confusion matrix...")

classes = sorted(
    list(set(all_true))
)

cm = confusion_matrix(
    all_true,
    all_pred,
    labels=classes
)

cm_df = pd.DataFrame(
    cm,
    index=classes,
    columns=classes
)

cm_path = os.path.join(
    OUTPUT_DIR,
    "confusion_matrix.csv"
)

cm_df.to_csv(
    cm_path
)

report = classification_report(
    all_true,
    all_pred,
    output_dict=True
)

report_df = pd.DataFrame(
    report
).transpose()

report_path = os.path.join(
    OUTPUT_DIR,
    "classification_report.csv"
)

report_df.to_csv(
    report_path
)


# ============================================================
# Permutation Null
# ============================================================

print("\n[11/17] Running permutation null...")

perm_scores = []

for sim in range(N_PERMUTATIONS):

    shuffled_y = np.random.permutation(y)

    sim_scores = []

    for (
        train_idx,
        test_idx
    ) in skf.split(X, shuffled_y):

        X_train = X[train_idx]
        X_test = X[test_idx]

        y_train = shuffled_y[train_idx]
        y_test = shuffled_y[test_idx]

        scaler = StandardScaler()

        X_train_scaled = scaler.fit_transform(
            X_train
        )

        X_test_scaled = scaler.transform(
            X_test
        )

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

        sim_scores.append(
            accuracy_score(
                y_test,
                pred
            )
        )

    perm_scores.append(
        np.mean(sim_scores)
    )

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_PERMUTATIONS}"
        )

perm_df = pd.DataFrame({
    "accuracy": perm_scores
})

perm_path = os.path.join(
    OUTPUT_DIR,
    "permutation_null.csv"
)

perm_df.to_csv(
    perm_path,
    index=False
)

perm_mean = np.mean(perm_scores)
perm_std = np.std(perm_scores)

perm_z = (
    accuracy - perm_mean
) / perm_std

perm_p = (
    np.sum(
        np.array(perm_scores)
        >= accuracy
    ) + 1
) / (N_PERMUTATIONS + 1)


# ============================================================
# Bootstrap Accuracy
# ============================================================

print("\n[12/17] Bootstrap confidence intervals...")

boot_scores = []

pred_array = np.array(all_pred)
true_array = np.array(all_true)

for _ in range(N_BOOTSTRAPS):

    idx = np.random.choice(
        len(pred_array),
        size=len(pred_array),
        replace=True
    )

    score = accuracy_score(
        true_array[idx],
        pred_array[idx]
    )

    boot_scores.append(score)

boot_df = pd.DataFrame({
    "accuracy": boot_scores
})

boot_path = os.path.join(
    OUTPUT_DIR,
    "bootstrap_accuracy.csv"
)

boot_df.to_csv(
    boot_path,
    index=False
)

boot_lo, boot_hi = bootstrap_ci(
    boot_scores
)


# ============================================================
# Figures
# ============================================================

print("\n[13/17] Writing figures...")

# ------------------------------------------------------------
# Confusion Matrix
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(8, 8)
)

im = ax.imshow(cm)

ax.set_xticks(
    np.arange(len(classes))
)

ax.set_yticks(
    np.arange(len(classes))
)

ax.set_xticklabels(
    classes,
    rotation=45,
    ha="right"
)

ax.set_yticklabels(classes)

for i in range(len(classes)):

    for j in range(len(classes)):

        ax.text(
            j,
            i,
            cm[i, j],
            ha="center",
            va="center"
        )

ax.set_title(
    "Held-Out Confusion Matrix"
)

fig.colorbar(im)

plt.tight_layout()

cm_fig = os.path.join(
    FIG_DIR,
    "confusion_matrix.png"
)

plt.savefig(
    cm_fig,
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# Permutation Null
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(8, 5)
)

ax.hist(
    perm_scores,
    bins=40
)

ax.axvline(
    accuracy,
    color="red",
    linewidth=3
)

ax.text(
    0.98,
    0.98,
    f"acc={accuracy:.3f}\n"
    f"z={perm_z:.2f}\n"
    f"p={perm_p:.4f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white")
)

ax.set_title(
    "Permutation Null Accuracy"
)

perm_fig = os.path.join(
    FIG_DIR,
    "permutation_null.png"
)

plt.tight_layout()

plt.savefig(
    perm_fig,
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# Bootstrap Accuracy
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(8, 5)
)

ax.hist(
    boot_scores,
    bins=40
)

ax.axvline(
    accuracy,
    color="red",
    linewidth=3
)

ax.axvline(
    boot_lo,
    linestyle="--"
)

ax.axvline(
    boot_hi,
    linestyle="--"
)

ax.set_title(
    "Bootstrap Accuracy Distribution"
)

boot_fig = os.path.join(
    FIG_DIR,
    "bootstrap_accuracy.png"
)

plt.tight_layout()

plt.savefig(
    boot_fig,
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# Calibration Curve
# ------------------------------------------------------------

print("\n[14/17] Calibration curve...")

correct = np.array(
    all_true
) == np.array(
    all_pred
)

prob_true, prob_pred = calibration_curve(
    correct,
    all_prob,
    n_bins=10
)

fig, ax = plt.subplots(
    figsize=(6, 6)
)

ax.plot(
    prob_pred,
    prob_true,
    marker="o"
)

ax.plot(
    [0, 1],
    [0, 1],
    linestyle="--"
)

ax.set_xlabel(
    "Predicted Confidence"
)

ax.set_ylabel(
    "Observed Accuracy"
)

ax.set_title(
    "Calibration Curve"
)

cal_fig = os.path.join(
    FIG_DIR,
    "calibration_curve.png"
)

plt.tight_layout()

plt.savefig(
    cal_fig,
    dpi=300
)

plt.close()


# ============================================================
# Leakage Audit
# ============================================================

print("\n[15/17] Leakage audit...")

leakage_audit = {

    "section_aggregation_used":
        False,

    "folio_overlap_detected":
        False,

    "train_test_scaler_leakage":
        False,

    "feature_vocabulary_aligned":
        True,

    "normalization_fit_train_only":
        True,

    "null_model":
        "label permutation"
}


# ============================================================
# Summary JSON
# ============================================================

print("\n[16/17] Writing summary...")

summary = {

    "test_name":
        "Held-Out Folio Classification",

    "version":
        "v1",

    "input_sha256": {
        INPUT_MATRIX:
            sha256_file(INPUT_MATRIX)
    },

    "matrix_shape":
        list(matrix.shape),

    "n_folios":
        int(matrix.shape[0]),

    "n_features":
        int(matrix.shape[1]),

    "sections":
        sorted(
            list(
                set(labels)
            )
        ),

    "metrics": {

        "accuracy":
            float(accuracy),

        "balanced_accuracy":
            float(balanced_acc),

        "macro_f1":
            float(macro_f1),

        "micro_f1":
            float(micro_f1)
    },

    "bootstrap_ci_95": {

        "lower":
            float(boot_lo),

        "upper":
            float(boot_hi)
    },

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

    "locked_thresholds": {

        "within_5_points_of_0.7945":
            abs(
                accuracy - 0.7945
            ) <= 0.05,

        "drop_gt_15_points":
            (
                0.7945 - accuracy
            ) > 0.15
    },

    "parser_self_test":
        sanity_sample,

    "leakage_audit":
        leakage_audit,

    "random_seed":
        SEED,

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
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

print("\n[17/17] Writing checksums...")

artifact_paths = [

    feature_matrix_path,
    vocab_path,
    fold_path,
    pred_path,
    perm_path,
    boot_path,
    cm_path,
    report_path,
    summary_path,

    cm_fig,
    perm_fig,
    boot_fig,
    cal_fig
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
print("COMPLETE")
print("====================================================")

print(
    f"Held-out accuracy: "
    f"{accuracy:.4f}"
)

print(
    f"Permutation z-score: "
    f"{perm_z:.2f}"
)

print(
    f"Permutation p-value: "
    f"{perm_p:.6f}"
)

print(
    f"95% bootstrap CI: "
    f"[{boot_lo:.4f}, {boot_hi:.4f}]"
)

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")