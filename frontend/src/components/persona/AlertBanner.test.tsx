import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AlertBanner from './AlertBanner'

describe('AlertBanner', () => {
  it('renders nothing when alerts is empty', () => {
    const { container } = render(<AlertBanner alerts={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders alert count in header', () => {
    render(
      <AlertBanner
        alerts={[
          {
            trait: 'sycophancy',
            score: 0.8,
            threshold: 0.65,
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(screen.getByText('Persona Alerts (1)')).toBeInTheDocument()
  })

  it('renders multiple alerts', () => {
    render(
      <AlertBanner
        alerts={[
          {
            trait: 'sycophancy',
            score: 0.8,
            threshold: 0.65,
            timestamp: new Date().toISOString(),
          },
          {
            trait: 'safety_bypass',
            score: 0.75,
            threshold: 0.6,
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(screen.getByText('Persona Alerts (2)')).toBeInTheDocument()
  })

  it('renders trait name with spaces replacing underscores', () => {
    render(
      <AlertBanner
        alerts={[
          {
            trait: 'safety_bypass',
            score: 0.75,
            threshold: 0.6,
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(screen.getByText('safety bypass')).toBeInTheDocument()
  })

  it('shows score and threshold percentages', () => {
    render(
      <AlertBanner
        alerts={[
          {
            trait: 'hallucination',
            score: 0.85,
            threshold: 0.7,
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(screen.getByText(/85\.0%/)).toBeInTheDocument()
    expect(screen.getByText(/70%/)).toBeInTheDocument()
  })

  it('displays exceeded threshold message', () => {
    render(
      <AlertBanner
        alerts={[
          {
            trait: 'sycophancy',
            score: 0.8,
            threshold: 0.65,
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(screen.getByText(/exceeded threshold/)).toBeInTheDocument()
  })
})
