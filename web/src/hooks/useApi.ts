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
