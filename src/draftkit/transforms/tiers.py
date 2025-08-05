from __future__ import annotations
from typing import List, Dict
import math
import numpy as np

def compute_replacement_and_vorp(players: List[Dict], cfg) -> List[Dict]:
    # Split by position
    by_pos = {}
    for p in players:
        by_pos.setdefault(p['pos'], []).append(p)
    # Determine replacement counts from roster settings
    teams = cfg.teams
    base_counts = {
        'QB': cfg.roster.get('QB', 1) * teams,
        'RB': cfg.roster.get('RB', 2) * teams,
        'WR': cfg.roster.get('WR', 2) * teams,
        'TE': cfg.roster.get('TE', 1) * teams,
    }
    # Allocate FLEX across RB/WR/TE by best available
    flex_slots = cfg.roster.get('FLEX', 0) * teams
    flex_pool = []
    for pos in cfg.flex_positions:
        for p in by_pos.get(pos, []):
            flex_pool.append(p)
    flex_pool.sort(key=lambda x: x['points'], reverse=True)
    # Count how many of the top N flex players belong to each pos
    flex_take = {'RB':0,'WR':0,'TE':0}
    for p in flex_pool[:flex_slots]:
        if p['pos'] in flex_take:
            flex_take[p['pos']] += 1
    # Final replacement counts
    repl_counts = {
        'QB': base_counts['QB'],
        'RB': base_counts['RB'] + flex_take['RB'],
        'WR': base_counts['WR'] + flex_take['WR'],
        'TE': base_counts['TE'] + flex_take['TE'],
    }
    # Compute replacement baselines and VORP
    for pos, plist in by_pos.items():
        plist.sort(key=lambda x: x['points'], reverse=True)
        n = repl_counts.get(pos, 0)
        idx = min(max(n-1, 0), len(plist)-1) if len(plist)>0 else 0
        baseline = plist[idx]['points'] if plist else 0.0
        for p in plist:
            p['repl_pts'] = baseline
            p['vorp'] = round(p['points'] - baseline, 2)
            p['pos_rank'] = 1 + plist.index(p)
    # Overall rank
    allp = [p for plist in by_pos.values() for p in plist]
    allp.sort(key=lambda x: x['points'], reverse=True)
    for i,p in enumerate(allp, start=1):
        p['overall_rank'] = i
    return allp

def add_tiers_kmeans(players: List[Dict], k: int = 6) -> List[Dict]:
    # Simple KMeans on VORP per position; fallback to quantile bins if too few samples
    try:
        from sklearn.cluster import KMeans
    except Exception:
        for p in players:
            p['tier'] = None
        return players

    by_pos = {}
    for p in players:
        by_pos.setdefault(p['pos'], []).append(p)

    for pos, plist in by_pos.items():
        if len(plist) < 8:
            # small set: 3 quantile tiers
            vals = np.array([p['vorp'] for p in plist])
            qs = np.quantile(vals, [0.33, 0.66])
            for p in plist:
                p['tier'] = 1 + int(p['vorp'] < qs[1]) + int(p['vorp'] < qs[0])
            continue
        X = np.array([[p['vorp']] for p in plist])
        kk = min(k, max(2, len(plist)//5))
        km = KMeans(n_clusters=kk, n_init='auto', random_state=42).fit(X)
        # Lower tier number = better (higher VORP)
        centers = km.cluster_centers_.flatten()
        order = np.argsort(-centers)  # descending
        label_to_tier = {int(lbl): int(i+1) for i,lbl in enumerate(order)}
        for p, lbl in zip(plist, km.labels_):
            p['tier'] = label_to_tier[int(lbl)]
    return players
