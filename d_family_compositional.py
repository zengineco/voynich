#!/usr/bin/env python3
"""
d-family compositional analysis.

Hypothesis: long d-forms like 'dalchedy', 'dalchdy', 'doiin', 'dory' are NOT 
monomorphemic d-clitics but COMPOUNDS:
   d + [base d-suffix] + [content morpheme]
For example:
   dalchedy = d + al + chedy  (d-clitic dal + content chedy)
   daiin    = d + aiin        (d-clitic + paradigm-suffix aiin, no content)
   dory     = d + ory          OR  d + or + y
   doiin    = d + oiin         OR  d + o + iin

Test: for each d-form, can we decompose tail as [d-suffix-tail] + [content stem]?
If yes, the d-form is a CLITIC + CONTENT compound, and its positional behavior
should be that of the d-clitic, not predicted by the full tail.
"""
import re, csv
from collections import defaultdict, Counter

# Reuse tokenization
folio_re = re.compile(r"^<f(\d+[rv]\d*)\.")
tag_re = re.compile(r"<[^>]*>")
alt_re = re.compile(r"\[([^:\]]+):[^\]]*\]")
misc_chars = re.compile(r"[%!$=*]")
def clean_token(tok):
    tok=tag_re.sub("",tok); tok=alt_re.sub(r"\1",tok); tok=misc_chars.sub("",tok); tok=tok.strip()
    if not tok or "?" in tok or not re.match(r"^[a-z]+$",tok): return None
    return tok

folio_section = {}
with open("/mnt/project/voynich_folio_profile.csv") as f:
    for row in csv.DictReader(f):
        folio_section[row["folio"].strip()] = row["section"].strip()
def norm_section(s): return "cosmo/zodiac" if s=="cosmo" else s

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
        current_folio = "f"+m.group(1)
        section = norm_section(folio_section.get(current_folio,"unknown"))
        if section=="unknown": continue
        text = line.split(">",1)[1] if ">" in line else line
        text = tag_re.sub("",text); text = alt_re.sub(r"\1",text); text = misc_chars.sub("",text)
        toks = [t for t in (clean_token(x) for x in re.split(r"[.,\s]+",text)) if t]
        if toks: line_sequences.append((current_folio, section, toks))

# d-family
def is_d_family(tok):
    if not tok.startswith("d"): return False
    if tok.startswith("dch") or tok.startswith("dsh"): return False
    return True

# Count d-forms
d_total = Counter()
for _, _, toks in line_sequences:
    for tok in toks:
        if is_d_family(tok): d_total[tok] += 1

# ===== Core inventory of simple d-clitics (from prior analysis) =====
# These are the d-clitic STEMS that should appear at the beginning of compounds.
SIMPLE_D_CLITICS = ["d", "da", "dal", "dar", "dol", "dor", "dy", "do",
                    "dain", "dair", "daiin", "daiir", "daly", "dary"]

# Content morphemes that could appear after a clitic — from architecture
# This includes: chedy, chol, chor, shedy, shol, shor, qokedy, etc.
# Build dynamic list from corpus: any token >= 3 chars seen >= 2 times that's not d-family.
content_seen = Counter()
for _, _, toks in line_sequences:
    for tok in toks:
        if not is_d_family(tok) and len(tok) >= 3:
            content_seen[tok] += 1

# Common content morphemes (3-7 chars, seen >= 5 times)
common_content = set(t for t, c in content_seen.items() if c >= 5 and 3 <= len(t) <= 8)
print(f"Common content morphemes considered as compound bodies: {len(common_content)}")

# Also include known suffix-only tails that aren't content but could be d-form internal:
INTERNAL_TAILS = {"y", "ar", "al", "am", "an", "or", "ol", "ain", "air", "aiin", "aiir",
                  "iin", "iiin", "iir", "edy", "eedy", "eey", "ey", "edy"}

def decompose_d_form(tok):
    """Try to decompose tok = d-clitic + content/internal-tail.
    Returns list of (clitic, body) pairs.
    """
    if not is_d_family(tok): return []
    results = []
    # Try every SIMPLE_D_CLITIC as the prefix (longest first to avoid d='d' eating everything)
    for clitic in sorted(SIMPLE_D_CLITICS, key=lambda x: -len(x)):
        if tok.startswith(clitic) and tok != clitic:
            body = tok[len(clitic):]
            if body in common_content:
                results.append((clitic, body, "content"))
            elif body in INTERNAL_TAILS:
                results.append((clitic, body, "internal"))
            elif body == "":
                pass  # tok == clitic, skip
            else:
                # Maybe body is itself a long content form
                if len(body) >= 3 and body in content_seen and content_seen[body] >= 2:
                    results.append((clitic, body, "rare-content"))
    return results

# ===== Apply decomposition to all d-forms n>=4 =====
print()
print("="*70)
print("d-FORM DECOMPOSITION (n >= 4)")
print("="*70)
decompositions = {}
for tok in sorted(d_total, key=lambda t: -d_total[t]):
    n = d_total[tok]
    if n < 4: continue
    parses = decompose_d_form(tok)
    decompositions[tok] = parses
    if parses:
        # Show shortest clitic + longest body? Or longest clitic + shortest body?
        # Prefer maximally-decomposed: longest body that's a content form
        best = sorted(parses, key=lambda p: (-(p[2]=="content"), -len(p[1])))[0]
        clitic, body, kind = best
        all_parses = "; ".join(f"{c}+{b}({k})" for c, b, k in parses)
        print(f"{tok:14s} {n:>5d}  best={clitic}+{body}[{kind}]   all=[{all_parses}]")
    else:
        print(f"{tok:14s} {n:>5d}  unparsed (atomic)")

# ===== Recompute positional class using CLITIC as the unit =====
HUMOR_BASES = ["ch", "sh"]
PROCESS_BASES = ["qok", "qot", "ok", "ot"]
HUMOR_PREFIXES = ["cth", "qok", "qot", "ok", "ot", "ch", "sh", "kch", "ksh",
                  "tch", "tsh", "k", "t"]
FUNCTION_WORDS = {"ol","or","ar","al","y","s","r","l","o","m","n","aiin","ain",
                  "aiir","air","saiin","sain","qol","ory","oro","oly","oky","oty",
                  "am","an","shy"}

def is_humor_content(tok):
    for base in HUMOR_BASES:
        for pfx in sorted(HUMOR_PREFIXES+[""], key=lambda x: -len(x)):
            if tok.startswith(pfx):
                rest = tok[len(pfx):]
                if rest.startswith(base): return True
    return False
def is_process_content(tok):
    return any(tok.startswith(b) for b in PROCESS_BASES)
def tc(tok):
    if tok is None: return None
    if is_d_family(tok): return "d"
    if is_humor_content(tok): return "Ch"
    if is_process_content(tok): return "Cp"
    if tok in FUNCTION_WORDS: return "F"
    return "L"

# Now test the COMPOSITIONAL hypothesis:
# If a d-form like 'dalchedy' is really 'dal' + 'chedy', then its position should
# track 'dal' position. dal has Lcontent=58%, Rcontent=36%, fin=22% — ENCLITIC.
# But 'dalchedy' itself has fin=57% — TERMINATOR.
#
# Different prediction: 'dalchedy' is a d-clitic 'dal' fused with the trailing
# content 'chedy', and the WHOLE THING behaves like the content 'chedy' grammatically
# (which is process-aspect, used in balneo-style chains).
#
# Test: in the corpus, where does 'dalchedy' appear, and what does 'chedy' do positionally?
# If they're similar → compositional. If not → 'dalchedy' is atomic.

def adjacency_for(tok):
    L = Counter(); R = Counter(); init = 0; fin = 0; n = 0
    for _, _, toks in line_sequences:
        L_n = len(toks)
        for i, t in enumerate(toks):
            if t != tok: continue
            n += 1
            if i == 0: init += 1; L["<LS>"] += 1
            else: L[tc(toks[i-1])] += 1
            if i == L_n - 1: fin += 1; R["<LE>"] += 1
            else: R[tc(toks[i+1])] += 1
    return L, R, init, fin, n

def class_of(L, R, init, fin, n):
    if n == 0: return None
    def pct(c, k): tot=sum(c.values()); return 100*c.get(k,0)/tot if tot else 0
    Lc = pct(L,"Ch")+pct(L,"Cp"); Rc = pct(R,"Ch")+pct(R,"Cp")
    init_p = 100*init/n; fin_p = 100*fin/n
    if fin_p >= 30: return "TERMINATOR"
    if init_p >= 20 and Rc-Lc >= 10: return "PROCLITIC"
    if Lc-Rc >= 10 and fin_p >= 15: return "ENCLITIC"
    Lf = pct(L,"F")+pct(L,"d"); Rf = pct(R,"F")+pct(R,"d")
    if Lf+Rf >= 30: return "DISCOURSE"
    if Lc >= 30 and Rc >= 30: return "CONNECTOR"
    return "MID"

# Compare each decomposable d-form with its components
print(f"\n{'='*70}")
print("COMPOSITIONAL TEST: d-form vs. its decomposed clitic vs. its content-body")
print(f"{'='*70}")
print(f"{'whole':14s} {'class':12s}  {'clitic':10s} {'class':12s}  {'body':10s} {'class':12s}")
test_pairs = []
for tok in sorted(d_total, key=lambda t: -d_total[t]):
    if d_total[tok] < 4: continue
    parses = decompositions.get(tok, [])
    content_parses = [p for p in parses if p[2] == "content" or p[2] == "rare-content"]
    if not content_parses: continue
    # Use the longest-body parse
    clitic, body, kind = sorted(content_parses, key=lambda p: -len(p[1]))[0]
    L, R, init, fin, n = adjacency_for(tok)
    cls_whole = class_of(L, R, init, fin, n)
    L2, R2, init2, fin2, n2 = adjacency_for(clitic)
    cls_clitic = class_of(L2, R2, init2, fin2, n2)
    L3, R3, init3, fin3, n3 = adjacency_for(body)
    cls_body = class_of(L3, R3, init3, fin3, n3)
    test_pairs.append((tok, cls_whole, clitic, cls_clitic, body, cls_body))
    print(f"{tok:14s} {cls_whole or '-':12s}  {clitic:10s} {cls_clitic or '-':12s}  {body:10s} {cls_body or '-':12s}")

# Compositional hypothesis test:
# H_compositional: cls_whole == cls_clitic (whole behaves like its clitic head)
# H_lexical:       cls_whole determined independently (no relation to clitic class)
print(f"\nCompositional alignment (whole = clitic class): "
      f"{sum(1 for p in test_pairs if p[1]==p[3])}/{len(test_pairs)}")
print(f"Body alignment (whole = body class):           "
      f"{sum(1 for p in test_pairs if p[1]==p[5])}/{len(test_pairs)}")
