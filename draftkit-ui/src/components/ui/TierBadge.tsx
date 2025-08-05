export function TierBadge({ tier }: { tier: number }) {
  const colors = {
    1: 'bg-indigo-600',
    2: 'bg-blue-600', 
    3: 'bg-emerald-600',
    4: 'bg-amber-600',
    5: 'bg-rose-600',
    6: 'bg-gray-600',
  } as const

  const bgColor = colors[tier as keyof typeof colors] || colors[6]

  return (
    <span className={`px-2 py-0.5 text-xs rounded-full text-white font-medium ${bgColor}`}>
      T{tier}
    </span>
  )
}
