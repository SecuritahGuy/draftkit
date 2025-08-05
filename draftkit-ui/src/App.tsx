import { usePlayers } from './hooks/usePlayers'
import { useFilteredPlayers } from './hooks/useFilteredPlayers'
import { Header, useKeyboardShortcuts } from './components/Header'
import { PlayerTable } from './components/PlayerTable'
import { PickTracker, Queue, Roster } from './components/right-rail'
import { useStore } from './store'

function App() {
  usePlayers() // Load player data on app start
  useKeyboardShortcuts() // Enable keyboard shortcuts
  
  const { players, meta } = useStore()
  const filteredPlayers = useFilteredPlayers()
  
  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <header className="border-b bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-2xl font-semibold tracking-tight">DraftKit</h1>
          <p className="mt-1 text-sm text-neutral-500">
            {meta.target_year || 2025} projections • {meta.lookback_years?.join('/') || '2024/23/22'} blend {meta.blend && `(${meta.blend.map(w => `${Math.round(w*100)}%`).join('/')})`}
          </p>
        </div>
      </header>
      
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Header />
        
        <div className="grid grid-cols-12 gap-6">
          {/* Main content area */}
          <div className="col-span-12 lg:col-span-8">
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Player Rankings</h2>
              <span className="text-sm text-neutral-500">
                {filteredPlayers.length} of {players.length} players
              </span>
            </div>
            
            {filteredPlayers.length > 0 ? (
              <PlayerTable players={filteredPlayers} />
            ) : (
              <div className="rounded-xl border bg-white p-6 shadow-sm">
                <p className="text-neutral-500 text-center">No players match your filters</p>
              </div>
            )}
          </div>

          {/* Right sidebar */}
          <aside className="col-span-12 lg:col-span-4 space-y-4">
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
