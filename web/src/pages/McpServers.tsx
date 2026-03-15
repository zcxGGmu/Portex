import { type CSSProperties, useEffect, useMemo, useState } from 'react'

import { apiClient, type McpTransport, type UpdateMcpServerPayload } from '../api/client'
import { AppLayout } from '../components/layout/AppLayout'
import { PrimaryButton } from '../components/ui/PrimaryButton'
import { useMcpServerDetailQuery, useMcpServersQuery } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'

const SERVER_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/

const CONTROL_STYLE: CSSProperties = {
  width: '100%',
  border: '1px solid var(--border)',
  borderRadius: '10px',
  padding: '0.62rem 0.75rem',
  font: 'inherit',
  backgroundColor: '#fff',
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

function defaultPayloadForTransport(transport: McpTransport): UpdateMcpServerPayload {
  if (transport === 'stdio') {
    return {
      transport,
      command: 'python',
      args: [],
      env: {},
      description: '',
    }
  }

  return {
    transport,
    url: 'https://example.com/mcp',
    headers: {},
    description: '',
  }
}

function parseStringMap(text: string, label: string): Record<string, string> {
  const normalized = text.trim()
  if (!normalized) {
    return {}
  }

  let value: unknown
  try {
    value = JSON.parse(normalized)
  } catch {
    throw new Error(`${label} must be a valid JSON object`)
  }

  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be a JSON object with string values`)
  }

  const result: Record<string, string> = {}
  for (const [key, item] of Object.entries(value)) {
    if (typeof item !== 'string') {
      throw new Error(`${label} must be a JSON object with string values`)
    }
    result[key] = item
  }

  return result
}

export function McpServers() {
  const token = useAuthStore((state) => state.token)
  const {
    data: serversData,
    isLoading: serversLoading,
    error: serversError,
    refetch: refetchServers,
  } = useMcpServersQuery()
  const servers = useMemo(() => serversData?.servers ?? [], [serversData])
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null)
  const [createServerId, setCreateServerId] = useState('')
  const [createTransport, setCreateTransport] = useState<McpTransport>('stdio')
  const [formTransport, setFormTransport] = useState<McpTransport>('stdio')
  const [description, setDescription] = useState('')
  const [command, setCommand] = useState('')
  const [argsInput, setArgsInput] = useState('')
  const [envInput, setEnvInput] = useState('{}')
  const [url, setUrl] = useState('')
  const [headersInput, setHeadersInput] = useState('{}')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<string | null>(null)

  const activeServerId = useMemo(() => {
    if (selectedServerId && servers.some((server) => server.server_id === selectedServerId)) {
      return selectedServerId
    }
    return servers[0]?.server_id ?? null
  }, [selectedServerId, servers])

  const {
    data: serverDetail,
    isLoading: detailLoading,
    error: detailError,
    refetch: refetchDetail,
  } = useMcpServerDetailQuery(activeServerId, Boolean(activeServerId))

  useEffect(() => {
    if (!serverDetail) {
      return
    }

    setFormTransport(serverDetail.transport)
    setDescription(serverDetail.description ?? '')
    setCommand(serverDetail.command ?? '')
    setArgsInput((serverDetail.args ?? []).join('\n'))
    setEnvInput(JSON.stringify(serverDetail.env ?? {}, null, 2))
    setUrl(serverDetail.url ?? '')
    setHeadersInput(JSON.stringify(serverDetail.headers ?? {}, null, 2))
  }, [serverDetail])

  async function handleCreateServer() {
    if (!token) {
      return
    }

    const normalizedServerId = createServerId.trim()
    if (!SERVER_ID_PATTERN.test(normalizedServerId)) {
      setActionError('Server id must match [A-Za-z0-9][A-Za-z0-9._-]*')
      setActionNotice(null)
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateMcpServer(token, normalizedServerId, defaultPayloadForTransport(createTransport))
      setCreateServerId('')
      setSelectedServerId(normalizedServerId)
      await refetchServers()
      await refetchDetail()
      setActionNotice('MCP server created.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to create MCP server')
    }
  }

  async function handleSaveServer() {
    if (!token || !activeServerId) {
      return
    }

    setActionError(null)
    setActionNotice(null)

    let payload: UpdateMcpServerPayload
    try {
      if (formTransport === 'stdio') {
        const normalizedCommand = command.trim()
        if (!normalizedCommand) {
          throw new Error('Command is required for stdio transport')
        }

        payload = {
          transport: 'stdio',
          command: normalizedCommand,
          args: argsInput
            .split('\n')
            .map((item) => item.trim())
            .filter(Boolean),
          env: parseStringMap(envInput, 'Env'),
          description,
        }
      } else {
        const normalizedUrl = url.trim()
        if (!normalizedUrl) {
          throw new Error('URL is required for http/sse transport')
        }

        payload = {
          transport: formTransport,
          url: normalizedUrl,
          headers: parseStringMap(headersInput, 'Headers'),
          description,
        }
      }
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Invalid MCP server payload')
      return
    }

    try {
      await apiClient.updateMcpServer(token, activeServerId, payload)
      await refetchServers()
      await refetchDetail()
      setActionNotice('MCP server saved.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to save MCP server')
    }
  }

  async function handleToggleState() {
    if (!token || !activeServerId || !serverDetail) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.updateMcpServerState(token, activeServerId, !serverDetail.enabled)
      await refetchServers()
      await refetchDetail()
      setActionNotice(serverDetail.enabled ? 'MCP server disabled.' : 'MCP server enabled.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to update MCP server state')
    }
  }

  async function handleDeleteServer() {
    if (!token || !activeServerId) {
      return
    }

    setActionError(null)
    setActionNotice(null)
    try {
      await apiClient.deleteMcpServer(token, activeServerId)
      setSelectedServerId(null)
      await refetchServers()
      setActionNotice('MCP server deleted.')
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Failed to delete MCP server')
    }
  }

  return (
    <AppLayout title="MCP Servers">
      <section className="panel">
        <h2 style={{ marginTop: 0 }}>My MCP Servers</h2>
        <div className="memory-toolbar">
          <div className="field" style={{ minWidth: '260px' }}>
            <span>New Server ID</span>
            <input
              onChange={(event) => setCreateServerId(event.target.value)}
              placeholder="local-cli"
              type="text"
              value={createServerId}
            />
          </div>
          <div className="field" style={{ minWidth: '180px' }}>
            <span>Transport</span>
            <select
              onChange={(event) => setCreateTransport(event.target.value as McpTransport)}
              style={CONTROL_STYLE}
              value={createTransport}
            >
              <option value="stdio">stdio</option>
              <option value="http">http</option>
              <option value="sse">sse</option>
            </select>
          </div>
          <div className="memory-toolbar-actions">
            <PrimaryButton onClick={handleCreateServer} type="button">
              Create
            </PrimaryButton>
            <PrimaryButton className="button--ghost" onClick={() => refetchServers()} type="button">
              Refresh
            </PrimaryButton>
          </div>
        </div>

        {actionError ? <p className="error-text">{actionError}</p> : null}
        {actionNotice ? <p className="muted">{actionNotice}</p> : null}

        <div className="memory-layout">
          <aside className="memory-sidebar">
            <h3 style={{ marginTop: 0 }}>Server List</h3>
            {serversLoading ? <p className="muted">Loading MCP servers...</p> : null}
            {serversError ? (
              <p className="error-text">
                {serversError instanceof Error ? serversError.message : 'Failed to load MCP servers'}
              </p>
            ) : null}
            {!serversLoading && servers.length === 0 ? <p className="muted">No MCP servers yet.</p> : null}
            <div className="memory-file-list">
              {servers.map((server) => (
                <button
                  className={`memory-file-button ${activeServerId === server.server_id ? 'active' : ''}`}
                  key={server.server_id}
                  onClick={() => {
                    setSelectedServerId(server.server_id)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                  type="button"
                >
                  <strong>{server.server_id}</strong>
                  <span className="muted">
                    {server.transport} · {server.enabled ? 'Enabled' : 'Disabled'} · {formatDate(server.updated_at)}
                  </span>
                </button>
              ))}
            </div>
          </aside>

          <div>
            <h3 style={{ marginTop: 0 }}>{activeServerId ? `Editing: ${activeServerId}` : 'Server Editor'}</h3>
            {!activeServerId ? <p className="muted">Create an MCP server or select one from the list.</p> : null}
            {activeServerId && detailLoading ? <p className="muted">Loading MCP server...</p> : null}
            {detailError ? (
              <p className="error-text">
                {detailError instanceof Error ? detailError.message : 'Failed to load MCP server'}
              </p>
            ) : null}
            {activeServerId && serverDetail ? (
              <>
                <div className="memory-toolbar-actions" style={{ marginBottom: '0.75rem' }}>
                  <PrimaryButton className="button--ghost" onClick={handleToggleState} type="button">
                    {serverDetail.enabled ? 'Disable' : 'Enable'}
                  </PrimaryButton>
                  <PrimaryButton className="button--ghost" onClick={handleDeleteServer} type="button">
                    Delete
                  </PrimaryButton>
                </div>

                <div className="form-stack">
                  <label className="field">
                    <span>Transport</span>
                    <select
                      onChange={(event) => setFormTransport(event.target.value as McpTransport)}
                      style={CONTROL_STYLE}
                      value={formTransport}
                    >
                      <option value="stdio">stdio</option>
                      <option value="http">http</option>
                      <option value="sse">sse</option>
                    </select>
                  </label>

                  {formTransport === 'stdio' ? (
                    <>
                      <label className="field">
                        <span>Command</span>
                        <input
                          onChange={(event) => setCommand(event.target.value)}
                          placeholder="uvx"
                          type="text"
                          value={command}
                        />
                      </label>
                      <label className="field">
                        <span>Args (one per line)</span>
                        <textarea
                          onChange={(event) => setArgsInput(event.target.value)}
                          style={{ ...CONTROL_STYLE, minHeight: '90px', resize: 'vertical' }}
                          value={argsInput}
                        />
                      </label>
                      <label className="field">
                        <span>Env (JSON object)</span>
                        <textarea
                          onChange={(event) => setEnvInput(event.target.value)}
                          style={{ ...CONTROL_STYLE, minHeight: '130px', resize: 'vertical' }}
                          value={envInput}
                        />
                      </label>
                    </>
                  ) : (
                    <>
                      <label className="field">
                        <span>URL</span>
                        <input
                          onChange={(event) => setUrl(event.target.value)}
                          placeholder="https://example.com/mcp"
                          type="text"
                          value={url}
                        />
                      </label>
                      <label className="field">
                        <span>Headers (JSON object)</span>
                        <textarea
                          onChange={(event) => setHeadersInput(event.target.value)}
                          style={{ ...CONTROL_STYLE, minHeight: '130px', resize: 'vertical' }}
                          value={headersInput}
                        />
                      </label>
                    </>
                  )}

                  <label className="field">
                    <span>Description</span>
                    <textarea
                      onChange={(event) => setDescription(event.target.value)}
                      style={{ ...CONTROL_STYLE, minHeight: '90px', resize: 'vertical' }}
                      value={description}
                    />
                  </label>
                </div>

                <div className="memory-editor-actions">
                  <PrimaryButton onClick={handleSaveServer} type="button">
                    Save MCP Server
                  </PrimaryButton>
                  <span className="muted">
                    State: {serverDetail.enabled ? 'enabled' : 'disabled'} · Created:{' '}
                    {formatDate(serverDetail.created_at)} · Updated: {formatDate(serverDetail.updated_at)}
                  </span>
                </div>
              </>
            ) : null}
          </div>
        </div>
      </section>
    </AppLayout>
  )
}
