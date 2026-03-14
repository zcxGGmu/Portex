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
