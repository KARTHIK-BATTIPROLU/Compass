import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import type { Role } from '@/lib/api'
import { GlassPanel } from '@/components/GlassPanel'
import { cn } from '@/lib/utils'

export function Login() {
  const { login, signup } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [role, setRole] = useState<Role>('teacher')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const user =
        mode === 'login'
          ? await login(email, password, role)
          : await signup(name, email, password, role)
      navigate(user.role === 'teacher' ? '/teacher' : '/student')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-svh flex items-center justify-center p-4">
      <GlassPanel className="w-full max-w-md p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 22 }}
        >
          <p className="font-display text-3xl tracking-tight text-sky-100">Compass</p>
          <p className="mt-1 text-sm text-slate-400">AI education content workspace</p>

          <div className="mt-6 grid grid-cols-2 gap-2 rounded-xl bg-black/25 p-1">
            {(['teacher', 'student'] as Role[]).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                className={cn(
                  'rounded-lg py-2 text-sm capitalize transition',
                  role === r ? 'bg-sky-500/25 text-sky-100' : 'text-slate-400',
                )}
              >
                {r}
              </button>
            ))}
          </div>

          <form onSubmit={onSubmit} className="mt-6 space-y-3 text-left">
            {mode === 'signup' && (
              <Field label="Name" value={name} onChange={setName} />
            )}
            <Field label="Email" type="email" value={email} onChange={setEmail} />
            <Field label="Password" type="password" value={password} onChange={setPassword} />
            {error && <p className="text-sm text-rose-300">{error}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-xl bg-gradient-to-r from-sky-500/80 to-emerald-500/70 py-2.5 font-medium disabled:opacity-50"
            >
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <button
            type="button"
            className="mt-4 text-sm text-slate-400 underline"
            onClick={() => setMode((m) => (m === 'login' ? 'signup' : 'login'))}
          >
            {mode === 'login' ? 'Need an account? Sign up' : 'Have an account? Sign in'}
          </button>
        </motion.div>
      </GlassPanel>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
}) {
  return (
    <label className="block text-sm">
      <span className="text-slate-400">{label}</span>
      <input
        type={type}
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:border-sky-400/40"
      />
    </label>
  )
}
