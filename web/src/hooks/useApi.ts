import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import { useAuthStore } from '../stores/auth'

export function useHealthQuery() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    staleTime: 60_000,
  })
}

export function useCurrentUserQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['current-user', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getCurrentUser(token)
    },
    staleTime: 60_000,
  })
}

export function useGroupsQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['groups', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getGroups(token)
    },
    staleTime: 60_000,
  })
}

export function useGroupMembersQuery(groupId: string | null) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['group-members', token, groupId],
    enabled: Boolean(token && groupId),
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }
      return apiClient.getGroupMembers(token, groupId)
    },
    staleTime: 5_000,
  })
}

export function useGroupSlotsQuery(groupId: string | null) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['group-slots', token, groupId],
    enabled: Boolean(token && groupId),
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }
      return apiClient.getGroupSlots(token, groupId)
    },
    staleTime: 5_000,
  })
}

export function useGroupImBindingsQuery(groupId: string | null, enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['group-im-bindings', token, groupId],
    enabled: Boolean(token && groupId && enabled),
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }
      return apiClient.getGroupImBindings(token, groupId)
    },
    staleTime: 5_000,
  })
}

export function useCurrentTerminalSessionQuery(groupId: string | null, enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['terminal-session-current', token, groupId],
    enabled: Boolean(token && groupId && enabled),
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }

      return apiClient.getCurrentTerminalSession(token, groupId)
    },
    staleTime: 1_000,
    refetchInterval: 5_000,
  })
}

export function useSettingsProviderQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['settings-provider', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getSettingsProvider(token)
    },
    staleTime: 5_000,
  })
}

export function useSettingsChannelsQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['settings-channels', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getSettingsChannels(token)
    },
    staleTime: 5_000,
  })
}

export function useSettingsRegistrationQuery(enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['settings-registration', token],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getSettingsRegistration(token)
    },
    staleTime: 5_000,
  })
}

export function useSettingsAppearanceQuery(enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['settings-appearance', token],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getSettingsAppearance(token)
    },
    staleTime: 5_000,
  })
}

export function useSettingsSystemQuery(enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['settings-system', token],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getSettingsSystem(token)
    },
    staleTime: 5_000,
  })
}

export function useMonitorQuery(enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['monitor', token],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getMonitor(token)
    },
    staleTime: 5_000,
    refetchInterval: 5_000,
  })
}

export function useTerminalOverviewQuery(enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['terminal-overview', token],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getTerminalOverview(token)
    },
    staleTime: 5_000,
    refetchInterval: 5_000,
  })
}

export function useTerminalHistoryTimelineQuery(
  groupId: string | null,
  options: {
    limit: number
    offset: number
    status?: 'created' | 'attached' | 'detached' | 'closed' | 'exited'
    ownerUserId?: string
    sessionIdPrefix?: string
  },
  enabled = true,
) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: [
      'terminal-history-timeline',
      token,
      groupId,
      options.limit,
      options.offset,
      options.status ?? null,
      options.ownerUserId ?? null,
      options.sessionIdPrefix ?? null,
    ],
    enabled: Boolean(token && groupId) && enabled,
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }

      return apiClient.getTerminalHistoryTimeline(token, groupId, options)
    },
    staleTime: 5_000,
  })
}

export function useTerminalHistoryDetailQuery(
  groupId: string | null,
  sessionId: string | null,
  enabled = true,
) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['terminal-history-detail', token, groupId, sessionId],
    enabled: Boolean(token && groupId && sessionId) && enabled,
    queryFn: async () => {
      if (!token || !groupId || !sessionId) {
        throw new Error('Missing token, group id, or session id')
      }

      return apiClient.getTerminalHistoryDetail(token, groupId, sessionId)
    },
    staleTime: 5_000,
  })
}

export function useUsageStatsQuery(days: number, enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['usage-stats', token, days],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getUsageStats(token, days)
    },
    staleTime: 5_000,
  })
}

export function useAuditMessagesQuery(
  options: { limit: number; groupId: string | null },
  enabled = true,
) {
  const token = useAuthStore((state) => state.token)
  const normalizedGroupId = options.groupId?.trim() ?? ''

  return useQuery({
    queryKey: ['audit-messages', token, options.limit, normalizedGroupId],
    enabled: Boolean(token) && enabled,
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getAuditMessages(token, {
        limit: options.limit,
        groupId: normalizedGroupId || null,
      })
    },
    staleTime: 5_000,
  })
}

export function useGlobalMemoryQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['memory-global', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.getGlobalMemory(token)
    },
    staleTime: 5_000,
  })
}

export function useWorkspaceMemoryFilesQuery(groupId: string | null) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['workspace-memory-files', token, groupId],
    enabled: Boolean(token && groupId),
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }

      return apiClient.listWorkspaceMemoryFiles(token, groupId)
    },
    staleTime: 5_000,
  })
}

export function useWorkspaceMemoryFileQuery(
  groupId: string | null,
  filePath: string | null,
  enabled = true,
) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['workspace-memory-file', token, groupId, filePath],
    enabled: Boolean(token && groupId && filePath && enabled),
    queryFn: async () => {
      if (!token || !groupId || !filePath) {
        throw new Error('Missing token, group id, or file path')
      }

      return apiClient.getWorkspaceMemoryFile(token, groupId, filePath)
    },
    staleTime: 5_000,
  })
}

export function useWorkspaceMemorySearchQuery(
  groupId: string | null,
  query: string,
  enabled = true,
) {
  const token = useAuthStore((state) => state.token)
  const normalizedQuery = query.trim()

  return useQuery({
    queryKey: ['workspace-memory-search', token, groupId, normalizedQuery],
    enabled: Boolean(token && groupId && normalizedQuery && enabled),
    queryFn: async () => {
      if (!token || !groupId || !normalizedQuery) {
        throw new Error('Missing token, group id, or query')
      }

      return apiClient.searchWorkspaceMemory(token, groupId, normalizedQuery)
    },
    staleTime: 2_000,
  })
}

export function useSkillsQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['skills', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.listSkills(token)
    },
    staleTime: 5_000,
  })
}

export function useSkillDetailQuery(skillId: string | null, enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['skill-detail', token, skillId],
    enabled: Boolean(token && skillId && enabled),
    queryFn: async () => {
      if (!token || !skillId) {
        throw new Error('Missing token or skill id')
      }

      return apiClient.getSkill(token, skillId)
    },
    staleTime: 5_000,
  })
}

export function useMcpServersQuery() {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['mcp-servers', token],
    enabled: Boolean(token),
    queryFn: async () => {
      if (!token) {
        throw new Error('Missing token')
      }

      return apiClient.listMcpServers(token)
    },
    staleTime: 5_000,
  })
}

export function useMcpServerDetailQuery(serverId: string | null, enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['mcp-server-detail', token, serverId],
    enabled: Boolean(token && serverId && enabled),
    queryFn: async () => {
      if (!token || !serverId) {
        throw new Error('Missing token or server id')
      }

      return apiClient.getMcpServer(token, serverId)
    },
    staleTime: 5_000,
  })
}

export function useWorkspaceFilesQuery(groupId: string | null, currentPath: string) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['workspace-files', token, groupId, currentPath],
    enabled: Boolean(token && groupId),
    queryFn: async () => {
      if (!token || !groupId) {
        throw new Error('Missing token or group id')
      }

      return apiClient.listWorkspaceFiles(token, groupId, currentPath)
    },
    staleTime: 5_000,
  })
}

export function useWorkspaceFileContentQuery(groupId: string | null, filePath: string | null, enabled = true) {
  const token = useAuthStore((state) => state.token)

  return useQuery({
    queryKey: ['workspace-file-content', token, groupId, filePath],
    enabled: Boolean(token && groupId && filePath && enabled),
    queryFn: async () => {
      if (!token || !groupId || !filePath) {
        throw new Error('Missing token, group id, or file path')
      }

      return apiClient.getWorkspaceFileContent(token, groupId, filePath)
    },
    staleTime: 5_000,
  })
}
