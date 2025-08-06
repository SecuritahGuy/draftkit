import React from 'react'
import { Search, Filter } from 'lucide-react'
import { useStore } from '../store-simple'

const positions = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST'] as const

export function Header() {
  const filters = useStore(s => s.filters)
  const actions = useStore(s => s.actions)
  
  const clearFilters = () => {
    actions.setFilters({ pos: 'ALL', search: '', tier: null })
  }
  
  return (
    <div className="sticky top-[89px] z-30 -mx-4 mb-6 border-b border-neutral-200 bg-white/95 backdrop-blur-sm px-6 py-6 shadow-sm">
      <div className="flex flex-col xl:flex-row xl:items-center gap-6">
        {/* Left side - Position filters */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-neutral-800 whitespace-nowrap">Position:</span>
          <div className="inline-flex rounded-xl border border-neutral-300 bg-neutral-50/80 p-1 shadow-sm">
            {positions.map(pos => (
              <button 
                key={pos}
                onClick={() => actions.setFilters({ pos })}
                className={`px-4 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 min-w-[52px] ${
                  filters.pos === pos
                    ? 'bg-blue-600 text-white shadow-lg transform scale-[1.02]' 
                    : 'text-neutral-700 hover:text-neutral-900 hover:bg-white hover:shadow-md'
                }`}
              >
                {pos}
              </button>
            ))}
          </div>
        </div>

        {/* Right side - Search and filters */}
        <div className="flex items-center gap-4 xl:ml-auto">
          {/* Tier filter */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-neutral-800 whitespace-nowrap">Tier:</span>
            <select 
              value={filters.tier || ''}
              onChange={(e) => actions.setFilters({ 
                tier: e.target.value ? parseInt(e.target.value) : null 
              })}
              className="rounded-xl border border-neutral-300 bg-white px-4 py-2.5 text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            >
              <option value="">All tiers</option>
              <option value="1">Tier 1</option>
              <option value="2">Tier 2</option>
              <option value="3">Tier 3</option>
              <option value="4">Tier 4</option>
              <option value="5">Tier 5</option>
              <option value="6">Tier 6</option>
            </select>
          </div>

          {/* Search */}
          <div className="relative flex items-center">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-500" />
            <input
              type="text"
              placeholder="Search players..."
              value={filters.search}
              onChange={(e) => actions.setFilters({ search: e.target.value })}
              className="w-72 rounded-xl border border-neutral-300 bg-white pl-11 pr-12 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  actions.setFilters({ search: '' })
                }
              }}
            />
            {filters.search && (
              <button
                onClick={() => actions.setFilters({ search: '' })}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-700 transition-colors"
              >
                ×
              </button>
            )}
          </div>

          {/* Clear filters */}
          <button 
            onClick={clearFilters}
            className="inline-flex items-center gap-2 rounded-xl border border-neutral-300 px-5 py-2.5 text-sm font-medium hover:bg-neutral-50 transition-all shadow-sm"
          >
            <Filter className="h-4 w-4" /> 
            Clear
          </button>
        </div>
      </div>
    </div>
  )
}

// Keyboard shortcut hook
export function useKeyboardShortcuts() {
  const actions = useStore(s => s.actions)
  
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
