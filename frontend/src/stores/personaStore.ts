import { create } from 'zustand'
import {
  PersonaScoreEntry,
  PersonaAlert,
  getPersonaHistory,
  getPersonaAlerts,
} from '../api/persona'

interface PersonaState {
  currentScores: Record<string, number>
  scoreHistory: PersonaScoreEntry[]
  alerts: PersonaAlert[]
  disclaimers: Record<string, string> // message_id -> disclaimer text
  isLoading: boolean

  updateScores: (entry: PersonaScoreEntry) => void
  setHistory: (history: PersonaScoreEntry[]) => void
  setAlerts: (alerts: PersonaAlert[]) => void
  addDisclaimer: (messageId: string, text: string) => void
  fetchHistory: (conversationId: string) => Promise<void>
  fetchAlerts: (conversationId: string) => Promise<void>
  clear: () => void
}

export const usePersonaStore = create<PersonaState>((set) => ({
  currentScores: {},
  scoreHistory: [],
  alerts: [],
  disclaimers: {},
  isLoading: false,

  updateScores: (entry) =>
    set((state) => ({
      currentScores: entry.scores,
      scoreHistory: [...state.scoreHistory, entry],
    })),

  setHistory: (history) => {
    const latest = history.length > 0 ? history[history.length - 1].scores : {}
    set({ scoreHistory: history, currentScores: latest })
  },

  setAlerts: (alerts) => set({ alerts }),

  addDisclaimer: (messageId, text) =>
    set((state) => ({
      disclaimers: { ...state.disclaimers, [messageId]: text },
    })),

  fetchHistory: async (conversationId) => {
    set({ isLoading: true })
    try {
      const history = await getPersonaHistory(conversationId)
      const latest =
        history.length > 0 ? history[history.length - 1].scores : {}
      set({ scoreHistory: history, currentScores: latest, isLoading: false })
    } catch {
      set({ isLoading: false })
    }
  },

  fetchAlerts: async (conversationId) => {
    try {
      const alerts = await getPersonaAlerts(conversationId)
      set({ alerts })
    } catch {
      // Silently ignore alert fetch failures
    }
  },

  clear: () =>
    set({
      currentScores: {},
      scoreHistory: [],
      alerts: [],
      disclaimers: {},
    }),
}))
