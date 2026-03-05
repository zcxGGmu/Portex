import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { useAuthStore } from '../../stores/auth'
import { PrimaryButton } from '../ui/PrimaryButton'

interface AppLayoutProps {
  title: string
  children: ReactNode
}

const navItems = [
  { to: '/chat', label: 'Chat' },
  { to: '/settings', label: 'Settings' },
]

export function AppLayout({ title, children }: AppLayoutProps) {
  const location = useLocation()
  const logout = useAuthStore((state) => state.logout)
  const currentUser = useAuthStore((state) => state.currentUser)

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-content">
          <h1 className="app-title">{title}</h1>
          <nav className="app-nav">
            {navItems.map((item) => (
              <Link
                className={`app-nav-link ${location.pathname === item.to ? 'active' : ''}`}
                key={item.to}
                to={item.to}
              >
                {item.label}
              </Link>
            ))}
            <span className="muted">{currentUser?.username ?? 'Guest'}</span>
            <PrimaryButton className="button--ghost" onClick={logout} type="button">
              Logout
            </PrimaryButton>
          </nav>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  )
}
