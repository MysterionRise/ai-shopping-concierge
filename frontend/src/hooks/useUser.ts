import { useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUser, updateUser, createUser, listUsers } from '../api/users'
import { User } from '../types'
import { useUserStore } from '../stores/userStore'
import { useChatStore } from '../stores/chatStore'

export function useUser(userId: string) {
  const setUser = useUserStore((state) => state.setUser)

  return useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const user = await getUser(userId)
      setUser(user)
      return user
    },
    enabled: !!userId,
    retry: false,
  })
}

export function useAvailableUsers() {
  const setAvailableUsers = useUserStore((s) => s.setAvailableUsers)
  const setIsLoadingUsers = useUserStore((s) => s.setIsLoadingUsers)

  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      setIsLoadingUsers(true)
      try {
        const users = await listUsers()
        setAvailableUsers(users)
        return users
      } finally {
        setIsLoadingUsers(false)
      }
    },
  })
}

export function useSwitchUser() {
  const setUser = useUserStore((s) => s.setUser)
  const setUserId = useChatStore((s) => s.setUserId)
  const clearMessages = useChatStore((s) => s.clearMessages)

  return useCallback((user: User) => {
    setUserId(user.id)
    setUser(user)
    clearMessages()
  }, [setUserId, setUser, clearMessages])
}

export function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string
      data: Parameters<typeof updateUser>[1]
    }) => updateUser(userId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['user', variables.userId] })
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
