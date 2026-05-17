#!/usr/bin/env python3
"""
d-family suffix → positional class predictive rule extraction.

Given the refined 5-class scheme (CONNECTOR/DISCOURSE/ENCLITIC/TERMINATOR/PROCLITIC),
extract per-suffix rules. Suffix = everything after the leading 'd'.

Then validate on lower-frequency d-forms (count 4-9): does the rule generalize?
"""
import re, csv
from collections import defaultdict, Counter

# ===== reuse tokenization and classifier from v2 =====
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
        if toks: line_sequences.append((current_folio, section, toks))

HUMOR_BASES = ["ch", "sh"]
PROCESS_BASES = ["qok", "qot", "ok", "ot"]
HUMOR_PREFIXES = ["cth", "qok", "qot", "ok", "ot", "ch", "sh", "kch", "ksh",
                  "tch", "tsh", "k", "t"]
FUNCTION_WORDS = {"ol","or","ar","al","y","s","r","l","o","m","n","aiin","ain",
                  "aiir","air","saiin","sain","qol","ory","oro","oly","oky","oty",
                  "am","an","shy"}

def is_d_family(tok):
    if not tok.startswith("d"): return False
    if tok.startswith("dch") or tok.startswith("dsh"): return False
    return True

def is_humor_content(tok):
    for base in HUMOR_BASES:
        for pfx in sorted(HUMOR_PREFIXES + [""], key=lambda x: -len(x)):
            if tok.startswith(pfx):
                rest = tok[len(pfx):]
                if rest.startswith(base):
                    return True
    return False

def is_process_content(tok):
    for base in PROCESS_BASES:
        if tok.startswith(base): return True
    return False

def token_class_refined(tok):
    if tok is None: return None
    if is_d_family(tok): return "d"
    if is_humor_content(tok): return "Ch"
    if is_process_content(tok): return "Cp"
    if tok in FUNCTION_WORDS: return "F"
    return "L"

# ===== Build adjacency for ALL d-forms (no count cutoff) =====
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
            d_left[tok]["<LS>"] += 1; d_line_init[tok] += 1
        else:
            d_left[tok][token_class_refined(toks[i-1])] += 1
        if i == n - 1:
            d_right[tok]["<LE>"] += 1; d_line_final[tok] += 1
        else:
            d_right[tok][token_class_refined(toks[i+1])] += 1

def pct(counter, key):
    tot = sum(counter.values())
    return 100 * counter.get(key, 0) / tot if tot else 0

def profile(tok):
    return {
        "n": d_total[tok],
        "init": 100*d_line_init[tok]/d_total[tok] if d_total[tok] else 0,
        "fin": 100*d_line_final[tok]/d_total[tok] if d_total[tok] else 0,
        "L_Ch": pct(d_left[tok], "Ch"), "L_Cp": pct(d_left[tok], "Cp"),
        "L_F": pct(d_left[tok], "F"), "L_d": pct(d_left[tok], "d"),
        "R_Ch": pct(d_right[tok], "Ch"), "R_Cp": pct(d_right[tok], "Cp"),
        "R_F": pct(d_right[tok], "F"), "R_d": pct(d_right[tok], "d"),
    }

def classify(prof):
    init=prof["init"]; fin=prof["fin"]
    Lc = prof["L_Ch"]+prof["L_Cp"]; Rc = prof["R_Ch"]+prof["R_Cp"]
    if fin >= 30: return "TERMINATOR"
    if init >= 20 and (Rc-Lc) >= 10: return "PROCLITIC"
    if Lc-Rc >= 10 and fin >= 15: return "ENCLITIC"
    Lf = prof["L_F"]+prof["L_d"]; Rf = prof["R_F"]+prof["R_d"]
    if Lf+Rf >= 30: return "DISCOURSE"
    if Lc >= 30 and Rc >= 30: return "CONNECTOR"
    return "MID"

# ===== Suffix → class table =====
# Group d-forms by their suffix-tail. For each tail, aggregate class counts of
# d-forms that have that tail. Compare to the dominant class.

print("="*70)
print("SUFFIX-TAIL → POSITIONAL CLASS — TOP FORMS (n>=10)")
print("="*70)
print(f"{'tail':10s} {'form':12s} {'n':>5s}  CLASS         init% fin% Lcont% Rcont%")
suffix_class_top = defaultdict(Counter)  # tail -> Counter of class -> count
for tok in sorted(d_total, key=lambda t: -d_total[t]):
    n = d_total[tok]
    if n < 10: break
    prof = profile(tok)
    cls = classify(prof)
    tail = tok[1:]  # strip 'd'
    suffix_class_top[tail][cls] += n
    Lc = prof['L_Ch']+prof['L_Cp']; Rc = prof['R_Ch']+prof['R_Cp']
    print(f"{tail:10s} {tok:12s} {n:>5d}  {cls:12s} {prof['init']:>4.0f}% {prof['fin']:>4.0f}% {Lc:>5.0f}% {Rc:>5.0f}%")

# ===== Map suffix-tail to dominant class =====
print(f"\n{'='*70}")
print("RULES: suffix-tail → predicted class")
print(f"{'='*70}")
rule_set = {}
for tail in sorted(suffix_class_top, key=lambda t: -sum(suffix_class_top[t].values())):
    cls_counts = suffix_class_top[tail]
    top_cls, top_n = cls_counts.most_common(1)[0]
    total = sum(cls_counts.values())
    rule_set[tail] = top_cls
    examples = ", ".join(f"{c}:{n}" for c, n in cls_counts.most_common())
    print(f"  -{tail:10s} → {top_cls:12s}  ({total:>5d} tokens; {examples})")

# ===== Validate on lower-count d-forms =====
print(f"\n{'='*70}")
print("VALIDATION: predict class for d-forms with n=4..9 using suffix-tail rules")
print(f"{'='*70}")
print(f"{'form':12s} {'tail':10s} {'n':>4s}  observed       predicted      match?")
correct = 0; total_val = 0; ambiguous = 0
val_results = []
for tok in sorted(d_total, key=lambda t: -d_total[t]):
    n = d_total[tok]
    if n < 4 or n >= 10: continue
    prof = profile(tok)
    observed = classify(prof)
    tail = tok[1:]
    # Best matching rule: longest suffix-suffix match
    pred = None
    for rule_tail in sorted(rule_set, key=lambda x: -len(x)):
        if tail.endswith(rule_tail) and rule_tail:
            pred = rule_set[rule_tail]
            break
    if pred is None:
        pred = "?"
    match = (pred == observed)
    if pred != "?":
        total_val += 1
        if match: correct += 1
    else:
        ambiguous += 1
    val_results.append((tok, tail, n, observed, pred, match))

# show first 30
for tok, tail, n, obs, pred, m in val_results[:30]:
    flag = "✓" if m else ("?" if pred == "?" else "✗")
    print(f"{tok:12s} {tail:10s} {n:>4d}  {obs:12s}   {pred:12s}   {flag}")

print(f"\nValidation summary: {correct}/{total_val} ({100*correct/total_val if total_val else 0:.1f}%) "
      f"correct on rule-coverable forms; {ambiguous} ambiguous (no matching rule)")

# Random baseline: just predict the most common class
class_counts = Counter(r[3] for r in val_results)
most_common = class_counts.most_common(1)[0]
baseline = 100*most_common[1]/sum(class_counts.values())
print(f"Random/majority baseline: {most_common[0]} = {baseline:.1f}%")

# ===== Section-weighted d-family pattern =====
print(f"\n{'='*70}")
print("d-FAMILY POSITIONAL CLASS × SECTION")
print(f"{'='*70}")
d_section_class = defaultdict(Counter)
for folio, section, toks in line_sequences:
    n = len(toks)
    for i, tok in enumerate(toks):
        if not is_d_family(tok): continue
        prof = profile(tok)
        if d_total[tok] < 4: continue  # skip ultra-rare
        cls = classify(prof)
        d_section_class[section][cls] += 1

sections = ["balneo", "stars", "cosmo/zodiac", "rosettes", "herbal-A", "pharm-herbal"]
print(f"{'section':18s} " + "  ".join(f"{c[:10]:>10s}" for c in ["CONNECTOR","DISCOURSE","TERMINATOR","ENCLITIC","PROCLITIC"]))
for s in sections:
    tot = sum(d_section_class[s].values())
    row = [f"{s:18s}"]
    for c in ["CONNECTOR","DISCOURSE","TERMINATOR","ENCLITIC","PROCLITIC"]:
        cnt = d_section_class[s][c]
        pct_v = 100*cnt/tot if tot else 0
        row.append(f"{pct_v:>8.1f}%")
    print("  ".join(row) + f"   (n={tot})")
