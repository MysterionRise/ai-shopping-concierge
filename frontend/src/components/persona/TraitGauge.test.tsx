import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TraitGauge from './TraitGauge'

describe('TraitGauge', () => {
  it('renders the trait name with spaces replacing underscores', () => {
    render(
      <TraitGauge
        name="over_confidence"
        score={0.3}
        threshold={0.7}
        description="Overly strong claims"
      />,
    )
    expect(screen.getByText('over confidence')).toBeInTheDocument()
  })

  it('renders the score as a percentage', () => {
    render(
      <TraitGauge
        name="sycophancy"
        score={0.45}
        threshold={0.65}
        description="Agreeing vs honest"
      />,
    )
    expect(screen.getByText('45.0%')).toBeInTheDocument()
  })

  it('renders the description', () => {
    render(
      <TraitGauge
        name="hallucination"
        score={0.2}
        threshold={0.7}
        description="Making unverified claims"
      />,
    )
    expect(screen.getByText('Making unverified claims')).toBeInTheDocument()
  })

  it('shows red styling when score exceeds threshold', () => {
    render(
      <TraitGauge
        name="safety_bypass"
        score={0.8}
        threshold={0.6}
        description="Bypassing safety"
      />,
    )
    // The percentage text should have red styling
    const scoreText = screen.getByText('80.0%')
    expect(scoreText.className).toContain('text-red-600')
  })

  it('does not show red styling when score is below threshold', () => {
    render(
      <TraitGauge
        name="sycophancy"
        score={0.3}
        threshold={0.65}
        description="Agreeing"
      />,
    )
    const scoreText = screen.getByText('30.0%')
    expect(scoreText.className).not.toContain('text-red-600')
  })

  it('renders the progress bar', () => {
    const { container } = render(
      <TraitGauge
        name="sales_pressure"
        score={0.5}
        threshold={0.7}
        description="Upselling"
      />,
    )
    const bar = container.querySelector('.bg-gray-100.rounded-full')
    expect(bar).toBeInTheDocument()
  })

  it('renders threshold marker', () => {
    const { container } = render(
      <TraitGauge
        name="hallucination"
        score={0.3}
        threshold={0.7}
        description="Claims"
      />,
    )
    const marker = container.querySelector('[title="Threshold: 70%"]')
    expect(marker).toBeInTheDocument()
  })
})
