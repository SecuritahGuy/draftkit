import { useStore } from '../store-simple';

export const TierBadge = ({tier}:{tier:number}) => (
  <span className={`px-2 py-0.5 text-xs rounded-full text-white font-medium
    ${tier===1?'bg-indigo-600':tier===2?'bg-blue-600':
      tier===3?'bg-emerald-600':tier===4?'bg-amber-600':
      tier===5?'bg-orange-600':'bg-rose-600'}`}>T{tier}</span>
);

export const ByeChip = ({week}:{week?:number}) =>
  <span className="inline-flex items-center rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-700 font-medium">
    {week ? `Bye ${week}` : '—'}
  </span>;

export const PosPill = ({pos}:{pos:string}) =>
  <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] font-medium text-neutral-700">{pos}</span>;

export function QueueStar({id}:{id:string}) {
  const queue = useStore(s => s.queue)
  const actions = useStore(s => s.actions)
  const queued = queue.includes(id);
  const queueIndex = queue.indexOf(id);
  
  return (
    <button 
      aria-label={queued ? `Queued #${queueIndex + 1}` : 'Add to queue'}
      onClick={()=>actions.toggleQueue(id)}
      className={`rounded p-1 hover:bg-neutral-200 ${queued?'text-indigo-600':'text-neutral-400'}`}
    >
      {queued ? '★' : '☆'}
    </button>
  );
}

export function DraftButton({id}:{id:string}) {
  const drafted = useStore(s => s.drafted)
  const actions = useStore(s => s.actions)
  const isDrafted = drafted[id];
  
  return (
    <button 
      disabled={isDrafted} 
      onClick={()=>actions.markDrafted(id, !isDrafted)}
      className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors
        ${isDrafted ? 'bg-neutral-200 text-neutral-500 cursor-not-allowed'
                    : 'bg-neutral-900 text-white hover:bg-neutral-800 active:scale-[.99]'}`}
    >
      {isDrafted ? 'Drafted' : 'Draft'}
    </button>
  );
}
