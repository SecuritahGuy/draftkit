import { useStore } from '../../store'
import { PosPill, TierBadge } from '../ui'
import { Trash2, GripVertical } from 'lucide-react'

export function Queue() {
  const { players, queue, drafted, actions } = useStore()
  
  const queuedPlayers = queue
    .map(id => players.find(p => p.player_id === id))
    .filter(Boolean)
    .filter(p => !drafted[p!.player_id]) // Remove drafted players from queue view
  
  const movePlayer = (fromIndex: number, toIndex: number) => {
    const newQueue = [...queue]
    const [moved] = newQueue.splice(fromIndex, 1)
    newQueue.splice(toIndex, 0, moved)
    // Update queue order - we'll need to add this action to the store
    // For now, just toggle off and back on in new order
    actions.toggleQueue(moved)
    setTimeout(() => actions.toggleQueue(moved), 50)
  }
  
  return (
    <section className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-neutral-900 mb-3">Queue</h3>
      
      {queuedPlayers.length === 0 ? (
        <p className="text-xs text-neutral-500 text-center py-4">
          Star players to add them to your draft queue
        </p>
      ) : (
        <div className="space-y-2">
          {queuedPlayers.map((player, index) => (
            <div
              key={player!.player_id}
              className="group flex items-center gap-2 p-2 rounded-lg border hover:bg-neutral-50 transition-colors"
            >
              {/* Drag Handle */}
              <div className="text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity">
                <GripVertical className="h-3 w-3" />
              </div>
              
              {/* Queue Number */}
              <div className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-medium flex items-center justify-center">
                {index + 1}
              </div>
              
              {/* Player Info */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-neutral-900 truncate">
                  {player!.name}
                </div>
                <div className="flex items-center gap-1 text-xs">
                  <PosPill pos={player!.pos} />
                  <span className="text-neutral-500">•</span>
                  <span className="text-neutral-500">{player!.tm}</span>
                  <TierBadge tier={player!.tier} />
                </div>
              </div>
              
              {/* VORP */}
              <div className="text-xs font-mono text-right">
                <div className={`${
                  player!.vorp > 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}>
                  {player!.vorp > 0 ? '+' : ''}{player!.vorp.toFixed(1)}
                </div>
                <div className="text-neutral-500">#{player!.overall_rank}</div>
              </div>
              
              {/* Remove Button */}
              <button
                onClick={() => actions.toggleQueue(player!.player_id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-neutral-400 hover:text-rose-600 transition-all"
                title="Remove from queue"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
      
      {/* Queue Actions */}
      {queuedPlayers.length > 0 && (
        <div className="border-t pt-3 mt-3">
          <button
            onClick={() => queuedPlayers.forEach(p => actions.toggleQueue(p!.player_id))}
            className="w-full text-xs text-neutral-600 hover:text-neutral-900 transition-colors"
          >
            Clear queue
          </button>
        </div>
      )}
    </section>
  )
}
