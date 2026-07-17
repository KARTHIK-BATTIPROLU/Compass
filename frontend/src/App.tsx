import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/hooks/useAuth'
import { Login } from '@/pages/Login'
import { TeacherDashboard } from '@/pages/TeacherDashboard'
import { StudentDashboard } from '@/pages/StudentDashboard'
import { ChatWorkspace } from '@/pages/ChatWorkspace'
import type { Role } from '@/lib/api'

function RoleGuard({ role }: { role: Role }) {
  const { user, token } = useAuth()
  if (!token || !user) return <Navigate to="/login" replace />
  if (user.role !== role) {
    return <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} replace />
  }
  return <Outlet />
}

function HomeRedirect() {
  const { user, token } = useAuth()
  if (!token || !user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} replace />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<HomeRedirect />} />

        <Route element={<RoleGuard role="teacher" />}>
          <Route path="/teacher" element={<TeacherDashboard />} />
          <Route path="/teacher/chat" element={<ChatWorkspace />} />
        </Route>

        <Route element={<RoleGuard role="student" />}>
          <Route path="/student" element={<StudentDashboard />} />
          <Route path="/student/chat" element={<ChatWorkspace />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
