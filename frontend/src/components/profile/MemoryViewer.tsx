import { Brain, Trash2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useUserStore } from '../../stores/userStore'
import { getUserMemories, deleteMemory } from '../../api/memory'
import { SkeletonRows } from '../Skeleton'

const CATEGORY_COLORS: Record<string, string> = {
  semantic: 'bg-blue-50 text-blue-700 border-blue-200',
  episodic: 'bg-purple-50 text-purple-700 border-purple-200',
  constraints: 'bg-red-50 text-red-700 border-red-200',
  preferences: 'bg-green-50 text-green-700 border-green-200',
  user_fact: 'bg-blue-50 text-blue-700 border-blue-200',
}

export default function MemoryViewer() {
  const user = useUserStore((s) => s.user)
  const queryClient = useQueryClient()

  const {
    data: memories = [],
    isLoading,
    isFetching,
    isError,
  } = useQuery({
    queryKey: ['memories', user?.id],
    queryFn: () => getUserMemories(user!.id),
    enabled: !!user?.id,
    staleTime: 0,
    placeholderData: undefined,
  })

  const deleteMutation = useMutation({
    mutationFn: (memoryId: string) => deleteMemory(user!.id, memoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories', user?.id] })
    },
  })

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-purple-500" />
        <h2 className="text-lg font-medium text-gray-900">Memory</h2>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        What the concierge remembers about you across sessions.
      </p>

      {(isLoading || isFetching) && <SkeletonRows count={3} />}

      {isError && !isFetching && (
        <p className="text-sm text-red-500 text-center py-4">
          Failed to load memories. Please try again later.
        </p>
      )}

      {!isLoading && !isFetching && !isError && (
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
              <button
                onClick={() => deleteMutation.mutate(memory.id)}
                disabled={deleteMutation.isPending}
                className="text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                title="Delete memory"
              >
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
      )}
    </section>
  )
}
