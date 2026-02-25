import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePersonaStore } from './personaStore'

vi.mock('../api/persona', () => ({
  getPersonaHistory: vi.fn().mockResolvedValue([]),
  getPersonaAlerts: vi.fn().mockResolvedValue([]),
}))

describe('personaStore', () => {
  beforeEach(() => {
    usePersonaStore.setState({
      currentScores: {},
      scoreHistory: [],
      alerts: [],
      disclaimers: {},
      isLoading: false,
    })
  })

  it('has correct initial state', () => {
    const state = usePersonaStore.getState()
    expect(state.currentScores).toEqual({})
    expect(state.scoreHistory).toEqual([])
    expect(state.alerts).toEqual([])
    expect(state.disclaimers).toEqual({})
    expect(state.isLoading).toBe(false)
  })

  it('updateScores adds entry and updates current scores', () => {
    const entry = {
      conversation_id: 'conv-1',
      message_id: 'msg-1',
      scores: { sycophancy: 0.3, hallucination: 0.2 },
      timestamp: new Date().toISOString(),
    }
    usePersonaStore.getState().updateScores(entry)
    const state = usePersonaStore.getState()
    expect(state.currentScores).toEqual({ sycophancy: 0.3, hallucination: 0.2 })
    expect(state.scoreHistory).toHaveLength(1)
    expect(state.scoreHistory[0].message_id).toBe('msg-1')
  })

  it('updateScores appends to history', () => {
    const entry1 = {
      conversation_id: 'conv-1',
      message_id: 'msg-1',
      scores: { sycophancy: 0.3 },
      timestamp: new Date().toISOString(),
    }
    const entry2 = {
      conversation_id: 'conv-1',
      message_id: 'msg-2',
      scores: { sycophancy: 0.5 },
      timestamp: new Date().toISOString(),
    }
    usePersonaStore.getState().updateScores(entry1)
    usePersonaStore.getState().updateScores(entry2)
    expect(usePersonaStore.getState().scoreHistory).toHaveLength(2)
    expect(usePersonaStore.getState().currentScores).toEqual({ sycophancy: 0.5 })
  })

  it('setHistory replaces history and sets latest scores', () => {
    const history = [
      {
        conversation_id: 'conv-1',
        message_id: 'msg-1',
        scores: { sycophancy: 0.2 },
        timestamp: '2025-01-01T00:00:00Z',
      },
      {
        conversation_id: 'conv-1',
        message_id: 'msg-2',
        scores: { sycophancy: 0.6 },
        timestamp: '2025-01-01T00:01:00Z',
      },
    ]
    usePersonaStore.getState().setHistory(history)
    expect(usePersonaStore.getState().scoreHistory).toHaveLength(2)
    expect(usePersonaStore.getState().currentScores).toEqual({ sycophancy: 0.6 })
  })

  it('setHistory with empty array clears scores', () => {
    usePersonaStore.setState({ currentScores: { sycophancy: 0.5 } })
    usePersonaStore.getState().setHistory([])
    expect(usePersonaStore.getState().currentScores).toEqual({})
    expect(usePersonaStore.getState().scoreHistory).toEqual([])
  })

  it('setAlerts replaces alerts', () => {
    const alerts = [
      {
        trait: 'sycophancy',
        score: 0.8,
        threshold: 0.65,
        message_id: 'msg-1',
        timestamp: new Date().toISOString(),
      },
    ]
    usePersonaStore.getState().setAlerts(alerts)
    expect(usePersonaStore.getState().alerts).toHaveLength(1)
    expect(usePersonaStore.getState().alerts[0].trait).toBe('sycophancy')
  })

  it('addDisclaimer adds a disclaimer for a message', () => {
    usePersonaStore.getState().addDisclaimer('msg-1', 'AI confidence notice')
    expect(usePersonaStore.getState().disclaimers['msg-1']).toBe('AI confidence notice')
  })

  it('addDisclaimer preserves existing disclaimers', () => {
    usePersonaStore.getState().addDisclaimer('msg-1', 'First')
    usePersonaStore.getState().addDisclaimer('msg-2', 'Second')
    expect(usePersonaStore.getState().disclaimers['msg-1']).toBe('First')
    expect(usePersonaStore.getState().disclaimers['msg-2']).toBe('Second')
  })

  it('clear resets all state', () => {
    usePersonaStore.setState({
      currentScores: { sycophancy: 0.5 },
      scoreHistory: [
        {
          conversation_id: 'c',
          message_id: 'm',
          scores: { sycophancy: 0.5 },
          timestamp: '',
        },
      ],
      alerts: [{ trait: 'x', score: 0.8, threshold: 0.6, message_id: 'm', timestamp: '' }],
      disclaimers: { 'm': 'text' },
    })
    usePersonaStore.getState().clear()
    const state = usePersonaStore.getState()
    expect(state.currentScores).toEqual({})
    expect(state.scoreHistory).toEqual([])
    expect(state.alerts).toEqual([])
    expect(state.disclaimers).toEqual({})
  })
})
