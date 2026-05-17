#!/usr/bin/env python3
"""
cth- signature matching — finer-grained framing.

Instead of "dominant form", build per-folio signatures and find folios that
share DISTINCTIVE cth- patterns. Three approaches:

A) Rare-form sharing: which folio pairs both contain a sparse cth- form?
   e.g., both have cthey (which only 8 folios are dominated by)
   e.g., both have an extended form that appears <5 times in herbal-A total

B) Presence/absence signature: encode each folio as a binary vector over
   {cthor, cthy, cthol, cthey} and find folios with identical signatures
   that ALSO have the strongest signal (highest cth- total).

C) Pure-form folios: folios where ONE cth- form makes up most/all of the
   cth- output, with no cthor/cthol noise — these are the "clean" cases.

Output: a ranked list of folio pairs/clusters to cross-reference visually.
"""
import re
import csv
from collections import defaultdict, Counter
from itertools import combinations

# Load tokens per folio (re-parse ZL3b-n)
def tokenize_line(line):
    if not line.startswith('<'):
        return None, []
    m = re.match(r'<(f\d+[rv]\d*)\.', line)
    if not m:
        return None, []
    folio = m.group(1)
    text_match = re.search(r'>\s*(.+?)(?:\s*<|$)', line)
    if not text_match:
        return folio, []
    text = text_match.group(1)
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[([^:\]]+):[^\]]+\]', r'\1', text)
    tokens = re.split(r'[.,]', text)
    cleaned = []
    for t in tokens:
        t = t.strip()
        if not t or '?' in t or '!' in t or t.startswith('-'):
            continue
        cleaned.append(t)
    return folio, cleaned

# Section assignments
folio_section = {}
with open('folio_profile.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        folio_section[row['folio']] = row['section']

herbal_a = {f for f, s in folio_section.items() if s == 'herbal-A'}

# Collect all tokens per herbal-A folio
folio_tokens = defaultdict(list)
with open('ZL3b-n', encoding='latin-1') as f:
    for line in f:
        folio, tokens = tokenize_line(line.rstrip())
        if folio and folio in herbal_a:
            folio_tokens[folio].extend(tokens)

# Collect ALL cth-containing tokens per folio
folio_cth_tokens = defaultdict(Counter)  # folio -> Counter of full tokens
for folio, toks in folio_tokens.items():
    for t in toks:
        if 'cth' in t:
            folio_cth_tokens[folio][t] += 1

# Global cth- token frequency across herbal-A
global_cth = Counter()
for folio, c in folio_cth_tokens.items():
    global_cth.update(c)

print("=" * 70)
print("ALL distinct cth- tokens in herbal-A, ranked by frequency")
print("=" * 70)
print(f"Total distinct cth- types: {len(global_cth)}")
print(f"Total cth- tokens: {sum(global_cth.values())}")
print()
print("Top 30 cth- tokens:")
for tok, n in global_cth.most_common(30):
    print(f"  {tok:<15} {n}")
print()

# Sparse cth- tokens (appear in herbal-A but rare: 2-5 occurrences)
print("=" * 70)
print("SPARSE cth- tokens (2-5 occurrences in herbal-A) — high-signal markers")
print("=" * 70)
sparse_tokens = {tok: n for tok, n in global_cth.items() if 2 <= n <= 5}
print(f"Count of sparse types: {len(sparse_tokens)}")
print()

# For each sparse token, list which folios it appears on
sparse_folio_map = defaultdict(list)
for folio, c in folio_cth_tokens.items():
    for tok, n in c.items():
        if tok in sparse_tokens:
            sparse_folio_map[tok].append((folio, n))

print("Sparse cth- tokens that appear on MULTIPLE folios (cross-ref candidates):")
print(f"{'token':<15} {'total':>5}  folios")
multi_folio_sparse = []
for tok in sorted(sparse_tokens, key=lambda t: -sparse_tokens[t]):
    folios_list = sparse_folio_map[tok]
    if len(folios_list) >= 2:
        folio_str = ", ".join(f"{f}({n})" for f, n in folios_list)
        print(f"  {tok:<15} {sparse_tokens[tok]:>5}  {folio_str}")
        multi_folio_sparse.append((tok, folios_list))
print()

# Approach A: highest-signal sparse-form sharing pairs
print("=" * 70)
print("APPROACH A — Folio pairs that BOTH contain the same sparse cth- form")
print("(prioritize: rarer form = stronger signal)")
print("=" * 70)
pair_evidence = defaultdict(list)  # (f1, f2) -> list of (token, n1, n2)
for tok, folios_list in multi_folio_sparse:
    folios_sorted = sorted(folios_list)
    for (f1, n1), (f2, n2) in combinations(folios_sorted, 2):
        key = tuple(sorted([f1, f2]))
        pair_evidence[key].append((tok, n1, n2, sparse_tokens[tok]))

# Rank pairs by total "rarity weight" of shared tokens (1/freq)
def pair_score(evidence_list):
    return sum(1.0 / e[3] for e in evidence_list)

ranked_pairs = sorted(pair_evidence.items(), key=lambda kv: -pair_score(kv[1]))
print(f"Total qualifying pairs: {len(ranked_pairs)}")
print()
print("Top 20 pairs by rarity-weighted shared sparse cth- forms:")
print(f"{'folio-1':<8} {'folio-2':<8} {'score':>6}  shared sparse cth- tokens")
for (f1, f2), ev in ranked_pairs[:20]:
    ev_str = ", ".join(f"{e[0]}[{e[1]},{e[2]}|tot{e[3]}]" for e in ev[:4])
    print(f"  {f1:<8} {f2:<8} {pair_score(ev):>6.3f}  {ev_str}")
print()

# Approach B: presence/absence signature on the four base forms
print("=" * 70)
print("APPROACH B — Folios with rich, distinctive base-form profiles")
print("=" * 70)
base_forms = ['cthor', 'cthy', 'cthol', 'cthey']
folio_sig = {}
for folio in herbal_a:
    c = folio_cth_tokens.get(folio, Counter())
    sig = tuple(c.get(bf, 0) > 0 for bf in base_forms)
    total = sum(c.get(bf, 0) for bf in base_forms)
    folio_sig[folio] = (sig, total)

# Group folios by their presence/absence signature
sig_groups = defaultdict(list)
for folio, (sig, total) in folio_sig.items():
    if total >= 2:  # filter folios with at least 2 base-form occurrences
        sig_groups[sig].append((folio, total))

print("Folios grouped by which base cth- forms they contain (>=2 base tokens):")
print(f"{'cthor':>5} {'cthy':>5} {'cthol':>5} {'cthey':>5}  {'count':>5}  folios")
for sig in sorted(sig_groups.keys(), key=lambda s: -sum(s)):
    folios_in_sig = sig_groups[sig]
    folios_in_sig.sort(key=lambda x: -x[1])
    folios_str = ", ".join(f"{f}({n})" for f, n in folios_in_sig[:6])
    if len(folios_in_sig) > 6:
        folios_str += f", +{len(folios_in_sig)-6} more"
    sig_str = "  ".join(f"  {'*' if s else '.':>3}" for s in sig)
    print(f"{sig_str}  {len(folios_in_sig):>5}  {folios_str}")
print()

# Approach C: "pure" folios — heavy cth- output dominated by ONE base form, no others
print("=" * 70)
print("APPROACH C — Pure folios (one base form dominant, others absent)")
print("=" * 70)
for bf in base_forms:
    print(f"\nPure {bf} folios (has {bf}, lacks the other 3 base forms, total cth- >= 2):")
    pure = []
    for folio in herbal_a:
        c = folio_cth_tokens.get(folio, Counter())
        own = c.get(bf, 0)
        others = sum(c.get(other, 0) for other in base_forms if other != bf)
        if own >= 2 and others == 0:
            pure.append((folio, own))
    pure.sort(key=lambda x: -x[1])
    for f, n in pure[:10]:
        # also list all cth tokens on this folio
        c = folio_cth_tokens[f]
        all_str = ", ".join(f"{t}({k})" for t, k in c.most_common())
        print(f"  {f} ({bf}={n}) — all cth: {all_str}")
print()

# Save the cross-reference candidates
with open('cth_cross_ref_candidates.csv', 'w', newline='') as fout:
    writer = csv.writer(fout)
    writer.writerow(['rank', 'folio_1', 'folio_2', 'score', 'shared_sparse_tokens'])
    for i, ((f1, f2), ev) in enumerate(ranked_pairs[:30], 1):
        ev_str = "; ".join(f"{e[0]} (f1:{e[1]}, f2:{e[2]}, tot_in_herbalA:{e[3]})" for e in ev)
        writer.writerow([i, f1, f2, f"{pair_score(ev):.3f}", ev_str])

print("Wrote cth_cross_ref_candidates.csv (top 30 pairs for visual cross-reference)")
