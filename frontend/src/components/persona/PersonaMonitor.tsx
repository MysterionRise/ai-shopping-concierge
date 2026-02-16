import { Activity } from 'lucide-react'
import TraitGauge from './TraitGauge'
import DriftChart from './DriftChart'
import AlertBanner from './AlertBanner'
import { PersonaEntry } from '../../types'

const TRAIT_DEFINITIONS = [
  {
    name: 'sycophancy',
    threshold: 0.65,
    description: 'Tendency to agree rather than provide honest advice',
  },
  {
    name: 'hallucination',
    threshold: 0.7,
    description: 'Making unverified product claims',
  },
  {
    name: 'over_confidence',
    threshold: 0.7,
    description: 'Overly strong claims about product efficacy',
  },
  {
    name: 'safety_bypass',
    threshold: 0.6,
    description: 'Willingness to bypass safety constraints',
  },
  {
    name: 'sales_pressure',
    threshold: 0.7,
    description: 'Excessive upselling behavior',
  },
]

// Mock data — will be replaced with real API data
const MOCK_SCORES: Record<string, number> = {
  sycophancy: 0.23,
  hallucination: 0.15,
  over_confidence: 0.31,
  safety_bypass: 0.08,
  sales_pressure: 0.19,
}

const MOCK_HISTORY: PersonaEntry[] = []

export default function PersonaMonitor() {
  const scores = MOCK_SCORES
  const history = MOCK_HISTORY
  const alerts = TRAIT_DEFINITIONS.filter(
    (t) => (scores[t.name] || 0) > t.threshold,
  ).map((t) => ({
    trait: t.name,
    score: scores[t.name] || 0,
    threshold: t.threshold,
    timestamp: new Date().toISOString(),
  }))

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-6 h-6 text-primary-500" />
            <h1 className="text-2xl font-semibold text-gray-900">
              Persona Monitor
            </h1>
          </div>
          <p className="text-gray-500 text-sm">
            Real-time monitoring of AI behavior traits using hidden state
            activation analysis
          </p>
        </div>

        <AlertBanner alerts={alerts} />

        <section className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Current Trait Scores
          </h2>
          <div className="space-y-4">
            {TRAIT_DEFINITIONS.map((trait) => (
              <TraitGauge
                key={trait.name}
                name={trait.name}
                score={scores[trait.name] || 0}
                threshold={trait.threshold}
                description={trait.description}
              />
            ))}
          </div>
        </section>

        <section className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Trait Drift Over Conversation
          </h2>
          <DriftChart history={history} />
        </section>
      </div>
    </div>
  )
}
