import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { PersonaEntry } from '../../types'

interface DriftChartProps {
  history: PersonaEntry[]
}

const TRAIT_COLORS: Record<string, string> = {
  sycophancy: '#ef4444',
  hallucination: '#f97316',
  overConfidence: '#eab308',
  safetyBypass: '#dc2626',
  salesPressure: '#8b5cf6',
}

export default function DriftChart({ history }: DriftChartProps) {
  const data = history.map((entry, i) => ({
    index: i + 1,
    ...entry.scores,
  }))

  if (data.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        No persona data yet. Start chatting to see drift analysis.
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="index" label={{ value: 'Message', position: 'bottom' }} />
        <YAxis domain={[0, 1]} />
        <Tooltip />
        <Legend />
        {Object.entries(TRAIT_COLORS).map(([key, color]) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={color}
            strokeWidth={2}
            dot={false}
            name={key.replace(/([A-Z])/g, ' $1').trim()}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
