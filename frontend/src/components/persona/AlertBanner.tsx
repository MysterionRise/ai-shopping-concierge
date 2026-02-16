import { AlertTriangle } from 'lucide-react'

interface Alert {
  trait: string
  score: number
  threshold: number
  timestamp: string
}

interface AlertBannerProps {
  alerts: Alert[]
}

export default function AlertBanner({ alerts }: AlertBannerProps) {
  if (alerts.length === 0) return null

  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className="w-5 h-5 text-red-500" />
        <h3 className="font-medium text-red-800">
          Persona Alerts ({alerts.length})
        </h3>
      </div>
      <div className="space-y-1">
        {alerts.map((alert, i) => (
          <p key={i} className="text-sm text-red-700">
            <span className="font-medium capitalize">
              {alert.trait.replace('_', ' ')}
            </span>{' '}
            exceeded threshold: {(alert.score * 100).toFixed(1)}% &gt;{' '}
            {(alert.threshold * 100).toFixed(0)}%
          </p>
        ))}
      </div>
    </div>
  )
}
