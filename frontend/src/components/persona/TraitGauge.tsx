interface TraitGaugeProps {
  name: string
  score: number
  threshold: number
  description: string
}

export default function TraitGauge({
  name,
  score,
  threshold,
  description,
}: TraitGaugeProps) {
  const percentage = Math.min(score * 100, 100)
  const isAlert = score > threshold

  let barColor: string
  if (isAlert) barColor = 'bg-red-500'
  else if (score > threshold * 0.7) barColor = 'bg-yellow-500'
  else barColor = 'bg-green-500'

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700 capitalize">
          {name.replace('_', ' ')}
        </span>
        <span
          className={`text-xs font-mono ${isAlert ? 'text-red-600 font-bold' : 'text-gray-500'}`}
        >
          {(score * 100).toFixed(1)}%
        </span>
      </div>
      <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
        <div
          className="absolute inset-y-0 w-0.5 bg-gray-400"
          style={{ left: `${threshold * 100}%` }}
          title={`Threshold: ${(threshold * 100).toFixed(0)}%`}
        />
      </div>
      <p className="text-xs text-gray-400">{description}</p>
    </div>
  )
}
