import { useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'

export function useChat() {
  const {
    messages,
    isTyping,
    streamingContent,
    streamingProducts,
    sendChatMessage,
    sendStreamingMessage,
    clearMessages,
  } = useChatStore()

  const sendMessage = useCallback(
    (text: string, streaming = false) => {
      if (streaming) {
        sendStreamingMessage(text)
      } else {
        sendChatMessage(text)
      }
    },
    [sendChatMessage, sendStreamingMessage],
  )

  return {
    messages,
    isTyping,
    streamingContent,
    streamingProducts,
    sendMessage,
    clearMessages,
  }
}
