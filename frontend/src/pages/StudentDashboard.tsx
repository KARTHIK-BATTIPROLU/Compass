import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { api, type GeneratedDoc, type WeakSpot } from '@/lib/api'
import { GlassPanel, SkeletonBlock } from '@/components/GlassPanel'
import { WeakSpotList } from '@/components/WeakSpotList'

export function StudentDashboard() {
  const { user, token, logout } = useAuth()
  const [spots, setSpots] = useState<WeakSpot[]>([])
  const [docs, setDocs] = useState<GeneratedDoc[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const [w, d] = await Promise.all([
          api.studentWeakSpots(token),
          api.generatedDocs(token),
        ])
        if (!cancelled) {
          setSpots(w.weak_spots)
          setDocs(d.docs)
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-display text-3xl text-sky-100">Compass</p>
          <p className="text-slate-400 text-sm">Student · {user?.name}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/student/chat"
            className="rounded-xl border border-emerald-400/30 bg-emerald-500/15 px-4 py-2 text-sm"
          >
            Study chat
          </Link>
          <button onClick={logout} className="rounded-xl border border-white/10 px-4 py-2 text-sm">
            Log out
          </button>
        </div>
      </header>

      {error && (
        <GlassPanel className="p-4 text-sm text-rose-300">
          {error}
          <button className="ml-2 underline" onClick={() => window.location.reload()}>
            Retry
          </button>
        </GlassPanel>
      )}

      <section className="grid gap-4 md:grid-cols-2">
        <GlassPanel className="p-5 text-left">
          <h2 className="font-display text-xl mb-3">Your weak spots</h2>
          {loading ? (
            <div className="space-y-2">
              <SkeletonBlock className="h-8 w-full" />
              <SkeletonBlock className="h-8 w-3/4" />
            </div>
          ) : (
            <WeakSpotList
              emptyLabel="No weak spots yet — take a quiz and we'll track what needs practice."
              items={spots.map((s) => ({
                label: s.concept,
                detail: `${s.topic} · failed ${s.failure_count}×${s.last_strategy ? ` · ${s.last_strategy}` : ''}`,
                level: Math.min(100, s.failure_count * 25),
              }))}
            />
          )}
        </GlassPanel>

        <GlassPanel className="p-5 text-left">
          <h2 className="font-display text-xl mb-3">Saved study materials</h2>
          {loading ? (
            <SkeletonBlock className="h-24 w-full" />
          ) : docs.length === 0 ? (
            <p className="text-sm text-slate-400">
              Your approved quizzes, slides, and notes will show up here.
            </p>
          ) : (
            <ul className="space-y-2 text-sm">
              {docs.slice(0, 8).map((d) => (
                <li key={d.id} className="flex justify-between border-b border-white/5 pb-2">
                  <span className="capitalize">{d.content_type}</span>
                  <span className="text-slate-500">{d.status}</span>
                </li>
              ))}
            </ul>
          )}
        </GlassPanel>
      </section>
    </div>
  )
}
