import { create } from 'zustand'
import type { Player, Meta } from './types'

type Filters = { 
  pos: 'ALL' | 'QB' | 'RB' | 'WR' | 'TE' | 'K' | 'DST'; 
  search: string; 
  tier: number | null;
}

type DraftState = {
  players: Player[];
  meta: Meta;
  filters: Filters;
  drafted: Record<string, boolean>;
  queue: string[];
  mySlot: number | null;
  dense: boolean;
  actions: {
    setPlayers(p: Player[]): void;
    setMeta(m: Meta): void;
    setFilters(patch: Partial<Filters>): void;
    toggleQueue(id: string): void;
    markDrafted(id: string, v?: boolean): void;
    setMySlot(n: number): void;
    setDense(v: boolean): void;
    importOverridesCsv(csv: string): Promise<void>;
    reset(): void;
  };
}

export const useStore = create<DraftState>()((set, get) => ({
  players: [],
  meta: {},
  filters: { pos: 'ALL', search: '', tier: null },
  drafted: {},
  queue: [],
  mySlot: null,
  dense: false,
  actions: {
    setPlayers: (p) => set({ players: p }),
    setMeta: (m) => set({ meta: m }),
    setFilters: (patch) => set({ filters: { ...get().filters, ...patch } }),
    toggleQueue: (id) => set((s) => ({
      queue: s.queue.includes(id) 
        ? s.queue.filter(x => x !== id) 
        : [...s.queue, id]
    })),
    markDrafted: (id, v) => set((s) => ({
      drafted: { ...s.drafted, [id]: v ?? !s.drafted[id] }
    })),
    setMySlot: (n) => set({ mySlot: n }),
    setDense: (v) => set({ dense: v }),
    importOverridesCsv: async (csv) => {
      // TODO: implement CSV parsing with Papa.parse
      console.log('CSV import not yet implemented:', csv);
    },
    reset: () => set({ drafted: {}, queue: [], mySlot: null })
  }
}))
