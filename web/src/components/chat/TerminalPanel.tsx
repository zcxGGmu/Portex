import type { FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { apiClient, type TerminalSessionResponse } from '../../api/client'
import { createTerminalWebSocket, parseWebSocketMessage } from '../../api/ws'
import { useCurrentTerminalSessionQuery } from '../../hooks/useApi'
import { useAuthStore } from '../../stores/auth'
import { PrimaryButton } from '../ui/PrimaryButton'

interface TerminalPanelProps {
  activeGroupId: string | null
  activeGroupName: string | null
}

type TerminalSocketState = 'idle' | 'connecting' | 'open' | 'closed' | 'error'
type SocketCloseIntent = 'dispose' | 'session-close' | null

const MIN_TERMINAL_COLS = 40
const MAX_TERMINAL_COLS = 240
const MIN_TERMINAL_ROWS = 12
const MAX_TERMINAL_ROWS = 80
const TERMINAL_CELL_WIDTH_PX = 9
const TERMINAL_CELL_HEIGHT_PX = 18
const RESIZE_THROTTLE_MS = 120
const READY_RESIZE_DELAY_MS = 80

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

function isRecordLike(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function getStatusLabel(
  currentSession: TerminalSessionResponse | null | undefined,
  socketState: TerminalSocketState,
): string {
  if (socketState === 'open') {
    return 'connected'
  }
  if (socketState === 'connecting') {
    return 'connecting'
  }
  if (socketState === 'error') {
    return 'error'
  }
  return currentSession?.status ?? 'idle'
}

function getStatusBadgeClass(statusLabel: string): string {
  if (statusLabel === 'connected') {
    return 'status-badge'
  }
  if (statusLabel === 'error') {
    return 'status-badge status-badge--danger'
  }
  return 'status-badge status-badge--idle'
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function estimateTerminalSize(container: HTMLElement | null): { cols: number; rows: number } {
  if (!container) {
    return { cols: 120, rows: 32 }
  }

  const width = Math.max(0, container.clientWidth - 16)
  const height = Math.max(0, container.clientHeight - 16)
  const cols = clamp(Math.floor(width / TERMINAL_CELL_WIDTH_PX), MIN_TERMINAL_COLS, MAX_TERMINAL_COLS)
  const rows = clamp(Math.floor(height / TERMINAL_CELL_HEIGHT_PX), MIN_TERMINAL_ROWS, MAX_TERMINAL_ROWS)
  return { cols, rows }
}

export function TerminalPanel({ activeGroupId, activeGroupName }: TerminalPanelProps) {
  const token = useAuthStore((state) => state.token)
  const currentUser = useAuthStore((state) => state.currentUser)
  const currentUserId = currentUser?.id ?? null
  const canUseTerminal = currentUser?.role === 'owner' || currentUser?.role === 'admin'

  const {
    data: currentSession,
    isLoading,
    error: currentSessionError,
    refetch,
  } = useCurrentTerminalSessionQuery(activeGroupId, canUseTerminal)

  const socketRef = useRef<WebSocket | null>(null)
  const closeIntentRef = useRef<SocketCloseIntent>(null)
  const transcriptRef = useRef<HTMLDivElement | null>(null)
  const resizeTimerRef = useRef<number | null>(null)
  const lastResizeRef = useRef<{ sessionId: string; cols: number; rows: number } | null>(null)

  const [socketState, setSocketState] = useState<TerminalSocketState>('idle')
  const [connectedSessionId, setConnectedSessionId] = useState<string | null>(null)
  const [commandInput, setCommandInput] = useState('')
  const [panelError, setPanelError] = useState<string | null>(null)
  const [panelNotice, setPanelNotice] = useState<string | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const [isClosing, setIsClosing] = useState(false)
  const [transcriptsByGroup, setTranscriptsByGroup] = useState<Record<string, string>>({})

  const ownsCurrentSession = Boolean(currentSession && currentUserId && currentSession.owner_user_id === currentUserId)
  const sessionBlockedByOtherUser = Boolean(
    currentSession &&
      currentUserId &&
      currentSession.owner_user_id !== currentUserId &&
      currentSession.status !== 'closed' &&
      currentSession.status !== 'exited',
  )
  const activeTranscript = useMemo(
    () => (activeGroupId ? transcriptsByGroup[activeGroupId] ?? '' : ''),
    [activeGroupId, transcriptsByGroup],
  )
  const statusLabel = useMemo(
    () => getStatusLabel(currentSession, socketState),
    [currentSession, socketState],
  )
  const startableSession = !currentSession || currentSession.status === 'closed' || currentSession.status === 'exited'
  const canStartTerminal = Boolean(activeGroupId && token && canUseTerminal && !sessionBlockedByOtherUser && startableSession)
  const canConnectTerminal = Boolean(
    activeGroupId &&
      token &&
      currentSession &&
      ownsCurrentSession &&
      currentSession.status !== 'closed' &&
      currentSession.status !== 'exited' &&
      socketState !== 'open',
  )
  const canCloseTerminal = Boolean(activeGroupId && token && currentSession && ownsCurrentSession)
  const canSendInput = Boolean(socketRef.current && socketState === 'open')

  function appendTranscript(groupId: string, content: string) {
    setTranscriptsByGroup((current) => ({
      ...current,
      [groupId]: `${current[groupId] ?? ''}${content}`,
    }))
  }

  function clearCurrentTranscript() {
    if (!activeGroupId) {
      return
    }
    setTranscriptsByGroup((current) => ({
      ...current,
      [activeGroupId]: '',
    }))
  }

  const sendTerminalResize = useCallback((socket: WebSocket, sessionId: string) => {
    if (socket.readyState !== WebSocket.OPEN) {
      return
    }

    const { cols, rows } = estimateTerminalSize(transcriptRef.current)
    const previous = lastResizeRef.current
    if (
      previous &&
      previous.sessionId === sessionId &&
      previous.cols === cols &&
      previous.rows === rows
    ) {
      return
    }

    socket.send(JSON.stringify({ type: 'terminal.resize', cols, rows }))
    lastResizeRef.current = { sessionId, cols, rows }
  }, [])

  function disconnectSocket(nextState: TerminalSocketState) {
    const socket = socketRef.current
    socketRef.current = null
    closeIntentRef.current = 'dispose'
    setConnectedSessionId(null)
    setSocketState(nextState)
    lastResizeRef.current = null

    if (
      socket &&
      (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)
    ) {
      socket.close()
    }
  }

  function connectToSession(session: TerminalSessionResponse) {
    if (!token || !activeGroupId) {
      return
    }

    disconnectSocket('idle')
    setPanelError(null)
    setPanelNotice(`Connecting terminal for ${activeGroupId}...`)
    setSocketState('connecting')
    lastResizeRef.current = null

    const targetGroupId = activeGroupId
    setTranscriptsByGroup((current) => ({
      ...current,
      [targetGroupId]: '',
    }))
    const socket = createTerminalWebSocket(session.session_id, token)
    socketRef.current = socket
    closeIntentRef.current = null

    socket.addEventListener('message', (event) => {
      if (socketRef.current !== socket) {
        return
      }

      const payload = parseWebSocketMessage(event.data)
      if (!isRecordLike(payload) || typeof payload.type !== 'string') {
        setPanelError('Invalid terminal websocket payload.')
        return
      }

      if (payload.type === 'terminal.ready') {
        setSocketState('open')
        setConnectedSessionId(session.session_id)
        setPanelNotice(`Terminal connected to ${targetGroupId}.`)
        sendTerminalResize(socket, session.session_id)
        window.setTimeout(() => {
          if (socketRef.current !== socket) {
            return
          }
          sendTerminalResize(socket, session.session_id)
        }, READY_RESIZE_DELAY_MS)
        return
      }

      if (payload.type === 'terminal.output' && typeof payload.data === 'string') {
        appendTranscript(targetGroupId, payload.data)
        return
      }

      if (payload.type === 'terminal.exit') {
        const exitCode =
          typeof payload.exit_code === 'number' ? payload.exit_code : null
        appendTranscript(
          targetGroupId,
          `\n[terminal exited${exitCode !== null ? ` with code ${exitCode}` : ''}]\n`,
        )
        setPanelNotice(
          exitCode !== null ? `Terminal exited with code ${exitCode}.` : 'Terminal exited.',
        )
        setIsClosing(false)
        disconnectSocket('closed')
        void refetch()
        return
      }

      if (payload.type === 'terminal.error') {
        setPanelError(
          typeof payload.error === 'string' ? payload.error : 'Terminal error.',
        )
      }
    })

    socket.addEventListener('error', () => {
      if (socketRef.current !== socket) {
        return
      }
      setSocketState('error')
      setPanelError('Terminal websocket error.')
    })

    socket.addEventListener('close', () => {
      if (socketRef.current !== socket) {
        return
      }

      const closeIntent = closeIntentRef.current
      socketRef.current = null
      closeIntentRef.current = null
      setConnectedSessionId(null)
      setSocketState('closed')
      setIsClosing(false)
      lastResizeRef.current = null

      if (closeIntent === 'session-close') {
        setPanelNotice('Terminal session closed.')
      } else {
        setPanelNotice('Terminal disconnected. Reconnect within 30 seconds if the session is still active.')
      }

      void refetch()
    })
  }

  useEffect(() => {
    return () => {
      disconnectSocket('idle')
    }
  }, [])

  useEffect(() => {
    disconnectSocket('idle')
    setCommandInput('')
    setPanelError(null)
    setPanelNotice(null)
    setIsStarting(false)
    setIsClosing(false)
  }, [activeGroupId])

  useEffect(() => {
    if (!connectedSessionId) {
      return
    }

    const handleWindowResize = () => {
      if (resizeTimerRef.current !== null) {
        window.clearTimeout(resizeTimerRef.current)
      }
      resizeTimerRef.current = window.setTimeout(() => {
        resizeTimerRef.current = null
        const socket = socketRef.current
        if (!socket) {
          return
        }
        sendTerminalResize(socket, connectedSessionId)
      }, RESIZE_THROTTLE_MS)
    }

    window.addEventListener('resize', handleWindowResize)
    return () => {
      window.removeEventListener('resize', handleWindowResize)
      if (resizeTimerRef.current !== null) {
        window.clearTimeout(resizeTimerRef.current)
        resizeTimerRef.current = null
      }
    }
  }, [connectedSessionId, sendTerminalResize])

  async function handleStartTerminal() {
    if (!token || !activeGroupId || !canStartTerminal) {
      return
    }

    try {
      setIsStarting(true)
      setPanelError(null)
      setPanelNotice(null)
      const session = await apiClient.createTerminalSession(token, activeGroupId)
      await refetch()
      connectToSession(session)
    } catch (error) {
      setPanelError(error instanceof Error ? error.message : 'Failed to start terminal.')
    } finally {
      setIsStarting(false)
    }
  }

  async function handleConnectTerminal() {
    if (!currentSession || !canConnectTerminal) {
      return
    }

    connectToSession(currentSession)
  }

  async function handleCloseTerminal() {
    if (!token || !activeGroupId || !currentSession || !canCloseTerminal) {
      return
    }

    let waitingForSocketClose = false

    try {
      setIsClosing(true)
      setPanelError(null)
      setPanelNotice(null)

      const socket = socketRef.current
      if (socket && socket.readyState === WebSocket.OPEN) {
        closeIntentRef.current = 'session-close'
        socket.send(JSON.stringify({ type: 'terminal.close' }))
        setPanelNotice('Closing terminal session...')
        waitingForSocketClose = true
        return
      }

      disconnectSocket('closed')
      await apiClient.closeCurrentTerminalSession(token, activeGroupId)
      await refetch()
      setPanelNotice('Terminal session closed.')
    } catch (error) {
      setPanelError(error instanceof Error ? error.message : 'Failed to close terminal session.')
    } finally {
      if (!waitingForSocketClose) {
        setIsClosing(false)
      }
    }
  }

  function handleCommandSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!activeGroupId) {
      return
    }

    const socket = socketRef.current
    const command = commandInput.trim()

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setPanelError('Terminal is not connected.')
      return
    }

    if (command.length === 0) {
      return
    }

    setPanelError(null)
    socket.send(JSON.stringify({ type: 'terminal.input', data: `${command}\n` }))
    appendTranscript(activeGroupId, `\n> ${command}\n`)
    setCommandInput('')
  }

  const connectLabel =
    currentSession?.status === 'detached' || socketState === 'closed'
      ? 'Reconnect'
      : 'Connect'

  return (
    <section className="panel terminal-panel">
      <div className="terminal-panel-header">
        <div>
          <h3 className="chat-shell-title">Terminal Panel</h3>
          <p className="chat-shell-note">
            Container-only v1 shell for the active workspace. Plain-text transcript only.
          </p>
        </div>
        <span className={getStatusBadgeClass(statusLabel)}>{statusLabel}</span>
      </div>

      {!activeGroupId ? (
        <p className="muted">Select a workspace to manage a terminal session.</p>
      ) : null}

      {activeGroupId ? (
        <div className="terminal-meta-grid">
          <div className="terminal-meta-card">
            <strong>Workspace</strong>
            <span>{activeGroupName ?? activeGroupId}</span>
          </div>
          <div className="terminal-meta-card">
            <strong>Session</strong>
            <span>{currentSession?.session_id ?? '-'}</span>
          </div>
          <div className="terminal-meta-card">
            <strong>Owner</strong>
            <span>{currentSession?.owner_user_id ?? '-'}</span>
          </div>
          <div className="terminal-meta-card">
            <strong>Backend</strong>
            <span>{currentSession?.backend ?? '-'}</span>
          </div>
          <div className="terminal-meta-card">
            <strong>Created</strong>
            <span>{formatDate(currentSession?.created_at ?? null)}</span>
          </div>
          <div className="terminal-meta-card">
            <strong>Reconnect Until</strong>
            <span>{formatDate(currentSession?.reconnect_deadline ?? null)}</span>
          </div>
        </div>
      ) : null}

      {!canUseTerminal ? (
        <p className="muted">Terminal access is limited to owner and admin roles.</p>
      ) : null}

      {canUseTerminal && activeGroupId && isLoading ? (
        <p className="muted">Checking current terminal session...</p>
      ) : null}

      {currentSessionError ? (
        <p className="error-text">
          {currentSessionError instanceof Error
            ? currentSessionError.message
            : 'Failed to load terminal session.'}
        </p>
      ) : null}

      {sessionBlockedByOtherUser ? (
        <p className="error-text">
          Terminal session is currently owned by {currentSession?.owner_user_id}. Forced takeover is disabled in v1.
        </p>
      ) : null}

      {panelError ? <p className="error-text">{panelError}</p> : null}
      {panelNotice ? <p className="muted">{panelNotice}</p> : null}

      <div className="terminal-toolbar">
        <PrimaryButton
          disabled={!canStartTerminal || isStarting || isClosing}
          onClick={handleStartTerminal}
          type="button"
        >
          {isStarting ? 'Starting...' : 'Start Terminal'}
        </PrimaryButton>
        <PrimaryButton
          className="button--ghost"
          disabled={!canConnectTerminal || isStarting || isClosing}
          onClick={handleConnectTerminal}
          type="button"
        >
          {connectLabel}
        </PrimaryButton>
        <PrimaryButton
          className="button--ghost"
          disabled={!canCloseTerminal || isStarting || isClosing}
          onClick={handleCloseTerminal}
          type="button"
        >
          {isClosing ? 'Closing...' : 'Close Session'}
        </PrimaryButton>
        <PrimaryButton
          className="button--ghost"
          disabled={activeTranscript.length === 0}
          onClick={clearCurrentTranscript}
          type="button"
        >
          Clear Output
        </PrimaryButton>
      </div>

      <div className="terminal-transcript" ref={transcriptRef} role="log">
        {activeTranscript.trim().length > 0 ? (
          <pre>{activeTranscript}</pre>
        ) : (
          <p className="muted">
            {connectedSessionId
              ? 'Terminal connected. Run a command below.'
              : 'No terminal output yet.'}
          </p>
        )}
      </div>

      <form className="terminal-command-form" onSubmit={handleCommandSubmit}>
        <input
          className="terminal-command-input"
          disabled={!canSendInput || isClosing}
          onChange={(event) => setCommandInput(event.target.value)}
          placeholder={canSendInput ? 'Enter one shell command' : 'Connect a terminal first'}
          type="text"
          value={commandInput}
        />
        <PrimaryButton disabled={!canSendInput || commandInput.trim().length === 0 || isClosing} type="submit">
          Send
        </PrimaryButton>
      </form>
    </section>
  )
}
