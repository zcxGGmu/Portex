export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CurrentUser {
  id: string
  username: string
  role: string
  status: string
}

export interface SettingsProviderResponse {
  enabled: boolean
  base_url: string
  default_model: string
  has_api_key: boolean
  updated_at: string | null
}

export interface UpdateSettingsProviderPayload {
  enabled: boolean
  base_url: string
  default_model: string
  api_key?: string
}

export interface SettingsChannelsResponse {
  feishu_enabled: boolean
  feishu_app_id: string
  feishu_has_app_secret: boolean
  feishu_has_encrypt_key: boolean
  feishu_has_verification_token: boolean
  telegram_enabled: boolean
  telegram_has_bot_token: boolean
  updated_at: string | null
}

export interface UpdateSettingsChannelsPayload {
  feishu_enabled: boolean
  feishu_app_id: string
  feishu_app_secret: string
  feishu_encrypt_key: string
  feishu_verification_token: string
  telegram_enabled: boolean
  telegram_bot_token: string
}

export interface SettingsRegistrationResponse {
  allow_registration: boolean
  require_invite_code: boolean
  updated_at: string | null
}

export interface SettingsAppearanceResponse {
  app_name: string
  ai_name: string
  ai_avatar_emoji: string
  ai_avatar_color: string
  updated_at: string | null
}

export interface UpdateSettingsAppearancePayload {
  app_name: string
  ai_name: string
  ai_avatar_emoji: string
  ai_avatar_color: string
}

export interface SettingsSystemResponse {
  default_execution_mode: 'openai' | 'host' | 'container'
  allow_host_execution: boolean
  updated_at: string | null
}

export interface UpdateSettingsSystemPayload {
  default_execution_mode: 'openai' | 'host' | 'container'
  allow_host_execution: boolean
}

export interface GroupSummary {
  group_id: string
  name: string
}

export interface GroupMemberSummary {
  group_id: string
  user_id: string
  role: string
  joined_at: string
}

export interface GroupMemberListResponse {
  members: GroupMemberSummary[]
}

export interface ConversationSlotSummary {
  group_id: string
  slot_id: string
  title: string
  created_by: string | null
  created_at: string
}

export interface ConversationSlotListResponse {
  slots: ConversationSlotSummary[]
}

export interface GroupImBindingSummary {
  im_jid: string
  name: string
  channel: 'telegram' | 'feishu'
  fallback_group_id: string
  binding_state: 'unbound' | 'bound' | 'orphaned'
  target_group_id: string | null
  target_group_name: string | null
  bound_to_current_group: boolean
}

export interface GroupImBindingListResponse {
  bindings: GroupImBindingSummary[]
}

export type TerminalBackend = 'docker_container'

export type TerminalSessionStatus = 'created' | 'attached' | 'detached' | 'closed' | 'exited'
export type TerminalHistorySearchSort = 'relevance' | 'newest' | 'oldest'

export interface TerminalSessionResponse {
  session_id: string
  group_id: string
  owner_user_id: string
  backend: TerminalBackend
  container_name: string | null
  status: TerminalSessionStatus
  created_at: string
  last_attached_at: string | null
  reconnect_deadline: string | null
}

export interface TerminalSessionHistorySummary {
  session: TerminalSessionResponse
  snapshot_at: string
  output_bytes: number
  history_max_bytes: number
  truncated: boolean
}

export interface TerminalSessionHistoryDetailResponse {
  session: TerminalSessionResponse
  snapshot_at: string
  output: string
  output_bytes: number
  history_max_bytes: number
  truncated: boolean
}

export interface TerminalSessionHistoryTimelineResponse {
  limit: number
  offset: number
  has_more: boolean
  items: TerminalSessionHistorySummary[]
}

export interface TerminalSessionHistorySearchMatch {
  session: TerminalSessionResponse
  snapshot_at: string
  match_count: number
  snippets: string[]
  snippet_matches: TerminalSessionHistorySearchSnippet[]
}

export interface TerminalSessionHistorySearchSnippet {
  text: string
  match_index: number
  match_offset: number
}

export interface TerminalSessionHistorySearchResponse {
  query: string
  limit: number
  offset: number
  total: number
  has_more: boolean
  items: TerminalSessionHistorySearchMatch[]
}

export interface TerminalWorkspaceSummary {
  group_id: string
  group_name: string
  chat_accessible: boolean
  session: TerminalSessionResponse | null
  history: TerminalSessionHistorySummary | null
}

export interface TerminalWorkspaceListResponse {
  items: TerminalWorkspaceSummary[]
}

export interface DeleteTerminalSessionResponse {
  status: 'closed'
}

export interface HealthResponse {
  status: string
  version: string
}

export interface WorkspaceFileEntry {
  name: string
  path: string
  type: 'file' | 'directory'
  size: number
  modified_at: string
}

export interface WorkspaceFileListResponse {
  current_path: string
  entries: WorkspaceFileEntry[]
}

export interface WorkspaceFileContentResponse {
  path: string
  content: string
  size: number
}

export interface MemoryGlobalResponse {
  content: string
  updated_at: string | null
  size: number
}

export interface WorkspaceMemoryFileEntry {
  path: string
  name: string
  updated_at: string
  size: number
}

export interface WorkspaceMemoryFileListResponse {
  files: WorkspaceMemoryFileEntry[]
}

export interface WorkspaceMemoryFileResponse {
  path: string
  content: string
  updated_at: string | null
  size: number
}

export interface WorkspaceMemorySearchResponse {
  hits: { path: string }[]
}

export interface SkillSummary {
  skill_id: string
  enabled: boolean
  updated_at: string
  size: number
}

export interface SkillListResponse {
  skills: SkillSummary[]
}

export interface SkillDetailResponse {
  skill_id: string
  enabled: boolean
  updated_at: string
  size: number
  content: string
}

export type McpTransport = 'stdio' | 'http' | 'sse'

export interface McpServerSummary {
  server_id: string
  transport: McpTransport
  enabled: boolean
  updated_at: string
}

export interface McpServerListResponse {
  servers: McpServerSummary[]
}

export interface McpServerDetailResponse {
  server_id: string
  transport: McpTransport
  enabled: boolean
  description: string | null
  created_at: string
  updated_at: string
  command: string | null
  args: string[] | null
  env: Record<string, string> | null
  url: string | null
  headers: Record<string, string> | null
}

export interface UpdateMcpServerPayload {
  transport: McpTransport
  command?: string
  args?: string[]
  env?: Record<string, string>
  url?: string
  headers?: Record<string, string>
  description?: string
}

export interface MonitorBackendHealth {
  backend: string
  status: 'ok' | 'error'
  detail: string
}

export interface MonitorHealth {
  api_status: string
  version: string
  coordinator_status: string
  backends: MonitorBackendHealth[]
}

export interface MonitorQueueGroup {
  group_id: string
  queued_runs: number
  running_runs: number
  active_run_id: string | null
  active_backend: string | null
}

export interface MonitorRunRecovery {
  attempted: boolean
  reason: string | null
  succeeded: boolean | null
}

export interface MonitorRunSummary {
  run_id: string
  group_id: string
  chat_jid: string
  user_id: string
  source: 'web' | 'im' | 'scheduled'
  slot_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout'
  backend: string | null
  requested_mode: 'openai' | 'host' | 'container' | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  error: string | null
  timeout_ms: number | null
  recovery: MonitorRunRecovery
}

export interface MonitorResponse {
  health: MonitorHealth
  queue: {
    groups: MonitorQueueGroup[]
  }
  runs: {
    items: MonitorRunSummary[]
  }
}

export interface UsageSummary {
  total_messages: number
  total_runs: number
  total_user_messages: number
  total_assistant_messages: number
  total_active_days: number
}

export interface UsageDailyBreakdown {
  date: string
  message_count: number
  run_count: number
  user_message_count: number
  assistant_message_count: number
}

export interface UsageChannelBreakdown {
  channel: 'web' | 'feishu' | 'telegram'
  message_count: number
  run_count: number
}

export interface UsageStatsResponse {
  days: number
  summary: UsageSummary
  daily: UsageDailyBreakdown[]
  channels: UsageChannelBreakdown[]
}

export interface AuditMessage {
  message_id: string
  chat_jid: string
  group_id: string
  channel: 'web' | 'feishu' | 'telegram'
  run_id: string | null
  external_message_id: string | null
  sender: string
  is_from_me: boolean
  slot_id: string
  content: string | null
  timestamp: string
}

export interface AuditMessageListResponse {
  limit: number
  group_id: string | null
  has_more: boolean
  items: AuditMessage[]
}

interface RequestOptions extends RequestInit {
  token?: string | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  details: unknown

  constructor(message: string, status: number, details: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, body, ...restOptions } = options
  const resolvedHeaders = new Headers(headers)

  if (!(body instanceof FormData) && !resolvedHeaders.has('Content-Type')) {
    resolvedHeaders.set('Content-Type', 'application/json')
  }

  if (token) {
    resolvedHeaders.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...restOptions,
    body,
    headers: resolvedHeaders,
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type')
    const details = contentType?.includes('application/json')
      ? await response.json()
      : await response.text()

    const detailMessage =
      typeof details === 'object' &&
      details !== null &&
      'detail' in details &&
      typeof (details as { detail: unknown }).detail === 'string'
        ? (details as { detail: string }).detail
        : `Request failed with status ${response.status}`

    throw new ApiError(detailMessage, response.status, details)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

async function requestBlob(path: string, options: RequestOptions = {}): Promise<Blob> {
  const { token, headers, body, ...restOptions } = options
  const resolvedHeaders = new Headers(headers)

  if (token) {
    resolvedHeaders.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...restOptions,
    body,
    headers: resolvedHeaders,
  })

  if (!response.ok) {
    const contentType = response.headers.get('content-type')
    const details = contentType?.includes('application/json')
      ? await response.json()
      : await response.text()

    const detailMessage =
      typeof details === 'object' &&
      details !== null &&
      'detail' in details &&
      typeof (details as { detail: unknown }).detail === 'string'
        ? (details as { detail: string }).detail
        : `Request failed with status ${response.status}`

    throw new ApiError(detailMessage, response.status, details)
  }

  return response.blob()
}

function encodePathSegments(path: string): string {
  return path
    .split('/')
    .filter(Boolean)
    .map((segment) => encodeURIComponent(segment))
    .join('/')
}

export const apiClient = {
  login(username: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },
  getCurrentUser(token: string): Promise<CurrentUser> {
    return request<CurrentUser>('/users/me', { token })
  },
  getSettingsProvider(token: string): Promise<SettingsProviderResponse> {
    return request<SettingsProviderResponse>('/settings/provider', { token })
  },
  updateSettingsProvider(
    token: string,
    payload: UpdateSettingsProviderPayload,
  ): Promise<SettingsProviderResponse> {
    return request<SettingsProviderResponse>('/settings/provider', {
      method: 'PUT',
      token,
      body: JSON.stringify(payload),
    })
  },
  getSettingsChannels(token: string): Promise<SettingsChannelsResponse> {
    return request<SettingsChannelsResponse>('/settings/channels', { token })
  },
  updateSettingsChannels(
    token: string,
    payload: UpdateSettingsChannelsPayload,
  ): Promise<SettingsChannelsResponse> {
    return request<SettingsChannelsResponse>('/settings/channels', {
      method: 'PUT',
      token,
      body: JSON.stringify(payload),
    })
  },
  getSettingsRegistration(token: string): Promise<SettingsRegistrationResponse> {
    return request<SettingsRegistrationResponse>('/settings/registration', { token })
  },
  updateSettingsRegistration(
    token: string,
    allowRegistration: boolean,
    requireInviteCode: boolean,
  ): Promise<SettingsRegistrationResponse> {
    return request<SettingsRegistrationResponse>('/settings/registration', {
      method: 'PUT',
      token,
      body: JSON.stringify({
        allow_registration: allowRegistration,
        require_invite_code: requireInviteCode,
      }),
    })
  },
  getSettingsAppearance(token: string): Promise<SettingsAppearanceResponse> {
    return request<SettingsAppearanceResponse>('/settings/appearance', { token })
  },
  updateSettingsAppearance(
    token: string,
    payload: UpdateSettingsAppearancePayload,
  ): Promise<SettingsAppearanceResponse> {
    return request<SettingsAppearanceResponse>('/settings/appearance', {
      method: 'PUT',
      token,
      body: JSON.stringify(payload),
    })
  },
  getSettingsSystem(token: string): Promise<SettingsSystemResponse> {
    return request<SettingsSystemResponse>('/settings/system', { token })
  },
  updateSettingsSystem(
    token: string,
    payload: UpdateSettingsSystemPayload,
  ): Promise<SettingsSystemResponse> {
    return request<SettingsSystemResponse>('/settings/system', {
      method: 'PUT',
      token,
      body: JSON.stringify(payload),
    })
  },
  getGroups(token: string): Promise<{ groups: GroupSummary[] }> {
    return request<{ groups: GroupSummary[] }>('/groups', { token })
  },
  getTerminalOverview(token: string): Promise<TerminalWorkspaceListResponse> {
    return request<TerminalWorkspaceListResponse>('/terminals', { token })
  },
  getTerminalHistoryTimeline(
    token: string,
    groupId: string,
    options: {
      limit?: number
      offset?: number
      status?: TerminalSessionStatus
      ownerUserId?: string
      sessionIdPrefix?: string
      snapshotFrom?: string
      snapshotTo?: string
    } = {},
  ): Promise<TerminalSessionHistoryTimelineResponse> {
    const params = new URLSearchParams()
    if (typeof options.limit === 'number') {
      params.set('limit', String(options.limit))
    }
    if (typeof options.offset === 'number') {
      params.set('offset', String(options.offset))
    }
    if (options.status) {
      params.set('status', options.status)
    }
    if (options.ownerUserId) {
      params.set('owner_user_id', options.ownerUserId)
    }
    if (options.sessionIdPrefix) {
      params.set('session_id_prefix', options.sessionIdPrefix)
    }
    if (options.snapshotFrom) {
      params.set('snapshot_from', options.snapshotFrom)
    }
    if (options.snapshotTo) {
      params.set('snapshot_to', options.snapshotTo)
    }
    const suffix = params.toString() ? `?${params.toString()}` : ''
    return request<TerminalSessionHistoryTimelineResponse>(
      `/terminals/${encodeURIComponent(groupId)}/sessions/history${suffix}`,
      { token },
    )
  },
  getTerminalHistorySearch(
    token: string,
    groupId: string,
    options: {
      query: string
      limit?: number
      offset?: number
      sort?: TerminalHistorySearchSort
      status?: TerminalSessionStatus
      ownerUserId?: string
      sessionIdPrefix?: string
      snapshotFrom?: string
      snapshotTo?: string
    },
  ): Promise<TerminalSessionHistorySearchResponse> {
    const query = options.query.trim()
    if (!query) {
      throw new Error('Search query is required')
    }
    const params = new URLSearchParams()
    params.set('q', query)
    if (typeof options.limit === 'number') {
      params.set('limit', String(options.limit))
    }
    if (typeof options.offset === 'number') {
      params.set('offset', String(options.offset))
    }
    if (options.sort) {
      params.set('sort', options.sort)
    }
    if (options.status) {
      params.set('status', options.status)
    }
    if (options.ownerUserId) {
      params.set('owner_user_id', options.ownerUserId)
    }
    if (options.sessionIdPrefix) {
      params.set('session_id_prefix', options.sessionIdPrefix)
    }
    if (options.snapshotFrom) {
      params.set('snapshot_from', options.snapshotFrom)
    }
    if (options.snapshotTo) {
      params.set('snapshot_to', options.snapshotTo)
    }
    return request<TerminalSessionHistorySearchResponse>(
      `/terminals/${encodeURIComponent(groupId)}/sessions/history/search?${params.toString()}`,
      { token },
    )
  },
  getTerminalHistoryDetail(
    token: string,
    groupId: string,
    sessionId: string,
  ): Promise<TerminalSessionHistoryDetailResponse> {
    return request<TerminalSessionHistoryDetailResponse>(
      `/terminals/${encodeURIComponent(groupId)}/sessions/history/${encodeURIComponent(sessionId)}`,
      { token },
    )
  },
  downloadTerminalHistoryDetail(token: string, groupId: string, sessionId: string): Promise<Blob> {
    return requestBlob(
      `/terminals/${encodeURIComponent(groupId)}/sessions/history/${encodeURIComponent(sessionId)}/download`,
      { token },
    )
  },
  getGroupMembers(token: string, groupId: string): Promise<GroupMemberListResponse> {
    return request<GroupMemberListResponse>(`/groups/${encodeURIComponent(groupId)}/members`, { token })
  },
  getGroupSlots(token: string, groupId: string): Promise<ConversationSlotListResponse> {
    return request<ConversationSlotListResponse>(`/groups/${encodeURIComponent(groupId)}/slots`, { token })
  },
  getGroupImBindings(token: string, groupId: string): Promise<GroupImBindingListResponse> {
    return request<GroupImBindingListResponse>(`/groups/${encodeURIComponent(groupId)}/bindings/im`, { token })
  },
  async getCurrentTerminalSession(
    token: string,
    groupId: string,
  ): Promise<TerminalSessionResponse | null> {
    try {
      return await request<TerminalSessionResponse>(
        `/terminals/${encodeURIComponent(groupId)}/sessions/current`,
        { token },
      )
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return null
      }
      throw error
    }
  },
  createTerminalSession(token: string, groupId: string): Promise<TerminalSessionResponse> {
    return request<TerminalSessionResponse>(`/terminals/${encodeURIComponent(groupId)}/sessions`, {
      method: 'POST',
      token,
      body: JSON.stringify({ requested_mode: 'container' }),
    })
  },
  closeCurrentTerminalSession(token: string, groupId: string): Promise<DeleteTerminalSessionResponse> {
    return request<DeleteTerminalSessionResponse>(
      `/terminals/${encodeURIComponent(groupId)}/sessions/current`,
      {
        method: 'DELETE',
        token,
      },
    )
  },
  forceCloseCurrentTerminalSession(token: string, groupId: string): Promise<DeleteTerminalSessionResponse> {
    return request<DeleteTerminalSessionResponse>(
      `/terminals/${encodeURIComponent(groupId)}/sessions/force`,
      {
        method: 'DELETE',
        token,
      },
    )
  },
  bindGroupImEndpoint(token: string, groupId: string, imJid: string): Promise<GroupImBindingSummary> {
    return request<GroupImBindingSummary>(
      `/groups/${encodeURIComponent(groupId)}/bindings/im/${encodeURIComponent(imJid)}`,
      {
        method: 'PUT',
        token,
      },
    )
  },
  unbindGroupImEndpoint(token: string, groupId: string, imJid: string): Promise<GroupImBindingSummary> {
    return request<GroupImBindingSummary>(
      `/groups/${encodeURIComponent(groupId)}/bindings/im/${encodeURIComponent(imJid)}`,
      {
        method: 'DELETE',
        token,
      },
    )
  },
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health')
  },
  getMonitor(token: string): Promise<MonitorResponse> {
    return request<MonitorResponse>('/monitor', { token })
  },
  getUsageStats(token: string, days = 7): Promise<UsageStatsResponse> {
    return request<UsageStatsResponse>(`/usage/stats?days=${encodeURIComponent(String(days))}`, {
      token,
    })
  },
  getAuditMessages(
    token: string,
    options: { limit?: number; groupId?: string | null } = {},
  ): Promise<AuditMessageListResponse> {
    const params = new URLSearchParams()
    if (typeof options.limit === 'number') {
      params.set('limit', String(options.limit))
    }
    if (options.groupId && options.groupId.trim()) {
      params.set('group_id', options.groupId.trim())
    }
    const suffix = params.toString() ? `?${params.toString()}` : ''
    return request<AuditMessageListResponse>(`/audit/messages${suffix}`, { token })
  },
  getGlobalMemory(token: string): Promise<MemoryGlobalResponse> {
    return request<MemoryGlobalResponse>('/memory/global', { token })
  },
  updateGlobalMemory(token: string, content: string): Promise<MemoryGlobalResponse> {
    return request<MemoryGlobalResponse>('/memory/global', {
      method: 'PUT',
      token,
      body: JSON.stringify({ content }),
    })
  },
  listWorkspaceMemoryFiles(token: string, groupId: string): Promise<WorkspaceMemoryFileListResponse> {
    return request<WorkspaceMemoryFileListResponse>(
      `/memory/workspaces/${encodeURIComponent(groupId)}/files`,
      { token },
    )
  },
  getWorkspaceMemoryFile(
    token: string,
    groupId: string,
    path: string,
  ): Promise<WorkspaceMemoryFileResponse> {
    return request<WorkspaceMemoryFileResponse>(
      `/memory/workspaces/${encodeURIComponent(groupId)}/file?path=${encodeURIComponent(path)}`,
      { token },
    )
  },
  updateWorkspaceMemoryFile(
    token: string,
    groupId: string,
    path: string,
    content: string,
  ): Promise<WorkspaceMemoryFileResponse> {
    return request<WorkspaceMemoryFileResponse>(
      `/memory/workspaces/${encodeURIComponent(groupId)}/file`,
      {
        method: 'PUT',
        token,
        body: JSON.stringify({ path, content }),
      },
    )
  },
  searchWorkspaceMemory(
    token: string,
    groupId: string,
    query: string,
  ): Promise<WorkspaceMemorySearchResponse> {
    return request<WorkspaceMemorySearchResponse>(
      `/memory/workspaces/${encodeURIComponent(groupId)}/search?q=${encodeURIComponent(query)}`,
      { token },
    )
  },
  listSkills(token: string): Promise<SkillListResponse> {
    return request<SkillListResponse>('/skills', { token })
  },
  getSkill(token: string, skillId: string): Promise<SkillDetailResponse> {
    return request<SkillDetailResponse>(`/skills/${encodeURIComponent(skillId)}`, { token })
  },
  updateSkill(token: string, skillId: string, content: string): Promise<SkillDetailResponse> {
    return request<SkillDetailResponse>(`/skills/${encodeURIComponent(skillId)}`, {
      method: 'PUT',
      token,
      body: JSON.stringify({ content }),
    })
  },
  updateSkillState(token: string, skillId: string, enabled: boolean): Promise<SkillDetailResponse> {
    return request<SkillDetailResponse>(`/skills/${encodeURIComponent(skillId)}/state`, {
      method: 'PATCH',
      token,
      body: JSON.stringify({ enabled }),
    })
  },
  deleteSkill(token: string, skillId: string): Promise<{ status: string }> {
    return request<{ status: string }>(`/skills/${encodeURIComponent(skillId)}`, {
      method: 'DELETE',
      token,
    })
  },
  listMcpServers(token: string): Promise<McpServerListResponse> {
    return request<McpServerListResponse>('/mcp-servers', { token })
  },
  getMcpServer(token: string, serverId: string): Promise<McpServerDetailResponse> {
    return request<McpServerDetailResponse>(`/mcp-servers/${encodeURIComponent(serverId)}`, { token })
  },
  updateMcpServer(
    token: string,
    serverId: string,
    payload: UpdateMcpServerPayload,
  ): Promise<McpServerDetailResponse> {
    return request<McpServerDetailResponse>(`/mcp-servers/${encodeURIComponent(serverId)}`, {
      method: 'PUT',
      token,
      body: JSON.stringify(payload),
    })
  },
  updateMcpServerState(
    token: string,
    serverId: string,
    enabled: boolean,
  ): Promise<McpServerDetailResponse> {
    return request<McpServerDetailResponse>(`/mcp-servers/${encodeURIComponent(serverId)}/state`, {
      method: 'PATCH',
      token,
      body: JSON.stringify({ enabled }),
    })
  },
  deleteMcpServer(token: string, serverId: string): Promise<{ status: string }> {
    return request<{ status: string }>(`/mcp-servers/${encodeURIComponent(serverId)}`, {
      method: 'DELETE',
      token,
    })
  },
  listWorkspaceFiles(token: string, groupId: string, currentPath = ''): Promise<WorkspaceFileListResponse> {
    const query = currentPath ? `?path=${encodeURIComponent(currentPath)}` : ''
    return request<WorkspaceFileListResponse>(`/groups/${encodeURIComponent(groupId)}/files${query}`, {
      token,
    })
  },
  uploadWorkspaceFiles(token: string, groupId: string, currentPath: string, files: File[]): Promise<{ files: string[] }> {
    const body = new FormData()
    body.set('path', currentPath)
    files.forEach((file) => body.append('files', file))
    return request<{ files: string[] }>(`/groups/${encodeURIComponent(groupId)}/files`, {
      method: 'POST',
      token,
      body,
    })
  },
  uploadChatAttachments(token: string, groupId: string, files: File[]): Promise<{ files: string[] }> {
    const body = new FormData()
    body.set('path', 'chat-attachments')
    files.forEach((file) => body.append('files', file))
    return request<{ files: string[] }>(`/groups/${encodeURIComponent(groupId)}/files`, {
      method: 'POST',
      token,
      body,
    })
  },
  getWorkspaceFileContent(
    token: string,
    groupId: string,
    filePath: string,
  ): Promise<WorkspaceFileContentResponse> {
    return request<WorkspaceFileContentResponse>(
      `/groups/${encodeURIComponent(groupId)}/files/content/${encodePathSegments(filePath)}`,
      { token },
    )
  },
  updateWorkspaceFileContent(
    token: string,
    groupId: string,
    filePath: string,
    content: string,
  ): Promise<WorkspaceFileContentResponse> {
    return request<WorkspaceFileContentResponse>(
      `/groups/${encodeURIComponent(groupId)}/files/content/${encodePathSegments(filePath)}`,
      {
        method: 'PUT',
        token,
        body: JSON.stringify({ content }),
      },
    )
  },
  deleteWorkspaceFile(token: string, groupId: string, filePath: string): Promise<{ status: string }> {
    return request<{ status: string }>(
      `/groups/${encodeURIComponent(groupId)}/files/${encodePathSegments(filePath)}`,
      {
        method: 'DELETE',
        token,
      },
    )
  },
  downloadWorkspaceFile(token: string, groupId: string, filePath: string): Promise<Blob> {
    return requestBlob(
      `/groups/${encodeURIComponent(groupId)}/files/download/${encodePathSegments(filePath)}`,
      { token },
    )
  },
  previewWorkspaceFile(token: string, groupId: string, filePath: string): Promise<Blob> {
    return requestBlob(
      `/groups/${encodeURIComponent(groupId)}/files/preview/${encodePathSegments(filePath)}`,
      { token },
    )
  },
}
