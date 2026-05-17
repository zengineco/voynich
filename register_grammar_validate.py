#!/usr/bin/env python3
"""
Predictive validation of the register grammar.

For each folio: 
  - compute its observed register fingerprint
  - score cosine similarity to (a) its own section's mean, (b) every other section's mean
  - if its own section is the highest cosine, the prediction "holds"
This is a leave-one-out check that the section-register grammar is REAL.
"""
import re, csv, math
from collections import defaultdict, Counter

# Reuse tokenization from build_register_grammar.py
import sys
sys.path.insert(0, "/home/claude")
from build_register_grammar import (
    tokens_by_folio_section, classify_suffix, parse_token, best_parse,
    HUMOR_BASES, PROCESS_BASES,
)

GRADES = ["bare", "e", "o", "eo"]
AXES = ["e_grade", "o_grade", "aspect", "paradigm", "clitic", "bare_suffix", "other"]

# Step 1: classify each folio's tokens
folio_cells = defaultdict(Counter)  # folio -> Counter of (base,grade,axis) -> count
folio_section_map = {}
for (folio, section), toks in tokens_by_folio_section.items():
    folio_section_map[folio] = section
    for tok in toks:
        parses = parse_token(tok)
        bp = best_parse(parses)
        if bp is None: continue
        axis, _ = classify_suffix(bp["suffix"])
        folio_cells[folio][(bp["base"], bp["grade"], axis)] += 1

# Step 2: build section profile = mean cell distribution across that section's folios
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

# Step 3: section centroid = sum of all folios' cells in that section
section_profile = {}
for section, folios in section_to_folios.items():
    agg = Counter()
    for f in folios:
        agg.update(folio_cells[f])
    section_profile[section] = vec_to_pct(agg)

# Step 4: for each folio, leave-one-out classify
results = []
section_correct = Counter()
section_total = Counter()
for folio, section in folio_section_map.items():
    fv = vec_to_pct(folio_cells[folio])
    if fv is None: continue
    # leave folio out of its section
    sec_minus = Counter()
    for f2 in section_to_folios[section]:
        if f2 == folio: continue
        sec_minus.update(folio_cells[f2])
    sec_minus_vec = vec_to_pct(sec_minus)
    if sec_minus_vec is None: continue
    # Compute cosine to each section (with own section using leave-one-out)
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
    results.append({
        "folio": folio,
        "actual": section,
        "predicted": predicted,
        "match": predicted == section,
        "own_sim": sims[section],
        "best_other": max((s for s in sims if s != section), key=sims.get),
        "best_other_sim": max(sims[s] for s in sims if s != section),
    })
    section_total[section] += 1
    if predicted == section:
        section_correct[section] += 1

# Step 5: report
print(f"\n{'='*70}")
print("LEAVE-ONE-OUT REGISTER CLASSIFICATION ACCURACY")
print(f"{'='*70}")
print(f"{'section':18s} {'correct':>8s} {'total':>8s} {'accuracy':>10s}  {'random':>8s}")
n_sections = len(section_total)
for s in sorted(section_total):
    acc = 100*section_correct[s]/section_total[s] if section_total[s] else 0
    print(f"{s:18s} {section_correct[s]:>8d} {section_total[s]:>8d} {acc:>9.1f}%  {100/n_sections:>7.1f}%")

total_correct = sum(section_correct.values())
total_n = sum(section_total.values())
print(f"\nOVERALL: {total_correct}/{total_n} = {100*total_correct/total_n:.1f}% (random baseline = {100/n_sections:.1f}%)")

# Step 6: show misclassifications
print(f"\n{'='*70}")
print("MISCLASSIFICATIONS (folios whose register doesn't match their section)")
print(f"{'='*70}")
mis = [r for r in results if not r["match"]]
mis.sort(key=lambda r: -(r["own_sim"] - r["best_other_sim"]))  # by margin (most surprising last)
# Show only those where margin > 0.05 to filter noise
mis_clean = [r for r in mis if (r["best_other_sim"] - r["own_sim"]) > 0.05]
for r in mis_clean[:30]:
    margin = r["best_other_sim"] - r["own_sim"]
    print(f"  {r['folio']:8s} actual={r['actual']:14s} → predicted={r['predicted']:14s} (margin {margin:+.3f})")

print(f"\nClean misclassifications (margin > 0.05): {len(mis_clean)} of {total_n}")
