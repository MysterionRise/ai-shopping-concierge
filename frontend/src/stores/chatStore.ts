import { create } from 'zustand'
import { ChatMessage, ProductCard } from '../types'
import { sendMessage, createSSEConnection, parseBackendProduct, StreamDoneData } from '../api/chat'

// Track the active SSE controller outside Zustand state (not serializable)
let activeStreamController: AbortController | null = null

interface ChatState {
  messages: ChatMessage[]
  isTyping: boolean
  currentConversationId: string | undefined
  streamingContent: string
  streamingProducts: ProductCard[]
  userId: string

  setUserId: (id: string) => void
  addMessage: (message: ChatMessage) => void
  sendChatMessage: (text: string) => Promise<void>
  sendStreamingMessage: (text: string) => void
  loadConversation: (conversationId: string, messages?: ChatMessage[]) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isTyping: false,
  currentConversationId: undefined,
  streamingContent: '',
  streamingProducts: [],
  userId: 'default-user',

  setUserId: (id) => {
    // Abort any in-flight streaming request when switching users
    if (activeStreamController) {
      activeStreamController.abort()
      activeStreamController = null
    }
    set({ userId: id, isTyping: false, streamingContent: '', streamingProducts: [] })
  },

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  sendChatMessage: async (text) => {
    const { userId, currentConversationId } = get()

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isTyping: true,
    }))

    try {
      const response = await sendMessage(text, userId, currentConversationId)

      // Discard response if user switched during the request
      if (get().userId !== userId) return

      const products = (response.products || []).map(parseBackendProduct)
      const violations = response.safety_violations || []
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        intent: response.intent,
        products: products.length > 0 ? products : undefined,
        safetyViolations: violations.length > 0 ? violations : undefined,
        timestamp: new Date().toISOString(),
      }

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isTyping: false,
        currentConversationId: response.conversation_id,
      }))
    } catch (err) {
      // Discard error if user switched during the request
      if (get().userId !== userId) return

      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Sorry, something went wrong: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      }
      set((state) => ({
        messages: [...state.messages, errorMessage],
        isTyping: false,
      }))
    }
  },

  sendStreamingMessage: (text) => {
    const { userId, currentConversationId } = get()

    // Abort any in-flight streaming request
    if (activeStreamController) {
      activeStreamController.abort()
      activeStreamController = null
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }

    set((state) => ({
      messages: [...state.messages, userMessage],
      isTyping: true,
      streamingContent: '',
      streamingProducts: [],
    }))

    activeStreamController = createSSEConnection(
      text,
      userId,
      currentConversationId,
      (token) => {
        // Discard tokens if user switched during streaming
        if (get().userId !== userId) return
        set((state) => ({
          streamingContent: state.streamingContent + token,
        }))
      },
      (doneData: StreamDoneData) => {
        activeStreamController = null
        // Discard response if user switched during streaming
        if (get().userId !== userId) {
          set({ isTyping: false, streamingContent: '', streamingProducts: [] })
          return
        }
        const content = get().streamingContent
        const products = get().streamingProducts
        const violations = doneData.safetyViolations || []
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content,
          intent: doneData.intent,
          products: products.length > 0 ? products : undefined,
          safetyViolations: violations.length > 0 ? violations : undefined,
          timestamp: new Date().toISOString(),
        }
        set((state) => ({
          messages: [...state.messages, assistantMessage],
          isTyping: false,
          streamingContent: '',
          streamingProducts: [],
          currentConversationId: doneData.conversationId || state.currentConversationId,
        }))
      },
      (error) => {
        activeStreamController = null
        // Discard error if user switched during streaming
        if (get().userId !== userId) {
          set({ isTyping: false, streamingContent: '', streamingProducts: [] })
          return
        }
        const errorMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Sorry, something went wrong: ${error}`,
          timestamp: new Date().toISOString(),
        }
        set((state) => ({
          messages: [...state.messages, errorMessage],
          isTyping: false,
          streamingContent: '',
          streamingProducts: [],
        }))
      },
      (products) => {
        // Discard products if user switched during streaming
        if (get().userId !== userId) return
        set({ streamingProducts: products })
      },
    )
  },

  loadConversation: (conversationId, messages) => {
    set({
      currentConversationId: conversationId,
      messages: messages || [],
      streamingContent: '',
      streamingProducts: [],
    })
  },

  clearMessages: () =>
    set({
      messages: [],
      currentConversationId: undefined,
      streamingContent: '',
      streamingProducts: [],
    }),
}))
