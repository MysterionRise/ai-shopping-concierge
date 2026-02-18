import { useChat } from '../../hooks/useChat'
import ChatInput from './ChatInput'
import MessageList from './MessageList'

export default function ChatView() {
  const { messages, isTyping, streamingContent, streamingProducts, sendMessage } = useChat()

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <MessageList
        messages={messages}
        isTyping={isTyping}
        streamingContent={streamingContent}
        streamingProducts={streamingProducts}
      />
      <ChatInput onSend={(text) => sendMessage(text, true)} disabled={isTyping} />
    </div>
  )
}
