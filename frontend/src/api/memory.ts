import { Memory } from '../types'
import { apiFetch } from './client'

interface BackendMemory {
  id: string
  content: string
  category: string
  metadata: Record<string, unknown>
  created_at: string
}

function toMemory(m: BackendMemory): Memory {
  return {
    id: m.id,
    content: m.content,
    category: m.category,
    metadata: m.metadata,
    createdAt: m.created_at,
  }
}

export async function getUserMemories(userId: string): Promise<Memory[]> {
  const data = await apiFetch<BackendMemory[]>(`/users/${userId}/memory`)
  return data.map(toMemory)
}

export async function deleteMemory(
  userId: string,
  memoryId: string,
): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/users/${userId}/memory/${memoryId}`, {
    method: 'DELETE',
  })
}
