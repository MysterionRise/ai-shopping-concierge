import { apiFetch, apiStreamUrl } from './client'

export interface PersonaScoreEntry {
  conversation_id: string
  message_id: string
  scores: Record<string, number>
  timestamp: string
}

export interface PersonaAlert {
  trait: string
  score: number
  threshold: number
  message_id: string
  timestamp: string
}

export async function getPersonaScores(
  conversationId: string,
  messageId: string,
): Promise<PersonaScoreEntry> {
  return apiFetch<PersonaScoreEntry>(
    `/persona/scores?conversation_id=${conversationId}&message_id=${messageId}`,
  )
}

export async function getPersonaHistory(
  conversationId: string,
): Promise<PersonaScoreEntry[]> {
  return apiFetch<PersonaScoreEntry[]>(
    `/persona/history?conversation_id=${conversationId}`,
  )
}

export async function getPersonaAlerts(
  conversationId: string,
): Promise<PersonaAlert[]> {
  return apiFetch<PersonaAlert[]>(
    `/persona/alerts?conversation_id=${conversationId}`,
  )
}

export function personaStreamUrl(conversationId: string): string {
  return apiStreamUrl(`/persona/stream?conversation_id=${conversationId}`)
}
