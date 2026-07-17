export function WeakSpotList({
  items,
  emptyLabel,
}: {
  items: { label: string; detail: string; level: number }[]
  emptyLabel: string
}) {
  if (!items.length) {
    return <p className="text-sm text-slate-400">{emptyLabel}</p>
  }
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.label + item.detail}>
          <div className="flex justify-between text-sm mb-1">
            <span className="font-medium">{item.label}</span>
            <span className="text-slate-500 text-xs">{item.detail}</span>
          </div>
          <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-400/80 to-rose-400/70"
              style={{ width: `${item.level}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}
