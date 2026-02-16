import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUser, updateUser, createUser } from '../api/users'
import { useUserStore } from '../stores/userStore'

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
    },
  })
}

export function useCreateUser() {
  return useMutation({
    mutationFn: createUser,
  })
}
