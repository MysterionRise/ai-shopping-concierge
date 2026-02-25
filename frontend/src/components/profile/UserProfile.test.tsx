import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import UserProfile from './UserProfile'
import { useUserStore } from '../../stores/userStore'

vi.mock('../../hooks/useUser', () => ({
  useUpdateUser: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
}))

vi.mock('./AllergyManager', () => ({
  default: () => <div data-testid="allergy-manager">AllergyManager</div>,
}))

vi.mock('./MemoryViewer', () => ({
  default: () => <div data-testid="memory-viewer">MemoryViewer</div>,
}))

function renderUserProfile() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <UserProfile />
    </QueryClientProvider>,
  )
}

describe('UserProfile', () => {
  beforeEach(() => {
    useUserStore.setState({
      user: {
        id: 'user-1',
        displayName: 'Test User',
        skinType: 'oily',
        skinConcerns: ['acne', 'aging'],
        allergies: ['paraben'],
        preferences: {},
        memoryEnabled: true,
      },
    })
  })

  it('renders the profile heading', () => {
    renderUserProfile()
    expect(screen.getByText('Your Profile')).toBeInTheDocument()
    expect(screen.getByText('Help us personalize your experience')).toBeInTheDocument()
  })

  it('renders the Skin Type section with all options', () => {
    renderUserProfile()
    expect(screen.getByText('Skin Type')).toBeInTheDocument()
    expect(screen.getByText('normal')).toBeInTheDocument()
    expect(screen.getByText('oily')).toBeInTheDocument()
    expect(screen.getByText('dry')).toBeInTheDocument()
    expect(screen.getByText('combination')).toBeInTheDocument()
    expect(screen.getByText('sensitive')).toBeInTheDocument()
  })

  it('renders the Skin Concerns section with all options', () => {
    renderUserProfile()
    expect(screen.getByText('Skin Concerns')).toBeInTheDocument()
    expect(screen.getByText('acne')).toBeInTheDocument()
    expect(screen.getByText('aging')).toBeInTheDocument()
    expect(screen.getByText('dark spots')).toBeInTheDocument()
    expect(screen.getByText('dryness')).toBeInTheDocument()
    expect(screen.getByText('redness')).toBeInTheDocument()
    expect(screen.getByText('sensitivity')).toBeInTheDocument()
    expect(screen.getByText('large pores')).toBeInTheDocument()
    expect(screen.getByText('uneven texture')).toBeInTheDocument()
  })

  it('shows Save Changes button when skin type is changed', () => {
    renderUserProfile()
    expect(screen.queryByText('Save Changes')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('dry'))
    expect(screen.getByText('Save Changes')).toBeInTheDocument()
  })

  it('shows Save Changes button when concerns are changed', () => {
    renderUserProfile()
    expect(screen.queryByText('Save Changes')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('dryness'))
    expect(screen.getByText('Save Changes')).toBeInTheDocument()
  })

  it('hides Save Changes when change is reverted', () => {
    renderUserProfile()
    fireEvent.click(screen.getByText('dry'))
    expect(screen.getByText('Save Changes')).toBeInTheDocument()
    // Revert back to oily
    fireEvent.click(screen.getByText('oily'))
    expect(screen.queryByText('Save Changes')).not.toBeInTheDocument()
  })

  it('toggles skin concern on click', () => {
    renderUserProfile()
    // 'dryness' is not in user's concerns, clicking adds it
    fireEvent.click(screen.getByText('dryness'))
    expect(screen.getByText('Save Changes')).toBeInTheDocument()
    // Click again to remove it (but still dirty from previous state)
    fireEvent.click(screen.getByText('dryness'))
    // Now concerns match original, so no save button
    expect(screen.queryByText('Save Changes')).not.toBeInTheDocument()
  })

  it('renders the AI Memory section', () => {
    renderUserProfile()
    expect(screen.getByText('AI Memory')).toBeInTheDocument()
    expect(screen.getByRole('switch')).toBeInTheDocument()
  })

  it('renders the memory toggle with correct initial state', () => {
    renderUserProfile()
    const toggle = screen.getByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })

  it('renders AllergyManager', () => {
    renderUserProfile()
    expect(screen.getByTestId('allergy-manager')).toBeInTheDocument()
  })

  it('renders MemoryViewer when memory is enabled', () => {
    renderUserProfile()
    expect(screen.getByTestId('memory-viewer')).toBeInTheDocument()
  })

  it('hides MemoryViewer when memory is disabled', () => {
    useUserStore.setState({
      user: {
        id: 'user-1',
        displayName: 'Test User',
        skinType: 'oily',
        skinConcerns: [],
        allergies: [],
        preferences: {},
        memoryEnabled: false,
      },
    })
    renderUserProfile()
    expect(screen.queryByTestId('memory-viewer')).not.toBeInTheDocument()
  })
})
