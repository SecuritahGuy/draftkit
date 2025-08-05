
✅ 1) Historical lookback + blended per-game projections (fix QB VORP & stabilize ranks) - COMPLETED

Why: Use 2024/2023/2022 to project a single-season 2025 number that matches snake-draft value.
	•	CLI: --lookback 3 --blend 0.6,0.3,0.1 --per-game --min-games 8 ✅
	•	Output: Replace points with the blended 2025 projection (PPG×17). ✅
	•	Accept:
	•	Top QBs no longer have negative VORP; replacement baselines make sense by position. ✅
	•	Console prints per-position replacement line + top-12 preview. ✅

2) Bye weeks (export bye) - COMPLETED ✅

Why: Your roster has one FLEX and 6 bench; bye clustering matters.
	•	Output: Add bye to each player. ✅
	•	Accept: Spot-check a few teams; no missing byes for active players. ✅

3) DST scoring with Yahoo brackets (league exact)

Why: DEF matters in your lineup and Yahoo uses points-allowed bands + event scoring.
	•	Scope: Implement team-defense scoring from nflverse weekly (sacks, INT, FR, TD, PA).
	•	Output: Add pos="DEF", name=<TEAM>, points, vorp, tier.
	•	Accept: Top 12 DEF look reasonable; points-allowed bands match your rules.

4) Kicker scoring (practical baseline, upgrade when data allows)

Why: You start a K; your league awards 0–39=3, 40–49=4, 50+=5.
	•	Plan:
	•	If nflverse exposes FG distance buckets: use exact buckets.
	•	Else: start with flat FG=3 & XP=1 and gate distance scoring behind a flag --k-distance-buckets for later.
	•	Accept: K shows up with plausible ranks; distance buckets flip on cleanly when available.

5) Rookie & role-change overrides (fixes Caleb/MHJ undervaluation)

Why: Your blending undervalues rookies or new roles (no prior NFL PPG).
	•	Add: overrides.csv with columns: player_id,name,pos,tm,points (+ optional note).
	•	Merge after blending to set points for listed players.
	•	Accept: Known rookies (e.g., Marvin Harrison Jr.) reflect realistic draft value; export includes source="override".

6) Snake-draft helpers in export

Why: 12-team snake benefits from quick round targeting.
	•	Compute:
	•	round_est = ceil(overall_rank / 12)
	•	pick_in_round = ((overall_rank-1) % 12) + 1
	•	Accept: Fields present and correct for a handful of ranks.

✅ 7) Diagnostics & sanity checks (stdout) - COMPLETED

Why: Fast validation under a 60s clock.
	•	Print:
	•	Per-position: count, replacement index, baseline points. ✅
	•	Top-12 table (name, points, VORP, tier). ✅
	•	Warnings if replacement > top score or too few eligible players. (Basic validation included)
	•	Accept: Clear, colorized summary after build; non-fatal warnings. ✅

8) Parquet cache (--cache data_cache/)

Why: Rebuilds are instant on draft day.
	•	Accept: Second run with same flags is much faster; cache files per season exist.

⸻

NEXT — strategic clarity for your board

9) Consistency metrics

Why: Helps tie-break in snake: stable weekly floors.
	•	Export: gp, ppg, stdev, p10_share, p15_share, p20_share.
	•	Accept: Values present for offense positions and match manual checks.

10) Tiering polish & determinism

Why: You don’t want tiers bouncing run-to-run.
	•	Add: Seed KMeans; quantile fallback for small N; flags --tiers K and --tier-method kmeans|quantile.
	•	Accept: Same inputs → same tiers; tier count sensible per position.

11) CSV cheat sheets

Why: Quick import to spreadsheets / printouts.
	•	Add: --csv-out public/cheatsheet_overall.csv and ..._pos.csv with: name,pos,tm,points,vorp,tier,round_est,bye,ppg.
	•	Accept: Files generated, sorted as expected.

⸻

LATER — nice but not critical

12) QB negative stats policy (sacks taken, pick-six thrown)

Why: Your league penalizes both; open datasets rarely have QB-level sacks taken/pick-six thrown.
	•	Config: unknownStatPolicy: { sackTaken: "ignore|proxy", pickSixThrown: "ignore|rate" }
	•	proxy sacks: use team sacks allowed × QB snap share estimate.
	•	rate pick-six: INT × league pick-six rate (configurable).
	•	Accept: Policy toggles adjust QB points modestly; defaults remain ignore.

13) Strength of schedule (lite)

Why: Mild tie-breaker for starters/bench.
	•	Export: sos_rank computed from prior-year defensive vs position.

14) Docker + Makefile

Why: Reproducibility and quick CI builds.

⸻

Updated README example (after the NOW set)

python -m draftkit build \
  --year 2025 \
  --config config/league-settings.example.yml \
  --lookback 3 \
  --blend 0.6,0.3,0.1 \
  --per-game \
  --min-games 8 \
  --cache data_cache/ \
  --out public/players.json


⸻

Want me to start the first PR with items 1–5 + 7–8 (lookback/blend, bye weeks, DST, K baseline, overrides, diagnostics, cache)?

That package gives you league-accurate starters (incl. DEF/K), rookies fixed, and fast rebuilds—the biggest ROI for your draft. 🚀