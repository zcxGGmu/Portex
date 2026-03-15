import type { FormEvent } from 'react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { createWebSocket, subscribeWebSocketMessages } from '../../api/ws'
import { useGroupMembersQuery, useGroupsQuery, useGroupSlotsQuery } from '../../hooks/useApi'
import { useChatStore } from '../../stores/chat'
import { isStreamEvent } from '../../types/events'
import { MessageList } from './MessageList'
import { ThinkingPanel } from './ThinkingPanel'
import { ToolCallTracker } from './ToolCallTracker'
import { PrimaryButton } from '../ui/PrimaryButton'

export function ChatPanel() {
  const { data: groupsData, isLoading: groupsLoading, error: groupsError } = useGroupsQuery()
  const groups = groupsData?.groups ?? []
  const activeGroup = groups[0] ?? null
  const activeGroupId = activeGroup?.group_id ?? null
  const {
    data: slotsData,
    isLoading: slotsLoading,
    error: slotsError,
  } = useGroupSlotsQuery(activeGroupId)
  const {
    data: membersData,
    isLoading: membersLoading,
    error: membersError,
  } = useGroupMembersQuery(activeGroupId)
  const messages = useChatStore((state) => state.messages)
  const streamEvents = useChatStore((state) => state.streamEvents)
  const draft = useChatStore((state) => state.draft)
  const isRunning = useChatStore((state) => state.isRunning)
  const activeRunId = useChatStore((state) => state.activeRunId)
  const addMessage = useChatStore((state) => state.addMessage)
  const addStreamEvent = useChatStore((state) => state.addStreamEvent)
  const setDraft = useChatStore((state) => state.setDraft)
  const sendDraft = useChatStore((state) => state.sendDraft)
  const clearRunState = useChatStore((state) => state.clearRunState)
  const clearMessages = useChatStore((state) => state.clearMessages)
  const wsRef = useRef<WebSocket | null>(null)
  const [wsState, setWsState] = useState<'connecting' | 'open' | 'closed' | 'error'>('connecting')

  const targetGroupFolder = activeGroupId ?? 'group-demo'
  const tokenDeltaCount = useMemo(
    () => streamEvents.filter((event) => event.event_type === 'run.token.delta').length,
    [streamEvents],
  )
  const toolEventCount = useMemo(
    () =>
      streamEvents.filter(
        (event) => event.event_type === 'run.tool.started' || event.event_type === 'run.tool.completed',
      ).length,
    [streamEvents],
  )
  const terminalEventCount = useMemo(
    () =>
      streamEvents.filter(
        (event) =>
          event.event_type === 'run.completed' ||
          event.event_type === 'run.failed' ||
          event.event_type === 'run.timeout',
      ).length,
    [streamEvents],
  )

  useEffect(() => {
    const websocket = createWebSocket(targetGroupFolder)
    wsRef.current = websocket

    const handleOpen = () => setWsState('open')
    const handleClose = () => setWsState('closed')
    const handleError = () => setWsState('error')

    websocket.addEventListener('open', handleOpen)
    websocket.addEventListener('close', handleClose)
    websocket.addEventListener('error', handleError)

    const unsubscribe = subscribeWebSocketMessages(websocket, (message) => {
      if (isStreamEvent(message)) {
        addStreamEvent(message)
        if (message.event_type === 'run.completed' && typeof message.payload?.final_output === 'string') {
          addMessage({ role: 'assistant', content: message.payload.final_output })
        } else if (message.event_type === 'run.failed') {
          if (message.payload?.status === 'cancelled') {
            addMessage({ role: 'assistant', content: 'Run cancelled.' })
            return
          }
          const errorMessage = message.payload?.error ?? message.payload?.status ?? 'unknown error'
          addMessage({ role: 'assistant', content: `Run failed: ${errorMessage}` })
        } else if (message.event_type === 'run.timeout') {
          addMessage({ role: 'assistant', content: 'Run timed out.' })
        }
        return
      }

      if (typeof message === 'string' && message.trim()) {
        addMessage({ role: 'assistant', content: message })
      }
    })

    return () => {
      unsubscribe()
      websocket.removeEventListener('open', handleOpen)
      websocket.removeEventListener('close', handleClose)
      websocket.removeEventListener('error', handleError)
      websocket.close()
      wsRef.current = null
      clearRunState()
    }
  }, [targetGroupFolder, addMessage, addStreamEvent, clearRunState])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isRunning) {
      return
    }

    const trimmed = draft.trim()
    if (!trimmed) {
      return
    }

    sendDraft()
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(trimmed)
    }
  }

  function handleCancel() {
    if (!activeRunId || wsRef.current?.readyState !== WebSocket.OPEN) {
      return
    }

    wsRef.current.send(
      JSON.stringify({
        type: 'cancel',
        run_id: activeRunId,
      }),
    )
  }

  return (
    <section className="chat-shell">
      <aside className="chat-shell-side">
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">Workspace Snapshot</h3>
          {groupsLoading ? <p className="muted">Loading workspaces...</p> : null}
          {groupsError ? <p className="error-text">{groupsError instanceof Error ? groupsError.message : 'Failed to load workspaces'}</p> : null}
          {!groupsLoading && !groupsError && !activeGroup ? <p className="muted">No workspace found.</p> : null}
          {activeGroup ? (
            <>
              <p className="chat-shell-entity">
                <strong>{activeGroup.name}</strong>
              </p>
              <p className="muted chat-shell-note">{activeGroup.group_id}</p>
            </>
          ) : null}
        </section>
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">Conversation Slots</h3>
          {!activeGroupId ? <p className="muted">Workspace unavailable.</p> : null}
          {activeGroupId && slotsLoading ? <p className="muted">Loading slots...</p> : null}
          {slotsError ? <p className="error-text">{slotsError instanceof Error ? slotsError.message : 'Failed to load slots'}</p> : null}
          {!slotsLoading && !slotsError && slotsData?.slots.length === 0 ? (
            <p className="muted">No slots configured.</p>
          ) : null}
          <ul className="chat-shell-list">
            {slotsData?.slots.slice(0, 6).map((slot) => (
              <li key={slot.slot_id}>
                <span>{slot.title}</span>
                <span className="muted">{slot.slot_id}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">Members</h3>
          {!activeGroupId ? <p className="muted">Workspace unavailable.</p> : null}
          {activeGroupId && membersLoading ? <p className="muted">Loading members...</p> : null}
          {membersError ? <p className="error-text">{membersError instanceof Error ? membersError.message : 'Failed to load members'}</p> : null}
          {!membersLoading && !membersError && membersData?.members.length === 0 ? (
            <p className="muted">No members listed.</p>
          ) : null}
          <ul className="chat-shell-list">
            {membersData?.members.slice(0, 8).map((member) => (
              <li key={`${member.user_id}-${member.role}`}>
                <span>{member.user_id}</span>
                <span className="muted">{member.role}</span>
              </li>
            ))}
          </ul>
        </section>
      </aside>

      <div className="chat-shell-center">
        <section className="panel chat-panel">
          <MessageList messages={messages} />
          <ThinkingPanel events={streamEvents} />
          <ToolCallTracker events={streamEvents} />
          <form className="chat-form" onSubmit={handleSubmit}>
            <textarea
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Type your message..."
              value={draft}
            />
            <div className="chat-form-actions">
              <PrimaryButton disabled={draft.trim().length === 0 || isRunning || wsState !== 'open'} type="submit">
                Send
              </PrimaryButton>
              <span className="muted">
                {wsState === 'open' ? 'Realtime link connected' : wsState === 'connecting' ? 'Connecting realtime link...' : 'Realtime link unavailable'}
              </span>
            </div>
          </form>
        </section>
      </div>

      <aside className="chat-shell-side">
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">Resource Dock</h3>
          <p className="muted chat-shell-note">Jump to dedicated workspace surfaces.</p>
          <div className="chat-shell-links">
            <Link className="app-nav-link" to="/files">
              Files
            </Link>
            <Link className="app-nav-link" to="/memory">
              Memory
            </Link>
            <Link className="app-nav-link" to="/skills">
              Skills
            </Link>
            <Link className="app-nav-link" to="/mcp-servers">
              MCP
            </Link>
          </div>
        </section>
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">Execution Controls</h3>
          <p className="chat-shell-entity">
            Status:{' '}
            <span className={`status-badge ${isRunning ? '' : 'status-badge--idle'}`}>
              {isRunning ? 'running' : 'idle'}
            </span>
          </p>
          <p className="muted chat-shell-note">Run ID: {activeRunId ?? '-'}</p>
          <div className="chat-shell-stats">
            <span>Token events: {tokenDeltaCount}</span>
            <span>Tool events: {toolEventCount}</span>
            <span>Terminal events: {terminalEventCount}</span>
          </div>
          <div className="chat-shell-actions">
            <PrimaryButton className="button--ghost" disabled={!isRunning} onClick={handleCancel} type="button">
              Cancel
            </PrimaryButton>
            <PrimaryButton className="button--ghost" disabled={isRunning} onClick={clearMessages} type="button">
              Clear
            </PrimaryButton>
          </div>
        </section>
      </aside>
    </section>
  )
}
