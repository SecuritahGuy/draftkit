
✅ Backend Roadmap — draftkid (nfl_data_py–first)

Goal: produce a rock-solid players.json/meta.json tailored to your Yahoo 12-team PPR snake league. Keep it local, reproducible, fast.

0) Repository hygiene (1x)
	•	Add pyproject.toml (editable install) so python -m draftkit works without PYTHONPATH.

[build-system]
requires = ["setuptools>=68","wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "draftkid"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.0","numpy>=1.24","PyYAML>=6.0","typer>=0.12.0",
  "rich>=13.0","nfl_data_py>=0.3.3","scikit-learn>=1.3","pyarrow>=14"
]

[tool.setuptools]
package-dir = {""="src"}
packages = ["draftkit"]

[project.scripts]
draftkit = "draftkit.cli:app"


	•	Install locally:

pip install -U pip && pip install -e .



DoD: python -m draftkit --help and draftkit --help both show the CLI.

⸻

1) Historical lookback + blended per-game projections (core)

Why: Stabilizes rankings; fixes odd VORP at QB.
CLI flags: --lookback 3 --blend 0.6,0.3,0.1 --per-game --min-games 8
	•	CLI: add options to src/draftkit/cli.py

@app.command()
def build(year: int = ..., config: Path = ..., outdir: Path = Path("public"),
          lookback: int = 1, blend: str = "", per_game: bool = True, min_games: int = 8, ...):
    # parse blend -> List[float]; derive years = [year-1 ...]


	•	Scoring: implement blending helpers in transforms/scoring.py

def to_season_points(weekly_df, cfg): ...  # current sum/row scoring
def to_season_ppg(weekly_df, cfg, min_games=8): ...
def blend_ppg(ppg_by_year: dict[int, pd.DataFrame], weights: list[float], season_len=17) -> pd.DataFrame:
    # align indices by player_id, weighted sum of PPG, then * season_len


	•	Aggregate logic in CLI:
	1.	Load each lookback season’s weekly; score per-game; filter < min_games.
	2.	Weighted blend → projected season points for target year.
	3.	Pass this single DataFrame to VORP/tiers.

DoD:
	•	Console shows per-position replacement lines that make sense.
	•	Top ~12 QBs have positive VORP (or near zero for QB12).
	•	README updated with example command.

⸻

2) Bye weeks

Why: Avoid bye clustering in snake.
	•	Connector: connectors/nflverse.py

def load_team_schedule(years: list[int]) -> pd.DataFrame: ...
def compute_bye_by_team(schedule_df: pd.DataFrame, year: int) -> dict[str,int]:
    # find week where team has 0 games; { "KC":10, ... }


	•	Merge into players in CLI after blending:

bye_by_tm = compute_bye_by_team(sched, target_year)
df['bye'] = df['team'].map(bye_by_tm)



DoD: Random spot-checks (KC, GB) show correct bye integer in players.json.

⸻

3) Overrides for rookies/role changes

Why: Blend undervalues rookies (MHJ, Caleb).
Format: overrides.csv → columns: player_id,name,pos,tm,points,note(optional)
	•	CLI flag: --overrides overrides.csv
	•	Merge after blending:

if overrides_path and overrides_path.exists():
    ov = pd.read_csv(overrides_path)
    df = df.drop(columns=['points']).merge(ov[['player_id','points']], on='player_id', how='left', suffixes=("","_ovr"))
    df['points'] = df['points_ovr'].fillna(df['points'])
    df['source'] = np.where(df['points_ovr'].notna(), 'override', 'blend')



DoD: Overridden players have source="override" and expected points.

⸻

4) DST scoring (league exact)

Why: You start a DEF; Yahoo bands matter.
	•	New module transforms/scoring_dst.py

def score_dst(weekly_team_df, league_cfg) -> pd.DataFrame:
    # aggregate team defense by season: sacks, ints, fr, tds, points_allowed
    # apply your scoring incl. PA bands to season totals
    # emit: player_id="DEF-<TEAM>", name="<TEAM> D/ST>", pos="DEF"


	•	Integrate into CLI path and include into VORP/tiers (separate positional baseline).

DoD: players.json includes DEF with plausible top-12.

⸻

5) K scoring (baseline, upgradeable)

Why: You start a K.
	•	New transforms/scoring_k.py

def score_kicker(weekly_k_df, league_cfg, granular: bool=False) -> pd.DataFrame:
    # baseline: FG=3, XP=1
    # if granular=True and splits exist, map 0–39=3, 40–49=4, 50+=5


	•	CLI flag: --k-distance-buckets

DoD: Ks appear with baseline values; flag flips to granular when data is present.

⸻

6) Replacement, VORP & tiers on the blended points

(You already have this—ensure it runs post-blend and includes DEF/K if present.)
	•	Confirm replacement counts: QB 12, RB 24, WR 24, TE 12 (+ FLEX reallocation).
	•	Ensure tier is deterministic (seed k-means), with quantile fallback.

DoD: Deterministic tiers between runs; FLEX allocation logged in console.

⸻

7) Diagnostics + caching + metadata
	•	Diagnostics (stdout): per-pos summary (count, replacement idx, baseline), top-12 table; warnings if anomalies.
	•	Cache: --cache data_cache/ → parquet by season for weekly & rosters (use pyarrow).
	•	Meta: write public/meta.json

{"generated_at":"...Z","target_year":2025,"lookback_years":[2024,2023,2022],
 "blend":[0.6,0.3,0.1],"per_game":true,"min_games":8,"schema_version":"0.1.0"}



DoD: Second run is much faster; meta.json exists and reflects flags.

⸻

✅ Frontend Roadmap — draftkid-ui (static GH Pages UI)

Goal: zero backend, load players.json/meta.json, give you a fast draft-day board: filters, tiers, bye visibility, queue, roster, pick tracker.

0) Bootstrap project (Vite React TS + Tailwind)
	•	Create app:

npm create vite@latest draftkid-ui -- --template react-ts
cd draftkid-ui
npm i zustand @tanstack/react-table @tanstack/react-virtual lucide-react classnames papaparse
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p


	•	Configure Tailwind
tailwind.config.js

export default { content: ["./index.html","./src/**/*.{ts,tsx}"], theme:{extend:{}}, plugins:[] }

src/index.css

@tailwind base;
@tailwind components;
@tailwind utilities;


	•	Vite base path for GH Pages
vite.config.ts

export default defineConfig({
  base: "/draftkid-ui/", // or your repo name
  plugins: [react()],
});



DoD: npm run dev renders a blank page with Tailwind styles.

⸻

1) Data contracts & types
	•	src/types.ts

export type Player = {
  player_id: string; name: string; pos: 'QB'|'RB'|'WR'|'TE'|'K'|'DEF';
  tm: string; points: number; vorp: number; pos_rank: number; overall_rank: number; tier: number;
  repl_pts: number; bye?: number; ppg?: number; gp?: number; stdev?: number;
  p10_share?: number; p15_share?: number; p20_share?: number;
  round_est?: number; pick_in_round?: number; source?: 'blend'|'override';
}
export type Meta = {
  generated_at?: string; target_year?: number; lookback_years?: number[];
  blend?: number[]; per_game?: boolean; min_games?: number; schema_version?: string;
}



DoD: Types compile.

⸻

2) Global state (Zustand) + localStorage persistence
	•	src/store.ts

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { Player, Meta } from './types'

type Filters = { pos:'ALL'|'QB'|'RB'|'WR'|'TE'|'K'|'DEF'; search:string; tier:number|null }

type DraftState = {
  players: Player[]; meta: Meta; filters: Filters;
  drafted: Record<string, boolean>; queue: string[]; mySlot: number | null;
  actions: {
    setPlayers(p: Player[]): void; setMeta(m: Meta): void;
    setFilters(patch: Partial<Filters>): void;
    toggleQueue(id: string): void; markDrafted(id: string, v?: boolean): void;
    setMySlot(n: number): void; importOverridesCsv(csv: string): Promise<void>;
    reset(): void;
  };
}

export const useStore = create<DraftState>()(persist((set,get)=>({
  players: [], meta: {}, filters:{pos:'ALL',search:'',tier:null},
  drafted: {}, queue: [], mySlot: null,
  actions: {
    setPlayers: (p)=> set({players:p}),
    setMeta: (m)=> set({meta:m}),
    setFilters: (patch)=> set({filters:{...get().filters,...patch}}),
    toggleQueue: (id)=> set(s => ({queue: s.queue.includes(id) ? s.queue.filter(x=>x!==id) : [...s.queue,id]})),
    markDrafted: (id, v)=> set(s => ({drafted:{...s.drafted, [id]: v ?? !s.drafted[id]}})),
    setMySlot: (n)=> set({mySlot:n}),
    importOverridesCsv: async (csv)=> { /* uses Papa.parse in UI action */ },
    reset: ()=> set({drafted:{}, queue:[], mySlot: null})
  }
}), { name:'draftkid:v0.1', storage: createJSONStorage(()=>localStorage) }))



DoD: State persists across reloads.

⸻

3) Data fetching hook
	•	src/hooks/usePlayers.ts

import { useEffect } from 'react'
import { useStore } from '../store'

export function usePlayers() {
  const { setPlayers, setMeta } = useStore(s=>s.actions)
  useEffect(()=>{
    let cancelled=false
    Promise.all([
      fetch('./players.json').then(r=>r.json()),
      fetch('./meta.json').then(r=>r.json()).catch(()=>({}))
    ]).then(([players,meta])=>{ if(!cancelled){ setPlayers(players); setMeta(meta) }})
    return ()=>{ cancelled=true }
  },[])
}



DoD: On page load, players/meta appear in state (log in devtools).

⸻

4) Header (filters + meta)
	•	src/components/Header.tsx
	•	Position filter (chips or select), search input, tier dropdown.
	•	Meta summary (target_year, lookback, blend).
	•	Keyboard shortcuts: / focuses search.

DoD: Filters update the table in real time.

⸻

5) Player Table (TanStack Table + react-virtual)
	•	src/components/PlayerTable.tsx
	•	Columns: overall_rank, ⭐ (queue index), name, pos, tm, bye, points, vorp, tier, source.
	•	Row actions: q to queue/unqueue; d to mark drafted.
	•	Virtualization with @tanstack/react-virtual.

// core setup (sketch)
const table = useReactTable({
  data: filteredPlayers,
  columns: [...],
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  state: { sorting },
  onSortingChange: setSorting,
})


	•	TierBadge.tsx (small colored pill), ByeBadge.tsx (warn if bye clash with roster later), OverrideBadge.tsx (OVR pill).

DoD: Table scrolls buttery smooth; sort by points/VORP/tier; queue/drafted actions work.

⸻

6) Right Rail: Roster + Queue + Pick Tracker
	•	src/lib/snake.ts

export const roundOf = (overall: number, teams=12) => Math.ceil(overall/teams)
export const pickInRound = (overall: number, teams=12) => ((overall-1)%teams)+1
export const nextPicksForSlot = (slot: number, currentOverall: number, teams=12) => {
  // compute your next two picks (snake): round parity flips order
}


	•	src/components/right-rail/Roster.tsx
	•	Show Starters (QB,RBx2,WRx2,TE,FLEX,K,DEF) + Bench; mark needs unfilled.
	•	src/components/right-rail/Queue.tsx
	•	Drag to reorder; show # index and quick remove.
	•	src/components/right-rail/PickTracker.tsx
	•	Input your draft slot (1..12); show next two pick numbers; when hovering a player row, show estimated round/pick.

DoD: You can set your slot, see next picks; hovering row shows round estimate.

⸻

7) Footer: import/export session
	•	import overrides.csv (optional) with PapaParse

import Papa from 'papaparse'
// parse -> produce override map -> apply to in-memory players, mark source='override'


	•	Export current session JSON (queue, drafted, slot) to a file for backup.

DoD: Importing overrides updates values live; exporting writes a JSON blob you can re-import later (stretch).

⸻

8) Visual polish & UX details
	•	Tier banding: light background stripes per tier in table.
	•	Bye indicator: ⚠️ on Right Rail if >2 starters share same bye.
	•	Icons: lucide-react (Star, Check, AlertCircle).
	•	Accessibility: focus states, row keyboard actions, aria labels.
	•	Color system: Tailwind classes; avoid red/green-only for color blindness (add icons/tooltips).

DoD: Clean, legible, keyboard-friendly UI that reads well in a dark room during the draft.

⸻

9) Build & Deploy to GitHub Pages
	•	Copy players.json + meta.json into draftkid-ui/public/ (or configure to fetch from repo root).
	•	Add GH Pages workflow:
.github/workflows/pages.yml

name: Deploy UI
on: { push: { branches: [ main ] } }
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with: { path: dist }
  deploy:
    needs: build
    permissions: { pages: write, id-token: write }
    environment: { name: github-pages, url: ${{ steps.deployment.outputs.page_url }} }
    runs-on: ubuntu-latest
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4


	•	Set vite.config.ts base to your pages path.

DoD: Site is live at https://github.com/<you>/<repo>/ pages URL and loads your JSON.

⸻

Optional “NEXT” Features (after Phase 1)

A) Consistency metrics display (PPG, stdev, 10+/15+/20+ shares)
	•	Backend: compute & export ppg, stdev, p10_share, p15_share, p20_share.
	•	UI: toggle columns; add tooltips (“% of weeks ≥ 15 pts in 2024–2022 blend”).

DoD: Columns show and sort; numbers match spot-checks.

B) Tier method toggle
	•	Backend: deterministic KMeans (seed) + quantile fallback; expose --tier-method kmeans|quantile, --tiers K.
	•	UI: dropdown to reflect tier method; badges update.

DoD: Same inputs → same tiers across runs.

C) CSV cheatsheets
	•	Backend: --csv-out public/cheatsheet_overall.csv and ..._pos.csv.
	•	UI: link to download these directly.

DoD: CSV sorted by overall and by position, opens clean in Sheets.

D) Run detector & stack hints
	•	UI only: If ≥3 picks of same position in last 6 drafted, show “RUN” chip.
	•	Stack hints: show QB+WR team stacks in Right Rail (toggle).

DoD: Visual cues help steer picks.

⸻

Suggested GitHub Issues (copy/paste)
	1.	feat(build): lookback blending (–lookback, –blend, –per-game, –min-games) and use projected season points
	2.	feat(data): attach team bye weeks and export "bye"
	3.	feat(scoring): add D/ST scoring with Yahoo PA bands
	4.	feat(scoring): add K scoring (baseline FG=3, XP=1; –k-distance-buckets)
	5.	feat(build): overrides.csv support for rookies/role changes
	6.	feat(build): diagnostics (pos summaries, replacement lines, top-12 preview)
	7.	feat(cache): parquet caching (–cache data_cache/)
	8.	feat(export): write public/meta.json
	9.	feat(ui): bootstrap draftkid-ui (Vite React TS + Tailwind + Zustand + TanStack Table + react-virtual)
	10.	feat(ui): header filters & meta summary
	11.	feat(ui): player table (virtualized) with tier/bye/override badges
	12.	feat(ui): right rail roster, queue, pick tracker (snake math)
	13.	feat(ui): import overrides.csv & export session
	14.	chore(ui): GH Pages deploy workflow

⸻

Quick Code Stubs You’ll Reuse

Pick math (src/lib/snake.ts)

export const roundOf = (overall: number, teams=12) => Math.ceil(overall/teams)
export const pickInRound = (overall: number, teams=12) => ((overall-1)%teams)+1
export function nextTwoPicks(slot: number, currentPick: number, teams=12) {
  const round = roundOf(currentPick, teams)
  const isOdd = round % 2 === 1
  const order = isOdd ? slot : (teams - slot + 1)
  const firstOverall = (round-1)*teams + order
  const secondOverall = (round)*teams + (isOdd ? (teams - slot +1) : slot)
  return [firstOverall, secondOverall]
}

Tier badge (TierBadge.tsx)

export default function TierBadge({ tier }: { tier: number }) {
  const colors = {1:'bg-indigo-500',2:'bg-blue-500',3:'bg-emerald-500',4:'bg-yellow-500',5:'bg-orange-500',6:'bg-red-500'}
  return <span className={`px-2 py-0.5 text-xs text-white rounded ${colors[tier]||'bg-gray-500'}`}>T{tier}</span>
}

Bye badge (ByeBadge.tsx)

export function ByeBadge({ bye }: { bye?: number }) {
  return <span className="text-xs text-gray-500">{bye ? `Bye ${bye}` : ''}</span>
}

Override pill (OverrideBadge.tsx)

export function OverrideBadge({ source }: { source?: string }) {
  if (source !== 'override') return null
  return <span className="px-1.5 py-0.5 text-[10px] rounded bg-purple-600 text-white">OVR</span>
}


⸻

If you want, I can also zip a starter draftkid-ui with the boilerplate scaffolding (store, hooks, header, stubbed table/rail) so you can jump straight into columns and styling. Otherwise, this roadmap should give you a crisp, box-checkable path from backend → UI → GH Pages. You’ve got this. 🚀