import { useMemo } from 'react'
import { useStore } from '../store-simple'
import type { Player } from '../types'

export function useFilteredPlayers(): Player[] {
  const players = useStore(s => s.players)
  const filters = useStore(s => s.filters)
  
  return useMemo(() => {
    return players.filter((player) => {
      // Position filter
      if (filters.pos !== 'ALL' && player.pos !== filters.pos) {
        return false
      }
      
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase()
        const nameMatch = player.name.toLowerCase().includes(searchLower)
        const teamMatch = player.tm.toLowerCase().includes(searchLower)
        const posMatch = player.pos.toLowerCase().includes(searchLower)
        if (!nameMatch && !teamMatch && !posMatch) {
          return false
        }
      }
      
      // Tier filter
      if (filters.tier !== null && player.tier !== filters.tier) {
        return false
      }
      
      return true
    })
  }, [players, filters])
}
