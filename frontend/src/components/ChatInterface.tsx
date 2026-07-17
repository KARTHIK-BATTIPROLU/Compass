import { GlassPanel } from '@/components/GlassPanel'

export function ChatInterface({
  statusMessages,
  streaming,
  error,
  onRetry,
}: {
  statusMessages: string[]
  streaming: boolean
  error: string | null
  onRetry?: () => void
}) {
  return (
    <GlassPanel className="max-h-48 overflow-auto p-3 text-left text-sm">
      {!statusMessages.length && !streaming && !error && (
        <p className="text-slate-500">
          Describe what you need — quizzes, slides, diagrams, notes. Floating actions appear from
          detected intent.
        </p>
      )}
      <ul className="space-y-1 text-slate-300">
        {statusMessages.slice(-12).map((m, i) => (
          <li key={`${m}-${i}`} className="font-mono text-xs text-sky-200/80">
            {m}
          </li>
        ))}
      </ul>
      {streaming && <p className="mt-2 text-xs text-emerald-300/80">Streaming…</p>}
      {error && (
        <div className="mt-2 text-rose-300">
          {error}{' '}
          {onRetry && (
            <button type="button" className="underline" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      )}
    </GlassPanel>
  )
}
