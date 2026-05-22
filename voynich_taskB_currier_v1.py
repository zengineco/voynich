#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK B: CURRIER EXTERNAL VALIDATION
(Independent Taxonomy Generalization Test)

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

Test whether the productive 130-cell register grammar
generalizes to an INDEPENDENT external classification system:
Currier A / Currier B.

This is an external validation test.

Unlike Task A, which predicts internally-derived sections,
Task B predicts an externally-established manuscript partition.

============================================================
CORE QUESTION
============================================================

Does the productive register grammar recover Currier structure
better than chance on held-out folios?

============================================================
METHODOLOGICAL STATUS
============================================================

This test is ONLY valid if Currier labels have:

1. explicit provenance
2. unambiguous folio linkage
3. stable mapping

The script HALTS if provenance requirements fail.

============================================================
INPUTS
============================================================

Required:
- MASTER_TOKEN_MATRIX.xlsx
- func_extended_communities.csv
  (optional contextual reference only)
- currier_labels.csv

============================================================
EXPECTED CURRIER LABEL FORMAT
============================================================

Required columns:
- folio
- currier

Allowed labels:
- A
- B
- ?   (excluded)
- mixed (excluded)

============================================================
CURRIER PROVENANCE REQUIREMENT
============================================================

currier_labels.csv MUST contain:

- folio
- currier
- source

The source field MUST identify provenance.

Examples:
- "Currier 1976"
- "Zandbergen-Landini"
- "Takahashi annotation"

If missing:
    HARD FAIL

============================================================
FEATURE SPACE
============================================================

- folio × productive-cell count matrix
- productive cells only
- FUNC excluded
- no section aggregation

============================================================
OUTPUT
============================================================

voynich_taskB_currier_v1/

FILES
=====

- currier_feature_matrix.csv
- fold_assignments.csv
- heldout_predictions.csv
- permutation_null.csv
- bootstrap_auc.csv
- confusion_matrix.csv
- classification_report.csv
- roc_curve.csv
- feature_importance.csv
- summary.json
- checksums.json

FIGURES
=======

- confusion_matrix.png
- roc_curve.png
- permutation_null.png
- bootstrap_auc.png
- calibration_curve.png
- top_features.png

============================================================
LOCK THRESHOLDS
============================================================

AUC > 0.80:
    LOCKED external validation

0.65–0.80:
    STRONG

0.55–0.65:
    CANDIDATE

<0.55:
    NULL

============================================================
METHODOLOGICAL SAFEGUARDS
============================================================

- strict folio isolation
- scaler fit on training only
- no inferred Currier labels
- no heuristic reconstruction
- deterministic seeds
- empirical p-values only
- bootstrap confidence intervals
- fail-fast provenance audit

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
    roc_auc_score,
    roc_curve
)

from sklearn.calibration import (
    calibration_curve
)

# ============================================================
# Constants
# ============================================================

SEED = 42

N_SPLITS = 5
N_PERMUTATIONS = 1000
N_BOOTSTRAPS = 1000

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"
INPUT_CURRIER = "currier_labels.csv"

OUTPUT_DIR = "voynich_taskB_currier_v1"

FIG_DIR = os.path.join(
    OUTPUT_DIR,
    "figures"
)

random.seed(SEED)
np.random.seed(SEED)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    FIG_DIR,
    exist_ok=True
)

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
print("TASK B: CURRIER EXTERNAL VALIDATION")
print("====================================================\n")


# ============================================================
# Input Audit
# ============================================================

print("[1/16] Auditing required files...")

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
# Load Matrix
# ============================================================

print("\n[2/16] Loading MASTER_TOKEN_MATRIX.xlsx...")

token_df = pd.read_excel(
    INPUT_MATRIX,
    sheet_name="tokens_atomic"
)

print(
    f"Loaded {len(token_df)} token rows"
)


# ============================================================
# Load Currier Labels
# ============================================================

print("\n[3/16] Loading Currier labels...")

currier_df = pd.read_csv(
    INPUT_CURRIER
)

print(
    f"Loaded {len(currier_df)} Currier rows"
)


# ============================================================
# Currier Provenance Audit
# ============================================================

print("\n[4/16] Currier provenance audit...")

required_currier_cols = [
    "folio",
    "currier",
    "source"
]

for col in required_currier_cols:

    if col not in currier_df.columns:

        raise RuntimeError(
            f"Missing required Currier column: {col}"
        )

print("Currier provenance column present.")

print("\nCurrier sources:")

print(
    currier_df["source"]
    .value_counts(dropna=False)
)

allowed_labels = {
    "A",
    "B",
    "?",
    "mixed"
}

bad_labels = set(
    currier_df["currier"]
) - allowed_labels

if len(bad_labels) > 0:

    raise RuntimeError(
        f"Unexpected Currier labels: {bad_labels}"
    )


# ============================================================
# Detect Token Columns
# ============================================================

print("\n[5/16] Detecting token columns...")

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
# Audit parsed Column
# ============================================================

print("\n[6/16] Auditing parsed column...")

print(
    token_df[parsed_col]
    .value_counts(dropna=False)
)


# ============================================================
# Build Productive Rows
# ============================================================

print("\n[7/16] Filtering productive cells...")

productive_rows = []

for _, row in token_df.iterrows():

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
    f"Remaining productive rows: "
    f"{len(prod_df)}"
)


# ============================================================
# Parser Self-Test
# ============================================================

print("\n[8/16] Parser self-test...")

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

print("\n[9/16] Building folio × cell matrix...")

matrix = pd.crosstab(
    prod_df["folio"],
    prod_df["cell_id"]
)

matrix = matrix.sort_index()

matrix_path = os.path.join(
    OUTPUT_DIR,
    "currier_feature_matrix.csv"
)

matrix.to_csv(
    matrix_path
)

print(
    f"Matrix shape: {matrix.shape}"
)


# ============================================================
# Merge Currier Labels
# ============================================================

print("\n[10/16] Merging Currier labels...")

currier_df = currier_df.copy()

currier_df = currier_df[
    currier_df["currier"]
    .isin(["A", "B"])
]

merged = pd.DataFrame({
    "folio":
        matrix.index
})

merged = merged.merge(
    currier_df[
        ["folio", "currier"]
    ],
    on="folio",
    how="inner"
)

print(
    f"Matched folios: {len(merged)}"
)

if len(merged) < 20:

    raise RuntimeError(
        "Too few Currier-linked folios."
    )

X = matrix.loc[
    merged["folio"]
].values

y = merged["currier"].values

folios = merged["folio"].values

class_counts = pd.Series(y).value_counts()

print("\nCurrier counts:")
print(class_counts)

if class_counts.min() < N_SPLITS:

    raise RuntimeError(
        "Cannot run 5-fold CV: "
        "one Currier class has <5 folios."
    )


# ============================================================
# Fold Construction
# ============================================================

print("\n[11/16] Constructing folds...")

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

            "currier":
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

            "currier":
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

print("\n[12/16] Running held-out classification...")

all_true = []
all_pred = []
all_prob = []

prediction_rows = []

feature_weights = []

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
    )[:, 1]

    all_true.extend(y_test)
    all_pred.extend(pred)
    all_prob.extend(prob)

    coef = clf.coef_[0]

    feature_weights.append(coef)

    for i in range(len(test_idx)):

        prediction_rows.append({

            "folio":
                folios[test_idx[i]],

            "true_currier":
                y_test[i],

            "predicted_currier":
                pred[i],

            "prob_B":
                float(prob[i]),

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
    index=False
)


# ============================================================
# Metrics
# ============================================================

print("\n[13/16] Computing metrics...")

y_binary = np.array([
    1 if x == "B" else 0
    for x in all_true
])

auc = roc_auc_score(
    y_binary,
    all_prob
)

accuracy = accuracy_score(
    all_true,
    all_pred
)

balanced_acc = balanced_accuracy_score(
    all_true,
    all_pred
)

print(
    f"AUC: {auc:.4f}"
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

cm = confusion_matrix(
    all_true,
    all_pred,
    labels=["A", "B"]
)

cm_df = pd.DataFrame(
    cm,
    index=["A", "B"],
    columns=["A", "B"]
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
    output_dict=True,
    zero_division=0
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
# ROC Curve
# ============================================================

fpr, tpr, thresh = roc_curve(
    y_binary,
    all_prob
)

roc_df = pd.DataFrame({

    "fpr":
        fpr,

    "tpr":
        tpr,

    "threshold":
        thresh
})

roc_path = os.path.join(
    OUTPUT_DIR,
    "roc_curve.csv"
)

roc_df.to_csv(
    roc_path,
    index=False
)


# ============================================================
# Permutation Null
# ============================================================

print("\n[14/16] Running permutation null...")

perm_aucs = []

for sim in range(N_PERMUTATIONS):

    shuffled_y = np.random.permutation(y)

    all_perm_true = []
    all_perm_prob = []

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

        prob = clf.predict_proba(
            X_test_scaled
        )[:, 1]

        all_perm_true.extend(y_test)
        all_perm_prob.extend(prob)

    perm_binary = np.array([
        1 if x == "B" else 0
        for x in all_perm_true
    ])

    perm_auc = roc_auc_score(
        perm_binary,
        all_perm_prob
    )

    perm_aucs.append(
        perm_auc
    )

    if (sim + 1) % 100 == 0:

        print(
            f"  {sim + 1}/{N_PERMUTATIONS}"
        )

perm_df = pd.DataFrame({
    "auc":
        perm_aucs
})

perm_path = os.path.join(
    OUTPUT_DIR,
    "permutation_null.csv"
)

perm_df.to_csv(
    perm_path,
    index=False
)

perm_mean = np.mean(
    perm_aucs
)

perm_std = np.std(
    perm_aucs
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
# Bootstrap AUC
# ============================================================

print("\n[15/16] Running bootstrap AUC...")

boot_aucs = []

true_array = np.array(
    y_binary
)

prob_array = np.array(
    all_prob
)

for _ in range(N_BOOTSTRAPS):

    idx = np.random.choice(
        len(prob_array),
        size=len(prob_array),
        replace=True
    )

    score = roc_auc_score(
        true_array[idx],
        prob_array[idx]
    )

    boot_aucs.append(score)

boot_df = pd.DataFrame({
    "auc":
        boot_aucs
})

boot_path = os.path.join(
    OUTPUT_DIR,
    "bootstrap_auc.csv"
)

boot_df.to_csv(
    boot_path,
    index=False
)

boot_lo, boot_hi = bootstrap_ci(
    boot_aucs
)


# ============================================================
# Feature Importance
# ============================================================

mean_coef = np.mean(
    feature_weights,
    axis=0
)

importance_df = pd.DataFrame({

    "cell_id":
        matrix.columns,

    "weight":
        mean_coef
})

importance_df = importance_df.sort_values(
    "weight",
    ascending=False
)

importance_path = os.path.join(
    OUTPUT_DIR,
    "feature_importance.csv"
)

importance_df.to_csv(
    importance_path,
    index=False
)


# ============================================================
# Figures
# ============================================================

print("\n[16/16] Writing figures...")

# ------------------------------------------------------------
# Confusion Matrix
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(6, 6)
)

im = ax.imshow(cm)

ax.set_xticks([0, 1])
ax.set_yticks([0, 1])

ax.set_xticklabels(["A", "B"])
ax.set_yticklabels(["A", "B"])

for i in range(2):

    for j in range(2):

        ax.text(
            j,
            i,
            cm[i, j],
            ha="center",
            va="center"
        )

ax.set_title(
    "Currier Confusion Matrix"
)

fig.colorbar(im)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "confusion_matrix.png"
    ),
    dpi=300
)

plt.close()

# ------------------------------------------------------------
# ROC Curve
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(6, 6)
)

ax.plot(
    fpr,
    tpr,
    linewidth=3,
    label=f"AUC={auc:.3f}"
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
    "Currier ROC Curve"
)

ax.legend()

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "roc_curve.png"
    ),
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
    perm_aucs,
    bins=40
)

ax.axvline(
    auc,
    color="red",
    linewidth=3
)

ax.text(
    0.98,
    0.98,
    f"AUC={auc:.3f}\n"
    f"z={perm_z:.2f}\n"
    f"p={perm_p:.4f}",
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white")
)

ax.set_title(
    "Permutation Null AUC"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "permutation_null.png"
    ),
    dpi=300
)

plt.close()

# ------------------------------------------------------------
# Bootstrap AUC
# ------------------------------------------------------------

fig, ax = plt.subplots(
    figsize=(8, 5)
)

ax.hist(
    boot_aucs,
    bins=40
)

ax.axvline(
    auc,
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
    "Bootstrap AUC"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "bootstrap_auc.png"
    ),
    dpi=300
)

plt.close()

# ------------------------------------------------------------
# Calibration Curve
# ------------------------------------------------------------

prob_true, prob_pred = calibration_curve(
    y_binary,
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
    "Predicted Probability"
)

ax.set_ylabel(
    "Observed Frequency"
)

ax.set_title(
    "Calibration Curve"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "calibration_curve.png"
    ),
    dpi=300
)

plt.close()

# ------------------------------------------------------------
# Top Features
# ------------------------------------------------------------

top_df = pd.concat([

    importance_df.head(15),

    importance_df.tail(15)

])

fig, ax = plt.subplots(
    figsize=(10, 8)
)

ax.barh(
    top_df["cell_id"],
    top_df["weight"]
)

ax.set_title(
    "Top Currier Predictive Features"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        FIG_DIR,
        "top_features.png"
    ),
    dpi=300
)

plt.close()


# ============================================================
# Summary
# ============================================================

finding_level = "NULL"

if auc > 0.80:
    finding_level = "LOCKED"

elif auc > 0.65:
    finding_level = "STRONG"

elif auc > 0.55:
    finding_level = "CANDIDATE"

summary = {

    "test_name":
        "Currier External Validation",

    "version":
        "v1",

    "finding_level":
        finding_level,

    "n_folios":
        int(len(merged)),

    "currier_counts":
        class_counts.to_dict(),

    "metrics": {

        "auc":
            float(auc),

        "accuracy":
            float(accuracy),

        "balanced_accuracy":
            float(balanced_acc)
    },

    "bootstrap_auc_ci_95": {

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

    "currier_provenance_verified":
        True,

    "unknown_currier_labels_excluded":
        True,

    "mixed_currier_labels_excluded":
        True,

    "random_seed":
        SEED,

    "input_sha256": {

        INPUT_MATRIX:
            sha256_file(INPUT_MATRIX),

        INPUT_CURRIER:
            sha256_file(INPUT_CURRIER)
    },

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

artifact_paths = [

    matrix_path,
    fold_path,
    pred_path,
    perm_path,
    boot_path,
    cm_path,
    report_path,
    roc_path,
    importance_path,
    summary_path
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
    f"AUC: {auc:.4f}"
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

print(
    f"Finding level: "
    f"{finding_level}"
)

print("\nOutput directory:")
print(f"  {OUTPUT_DIR}")

print("\n====================================================\n")