import { useStore } from '../../store-simple'
import { Trash2, GripVertical } from 'lucide-react'

export function Queue() {
  const players = useStore(s => s.players)
  const queue = useStore(s => s.queue)
  const drafted = useStore(s => s.drafted)
  const actions = useStore(s => s.actions)
  
  const queuedPlayers = queue
    .map(id => players.find(p => p.player_id === id))
    .filter(Boolean)
    .filter(p => !drafted[p!.player_id]) // Remove drafted players from queue view
  
  return (
    <section className="rounded-2xl border border-neutral-300 bg-white/90 backdrop-blur-sm p-6 shadow-xl">
      <h3 className="text-lg font-bold text-neutral-900 mb-5 border-b border-neutral-200 pb-3">Queue</h3>
      
      {queuedPlayers.length === 0 ? (
        <p className="text-sm text-neutral-600 text-center py-6 bg-neutral-50 rounded-xl border border-neutral-200">
          Star players to add them to your draft queue
        </p>
      ) : (
        <div className="space-y-3">
          {queuedPlayers.map((player, index) => (
            <div
              key={player!.player_id}
              className="group flex items-center gap-3 p-3 rounded-xl border border-neutral-200 hover:bg-blue-50/50 hover:border-blue-300 transition-all shadow-sm"
            >
              {/* Drag Handle */}
              <div className="text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity">
                <GripVertical className="h-4 w-4" />
              </div>
              
              {/* Queue Number */}
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-r from-blue-100 to-blue-200 text-blue-700 text-xs font-bold flex items-center justify-center border border-blue-300 shadow-sm">
                {index + 1}
              </div>
              
              {/* Player Info */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-neutral-900 truncate">
                  {player!.name}
                </div>
                <div className="flex items-center gap-2 text-xs mt-1">
                  <span className="rounded-lg bg-gradient-to-r from-neutral-100 to-neutral-200 px-2 py-0.5 text-[10px] font-bold text-neutral-800 uppercase tracking-wide border border-neutral-300 shadow-sm">
                    {player!.pos}
                  </span>
                  <span className="text-neutral-400">•</span>
                  <span className="text-neutral-600 font-medium">{player!.tm}</span>
                  <span className={`inline-flex items-center px-2 py-0.5 text-[10px] rounded-full text-white font-bold shadow-sm ${
                    player!.tier === 1 ? 'bg-gradient-to-r from-purple-500 to-purple-600' :
                    player!.tier === 2 ? 'bg-gradient-to-r from-blue-500 to-blue-600' :
                    player!.tier === 3 ? 'bg-gradient-to-r from-emerald-500 to-emerald-600' :
                    player!.tier === 4 ? 'bg-gradient-to-r from-amber-500 to-amber-600' :
                    player!.tier === 5 ? 'bg-gradient-to-r from-rose-500 to-rose-600' :
                    'bg-gradient-to-r from-gray-500 to-gray-600'
                  }`}>
                    T{player!.tier}
                  </span>
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
