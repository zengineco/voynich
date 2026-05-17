#!/usr/bin/env python3
"""
d-family unsupervised clustering.

Drop the 5-class scheme. Each d-form has a 9-dim feature vector:
  [init%, fin%, L_Ch%, L_Cp%, L_F%, R_Ch%, R_Cp%, R_F%, total_count_log]
Cluster d-forms by feature-vector similarity. See if natural groups emerge.
"""
import re, csv, math
from collections import defaultdict, Counter

# ===== reuse tokenization =====
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

def is_d_family(tok):
    if not tok.startswith("d"): return False
    if tok.startswith("dch") or tok.startswith("dsh"): return False
    return True

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

# Build features for all d-forms n>=8
d_total = Counter()
d_left = defaultdict(Counter); d_right = defaultdict(Counter)
d_init = Counter(); d_fin = Counter()
for _, _, toks in line_sequences:
    n = len(toks)
    for i, t in enumerate(toks):
        if not is_d_family(t): continue
        d_total[t] += 1
        if i == 0: d_init[t] += 1; d_left[t]["<LS>"] += 1
        else: d_left[t][tc(toks[i-1])] += 1
        if i == n-1: d_fin[t] += 1; d_right[t]["<LE>"] += 1
        else: d_right[t][tc(toks[i+1])] += 1

def pct(c, k):
    tot = sum(c.values()); return 100*c.get(k,0)/tot if tot else 0

# Build feature vectors
features = {}
for tok, n in d_total.items():
    if n < 8: continue
    features[tok] = {
        "init": 100*d_init[tok]/n,
        "fin": 100*d_fin[tok]/n,
        "L_Ch": pct(d_left[tok], "Ch"),
        "L_Cp": pct(d_left[tok], "Cp"),
        "L_F": pct(d_left[tok], "F"),
        "L_d": pct(d_left[tok], "d"),
        "R_Ch": pct(d_right[tok], "Ch"),
        "R_Cp": pct(d_right[tok], "Cp"),
        "R_F": pct(d_right[tok], "F"),
        "R_d": pct(d_right[tok], "d"),
        "n": n,
    }

print(f"d-forms with n>=8: {len(features)}")

# ===== Compute pairwise euclidean distance =====
FEAT_KEYS = ["init", "fin", "L_Ch", "L_Cp", "L_F", "L_d",
             "R_Ch", "R_Cp", "R_F", "R_d"]

def vec(tok):
    return [features[tok][k] for k in FEAT_KEYS]

def euclidean(v1, v2):
    return math.sqrt(sum((a-b)**2 for a, b in zip(v1, v2)))

tokens = sorted(features, key=lambda t: -features[t]["n"])
print("\nPairwise distance matrix (smaller = more similar):")
print(f"{'':12s} " + " ".join(f"{t[:10]:>10s}" for t in tokens))
for t1 in tokens:
    row = [f"{t1:12s}"]
    for t2 in tokens:
        d = euclidean(vec(t1), vec(t2))
        row.append(f"{d:>10.1f}")
    print(" ".join(row))

# ===== Single-linkage hierarchical clustering =====
print(f"\n{'='*70}")
print("HIERARCHICAL CLUSTERING (single-linkage, merge until distance > threshold)")
print(f"{'='*70}")
# Initialize each token in its own cluster
clusters = [[t] for t in tokens]
distances = {(t1, t2): euclidean(vec(t1), vec(t2))
             for t1 in tokens for t2 in tokens if t1 != t2}

def cluster_dist(c1, c2):
    return min(distances[(a, b)] for a in c1 for b in c2)

merge_log = []
while len(clusters) > 1:
    best = None
    best_d = float("inf")
    for i in range(len(clusters)):
        for j in range(i+1, len(clusters)):
            d = cluster_dist(clusters[i], clusters[j])
            if d < best_d:
                best_d = d
                best = (i, j)
    if best is None: break
    i, j = best
    merged = clusters[i] + clusters[j]
    merge_log.append((best_d, clusters[i], clusters[j], merged))
    clusters = [c for k, c in enumerate(clusters) if k != i and k != j]
    clusters.append(merged)

print(f"\nMerge history (distance, cluster1, cluster2):")
for d, c1, c2, m in merge_log:
    print(f"  d={d:>5.1f}  {sorted(c1)} + {sorted(c2)}")

# ===== Cut tree at meaningful threshold =====
# Find natural threshold: largest jump in merge distances
sorted_d = [d for d, _, _, _ in merge_log]
print(f"\nMerge distances: {[f'{d:.1f}' for d in sorted_d]}")
# Show clusters at each meaningful cut
print(f"\n{'='*70}")
print("CLUSTERS AT MULTIPLE THRESHOLDS")
print(f"{'='*70}")
for threshold in [20, 30, 40, 50, 60]:
    # Replay merges, stopping when d > threshold
    cur = [[t] for t in tokens]
    for d, c1, c2, m in merge_log:
        if d > threshold: break
        # find and merge
        cur = [c for c in cur if c != c1 and c != c2]
        cur.append(m)
    print(f"\nThreshold {threshold}: {len(cur)} clusters")
    for cl in sorted(cur, key=lambda c: -sum(d_total[t] for t in c)):
        total = sum(d_total[t] for t in cl)
        forms = ", ".join(f"{t}({d_total[t]})" for t in sorted(cl, key=lambda t: -d_total[t]))
        print(f"  [{total:>4d}]  {forms}")

# ===== Profile of natural clusters: what's their signature? =====
print(f"\n{'='*70}")
print("FINAL: 4 NATURAL CLUSTERS AT THRESHOLD ~40")
print(f"{'='*70}")
threshold = 40
cur = [[t] for t in tokens]
for d, c1, c2, m in merge_log:
    if d > threshold: break
    cur = [c for c in cur if c != c1 and c != c2]
    cur.append(m)

for cl in sorted(cur, key=lambda c: -sum(d_total[t] for t in c)):
    total = sum(d_total[t] for t in cl)
    forms = sorted(cl, key=lambda t: -d_total[t])
    print(f"\nCLUSTER (total {total} tokens): {[f for f in forms]}")
    # Average feature signature
    avg = {k: sum(features[t][k] for t in cl)/len(cl) for k in FEAT_KEYS}
    print(f"  Average signature:")
    print(f"    init={avg['init']:.1f}% fin={avg['fin']:.1f}%")
    print(f"    LEFT:  Ch={avg['L_Ch']:.1f}% Cp={avg['L_Cp']:.1f}% F={avg['L_F']:.1f}% d={avg['L_d']:.1f}%")
    print(f"    RIGHT: Ch={avg['R_Ch']:.1f}% Cp={avg['R_Cp']:.1f}% F={avg['R_F']:.1f}% d={avg['R_d']:.1f}%")
