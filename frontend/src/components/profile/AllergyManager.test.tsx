import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AllergyManager from './AllergyManager'
import { useUserStore } from '../../stores/userStore'

vi.mock('../../hooks/useUser', () => ({
  useUpdateUser: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
}))

function renderAllergyManager() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <AllergyManager />
    </QueryClientProvider>,
  )
}

describe('AllergyManager', () => {
  beforeEach(() => {
    useUserStore.setState({
      user: {
        id: 'user-1',
        displayName: 'Test User',
        skinType: 'oily',
        skinConcerns: [],
        allergies: ['paraben', 'sulfate'],
        preferences: {},
        memoryEnabled: true,
      },
    })
  })

  it('renders the section heading', () => {
    renderAllergyManager()
    expect(screen.getByText('Allergies & Sensitivities')).toBeInTheDocument()
  })

  it('renders existing allergy tags', () => {
    renderAllergyManager()
    expect(screen.getByText('paraben')).toBeInTheDocument()
    expect(screen.getByText('sulfate')).toBeInTheDocument()
  })

  it('adds a new allergy via input and button', () => {
    renderAllergyManager()
    const input = screen.getByPlaceholderText('e.g., paraben, sulfate, fragrance')
    fireEvent.change(input, { target: { value: 'fragrance' } })
    // The add button is the sibling of the input in the flex container
    const addButton = input.parentElement!.querySelector('button')!
    fireEvent.click(addButton)
    expect(screen.getByText('fragrance')).toBeInTheDocument()
  })

  it('adds a new allergy via Enter key', () => {
    renderAllergyManager()
    const input = screen.getByPlaceholderText('e.g., paraben, sulfate, fragrance')
    fireEvent.change(input, { target: { value: 'retinol' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByText('retinol')).toBeInTheDocument()
  })

  it('does not add duplicate allergies', () => {
    renderAllergyManager()
    const input = screen.getByPlaceholderText('e.g., paraben, sulfate, fragrance')
    fireEvent.change(input, { target: { value: 'paraben' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    // Should still have exactly one 'paraben' tag (the original)
    const parabenTags = screen.getAllByText('paraben')
    expect(parabenTags).toHaveLength(1)
  })

  it('removes an allergy when X is clicked', () => {
    renderAllergyManager()
    // Each allergy tag is a <span> containing the text and a <button> with X icon
    const sulfateTag = screen.getByText('sulfate')
    // The X button is a direct child of the span tag element
    const removeButton = sulfateTag.querySelector('button')!
    fireEvent.click(removeButton)
    expect(screen.queryByText('sulfate')).not.toBeInTheDocument()
  })

  it('shows empty state when no allergies', () => {
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
    renderAllergyManager()
    expect(screen.getByText('No allergies added yet')).toBeInTheDocument()
  })

  it('shows Save button when allergies are modified', () => {
    renderAllergyManager()
    const input = screen.getByPlaceholderText('e.g., paraben, sulfate, fragrance')
    fireEvent.change(input, { target: { value: 'niacinamide' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByText('Save Allergies')).toBeInTheDocument()
  })
})
