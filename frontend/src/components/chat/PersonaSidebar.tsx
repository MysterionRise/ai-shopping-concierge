import { useEffect } from 'react'
import { Activity } from 'lucide-react'
import TraitGauge from '../persona/TraitGauge'
import DriftChart from '../persona/DriftChart'
import { usePersonaStore } from '../../stores/personaStore'
import { useChatStore } from '../../stores/chatStore'
import { usePersonaStream } from '../../hooks/usePersonaStream'

const TRAIT_DEFINITIONS = [
  { name: 'sycophancy', threshold: 0.65, description: 'Agreeing vs honest advice' },
  { name: 'hallucination', threshold: 0.7, description: 'Unverified claims' },
  { name: 'over_confidence', threshold: 0.7, description: 'Overly strong claims' },
  { name: 'safety_bypass', threshold: 0.6, description: 'Bypassing safety' },
  { name: 'sales_pressure', threshold: 0.7, description: 'Upselling behavior' },
]

export default function PersonaSidebar() {
  const conversationId = useChatStore((s) => s.currentConversationId)
  const { currentScores, scoreHistory, fetchHistory } = usePersonaStore()

  usePersonaStream(conversationId)

  useEffect(() => {
    if (conversationId) {
      fetchHistory(conversationId)
    }
  }, [conversationId, fetchHistory])

  const normalizedHistory = scoreHistory.map((entry) => ({
    conversation_id: entry.conversation_id,
    message_id: entry.message_id,
    scores: {
      sycophancy: entry.scores.sycophancy || 0,
      hallucination: entry.scores.hallucination || 0,
      over_confidence: entry.scores.over_confidence || 0,
      safety_bypass: entry.scores.safety_bypass || 0,
      sales_pressure: entry.scores.sales_pressure || 0,
    },
    timestamp: entry.timestamp,
  }))

  return (
    <div className="w-80 border-l border-gray-200 bg-white overflow-y-auto p-4">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-4 h-4 text-primary-500" />
        <h3 className="text-sm font-semibold text-gray-700">Persona Monitor</h3>
      </div>

      <div className="space-y-3 mb-4">
        {TRAIT_DEFINITIONS.map((trait) => (
          <TraitGauge
            key={trait.name}
            name={trait.name}
            score={currentScores[trait.name] || 0}
            threshold={trait.threshold}
            description={trait.description}
          />
        ))}
      </div>

      <div className="border-t border-gray-100 pt-3">
        <h4 className="text-xs font-medium text-gray-500 mb-2">Drift</h4>
        <DriftChart history={normalizedHistory} />
      </div>
    </div>
  )
}
