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
    <div className="col-span-12 sticky top-0 z-30 border-b border-neutral-200/60 bg-white/95 backdrop-blur-lg shadow-sm mb-8">
      <div className="px-6 py-5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Position segmented control */}
          <div className="inline-flex rounded-xl border border-neutral-200 bg-neutral-50/50 p-1 shadow-sm backdrop-blur-sm">
            {POS.map(p=>(
              <button key={p}
                onClick={()=>setPos(p)}
                className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                  pos===p 
                    ? 'bg-indigo-600 text-white shadow-md transform scale-[1.02]' 
                    : 'text-neutral-600 hover:text-neutral-900 hover:bg-white/70 hover:shadow-sm'
                }`}
              >{p}
              </button>
            ))}
          </div>

          {/* Tier filter */}
          <select value={tier ?? ""} onChange={e=>setTier(e.target.value?Number(e.target.value):null)}
            className="rounded-lg border border-neutral-200 bg-white/90 backdrop-blur-sm px-4 py-2.5 text-sm font-medium shadow-sm hover:shadow-md focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all">
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
              className="w-full rounded-lg border border-neutral-200 bg-white/90 backdrop-blur-sm pl-11 pr-4 py-2.5 text-sm shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all"/>
          </div>

          <button onClick={onClear}
            className="inline-flex items-center gap-2 rounded-lg border border-neutral-200 bg-white/90 backdrop-blur-sm px-4 py-2.5 text-sm font-medium hover:bg-neutral-50 hover:shadow-md transition-all shadow-sm">
            <Filter className="h-4 w-4"/> Clear
          </button>
        </div>

        <div className="flex items-center gap-6">
          {/* Player count */}
          <div className="text-sm text-neutral-600 font-medium bg-neutral-100/70 px-3 py-1.5 rounded-lg">
            {shown} of {total} players
          </div>

          {/* Density toggle */}
          <div className="inline-flex items-center gap-2 bg-neutral-50/50 rounded-lg p-1 border border-neutral-200">
            <span className="text-xs text-neutral-600 font-medium px-2">View</span>
            <button
              onClick={() => setDense(false)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                !dense ? 'bg-indigo-600 text-white shadow-sm' : 'text-neutral-600 hover:bg-white/70'
              }`}>
              Comfort
            </button>
            <button
              onClick={() => setDense(true)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                dense ? 'bg-indigo-600 text-white shadow-sm' : 'text-neutral-600 hover:bg-white/70'
              }`}>
              Compact
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
