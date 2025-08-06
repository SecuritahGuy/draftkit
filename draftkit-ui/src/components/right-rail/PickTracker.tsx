import { useState } from 'react'
import { useStore } from '../../store-simple'
import { nextTwoPicks, getPicksForSlot } from '../../lib/snake'

export function PickTracker() {
  const mySlot = useStore(s => s.mySlot)
  const actions = useStore(s => s.actions)
  const [currentPick, setCurrentPick] = useState(1)
  
  const handleSlotChange = (slot: number) => {
    actions.setMySlot(slot)
  }
  
  const nextPicks = mySlot ? nextTwoPicks(mySlot, currentPick) : []
  const myPicks = mySlot ? getPicksForSlot(mySlot).slice(0, 8) : [] // First 8 rounds
  
  return (
    <section className="rounded-2xl border border-neutral-300 bg-white/90 backdrop-blur-sm p-6 shadow-xl">
      <h3 className="text-lg font-bold text-neutral-900 mb-5 border-b border-neutral-200 pb-3">Pick Tracker</h3>
      
      {/* Draft Slot Selection */}
      <div className="mb-6">
        <label className="block text-sm font-bold text-neutral-800 mb-3">Your Draft Slot</label>
        <select
          value={mySlot || ''}
          onChange={(e) => handleSlotChange(parseInt(e.target.value))}
          className="w-full px-4 py-3 border border-neutral-300 rounded-xl text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-medium transition-all"
        >
          <option value="">Select slot...</option>
          {Array.from({ length: 12 }, (_, i) => i + 1).map(slot => (
            <option key={slot} value={slot}>Slot {slot}</option>
          ))}
        </select>
      </div>
      
      {/* Current Pick */}
      <div className="mb-6">
        <label className="block text-sm font-bold text-neutral-800 mb-3">Current Pick</label>
        <input
          type="number"
          min="1"
          max="192"
          value={currentPick}
          onChange={(e) => setCurrentPick(parseInt(e.target.value) || 1)}
          className="w-full px-4 py-3 border border-neutral-300 rounded-xl text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-medium transition-all"
        />
      </div>
      
      {mySlot && (
        <>
          {/* Next Picks */}
          {nextPicks.length > 0 && (
            <div className="mb-5">
              <h4 className="text-sm font-semibold text-neutral-700 mb-3 border-b border-neutral-100 pb-1">Your Next Picks</h4>
              <div className="space-y-2">
                {nextPicks.map((pick, i) => (
                  <div key={i} className="flex justify-between items-center p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                    <span className="text-sm font-medium text-indigo-900">Pick {pick}</span>
                    <span className="font-mono text-sm font-bold text-indigo-700 bg-indigo-100 px-2 py-1 rounded">
                      R{Math.ceil(pick / 12)}P{((pick - 1) % 12) + 1}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* All Your Picks */}
          <div>
            <h4 className="text-sm font-semibold text-neutral-700 mb-3 border-b border-neutral-100 pb-1">All Your Picks</h4>
            <div className="grid grid-cols-3 gap-2 text-xs">
              {myPicks.map((pickObj, i) => (
                <div key={i} className={`px-3 py-2 text-center font-mono font-bold rounded-lg border-2 transition-colors ${
                  pickObj.overall <= currentPick 
                    ? 'bg-neutral-100 text-neutral-500 border-neutral-200' 
                    : 'bg-indigo-50 text-indigo-800 border-indigo-200 hover:bg-indigo-100'
                }`}>
                  {pickObj.overall}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  )
}
