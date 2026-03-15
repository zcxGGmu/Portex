import type { ChangeEvent, FormEvent } from 'react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiClient } from '../../api/client'
import { createWebSocket, subscribeWebSocketMessages } from '../../api/ws'
import {
  useGroupImBindingsQuery,
  useGroupMembersQuery,
  useGroupsQuery,
  useGroupSlotsQuery,
} from '../../hooks/useApi'
import { useAuthStore } from '../../stores/auth'
import { useChatStore } from '../../stores/chat'
import { isStreamEvent } from '../../types/events'
import { MessageList } from './MessageList'
import { ThinkingPanel } from './ThinkingPanel'
import { ToolCallTracker } from './ToolCallTracker'
import { PrimaryButton } from '../ui/PrimaryButton'

const ATTACHMENT_PREVIEW_LIMIT = 6
const SLOT_PREVIEW_LIMIT = 10
const DEFAULT_ROOM_ID = 'main'
const CHAT_WORKSPACE_STORAGE_KEY = 'portex-chat.active-workspace'

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

function buildContextId(groupId: string, roomId: string): string {
  return `${groupId}::${roomId}`
}

function resolveDefaultRoomId(slotIds: string[]): string {
  if (slotIds.includes(DEFAULT_ROOM_ID)) {
    return DEFAULT_ROOM_ID
  }
  return slotIds[0] ?? DEFAULT_ROOM_ID
}

function composePromptMessage(draft: string, uploadedPaths: string[], roomId: string): string {
  const text = draft.trim()
  const roomSection =
    roomId !== DEFAULT_ROOM_ID ? `Conversation room: ${roomId}\n` : ''
  if (uploadedPaths.length === 0) {
    return `${roomSection}${text}`.trim()
  }

  const body = text || 'Please review the uploaded attachments.'
  return `${roomSection}${body}\n\nAttached workspace files:\n${buildAttachmentBulletList(uploadedPaths)}`.trim()
}

function composeVisibleUserMessage(draft: string, uploadedPaths: string[], roomId: string): string {
  const text = draft.trim()
  const roomTag = roomId !== DEFAULT_ROOM_ID ? `[Room: ${roomId}]` : ''
  if (uploadedPaths.length === 0) {
    return [roomTag, text].filter(Boolean).join('\n')
  }

  const attachmentsSection = `[Attachments]\n${buildAttachmentBulletList(uploadedPaths)}`
  const body = text || '[No text]'
  return [roomTag, body, attachmentsSection].filter(Boolean).join('\n\n')
}

function getStoredWorkspaceId(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return window.localStorage.getItem(CHAT_WORKSPACE_STORAGE_KEY)
}

function setStoredWorkspaceId(workspaceId: string): void {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(CHAT_WORKSPACE_STORAGE_KEY, workspaceId)
}

export function ChatPanel() {
  const token = useAuthStore((state) => state.token)
  const currentUser = useAuthStore((state) => state.currentUser)
  const isOwner = currentUser?.role === 'owner'
  const canUploadAttachments = currentUser?.role === 'owner' || currentUser?.role === 'admin'
  const { data: groupsData, isLoading: groupsLoading, error: groupsError } = useGroupsQuery()
  const groups = useMemo(() => groupsData?.groups ?? [], [groupsData])

  const [workspaceFilter, setWorkspaceFilter] = useState('')
  const [selectedGroupIdInput, setSelectedGroupIdInput] = useState<string | null>(() => getStoredWorkspaceId())
  const [selectedRoomByWorkspace, setSelectedRoomByWorkspace] = useState<Record<string, string>>({})
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [attachmentError, setAttachmentError] = useState<string | null>(null)
  const [attachmentNotice, setAttachmentNotice] = useState<string | null>(null)
  const [latestUploadedPaths, setLatestUploadedPaths] = useState<string[]>([])
  const [bindingError, setBindingError] = useState<string | null>(null)
  const [bindingNotice, setBindingNotice] = useState<string | null>(null)
  const [bindingActionTarget, setBindingActionTarget] = useState<string | null>(null)
  const [wsState, setWsState] = useState<'connecting' | 'open' | 'closed' | 'error'>('connecting')
  const wsRef = useRef<WebSocket | null>(null)

  const filteredGroups = useMemo(() => {
    const query = workspaceFilter.trim().toLowerCase()
    if (!query) {
      return groups
    }
    return groups.filter(
      (group) =>
        group.name.toLowerCase().includes(query) || group.group_id.toLowerCase().includes(query),
    )
  }, [groups, workspaceFilter])

  const activeGroupId = useMemo(() => {
    if (selectedGroupIdInput && groups.some((group) => group.group_id === selectedGroupIdInput)) {
      return selectedGroupIdInput
    }
    return groups[0]?.group_id ?? null
  }, [groups, selectedGroupIdInput])
  const activeGroup = groups.find((group) => group.group_id === activeGroupId) ?? null

  const {
    data: slotsData,
    isLoading: slotsLoading,
    error: slotsError,
  } = useGroupSlotsQuery(activeGroupId)
  const availableSlots = slotsData?.slots ?? []
  const slotIds = availableSlots.map((slot) => slot.slot_id)
  const defaultRoomId = useMemo(() => resolveDefaultRoomId(slotIds), [slotIds])
  const activeRoomId = useMemo(() => {
    if (!activeGroupId) {
      return DEFAULT_ROOM_ID
    }
    const storedRoomId = selectedRoomByWorkspace[activeGroupId]
    if (storedRoomId && slotIds.includes(storedRoomId)) {
      return storedRoomId
    }
    return defaultRoomId
  }, [activeGroupId, selectedRoomByWorkspace, slotIds, defaultRoomId])

  const {
    data: membersData,
    isLoading: membersLoading,
    error: membersError,
  } = useGroupMembersQuery(activeGroupId)
  const {
    data: bindingsData,
    isLoading: bindingsLoading,
    error: bindingsQueryError,
    refetch: refetchBindings,
  } = useGroupImBindingsQuery(activeGroupId, isOwner)
  const bindings = bindingsData?.bindings ?? []

  const messages = useChatStore((state) => state.messages)
  const streamEvents = useChatStore((state) => state.streamEvents)
  const draft = useChatStore((state) => state.draft)
  const isRunning = useChatStore((state) => state.isRunning)
  const activeRunId = useChatStore((state) => state.activeRunId)
  const addMessage = useChatStore((state) => state.addMessage)
  const addStreamEvent = useChatStore((state) => state.addStreamEvent)
  const switchContext = useChatStore((state) => state.switchContext)
  const setDraft = useChatStore((state) => state.setDraft)
  const clearRunState = useChatStore((state) => state.clearRunState)
  const clearMessages = useChatStore((state) => state.clearMessages)

  const targetGroupFolder = activeGroupId ?? 'group-demo'
  const activeContextId = useMemo(
    () => buildContextId(targetGroupFolder, activeRoomId),
    [targetGroupFolder, activeRoomId],
  )
  const canSwitchContext = !isRunning && !isUploading

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
    switchContext(activeContextId)
  }, [activeContextId, switchContext])

  useEffect(() => {
    setSelectedFiles([])
    setAttachmentError(null)
    setAttachmentNotice(null)
    setLatestUploadedPaths([])
    setBindingError(null)
    setBindingNotice(null)
    setBindingActionTarget(null)
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

  function handleWorkspaceSwitch(nextGroupId: string) {
    if (!canSwitchContext) {
      return
    }
    setSelectedGroupIdInput(nextGroupId)
    setStoredWorkspaceId(nextGroupId)
    setWsState('connecting')
    setSelectedFiles([])
    setAttachmentError(null)
    setAttachmentNotice(null)
  }

  function handleRoomSwitch(nextRoomId: string) {
    if (!canSwitchContext || !activeGroupId) {
      return
    }
    setSelectedRoomByWorkspace((current) => ({
      ...current,
      [activeGroupId]: nextRoomId,
    }))
  }

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

      const promptMessage = composePromptMessage(trimmed, uploadedPaths, activeRoomId)
      if (!promptMessage.trim()) {
        return
      }
      const visibleMessage = composeVisibleUserMessage(trimmed, uploadedPaths, activeRoomId)
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

  async function handleBindEndpoint(imJid: string) {
    if (!token || !activeGroupId || !isOwner) {
      return
    }
    try {
      setBindingActionTarget(imJid)
      setBindingError(null)
      setBindingNotice(null)
      await apiClient.bindGroupImEndpoint(token, activeGroupId, imJid)
      await refetchBindings()
      setBindingNotice(`Bound ${imJid} to ${activeGroupId}.`)
    } catch (error) {
      setBindingError(error instanceof Error ? error.message : 'Failed to bind endpoint')
    } finally {
      setBindingActionTarget(null)
    }
  }

  async function handleUnbindEndpoint(imJid: string) {
    if (!token || !activeGroupId || !isOwner) {
      return
    }
    try {
      setBindingActionTarget(imJid)
      setBindingError(null)
      setBindingNotice(null)
      await apiClient.unbindGroupImEndpoint(token, activeGroupId, imJid)
      await refetchBindings()
      setBindingNotice(`Unbound ${imJid}.`)
    } catch (error) {
      setBindingError(error instanceof Error ? error.message : 'Failed to unbind endpoint')
    } finally {
      setBindingActionTarget(null)
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
          <label className="field chat-workspace-filter" htmlFor="chat-workspace-filter">
            <span>Search Workspace</span>
            <input
              id="chat-workspace-filter"
              onChange={(event) => setWorkspaceFilter(event.target.value)}
              placeholder="Filter by name or id"
              type="text"
              value={workspaceFilter}
            />
          </label>
          <label className="field chat-workspace-select" htmlFor="chat-workspace-select">
            <span>Active Workspace</span>
            <select
              disabled={!canSwitchContext || filteredGroups.length === 0}
              id="chat-workspace-select"
              onChange={(event) => handleWorkspaceSwitch(event.target.value)}
              value={activeGroupId ?? ''}
            >
              {groupsLoading ? <option value="">Loading...</option> : null}
              {!groupsLoading && filteredGroups.length === 0 ? <option value="">No workspace match</option> : null}
              {filteredGroups.map((group) => (
                <option key={group.group_id} value={group.group_id}>
                  {group.name} ({group.group_id})
                </option>
              ))}
            </select>
          </label>
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
              <p className="muted chat-shell-note">Workspace ID: {activeGroup.group_id}</p>
            </>
          ) : null}
        </section>
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">Conversation Rooms</h3>
          {!activeGroupId ? <p className="muted">Workspace unavailable.</p> : null}
          {activeGroupId && slotsLoading ? <p className="muted">Loading slots...</p> : null}
          {slotsError ? (
            <p className="error-text">
              {slotsError instanceof Error ? slotsError.message : 'Failed to load slots'}
            </p>
          ) : null}
          {!slotsLoading && !slotsError && availableSlots.length === 0 ? (
            <p className="muted">No slots configured.</p>
          ) : null}
          <ul className="chat-room-list">
            {availableSlots.slice(0, SLOT_PREVIEW_LIMIT).map((slot) => (
              <li key={slot.slot_id}>
                <button
                  className={`chat-room-button ${activeRoomId === slot.slot_id ? 'active' : ''}`}
                  disabled={!canSwitchContext}
                  onClick={() => handleRoomSwitch(slot.slot_id)}
                  type="button"
                >
                  <span>{slot.title}</span>
                  <span className="muted">{slot.slot_id}</span>
                </button>
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
                    <li
                      className="chat-attachment-item"
                      key={`${file.name}-${file.size}-${file.lastModified}-${index}`}
                    >
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
          <p className="muted chat-shell-note">
            Active context: {targetGroupFolder} / {activeRoomId}
          </p>
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
        <section className="panel chat-shell-card">
          <h3 className="chat-shell-title">IM Bindings</h3>
          {!isOwner ? <p className="muted">Only owner can manage IM endpoint bindings.</p> : null}
          {isOwner && !activeGroupId ? <p className="muted">Select a workspace first.</p> : null}
          {isOwner && activeGroupId && bindingsLoading ? <p className="muted">Loading bindings...</p> : null}
          {bindingsQueryError ? (
            <p className="error-text">
              {bindingsQueryError instanceof Error ? bindingsQueryError.message : 'Failed to load bindings'}
            </p>
          ) : null}
          {bindingError ? <p className="error-text">{bindingError}</p> : null}
          {bindingNotice ? <p className="muted">{bindingNotice}</p> : null}
          {isOwner && !bindingsLoading && !bindingsQueryError && bindings.length === 0 ? (
            <p className="muted">No IM endpoints available.</p>
          ) : null}
          <ul className="chat-binding-list">
            {bindings.map((binding) => {
              const isBoundHere = binding.bound_to_current_group
              const isActionPending = bindingActionTarget === binding.im_jid
              return (
                <li className="chat-binding-item" key={binding.im_jid}>
                  <div className="chat-binding-meta">
                    <strong>{binding.im_jid}</strong>
                    <span className="muted">
                      {binding.channel} · {binding.binding_state}
                    </span>
                    <span className="muted">
                      target: {binding.target_group_id ?? '-'} / fallback: {binding.fallback_group_id}
                    </span>
                  </div>
                  {isOwner ? (
                    <PrimaryButton
                      className="button--ghost"
                      disabled={Boolean(bindingActionTarget) || isRunning}
                      onClick={() =>
                        isBoundHere
                          ? handleUnbindEndpoint(binding.im_jid)
                          : handleBindEndpoint(binding.im_jid)
                      }
                      type="button"
                    >
                      {isActionPending
                        ? 'Working...'
                        : isBoundHere
                          ? 'Unbind'
                          : 'Bind Here'}
                    </PrimaryButton>
                  ) : null}
                </li>
              )
            })}
          </ul>
        </section>
      </aside>
    </section>
  )
}
