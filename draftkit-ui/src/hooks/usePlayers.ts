import { useEffect } from 'react'
import { useStore } from '../store'

export function usePlayers() {
  const { setPlayers, setMeta } = useStore(s => s.actions)
  
  useEffect(() => {
    let cancelled = false
    
    Promise.all([
      fetch('./players.json').then(r => r.json()),
      fetch('./meta.json').then(r => r.json()).catch(() => ({}))
    ]).then(([players, meta]) => {
      if (!cancelled) {
        setPlayers(players)
        setMeta(meta)
      }
    }).catch(error => {
      console.error('Failed to load player data:', error)
    })
    
    return () => {
      cancelled = true
    }
  }, [setPlayers, setMeta])
}
