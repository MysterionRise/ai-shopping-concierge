import { useState } from 'react'
import { useUserStore } from '../../stores/userStore'
import AllergyManager from './AllergyManager'
import MemoryViewer from './MemoryViewer'

const SKIN_TYPES = ['normal', 'oily', 'dry', 'combination', 'sensitive']
const SKIN_CONCERNS = [
  'acne',
  'aging',
  'dark spots',
  'dryness',
  'redness',
  'sensitivity',
  'large pores',
  'uneven texture',
]

export default function UserProfile() {
  const user = useUserStore((s) => s.user)
  const [skinType, setSkinType] = useState(user?.skinType || '')
  const [concerns, setConcerns] = useState<string[]>(user?.skinConcerns || [])

  const toggleConcern = (concern: string) => {
    setConcerns((prev) =>
      prev.includes(concern)
        ? prev.filter((c) => c !== concern)
        : [...prev, concern],
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 mb-1">
            Your Profile
          </h1>
          <p className="text-gray-500 text-sm">
            Help us personalize your experience
          </p>
        </div>

        <section className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Skin Type</h2>
          <div className="flex flex-wrap gap-2">
            {SKIN_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => setSkinType(type)}
                className={`px-4 py-2 rounded-full text-sm capitalize transition-colors ${
                  skinType === type
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </section>

        <section className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Skin Concerns
          </h2>
          <div className="flex flex-wrap gap-2">
            {SKIN_CONCERNS.map((concern) => (
              <button
                key={concern}
                onClick={() => toggleConcern(concern)}
                className={`px-4 py-2 rounded-full text-sm capitalize transition-colors ${
                  concerns.includes(concern)
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {concern}
              </button>
            ))}
          </div>
        </section>

        <AllergyManager />
        <MemoryViewer />
      </div>
    </div>
  )
}
