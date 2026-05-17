#!/usr/bin/env python3
"""
Voynichese Register Grammar — full scope
========================================
Builds: section × content-root × vowel-grade × suffix-axis distribution table
Inputs: /mnt/project/ZL3b-n + /mnt/project/voynich_folio_profile.csv
Output: CSVs + console summary.

Tokenizer v4 baseline (per project memory):
  - read <fNNNa.line,locus>  lines only
  - drop comment lines starting with #
  - split tokens on .  and  ,
  - strip <...> tags inline
  - strip [a:b] alternates → take first reading 'a'
  - drop ? tokens
  - drop *, !, %, =, $ markers
  - keep alphabetic eva tokens
"""
import re
import csv
import sys
from collections import defaultdict, Counter

ZL = "/mnt/project/ZL3b-n"
PROFILE = "/mnt/project/voynich_folio_profile.csv"
OUTDIR = "/home/claude"

# ---------- 1. Load section labels per folio ----------
folio_section = {}
with open(PROFILE) as f:
    reader = csv.DictReader(f)
    for row in reader:
        folio_section[row["folio"].strip()] = row["section"].strip()

# Treat cosmo and cosmo/zodiac as one bucket for register work; keep zodiac separate later if needed
def norm_section(s):
    if s == "cosmo": return "cosmo/zodiac"
    return s

# ---------- 2. Parse ZL3b-n into (folio, section, tokens) ----------
folio_re = re.compile(r"^<f(\d+[rv]\d*)\.")   # folio identifier including subpage digit
# Drop inline tags <...>, locus markers, alt brackets etc.
tag_re = re.compile(r"<[^>]*>")
alt_re = re.compile(r"\[([^:\]]+):[^\]]*\]")     # [a:b] → a
misc_chars = re.compile(r"[%!$=*]")

def clean_token(tok):
    tok = tag_re.sub("", tok)
    tok = alt_re.sub(r"\1", tok)
    tok = misc_chars.sub("", tok)
    tok = tok.strip()
    if not tok:
        return None
    if "?" in tok:
        return None
    if not re.match(r"^[a-z]+$", tok):
        return None
    return tok

tokens_by_folio_section = defaultdict(list)
current_folio = None
with open(ZL) as f:
    for line in f:
        if line.startswith("#"): continue
        m = folio_re.match(line)
        if not m:
            # folio-header lines like <f1r>   <! ... > — just set current folio, no tokens
            mh = re.match(r"^<(f\d+[rv]\d*)>", line)
            if mh:
                current_folio = mh.group(1)
            continue
        current_folio = "f" + m.group(1)
        # text portion after first whitespace block
        # strip locus and leading <tag>
        text = line.split(">", 1)[1] if ">" in line else line
        # remove all tags
        text = tag_re.sub("", text)
        # remove alt brackets keeping first reading
        text = alt_re.sub(r"\1", text)
        text = misc_chars.sub("", text)
        # tokenize on . , whitespace
        raw = re.split(r"[.,\s]+", text)
        for tok in raw:
            ct = clean_token(tok)
            if ct:
                section = norm_section(folio_section.get(current_folio, "unknown"))
                tokens_by_folio_section[(current_folio, section)].append(ct)

# ---------- 3. Aggregate tokens per section ----------
section_tokens = defaultdict(list)
for (folio, section), toks in tokens_by_folio_section.items():
    section_tokens[section].extend(toks)

total_tokens = sum(len(v) for v in section_tokens.values())
print(f"TOTAL TOKENS (post tokenizer v4): {total_tokens}")
for s, t in sorted(section_tokens.items(), key=lambda x: -len(x[1])):
    print(f"  {s:20s}  {len(t):7d}")

# ---------- 4. Define the architecture ----------
# Content roots: 2 humor bases + 4 process bases
HUMOR_BASES = ["ch", "sh"]
PROCESS_BASES = ["qok", "qot", "ok", "ot"]
ALL_BASES = HUMOR_BASES + PROCESS_BASES

# Vowel grades: ∅ | e | o | eo applied to base
# Detection: after stripping derivational prefixes (k|d|t|ok|ot|qok|qot|cth), test for:
#   bare:  base + suffix  (e.g. ch + or = chor)
#   e:     base + 'e' + suffix  (e.g. ch + e + dy = chedy)
#   o:     base + 'o' + suffix  (e.g. ch + o + r = chor)
#   eo:    base + 'eo' + suffix (e.g. ch + eo + l = cheol)
# We'll identify which vowel-grade is in a token by infix detection AFTER prefix stripped.

# Derivational prefixes for HUMOR bases only (process roots don't take them)
HUMOR_PREFIXES = ["cth", "qok", "qot", "ok", "ot", "ch", "sh", "kch", "ksh", "dch", "dsh", "tch", "tsh", "k", "d", "t"]
# We'll detect prefix by greedy longest match before the base.

# Suffix axes — 5 dimensions, classify each token's tail
SUFFIX_AXES = {
    "e_grade":     [r"^$", r"^y$", r"^ey$"],          # ∅ | -y | -ey
    "o_grade":     [r"^r$", r"^l$", r"^or$", r"^ol$"], # quality-axis suffix after o/eo grade (also bare base)
    "aspect":      [r"^dy$", r"^edy$", r"^eedy$", r"^eey$", r"^ody$", r"^eody$"],
    "paradigm":    [r"^aiin$", r"^ain$", r"^aiir$", r"^air$"],
    "clitic":      [r"^ar$", r"^al$", r"^am$", r"^an$"],
}

# Build precise vowel-grade detector
def detect_vowel_grade(stem_after_prefix, base):
    """Return (vowel_grade, suffix) given residue after prefix-strip.
       residue must START with base. Returns None if not parseable."""
    if not stem_after_prefix.startswith(base):
        return None
    rest = stem_after_prefix[len(base):]
    # try eo first (longest)
    if rest.startswith("eo"):
        return ("eo", rest[2:])
    if rest.startswith("e"):
        return ("e", rest[1:])
    if rest.startswith("o"):
        return ("o", rest[1:])
    return ("bare", rest)

def classify_suffix(suf):
    for axis, patterns in SUFFIX_AXES.items():
        for p in patterns:
            if re.match(p, suf):
                return (axis, suf)
    if suf == "":
        return ("bare_suffix", "")
    return ("other", suf)

def parse_token(tok):
    """Try to parse a token as PREFIX + BASE + VOWEL_GRADE + SUFFIX for each base.
       Return all valid parses (token may match more than one base; we'll prefer humor
       bases over process bases when ambiguous, and longest prefix)."""
    parses = []
    # Try humor bases with prefixes
    for base in HUMOR_BASES:
        # try every prefix (sorted longest first) + no prefix
        prefixes = sorted(HUMOR_PREFIXES, key=lambda x: -len(x)) + [""]
        for pre in prefixes:
            if tok.startswith(pre):
                residue = tok[len(pre):]
                vg = detect_vowel_grade(residue, base)
                if vg is not None:
                    grade, suf = vg
                    parses.append({
                        "base": base,
                        "prefix": pre,
                        "grade": grade,
                        "suffix": suf,
                        "kind": "humor"
                    })
                    break  # only longest matching prefix per base
    # Try process bases (no prefix system)
    for base in PROCESS_BASES:
        vg = detect_vowel_grade(tok, base)
        if vg is not None:
            grade, suf = vg
            # but make sure we don't double-count when prefix-stripping has already given this
            parses.append({
                "base": base,
                "prefix": "",
                "grade": grade,
                "suffix": suf,
                "kind": "process"
            })
    return parses

def best_parse(parses):
    """Tie-breaker: prefer humor parses, prefer no-prefix if base is process root,
       prefer longest prefix for humor."""
    if not parses:
        return None
    # If only one parse, use it
    if len(parses) == 1:
        return parses[0]
    # Prefer parses whose suffix is in a known axis
    def suffix_known(p):
        axis, _ = classify_suffix(p["suffix"])
        return axis != "other"
    known = [p for p in parses if suffix_known(p)]
    pool = known if known else parses
    # Within pool, prefer humor over process
    humor = [p for p in pool if p["kind"] == "humor"]
    if humor:
        # Among humor, longest prefix wins (most specific decomposition)
        humor.sort(key=lambda p: -len(p["prefix"]))
        return humor[0]
    return pool[0]

# ---------- 5. Build the full register grid ----------
# Grid: [section][base][grade][axis][specific_suffix] = count
grid = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(Counter))))
# Token totals per section/base for normalization
base_totals = defaultdict(lambda: defaultdict(int))
section_totals = Counter()

unparsed = Counter()

for section, toks in section_tokens.items():
    section_totals[section] = len(toks)
    for tok in toks:
        parses = parse_token(tok)
        bp = best_parse(parses)
        if bp is None:
            unparsed[tok] += 1
            continue
        axis, specific = classify_suffix(bp["suffix"])
        grid[section][bp["base"]][bp["grade"]][axis][specific] += 1
        base_totals[section][bp["base"]] += 1

# ---------- 6. Emit summary CSV: section × base × grade ----------
out1 = OUTDIR + "/register_grid_grade.csv"
with open(out1, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["section", "base", "kind", "grade",
                "count", "pct_of_base_in_section",
                "pct_of_section"])
    for section in sorted(section_totals):
        for base in ALL_BASES:
            kind = "humor" if base in HUMOR_BASES else "process"
            btot = base_totals[section][base]
            if btot == 0: continue
            for grade in ["bare", "e", "o", "eo"]:
                c = sum(sum(v.values()) for v in grid[section][base][grade].values())
                pct_base = 100*c/btot if btot else 0
                pct_sec = 100*c/section_totals[section] if section_totals[section] else 0
                w.writerow([section, base, kind, grade, c,
                            f"{pct_base:.2f}", f"{pct_sec:.2f}"])

print(f"\nWrote {out1}")

# ---------- 7. Emit suffix-axis CSV: section × base × grade × axis ----------
out2 = OUTDIR + "/register_grid_axis.csv"
with open(out2, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["section", "base", "grade", "suffix_axis",
                "count", "pct_of_base_grade"])
    for section in sorted(section_totals):
        for base in ALL_BASES:
            for grade in ["bare", "e", "o", "eo"]:
                bg_total = sum(sum(v.values()) for v in grid[section][base][grade].values())
                if bg_total == 0: continue
                for axis in list(SUFFIX_AXES.keys()) + ["bare_suffix", "other"]:
                    c = sum(grid[section][base][grade][axis].values())
                    if c == 0: continue
                    w.writerow([section, base, grade, axis, c,
                                f"{100*c/bg_total:.2f}"])
print(f"Wrote {out2}")

# ---------- 8. Emit full specific-suffix CSV ----------
out3 = OUTDIR + "/register_grid_specific.csv"
with open(out3, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["section", "base", "grade", "axis", "specific_suffix", "count"])
    for section in sorted(section_totals):
        for base in ALL_BASES:
            for grade in ["bare", "e", "o", "eo"]:
                for axis, sufs in grid[section][base][grade].items():
                    for suf, c in sufs.items():
                        w.writerow([section, base, grade, axis, suf, c])
print(f"Wrote {out3}")

# ---------- 9. Console: register-axis ratio matrix ----------
print("\n" + "="*70)
print("E:(O+EO) RATIO MATRIX — register-axis fingerprint per (section, root)")
print("="*70)
print(f"{'section':20s} " + " ".join(f"{b:>8s}" for b in ALL_BASES))
for section in sorted(section_totals):
    row = [f"{section:20s}"]
    for base in ALL_BASES:
        bare = sum(sum(v.values()) for v in grid[section][base]["bare"].values())
        e    = sum(sum(v.values()) for v in grid[section][base]["e"].values())
        o    = sum(sum(v.values()) for v in grid[section][base]["o"].values())
        eo   = sum(sum(v.values()) for v in grid[section][base]["eo"].values())
        denom = o + eo
        if denom == 0:
            ratio = float("inf") if e > 0 else 0
            cell = f"{e:>4d}/0  "
        else:
            ratio = e/denom
            cell = f"{ratio:>8.2f}"
        row.append(cell)
    print(" ".join(row))

print("\n" + "="*70)
print("PARSE COVERAGE PER SECTION")
print("="*70)
for section in sorted(section_totals):
    parsed = sum(base_totals[section][b] for b in ALL_BASES)
    pct = 100*parsed/section_totals[section] if section_totals[section] else 0
    print(f"  {section:20s}  {parsed:6d}/{section_totals[section]:6d}  ({pct:5.1f}%)")

print(f"\nTotal unparsed-by-architecture types: {len(unparsed)}")
print(f"Top unparsed tokens (function words + non-architecture content):")
for tok, c in unparsed.most_common(20):
    print(f"  {tok:15s}  {c}")
