import { useState } from 'react'

import { ApiError } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import { useCurrentUserQuery, useUsageStatsQuery } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

const PERIOD_OPTIONS = [7, 14, 30, 90]

export function Usage() {
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const isOperator = currentUser?.role === 'owner' || currentUser?.role === 'admin'

  const [days, setDays] = useState(7)
  const { data, isLoading, isError, error, refetch } = useUsageStatsQuery(days, isOperator)
  const isForbidden = error instanceof ApiError && error.status === 403

  return (
    <AppLayout title="Usage">
      {!isOperator ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Operator Access Required</h2>
          <p className="muted">This page is available to owner and admin roles only.</p>
        </section>
      ) : null}

      {isOperator ? (
        <section className="panel" style={{ marginBottom: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>Window</h2>
          <div className="settings-row">
            {PERIOD_OPTIONS.map((option) => (
              <PrimaryButton
                className={days === option ? '' : 'button--ghost'}
                key={option}
                onClick={() => setDays(option)}
                type="button"
              >
                {option}d
              </PrimaryButton>
            ))}
            <PrimaryButton className="button--ghost" onClick={() => void refetch()} type="button">
              Refresh
            </PrimaryButton>
          </div>
        </section>
      ) : null}

      {isOperator && isLoading ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Loading Usage</h2>
          <p className="muted">Aggregating usage statistics...</p>
        </section>
      ) : null}

      {isOperator && isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Forbidden</h2>
          <p className="error-text">Your account does not have permission to view usage data.</p>
        </section>
      ) : null}

      {isOperator && isError && !isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Usage Unavailable</h2>
          <p className="error-text">The usage API is currently unreachable.</p>
        </section>
      ) : null}

      {isOperator && data ? (
        <div className="monitor-grid">
          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Summary ({data.days} days)</h2>
            <div className="settings-grid">
              <div className="stat-card">
                <strong>Total Messages</strong>
                <p>{data.summary.total_messages}</p>
              </div>
              <div className="stat-card">
                <strong>Total Runs</strong>
                <p>{data.summary.total_runs}</p>
              </div>
              <div className="stat-card">
                <strong>User Messages</strong>
                <p>{data.summary.total_user_messages}</p>
              </div>
              <div className="stat-card">
                <strong>Assistant Messages</strong>
                <p>{data.summary.total_assistant_messages}</p>
              </div>
              <div className="stat-card">
                <strong>Active Days</strong>
                <p>{data.summary.total_active_days}</p>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Daily Breakdown</h2>
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Messages</th>
                    <th>Runs</th>
                    <th>User</th>
                    <th>Assistant</th>
                  </tr>
                </thead>
                <tbody>
                  {data.daily.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={5}>
                        No usage data in this window.
                      </td>
                    </tr>
                  ) : (
                    data.daily.map((item) => (
                      <tr key={item.date}>
                        <td>{item.date}</td>
                        <td>{item.message_count}</td>
                        <td>{item.run_count}</td>
                        <td>{item.user_message_count}</td>
                        <td>{item.assistant_message_count}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h2 style={{ marginTop: 0 }}>Channel Breakdown</h2>
            <div className="monitor-table-wrap">
              <table className="monitor-table">
                <thead>
                  <tr>
                    <th>Channel</th>
                    <th>Messages</th>
                    <th>Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {data.channels.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={3}>
                        No channel usage records.
                      </td>
                    </tr>
                  ) : (
                    data.channels.map((item) => (
                      <tr key={item.channel}>
                        <td>{item.channel}</td>
                        <td>{item.message_count}</td>
                        <td>{item.run_count}</td>
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
