import type { ReactNode } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { Chat } from './pages/Chat'
import { Files } from './pages/Files'
import { Login } from './pages/Login'
import { Memory } from './pages/Memory'
import { Monitor } from './pages/Monitor'
import { Register } from './pages/Register'
import { Settings } from './pages/Settings'
import { useAuthStore } from './stores/auth'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = useAuthStore((state) => state.token)
  const location = useLocation()

  if (!token) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />
  }

  return <>{children}</>
}

function GuestRoute({ children }: { children: ReactNode }) {
  const token = useAuthStore((state) => state.token)

  if (token) {
    return <Navigate replace to="/chat" />
  }

  return <>{children}</>
}

function App() {
  const token = useAuthStore((state) => state.token)

  return (
    <Routes>
      <Route
        element={
          <GuestRoute>
            <Login />
          </GuestRoute>
        }
        path="/login"
      />
      <Route
        element={
          <GuestRoute>
            <Register />
          </GuestRoute>
        }
        path="/register"
      />
      <Route
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        }
        path="/chat"
      />
      <Route
        element={
          <ProtectedRoute>
            <Files />
          </ProtectedRoute>
        }
        path="/files"
      />
      <Route
        element={
          <ProtectedRoute>
            <Memory />
          </ProtectedRoute>
        }
        path="/memory"
      />
      <Route
        element={
          <ProtectedRoute>
            <Monitor />
          </ProtectedRoute>
        }
        path="/monitor"
      />
      <Route
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
        path="/settings"
      />
      <Route element={<Navigate replace to={token ? '/chat' : '/login'} />} path="*" />
    </Routes>
  )
}

export default App
