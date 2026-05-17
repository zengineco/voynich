#!/usr/bin/env python3
"""
Register grammar: deep view.
Reads /home/claude/register_grid_specific.csv and:
  1. Builds section fingerprint vectors (suffix-axis distribution per root)
  2. Computes inter-section cosine similarity matrix
  3. Identifies CANONICAL register-cells (the 30-40 productive cells)
  4. Finds register-axis collapse / divergence per section
  5. Produces predictive distribution: P(suffix-axis | section, root)
"""
import csv
import math
from collections import defaultdict, Counter

SPECIFIC = "/home/claude/register_grid_specific.csv"
GRADE = "/home/claude/register_grid_grade.csv"

# Load specific suffix data
rows = []
with open(SPECIFIC) as f:
    for r in csv.DictReader(f):
        r["count"] = int(r["count"])
        rows.append(r)

# Sections in display order matching Canon-book mapping
SECTION_ORDER = ["balneo", "stars", "cosmo/zodiac", "rosettes",
                 "herbal-A", "pharm-herbal"]
BASES = ["ch", "sh", "qok", "qot", "ok", "ot"]
GRADES = ["bare", "e", "o", "eo"]
AXES = ["e_grade", "o_grade", "aspect", "paradigm", "clitic", "bare_suffix", "other"]

# ---------- Cell aggregation ----------
# cell[(section, base, grade, axis)] = count
cell = defaultdict(int)
# section_total: tokens per section (across all bases parsed)
section_base_total = defaultdict(int)
for r in rows:
    cell[(r["section"], r["base"], r["grade"], r["axis"])] += r["count"]
    section_base_total[(r["section"], r["base"])] += r["count"]

# Productive cells: count >= 10 in at least one section
productive = set()
for (sec, base, grade, axis), c in cell.items():
    if c >= 10:
        productive.add((base, grade, axis))

print(f"PRODUCTIVE CELLS (count>=10 in some section): {len(productive)}")
print(f"Total possible cells (6 bases × 4 grades × 7 axes): {6*4*7}")

# ---------- Section fingerprint vector ----------
# Vector dimension = productive cells; value = pct of section's parsed tokens
def section_vector(section):
    vec = {}
    sec_total = sum(c for (s, b, g, a), c in cell.items() if s == section)
    if sec_total == 0:
        return None, 0
    for (base, grade, axis) in productive:
        c = cell.get((section, base, grade, axis), 0)
        vec[(base, grade, axis)] = c / sec_total
    return vec, sec_total

vectors = {}
totals = {}
for s in SECTION_ORDER:
    v, t = section_vector(s)
    vectors[s] = v
    totals[s] = t

# ---------- Cosine similarity matrix ----------
def cosine(v1, v2):
    keys = set(v1) | set(v2)
    dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in keys)
    n1 = math.sqrt(sum(x*x for x in v1.values()))
    n2 = math.sqrt(sum(x*x for x in v2.values()))
    return dot / (n1*n2) if n1*n2 else 0

print(f"\n{'='*80}")
print("SECTION COSINE SIMILARITY (full register fingerprint)")
print(f"{'='*80}")
print(f"{'':18s} " + " ".join(f"{s[:9]:>9s}" for s in SECTION_ORDER))
for s1 in SECTION_ORDER:
    row = [f"{s1:18s}"]
    for s2 in SECTION_ORDER:
        c = cosine(vectors[s1], vectors[s2])
        row.append(f"{c:>9.3f}")
    print(" ".join(row))

# ---------- Top differential cells per section ----------
# Z-score per cell against mean across sections
mean_by_cell = {}
for c_key in productive:
    vals = [vectors[s].get(c_key, 0) for s in SECTION_ORDER]
    mean_by_cell[c_key] = (sum(vals)/len(vals), vals)

print(f"\n{'='*80}")
print("TOP 5 OVER-REPRESENTED CELLS PER SECTION (relative to corpus mean)")
print(f"{'='*80}")
for s in SECTION_ORDER:
    # for each productive cell, deviation from mean
    deltas = []
    for c_key, (mn, vals) in mean_by_cell.items():
        v = vectors[s].get(c_key, 0)
        if mn > 0:
            ratio = v/mn
            deltas.append((c_key, v, mn, ratio))
    deltas.sort(key=lambda x: -x[3])
    print(f"\n{s} (n={totals[s]}):")
    for (c_key, v, mn, ratio), _ in zip(deltas[:5], range(5)):
        base, grade, axis = c_key
        print(f"  {base:4s} {grade:4s} {axis:14s}  {100*v:5.2f}% (corpus mean {100*mn:5.2f}%) × {ratio:5.2f}")

# ---------- Predictive distribution: P(axis | section, ch-root, grade) ----------
# This is the predictive model: given a section and an "underlying" root choice and grade,
# what's the expected suffix-axis selection?
print(f"\n{'='*80}")
print("P(suffix-axis | section, root, grade) — predictive register grammar")
print(f"For ch and sh (humor roots). Top 3 axes per cell only.")
print(f"{'='*80}")

for base in ["ch", "sh"]:
    print(f"\n┌── BASE: {base} {'─'*60}")
    for grade in GRADES:
        # Header
        print(f"│  grade={grade}")
        print(f"│  {'section':18s} " + " ".join(f"{a[:9]:>9s}" for a in ["e_grade", "o_grade", "aspect", "paradigm", "clitic"]))
        for s in SECTION_ORDER:
            tot = sum(cell.get((s, base, grade, a), 0) for a in AXES)
            if tot < 5:
                continue
            row = [f"│  {s:18s}"]
            for a in ["e_grade", "o_grade", "aspect", "paradigm", "clitic"]:
                c = cell.get((s, base, grade, a), 0)
                pct = 100*c/tot if tot else 0
                row.append(f"{pct:>8.1f}%")
            row.append(f"   n={tot}")
            print(" ".join(row))
    print(f"└{'─'*70}")

# ---------- Most productive specific cells across corpus ----------
print(f"\n{'='*80}")
print("TOP 30 SPECIFIC REGISTER-WORD-FORMS (base + grade + axis + suffix) across corpus")
print(f"{'='*80}")
specific_total = Counter()
for r in rows:
    specific_total[(r["base"], r["grade"], r["axis"], r["specific_suffix"])] += r["count"]
print(f"  {'rank':>4s}  {'base':4s} {'grade':5s} {'axis':14s} {'suffix':10s} {'count':>6s}  reconstructed-form")
for i, ((base, grade, axis, suf), c) in enumerate(specific_total.most_common(30), 1):
    if grade == "bare":
        v = ""
    elif grade == "e":
        v = "e"
    elif grade == "o":
        v = "o"
    elif grade == "eo":
        v = "eo"
    form = base + v + suf
    print(f"  {i:>4d}  {base:4s} {grade:5s} {axis:14s} {suf:10s} {c:>6d}  {form}")
