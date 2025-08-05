import React from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  createColumnHelper,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Star, ChevronUp, ChevronDown } from 'lucide-react'
import type { Player } from '../types'
import { useStore } from '../store'
import { TierBadge, ByeChip, PosPill } from './ui'

const columnHelper = createColumnHelper<Player>()

// Helper function to format numbers with proper sign
const formatPoints = (value: number) => {
  return new Intl.NumberFormat('en', { 
    maximumFractionDigits: 1,
    minimumFractionDigits: 1 
  }).format(value)
}

const formatVORP = (value: number) => {
  const formatted = new Intl.NumberFormat('en', { 
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
    signDisplay: 'always' 
  }).format(value)
  return formatted
}

const formatRoundPick = (overallRank: number, numTeams = 12) => {
  // Calculate round and pick based on snake draft
  const round = Math.ceil(overallRank / numTeams)
  let pick: number
  
  if (round % 2 === 1) {
    // Odd rounds: pick increases normally
    pick = ((overallRank - 1) % numTeams) + 1
  } else {
    // Even rounds: pick reverses
    pick = numTeams - ((overallRank - 1) % numTeams)
  }
  
  return `R${round}P${pick}`
}

export function PlayerTable({ players }: { players: Player[] }) {
  const { queue, drafted, actions } = useStore()
  const [sorting, setSorting] = React.useState<SortingState>([])
  
  const columns = React.useMemo(
    () => [
      columnHelper.accessor('overall_rank', {
        header: '#',
        size: 50,
        cell: (info) => (
          <span className="text-neutral-500 text-right font-mono text-sm">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.display({
        id: 'queue',
        header: '⭐',
        size: 40,
        cell: (info) => {
          const player = info.row.original
          const isQueued = queue.includes(player.player_id)
          const queueIndex = queue.indexOf(player.player_id)
          
          return (
            <button
              onClick={() => actions.toggleQueue(player.player_id)}
              className={`rounded p-1 transition-colors ${
                isQueued 
                  ? 'text-yellow-500 hover:text-yellow-600' 
                  : 'text-neutral-400 hover:text-yellow-500'
              }`}
              title={isQueued ? `Queued #${queueIndex + 1}` : 'Add to queue'}
            >
              <Star className={`h-4 w-4 ${isQueued ? 'fill-current' : ''}`} />
            </button>
          )
        },
      }),
      columnHelper.accessor('name', {
        header: 'Player',
        size: 220,
        cell: (info) => {
          const player = info.row.original
          const isDrafted = drafted[player.player_id]
          
          return (
            <div className="flex items-center gap-2">
              <div>
                <div className={`font-medium ${isDrafted ? 'line-through opacity-50' : ''}`}>
                  {info.getValue()}
                </div>
                <div className="text-xs text-neutral-500 flex items-center gap-1">
                  <PosPill pos={player.pos} />
                  <span>•</span>
                  <span>{player.tm}</span>
                </div>
              </div>
            </div>
          )
        },
      }),
      columnHelper.accessor('bye', {
        header: 'Bye',
        size: 70,
        cell: (info) => <ByeChip week={info.getValue()} />,
      }),
      columnHelper.accessor('points', {
        header: 'Points',
        size: 80,
        cell: (info) => (
          <span className="text-right font-mono">
            {formatPoints(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor('vorp', {
        header: 'VORP',
        size: 80,
        cell: (info) => (
          <span className={`text-right font-mono ${
            info.getValue() > 0 ? 'text-emerald-600' : 'text-rose-600'
          }`}>
            {formatVORP(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor('tier', {
        header: 'Tier',
        size: 60,
        cell: (info) => <TierBadge tier={info.getValue()} />,
      }),
      columnHelper.accessor('overall_rank', {
        id: 'round_pick',
        header: 'Round',
        size: 80,
        cell: (info) => (
          <span className="text-xs text-neutral-600 font-mono">
            {formatRoundPick(info.getValue())}
          </span>
        ),
      }),
      columnHelper.display({
        id: 'actions',
        header: '',
        size: 80,
        cell: (info) => {
          const player = info.row.original
          const isDrafted = drafted[player.player_id]
          
          return (
            <button
              onClick={() => actions.markDrafted(player.player_id, true)}
              disabled={isDrafted}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                isDrafted
                  ? 'bg-neutral-200 text-neutral-500 cursor-not-allowed'
                  : 'bg-neutral-900 text-white hover:bg-neutral-800'
              }`}
            >
              {isDrafted ? 'Drafted' : 'Draft'}
            </button>
          )
        },
      }),
    ],
    [queue, drafted, actions]
  )

  const table = useReactTable({
    data: players,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  const { rows } = table.getRowModel()
  
  const parentRef = React.useRef<HTMLDivElement>(null)
  
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 52, // Fixed row height for smooth scrolling
    overscan: 10,
  })

  return (
    <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
      {/* Table Header */}
      <div className="sticky top-[120px] bg-white shadow-[inset_0_-1px_0_rgba(0,0,0,0.06)] z-20">
        {table.getHeaderGroups().map((headerGroup) => (
          <div key={headerGroup.id} className="flex">
            {headerGroup.headers.map((header) => (
              <div
                key={header.id}
                className="px-3 py-2.5 text-left text-xs font-semibold text-neutral-900 uppercase tracking-wider cursor-pointer hover:bg-neutral-50 transition-colors"
                style={{ width: header.getSize() }}
                onClick={header.column.getToggleSortingHandler()}
              >
                <div className="flex items-center gap-1">
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getIsSorted() && (
                    <span className="text-neutral-400">
                      {header.column.getIsSorted() === 'asc' ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Table Body */}
      <div
        ref={parentRef}
        className="overflow-auto"
        style={{ height: '600px' }}
      >
        <div style={{ height: virtualizer.getTotalSize() }}>
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index]
            const player = row.original
            const isDrafted = drafted[player.player_id]
            const isQueued = queue.includes(player.player_id)
            
            return (
              <div
                key={row.id}
                className={`absolute w-full flex items-center transition-colors ${
                  isDrafted 
                    ? 'opacity-40' 
                    : virtualRow.index % 2 === 0 
                      ? 'bg-white hover:bg-neutral-100/60' 
                      : 'bg-neutral-50 hover:bg-neutral-100/60'
                } ${isQueued ? 'border-l-4 border-indigo-600' : ''}`}
                style={{
                  height: virtualRow.size,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <div
                    key={cell.id}
                    className="px-3 py-2.5 text-sm"
                    style={{ width: cell.column.getSize() }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
