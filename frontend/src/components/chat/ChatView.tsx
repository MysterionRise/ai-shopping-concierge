import { useChat } from '../../hooks/useChat'
import ChatInput from './ChatInput'
import MessageList from './MessageList'

export default function ChatView() {
  const { messages, isTyping, streamingContent, sendMessage } = useChat()

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <MessageList
        messages={messages}
        isTyping={isTyping}
        streamingContent={streamingContent}
      />
      <ChatInput onSend={(text) => sendMessage(text)} disabled={isTyping} />
    </div>
  )
}
