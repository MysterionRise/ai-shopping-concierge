import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import MemoryViewer from './MemoryViewer'
import { useUserStore } from '../../stores/userStore'

vi.mock('../../api/memory', () => ({
  getUserMemories: vi.fn().mockResolvedValue([]),
  deleteMemory: vi.fn().mockResolvedValue({ status: 'ok' }),
}))

function renderMemoryViewer() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryViewer />
    </QueryClientProvider>,
  )
}

describe('MemoryViewer', () => {
  beforeEach(() => {
    useUserStore.setState({
      user: {
        id: 'user-1',
        displayName: 'Test User',
        skinType: 'oily',
        skinConcerns: [],
        allergies: [],
        preferences: {},
        memoryEnabled: true,
      },
    })
  })

  it('renders the Memory heading', () => {
    renderMemoryViewer()
    expect(screen.getByText('Memory')).toBeInTheDocument()
  })

  it('renders the description text', () => {
    renderMemoryViewer()
    expect(
      screen.getByText('What the concierge remembers about you across sessions.'),
    ).toBeInTheDocument()
  })

  it('shows empty state when no memories are loaded', async () => {
    renderMemoryViewer()
    const emptyText = await screen.findByText('No memories stored yet. Start chatting!')
    expect(emptyText).toBeInTheDocument()
  })
})
