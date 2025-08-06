import { Search, Filter } from "lucide-react";
import { useMemo } from "react";
import { useStore } from "../store-simple";

export function Toolbar({
  pos, setPos, tier, setTier, search, setSearch, onClear, filteredPlayers
}:{
  pos:string; setPos:(p:string)=>void;
  tier:number|null; setTier:(n:number|null)=>void;
  search:string; setSearch:(s:string)=>void;
  onClear:()=>void;
  filteredPlayers: any[];  // Add prop for filtered players
}){
  const dense = useStore(s => s.dense);
  const setDense = useStore(s => s.actions.setDense);
  const total = useStore(s => s.players.length);
  const shown = useMemo(() => filteredPlayers.length, [filteredPlayers]);

  const POS = ["ALL","QB","RB","WR","TE","K","DST"];
  return (
    <div className="sticky top-[72px] z-30 -mx-4 border-b bg-white/85 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 py-3 flex flex-wrap items-center gap-2">
        {/* Position segmented control */}
        <div className="inline-flex rounded-full border-2 border-neutral-200 bg-neutral-50 p-1 shadow-sm">
          {POS.map(p=>(
            <button key={p}
              onClick={()=>setPos(p)}
              className={`px-4 py-2 text-sm font-semibold rounded-full transition-all duration-200 ${
                pos===p 
                  ? 'bg-indigo-600 text-white shadow-lg transform scale-105' 
                  : 'text-neutral-600 hover:text-neutral-900 hover:bg-white hover:shadow-md'
              }`}
            >{p}
            </button>
          ))}
        </div>

        {/* Tier filter */}
        <select value={tier ?? ""} onChange={e=>setTier(e.target.value?Number(e.target.value):null)}
          className="rounded-xl border-2 border-neutral-200 bg-white px-4 py-2.5 text-sm font-medium shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all">
          <option value="">All tiers</option>
          {[1,2,3,4,5,6].map(t=><option key={t} value={t}>Tier {t}</option>)}
        </select>

        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400"/>
          <input 
            id="global-search"
            value={search} 
            onChange={e=>setSearch(e.target.value)}
            placeholder="Search players (press /)"
            className="w-full rounded-xl border-2 border-neutral-200 bg-white pl-11 pr-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"/>
        </div>

        <button onClick={onClear}
          className="inline-flex items-center gap-2 rounded-xl border-2 border-neutral-200 px-4 py-2.5 text-sm font-medium hover:bg-neutral-50 transition-all shadow-sm">
          <Filter className="h-4 w-4"/> Clear
        </button>

        {/* Player count */}
        <div className="ml-2 text-xs text-neutral-500">{shown} of {total} players</div>

        {/* Density toggle */}
        <div className="ml-auto inline-flex items-center gap-2">
          <label className="text-xs text-neutral-600">Density</label>
          <button
            onClick={() => setDense(false)}
            className={`rounded-md border px-2 py-1 text-xs ${!dense ? 'bg-neutral-900 text-white' : 'bg-white'}`}>
            Comfort
          </button>
          <button
            onClick={() => setDense(true)}
            className={`rounded-md border px-2 py-1 text-xs ${dense ? 'bg-neutral-900 text-white' : 'bg-white'}`}>
            Compact
          </button>
        </div>
      </div>
    </div>
  );
}
