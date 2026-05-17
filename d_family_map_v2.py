#!/usr/bin/env python3
"""
d-family deep map v2.

The naive 4-class adjacency model collapsed: 78% of d-tokens are 'FREE' (balanced 
adjacency to content roots). The handoff's PROCLITIC/CONNECTOR/ENCLITIC distinction
is not visible at the immediate-adjacency level.

This script tests two refined hypotheses:
  H1: Within "FREE" d-forms, the LINE-INITIAL pattern distinguishes proclitics 
      from mid-line connectors. Check: pct of tokens that are line-initial.
  H2: The "C" content-root adjacency lumps too coarsely. Split it into:
      - C_humor (ch/sh-base): substance NPs
      - C_process (qok/qot/ok/ot-base): process NPs
      Different d-forms may prefer one over the other.
  H3: For high-frequency d-forms, check left-right SYMMETRY in section weighting.
      If a d-form's left-neighbors are mostly content but its right-neighbors are
      mostly function words, that's still positional bias.

Also: revisit the classification thresholds — they were too strict.
"""
import re, csv
from collections import defaultdict, Counter

# ---------- Tokenize (reuse) ----------
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
def norm_section(s):
    return "cosmo/zodiac" if s == "cosmo" else s

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
        section = norm_section(folio_section.get(current_folio, "unknown"))
        if section == "unknown": continue
        text = line.split(">", 1)[1] if ">" in line else line
        text = tag_re.sub("", text); text = alt_re.sub(r"\1", text); text = misc_chars.sub("", text)
        toks = [t for t in (clean_token(x) for x in re.split(r"[.,\s]+", text)) if t]
        if toks:
            line_sequences.append((current_folio, section, toks))

# ---------- Refined token classification ----------
HUMOR_BASES = ["ch", "sh"]
PROCESS_BASES = ["qok", "qot", "ok", "ot"]
HUMOR_PREFIXES = ["cth", "qok", "qot", "ok", "ot", "ch", "sh", "kch", "ksh",
                  "tch", "tsh", "k", "t"]

def is_d_family(tok):
    if not tok.startswith("d"): return False
    if tok.startswith("dch") or tok.startswith("dsh"): return False
    return True

def is_humor_content(tok):
    """Token parses as a humor-root content word (ch/sh base, optional prefix).
    Try all prefixes; do NOT break after first failed prefix match."""
    for base in HUMOR_BASES:
        for pfx in sorted(HUMOR_PREFIXES + [""], key=lambda x: -len(x)):
            if tok.startswith(pfx):
                rest = tok[len(pfx):]
                if rest.startswith(base):
                    return True
                # do NOT break — keep trying shorter prefixes including ""
    return False

def is_process_content(tok):
    """Token parses as a process-root content word (qok/qot/ok/ot at start)."""
    for base in PROCESS_BASES:
        if tok.startswith(base):
            return True
    return False

FUNCTION_WORDS = {"ol", "or", "ar", "al", "y", "s", "r", "l", "o", "m", "n",
                  "aiin", "ain", "aiir", "air", "saiin", "sain", "qol", "ory",
                  "oro", "oly", "oky", "oty", "am", "an", "sain", "shy"}

def token_class_refined(tok):
    if tok is None: return None
    if is_d_family(tok): return "d"
    if is_humor_content(tok): return "Ch"   # ch/sh content
    if is_process_content(tok): return "Cp"  # process content
    if tok in FUNCTION_WORDS: return "F"
    return "L"

# ---------- Build refined adjacency profile ----------
d_left = defaultdict(Counter)
d_right = defaultdict(Counter)
d_total = Counter()
d_line_init = Counter()
d_line_final = Counter()

for folio, section, toks in line_sequences:
    n = len(toks)
    for i, tok in enumerate(toks):
        if not is_d_family(tok): continue
        d_total[tok] += 1
        if i == 0:
            d_left[tok]["<LS>"] += 1
            d_line_init[tok] += 1
        else:
            d_left[tok][token_class_refined(toks[i-1])] += 1
        if i == n - 1:
            d_right[tok]["<LE>"] += 1
            d_line_final[tok] += 1
        else:
            d_right[tok][token_class_refined(toks[i+1])] += 1

# ---------- Display refined profile for top forms ----------
print("REFINED d-family adjacency profile (count >= 10)")
print("Columns: n, LineInit%, LineFinal%, then Left/Right %% of [Ch=humor, Cp=process, F=fn, L=label, d=d-fam]")
print()
header = f"{'form':12s} {'n':>5s} {'init':>5s} {'fin':>5s}  " \
         f"{'L_Ch':>5s} {'L_Cp':>5s} {'L_F':>5s} {'L_L':>5s} {'L_d':>5s}   " \
         f"{'R_Ch':>5s} {'R_Cp':>5s} {'R_F':>5s} {'R_L':>5s} {'R_d':>5s}"
print(header)
print("-" * len(header))

def pct(counter, key):
    tot = sum(counter.values())
    return 100 * counter.get(key, 0) / tot if tot else 0

profiles = {}
for tok, total in d_total.most_common():
    if total < 10: break
    li_pct = 100*d_line_init[tok]/total
    lf_pct = 100*d_line_final[tok]/total
    prof = {
        "n": total,
        "init": li_pct, "fin": lf_pct,
        "L_Ch": pct(d_left[tok], "Ch"),
        "L_Cp": pct(d_left[tok], "Cp"),
        "L_F":  pct(d_left[tok], "F"),
        "L_L":  pct(d_left[tok], "L"),
        "L_d":  pct(d_left[tok], "d"),
        "R_Ch": pct(d_right[tok], "Ch"),
        "R_Cp": pct(d_right[tok], "Cp"),
        "R_F":  pct(d_right[tok], "F"),
        "R_L":  pct(d_right[tok], "L"),
        "R_d":  pct(d_right[tok], "d"),
    }
    profiles[tok] = prof
    print(f"{tok:12s} {total:>5d} {li_pct:>4.0f}% {lf_pct:>4.0f}%  "
          f"{prof['L_Ch']:>4.0f}% {prof['L_Cp']:>4.0f}% {prof['L_F']:>4.0f}% {prof['L_L']:>4.0f}% {prof['L_d']:>4.0f}%   "
          f"{prof['R_Ch']:>4.0f}% {prof['R_Cp']:>4.0f}% {prof['R_F']:>4.0f}% {prof['R_L']:>4.0f}% {prof['R_d']:>4.0f}%")

# ---------- Aggregate by suffix-tail signature ----------
# For each top d-form, compute a "signature vector" and cluster.
print("\n" + "="*70)
print("HYPOTHESIS H1: Line-initial pct distinguishes proclitics")
print("="*70)
print(f"{'form':12s} {'n':>5s} {'init%':>6s}  baseline = {sum(d_line_init.values())/sum(d_total.values())*100:.1f}%")
top = sorted(profiles.items(), key=lambda x: -x[1]["init"])
for tok, prof in top[:15]:
    print(f"{tok:12s} {prof['n']:>5d} {prof['init']:>5.0f}%")

# Compute baseline: what % of ALL tokens are line-initial?
total_lines = len(line_sequences)
total_tokens = sum(len(t) for _, _, t in line_sequences)
print(f"\nTotal lines: {total_lines}, total tokens: {total_tokens}, line-init baseline: {100*total_lines/total_tokens:.1f}%")

# ---------- Hypothesis H2: humor vs process content preference ----------
print("\n" + "="*70)
print("HYPOTHESIS H2: humor vs process content preference (L_Ch+R_Ch vs L_Cp+R_Cp)")
print("="*70)
print(f"{'form':12s} {'n':>5s}  hum%   prc%   ratio")
items = []
for tok, prof in profiles.items():
    hum = prof["L_Ch"] + prof["R_Ch"]
    prc = prof["L_Cp"] + prof["R_Cp"]
    ratio = hum/prc if prc else float("inf")
    items.append((tok, prof["n"], hum, prc, ratio))
items.sort(key=lambda x: -x[4] if x[4] != float("inf") else -999)
for tok, n, hum, prc, ratio in items:
    rs = "inf" if ratio == float("inf") else f"{ratio:.2f}"
    print(f"{tok:12s} {n:>5d}  {hum:>4.0f}%  {prc:>4.0f}%  {rs}")

# ---------- Final classification (refined) ----------
print("\n" + "="*70)
print("REFINED CLASSIFICATION (5 features: init%, fin%, Lcontent%, Rcontent%, line-edge asymmetry)")
print("="*70)

def classify_refined(prof):
    """Refined classifier:
    - TERMINATOR: line-final pct >= 30% OR right-edge >= 25%
    - PROCLITIC:  line-initial pct >= 20% AND right-content > left-content + 10
    - ENCLITIC:   line-final OK + left-content > right-content + 10 (but not strong terminator)
    - CONNECTOR:  left and right content roughly balanced and both >= 20%
    - DISCOURSE:  high adjacency to other function/d words (intra-function chains)
    - MID:        balanced, mostly content on both sides at moderate levels
    """
    init = prof["init"]; fin = prof["fin"]
    L_content = prof["L_Ch"] + prof["L_Cp"]
    R_content = prof["R_Ch"] + prof["R_Cp"]
    L_func = prof["L_F"] + prof["L_d"]
    R_func = prof["R_F"] + prof["R_d"]
    if fin >= 30:
        return "TERMINATOR"
    if init >= 20 and (R_content - L_content) >= 10:
        return "PROCLITIC"
    if L_content - R_content >= 10 and fin >= 15:
        return "ENCLITIC"
    if L_func + R_func >= 30:
        return "DISCOURSE"
    if L_content >= 20 and R_content >= 20:
        return "CONNECTOR"
    return "MID"

print(f"{'form':12s} {'n':>5s} {'init%':>5s} {'fin%':>5s} {'Lcont':>6s} {'Rcont':>6s} {'Lfn':>5s} {'Rfn':>5s}  CLASS")
classes_assigned = Counter()
class_breakdown = defaultdict(list)
for tok, prof in profiles.items():
    cls = classify_refined(prof)
    classes_assigned[cls] += prof["n"]
    class_breakdown[cls].append((tok, prof["n"]))
    L_content = prof["L_Ch"] + prof["L_Cp"]
    R_content = prof["R_Ch"] + prof["R_Cp"]
    L_func = prof["L_F"] + prof["L_d"]
    R_func = prof["R_F"] + prof["R_d"]
    print(f"{tok:12s} {prof['n']:>5d} {prof['init']:>4.0f}% {prof['fin']:>4.0f}% "
          f"{L_content:>5.0f}% {R_content:>5.0f}% {L_func:>4.0f}% {R_func:>4.0f}%   {cls}")

print(f"\nClass aggregate (counts):")
total_d_top = sum(classes_assigned.values())
for cls, c in classes_assigned.most_common():
    print(f"  {cls:11s} {c:>5d}  ({100*c/total_d_top:.1f}%)")

print(f"\nForms per class:")
for cls in classes_assigned:
    forms = class_breakdown[cls]
    forms_str = ", ".join(f"{t}({n})" for t, n in forms)
    print(f"  {cls:11s}: {forms_str}")
