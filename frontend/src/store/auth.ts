import { create } from 'zustand'
import type { User } from '../api/client'

interface AuthState {
  accessToken: string | null
  user: User | null
  bootstrapped: boolean
  setSession: (accessToken: string, user: User) => void
  setAccessToken: (accessToken: string) => void
  setUser: (user: User | null) => void
  setBootstrapped: (value: boolean) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  bootstrapped: false,
  setSession: (accessToken, user) => set({ accessToken, user }),
  setAccessToken: (accessToken) => set({ accessToken }),
  setUser: (user) => set({ user }),
  setBootstrapped: (bootstrapped) => set({ bootstrapped }),
  clearAuth: () => set({ accessToken: null, user: null }),
}))

interface UiState {
  darkMode: boolean
  toggleDarkMode: () => void
}

export const useUiStore = create<UiState>((set) => ({
  darkMode: false,
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
}))
