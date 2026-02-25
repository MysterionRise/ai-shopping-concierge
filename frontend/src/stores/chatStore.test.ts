import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from './chatStore'

describe('chatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isTyping: false,
      currentConversationId: undefined,
      streamingContent: '',
      streamingProducts: [],
      userId: 'default-user',
    })
  })

  it('has correct initial state', () => {
    const state = useChatStore.getState()
    expect(state.messages).toEqual([])
    expect(state.isTyping).toBe(false)
    expect(state.currentConversationId).toBeUndefined()
    expect(state.streamingContent).toBe('')
    expect(state.streamingProducts).toEqual([])
    expect(state.userId).toBe('default-user')
  })

  it('setUserId updates user id', () => {
    useChatStore.getState().setUserId('user-123')
    expect(useChatStore.getState().userId).toBe('user-123')
  })

  it('setUserId resets streaming state', () => {
    useChatStore.setState({
      isTyping: true,
      streamingContent: 'some content',
      streamingProducts: [
        {
          id: 'p1',
          name: 'Product',
          brand: null,
          ingredients: [],
          safetyScore: null,
          imageUrl: null,
        },
      ],
    })
    useChatStore.getState().setUserId('user-456')
    const state = useChatStore.getState()
    expect(state.isTyping).toBe(false)
    expect(state.streamingContent).toBe('')
    expect(state.streamingProducts).toEqual([])
  })

  it('addMessage appends a message', () => {
    const msg = {
      id: 'msg-1',
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date().toISOString(),
    }
    useChatStore.getState().addMessage(msg)
    expect(useChatStore.getState().messages).toHaveLength(1)
    expect(useChatStore.getState().messages[0].content).toBe('Hello')
  })

  it('addMessage appends multiple messages in order', () => {
    const msg1 = {
      id: 'msg-1',
      role: 'user' as const,
      content: 'First',
      timestamp: new Date().toISOString(),
    }
    const msg2 = {
      id: 'msg-2',
      role: 'assistant' as const,
      content: 'Second',
      timestamp: new Date().toISOString(),
    }
    useChatStore.getState().addMessage(msg1)
    useChatStore.getState().addMessage(msg2)
    expect(useChatStore.getState().messages).toHaveLength(2)
    expect(useChatStore.getState().messages[0].content).toBe('First')
    expect(useChatStore.getState().messages[1].content).toBe('Second')
  })

  it('clearMessages resets messages and conversation id', () => {
    useChatStore.setState({
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date().toISOString(),
        },
      ],
      currentConversationId: 'conv-1',
      streamingContent: 'partial',
      streamingProducts: [],
    })
    useChatStore.getState().clearMessages()
    const state = useChatStore.getState()
    expect(state.messages).toEqual([])
    expect(state.currentConversationId).toBeUndefined()
    expect(state.streamingContent).toBe('')
  })

  it('loadConversation sets conversation id and messages', () => {
    const messages = [
      {
        id: 'msg-1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-2',
        role: 'assistant' as const,
        content: 'Hi!',
        timestamp: new Date().toISOString(),
      },
    ]
    useChatStore.getState().loadConversation('conv-42', messages)
    const state = useChatStore.getState()
    expect(state.currentConversationId).toBe('conv-42')
    expect(state.messages).toHaveLength(2)
    expect(state.streamingContent).toBe('')
    expect(state.streamingProducts).toEqual([])
  })

  it('loadConversation with no messages defaults to empty array', () => {
    useChatStore.getState().loadConversation('conv-99')
    expect(useChatStore.getState().messages).toEqual([])
  })
})
