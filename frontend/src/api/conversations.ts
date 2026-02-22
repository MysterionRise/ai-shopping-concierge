import { Conversation, ChatMessage } from '../types'
import { apiFetch } from './client'

interface BackendConversation {
  id: string
  user_id: string
  langgraph_thread_id: string
  title: string | null
  created_at: string
}

interface BackendMessage {
  id: string
  role: string
  content: string
  agent_name: string | null
  created_at: string
}

export async function getConversations(userId: string): Promise<Conversation[]> {
  const data = await apiFetch<BackendConversation[]>(
    `/conversations?user_id=${userId}`,
  )
  return data.map((c) => ({
    id: c.id,
    userId: c.user_id,
    title: c.title,
    createdAt: c.created_at,
  }))
}

export async function getConversationMessages(
  conversationId: string,
  userId: string,
): Promise<ChatMessage[]> {
  const data = await apiFetch<BackendMessage[]>(
    `/conversations/${conversationId}/messages?user_id=${userId}`,
  )
  return data.map((m) => ({
    id: m.id,
    role: m.role as 'user' | 'assistant',
    content: m.content,
    agentName: m.agent_name ?? undefined,
    timestamp: m.created_at,
  }))
}
