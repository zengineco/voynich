#!/usr/bin/env python3
"""
VOYNICH MANUSCRIPT RESEARCH PROGRAM
TASK A v1b: SPEC-COMPLIANT HELD-OUT CLASSIFICATION

Author: OpenAI GPT-5.5
Seed: 42

============================================================
PURPOSE
============================================================

Strict replication and stress-test of the locked
79.45% folio classification result under:

1. Leakage-controlled held-out evaluation
2. Spec-compliant 5-fold validation
3. Explicit unknown-class handling
4. Permutation testing
5. Bootstrap confidence intervals

============================================================
DESIGN
============================================================

TRACK A1
--------
All 7 sections retained.
Dynamic fold count determined by smallest class.

Purpose:
- corpus completeness
- descriptive robustness

TRACK A2
--------
Exclude "unknown" section ONLY.

Fixed 5-fold CV.

Purpose:
- strict spec compliance
- direct comparability to prior 79.45% result

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
- cell_id
- parsed

============================================================
FEATURE SPACE
============================================================

- folio × productive-cell count matrix
- FUNC excluded
- no section aggregation
- no feature leakage

============================================================
OUTPUT
============================================================

voynich_taskA_heldout_v1b/

FILES
=====

GENERAL
-------
- feature_vocabulary.csv
- folio_feature_matrix.csv
- checksums.json

TRACK A1
--------
- fold_assignments_full.csv
- heldout_predictions_full.csv
- permutation_null_full.csv
- bootstrap_accuracy_full.csv
- confusion_matrix_full.csv
- classification_report_full.csv
- summary_full.json

TRACK A2
--------
- fold_assignments_5fold.csv
- heldout_predictions_5fold.csv
- permutation_null_5fold.csv
- bootstrap_accuracy_5fold.csv
- confusion_matrix_5fold.csv
- classification_report_5fold.csv
- summary_5fold.json

FIGURES
=======
- confusion_matrix_full.png
- confusion_matrix_5fold.png
- permutation_null_full.png
- permutation_null_5fold.png
- bootstrap_accuracy_full.png
- bootstrap_accuracy_5fold.png
- calibration_curve_full.png
- calibration_curve_5fold.png

============================================================
METHODOLOGICAL RULES
============================================================

- no train/test folio overlap
- scaler fit on training only
- no section aggregation
- deterministic seeds
- explicit parser audit
- fail-fast assertions
- empirical p-values only
- bootstrap CIs explicitly labeled

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
    f1_score
)

from sklearn.calibration import (
    calibration_curve
)

# ============================================================
# Constants
# ============================================================

SEED = 42

DEFAULT_SPLITS = 5

N_PERMUTATIONS = 1000
N_BOOTSTRAPS = 1000

INPUT_MATRIX = "MASTER_TOKEN_MATRIX.xlsx"

OUTPUT_DIR = "voynich_taskA_heldout_v1b"
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
# Evaluation Engine
# ============================================================

def run_evaluation(
    matrix,
    labels,
    folios,
    track_name,
    n_splits,
    exclusion_note
):

    print("\n====================================================")
    print(f"RUNNING {track_name}")
    print("====================================================")

    X = matrix.values
    y = labels.values

    skf = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=SEED
    )

    # ========================================================
    # Fold assignments
    # ========================================================

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
        f"fold_assignments_{track_name}.csv"
    )

    fold_df.to_csv(
        fold_path,
        index=False
    )

    # ========================================================
    # Classification
    # ========================================================

    all_true = []
    all_pred = []
    all_prob = []

    pred_rows = []

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

            pred_rows.append({

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
        pred_rows
    )

    pred_path = os.path.join(
        OUTPUT_DIR,
        f"heldout_predictions_{track_name}.csv"
    )

    pred_df.to_csv(
        pred_path,
        index=False
    )

    # ========================================================
    # Metrics
    # ========================================================

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
        average="macro",
        zero_division=0
    )

    micro_f1 = f1_score(
        all_true,
        all_pred,
        average="micro",
        zero_division=0
    )

    print(
        f"Accuracy: {accuracy:.4f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{balanced_acc:.4f}"
    )

    # ========================================================
    # Confusion matrix
    # ========================================================

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
        f"confusion_matrix_{track_name}.csv"
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
        f"classification_report_{track_name}.csv"
    )

    report_df.to_csv(
        report_path
    )

    # ========================================================
    # Permutation null
    # ========================================================

    print(
        f"\nRunning permutation null "
        f"({track_name})..."
    )

    perm_scores = []

    for sim in range(N_PERMUTATIONS):

        shuffled_y = np.random.permutation(y)

        sim_fold_scores = []

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

            score = accuracy_score(
                y_test,
                pred
            )

            sim_fold_scores.append(score)

        perm_scores.append(
            np.mean(sim_fold_scores)
        )

        if (sim + 1) % 100 == 0:

            print(
                f"  {sim + 1}/{N_PERMUTATIONS}"
            )

    perm_df = pd.DataFrame({
        "accuracy":
            perm_scores
    })

    perm_path = os.path.join(
        OUTPUT_DIR,
        f"permutation_null_{track_name}.csv"
    )

    perm_df.to_csv(
        perm_path,
        index=False
    )

    perm_mean = np.mean(
        perm_scores
    )

    perm_std = np.std(
        perm_scores
    )

    if perm_std <= 0:

        raise RuntimeError(
            "Degenerate permutation null."
        )

    perm_z = (
        accuracy - perm_mean
    ) / perm_std

    perm_p = (
        np.sum(
            np.array(perm_scores)
            >= accuracy
        ) + 1
    ) / (
        N_PERMUTATIONS + 1
    )

    # ========================================================
    # Bootstrap CI
    # ========================================================

    print(
        f"\nRunning bootstrap "
        f"({track_name})..."
    )

    pred_array = np.array(
        all_pred
    )

    true_array = np.array(
        all_true
    )

    boot_scores = []

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
        "accuracy":
            boot_scores
    })

    boot_path = os.path.join(
        OUTPUT_DIR,
        f"bootstrap_accuracy_{track_name}.csv"
    )

    boot_df.to_csv(
        boot_path,
        index=False
    )

    boot_lo, boot_hi = bootstrap_ci(
        boot_scores
    )

    # ========================================================
    # FIGURE: confusion matrix
    # ========================================================

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

    ax.set_yticklabels(
        classes
    )

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
        f"Confusion Matrix ({track_name})"
    )

    fig.colorbar(im)

    plt.tight_layout()

    fig_path = os.path.join(
        FIG_DIR,
        f"confusion_matrix_{track_name}.png"
    )

    plt.savefig(
        fig_path,
        dpi=300
    )

    plt.close()

    # ========================================================
    # FIGURE: permutation null
    # ========================================================

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
        f"Permutation Null ({track_name})"
    )

    plt.tight_layout()

    fig_path_perm = os.path.join(
        FIG_DIR,
        f"permutation_null_{track_name}.png"
    )

    plt.savefig(
        fig_path_perm,
        dpi=300
    )

    plt.close()

    # ========================================================
    # FIGURE: bootstrap
    # ========================================================

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
        f"Bootstrap Accuracy ({track_name})"
    )

    plt.tight_layout()

    fig_path_boot = os.path.join(
        FIG_DIR,
        f"bootstrap_accuracy_{track_name}.png"
    )

    plt.savefig(
        fig_path_boot,
        dpi=300
    )

    plt.close()

    # ========================================================
    # FIGURE: calibration
    # ========================================================

    correct = (
        np.array(all_true)
        ==
        np.array(all_pred)
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
        f"Calibration Curve ({track_name})"
    )

    plt.tight_layout()

    cal_path = os.path.join(
        FIG_DIR,
        f"calibration_curve_{track_name}.png"
    )

    plt.savefig(
        cal_path,
        dpi=300
    )

    plt.close()

    # ========================================================
    # Summary
    # ========================================================

    summary = {

        "track":
            track_name,

        "n_splits":
            n_splits,

        "exclusion_note":
            exclusion_note,

        "accuracy":
            float(accuracy),

        "balanced_accuracy":
            float(balanced_acc),

        "macro_f1":
            float(macro_f1),

        "micro_f1":
            float(micro_f1),

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

        "comparison_to_locked_79_45": {

            "locked_target":
                0.7945,

            "difference":
                float(
                    accuracy - 0.7945
                ),

            "within_5_points":
                (
                    abs(
                        accuracy - 0.7945
                    ) <= 0.05
                )
        },

        "timestamp_utc":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    summary_path = os.path.join(
        OUTPUT_DIR,
        f"summary_{track_name}.json"
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

    return {

        "summary_path":
            summary_path,

        "artifact_paths": [

            fold_path,
            pred_path,
            perm_path,
            boot_path,
            cm_path,
            report_path,

            fig_path,
            fig_path_perm,
            fig_path_boot,
            cal_path
        ]
    }


# ============================================================
# Initialize
# ============================================================

print("\n====================================================")
print("TASK A v1b")
print("SPEC-COMPLIANT HELD-OUT CLASSIFICATION")
print("====================================================\n")


# ============================================================
# Load Data
# ============================================================

print("[1/12] Loading MASTER_TOKEN_MATRIX.xlsx...")

if not os.path.exists(INPUT_MATRIX):

    raise FileNotFoundError(
        f"Missing required file: "
        f"{INPUT_MATRIX}"
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

print("\n[2/12] Detecting columns...")

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

print("Detected:")
print(f"  folio: {folio_col}")
print(f"  section: {section_col}")
print(f"  cell_id: {cell_col}")
print(f"  parsed: {parsed_col}")


# ============================================================
# Audit parsed Column
# ============================================================

print("\n[3/12] Auditing parsed column...")

print(
    df[parsed_col]
    .value_counts(dropna=False)
)


# ============================================================
# Filter Productive Cells
# ============================================================

print("\n[4/12] Filtering productive cells...")

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


# ============================================================
# Parser Self-Test
# ============================================================

print("\n[5/12] Parser self-test...")

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
# Build Feature Matrix
# ============================================================

print("\n[6/12] Building folio × cell matrix...")

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

labels = labels.loc[
    matrix.index
]

folios = matrix.index.values

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
    "cell_id":
        matrix.columns
}).to_csv(
    vocab_path,
    index=False
)

print(
    f"Matrix shape: {matrix.shape}"
)

print(
    f"Sections: "
    f"{sorted(labels.unique())}"
)


# ============================================================
# Track A1
# ============================================================

print("\n[7/12] Preparing TRACK A1...")

section_counts = (
    pd.Series(labels)
    .value_counts()
)

print("\nSection counts:")
print(section_counts)

min_class_size = int(
    section_counts.min()
)

if min_class_size < 2:

    raise RuntimeError(
        "At least one section has <2 folios."
    )

safe_splits = min(
    DEFAULT_SPLITS,
    min_class_size
)

print(
    f"\nUsing {safe_splits} folds "
    f"for full corpus."
)

trackA1 = run_evaluation(

    matrix=matrix,
    labels=labels,
    folios=folios,

    track_name="full",

    n_splits=safe_splits,

    exclusion_note=(
        "No exclusions. "
        "Dynamic folds used because "
        "minimum class size constrains CV."
    )
)


# ============================================================
# Track A2
# ============================================================

print("\n[8/12] Preparing TRACK A2...")

known_mask = (
    labels != "unknown"
)

matrix_known = matrix.loc[
    known_mask
]

labels_known = labels.loc[
    known_mask
]

folios_known = (
    matrix_known.index.values
)

known_counts = (
    pd.Series(labels_known)
    .value_counts()
)

print("\nKnown-section counts:")
print(known_counts)

if known_counts.min() < 5:

    raise RuntimeError(
        "Cannot run strict 5-fold CV: "
        "a known section has <5 folios."
    )

trackA2 = run_evaluation(

    matrix=matrix_known,
    labels=labels_known,
    folios=folios_known,

    track_name="5fold",

    n_splits=5,

    exclusion_note=(
        "Excluded only the 'unknown' section "
        "to satisfy strict 5-fold "
        "stratification requirements."
    )
)


# ============================================================
# Checksums
# ============================================================

print("\n[9/12] Writing checksums...")

artifact_paths = [

    feature_matrix_path,
    vocab_path,

    trackA1["summary_path"],
    trackA2["summary_path"]
]

artifact_paths.extend(
    trackA1["artifact_paths"]
)

artifact_paths.extend(
    trackA2["artifact_paths"]
)

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
# Final Report
# ============================================================

print("\n[10/12] Finalizing...")

master_summary = {

    "test":
        "Task A v1b",

    "tracks": {

        "A1":
            "Full corpus dynamic-fold evaluation",

        "A2":
            "Spec-compliant 5-fold evaluation"
    },

    "random_seed":
        SEED,

    "input_sha256": {

        INPUT_MATRIX:
            sha256_file(INPUT_MATRIX)
    },

    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat()
}

master_summary_path = os.path.join(
    OUTPUT_DIR,
    "master_summary.json"
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

print("\n[11/12] COMPLETE")

print("\n====================================================")
print("TASK A v1b COMPLETE")
print("====================================================")

print(
    "\nOutputs written to:"
)

print(
    f"  {OUTPUT_DIR}"
)

print("\n[12/12] DONE\n")