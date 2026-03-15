import type { ChangeEvent, FormEvent } from 'react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiClient } from '../../api/client'
import { createWebSocket, subscribeWebSocketMessages } from '../../api/ws'
import { useGroupMembersQuery, useGroupsQuery, useGroupSlotsQuery } from '../../hooks/useApi'
import { useAuthStore } from '../../stores/auth'
import { useChatStore } from '../../stores/chat'
import { isStreamEvent } from '../../types/events'
import { MessageList } from './MessageList'
import { ThinkingPanel } from './ThinkingPanel'
import { ToolCallTracker } from './ToolCallTracker'
import { PrimaryButton } from '../ui/PrimaryButton'

const ATTACHMENT_PREVIEW_LIMIT = 6

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${bytes} B`
}

function buildAttachmentBulletList(paths: string[]): string {
  return paths.map((path) => `- ${path}`).join('\n')
}

function composePromptMessage(draft: string, uploadedPaths: string[]): string {
  const text = draft.trim()
  if (uploadedPaths.length === 0) {
    return text
  }

  const body = text || 'Please review the uploaded attachments.'
  return `${body}\n\nAttached workspace files:\n${buildAttachmentBulletList(uploadedPaths)}`
}

function composeVisibleUserMessage(draft: string, uploadedPaths: string[]): string {
  const text = draft.trim()
  if (uploadedPaths.length === 0) {
    return text
  }

  const attachmentsSection = `[Attachments]\n${buildAttachmentBulletList(uploadedPaths)}`
  if (!text) {
    return attachmentsSection
  }
  return `${text}\n\n${attachmentsSection}`
}

export function ChatPanel() {
  const token = useAuthStore((state) => state.token)
  const currentUser = useAuthStore((state) => state.currentUser)
  const { data: groupsData, isLoading: groupsLoading, error: groupsError } = useGroupsQuery()
  const groups = groupsData?.groups ?? []
  const activeGroup = groups[0] ?? null
  const activeGroupId = activeGroup?.group_id ?? null
  const canUploadAttachments = currentUser?.role === 'owner' || currentUser?.role === 'admin'
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
  const clearRunState = useChatStore((state) => state.clearRunState)
  const clearMessages = useChatStore((state) => state.clearMessages)
  const wsRef = useRef<WebSocket | null>(null)
  const [wsState, setWsState] = useState<'connecting' | 'open' | 'closed' | 'error'>('connecting')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [attachmentError, setAttachmentError] = useState<string | null>(null)
  const [attachmentNotice, setAttachmentNotice] = useState<string | null>(null)
  const [latestUploadedPaths, setLatestUploadedPaths] = useState<string[]>([])

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
    setSelectedFiles([])
    setAttachmentError(null)
    setAttachmentNotice(null)
    setLatestUploadedPaths([])
  }, [targetGroupFolder])

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

  function handleAttachmentSelection(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (files.length === 0) {
      return
    }
    setSelectedFiles((current) => [...current, ...files])
    setAttachmentError(null)
    setAttachmentNotice(null)
    event.target.value = ''
  }

  function removeSelectedFile(index: number) {
    setSelectedFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isRunning || isUploading) {
      return
    }

    const trimmed = draft.trim()
    if (!trimmed && selectedFiles.length === 0) {
      return
    }

    if (selectedFiles.length > 0 && !canUploadAttachments) {
      setAttachmentError('Current role cannot upload attachments in chat.')
      return
    }

    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      setAttachmentError('Realtime link unavailable. Please wait for reconnect.')
      return
    }

    let uploadedPaths: string[] = []
    try {
      setAttachmentError(null)
      setAttachmentNotice(null)
      if (selectedFiles.length > 0) {
        if (!token || !activeGroupId) {
          setAttachmentError('Workspace context is not ready for attachment upload.')
          return
        }
        setIsUploading(true)
        const uploaded = await apiClient.uploadChatAttachments(token, activeGroupId, selectedFiles)
        uploadedPaths = uploaded.files
        setLatestUploadedPaths(uploadedPaths)
        setAttachmentNotice(
          `Uploaded ${uploadedPaths.length} attachment${uploadedPaths.length === 1 ? '' : 's'} to workspace.`,
        )
      }

      const promptMessage = composePromptMessage(trimmed, uploadedPaths)
      if (!promptMessage.trim()) {
        return
      }
      const visibleMessage = composeVisibleUserMessage(trimmed, uploadedPaths)
      setDraft('')
      addMessage({ role: 'user', content: visibleMessage })
      setSelectedFiles([])
      wsRef.current?.send(promptMessage)
    } catch (error) {
      setAttachmentError(error instanceof Error ? error.message : 'Failed to upload chat attachments')
    } finally {
      setIsUploading(false)
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
          {groupsError ? (
            <p className="error-text">
              {groupsError instanceof Error ? groupsError.message : 'Failed to load workspaces'}
            </p>
          ) : null}
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
          {slotsError ? (
            <p className="error-text">
              {slotsError instanceof Error ? slotsError.message : 'Failed to load slots'}
            </p>
          ) : null}
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
          {membersError ? (
            <p className="error-text">
              {membersError instanceof Error ? membersError.message : 'Failed to load members'}
            </p>
          ) : null}
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
            <section className="chat-attachments">
              <div className="chat-attachment-toolbar">
                <label
                  className={`button button--ghost ${
                    !canUploadAttachments || !activeGroupId || isRunning || isUploading ? 'button--disabled' : ''
                  }`}
                >
                  {isUploading ? 'Uploading...' : 'Attach Files'}
                  <input
                    disabled={!canUploadAttachments || !activeGroupId || isRunning || isUploading}
                    hidden
                    multiple
                    onChange={handleAttachmentSelection}
                    type="file"
                  />
                </label>
                <PrimaryButton
                  className="button--ghost"
                  disabled={selectedFiles.length === 0 || isUploading}
                  onClick={() => setSelectedFiles([])}
                  type="button"
                >
                  Clear Attachments
                </PrimaryButton>
              </div>
              {selectedFiles.length === 0 ? <p className="muted">No attachments selected.</p> : null}
              {selectedFiles.length > 0 ? (
                <ul className="chat-attachment-list">
                  {selectedFiles.map((file, index) => (
                    <li className="chat-attachment-item" key={`${file.name}-${file.size}-${file.lastModified}-${index}`}>
                      <div className="chat-attachment-meta">
                        <strong>{file.name}</strong>
                        <span className="muted">{formatFileSize(file.size)}</span>
                      </div>
                      <button
                        className="chat-attachment-remove"
                        onClick={() => removeSelectedFile(index)}
                        type="button"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
              {attachmentError ? <p className="error-text">{attachmentError}</p> : null}
              {attachmentNotice ? <p className="muted">{attachmentNotice}</p> : null}
            </section>
            <div className="chat-form-actions">
              <PrimaryButton
                disabled={
                  (draft.trim().length === 0 && selectedFiles.length === 0) ||
                  isRunning ||
                  isUploading ||
                  wsState !== 'open'
                }
                type="submit"
              >
                Send
              </PrimaryButton>
              <span className="muted">
                {wsState === 'open'
                  ? 'Realtime link connected'
                  : wsState === 'connecting'
                    ? 'Connecting realtime link...'
                    : 'Realtime link unavailable'}
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
          {latestUploadedPaths.length > 0 ? (
            <div className="chat-recent-uploads">
              <p className="chat-shell-note">Recent uploads</p>
              <ul className="chat-shell-list">
                {latestUploadedPaths.slice(0, ATTACHMENT_PREVIEW_LIMIT).map((path) => (
                  <li key={path}>
                    <span>{path}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
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
