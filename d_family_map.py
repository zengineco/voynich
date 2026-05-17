#!/usr/bin/env python3
"""
d-family deep map (Option B).

For each productive d-form (count >= 5 in corpus):
  - Compute left-neighbor and right-neighbor class profile
  - Classify by adjacency into positional class:
      PROCLITIC:  high right-content, low left-content (sits before content NPs)
      ENCLITIC:   high left-content, low right-content (sits after content NPs)
      CONNECTOR:  high content on BOTH sides (between NPs)
      TERMINATOR: low content on both sides, often line/paragraph-end
      FREE:       roughly balanced, no strong adjacency preference
  - Test: does the SUFFIX of the d-form predict the positional class?
"""
import re, csv
from collections import defaultdict, Counter

# ---------- Tokenize (reuse logic) ----------
folio_re = re.compile(r"^<f(\d+[rv]\d*)\.")
tag_re = re.compile(r"<[^>]*>")
alt_re = re.compile(r"\[([^:\]]+):[^\]]*\]")
misc_chars = re.compile(r"[%!$=*]")

def clean_token(tok):
    tok = tag_re.sub("", tok)
    tok = alt_re.sub(r"\1", tok)
    tok = misc_chars.sub("", tok)
    tok = tok.strip()
    if not tok or "?" in tok: return None
    if not re.match(r"^[a-z]+$", tok): return None
    return tok

# Load section labels
folio_section = {}
with open("/mnt/project/voynich_folio_profile.csv") as f:
    for row in csv.DictReader(f):
        folio_section[row["folio"].strip()] = row["section"].strip()
def norm_section(s):
    return "cosmo/zodiac" if s == "cosmo" else s

# Parse with LINE boundaries marked (so we can detect line-initial/final position)
# Format each token's "line-position": position within a line, and total tokens in line.
# We'll mark first-of-line with prev=<LINE_START> and last-of-line with next=<LINE_END>.

line_sequences = []  # list of (folio, section, [tokens])
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
        section = norm_section(folio_section.get(current_folio, "unknown"))
        if section == "unknown": continue
        text = line.split(">", 1)[1] if ">" in line else line
        text = tag_re.sub("", text)
        text = alt_re.sub(r"\1", text)
        text = misc_chars.sub("", text)
        raw = re.split(r"[.,\s]+", text)
        toks = [clean_token(t) for t in raw]
        toks = [t for t in toks if t]
        if toks:
            line_sequences.append((current_folio, section, toks))

# ---------- d-family detection ----------
def is_d_family(tok):
    if not tok.startswith("d"): return False
    if tok.startswith("dch") or tok.startswith("dsh"): return False
    return True

# ---------- Token classification: is it a content root, function word, or label? ----------
HUMOR_BASES = ["ch", "sh"]
PROCESS_BASES = ["qok", "qot", "ok", "ot"]
HUMOR_PREFIXES = ["cth", "qok", "qot", "ok", "ot", "ch", "sh", "kch", "ksh",
                  "dch", "dsh", "tch", "tsh", "k", "t"]
# Note: 'd' is excluded from prefixes here because we're analyzing d-family separately.

def is_content_root_token(tok):
    """True if token parses as content root under architecture."""
    # Try humor bases with optional derivational prefix
    for base in HUMOR_BASES:
        for pfx in sorted(HUMOR_PREFIXES + [""], key=lambda x: -len(x)):
            if tok.startswith(pfx):
                rest = tok[len(pfx):]
                if rest.startswith(base):
                    return True
                break
    # Try process bases at start
    for base in PROCESS_BASES:
        if tok.startswith(base):
            return True
    return False

# Function-word inventory (Levels 2-4 of architecture, excluding d-family)
FUNCTION_WORDS = {"ol", "or", "ar", "al", "y", "s", "r", "l", "o", "m", "n", "aiin", "ain",
                  "aiir", "air", "saiin", "sain", "qol", "ory", "oro", "oly", "oky", "oty",
                  "am", "an"}

def token_class(tok):
    """Classify a token: 'd' (d-family), 'C' (content root), 'F' (function word), 
       'L' (likely label/other)."""
    if tok is None: return None
    if is_d_family(tok): return "d"
    if is_content_root_token(tok): return "C"
    if tok in FUNCTION_WORDS: return "F"
    return "L"  # label / other

# ---------- Build adjacency profile per d-form ----------
# For each d-token occurrence, record:
#   - left neighbor class (or LINE_START)
#   - right neighbor class (or LINE_END)
#   - section

d_left = defaultdict(Counter)   # d_form -> Counter of left-neighbor class
d_right = defaultdict(Counter)
d_section = defaultdict(Counter)
d_total = Counter()

for folio, section, toks in line_sequences:
    n = len(toks)
    for i, tok in enumerate(toks):
        if not is_d_family(tok): continue
        d_total[tok] += 1
        d_section[tok][section] += 1
        # left
        if i == 0:
            d_left[tok]["<LS>"] += 1
        else:
            d_left[tok][token_class(toks[i-1])] += 1
        # right
        if i == n - 1:
            d_right[tok]["<LE>"] += 1
        else:
            d_right[tok][token_class(toks[i+1])] += 1

# ---------- Position classification ----------
# Compute, per d-form, pct of left-context that is CONTENT, pct of right-context that is CONTENT.
# Plus line-edge pct.

def pcts(counter):
    tot = sum(counter.values())
    if tot == 0: return {"C": 0, "F": 0, "d": 0, "L": 0, "edge": 0, "n": 0}
    return {
        "C": 100*counter.get("C", 0)/tot,
        "F": 100*counter.get("F", 0)/tot,
        "d": 100*counter.get("d", 0)/tot,
        "L": 100*counter.get("L", 0)/tot,
        "edge": 100*(counter.get("<LS>", 0) + counter.get("<LE>", 0))/tot,
        "n": tot,
    }

# Classification rules (transparent, not fitted):
def classify_position(left_pct, right_pct):
    """left_pct, right_pct: dicts with C, F, d, L, edge.
       Returns one of: PROCLITIC, CONNECTOR, ENCLITIC, TERMINATOR, FREE.
       Decision based on CONTENT-on-both-sides asymmetry + edge-prevalence."""
    L_content = left_pct["C"]
    R_content = right_pct["C"]
    L_edge = left_pct["edge"]
    R_edge = right_pct["edge"]
    # TERMINATOR: high line-edge on right (>= 25%) — clause/line-final marker
    if R_edge >= 25:
        return "TERMINATOR"
    # PROCLITIC: line-edge on left (or low left content) + high right content
    if (L_edge >= 25 or L_content < 25) and R_content >= 35:
        return "PROCLITIC"
    # ENCLITIC: high left content, low right content
    if L_content >= 35 and R_content < 25:
        return "ENCLITIC"
    # CONNECTOR: content on both sides
    if L_content >= 25 and R_content >= 25:
        return "CONNECTOR"
    return "FREE"

# ---------- Score d-forms ----------
print(f"d-family positional profile (count >= 10):")
print(f"{'form':12s} {'n':>5s}  L:C%  R:C%  L:F%  R:F%  L:ed% R:ed%  CLASS")
profiles = {}
for tok, total in d_total.most_common():
    if total < 10: break
    lp = pcts(d_left[tok])
    rp = pcts(d_right[tok])
    cls = classify_position(lp, rp)
    profiles[tok] = (lp, rp, cls, total)
    print(f"{tok:12s} {total:>5d}  {lp['C']:>4.0f}  {rp['C']:>4.0f}  {lp['F']:>4.0f}  {rp['F']:>4.0f}  "
          f"{lp['edge']:>4.0f}  {rp['edge']:>4.0f}   {cls}")

# ---------- Suffix → position predictability ----------
# Strip 'd' prefix, treat the rest as "suffix" of the d-form.
# Build P(class | suffix-tail) and compute accuracy of best class per suffix.
print(f"\n{'='*70}")
print("SUFFIX-TAIL → POSITION CLASS")
print(f"{'='*70}")
suffix_class = defaultdict(Counter)
suffix_total = Counter()
for tok, (lp, rp, cls, total) in profiles.items():
    tail = tok[1:] if tok != "d" else ""
    suffix_class[tail][cls] += total
    suffix_total[tail] += total

print(f"{'tail':12s} {'class profile':35s}  predicted_class  predictability")
for tail, total in sorted(suffix_total.items(), key=lambda x: -x[1]):
    profile = suffix_class[tail]
    top_class, top_count = profile.most_common(1)[0]
    predictability = 100*top_count/total
    profile_str = ", ".join(f"{c}:{n}" for c, n in profile.most_common())
    print(f"{tail:12s} {profile_str:35s}  {top_class:11s}  {predictability:>5.1f}%")

# Aggregate predictability: weight by suffix frequency
total_correct = sum(suffix_class[t].most_common(1)[0][1] for t in suffix_total)
total_all = sum(suffix_total.values())
print(f"\nOverall suffix-tail → class predictability: {total_correct}/{total_all} = {100*total_correct/total_all:.1f}%")

# Random baseline = max-class share
class_counts = Counter()
for tok, (lp, rp, cls, total) in profiles.items():
    class_counts[cls] += total
print(f"\nClass distribution across all d-tokens:")
for cls, c in class_counts.most_common():
    print(f"  {cls:11s} {c:>5d}  ({100*c/total_all:.1f}%)")
print(f"Trivial 'always predict most-common-class' baseline: "
      f"{100*class_counts.most_common(1)[0][1]/total_all:.1f}%")

# ---------- Compound suffix examples ----------
print(f"\n{'='*70}")
print("d-family COMPOUND-SUFFIX EXAMPLES (lower-count types)")
print(f"{'='*70}")
print(f"These are productive but rare — used to validate 'compound suffix subclass' hypothesis.")
compound_examples = [t for t in d_total if d_total[t] >= 4 and len(t) >= 5][:30]
print(f"\n{'form':12s} {'count':>5s}  {'left-class':30s}  {'right-class':30s}")
for tok in compound_examples:
    if tok in profiles: continue  # already in main table
    lp = pcts(d_left[tok])
    rp = pcts(d_right[tok])
    cls = classify_position(lp, rp)
    n = d_total[tok]
    lp_str = f"C{lp['C']:.0f}/F{lp['F']:.0f}/ed{lp['edge']:.0f}"
    rp_str = f"C{rp['C']:.0f}/F{rp['F']:.0f}/ed{rp['edge']:.0f}"
    print(f"{tok:12s} {n:>5d}  {lp_str:30s}  {rp_str:30s}  {cls}")

# ---------- Section-conditioned analysis ----------
print(f"\n{'='*70}")
print("d-FAMILY USAGE PER SECTION")
print(f"{'='*70}")
# d-token rate per section, and which d-forms dominate per section
sections = ["balneo", "stars", "cosmo/zodiac", "rosettes", "herbal-A", "pharm-herbal"]
section_total_tokens = Counter()
for folio, section, toks in line_sequences:
    section_total_tokens[section] += len(toks)
section_d_total = {s: sum(d_section[t][s] for t in d_section) for s in sections}
print(f"{'section':18s} d-tokens   total   d-rate  top-3 d-forms")
for s in sections:
    dt = section_d_total[s]
    tt = section_total_tokens[s]
    rate = 100*dt/tt if tt else 0
    # top 3 d-forms in this section
    in_sec = Counter({t: d_section[t][s] for t in d_section})
    top3 = ", ".join(f"{t}({c})" for t, c in in_sec.most_common(3))
    print(f"{s:18s} {dt:>7d}  {tt:>6d}  {rate:>5.1f}%  {top3}")
