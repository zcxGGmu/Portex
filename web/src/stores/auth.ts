import { create } from 'zustand'

import { apiClient, type CurrentUser } from '../api/client'

interface AuthState {
  token: string | null
  currentUser: CurrentUser | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  currentUser: null,
  async login(username, password) {
    const tokenResponse = await apiClient.login(username, password)
    const currentUser = await apiClient.getCurrentUser(tokenResponse.access_token)

    set({
      token: tokenResponse.access_token,
      currentUser,
    })
  },
  logout() {
    set({ token: null, currentUser: null })
  },
}))
