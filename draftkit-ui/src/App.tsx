import { usePlayers } from './hooks/usePlayers'
import { useFilteredPlayers } from './hooks/useFilteredPlayers'
import { PlayerTable } from './components/PlayerTable'
import { PickTracker, Queue, Roster } from './components/right-rail'
import { useStore } from './store-simple'
import { AppShell } from './AppShell'
import { Toolbar } from './components/Toolbar'
import { Shortcuts } from './components/Shortcuts'

function App() {
  usePlayers() // Load player data on app start
  
  const players = useStore(s => s.players)
  const meta = useStore(s => s.meta)
  const filters = useStore(s => s.filters)
  const drafted = useStore(s => s.drafted)
  const actions = useStore(s => s.actions)
  const filteredPlayers = useFilteredPlayers()
  
  // Separate drafted and undrafted players
  const undraftedPlayers = filteredPlayers.filter(p => !drafted[p.player_id])
  const draftedPlayers = players.filter(p => drafted[p.player_id])
  
  const clearFilters = () => {
    actions.setFilters({ pos: 'ALL', search: '', tier: null })
  }
  
  return (
    <AppShell>
      <Shortcuts />
      <Toolbar 
        pos={filters.pos}
        setPos={(pos) => actions.setFilters({ pos: pos as any })}
        tier={filters.tier}
        setTier={(tier) => actions.setFilters({ tier })}
        search={filters.search}
        setSearch={(search) => actions.setFilters({ search })}
        onClear={clearFilters}
        filteredPlayers={filteredPlayers}
      />
      
      {/* Main content area */}
      <div className="col-span-12 lg:col-span-8 flex flex-col min-h-0 overflow-hidden">
        {/* Undrafted Players Section */}
        <div className="flex-1 min-h-0 flex flex-col">
          <div className="mb-6 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 tracking-tight">Available Players</h2>
              <p className="text-sm text-neutral-600 mt-1">
                Click any player to mark as drafted
                {meta.min_games && (
                  <span className="text-neutral-500"> • Min {meta.min_games} game{meta.min_games !== 1 ? 's' : ''}</span>
                )}
                {meta.per_game && (
                  <span className="text-neutral-500"> • Per game scoring</span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-neutral-700 bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200/50 px-4 py-2 rounded-xl font-medium shadow-sm">
                {undraftedPlayers.length} of {players.length} available
              </span>
            </div>
          </div>
          
          <div className="flex-1 min-h-0 rounded-xl border border-neutral-200/60 bg-white/90 backdrop-blur-sm shadow-lg flex flex-col overflow-hidden">
            <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain">
              {undraftedPlayers.length > 0 ? (
                <PlayerTable players={undraftedPlayers} />
              ) : (
                <div className="p-12 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-neutral-100 to-neutral-200 flex items-center justify-center">
                    <span className="text-2xl">🔍</span>
                  </div>
                  <p className="text-neutral-600 text-lg font-medium mb-2">No players match your filters</p>
                  <p className="text-neutral-500 text-sm">Try adjusting your position, tier, or search filters</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Drafted Players Section */}
        {draftedPlayers.length > 0 && (
          <div className="mt-6 flex-shrink-0">
            <div className="mb-4 flex justify-between items-center bg-gradient-to-r from-red-50 to-rose-50 rounded-xl border border-red-200/60 p-4 shadow-sm backdrop-blur-sm">
              <div>
                <h2 className="text-lg font-bold text-red-800 tracking-tight">Drafted Players</h2>
                <p className="text-sm text-red-600 mt-0.5">Click any player to undraft</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-red-700 bg-red-100/70 border border-red-200 px-3 py-1.5 rounded-lg font-medium">
                  {draftedPlayers.length} drafted
                </span>
                <button
                  onClick={() => draftedPlayers.forEach(p => actions.markDrafted(p.player_id, false))}
                  className="text-xs text-red-600 hover:text-red-800 underline font-medium hover:no-underline transition-all"
                >
                  Clear all
                </button>
              </div>
            </div>
            <div className="bg-gradient-to-br from-red-50/50 to-rose-50/30 backdrop-blur-sm rounded-xl border border-red-200/50 p-4 max-h-[25vh] overflow-y-auto shadow-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {draftedPlayers.map(player => (
                  <div
                    key={player.player_id}
                    className="flex items-center justify-between bg-white/90 backdrop-blur-sm rounded-lg border border-red-200/60 p-3 text-sm hover:bg-white hover:shadow-md hover:scale-[1.01] transition-all cursor-pointer group"
                    onClick={() => actions.markDrafted(player.player_id, false)}
                  >
                    <div>
                      <div className="font-semibold text-neutral-900 group-hover:text-red-700 transition-colors">{player.name}</div>
                      <div className="text-xs text-neutral-600 font-medium">{player.pos} • {player.tm}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-xs text-neutral-500">#{player.overall_rank}</div>
                      <div className="w-1.5 h-1.5 rounded-full bg-red-400 group-hover:bg-red-600 transition-colors"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right sidebar */}
      <aside className="col-span-12 lg:col-span-4 flex flex-col space-y-6 min-h-0 overflow-y-auto">
        <PickTracker />
        <Roster />
        <Queue />
      </aside>
    </AppShell>
  )
}

export default App
