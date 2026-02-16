import { MessageSquare, Plus } from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'

export default function Sidebar() {
  const clearMessages = useChatStore((s) => s.clearMessages)

  return (
    <aside className="w-64 bg-white border-r border-gray-200 p-4 hidden lg:block">
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
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-500">
          <MessageSquare className="w-4 h-4" />
          <span className="truncate">Conversations will appear here</span>
        </div>
      </div>
    </aside>
  )
}
