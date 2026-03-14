import { ApiError } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { useCurrentUserQuery, useMonitorQuery } from '../hooks/useApi'
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

export function Monitor() {
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const isOperator = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const { data, isLoading, isError, error } = useMonitorQuery(isOperator)
  const isForbidden = error instanceof ApiError && error.status === 403

  return (
    <AppLayout title="Monitor">
      {!isOperator ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Operator Access Required</h2>
          <p className="muted">This page is available to owner and admin roles only.</p>
        </section>
      ) : null}

      {isOperator && isLoading ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Loading Monitor</h2>
          <p className="muted">Fetching queue, run, and backend status...</p>
        </section>
      ) : null}

      {isOperator && isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Forbidden</h2>
          <p className="error-text">Your account does not have permission to view monitor data.</p>
        </section>
      ) : null}

      {isOperator && isError && !isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Monitor Unavailable</h2>
          <p className="error-text">The monitor API is currently unreachable.</p>
        </section>
      ) : null}

      {isOperator && data ? (
        <div className="monitor-grid">
          <section className="panel">
            <h2 style={{ marginTop: 0 }}>System Health</h2>
            <div className="settings-grid">
              <div className="stat-card">
                <strong>API</strong>
                <p>{data.health.api_status}</p>
              </div>
              <div className="stat-card">
                <strong>Version</strong>
                <p>{data.health.version}</p>
              </div>
              <div className="stat-card">
                <strong>Coordinator</strong>
                <p>{data.health.coordinator_status}</p>
              </div>
            </div>
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Backend</th>
                    <th>Status</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {data.health.backends.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={3}>
                        No backend health entries.
                      </td>
                    </tr>
                  ) : (
                    data.health.backends.map((backend) => (
                      <tr key={backend.backend}>
                        <td>{backend.backend}</td>
                        <td>{backend.status}</td>
                        <td>{backend.detail}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Queue By Workspace</h2>
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Workspace</th>
                    <th>Queued</th>
                    <th>Running</th>
                    <th>Active Run</th>
                    <th>Backend</th>
                  </tr>
                </thead>
                <tbody>
                  {data.queue.groups.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={5}>
                        No active queue state.
                      </td>
                    </tr>
                  ) : (
                    data.queue.groups.map((group) => (
                      <tr key={group.group_id}>
                        <td>{group.group_id}</td>
                        <td>{group.queued_runs}</td>
                        <td>{group.running_runs}</td>
                        <td>{group.active_run_id ?? '-'}</td>
                        <td>{group.active_backend ?? '-'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Recent Runs</h2>
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Workspace</th>
                    <th>Status</th>
                    <th>Source</th>
                    <th>Slot</th>
                    <th>Backend</th>
                    <th>Created</th>
                    <th>Finished</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {data.runs.items.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={9}>
                        No tracked runs.
                      </td>
                    </tr>
                  ) : (
                    data.runs.items.map((run) => (
                      <tr key={run.run_id}>
                        <td>{run.run_id}</td>
                        <td>{run.group_id}</td>
                        <td>{run.status}</td>
                        <td>{run.source}</td>
                        <td>{run.slot_id}</td>
                        <td>{run.backend ?? '-'}</td>
                        <td>{formatDate(run.created_at)}</td>
                        <td>{formatDate(run.finished_at)}</td>
                        <td>{run.error ?? '-'}</td>
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
