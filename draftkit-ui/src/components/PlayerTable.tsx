import { useState } from 'react'
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
function rowClassnames(row: Row<Player>, queueIds: string[]) {
  const queued = queueIds.includes(row.original.player_id);
  // Since drafted players are filtered out, we don't need drafted styling here
  return [
    "tr-row odd:bg-white even:bg-neutral-50 hover:bg-neutral-100/70 transition-colors",
    queued && "border-l-4 border-indigo-600 bg-indigo-50/30"
  ].filter(Boolean).join(" ");
}

export function PlayerTable({ players }: { players: Player[] }) {
  const queue = useStore(s => s.queue)
  const dense = useStore(s => s.dense)
  const actions = useStore(s => s.actions)
  const [sorting, setSorting] = useState<SortingState>([])

  const handlePlayerClick = (player: Player) => {
    // Toggle drafted status
    actions.markDrafted(player.player_id)
  }

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

  return (
    <div className="scroll-area overflow-auto">
      <table className="w-full min-w-[760px] border-separate border-spacing-0 table-sticky">
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header, i) => {
                const isFirst = i === 0;
                const isLast = i === headerGroup.headers.length - 1;
                const sticky = isFirst
                  ? 'sticky left-0 z-10 bg-white'
                  : isLast
                  ? 'sticky right-0 z-10 bg-white'
                  : '';

                const sortState = header.column.getIsSorted();
                const ariaSort =
                  sortState === 'asc'
                    ? 'ascending'
                    : sortState === 'desc'
                    ? 'descending'
                    : 'none';

                return (
                  <th
                    key={header.id}
                    scope="col"
                    aria-sort={ariaSort as any}
                    className={`px-3 py-3 text-left text-xs font-bold uppercase tracking-wider text-neutral-700 cursor-pointer hover:bg-neutral-50 transition-colors ${sticky} ${
                      header.column.columnDef.meta?.className || ''
                    } ${
                      header.column.columnDef.meta?.thClass || ''
                    }`}
                    style={{ width: header.getSize() }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div
                      className={`flex items-center gap-2 ${
                        header.column.columnDef.meta?.className?.includes('text-right')
                          ? 'justify-end'
                          : ''
                      }`}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {sortState && (
                        <span className="text-indigo-600">
                          {sortState === 'asc' ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody data-density={dense ? 'compact' : undefined}>
          {rows.map(row => (
            <tr
              key={row.id}
              className={rowClassnames(row, queue)}
              onClick={(e) => {
                const el = e.target as HTMLElement;
                if (el.closest('button, a, [data-no-row-click]')) return; // let inner controls handle their own clicks
                handlePlayerClick(row.original);
              }}
              style={{ cursor: 'pointer' }}
            >
              {row.getVisibleCells().map((cell, i) => {
                const isFirst = i === 0;
                const isLast = i === row.getVisibleCells().length - 1;
                const sticky = isFirst
                  ? 'sticky left-0 z-10 bg-white'
                  : isLast
                  ? 'sticky right-0 z-10 bg-white'
                  : '';
                const val = cell.getValue() as any;
                const isNumeric = typeof val === 'number';
                return (
                  <td
                    key={cell.id}
                    className={`px-3 py-2.5 align-middle ${isNumeric ? 'text-right num' : ''} ${sticky} ${
                      cell.column.columnDef.meta?.tdClass || ''
                    }`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
