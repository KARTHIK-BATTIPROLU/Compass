const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export type Role = 'teacher' | 'student'

export interface User {
  id: string
  email: string
  name: string
  role: Role
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.json() as Promise<T>
}

export const api = {
  signup: (body: { email: string; password: string; name: string; role: Role }) =>
    request<TokenResponse>('/auth/signup', { method: 'POST', body: JSON.stringify(body) }),

  login: (body: { email: string; password: string; role: Role }) =>
    request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),

  me: (token: string) => request<User>('/auth/me', {}, token),

  approve: (token: string, body: Record<string, unknown>) =>
    request('/agent/approve', { method: 'POST', body: JSON.stringify(body) }, token),

  edit: (token: string, body: Record<string, unknown>) =>
    request('/agent/edit', { method: 'POST', body: JSON.stringify(body) }, token),

  regenerate: (token: string, body: Record<string, unknown>) =>
    request('/agent/regenerate', { method: 'POST', body: JSON.stringify(body) }, token),

  submitQuizAnswer: (
    token: string,
    body: { topic: string; concept: string; correct: boolean; question?: string },
  ) => request('/agent/submit-quiz-answer', { method: 'POST', body: JSON.stringify(body) }, token),

  studentWeakSpots: (token: string) =>
    request<{ weak_spots: WeakSpot[] }>('/student/weak-spots', {}, token),

  teacherClassWeakSpots: (token: string) =>
    request<{ class_weak_spots: ClassWeakSpot[]; student_count: number }>(
      '/teacher/class-weak-spots',
      {},
      token,
    ),

  generatedDocs: (token: string) =>
    request<{ docs: GeneratedDoc[] }>('/student/generated-docs', {}, token),
}

export interface WeakSpot {
  id: string
  topic: string
  concept: string
  failure_count: number
  last_attempt_correct: boolean
  last_strategy?: string
  last_updated?: string
}

export interface ClassWeakSpot {
  concept: string
  topic: string
  total_failures: number
  students: number
}

export interface GeneratedDoc {
  id: string
  content_type: string
  status: string
  created_at?: string
  content: unknown
}

export { API_BASE }
