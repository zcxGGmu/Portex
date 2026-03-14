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
