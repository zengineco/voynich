#!/usr/bin/env python3
"""
cth- botanical anchoring — Test 1
Pre-registered predictions:
 P1: Folios sharing dominant cth- form have closer morphological profiles
     (lower pairwise euclidean distance on standardized feature vectors)
     than folios with different dominants. Direction: positive.
 P2: At least one cth- form has a distinctive morphological signature
     (cthor- vs cthy- vs cthol-dominant folios differ on at least one
     marker at p<0.01, Kruskal-Wallis).
 P3: Falsification: if neither P1 nor P2 holds, Test 1 fails.

We use folio_profile.csv feature columns:
   C3suf_pct, C3pre_pct, C4pre_pct, chedy_k, chor_k, qok_k, aiin_k

Permutation null: shuffle dominant-form labels 5000x, recompute the within-group
vs between-group distance ratio. Report percentile of observed.

Kruskal-Wallis: for each feature, test if distributions differ across the
three viable groups (cthor, cthy, cthol). cthey excluded (n=8, low power),
but reported separately.
"""
import csv
import random
import statistics
import math
from collections import defaultdict

random.seed(42)

# Load morphological profile
profile = {}
features = ['C3suf_pct', 'C3pre_pct', 'C4pre_pct', 'chedy_k', 'chor_k', 'qok_k', 'aiin_k']
with open('folio_profile.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['section'] != 'herbal-A':
            continue
        profile[row['folio']] = {feat: float(row[feat]) for feat in features}

# Load cth- inventory (dominant_base column)
folio_dom = {}
with open('cth_inventory.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['dominant_base']:
            folio_dom[row['folio']] = row['dominant_base']

# Intersection: folios with profile AND dominant cth- form
data = [(f, folio_dom[f], profile[f]) for f in profile if f in folio_dom]
print(f"Herbal-A folios with both profile and dominant cth-: {len(data)}")

# Group by dominant form
groups = defaultdict(list)
for f, dom, prof in data:
    groups[dom].append((f, prof))
for dom in ['cthor', 'cthy', 'cthol', 'cthey']:
    print(f"  {dom}: n={len(groups[dom])}")
print()

# Standardize features across all folios (z-scores)
all_folios = list(profile.keys())
feat_mean = {}
feat_sd = {}
for feat in features:
    vals = [profile[f][feat] for f in all_folios]
    feat_mean[feat] = statistics.mean(vals)
    feat_sd[feat] = statistics.stdev(vals) if len(vals) > 1 else 1.0

def z_vector(prof):
    return [(prof[feat] - feat_mean[feat]) / (feat_sd[feat] if feat_sd[feat] > 0 else 1.0)
            for feat in features]

# Build z-vectors for the cth-folios subset
z_data = [(f, dom, z_vector(prof)) for f, dom, prof in data]

# Euclidean distance
def edist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# Within-group vs between-group mean distance
# Use only the three viable groups (cthor, cthy, cthol) for main test;
# cthey reported separately
viable_doms = {'cthor', 'cthy', 'cthol'}
viable = [(f, d, z) for f, d, z in z_data if d in viable_doms]
print(f"Folios in main test (cthor/cthy/cthol-dominant): {len(viable)}")

def within_between_ratio(items):
    """items: list of (folio, dom, zvec). Return mean_within / mean_between."""
    within_dists = []
    between_dists = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            d = edist(items[i][2], items[j][2])
            if items[i][1] == items[j][1]:
                within_dists.append(d)
            else:
                between_dists.append(d)
    mw = statistics.mean(within_dists) if within_dists else float('nan')
    mb = statistics.mean(between_dists) if between_dists else float('nan')
    return mw, mb, mw / mb if mb > 0 else float('nan')

mw, mb, ratio = within_between_ratio(viable)
print(f"\nObserved: mean within-group dist = {mw:.3f}")
print(f"Observed: mean between-group dist = {mb:.3f}")
print(f"Observed: within/between ratio = {ratio:.4f}")
print(f"  (ratio < 1 means within-group folios are MORE similar than between)")
print()

# Permutation null: shuffle dominant labels, recompute ratio
n_perm = 5000
labels = [d for _, d, _ in viable]
folio_zs = [(f, z) for f, _, z in viable]

null_ratios = []
for _ in range(n_perm):
    perm_labels = labels[:]
    random.shuffle(perm_labels)
    perm_items = [(folio_zs[i][0], perm_labels[i], folio_zs[i][1]) for i in range(len(viable))]
    _, _, r = within_between_ratio(perm_items)
    null_ratios.append(r)

null_ratios_sorted = sorted(null_ratios)
# Percentile of observed ratio (lower = more clustered)
n_below = sum(1 for r in null_ratios if r <= ratio)
percentile = n_below / n_perm * 100
print(f"Permutation null (n={n_perm}): observed ratio is at percentile {percentile:.2f}")
print(f"  p-value (one-tailed, ratio < null): {n_below / n_perm:.4f}")
print(f"  null mean ratio: {statistics.mean(null_ratios):.4f}")
print(f"  null sd: {statistics.stdev(null_ratios):.4f}")
print(f"  null 5th percentile: {null_ratios_sorted[int(0.05*n_perm)]:.4f}")
print()

# P2 test: Kruskal-Wallis for each feature across cthor/cthy/cthol groups
print("Kruskal-Wallis test per feature (groups: cthor, cthy, cthol):")
print(f"{'feature':<12} {'H':>8} {'df':>3} {'p':>10}")

def kruskal_wallis(groups_vals):
    """groups_vals: list of lists. Returns H statistic and approximate p."""
    all_vals = []
    for g in groups_vals:
        all_vals.extend(g)
    n = len(all_vals)
    # Rank all values together (average ranks for ties)
    sorted_idx = sorted(range(n), key=lambda i: all_vals[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and all_vals[sorted_idx[j + 1]] == all_vals[sorted_idx[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[sorted_idx[k]] = avg_rank
        i = j + 1
    # Sum of ranks per group
    pos = 0
    H = 0
    for g in groups_vals:
        ng = len(g)
        if ng == 0:
            continue
        r_sum = sum(ranks[pos:pos + ng])
        H += r_sum ** 2 / ng
        pos += ng
    H = (12.0 / (n * (n + 1))) * H - 3 * (n + 1)
    df = len(groups_vals) - 1
    # Approximate p-value using chi-square distribution
    # We'll compute using a simple chi2 survival approximation
    # via incomplete gamma function (use lookup for small df)
    return H, df

def chi2_p(x, df):
    """Approximate upper-tail p-value for chi-square."""
    # Use survival function via series for incomplete gamma
    # Wilson-Hilferty approximation for chi2 -> normal
    if x <= 0:
        return 1.0
    z = ((x / df) ** (1.0/3) - (1 - 2.0/(9*df))) / math.sqrt(2.0/(9*df))
    # Standard normal upper tail via erfc
    return 0.5 * math.erfc(z / math.sqrt(2))

for feat in features:
    g_cthor = [profile[f][feat] for f, d, _ in viable if d == 'cthor']
    g_cthy = [profile[f][feat] for f, d, _ in viable if d == 'cthy']
    g_cthol = [profile[f][feat] for f, d, _ in viable if d == 'cthol']
    H, df = kruskal_wallis([g_cthor, g_cthy, g_cthol])
    p = chi2_p(H, df)
    flag = ' ***' if p < 0.01 else (' **' if p < 0.05 else '')
    print(f"{feat:<12} {H:>8.3f} {df:>3d} {p:>10.4f}{flag}")
print()

# Per-group means for the features that show signal
print("Per-group feature means (cthor / cthy / cthol):")
print(f"{'feature':<12} {'cthor':>10} {'cthy':>10} {'cthol':>10}")
for feat in features:
    g_cthor = [profile[f][feat] for f, d, _ in viable if d == 'cthor']
    g_cthy = [profile[f][feat] for f, d, _ in viable if d == 'cthy']
    g_cthol = [profile[f][feat] for f, d, _ in viable if d == 'cthol']
    m_cthor = statistics.mean(g_cthor) if g_cthor else float('nan')
    m_cthy = statistics.mean(g_cthy) if g_cthy else float('nan')
    m_cthol = statistics.mean(g_cthol) if g_cthol else float('nan')
    print(f"{feat:<12} {m_cthor:>10.2f} {m_cthy:>10.2f} {m_cthol:>10.2f}")
print()

# cthey (small n=8 reported separately)
g_cthey_folios = [(f, prof) for f, dom, prof in data if dom == 'cthey']
print(f"cthey-dominant folios (n={len(g_cthey_folios)}, reported separately):")
for feat in features:
    vals = [prof[feat] for _, prof in g_cthey_folios]
    if vals:
        print(f"  {feat}: mean={statistics.mean(vals):.2f}, range=[{min(vals):.2f}, {max(vals):.2f}]")
