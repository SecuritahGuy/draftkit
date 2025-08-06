import { useEffect } from 'react'
import { useStore } from '../store-simple'

export function usePlayers() {
  const actions = useStore(s => s.actions)
  
  useEffect(() => {
    let cancelled = false
    
    // Both dev and prod use the base path due to vite.config.ts base setting
    const basePath = '/draftkit'
    
    Promise.all([
      fetch(`${basePath}/players.json`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`)
        return r.json()
      }),
      fetch(`${basePath}/meta.json`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`)
        return r.json()
      }).catch(() => ({}))
    ]).then(([players, meta]) => {
      if (!cancelled) {
        actions.setPlayers(players)
        actions.setMeta(meta)
      }
    }).catch(error => {
      console.error('Failed to load player data:', error)
    })
    
    return () => {
      cancelled = true
    }
  }, [actions.setPlayers, actions.setMeta])
}
