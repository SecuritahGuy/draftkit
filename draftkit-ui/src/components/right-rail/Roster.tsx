import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { useStore } from '../../store-simple'
import { PosPill } from '../ui/PosPill'

const starterSlots = [
  { pos: 'QB', count: 1 },
  { pos: 'RB', count: 2 },
  { pos: 'WR', count: 3 },
  { pos: 'TE', count: 1 },
  { pos: 'K', count: 1 },
  { pos: 'DST', count: 1 },
] as const

export function Roster() {
  const players = useStore(s => s.players)
  const drafted = useStore(s => s.drafted)
  const [expandedCollisions, setExpandedCollisions] = useState<Set<number>>(new Set())
  
  const draftedPlayers = players.filter(p => drafted[p.player_id])
  
  // Group by position for roster organization
  const byPosition = draftedPlayers.reduce((acc, player) => {
    if (!acc[player.pos]) acc[player.pos] = []
    acc[player.pos].push(player)
    return acc
  }, {} as Record<string, typeof draftedPlayers>)
  
  // Calculate needs
  const needs = starterSlots.map(slot => {
    const filled = byPosition[slot.pos]?.length || 0
    const needed = Math.max(0, slot.count - filled)
    return { ...slot, filled, needed }
  })
  
  // Calculate bye week collisions with player details
  const byeWeekGroups = draftedPlayers.reduce((acc, player) => {
    if (player.bye) {
      if (!acc[player.bye]) acc[player.bye] = []
      acc[player.bye].push(player)
    }
    return acc
  }, {} as Record<number, typeof draftedPlayers>)
  
  const byeCollisions = Object.entries(byeWeekGroups)
    .filter(([, players]) => players.length >= 3)
    .map(([bye, players]) => ({ bye: parseInt(bye), players }))
    .sort((a, b) => a.bye - b.bye)
  
  return (
    <section className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-neutral-900 mb-3">Your roster</h3>
      
      {/* Starters Grid */}
      <div className="space-y-2 mb-4">
        {starterSlots.map(slot => {
          const positionPlayers = byPosition[slot.pos] || []
          const slots = Array.from({ length: slot.count }, (_, i) => 
            positionPlayers[i] || null
          )
          
          return (
            <div key={slot.pos} className="text-xs">
              <div className="flex items-center justify-between mb-1">
                <PosPill pos={slot.pos} />
                <span className="text-neutral-500">{slot.count}</span>
              </div>
              
              <div className="space-y-1">
                {slots.map((player, i) => (
                  <div key={i} className={`px-2 py-1 rounded text-xs ${
                    player 
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
                      : 'bg-neutral-50 text-neutral-400 border border-dashed border-neutral-300'
                  }`}>
                    {player ? player.name : `${slot.pos} needed`}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Needs Summary */}
      <div className="border-t pt-3">
        <h4 className="text-xs font-medium text-neutral-700 mb-2">Immediate needs</h4>
        <div className="flex flex-wrap gap-1">
          {needs
            .filter(n => n.needed > 0)
            .map(need => (
              <span key={need.pos} className="inline-flex items-center gap-1 rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
                {need.pos} × {need.needed}
              </span>
            ))}
          {needs.every(n => n.needed === 0) && (
            <span className="text-xs text-neutral-500">All starter slots filled</span>
          )}
        </div>
      </div>
      
      {/* Bye Week Collisions */}
      {byeCollisions.length > 0 && (
        <div className="border-t pt-3 mt-3">
          <h4 className="text-xs font-medium text-rose-700 mb-2">⚠️ Bye week collisions</h4>
          <div className="space-y-2">
            {byeCollisions.map(({ bye, players }) => {
              const isExpanded = expandedCollisions.has(bye)
              return (
                <div key={bye} className="rounded bg-rose-50 border border-rose-200">
                  <button
                    onClick={() => {
                      const newExpanded = new Set(expandedCollisions)
                      if (isExpanded) {
                        newExpanded.delete(bye)
                      } else {
                        newExpanded.add(bye)
                      }
                      setExpandedCollisions(newExpanded)
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 text-xs text-rose-800 hover:bg-rose-100 transition-colors"
                  >
                    <span>Week {bye}: {players.length} players</span>
                    {isExpanded ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                  </button>
                  
                  {isExpanded && (
                    <div className="px-3 pb-2 space-y-1">
                      {players
                        .sort((a, b) => a.pos.localeCompare(b.pos))
                        .map(player => (
                          <div key={player.player_id} className="flex items-center justify-between text-xs text-rose-700 bg-white/60 rounded px-2 py-1">
                            <span className="truncate font-medium">{player.name}</span>
                            <div className="flex items-center gap-1">
                              <PosPill pos={player.pos} />
                              <span className="text-rose-500 text-xs">#{player.overall_rank}</span>
                            </div>
                          </div>
                        ))
                      }
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
      
      {/* Bench */}
      {draftedPlayers.length > 9 && (
        <div className="border-t pt-3 mt-3">
          <h4 className="text-xs font-medium text-neutral-700 mb-2">Bench</h4>
          <div className="space-y-1">
            {draftedPlayers.slice(9).map(player => (
              <div key={player.player_id} className="flex items-center justify-between text-xs">
                <span className="truncate">{player.name}</span>
                <PosPill pos={player.pos} />
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
