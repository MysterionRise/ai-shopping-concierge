import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import UserSelector from './UserSelector'
import { useUserStore } from '../../stores/userStore'

vi.mock('../../hooks/useUser', () => ({
  useAvailableUsers: () => ({ data: undefined }),
  useSwitchUser: () => vi.fn(),
}))

function renderUserSelector() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <UserSelector />
    </QueryClientProvider>,
  )
}

describe('UserSelector', () => {
  beforeEach(() => {
    useUserStore.setState({
      user: {
        id: 'user-1',
        displayName: 'Jane Doe',
        skinType: 'oily',
        skinConcerns: ['acne'],
        allergies: ['paraben'],
        preferences: {},
        memoryEnabled: true,
      },
      availableUsers: [
        {
          id: 'user-1',
          displayName: 'Jane Doe',
          skinType: 'oily',
          skinConcerns: ['acne'],
          allergies: ['paraben'],
          preferences: {},
          memoryEnabled: true,
        },
        {
          id: 'user-2',
          displayName: 'John Smith',
          skinType: 'dry',
          skinConcerns: [],
          allergies: [],
          preferences: {},
          memoryEnabled: true,
        },
      ],
      isLoadingUsers: false,
    })
  })

  it('renders the current user name', () => {
    renderUserSelector()
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
  })

  it('shows Select User when no user is selected', () => {
    useUserStore.setState({ user: null })
    renderUserSelector()
    expect(screen.getByText('Select User')).toBeInTheDocument()
  })

  it('opens dropdown on click and shows available users', () => {
    renderUserSelector()
    fireEvent.click(screen.getByText('Jane Doe'))
    expect(screen.getByText('John Smith')).toBeInTheDocument()
  })

  it('shows skin type badges in dropdown', () => {
    renderUserSelector()
    fireEvent.click(screen.getByText('Jane Doe'))
    expect(screen.getByText('oily')).toBeInTheDocument()
    expect(screen.getByText('dry')).toBeInTheDocument()
  })

  it('shows allergy info in dropdown', () => {
    renderUserSelector()
    fireEvent.click(screen.getByText('Jane Doe'))
    expect(screen.getByText('Allergies: paraben')).toBeInTheDocument()
  })
})
