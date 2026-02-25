import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import PersonaMonitor from './PersonaMonitor'

vi.mock('../../stores/chatStore', () => ({
  useChatStore: () => 'conv-1',
}))

const mockFetchHistory = vi.fn()
const mockFetchAlerts = vi.fn()

vi.mock('../../stores/personaStore', () => ({
  usePersonaStore: () => ({
    currentScores: {
      sycophancy: 0.3,
      hallucination: 0.5,
      over_confidence: 0.2,
      safety_bypass: 0.1,
      sales_pressure: 0.4,
    },
    scoreHistory: [],
    fetchHistory: mockFetchHistory,
    fetchAlerts: mockFetchAlerts,
    alerts: [],
    isLoading: false,
  }),
}))

vi.mock('../../hooks/usePersonaStream', () => ({
  usePersonaStream: vi.fn(),
}))

vi.mock('./TraitGauge', () => ({
  default: ({ name, score }: { name: string; score: number }) => (
    <div data-testid={`trait-${name}`}>
      {name}: {(score * 100).toFixed(1)}%
    </div>
  ),
}))

vi.mock('./DriftChart', () => ({
  default: () => <div data-testid="drift-chart">DriftChart</div>,
}))

vi.mock('./AlertBanner', () => ({
  default: ({ alerts }: { alerts: unknown[] }) => (
    <div data-testid="alert-banner">{alerts.length} alerts</div>
  ),
}))

describe('PersonaMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page heading', () => {
    render(<PersonaMonitor />)
    expect(screen.getByText('Persona Monitor')).toBeInTheDocument()
  })

  it('renders the description text', () => {
    render(<PersonaMonitor />)
    expect(
      screen.getByText(/Real-time monitoring of AI behavior traits/),
    ).toBeInTheDocument()
  })

  it('renders all 5 trait gauges', () => {
    render(<PersonaMonitor />)
    expect(screen.getByTestId('trait-sycophancy')).toBeInTheDocument()
    expect(screen.getByTestId('trait-hallucination')).toBeInTheDocument()
    expect(screen.getByTestId('trait-over_confidence')).toBeInTheDocument()
    expect(screen.getByTestId('trait-safety_bypass')).toBeInTheDocument()
    expect(screen.getByTestId('trait-sales_pressure')).toBeInTheDocument()
  })

  it('renders alert banner', () => {
    render(<PersonaMonitor />)
    expect(screen.getByTestId('alert-banner')).toBeInTheDocument()
  })

  it('renders drift chart', () => {
    render(<PersonaMonitor />)
    expect(screen.getByTestId('drift-chart')).toBeInTheDocument()
  })

  it('renders section headings', () => {
    render(<PersonaMonitor />)
    expect(screen.getByText('Current Trait Scores')).toBeInTheDocument()
    expect(screen.getByText('Trait Drift Over Conversation')).toBeInTheDocument()
  })

  it('calls fetchHistory and fetchAlerts on mount', () => {
    render(<PersonaMonitor />)
    expect(mockFetchHistory).toHaveBeenCalledWith('conv-1')
    expect(mockFetchAlerts).toHaveBeenCalledWith('conv-1')
  })
})
