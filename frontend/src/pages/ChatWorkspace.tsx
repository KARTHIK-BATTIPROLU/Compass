import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useSSEStream } from '@/hooks/useSSEStream'
import { GlassPanel, SkeletonBlock } from '@/components/GlassPanel'
import { ContentPreview } from '@/components/ContentPreview'
import { FloatingActionBar } from '@/components/FloatingActionBar'
import { ChatInterface } from '@/components/ChatInterface'

export function ChatWorkspace() {
  const { token, user } = useAuth()
  const { events, streaming, error, start, reset } = useSSEStream()
  const [input, setInput] = useState('')
  const [activeKey, setActiveKey] = useState<string | null>(null)
  const [contentOverride, setContentOverride] = useState<Record<string, Record<string, unknown>>>({})

  const basePath = user?.role === 'teacher' ? '/teacher' : '/student'

  const threadId = useMemo(() => {
    const t = events.find((e) => e.type === 'thread' || e.type === 'final')
    return (t?.thread_id as string) || null
  }, [events])

  const intents = useMemo(() => {
    const intentEvt = [...events].reverse().find((e) => e.type === 'intents' || e.type === 'final')
    return (intentEvt?.intents as string[]) || (intentEvt?.detected_intents as string[]) || []
  }, [events])

  const generatedContent = useMemo(() => {
    const finalEvt = [...events].reverse().find((e) => e.type === 'final' || e.type === 'content')
    const raw = (finalEvt?.content || finalEvt?.generated_content || {}) as Record<
      string,
      Record<string, unknown>
    >
    return { ...raw, ...contentOverride }
  }, [events, contentOverride])

  const statusMessages = events
    .filter((e) => e.type === 'status' || e.type === 'node_start' || e.type === 'message')
    .map((e) => {
      if (e.type === 'status') return String(e.message)
      if (e.type === 'node_start') return `Running ${e.node}…`
      const msg = e.message as { content?: string } | undefined
      return msg?.content || ''
    })
    .filter(Boolean)

  async function onSend(e: FormEvent) {
    e.preventDefault()
    if (!token || !input.trim() || streaming) return
    setContentOverride({})
    setActiveKey(null)
    const message = input.trim()
    setInput('')
    reset()
    await start(token, message)
  }

  const previewKeys = Object.keys(generatedContent).filter(
    (k) => !['grounding_used', 'sources'].includes(k),
  )
  const shownKey = activeKey && generatedContent[activeKey] ? activeKey : previewKeys[0]

  return (
    <div className="mx-auto flex min-h-svh max-w-5xl flex-col px-3 pb-28 pt-6 sm:px-4">
      <header className="mb-4 flex items-center justify-between gap-2">
        <div>
          <p className="font-display text-2xl text-sky-100">Compass</p>
          <p className="text-xs text-slate-400">Chat workspace · {user?.role}</p>
        </div>
        <Link to={basePath} className="text-sm text-slate-400 underline">
          Back to dashboard
        </Link>
      </header>

      <ChatInterface
        statusMessages={statusMessages}
        streaming={streaming}
        error={error}
        onRetry={() => {
          /* user re-sends */
        }}
      />

      {streaming && !previewKeys.length && (
        <GlassPanel className="mt-4 space-y-3 p-4">
          <SkeletonBlock className="h-5 w-1/3" />
          <SkeletonBlock className="h-28 w-full" />
        </GlassPanel>
      )}

      {shownKey && generatedContent[shownKey] && (
        <div className="mt-4">
          <ContentPreview
            contentType={shownKey}
            content={generatedContent[shownKey]}
            threadId={threadId}
            onUpdated={(key, next) =>
              setContentOverride((prev) => ({ ...prev, [key]: next }))
            }
          />
        </div>
      )}

      {generatedContent.sources && Array.isArray(generatedContent.sources) && (
        <GlassPanel className="mt-3 p-3 text-left text-xs text-slate-400">
          Sources:{' '}
          {(generatedContent.sources as { url?: string; title?: string }[])
            .map((s) => s.title || s.url)
            .filter(Boolean)
            .join(' · ')}
        </GlassPanel>
      )}

      <form onSubmit={onSend} className="mt-auto pt-4">
        <GlassPanel className="flex gap-2 p-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder='e.g. "quiz me on photosynthesis" or "slides and a diagram of Krebs cycle"'
            className="min-w-0 flex-1 rounded-xl bg-transparent px-3 py-2 text-sm outline-none"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="shrink-0 rounded-xl bg-sky-500/30 px-4 py-2 text-sm disabled:opacity-40"
          >
            {streaming ? '…' : 'Send'}
          </button>
        </GlassPanel>
      </form>

      <FloatingActionBar
        intents={intents}
        active={shownKey}
        onSelect={(key) => setActiveKey(key)}
      />
    </div>
  )
}
