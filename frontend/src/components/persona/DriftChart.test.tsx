import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import DriftChart from './DriftChart'

// Mock recharts since it depends on DOM measurements
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
}))

describe('DriftChart', () => {
  it('renders empty state when no history', () => {
    render(<DriftChart history={[]} />)
    expect(
      screen.getByText('No persona data yet. Start chatting to see drift analysis.'),
    ).toBeInTheDocument()
  })

  it('renders chart when history has data', () => {
    render(
      <DriftChart
        history={[
          {
            conversation_id: 'conv-1',
            message_id: 'msg-1',
            scores: {
              sycophancy: 0.3,
              hallucination: 0.2,
              over_confidence: 0.1,
              safety_bypass: 0.15,
              sales_pressure: 0.25,
            },
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  it('does not render empty state when history has data', () => {
    render(
      <DriftChart
        history={[
          {
            conversation_id: 'conv-1',
            message_id: 'msg-1',
            scores: {
              sycophancy: 0.3,
              hallucination: 0.2,
              over_confidence: 0.1,
              safety_bypass: 0.15,
              sales_pressure: 0.25,
            },
            timestamp: new Date().toISOString(),
          },
        ]}
      />,
    )
    expect(
      screen.queryByText('No persona data yet. Start chatting to see drift analysis.'),
    ).not.toBeInTheDocument()
  })
})
