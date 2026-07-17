import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { api, type ClassWeakSpot, type GeneratedDoc } from '@/lib/api'
import { GlassPanel, SkeletonBlock } from '@/components/GlassPanel'
import { WeakSpotList } from '@/components/WeakSpotList'

export function TeacherDashboard() {
  const { user, token, logout } = useAuth()
  const [spots, setSpots] = useState<ClassWeakSpot[]>([])
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
          api.teacherClassWeakSpots(token),
          api.generatedDocs(token),
        ])
        if (!cancelled) {
          setSpots(w.class_weak_spots)
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
          <p className="text-slate-400 text-sm">Teacher · {user?.name}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/teacher/chat"
            className="rounded-xl border border-sky-400/30 bg-sky-500/15 px-4 py-2 text-sm"
          >
            Open chat workspace
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
          <h2 className="font-display text-xl mb-3">Class weak spots</h2>
          {loading ? (
            <div className="space-y-2">
              <SkeletonBlock className="h-8 w-full" />
              <SkeletonBlock className="h-8 w-4/5" />
            </div>
          ) : (
            <WeakSpotList
              emptyLabel="No student struggle patterns yet. Assign quizzes to start tracking."
              items={spots.map((s) => ({
                label: s.concept || s.topic,
                detail: `${s.students} students · ${s.total_failures} failures`,
                level: Math.min(100, s.total_failures * 15),
              }))}
            />
          )}
        </GlassPanel>

        <GlassPanel className="p-5 text-left">
          <h2 className="font-display text-xl mb-3">Approved materials</h2>
          {loading ? (
            <SkeletonBlock className="h-24 w-full" />
          ) : docs.length === 0 ? (
            <p className="text-sm text-slate-400">
              Nothing approved yet. Generate content in chat, then approve it here.
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
