import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Sidebar from './Sidebar'

vi.mock('../../stores/chatStore', () => ({
  useChatStore: () => vi.fn(),
}))

vi.mock('../../stores/userStore', () => ({
  useUserStore: () => null,
}))

vi.mock('../../api/conversations', () => ({
  getConversations: vi.fn().mockResolvedValue([]),
  getConversationMessages: vi.fn().mockResolvedValue([]),
}))

function renderSidebar() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <Sidebar />
    </QueryClientProvider>,
  )
}

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the New Chat button', () => {
    renderSidebar()
    expect(screen.getByText('New Chat')).toBeInTheDocument()
  })

  it('renders the Recent section header', () => {
    renderSidebar()
    expect(screen.getByText('Recent')).toBeInTheDocument()
  })

  it('shows empty state when no conversations', () => {
    renderSidebar()
    expect(screen.getByText('No conversations yet')).toBeInTheDocument()
  })
})
