import { User } from '../types'
import { apiFetch } from './client'

export async function getUser(userId: string): Promise<User> {
  const data = await apiFetch<Record<string, unknown>>(`/users/${userId}`)
  return {
    id: data.id as string,
    displayName: data.display_name as string,
    skinType: data.skin_type as string | null,
    skinConcerns: data.skin_concerns as string[],
    allergies: data.allergies as string[],
    preferences: data.preferences as Record<string, unknown>,
    memoryEnabled: (data.memory_enabled as boolean) ?? true,
  }
}

export async function createUser(data: {
  displayName: string
  skinType?: string
  allergies?: string[]
}): Promise<User> {
  const result = await apiFetch<Record<string, unknown>>('/users', {
    method: 'POST',
    body: JSON.stringify({
      display_name: data.displayName,
      skin_type: data.skinType,
      allergies: data.allergies || [],
    }),
  })
  return {
    id: result.id as string,
    displayName: result.display_name as string,
    skinType: result.skin_type as string | null,
    skinConcerns: result.skin_concerns as string[],
    allergies: result.allergies as string[],
    preferences: result.preferences as Record<string, unknown>,
    memoryEnabled: (result.memory_enabled as boolean) ?? true,
  }
}

export async function updateUser(
  userId: string,
  data: Partial<{
    displayName: string
    skinType: string
    skinConcerns: string[]
    allergies: string[]
    preferences: Record<string, unknown>
    memoryEnabled: boolean
  }>,
): Promise<User> {
  const result = await apiFetch<Record<string, unknown>>(`/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      display_name: data.displayName,
      skin_type: data.skinType,
      skin_concerns: data.skinConcerns,
      allergies: data.allergies,
      preferences: data.preferences,
      memory_enabled: data.memoryEnabled,
    }),
  })
  return {
    id: result.id as string,
    displayName: result.display_name as string,
    skinType: result.skin_type as string | null,
    skinConcerns: result.skin_concerns as string[],
    allergies: result.allergies as string[],
    preferences: result.preferences as Record<string, unknown>,
    memoryEnabled: (result.memory_enabled as boolean) ?? true,
  }
}
