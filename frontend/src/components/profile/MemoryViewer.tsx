import { Brain, Trash2 } from 'lucide-react'
import { Memory } from '../../types'

const MOCK_MEMORIES: Memory[] = [
  {
    id: '1',
    content: 'User has oily skin with acne concerns',
    category: 'semantic',
    metadata: { source: 'conversation' },
    createdAt: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    content: 'Prefers lightweight, non-comedogenic products',
    category: 'preferences',
    metadata: { source: 'conversation' },
    createdAt: '2024-01-15T10:05:00Z',
  },
]

const CATEGORY_COLORS: Record<string, string> = {
  semantic: 'bg-blue-50 text-blue-700 border-blue-200',
  episodic: 'bg-purple-50 text-purple-700 border-purple-200',
  constraints: 'bg-red-50 text-red-700 border-red-200',
  preferences: 'bg-green-50 text-green-700 border-green-200',
}

export default function MemoryViewer() {
  const memories = MOCK_MEMORIES // Will be replaced with API call

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-purple-500" />
        <h2 className="text-lg font-medium text-gray-900">Memory</h2>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        What the concierge remembers about you across sessions.
      </p>

      <div className="space-y-2">
        {memories.map((memory) => (
          <div
            key={memory.id}
            className="flex items-start justify-between gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50"
          >
            <div className="flex-1">
              <p className="text-sm text-gray-800">{memory.content}</p>
              <span
                className={`inline-block mt-1 px-2 py-0.5 rounded text-xs border ${
                  CATEGORY_COLORS[memory.category] || 'bg-gray-50 text-gray-600'
                }`}
              >
                {memory.category}
              </span>
            </div>
            <button className="text-gray-400 hover:text-red-500 transition-colors">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        {memories.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-4">
            No memories stored yet. Start chatting!
          </p>
        )}
      </div>
    </section>
  )
}
