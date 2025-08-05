import React from 'react'
import { Search, Filter } from 'lucide-react'
import { useStore } from '../store'

const positions = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST'] as const

export function Header() {
  const { filters, actions } = useStore()
  
  const clearFilters = () => {
    actions.setFilters({ pos: 'ALL', search: '', tier: null })
  }
  
  return (
    <div className="sticky top-[73px] z-30 -mx-4 mb-6 border-b bg-white/80 backdrop-blur px-4">
      <div className="flex flex-wrap items-center gap-4 py-3">
        {/* Position segmented control */}
        <div className="inline-flex rounded-full border bg-neutral-50">
          {positions.map(pos => (
            <button 
              key={pos}
              onClick={() => actions.setFilters({ pos })}
              className={`px-3 py-1.5 text-sm font-medium rounded-full transition-all ${
                filters.pos === pos
                  ? 'bg-white shadow text-neutral-900' 
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              {pos}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative ml-auto w-full sm:w-80">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search players (⌘/)"
            value={filters.search}
            onChange={(e) => actions.setFilters({ search: e.target.value })}
            className="w-full rounded-md border bg-white pl-8 pr-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                actions.setFilters({ search: '' })
              }
            }}
          />
          {filters.search && (
            <button
              onClick={() => actions.setFilters({ search: '' })}
              className="absolute right-2 top-2.5 text-neutral-400 hover:text-neutral-600"
            >
              ×
            </button>
          )}
        </div>

        {/* Tier filter */}
        <select 
          value={filters.tier || ''}
          onChange={(e) => actions.setFilters({ 
            tier: e.target.value ? parseInt(e.target.value) : null 
          })}
          className="rounded-md border bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">All tiers</option>
          <option value="1">T1</option>
          <option value="2">T2</option>
          <option value="3">T3</option>
          <option value="4">T4</option>
          <option value="5">T5</option>
          <option value="6">T6</option>
        </select>

        {/* Clear/Reset */}
        <button 
          onClick={clearFilters}
          className="inline-flex items-center gap-1 rounded-md border px-3 py-2 text-sm hover:bg-neutral-50 transition-colors"
        >
          <Filter className="h-4 w-4" /> Clear filters
        </button>
      </div>
    </div>
  )
}

// Keyboard shortcut hook
export function useKeyboardShortcuts() {
  const { actions } = useStore()
  
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
  }, [actions])
}
