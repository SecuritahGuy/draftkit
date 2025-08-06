import { Fragment, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
  type Row,
} from '@tanstack/react-table'
import { ChevronUp, ChevronDown } from 'lucide-react'
import type { Player } from '../types'
import { useStore } from '../store-simple'
import { columns } from './columns'

// Row classnames helper
function rowClassnames(row: Row<Player>, queueIds: string[], draftedIds: Record<string, boolean>) {
  const queued = queueIds.includes(row.original.player_id);
  const drafted = draftedIds[row.original.player_id];
  return [
    "tr-row odd:bg-white even:bg-neutral-50 hover:bg-neutral-100/70 transition-colors",
    queued && "border-l-4 border-indigo-600 bg-indigo-50/30",
    drafted && "opacity-50 pointer-events-none"
  ].filter(Boolean).join(" ");
}

export function PlayerTable({ players }: { players: Player[] }) {
  const queue = useStore(s => s.queue)
  const drafted = useStore(s => s.drafted)
  const dense = useStore(s => s.dense)
  const [sorting, setSorting] = useState<SortingState>([])

  const table = useReactTable({
    data: players,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  const { rows } = table.getRowModel()

  // Loading skeleton
  if (players.length === 0) {
    return (
      <div className="card p-4">
        {Array.from({length:8}).map((_,i)=>(
          <div key={i} className="mb-2 h-9 animate-pulse rounded bg-neutral-200/70" />
        ))}
      </div>
    );
  }

  // Empty state
  if (rows.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-neutral-600">
        No players match your filters.
      </div>
    );
  }

  let prevTier: number | null = null;

  return (
    <div className="card overflow-hidden max-h-[70vh]">
      <div className="overflow-x-auto overflow-y-auto h-full">
        <table className="w-full min-w-[760px] border-separate border-spacing-0">
          <thead className="sticky top-0 z-20 bg-white sticky-head">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className={`px-3 py-3 text-left text-xs font-bold uppercase tracking-wider text-neutral-700 cursor-pointer hover:bg-neutral-50 transition-colors ${
                      header.column.columnDef.meta?.className || ''
                    } ${
                      header.column.columnDef.meta?.thClass || ''
                    }`}
                    style={{ width: header.getSize() }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className={`flex items-center gap-2 ${
                      header.column.columnDef.meta?.className?.includes('text-right') ? 'justify-end' : ''
                    }`}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() && (
                        <span className="text-indigo-600">
                          {header.column.getIsSorted() === 'asc' ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody data-density={dense ? 'compact' : undefined}>
            {rows.map(row => {
              const curTier = row.original.tier;
              const showTierHeader = curTier !== prevTier;
              prevTier = curTier;

              return (
                <Fragment key={`frag-${row.id}`}>
                  {showTierHeader && (
                    <tr className="sticky top-0 z-10">
                      <td colSpan={columns.length}
                          className="bg-neutral-100/80 backdrop-blur px-3 py-1.5 text-xs font-semibold text-neutral-600">
                        Tier {curTier}
                      </td>
                    </tr>
                  )}
                  <tr className={rowClassnames(row, queue, drafted)}>
                    {row.getVisibleCells().map(cell => (
                      <td 
                        key={cell.id} 
                        className={`px-3 py-2.5 align-middle ${
                          cell.column.columnDef.meta?.tdClass || ''
                        }`}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
