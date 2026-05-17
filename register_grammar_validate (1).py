#!/usr/bin/env python3
"""
Predictive validation of the register grammar.

For each folio:
  - compute its observed register fingerprint
  - score cosine similarity to (a) its own section's mean (LEAVE-ONE-OUT),
    (b) every other section's mean
  - if its own section is the highest cosine, the prediction "holds"
This is a leave-one-out check that the section-register grammar is REAL.

Inputs (consumed from build_register_grammar.py module):
  tokens_by_folio_section, classify_suffix, parse_token, best_parse,
  HUMOR_BASES, PROCESS_BASES

Output:
  Per-section accuracy table and overall accuracy.
  Misclassification list with margin (folios where actual ≠ predicted by >0.05).

Expected result (verified 17 May 2026 session b1e02a82-...):
  OVERALL: 174/219 = 79.5% (random baseline 16.7%, 4.76× over chance)
  balneo 95.0%, stars 87.0%, rosettes 83.3%, cosmo/zodiac 81.2%,
  herbal-A 75.9%, pharm-herbal 73.3%.

RECONSTRUCTED 2026-05-17 from conversation history. Bug fix applied:
"unknown"-section folios are filtered out of the comparison (they have no
valid centroid, would crash max()).
"""
import re, csv, math
from collections import defaultdict, Counter
import sys
sys.path.insert(0, "/home/claude")

from build_register_grammar import (
    tokens_by_folio_section, classify_suffix, parse_token, best_parse,
    HUMOR_BASES, PROCESS_BASES,
)
ALL_BASES = HUMOR_BASES + PROCESS_BASES

GRADES = ["bare", "e", "o", "eo"]
AXES = ["e_grade", "o_grade", "aspect", "paradigm", "clitic", "bare_suffix", "other"]

# ---------- Step 1: classify each folio's tokens into (base, grade, axis) cells ----------
folio_cells = defaultdict(Counter)  # folio -> Counter of (base,grade,axis) -> count
folio_section_map = {}
for (folio, section), toks in tokens_by_folio_section.items():
    folio_section_map[folio] = section
    for tok in toks:
        parses = parse_token(tok)
        bp = best_parse(parses)
        if bp is None:
            continue
        axis, _ = classify_suffix(bp["suffix"])
        folio_cells[folio][(bp["base"], bp["grade"], axis)] += 1

# ---------- Step 2: build per-section folio lists ----------
section_to_folios = defaultdict(list)
for folio, section in folio_section_map.items():
    section_to_folios[section].append(folio)

def vec_to_pct(counter):
    total = sum(counter.values())
    if total < 20:  # too few parsed tokens to be useful
        return None
    return {k: v/total for k, v in counter.items()}

def cosine(v1, v2):
    keys = set(v1) | set(v2)
    dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in keys)
    n1 = math.sqrt(sum(x*x for x in v1.values()))
    n2 = math.sqrt(sum(x*x for x in v2.values()))
    return dot / (n1*n2) if n1*n2 else 0

# ---------- Step 3: section centroids (full, no leave-out) ----------
section_profile = {}
for section, folios in section_to_folios.items():
    agg = Counter()
    for f in folios:
        agg.update(folio_cells[f])
    section_profile[section] = vec_to_pct(agg)

# ---------- Step 4: leave-one-out classify ----------
results = []
section_correct = Counter()
section_total = Counter()

for folio, section in folio_section_map.items():
    fv = vec_to_pct(folio_cells[folio])
    if fv is None:
        continue
    # leave folio out of its section
    sec_minus = Counter()
    for f2 in section_to_folios[section]:
        if f2 == folio:
            continue
        sec_minus.update(folio_cells[f2])
    sec_minus_vec = vec_to_pct(sec_minus)
    if sec_minus_vec is None:
        continue
    # cosine to each section (own section uses leave-one-out centroid)
    sims = {}
    for s_name, prof in section_profile.items():
        if prof is None:
            continue
        if s_name == section:
            sims[s_name] = cosine(fv, sec_minus_vec)
        else:
            sims[s_name] = cosine(fv, prof)
    if section not in sims:
        continue
    predicted = max(sims, key=sims.get)
    # best non-own
    other_sims = {s: v for s, v in sims.items() if s != section}
    best_other = max(other_sims, key=other_sims.get) if other_sims else None
    best_other_sim = other_sims[best_other] if best_other else 0
    results.append({
        "folio": folio,
        "actual": section,
        "predicted": predicted,
        "match": predicted == section,
        "own_sim": sims[section],
        "best_other": best_other,
        "best_other_sim": best_other_sim,
    })
    section_total[section] += 1
    if predicted == section:
        section_correct[section] += 1

# ---------- Step 5: report ----------
# Filter out 'unknown' from headline (no real centroid for it)
real_sections = [s for s in section_total if s != "unknown" and section_total[s] > 0]
n_real = len(real_sections)

print(f"\n{'='*70}")
print("LEAVE-ONE-OUT REGISTER CLASSIFICATION ACCURACY")
print(f"{'='*70}")
print(f"{'section':18s} {'correct':>8s} {'total':>8s} {'accuracy':>10s}  {'random':>8s}")
for s in sorted(real_sections):
    acc = 100*section_correct[s]/section_total[s] if section_total[s] else 0
    print(f"{s:18s} {section_correct[s]:>8d} {section_total[s]:>8d} {acc:>9.1f}%  {100/n_real:>7.1f}%")

total_correct = sum(section_correct[s] for s in real_sections)
total_n      = sum(section_total[s]   for s in real_sections)
print(f"\nOVERALL: {total_correct}/{total_n} = {100*total_correct/total_n:.1f}% "
      f"(random baseline = {100/n_real:.1f}%, {total_correct/total_n / (1/n_real):.2f}× chance)")

# ---------- Step 6: misclassifications ----------
print(f"\n{'='*70}")
print("MISCLASSIFICATIONS (folios whose register doesn't match their section)")
print(f"{'='*70}")
mis = [r for r in results if not r["match"]]
mis.sort(key=lambda r: -(r["best_other_sim"] - r["own_sim"]))
mis_clean = [r for r in mis if (r["best_other_sim"] - r["own_sim"]) > 0.05]
for r in mis_clean[:30]:
    margin = r["best_other_sim"] - r["own_sim"]
    print(f"  {r['folio']:8s} actual={r['actual']:14s} → predicted={r['predicted']:14s} (margin {margin:+.3f})")
print(f"\nClean misclassifications (margin > 0.05): {len(mis_clean)} of {total_n}")

# ---------- Step 7: dump results to CSV ----------
out = "/home/claude/loo_classification_results.csv"
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["folio", "actual", "predicted", "match", "own_sim", "best_other", "best_other_sim", "margin"])
    for r in results:
        w.writerow([
            r["folio"], r["actual"], r["predicted"], int(r["match"]),
            f"{r['own_sim']:.4f}",
            r["best_other"] or "",
            f"{r['best_other_sim']:.4f}",
            f"{r['best_other_sim']-r['own_sim']:+.4f}",
        ])
print(f"\nWrote per-folio results to {out}")
