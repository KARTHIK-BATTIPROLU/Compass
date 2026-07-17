import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, type Role, type User } from '@/lib/api'

interface AuthState {
  token: string | null
  user: User | null
  login: (email: string, password: string, role: Role) => Promise<User>
  signup: (name: string, email: string, password: string, role: Role) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)

  const login = useCallback(async (email: string, password: string, role: Role) => {
    const res = await api.login({ email, password, role })
    setToken(res.access_token)
    setUser(res.user)
    return res.user
  }, [])

  const signup = useCallback(
    async (name: string, email: string, password: string, role: Role) => {
      const res = await api.signup({ name, email, password, role })
      setToken(res.access_token)
      setUser(res.user)
      return res.user
    },
    [],
  )

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ token, user, login, signup, logout }),
    [token, user, login, signup, logout],
  )

  return createElement(AuthContext.Provider, { value }, children)
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
