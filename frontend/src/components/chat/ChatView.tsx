import { useState } from 'react'
import { Activity } from 'lucide-react'
import { useChat } from '../../hooks/useChat'
import ChatInput from './ChatInput'
import MessageList from './MessageList'
import PersonaSidebar from './PersonaSidebar'

export default function ChatView() {
  const { messages, isTyping, streamingContent, streamingProducts, sendMessage } = useChat()
  const [showPersona, setShowPersona] = useState(false)

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <div className="flex items-center justify-end px-4 py-1 border-b border-gray-100 bg-white">
        <button
          onClick={() => setShowPersona(!showPersona)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            showPersona
              ? 'bg-primary-50 text-primary-700 border border-primary-200'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          }`}
          title="Toggle persona monitor"
        >
          <Activity className="w-3.5 h-3.5" />
          Persona
        </button>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex flex-col">
          <MessageList
            messages={messages}
            isTyping={isTyping}
            streamingContent={streamingContent}
            streamingProducts={streamingProducts}
          />
          <ChatInput onSend={(text) => sendMessage(text, true)} disabled={isTyping} />
        </div>
        {showPersona && <PersonaSidebar />}
      </div>
    </div>
  )
}
