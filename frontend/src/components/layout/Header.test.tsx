import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Header from './Header'

vi.mock('./UserSelector', () => ({
  default: () => <div data-testid="user-selector">UserSelector</div>,
}))

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>,
  )
}

describe('Header', () => {
  it('renders the app name', () => {
    renderHeader()
    expect(screen.getByText('Beauty Concierge')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderHeader()
    expect(screen.getByText('Chat')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Persona')).toBeInTheDocument()
  })

  it('renders Chat link pointing to /', () => {
    renderHeader()
    const chatLink = screen.getByText('Chat').closest('a')
    expect(chatLink).toHaveAttribute('href', '/')
  })

  it('renders Profile link pointing to /profile', () => {
    renderHeader()
    const profileLink = screen.getByText('Profile').closest('a')
    expect(profileLink).toHaveAttribute('href', '/profile')
  })

  it('renders Persona link pointing to /persona', () => {
    renderHeader()
    const personaLink = screen.getByText('Persona').closest('a')
    expect(personaLink).toHaveAttribute('href', '/persona')
  })

  it('renders UserSelector', () => {
    renderHeader()
    expect(screen.getByTestId('user-selector')).toBeInTheDocument()
  })
})
