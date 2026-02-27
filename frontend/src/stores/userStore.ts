import { create } from 'zustand'
import { setActiveUserId } from '../api/client'
import { User } from '../types'

interface UserState {
  user: User | null
  availableUsers: User[]
  isLoadingUsers: boolean
  setUser: (user: User) => void
  clearUser: () => void
  setAvailableUsers: (users: User[]) => void
  setIsLoadingUsers: (loading: boolean) => void
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  availableUsers: [],
  isLoadingUsers: false,
  setUser: (user) => {
    setActiveUserId(user.id)
    set({ user })
  },
  clearUser: () => {
    setActiveUserId(null)
    set({ user: null })
  },
  setAvailableUsers: (users) => set({ availableUsers: users }),
  setIsLoadingUsers: (loading) => set({ isLoadingUsers: loading }),
}))
