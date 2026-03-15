import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { useAuthStore } from '../../stores/auth'
import { PwaControls } from '../pwa/PwaControls'
import { PrimaryButton } from '../ui/PrimaryButton'

interface AppLayoutProps {
  title: string
  children: ReactNode
}

interface NavItem {
  to: string
  label: string
}

const MOBILE_PRIMARY_ROUTES = new Set(['/chat', '/files', '/memory', '/settings'])

export function AppLayout({ title, children }: AppLayoutProps) {
  const location = useLocation()
  const logout = useAuthStore((state) => state.logout)
  const currentUser = useAuthStore((state) => state.currentUser)
  const [isMobileMoreOpen, setIsMobileMoreOpen] = useState(false)

  const navItems = useMemo<NavItem[]>(
    () => [
      { to: '/setup', label: 'Setup' },
      { to: '/chat', label: 'Chat' },
      { to: '/files', label: 'Files' },
      { to: '/memory', label: 'Memory' },
      { to: '/skills', label: 'Skills' },
      { to: '/mcp-servers', label: 'MCP' },
      ...(currentUser?.role === 'owner' || currentUser?.role === 'admin'
        ? [
            { to: '/monitor', label: 'Monitor' },
            { to: '/usage', label: 'Usage' },
            { to: '/audit', label: 'Audit' },
          ]
        : []),
      { to: '/settings', label: 'Settings' },
    ],
    [currentUser?.role],
  )

  const primaryNavItems = useMemo(
    () => navItems.filter((item) => MOBILE_PRIMARY_ROUTES.has(item.to)),
    [navItems],
  )
  const secondaryNavItems = useMemo(
    () => navItems.filter((item) => !MOBILE_PRIMARY_ROUTES.has(item.to)),
    [navItems],
  )
  const isSecondaryRouteActive = secondaryNavItems.some((item) => item.to === location.pathname)

  function handleLogout() {
    setIsMobileMoreOpen(false)
    logout()
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-content">
          <div className="app-header-row">
            <div className="app-header-meta">
              <p className="app-kicker">Portex</p>
              <h1 className="app-title">{title}</h1>
              <p className="app-userline">{currentUser?.username ?? 'Guest'}</p>
            </div>
            <div className="app-header-actions">
              <PwaControls />
              <PrimaryButton className="button--ghost" onClick={handleLogout} type="button">
                Logout
              </PrimaryButton>
            </div>
          </div>
          <nav aria-label="Primary navigation" className="app-nav">
            {navItems.map((item) => (
              <Link
                className={`app-nav-link ${location.pathname === item.to ? 'active' : ''}`}
                key={item.to}
                to={item.to}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="app-main">{children}</main>
      <button
        aria-hidden={!isMobileMoreOpen}
        className={`mobile-more-backdrop ${isMobileMoreOpen ? 'open' : ''}`}
        onClick={() => setIsMobileMoreOpen(false)}
        tabIndex={isMobileMoreOpen ? 0 : -1}
        type="button"
      />
      <section
        aria-hidden={!isMobileMoreOpen}
        className={`panel mobile-more-sheet ${isMobileMoreOpen ? 'open' : ''}`}
      >
        <div className="mobile-more-header">
          <div>
            <p className="app-kicker">Portex</p>
            <h2 className="mobile-more-title">More</h2>
          </div>
          <p className="muted">{currentUser?.username ?? 'Guest'}</p>
        </div>
        <PwaControls variant="stacked" />
        <nav aria-label="Secondary navigation" className="mobile-more-nav">
          {secondaryNavItems.map((item) => (
            <Link
              className={`mobile-more-link ${location.pathname === item.to ? 'active' : ''}`}
              key={item.to}
              onClick={() => setIsMobileMoreOpen(false)}
              to={item.to}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <PrimaryButton className="button--ghost mobile-more-logout" onClick={handleLogout} type="button">
          Logout
        </PrimaryButton>
      </section>
      <nav aria-label="Mobile quick navigation" className="mobile-quick-nav">
        {primaryNavItems.map((item) => (
          <Link
            className={`mobile-quick-nav-button ${location.pathname === item.to ? 'active' : ''}`}
            key={item.to}
            onClick={() => setIsMobileMoreOpen(false)}
            to={item.to}
          >
            {item.label}
          </Link>
        ))}
        <button
          aria-expanded={isMobileMoreOpen}
          aria-label="Open more navigation"
          className={`mobile-quick-nav-button ${isMobileMoreOpen || isSecondaryRouteActive ? 'active' : ''}`}
          onClick={() => setIsMobileMoreOpen((current) => !current)}
          type="button"
        >
          More
        </button>
      </nav>
    </div>
  )
}
