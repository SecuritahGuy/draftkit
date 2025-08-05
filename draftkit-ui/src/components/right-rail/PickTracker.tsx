import { useState } from 'react'
import { useStore } from '../../store'
import { nextTwoPicks, getPicksForSlot } from '../../lib/snake'

export function PickTracker() {
  const { mySlot, actions } = useStore()
  const [currentPick, setCurrentPick] = useState(1)
  
  const handleSlotChange = (slot: number) => {
    actions.setMySlot(slot)
  }
  
  const nextPicks = mySlot ? nextTwoPicks(mySlot, currentPick) : []
  const myPicks = mySlot ? getPicksForSlot(mySlot).slice(0, 8) : [] // First 8 rounds
  
  return (
    <section className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-neutral-900 mb-3">Pick tracker</h3>
      
      {/* Draft Slot Selection */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-neutral-700 mb-2">Your Draft Slot</label>
        <select
          value={mySlot || ''}
          onChange={(e) => handleSlotChange(parseInt(e.target.value))}
          className="w-full px-3 py-2 border rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Select slot...</option>
          {Array.from({ length: 12 }, (_, i) => i + 1).map(slot => (
            <option key={slot} value={slot}>Slot {slot}</option>
          ))}
        </select>
      </div>
      
      {/* Current Pick */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-neutral-700 mb-2">Current Pick</label>
        <input
          type="number"
          min="1"
          max="192"
          value={currentPick}
          onChange={(e) => setCurrentPick(parseInt(e.target.value) || 1)}
          className="w-full px-3 py-2 border rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>
      
      {mySlot && (
        <>
          {/* Next Picks */}
          {nextPicks.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-neutral-700 mb-2">Your next picks</h4>
              <div className="space-y-1">
                {nextPicks.map((pick, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-neutral-600">Pick {pick}</span>
                    <span className="font-mono text-neutral-900">
                      R{Math.ceil(pick / 12)}P{((pick - 1) % 12) + 1}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* All Your Picks */}
          <div>
            <h4 className="text-xs font-medium text-neutral-700 mb-2">All your picks</h4>
            <div className="grid grid-cols-2 gap-1 text-xs">
              {myPicks.map((pickObj, i) => (
                <div key={i} className={`px-2 py-1 rounded text-center font-mono ${
                  pickObj.overall <= currentPick ? 'bg-neutral-100 text-neutral-500' : 'bg-indigo-50 text-indigo-700'
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
