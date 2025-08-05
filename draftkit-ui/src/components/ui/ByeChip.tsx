export function ByeChip({ week }: { week?: number }) {
  return (
    <span className="inline-flex items-center rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-700 font-medium">
      Bye {week ?? "—"}
    </span>
  )
}
