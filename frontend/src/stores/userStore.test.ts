import { describe, it, expect, beforeEach } from 'vitest'
import { useUserStore } from './userStore'

describe('userStore', () => {
  beforeEach(() => {
    useUserStore.setState({
      user: null,
      availableUsers: [],
      isLoadingUsers: false,
    })
  })

  it('has correct initial state', () => {
    const state = useUserStore.getState()
    expect(state.user).toBeNull()
    expect(state.availableUsers).toEqual([])
    expect(state.isLoadingUsers).toBe(false)
  })

  it('setUser sets the current user', () => {
    const user = {
      id: 'user-1',
      displayName: 'Jane',
      skinType: 'oily' as const,
      skinConcerns: ['acne'],
      allergies: ['paraben'],
      preferences: {},
      memoryEnabled: true,
    }
    useUserStore.getState().setUser(user)
    expect(useUserStore.getState().user).toEqual(user)
  })

  it('clearUser sets user to null', () => {
    useUserStore.setState({
      user: {
        id: 'user-1',
        displayName: 'Jane',
        skinType: 'oily',
        skinConcerns: [],
        allergies: [],
        preferences: {},
        memoryEnabled: true,
      },
    })
    useUserStore.getState().clearUser()
    expect(useUserStore.getState().user).toBeNull()
  })

  it('setAvailableUsers updates the available users list', () => {
    const users = [
      {
        id: 'user-1',
        displayName: 'Jane',
        skinType: 'oily' as const,
        skinConcerns: [],
        allergies: [],
        preferences: {},
        memoryEnabled: true,
      },
      {
        id: 'user-2',
        displayName: 'John',
        skinType: 'dry' as const,
        skinConcerns: [],
        allergies: [],
        preferences: {},
        memoryEnabled: true,
      },
    ]
    useUserStore.getState().setAvailableUsers(users)
    expect(useUserStore.getState().availableUsers).toHaveLength(2)
    expect(useUserStore.getState().availableUsers[0].displayName).toBe('Jane')
    expect(useUserStore.getState().availableUsers[1].displayName).toBe('John')
  })

  it('setIsLoadingUsers updates loading state', () => {
    useUserStore.getState().setIsLoadingUsers(true)
    expect(useUserStore.getState().isLoadingUsers).toBe(true)
    useUserStore.getState().setIsLoadingUsers(false)
    expect(useUserStore.getState().isLoadingUsers).toBe(false)
  })

  it('setUser replaces existing user', () => {
    useUserStore.getState().setUser({
      id: 'user-1',
      displayName: 'Jane',
      skinType: 'oily',
      skinConcerns: [],
      allergies: [],
      preferences: {},
      memoryEnabled: true,
    })
    useUserStore.getState().setUser({
      id: 'user-2',
      displayName: 'John',
      skinType: 'dry',
      skinConcerns: [],
      allergies: [],
      preferences: {},
      memoryEnabled: false,
    })
    expect(useUserStore.getState().user?.id).toBe('user-2')
    expect(useUserStore.getState().user?.displayName).toBe('John')
  })
})
