import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SafetyBadge from './SafetyBadge'

describe('SafetyBadge', () => {
  it('renders "Safe" for score >= 8', () => {
    render(<SafetyBadge score={8.5} />)
    expect(screen.getByText(/Safe/)).toBeInTheDocument()
    expect(screen.getByText(/8\.5/)).toBeInTheDocument()
  })

  it('renders "Caution" for score >= 5 and < 8', () => {
    render(<SafetyBadge score={6.0} />)
    expect(screen.getByText(/Caution/)).toBeInTheDocument()
    expect(screen.getByText(/6\.0/)).toBeInTheDocument()
  })

  it('renders "Warning" for score < 5', () => {
    render(<SafetyBadge score={3.2} />)
    expect(screen.getByText(/Warning/)).toBeInTheDocument()
    expect(screen.getByText(/3\.2/)).toBeInTheDocument()
  })

  it('renders "Unverified" when score is null', () => {
    render(<SafetyBadge score={null} />)
    expect(screen.getByText(/Unverified/)).toBeInTheDocument()
  })

  it('renders "Unverified" when badge is "unverified"', () => {
    render(<SafetyBadge score={9.0} badge="unverified" />)
    expect(screen.getByText(/Unverified/)).toBeInTheDocument()
  })

  it('shows safety score in title attribute', () => {
    render(<SafetyBadge score={8.0} />)
    expect(screen.getByTitle('Safety score: 8/10')).toBeInTheDocument()
  })

  it('renders "Safe" at exactly score 8', () => {
    render(<SafetyBadge score={8} />)
    expect(screen.getByText(/Safe/)).toBeInTheDocument()
  })

  it('renders "Caution" at exactly score 5', () => {
    render(<SafetyBadge score={5} />)
    expect(screen.getByText(/Caution/)).toBeInTheDocument()
  })
})
