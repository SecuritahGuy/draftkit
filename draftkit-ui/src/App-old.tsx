import { usePlayers } from './hooks/usePlayers'
import { useFilteredPlayers } from './hooks/useFilteredPlayers'
import { PlayerTable } from './components/PlayerTable'
import { PickTracker, Queue, Roster } from './components/right-rail'
import { useStore } from './store'
import { AppShell } from './AppShell'
import { Toolbar } from './components/Toolbar'

function App() {
  usePlayers() // Load player data on app start
  
  const { players, meta, filters, actions } = useStore()
  const filteredPlayers = useFilteredPlayers()
  
  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && e.target === document.body) {
        e.preventDefault()
        const searchInput = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement
        searchInput?.focus()
      }
    }
    
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])
  
  const clearFilters = () => {
    actions.setFilters({ pos: 'ALL', search: '', tier: null })
  }
  
  return (
    <AppShell>
      <Toolbar 
        pos={filters.pos}
        setPos={(pos) => actions.setFilters({ pos })}
        tier={filters.tier}
        setTier={(tier) => actions.setFilters({ tier })}
        search={filters.search}
        setSearch={(search) => actions.setFilters({ search })}
        onClear={clearFilters}
      />
      
      {/* Main content area */}
      <div className="col-span-12 lg:col-span-8">
        <div className="mb-6 flex justify-between items-center bg-white/80 backdrop-blur-sm rounded-2xl border border-neutral-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-neutral-900 tracking-tight">Player Rankings</h2>
          <div className="flex items-center gap-4">
            <span className="text-sm text-neutral-700 bg-neutral-100 px-3 py-1.5 rounded-full font-medium border border-neutral-200">
              {filteredPlayers.length} of {players.length} players
            </span>
          </div>
        </div>
            
            {filteredPlayers.length > 0 ? (
              <PlayerTable players={filteredPlayers} />
            ) : (
              <div className="rounded-xl border-2 border-neutral-200 bg-white p-8 shadow-lg text-center">
                <p className="text-neutral-500 text-lg font-medium">No players match your filters</p>
                <p className="text-neutral-400 text-sm mt-2">Try adjusting your position or tier filters</p>
              </div>
            )}
          </div>

          {/* Right sidebar */}
          <aside className="col-span-12 lg:col-span-4 space-y-6">
            <PickTracker />
            <Roster />
            <Queue />
          </aside>
        </div>
      </main>
    </div>
  )
}

export default App
