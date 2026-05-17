#!/usr/bin/env python3
"""
What's in the 'L' (label/other) neighbor class for d-forms?
The naive d-family analysis shows L-class dominates neighbors (44-67% left).
Either:
  (a) These ARE content words my architecture misses → fix architecture
  (b) These are label/hapax tokens → confirms d-family lives in label-rich text
  (c) These are compound forms with 'l' / 'ckh' / 'cfh' prefixes I should add as bases
"""
import re, csv
from collections import defaultdict, Counter

folio_re = re.compile(r"^<f(\d+[rv]\d*)\.")
tag_re = re.compile(r"<[^>]*>")
alt_re = re.compile(r"\[([^:\]]+):[^\]]*\]")
misc_chars = re.compile(r"[%!$=*]")

def clean_token(tok):
    tok = tag_re.sub("", tok); tok = alt_re.sub(r"\1", tok); tok = misc_chars.sub("", tok)
    tok = tok.strip()
    if not tok or "?" in tok: return None
    if not re.match(r"^[a-z]+$", tok): return None
    return tok

folio_section = {}
with open("/mnt/project/voynich_folio_profile.csv") as f:
    for row in csv.DictReader(f):
        folio_section[row["folio"].strip()] = row["section"].strip()

line_sequences = []
current_folio = None
with open("/mnt/project/ZL3b-n") as f:
    for line in f:
        if line.startswith("#"): continue
        m = folio_re.match(line)
        if not m:
            mh = re.match(r"^<(f\d+[rv]\d*)>", line)
            if mh: current_folio = mh.group(1)
            continue
        current_folio = "f" + m.group(1)
        section = folio_section.get(current_folio, "unknown")
        if section == "unknown": continue
        text = line.split(">", 1)[1] if ">" in line else line
        text = tag_re.sub("", text); text = alt_re.sub(r"\1", text); text = misc_chars.sub("", text)
        toks = [t for t in (clean_token(x) for x in re.split(r"[.,\s]+", text)) if t]
        if toks:
            line_sequences.append((current_folio, section, toks))

HUMOR_BASES = ["ch", "sh"]
PROCESS_BASES = ["qok", "qot", "ok", "ot"]
HUMOR_PREFIXES = ["cth", "qok", "qot", "ok", "ot", "ch", "sh", "kch", "ksh",
                  "tch", "tsh", "k", "t"]
FUNCTION_WORDS = {"ol", "or", "ar", "al", "y", "s", "r", "l", "o", "m", "n",
                  "aiin", "ain", "aiir", "air", "saiin", "sain", "qol", "ory",
                  "oro", "oly", "oky", "oty", "am", "an", "shy"}

def is_d_family(tok):
    if not tok.startswith("d"): return False
    if tok.startswith("dch") or tok.startswith("dsh"): return False
    return True

def is_humor_content(tok):
    for base in HUMOR_BASES:
        for pfx in sorted(HUMOR_PREFIXES + [""], key=lambda x: -len(x)):
            if tok.startswith(pfx):
                rest = tok[len(pfx):]
                if rest.startswith(base): return True
                break
    return False

def is_process_content(tok):
    for base in PROCESS_BASES:
        if tok.startswith(base): return True
    return False

def classify_neighbor(tok):
    if is_d_family(tok): return "d"
    if is_humor_content(tok): return "Ch"
    if is_process_content(tok): return "Cp"
    if tok in FUNCTION_WORDS: return "F"
    return None  # the 'L' class

# Collect all "L-class" neighbors of high-frequency d-forms
target_d_forms = ["daiin", "dar", "dal", "dain", "dair", "dol", "dor", "dy", "dam"]

left_L_neighbors = defaultdict(Counter)   # d_form -> Counter of L-class left tokens
right_L_neighbors = defaultdict(Counter)

for folio, section, toks in line_sequences:
    n = len(toks)
    for i, tok in enumerate(toks):
        if tok not in target_d_forms: continue
        if i > 0:
            left_t = toks[i-1]
            if classify_neighbor(left_t) is None:
                left_L_neighbors[tok][left_t] += 1
        if i < n - 1:
            right_t = toks[i+1]
            if classify_neighbor(right_t) is None:
                right_L_neighbors[tok][right_t] += 1

# ---------- For each target form: top L-neighbors ----------
print("Top 'L-class' (unparsed) LEFT neighbors of major d-forms:")
print("Each entry shows count, the unparsed neighbor token, and what it might be.")
print()
for d in target_d_forms:
    print(f"--- LEFT of {d} ---")
    for tok, c in left_L_neighbors[d].most_common(10):
        # heuristic: starts with what?
        prefix = tok[:3] if len(tok) >= 3 else tok
        print(f"  {c:>3d}  {tok:15s}  starts: {prefix}")
    print()

print("=" * 70)
print("Top 'L-class' (unparsed) RIGHT neighbors of major d-forms:")
print("=" * 70)
for d in target_d_forms:
    print(f"--- RIGHT of {d} ---")
    for tok, c in right_L_neighbors[d].most_common(10):
        prefix = tok[:3] if len(tok) >= 3 else tok
        print(f"  {c:>3d}  {tok:15s}  starts: {prefix}")
    print()

# ---------- Aggregate L-class prefix distribution ----------
print("=" * 70)
print("AGGREGATE: what does the 'L-class' actually consist of?")
print("=" * 70)
all_L = Counter()
for d in target_d_forms:
    all_L.update(left_L_neighbors[d])
    all_L.update(right_L_neighbors[d])

# Bin by leading-prefix substring
prefix_bins = Counter()
for tok, c in all_L.items():
    # Bin into 3-char buckets
    for plen in [3, 2, 1]:
        if len(tok) >= plen:
            prefix_bins[tok[:plen]] += c
            break

print(f"\nTop 30 leading-character bins (3-char):")
prefix_3 = Counter()
for tok, c in all_L.items():
    if len(tok) >= 3: prefix_3[tok[:3]] += c
    elif len(tok) == 2: prefix_3[tok[:2]] += c
    elif len(tok) == 1: prefix_3[tok] += c
for p, c in prefix_3.most_common(30):
    print(f"  {p:6s}  {c}")

# ---------- Specific check: what % of L-class neighbors start with characters that look like content roots? ----------
print("\nL-class neighbor categorical breakdown:")
def bucket(tok):
    """Bucket an unparsed token into a heuristic category."""
    if tok.startswith("l"): return "l-initial"
    if tok.startswith("s"): return "s-initial"
    if tok.startswith("r"): return "r-initial"
    if tok.startswith("o"): return "o-initial-other"  # but not ok/ot/ol/or/oly/oky
    if tok.startswith("y"): return "y-initial"
    if tok.startswith("ck") or tok.startswith("cf"): return "ck/cf-cluster"
    if tok.startswith("a"): return "a-initial"
    if tok.startswith("p"): return "p-initial"
    if tok.startswith("e"): return "e-initial"
    if tok.startswith("ch") or tok.startswith("sh"): return "MISSED-humor"
    if tok.startswith("d"): return "d-initial-other"
    return "other"

bucket_counts = Counter()
for tok, c in all_L.items():
    bucket_counts[bucket(tok)] += c
total_L = sum(bucket_counts.values())
print(f"Total L-class neighbor tokens of d-forms: {total_L}")
for b, c in bucket_counts.most_common():
    print(f"  {b:25s} {c:>6d}  ({100*c/total_L:.1f}%)")
