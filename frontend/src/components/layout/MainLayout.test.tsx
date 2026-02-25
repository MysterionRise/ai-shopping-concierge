import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import MainLayout from './MainLayout'

vi.mock('./Header', () => ({
  default: () => <div data-testid="header">Header</div>,
}))

vi.mock('./Sidebar', () => ({
  default: () => <div data-testid="sidebar">Sidebar</div>,
}))

function renderMainLayout() {
  return render(
    <MemoryRouter>
      <MainLayout />
    </MemoryRouter>,
  )
}

describe('MainLayout', () => {
  it('renders the header', () => {
    renderMainLayout()
    expect(screen.getByTestId('header')).toBeInTheDocument()
  })

  it('renders the sidebar', () => {
    renderMainLayout()
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
  })

  it('renders a main content area', () => {
    renderMainLayout()
    const main = document.querySelector('main')
    expect(main).toBeInTheDocument()
  })
})
