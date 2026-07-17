import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import mermaid from 'mermaid'
import { api } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import { GlassPanel, SkeletonBlock } from '@/components/GlassPanel'
import { cn } from '@/lib/utils'

mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })

interface ContentPreviewProps {
  contentType: string
  content: Record<string, unknown>
  threadId?: string | null
  onUpdated?: (contentType: string, content: Record<string, unknown>) => void
  loading?: boolean
}

export function ContentPreview({
  contentType,
  content,
  threadId,
  onUpdated,
  loading,
}: ContentPreviewProps) {
  const { token } = useAuth()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(JSON.stringify(content, null, 2))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (loading) {
    return (
      <GlassPanel className="p-4 space-y-3">
        <SkeletonBlock className="h-6 w-1/3" />
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
      </GlassPanel>
    )
  }

  if (content?.error) {
    return (
      <GlassPanel className="p-4">
        <p className="text-rose-300 text-sm">{String(content.error)}</p>
        {threadId && token && (
          <button
            className="mt-3 text-sm text-sky-300 underline"
            onClick={async () => {
              setBusy(true)
              setError(null)
              try {
                const res = (await api.regenerate(token, {
                  thread_id: threadId,
                  action: 'regenerate',
                  target: contentType,
                })) as { generated_content?: Record<string, Record<string, unknown>> }
                const next = res.generated_content?.[contentType]
                if (next) onUpdated?.(contentType, next)
              } catch (e) {
                setError((e as Error).message)
              } finally {
                setBusy(false)
              }
            }}
          >
            {busy ? 'Retrying…' : 'Retry / Regenerate'}
          </button>
        )}
      </GlassPanel>
    )
  }

  async function handleApprove() {
    if (!token || !threadId) return
    setBusy(true)
    setError(null)
    try {
      await api.approve(token, { thread_id: threadId, action: 'approve' })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function handleEditSave() {
    if (!token || !threadId) return
    setBusy(true)
    setError(null)
    try {
      const parsed = JSON.parse(draft) as Record<string, unknown>
      await api.edit(token, {
        thread_id: threadId,
        action: 'edit',
        content: { [contentType]: parsed },
      })
      onUpdated?.(contentType, parsed)
      setEditing(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function handleRegenerate() {
    if (!token || !threadId) return
    setBusy(true)
    setError(null)
    try {
      const res = (await api.regenerate(token, {
        thread_id: threadId,
        action: 'regenerate',
        target: contentType,
        instruction: 'The user rejected the previous output, try again differently.',
      })) as { generated_content?: Record<string, Record<string, unknown>> }
      const next = res.generated_content?.[contentType]
      if (next) {
        onUpdated?.(contentType, next)
        setDraft(JSON.stringify(next, null, 2))
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <GlassPanel className="p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-display text-lg capitalize text-sky-200">{contentType}</h3>
        <div className="flex flex-wrap gap-2">
          <ActionBtn onClick={handleApprove} disabled={busy}>
            Approve
          </ActionBtn>
          <ActionBtn onClick={() => setEditing((v) => !v)} disabled={busy}>
            Edit
          </ActionBtn>
          <ActionBtn onClick={handleRegenerate} disabled={busy}>
            Regenerate
          </ActionBtn>
        </div>
      </div>

      {error && <p className="text-sm text-rose-300">{error}</p>}

      {editing ? (
        <div className="space-y-2">
          <textarea
            className="w-full min-h-48 rounded-xl bg-black/30 border border-white/10 p-3 text-sm font-mono"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <button
            onClick={handleEditSave}
            className="rounded-lg bg-emerald-500/20 border border-emerald-400/30 px-3 py-1.5 text-sm"
          >
            Save edits
          </button>
        </div>
      ) : (
        <Renderer contentType={contentType} content={content} />
      )}
    </GlassPanel>
  )
}

function ActionBtn({
  children,
  onClick,
  disabled,
}: {
  children: string
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs uppercase tracking-wide hover:bg-white/10 disabled:opacity-50"
    >
      {children}
    </button>
  )
}

function Renderer({
  contentType,
  content,
}: {
  contentType: string
  content: Record<string, unknown>
}) {
  if (contentType === 'quiz') return <QuizView content={content} />
  if (contentType === 'slides') return <SlidesView content={content} />
  if (contentType === 'diagram') return <DiagramView content={content} />
  if (contentType === 'notes') return <NotesView content={content} />
  return (
    <pre className="text-left text-xs overflow-auto max-h-80 text-slate-300">
      {JSON.stringify(content, null, 2)}
    </pre>
  )
}

function QuizView({ content }: { content: Record<string, unknown> }) {
  const { token } = useAuth()
  const questions = (content.questions as Array<Record<string, unknown>>) || []
  const topic = String(content.topic || 'quiz')
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [results, setResults] = useState<Record<number, boolean>>({})

  async function check(i: number, q: Record<string, unknown>) {
    const selected = answers[i]
    if (!selected) return
    const correct = selected.trim().toLowerCase() === String(q.correct_answer).trim().toLowerCase()
    setResults((r) => ({ ...r, [i]: correct }))
    if (token) {
      try {
        await api.submitQuizAnswer(token, {
          topic,
          concept: String(q.question || topic).slice(0, 120),
          correct,
          question: String(q.question || ''),
        })
      } catch {
        /* non-blocking */
      }
    }
  }

  return (
    <div className="space-y-3 text-left">
      {questions.map((q, i) => (
        <div key={i} className="rounded-xl border border-white/10 bg-black/20 p-3">
          <p className="text-sm font-medium mb-2">
            {i + 1}. {String(q.question)}
          </p>
          {(q.options as string[] | undefined)?.length ? (
            <div className="space-y-1">
              {(q.options as string[]).map((opt) => (
                <label key={opt} className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="radio"
                    name={`q-${i}`}
                    checked={answers[i] === opt}
                    onChange={() => setAnswers((a) => ({ ...a, [i]: opt }))}
                  />
                  {opt}
                </label>
              ))}
            </div>
          ) : (
            <input
              className="w-full rounded-lg bg-black/30 border border-white/10 px-2 py-1 text-sm"
              value={answers[i] || ''}
              onChange={(e) => setAnswers((a) => ({ ...a, [i]: e.target.value }))}
              placeholder="Your answer"
            />
          )}
          <button
            className="mt-2 text-xs text-sky-300"
            onClick={() => check(i, q)}
          >
            Check
          </button>
          {results[i] !== undefined && (
            <p className={cn('text-xs mt-1', results[i] ? 'text-emerald-300' : 'text-rose-300')}>
              {results[i] ? 'Correct' : `Incorrect — answer: ${String(q.correct_answer)}`}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

function SlidesView({ content }: { content: Record<string, unknown> }) {
  const slides = (content.slides as Array<Record<string, unknown>>) || []
  const [idx, setIdx] = useState(0)
  const slide = slides[idx]
  if (!slide) return <p className="text-sm text-slate-400">No slides</p>
  return (
    <div className="text-left space-y-3">
      <motion.div
        key={idx}
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ type: 'spring', stiffness: 280, damping: 24 }}
        className="min-h-40 rounded-xl border border-white/10 bg-gradient-to-br from-sky-500/10 to-emerald-500/5 p-4"
      >
        <h4 className="font-display text-xl mb-2">{String(slide.title)}</h4>
        <ul className="list-disc pl-5 space-y-1 text-sm text-slate-200">
          {((slide.bullet_points as string[]) || []).map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
        {slide.speaker_notes ? (
          <p className="mt-3 text-xs text-slate-400">Notes: {String(slide.speaker_notes)}</p>
        ) : null}
      </motion.div>
      <div className="flex items-center justify-between text-sm">
        <button disabled={idx === 0} onClick={() => setIdx((i) => i - 1)} className="disabled:opacity-40">
          Prev
        </button>
        <span className="text-slate-400">
          {idx + 1} / {slides.length}
        </span>
        <button
          disabled={idx >= slides.length - 1}
          onClick={() => setIdx((i) => i + 1)}
          className="disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  )
}

function DiagramView({ content }: { content: Record<string, unknown> }) {
  const ref = useRef<HTMLDivElement>(null)
  const [err, setErr] = useState<string | null>(null)
  const mermaidCode = String(content.mermaid || '')

  useEffect(() => {
    let cancelled = false
    async function render() {
      if (!ref.current || !mermaidCode) return
      try {
        setErr(null)
        const id = `mmd-${Math.random().toString(36).slice(2)}`
        const { svg } = await mermaid.render(id, mermaidCode)
        if (!cancelled && ref.current) ref.current.innerHTML = svg
      } catch (e) {
        if (!cancelled) setErr((e as Error).message || 'Invalid Mermaid syntax')
      }
    }
    void render()
    return () => {
      cancelled = true
    }
  }, [mermaidCode])

  if (err) {
    return (
      <div className="text-left space-y-2">
        <p className="text-sm text-rose-300">Diagram failed to render. Try regenerate.</p>
        <pre className="text-xs text-slate-400 overflow-auto">{mermaidCode}</pre>
      </div>
    )
  }
  return <div ref={ref} className="overflow-auto text-left" />
}

function NotesView({ content }: { content: Record<string, unknown> }) {
  return (
    <div className="text-left space-y-2">
      <h4 className="font-display text-lg">{String(content.title || 'Notes')}</h4>
      {content.strategy ? (
        <p className="text-xs uppercase tracking-wide text-emerald-300/80">
          Strategy: {String(content.strategy)}
        </p>
      ) : null}
      <pre className="whitespace-pre-wrap text-sm text-slate-200 font-body">
        {String(content.body || '')}
      </pre>
    </div>
  )
}
