import type { ColumnDef } from '@tanstack/react-table';
import type { Player } from '../types';
import { TierBadge, ByeChip, PosPill, DraftButton, QueueStar } from './cells';

const fmt = (n:number)=> new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(n);

// VORP cell with color coding
const VorpCell = ({v}:{v:number}) => (
  <div className={`num text-right ${v>0?'text-emerald-700':v<0?'text-rose-700':'text-neutral-700'}`}>
    {(v>=0?'+':'')}{new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(v)}
  </div>
);

// Header with tooltip
function HeaderWithTip({label, tip}:{label:string; tip:string}) {
  return (
    <div className="inline-flex items-center gap-1">
      <span>{label}</span>
      <span className="cursor-help text-neutral-400" title={tip}>ⓘ</span>
    </div>
  );
}

export const columns: ColumnDef<Player>[] = [
  { 
    header:'#', 
    accessorKey:'overall_rank',
    cell:({getValue}) => <div className="num text-right w-8">{getValue<number>()}</div>,
    size:48, 
    meta:{className:'text-right', thClass:'sticky left-0 z-10 bg-white', tdClass:'sticky left-0 z-10 bg-inherit'} 
  },

  { 
    header:'Name', 
    accessorKey:'name',
    cell:({row})=>(
      <div className="flex items-center gap-2 min-w-[220px]">
        <QueueStar id={row.original.player_id}/>
        <div className="flex-1">
          <div className="font-medium">{row.original.name}</div>
          <div className="text-xs text-neutral-500 flex items-center gap-1">
            <PosPill pos={row.original.pos}/> • {row.original.tm}
          </div>
        </div>
      </div>
    ), 
    size:320,
    meta:{thClass:'sticky left-12 z-10 bg-white', tdClass:'sticky left-12 z-10 bg-inherit'} 
  },

  { 
    header:'Bye', 
    accessorKey:'bye',
    cell:({getValue}) => <ByeChip week={getValue<number|undefined>()}/>,
    size:80,
    meta: { className: 'hidden sm:table-cell', thClass:'hidden sm:table-cell', tdClass:'hidden sm:table-cell' }
  },

  { 
    header:'Points', 
    accessorKey:'points',
    cell:({getValue}) => <div className="num text-right">{fmt(getValue<number>())}</div>,
    size:110, 
    meta:{className:'text-right'} 
  },

  { 
    header: () => <HeaderWithTip label="VORP" tip="Points above positional replacement (including FLEX allocation)." />, 
    accessorKey:'vorp',
    cell:({getValue}) => <VorpCell v={getValue<number>()}/>,
    size:110, 
    meta:{className:'text-right'} 
  },

  { 
    header:'Tier', 
    accessorKey:'tier',
    cell:({getValue}) => <TierBadge tier={getValue<number>()}/>,
    size:72 
  },

  { 
    header: () => <HeaderWithTip label="Round" tip="Estimated draft round and pick in 12-team league." />,
    accessorKey:'round_est',
    cell:({row}) => <div className="num text-xs text-right">
      R{row.original.round_est}P{row.original.pick_in_round}
    </div>, 
    size:90,
    meta: { className: 'text-right hidden sm:table-cell', thClass:'hidden sm:table-cell', tdClass:'hidden sm:table-cell' }
  },

  { 
    id:'draft', 
    header:'Draft',
    cell:({row}) => <DraftButton id={row.original.player_id}/>, 
    size:90 
  },
];
