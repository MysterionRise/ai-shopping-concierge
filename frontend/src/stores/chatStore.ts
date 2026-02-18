import { create } from 'zustand'
import { ChatMessage, ProductCard } from '../types'
import { sendMessage, createSSEConnection, parseBackendProduct } from '../api/chat'

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
  loadConversation: (conversationId: string) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isTyping: false,
  currentConversationId: undefined,
  streamingContent: '',
  streamingProducts: [],
  userId: 'default-user',

  setUserId: (id) => set({ userId: id }),

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

      const products = (response.products || []).map(parseBackendProduct)
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        products: products.length > 0 ? products : undefined,
        timestamp: new Date().toISOString(),
      }

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isTyping: false,
        currentConversationId: response.conversation_id,
      }))
    } catch (err) {
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

    createSSEConnection(
      text,
      userId,
      currentConversationId,
      (token) => {
        set((state) => ({
          streamingContent: state.streamingContent + token,
        }))
      },
      (conversationId) => {
        const content = get().streamingContent
        const products = get().streamingProducts
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content,
          products: products.length > 0 ? products : undefined,
          timestamp: new Date().toISOString(),
        }
        set((state) => ({
          messages: [...state.messages, assistantMessage],
          isTyping: false,
          streamingContent: '',
          streamingProducts: [],
          currentConversationId: conversationId || state.currentConversationId,
        }))
      },
      (error) => {
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
        set({ streamingProducts: products })
      },
    )
  },

  loadConversation: (conversationId) => {
    set({ currentConversationId: conversationId, messages: [] })
  },

  clearMessages: () =>
    set({
      messages: [],
      currentConversationId: undefined,
      streamingContent: '',
      streamingProducts: [],
    }),
}))
