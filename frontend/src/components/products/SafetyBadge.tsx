interface SafetyBadgeProps {
  score: number | null
}

export default function SafetyBadge({ score }: SafetyBadgeProps) {
  if (score === null) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        N/A
      </span>
    )
  }

  let colorClass: string
  let label: string

  if (score >= 8) {
    colorClass = 'bg-green-100 text-green-800'
    label = 'Safe'
  } else if (score >= 5) {
    colorClass = 'bg-yellow-100 text-yellow-800'
    label = 'Caution'
  } else {
    colorClass = 'bg-red-100 text-red-800'
    label = 'Warning'
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
      title={`Safety score: ${score}/10`}
    >
      {score.toFixed(1)} — {label}
    </span>
  )
}
