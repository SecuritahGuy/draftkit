import React from 'react';
import { useStore } from './store-simple';

export function AppShell({ children }: { children: React.ReactNode }) {
  const meta = useStore(s => s.meta);
  
  // Create blend description from meta data
  const createBlendDescription = () => {
    if (!meta.lookback_years || !meta.blend || !meta.target_year) {
      return "Loading projection data...";
    }
    
    if (meta.lookback_years.length === 1 && meta.blend[0] === 1.0) {
      return `${meta.target_year} projections • ${meta.lookback_years[0]} data (100%)`;
    }
    
    const blendPairs = meta.lookback_years.map((year, i) => 
      `${year} (${Math.round(meta.blend![i] * 100)}%)`
    );
    return `${meta.target_year} projections • ${blendPairs.join('/')} blend`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-white to-indigo-50/30 text-neutral-900 flex flex-col">
      <header className="border-b border-neutral-200/50 bg-white/80 backdrop-blur-xl shadow-sm flex-shrink-0">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-neutral-900">
                <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
                  DraftKit
                </span>
              </h1>
              <p className="mt-1 text-sm text-neutral-600 font-medium">
                {createBlendDescription()}
              </p>
            </div>
            <div className="hidden sm:flex items-center gap-3">
              <div className="text-right">
                <div className="text-sm font-semibold text-neutral-800">Fantasy Draft Assistant</div>
                <div className="text-xs text-neutral-500">
                  {meta.generated_at ? 
                    `Updated ${new Date(meta.generated_at).toLocaleDateString()}` :
                    'Powered by nflverse data'
                  }
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-lg">⚡</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 min-h-0 overflow-hidden">
        <div className="mx-auto max-w-7xl h-full px-6 py-6">
          <div className="grid grid-cols-12 gap-8 h-full min-h-0">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
