#!/usr/bin/env python3
"""
cth- botanical anchoring — Test 1, Stage 1
Build per-folio inventory of cth- forms in herbal-A.

Locked cth- paradigm forms: cthor, cthy, cthol, cthey
Plus extended forms with prefixes/suffixes: dcthor, dcthol, cthody, cthedy, etc.

This stage: tabulate raw occurrences of each base cth- form per herbal-A folio
to see if there's enough signal to test partitioning.
"""
import re
import csv
from collections import defaultdict, Counter

# Load section assignments
folio_section = {}
with open('folio_profile.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        folio_section[row['folio']] = row['section']

herbal_a_folios = {f for f, s in folio_section.items() if s == 'herbal-A'}

# Parse ZL3b-n
# Format: lines like <f1r.1,@P0> text.with.periods.as.separators
# We want tokens. Standard tokenizer: split on '.' and ','; strip brackets.

def tokenize_line(line):
    """Extract Voynichese tokens from a transcription line."""
    # Skip header/comment lines
    if not line.startswith('<'):
        return None, []
    # Match folio tag like <f1r.1,@P0>
    m = re.match(r'<(f\d+[rv]\d*)\.', line)
    if not m:
        return None, []
    folio = m.group(1)
    # Text is after the closing >
    text_match = re.search(r'>\s*(.+?)(?:\s*<|$)', line)
    if not text_match:
        return folio, []
    text = text_match.group(1)
    # Remove comments {...} and uncertain markers
    text = re.sub(r'\{[^}]*\}', '', text)
    # Resolve [a:b] -> a (first reading)
    text = re.sub(r'\[([^:\]]+):[^\]]+\]', r'\1', text)
    # Split on period (word separator) and comma (line separator within paragraph)
    tokens = re.split(r'[.,]', text)
    # Clean: strip whitespace, remove empties, remove ?, remove !
    cleaned = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if '?' in t or '!' in t:
            continue
        # Remove paragraph markers if any leaked through
        if t.startswith('-'):
            continue
        cleaned.append(t)
    return folio, cleaned

# Collect tokens per folio
folio_tokens = defaultdict(list)
with open('ZL3b-n', encoding='latin-1') as f:
    for line in f:
        folio, tokens = tokenize_line(line.rstrip())
        if folio:
            folio_tokens[folio].extend(tokens)

# cth- forms to track. Start with the four locked base forms.
# Then track them as substrings to catch prefixed/suffixed variants.
base_forms = ['cthor', 'cthy', 'cthol', 'cthey']

# For each herbal-A folio: count occurrences of each base form (as a whole token).
# Also count tokens containing cth- with each vowel/suffix pattern.
folio_cth = defaultdict(Counter)
folio_cth_extended = defaultdict(Counter)

for folio in herbal_a_folios:
    tokens = folio_tokens.get(folio, [])
    for tok in tokens:
        # Exact base form match
        if tok in base_forms:
            folio_cth[folio][tok] += 1
        # Extended: any token starting with cth and containing one of the vowel patterns
        # Categorize by which base "root" the token most resembles
        if 'cth' in tok:
            # Classify by suffix pattern
            if tok.endswith('or') or 'cthor' in tok:
                folio_cth_extended[folio]['cthor_family'] += 1
            elif tok.endswith('ol') or 'cthol' in tok:
                folio_cth_extended[folio]['cthol_family'] += 1
            elif tok.endswith('ey') or 'cthey' in tok:
                folio_cth_extended[folio]['cthey_family'] += 1
            elif tok.endswith('y') or 'cthy' in tok:
                folio_cth_extended[folio]['cthy_family'] += 1
            else:
                folio_cth_extended[folio]['cth_other'] += 1

# Summary
print(f"Herbal-A folios: {len(herbal_a_folios)}")
print(f"Folios with ZL3b tokens: {sum(1 for f in herbal_a_folios if folio_tokens.get(f))}")
print()

# Base-form occurrence totals
total_base = Counter()
for folio, counter in folio_cth.items():
    total_base.update(counter)
print("Base cth- form totals across all herbal-A:")
for form in base_forms:
    print(f"  {form}: {total_base[form]}")
print()

# Folio-level breakdown
print("Folios with at least one base cth- form:")
folios_with_cth = [f for f in herbal_a_folios if folio_cth[f]]
print(f"  Count: {len(folios_with_cth)} / {len(herbal_a_folios)}")
print()

# Distribution of folio "dominant base form"
print("Per-folio dominant base form (folios with >=1 base cth-):")
dominant = Counter()
folio_dom = {}
for f in folios_with_cth:
    c = folio_cth[f]
    top = max(c.items(), key=lambda x: x[1])
    dominant[top[0]] += 1
    folio_dom[f] = top[0]
for form in base_forms:
    print(f"  {form}-dominant: {dominant[form]} folios")
print()

# Now check extended families for richer signal
print("Extended cth- family totals (anything containing cth- classified by suffix):")
total_ext = Counter()
for folio, counter in folio_cth_extended.items():
    total_ext.update(counter)
for k, v in total_ext.most_common():
    print(f"  {k}: {v}")
print()

# Dominant extended family per folio
print("Per-folio dominant extended cth- family:")
dom_ext = Counter()
folio_dom_ext = {}
for f in herbal_a_folios:
    c = folio_cth_extended[f]
    if not c:
        continue
    top = max(c.items(), key=lambda x: x[1])
    dom_ext[top[0]] += 1
    folio_dom_ext[f] = top[0]
for k, v in dom_ext.most_common():
    print(f"  {k}-dominant: {v} folios")
print()

# Save the per-folio inventory for next stage
with open('cth_inventory.csv', 'w', newline='') as fout:
    writer = csv.writer(fout)
    writer.writerow(['folio', 'cthor', 'cthy', 'cthol', 'cthey', 'dominant_base',
                     'cthor_fam', 'cthy_fam', 'cthol_fam', 'cthey_fam', 'cth_other',
                     'dominant_family', 'total_cth_tokens'])
    for f in sorted(herbal_a_folios):
        c = folio_cth[f]
        ce = folio_cth_extended[f]
        total = sum(ce.values())
        writer.writerow([
            f,
            c.get('cthor', 0), c.get('cthy', 0), c.get('cthol', 0), c.get('cthey', 0),
            folio_dom.get(f, ''),
            ce.get('cthor_family', 0), ce.get('cthy_family', 0),
            ce.get('cthol_family', 0), ce.get('cthey_family', 0),
            ce.get('cth_other', 0),
            folio_dom_ext.get(f, ''),
            total
        ])

print("Wrote cth_inventory.csv")
