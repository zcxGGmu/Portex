import { useState } from 'react'

import { ApiError } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import { useAuditMessagesQuery, useCurrentUserQuery } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

function previewContent(value: string | null): string {
  if (!value) {
    return '-'
  }
  const normalized = value.replace(/\s+/g, ' ').trim()
  if (normalized.length <= 120) {
    return normalized
  }
  return `${normalized.slice(0, 117)}...`
}

const LIMIT_OPTIONS = [20, 50, 100, 200]

export function Audit() {
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const isOperator = currentUser?.role === 'owner' || currentUser?.role === 'admin'

  const [limit, setLimit] = useState(100)
  const [groupInput, setGroupInput] = useState('')
  const [groupFilter, setGroupFilter] = useState<string | null>(null)

  const { data, isLoading, isError, error, refetch } = useAuditMessagesQuery(
    { limit, groupId: groupFilter },
    isOperator,
  )
  const isForbidden = error instanceof ApiError && error.status === 403

  return (
    <AppLayout title="Audit">
      {!isOperator ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Operator Access Required</h2>
          <p className="muted">This page is available to owner and admin roles only.</p>
        </section>
      ) : null}

      {isOperator ? (
        <section className="panel" style={{ marginBottom: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>Filters</h2>
          <div className="audit-toolbar">
            <div className="field audit-toolbar-field">
              <label htmlFor="audit-limit">Limit</label>
              <select
                id="audit-limit"
                onChange={(event) => setLimit(Number(event.target.value))}
                value={limit}
              >
                {LIMIT_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            <div className="field audit-toolbar-field audit-toolbar-search">
              <label htmlFor="audit-group">Workspace Filter (optional)</label>
              <input
                id="audit-group"
                onChange={(event) => setGroupInput(event.target.value)}
                placeholder="project-alpha"
                type="text"
                value={groupInput}
              />
            </div>
            <div className="settings-row">
              <PrimaryButton
                onClick={() => setGroupFilter(groupInput.trim() ? groupInput.trim() : null)}
                type="button"
              >
                Apply
              </PrimaryButton>
              <PrimaryButton
                className="button--ghost"
                onClick={() => {
                  setGroupInput('')
                  setGroupFilter(null)
                }}
                type="button"
              >
                Clear
              </PrimaryButton>
              <PrimaryButton className="button--ghost" onClick={() => void refetch()} type="button">
                Refresh
              </PrimaryButton>
            </div>
          </div>
        </section>
      ) : null}

      {isOperator && isLoading ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Loading Audit Feed</h2>
          <p className="muted">Fetching recent audit messages...</p>
        </section>
      ) : null}

      {isOperator && isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Forbidden</h2>
          <p className="error-text">Your account does not have permission to view audit data.</p>
        </section>
      ) : null}

      {isOperator && isError && !isForbidden ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Audit Unavailable</h2>
          <p className="error-text">The audit API is currently unreachable.</p>
        </section>
      ) : null}

      {isOperator && data ? (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Recent Messages</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            Limit: {data.limit}
            {data.group_id ? ` · Filter: ${data.group_id}` : ''}
            {data.has_more ? ' · More records available' : ''}
          </p>

          <div className="monitor-table-wrap">
            <table className="monitor-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Group</th>
                  <th>Channel</th>
                  <th>Direction</th>
                  <th>Sender</th>
                  <th>Run</th>
                  <th>Slot</th>
                  <th>Content</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td className="muted" colSpan={8}>
                      No audit records for current filters.
                    </td>
                  </tr>
                ) : (
                  data.items.map((item) => (
                    <tr key={item.message_id}>
                      <td>{formatDate(item.timestamp)}</td>
                      <td>{item.group_id}</td>
                      <td>{item.channel}</td>
                      <td>{item.is_from_me ? 'assistant' : 'user'}</td>
                      <td>{item.sender}</td>
                      <td>{item.run_id ?? '-'}</td>
                      <td>{item.slot_id}</td>
                      <td title={item.content ?? ''}>{previewContent(item.content)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </AppLayout>
  )
}
