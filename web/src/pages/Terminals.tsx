import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { TerminalSessionStatus, TerminalWorkspaceSummary } from '../api/client'
import { ApiError, apiClient } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import {
  useCurrentUserQuery,
  useTerminalHistoryDetailQuery,
  useTerminalHistoryTimelineQuery,
  useTerminalOverviewQuery,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

const TIMELINE_PAGE_SIZE = 5
const TERMINAL_HISTORY_STATUS_OPTIONS: Array<{ value: TerminalSessionStatus; label: string }> = [
  { value: 'created', label: 'Created' },
  { value: 'attached', label: 'Attached' },
  { value: 'detached', label: 'Detached' },
  { value: 'closed', label: 'Closed' },
  { value: 'exited', label: 'Exited' },
]
const DEFAULT_TIMELINE_FILTERS = {
  status: '' as TerminalSessionStatus | '',
  ownerUserId: '',
  sessionIdPrefix: '',
}

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
  const token = useAuthStore((state) => state.token)
  const storedUser = useAuthStore((state) => state.currentUser)
  const { data: currentUserData } = useCurrentUserQuery()
  const currentUser = currentUserData ?? storedUser
  const isOperator = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const { data, isLoading, isError, error, refetch } = useTerminalOverviewQuery(isOperator)
  const isForbidden = error instanceof ApiError && error.status === 403

  const [actionKey, setActionKey] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)
  const [timelineGroupId, setTimelineGroupId] = useState<string | null>(null)
  const [timelineOffset, setTimelineOffset] = useState(0)
  const [timelineFilters, setTimelineFilters] = useState<{
    status: TerminalSessionStatus | ''
    ownerUserId: string
    sessionIdPrefix: string
  }>(DEFAULT_TIMELINE_FILTERS)
  const [detailSessionId, setDetailSessionId] = useState<string | null>(null)

  const {
    data: timelineData,
    isLoading: isTimelineLoading,
    isFetching: isTimelineFetching,
    isError: isTimelineError,
    error: timelineError,
    refetch: refetchTimeline,
  } = useTerminalHistoryTimelineQuery(
    timelineGroupId,
    {
      limit: TIMELINE_PAGE_SIZE,
      offset: timelineOffset,
      status: timelineFilters.status || undefined,
      ownerUserId: timelineFilters.ownerUserId || undefined,
      sessionIdPrefix: timelineFilters.sessionIdPrefix || undefined,
    },
    isOperator && timelineGroupId !== null,
  )
  const {
    data: detailData,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: detailError,
  } = useTerminalHistoryDetailQuery(
    timelineGroupId,
    detailSessionId,
    isOperator && timelineGroupId !== null && detailSessionId !== null,
  )

  const items = data?.items ?? []
  const summary = summarize(items)
  const currentUserId = currentUser?.id ?? null

  function isActiveSession(item: TerminalWorkspaceSummary): boolean {
    if (!item.session) {
      return false
    }
    return (
      item.session.status === 'created' ||
      item.session.status === 'attached' ||
      item.session.status === 'detached'
    )
  }

  function toggleTimeline(groupId: string) {
    setActionError(null)
    setActionNotice(null)
    if (timelineGroupId === groupId) {
      setTimelineGroupId(null)
      setTimelineOffset(0)
      setTimelineFilters(DEFAULT_TIMELINE_FILTERS)
      setDetailSessionId(null)
      return
    }
    setTimelineGroupId(groupId)
    setTimelineOffset(0)
    setTimelineFilters(DEFAULT_TIMELINE_FILTERS)
    setDetailSessionId(null)
  }

  function updateTimelineFilters(
    patch: Partial<{
      status: TerminalSessionStatus | ''
      ownerUserId: string
      sessionIdPrefix: string
    }>,
  ) {
    setTimelineFilters((current) => ({
      ...current,
      ...patch,
    }))
    setTimelineOffset(0)
    setDetailSessionId(null)
  }

  async function handleClose(item: TerminalWorkspaceSummary) {
    if (!token || !item.session) {
      return
    }
    const key = `close:${item.group_id}`
    try {
      setActionKey(key)
      setActionError(null)
      setActionNotice(null)
      await apiClient.closeCurrentTerminalSession(token, item.group_id)
      await refetch()
      if (timelineGroupId === item.group_id) {
        await refetchTimeline()
      }
      setActionNotice(`Closed terminal session for ${item.group_id}.`)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to close terminal session.')
    } finally {
      setActionKey(null)
    }
  }

  async function handleForceClose(item: TerminalWorkspaceSummary) {
    if (!token || !item.session) {
      return
    }
    const key = `force:${item.group_id}`
    try {
      setActionKey(key)
      setActionError(null)
      setActionNotice(null)
      await apiClient.forceCloseCurrentTerminalSession(token, item.group_id)
      await refetch()
      if (timelineGroupId === item.group_id) {
        await refetchTimeline()
      }
      setActionNotice(`Force-closed terminal session for ${item.group_id}.`)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to force-close terminal session.')
    } finally {
      setActionKey(null)
    }
  }

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
          {actionError ? (
            <section className="panel">
              <p className="error-text">{actionError}</p>
            </section>
          ) : null}
          {actionNotice ? (
            <section className="panel">
              <p className="muted">{actionNotice}</p>
            </section>
          ) : null}
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
                    <th>History Session</th>
                    <th>History Bytes</th>
                    <th>History Truncated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 ? (
                    <tr>
                      <td className="muted" colSpan={13}>
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
                        <td>{item.history ? item.history.session.status : '-'}</td>
                        <td>{item.history ? item.history.output_bytes.toLocaleString() : '-'}</td>
                        <td>{item.history ? (item.history.truncated ? 'yes' : 'no') : '-'}</td>
                        <td>
                          <div className="terminal-actions">
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
                            {item.session &&
                            item.chat_accessible &&
                            currentUserId === item.session.owner_user_id &&
                            isActiveSession(item) ? (
                              <PrimaryButton
                                className="button--ghost"
                                disabled={actionKey !== null}
                                onClick={() => void handleClose(item)}
                                type="button"
                              >
                                {actionKey === `close:${item.group_id}` ? 'Closing...' : 'Close'}
                              </PrimaryButton>
                            ) : null}
                            {item.session && isActiveSession(item) ? (
                              <PrimaryButton
                                className="button--ghost"
                                disabled={actionKey !== null}
                                onClick={() => void handleForceClose(item)}
                                type="button"
                              >
                                {actionKey === `force:${item.group_id}` ? 'Closing...' : 'Force Close'}
                              </PrimaryButton>
                            ) : null}
                            <PrimaryButton
                              className="button--ghost"
                              disabled={actionKey !== null}
                              onClick={() => toggleTimeline(item.group_id)}
                              type="button"
                            >
                              {timelineGroupId === item.group_id ? 'Hide Timeline' : 'View Timeline'}
                            </PrimaryButton>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {timelineGroupId ? (
            <section className="panel">
              <h2 style={{ marginTop: 0 }}>History Timeline: {timelineGroupId}</h2>
              <div className="settings-grid" style={{ marginBottom: '1rem' }}>
                <label>
                  <span className="muted">Status</span>
                  <select
                    onChange={(event) =>
                      updateTimelineFilters({
                        status: (event.target.value as TerminalSessionStatus | '') || '',
                      })
                    }
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    value={timelineFilters.status}
                  >
                    <option value="">All statuses</option>
                    {TERMINAL_HISTORY_STATUS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span className="muted">Owner User ID</span>
                  <input
                    onChange={(event) => updateTimelineFilters({ ownerUserId: event.target.value })}
                    placeholder="owner-1"
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    type="text"
                    value={timelineFilters.ownerUserId}
                  />
                </label>
                <label>
                  <span className="muted">Session ID Prefix</span>
                  <input
                    onChange={(event) => updateTimelineFilters({ sessionIdPrefix: event.target.value })}
                    placeholder="terminal-session"
                    style={{ width: '100%', marginTop: '0.35rem' }}
                    type="text"
                    value={timelineFilters.sessionIdPrefix}
                  />
                </label>
              </div>
              {isTimelineLoading ? <p className="muted">Loading timeline...</p> : null}
              {isTimelineError ? (
                <p className="error-text">
                  {timelineError instanceof Error ? timelineError.message : 'Failed to load timeline.'}
                </p>
              ) : null}
              {!isTimelineLoading && !isTimelineError && timelineData ? (
                <>
                  <div className="monitor-table-wrap">
                    <table className="monitor-table">
                      <thead>
                        <tr>
                          <th>Session</th>
                          <th>Status</th>
                          <th>Owner</th>
                          <th>Snapshot At</th>
                          <th>Created</th>
                          <th>Output Bytes</th>
                          <th>Truncated</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {timelineData.items.length === 0 ? (
                          <tr>
                            <td className="muted" colSpan={7}>
                              Timeline is empty.
                            </td>
                          </tr>
                        ) : (
                          timelineData.items.map((entry) => (
                            <tr key={entry.session.session_id}>
                              <td>{entry.session.session_id}</td>
                              <td>{entry.session.status}</td>
                              <td>{entry.session.owner_user_id}</td>
                              <td>{formatDate(entry.snapshot_at)}</td>
                              <td>{formatDate(entry.session.created_at)}</td>
                              <td>{entry.output_bytes.toLocaleString()}</td>
                              <td>{entry.truncated ? 'yes' : 'no'}</td>
                              <td>
                                <PrimaryButton
                                  className="button--ghost"
                                  onClick={() => setDetailSessionId(entry.session.session_id)}
                                  type="button"
                                >
                                  {detailSessionId === entry.session.session_id ? 'Viewing' : 'View Details'}
                                </PrimaryButton>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div className="terminal-timeline-pagination">
                    <span className="muted">
                      Offset {timelineData.offset} · Page Size {timelineData.limit}
                    </span>
                    <div className="terminal-actions">
                      <PrimaryButton
                        className="button--ghost"
                        disabled={timelineOffset === 0 || isTimelineFetching}
                        onClick={() => setTimelineOffset((value) => Math.max(0, value - TIMELINE_PAGE_SIZE))}
                        type="button"
                      >
                        Previous
                      </PrimaryButton>
                      <PrimaryButton
                        className="button--ghost"
                        disabled={!timelineData.has_more || isTimelineFetching}
                        onClick={() => setTimelineOffset((value) => value + TIMELINE_PAGE_SIZE)}
                        type="button"
                      >
                        Next
                      </PrimaryButton>
                    </div>
                  </div>
                </>
              ) : null}
            </section>
          ) : null}

          {timelineGroupId && detailSessionId ? (
            <section className="panel">
              <h2 style={{ marginTop: 0 }}>History Detail: {detailSessionId}</h2>
              {isDetailLoading ? <p className="muted">Loading terminal history detail...</p> : null}
              {isDetailError ? (
                <p className="error-text">
                  {detailError instanceof Error ? detailError.message : 'Failed to load terminal history detail.'}
                </p>
              ) : null}
              {detailData ? (
                <>
                  <div className="settings-grid" style={{ marginBottom: '1rem' }}>
                    <div className="stat-card">
                      <strong>Status</strong>
                      <p>{detailData.session.status}</p>
                    </div>
                    <div className="stat-card">
                      <strong>Owner</strong>
                      <p>{detailData.session.owner_user_id}</p>
                    </div>
                    <div className="stat-card">
                      <strong>Snapshot At</strong>
                      <p>{formatDate(detailData.snapshot_at)}</p>
                    </div>
                    <div className="stat-card">
                      <strong>Output Bytes</strong>
                      <p>{detailData.output_bytes.toLocaleString()}</p>
                    </div>
                  </div>
                  <pre
                    style={{
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      maxHeight: '24rem',
                      overflow: 'auto',
                    }}
                  >
                    {detailData.output || '(no output)'}
                  </pre>
                </>
              ) : null}
            </section>
          ) : null}
        </div>
      ) : null}
    </AppLayout>
  )
}
