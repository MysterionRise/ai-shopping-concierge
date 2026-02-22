import { MessageSquare, Plus, Loader2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useChatStore } from '../../stores/chatStore'
import { useUserStore } from '../../stores/userStore'
import { getConversations, getConversationMessages } from '../../api/conversations'
import { useState } from 'react'

function formatTime(isoString: string): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' })
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

export default function Sidebar() {
  const clearMessages = useChatStore((s) => s.clearMessages)
  const loadConversation = useChatStore((s) => s.loadConversation)
  const currentConversationId = useChatStore((s) => s.currentConversationId)
  const user = useUserStore((s) => s.user)
  const [loadingId, setLoadingId] = useState<string | null>(null)

  const { data: conversations = [] } = useQuery({
    queryKey: ['conversations', user?.id],
    queryFn: () => getConversations(user!.id),
    enabled: !!user?.id,
    refetchInterval: 30000,
  })

  const handleSelect = async (conversationId: string) => {
    if (conversationId === currentConversationId || !user) return
    setLoadingId(conversationId)
    try {
      const messages = await getConversationMessages(conversationId, user.id)
      loadConversation(conversationId, messages)
    } catch {
      loadConversation(conversationId)
    } finally {
      setLoadingId(null)
    }
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 p-4 hidden lg:block overflow-y-auto">
      <button
        onClick={clearMessages}
        className="w-full flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors mb-4"
      >
        <Plus className="w-4 h-4" />
        New Chat
      </button>
      <div className="text-xs text-gray-400 uppercase font-medium mb-2">
        Recent
      </div>
      <div className="space-y-1">
        {conversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => handleSelect(conv.id)}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
              conv.id === currentConversationId
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            {loadingId === conv.id ? (
              <Loader2 className="w-4 h-4 flex-shrink-0 animate-spin" />
            ) : (
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <span className="block truncate">
                {conv.title || 'Conversation'}
              </span>
              <span className="block text-xs text-gray-400">
                {formatTime(conv.createdAt)}
              </span>
            </div>
          </button>
        ))}
        {conversations.length === 0 && (
          <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400">
            <MessageSquare className="w-4 h-4" />
            <span className="truncate">No conversations yet</span>
          </div>
        )}
      </div>
    </aside>
  )
}
