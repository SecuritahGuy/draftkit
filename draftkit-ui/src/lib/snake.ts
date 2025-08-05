export const roundOf = (overall: number, teams = 12) => Math.ceil(overall / teams)

export const pickInRound = (overall: number, teams = 12) => ((overall - 1) % teams) + 1

export function nextTwoPicks(slot: number, currentPick: number, teams = 12) {
  const round = roundOf(currentPick, teams)
  const isOdd = round % 2 === 1
  const order = isOdd ? slot : (teams - slot + 1)
  const firstOverall = (round - 1) * teams + order
  const secondOverall = round * teams + (isOdd ? (teams - slot + 1) : slot)
  return [firstOverall, secondOverall]
}

export function getPicksForSlot(slot: number, teams = 12, totalRounds = 16) {
  const picks = []
  for (let round = 1; round <= totalRounds; round++) {
    const isOdd = round % 2 === 1
    const pickInThisRound = isOdd ? slot : (teams - slot + 1)
    const overall = (round - 1) * teams + pickInThisRound
    picks.push({ round, pick: pickInThisRound, overall })
  }
  return picks
}
