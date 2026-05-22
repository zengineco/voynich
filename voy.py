import os
import random
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

INPUT_PATH = "/mnt/data/MASTER_TOKEN_MATRIX.xlsx"
OUTPUT_PATH = "/mnt/data/voynich_human_readable_specimens.txt"

TARGET_D_FORMS = {"daiin", "dain", "dair", "dol", "dar"}
COMPOUND_TARGETS = ["dchedy", "dchor", "dalchedy", "daldy", "dchey", "dcheor"]

F57V_LOCI = ["2,@Cc", "3,+Cc", "4,+Cc", "5,+Cc"]

VOWELS = set("aeiouy")


def first_vowel_index(s):
    for idx, ch in enumerate(s):
        if ch in VOWELS:
            return idx
    return -1


def render_line(tokens, mark_positions=None):
    if mark_positions is None:
        mark_positions = {}

    rendered = []
    for idx, tok in enumerate(tokens):
        if idx in mark_positions:
            rendered.append(mark_positions[idx])
        else:
            rendered.append(tok)
    return " ".join(rendered)


def balanced_contexts(line_records, max_lines=3):
    by_section = defaultdict(list)

    for rec in line_records:
        by_section[rec["section"]].append(rec)

    sections = sorted(by_section.keys())

    selected = []
    used = set()

    while len(selected) < max_lines:
        progress = False

        for sec in sections:
            if len(selected) >= max_lines:
                break

            while by_section[sec]:
                rec = by_section[sec].pop(0)
                key = (rec["folio"], rec["locus"])

                if key not in used:
                    selected.append(rec)
                    used.add(key)
                    progress = True
                    break

        if not progress:
            break

    return selected


def write_separator(handle, char="-", width=72):
    handle.write(char * width + "\n")


df = pd.read_excel(INPUT_PATH, sheet_name="tokens_atomic")

for col in ["folio", "section", "locus", "token"]:
    df[col] = df[col].astype(str)

df["line_token_index"] = pd.to_numeric(df["line_token_index"], errors="coerce")
df = df.sort_values(
    ["folio", "locus", "line_token_index"],
    kind="mergesort"
).reset_index(drop=True)

line_groups = {}

for (folio, locus), group in df.groupby(["folio", "locus"], sort=False):
    line_groups[(folio, locus)] = (
        group.sort_values("line_token_index", kind="mergesort")
        .reset_index(drop=True)
    )

token_counts = Counter(df["token"].tolist())

parsed_mask = df["cell_id"].notna()

section_emission_counts = {
    "Section 1": 0,
    "Section 2": 0,
    "Section 3": 0,
    "Section 4": 0,
    "Section 5A": 0,
    "Section 5B": 0,
    "Section 6": 0,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as out:

    # ============================================================
    write_separator(out, "=")
    out.write("SECTION 1 — VOWEL-FLIP MINIMAL PAIRS\n")

    pair_candidates = []

    for token_x, count_x in token_counts.items():
        if count_x < 5:
            continue

        vowel_idx = first_vowel_index(token_x)

        if vowel_idx <= 0:
            continue

        token_y = token_x[:vowel_idx] + "e" + token_x[vowel_idx:]

        if token_y == token_x:
            continue

        count_y = token_counts.get(token_y, 0)

        if count_y < 5:
            continue

        pair_key = tuple(sorted([token_x, token_y]))
        combined = count_x + count_y

        pair_candidates.append((pair_key, combined))

    dedup_pairs = {}
    for pair_key, combined in pair_candidates:
        if pair_key not in dedup_pairs:
            dedup_pairs[pair_key] = combined
        else:
            dedup_pairs[pair_key] = max(dedup_pairs[pair_key], combined)

    ranked_pairs = sorted(
        dedup_pairs.items(),
        key=lambda x: (-x[1], x[0])
    )

    top_pairs = ranked_pairs[:15]

    for (token_a, token_b), _combined in top_pairs:

        write_separator(out)

        count_a = token_counts[token_a]
        count_b = token_counts[token_b]

        out.write(f"PAIR: {token_a} / {token_b}\n")
        out.write(f"COUNTS: {token_a}={count_a}   {token_b}={count_b}\n")

        subset = df[df["token"].isin([token_a, token_b])]

        cross = pd.crosstab(
            subset["section"],
            subset["token"]
        ).fillna(0)

        out.write(cross.to_string())
        out.write("\n")

        for target in [token_a, token_b]:

            out.write(f"\nTOKEN: {target}\n")

            matching_records = []

            for (folio, locus), group in line_groups.items():
                token_positions = group.index[group["token"] == target].tolist()

                if token_positions:
                    matching_records.append({
                        "folio": folio,
                        "locus": locus,
                        "section": group["section"].iloc[0],
                        "positions": token_positions,
                        "tokens": group["token"].tolist()
                    })

            selected = balanced_contexts(matching_records, max_lines=3)

            for rec in selected:
                mark_positions = {
                    pos: f"<<{rec['tokens'][pos]}>>"
                    for pos in rec["positions"]
                }

                line_text = render_line(rec["tokens"], mark_positions)

                out.write(
                    f"[{rec['folio']} {rec['locus']}] "
                    f"{line_text}\n"
                )

        section_emission_counts["Section 1"] += 1

    # ============================================================
    write_separator(out, "=")
    out.write("SECTION 2 — D-FORM CLUSTERS IN CONTEXT\n")

    qualifying_by_section = defaultdict(list)

    for (folio, locus), group in line_groups.items():
        tokens = group["token"].tolist()

        present = set(tok for tok in tokens if tok in TARGET_D_FORMS)

        if len(present) >= 2:
            qualifying_by_section[group["section"].iloc[0]].append({
                "folio": folio,
                "locus": locus,
                "tokens": tokens
            })

    selected_lines = []

    sections = sorted(qualifying_by_section.keys())

    per_section_limit = 5
    section_taken = Counter()

    progress = True

    while progress and len(selected_lines) < 25:
        progress = False

        for sec in sections:
            if len(selected_lines) >= 25:
                break

            if section_taken[sec] >= per_section_limit:
                continue

            if qualifying_by_section[sec]:
                rec = qualifying_by_section[sec].pop(0)
                selected_lines.append((sec, rec))
                section_taken[sec] += 1
                progress = True

    for sec, rec in selected_lines:
        mark_positions = {}

        for idx, tok in enumerate(rec["tokens"]):
            if tok in TARGET_D_FORMS:
                mark_positions[idx] = f"<<{tok}>>"

        line_text = render_line(rec["tokens"], mark_positions)

        out.write(
            f"[{sec}] "
            f"[{rec['folio']} {rec['locus']}] "
            f"{line_text}\n"
        )

    section_emission_counts["Section 2"] = len(selected_lines)

    # ============================================================
    write_separator(out, "=")
    out.write("SECTION 3 — COMPOUND D-FORMS\n")

    for target in COMPOUND_TARGETS:

        write_separator(out)

        global_count = token_counts.get(target, 0)

        out.write(
            f"COMPOUND: {target}   GLOBAL COUNT: {global_count}\n"
        )

        if global_count == 0:
            continue

        found = 0

        for (folio, locus), group in line_groups.items():
            token_positions = group.index[group["token"] == target].tolist()

            if not token_positions:
                continue

            tokens = group["token"].tolist()

            mark_positions = {
                pos: f"<<{tokens[pos]}>>"
                for pos in token_positions
            }

            line_text = render_line(tokens, mark_positions)

            out.write(
                f"[{group['section'].iloc[0]}] "
                f"[{folio} {locus}] "
                f"{line_text}\n"
            )

            found += 1

            if found >= 5:
                break

        section_emission_counts["Section 3"] += found

    # ============================================================
    write_separator(out, "=")
    out.write("SECTION 4 — F57V ALPHABET PAGE VS COSMO/ZODIAC PROSE\n")

    for locus in F57V_LOCI:

        write_separator(out)

        key = ("f57v", locus)

        if key not in line_groups:
            out.write(f"f57v {locus}   LENGTH: 0 tokens   PARSED: 0\n")
            continue

        group = line_groups[key]

        length_n = len(group)
        parsed_n = group["cell_id"].notna().sum()

        out.write(
            f"f57v {locus}   LENGTH: {length_n} tokens   PARSED: {parsed_n}\n"
        )

        for tok in group["token"].tolist():
            out.write(f"{tok}\n")

        section_emission_counts["Section 4"] += 1

    write_separator(out)

    out.write("RANDOM COSMO/ZODIAC LINES\n")

    cosmo_candidates = []

    for (folio, locus), group in line_groups.items():
        if (
            group["section"].iloc[0] == "cosmo/zodiac"
            and folio != "f57v"
            and len(group) >= 5
        ):
            cosmo_candidates.append((folio, locus))

    if len(cosmo_candidates) >= 3:
        chosen_indices = np.random.choice(
            len(cosmo_candidates),
            size=3,
            replace=False
        )
        chosen_lines = [cosmo_candidates[i] for i in chosen_indices]
    else:
        chosen_lines = cosmo_candidates

    for folio, locus in chosen_lines:
        group = line_groups[(folio, locus)]

        out.write(
            f"[{folio} {locus}]   LENGTH: {len(group)}\n"
        )

        for tok in group["token"].tolist():
            out.write(f"{tok}\n")

        write_separator(out)

    # ============================================================
    write_separator(out, "=")
    out.write("SECTION 5 — EO-GRADE CONTEXTS IN PHARM-HERBAL\n")

    pharm_lines = []

    for (folio, locus), group in line_groups.items():
        if group["section"].iloc[0] == "pharm-herbal":
            pharm_lines.append((folio, locus, group))

    # ------------------------------------------------------------
    out.write("SUB-SECTION 5A — LINES WITH TWO OR MORE EO-GRADE TOKENS\n")

    qualifying_5a = []

    for folio, locus, group in pharm_lines:

        eo_positions = group.index[group["grade"] == "eo"].tolist()

        if len(eo_positions) >= 2:
            qualifying_5a.append((folio, locus))

    if len(qualifying_5a) > 15:
        chosen_idx = np.random.choice(
            len(qualifying_5a),
            size=15,
            replace=False
        )
        chosen_5a = [qualifying_5a[i] for i in chosen_idx]
    else:
        chosen_5a = qualifying_5a

    for folio, locus in chosen_5a:
        group = line_groups[(folio, locus)]

        tokens = group["token"].tolist()

        eo_positions = group.index[group["grade"] == "eo"].tolist()

        mark_positions = {
            pos: f"<<{tokens[pos]}>>"
            for pos in eo_positions
        }

        line_text = render_line(tokens, mark_positions)

        out.write(f"[{folio} {locus}] {line_text}\n")

    section_emission_counts["Section 5A"] = len(chosen_5a)

    # ------------------------------------------------------------
    out.write("\n")
    out.write("SUB-SECTION 5B — LINES WITH ZERO EO-GRADE TOKENS AND LENGTH <= 4\n")

    qualifying_5b = []

    for folio, locus, group in pharm_lines:

        eo_count = (group["grade"] == "eo").sum()

        if eo_count == 0 and len(group) <= 4:
            qualifying_5b.append((folio, locus))

    chosen_5b = qualifying_5b[:15]

    for folio, locus in chosen_5b:
        group = line_groups[(folio, locus)]

        line_text = render_line(group["token"].tolist())

        out.write(f"[{folio} {locus}] {line_text}\n")

    section_emission_counts["Section 5B"] = len(chosen_5b)

    # ============================================================
    write_separator(out, "=")
    out.write("SECTION 6 — FORBIDDEN TRANSITION NEAR-MISSES\n")

    near_misses = []

    for (folio, locus), group in line_groups.items():

        cell_ids = group["cell_id"].tolist()
        tokens = group["token"].tolist()

        ai_positions = [
            idx for idx, cid in enumerate(cell_ids)
            if cid == "ch|e|e_grade"
        ]

        bi_positions = [
            idx for idx, cid in enumerate(cell_ids)
            if cid == "sh|e|aspect"
        ]

        if not ai_positions or not bi_positions:
            continue

        best_gap = None
        best_pair = None

        for ai in ai_positions:
            for bi in bi_positions:
                if bi > ai:
                    gap = bi - ai - 1

                    if best_gap is None or gap < best_gap:
                        best_gap = gap
                        best_pair = (ai, bi)

        if best_pair is None:
            continue

        near_misses.append({
            "folio": folio,
            "locus": locus,
            "gap": best_gap,
            "pair": best_pair,
            "tokens": tokens
        })

    near_misses = sorted(
        near_misses,
        key=lambda x: (x["gap"], x["folio"], x["locus"])
    )

    emitted = near_misses[:20]

    for rec in emitted:

        ai, bi = rec["pair"]

        mark_positions = {
            ai: f"<<a:{rec['tokens'][ai]}>>",
            bi: f"<<b:{rec['tokens'][bi]}>>"
        }

        line_text = render_line(rec["tokens"], mark_positions)

        out.write(
            f"[{rec['folio']} {rec['locus']}] "
            f"GAP={rec['gap']}   "
            f"{line_text}\n"
        )

    section_emission_counts["Section 6"] = len(emitted)

print(f"TOTAL TOKENS LOADED: {len(df)}")
print(f"TOTAL LINES: {len(line_groups)}")
print(f"TOTAL PARSED TOKENS: {parsed_mask.sum()}")

for section_name, count in section_emission_counts.items():
    print(f"{section_name} SPECIMENS: {count}")

byte_size = os.path.getsize(OUTPUT_PATH)

print(f"OUTPUT FILE: {OUTPUT_PATH}")
print(f"OUTPUT FILE SIZE: {byte_size} bytes")