import { Link } from 'react-router-dom'

import type { TerminalWorkspaceSummary } from '../api/client'
import { ApiError } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { useCurrentUserQuery, useTerminalOverviewQuery } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

function formatDate(value: string | null): string {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

function summarize(items: TerminalWorkspaceSummary[]) {
  let activeCount = 0
  let detachedCount = 0
  let closedCount = 0
  let emptyCount = 0

  for (const item of items) {
    if (!item.session) {
      emptyCount += 1
      continue
    }
    if (item.session.status === 'detached') {
      detachedCount += 1
      continue
    }
    if (item.session.status === 'created' || item.session.status === 'attached') {
      activeCount += 1
      continue
    }
    if (item.session.status === 'closed' || item.session.status === 'exited') {
      closedCount += 1
    }
  }

  return { activeCount, detachedCount, closedCount, emptyCount }
}

export function Terminals() {
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const isOperator = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const { data, isLoading, isError, error } = useTerminalOverviewQuery(isOperator)
  const isForbidden = error instanceof ApiError && error.status === 403

  const items = data?.items ?? []
  const summary = summarize(items)

  return (
    <AppLayout title="Terminals">
      {!isOperator ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Operator Access Required</h2>
          <p className="muted">This page is available to owner and admin roles only.</p>
        </section>
      ) : null}

      {isOperator && isLoading ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Loading Terminals</h2>
          <p className="muted">Fetching terminal overview across workspaces...</p>
        </section>
      ) : null}

      {isOperator && isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Forbidden</h2>
          <p className="error-text">Your account does not have permission to view terminal overview data.</p>
        </section>
      ) : null}

      {isOperator && isError && !isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Terminals Unavailable</h2>
          <p className="error-text">The terminal overview API is currently unreachable.</p>
        </section>
      ) : null}

      {isOperator && data ? (
        <div className="monitor-grid">
          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Session Summary</h2>
            <div className="settings-grid">
              <div className="stat-card">
                <strong>Workspaces</strong>
                <p>{items.length}</p>
              </div>
              <div className="stat-card">
                <strong>Active</strong>
                <p>{summary.activeCount}</p>
              </div>
              <div className="stat-card">
                <strong>Detached</strong>
                <p>{summary.detachedCount}</p>
              </div>
              <div className="stat-card">
                <strong>Closed / Exited</strong>
                <p>{summary.closedCount}</p>
              </div>
              <div className="stat-card">
                <strong>No Session</strong>
                <p>{summary.emptyCount}</p>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Workspace Sessions</h2>
            {items.length === 0 ? <p className="muted">No canonical workspaces found.</p> : null}
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Workspace</th>
                    <th>Session</th>
                    <th>Status</th>
                    <th>Owner</th>
                    <th>Backend</th>
                    <th>Container</th>
                    <th>Created</th>
                    <th>Last Attached</th>
                    <th>Reconnect Deadline</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={10}>
                        Terminal overview is empty.
                      </td>
                    </tr>
                  ) : (
                    items.map((item) => (
                      <tr key={item.group_id}>
                        <td>
                          <strong>{item.group_name}</strong>
                          <br />
                          <span className="muted">{item.group_id}</span>
                        </td>
                        <td>{item.session?.session_id ?? '-'}</td>
                        <td>{item.session?.status ?? 'none'}</td>
                        <td>{item.session?.owner_user_id ?? '-'}</td>
                        <td>{item.session?.backend ?? '-'}</td>
                        <td>{item.session?.container_name ?? '-'}</td>
                        <td>{formatDate(item.session?.created_at ?? null)}</td>
                        <td>{formatDate(item.session?.last_attached_at ?? null)}</td>
                        <td>{formatDate(item.session?.reconnect_deadline ?? null)}</td>
                        <td>
                          {item.chat_accessible ? (
                            <Link
                              className="app-nav-link terminal-open-link"
                              to={`/chat?workspace=${encodeURIComponent(item.group_id)}`}
                            >
                              Open in Chat
                            </Link>
                          ) : (
                            <span className="muted">No chat access</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}
    </AppLayout>
  )
}
