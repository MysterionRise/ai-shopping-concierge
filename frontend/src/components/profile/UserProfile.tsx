import { useState } from 'react'
import { updateUser } from '../../api/users'
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
  const setUser = useUserStore((s) => s.setUser)
  const [skinType, setSkinType] = useState(user?.skinType || '')
  const [concerns, setConcerns] = useState<string[]>(user?.skinConcerns || [])
  const [memoryEnabled, setMemoryEnabled] = useState(user?.memoryEnabled ?? true)
  const [toggling, setToggling] = useState(false)

  const toggleConcern = (concern: string) => {
    setConcerns((prev) =>
      prev.includes(concern)
        ? prev.filter((c) => c !== concern)
        : [...prev, concern],
    )
  }

  const handleMemoryToggle = async () => {
    if (!user || toggling) return
    setToggling(true)
    try {
      const updated = await updateUser(user.id, { memoryEnabled: !memoryEnabled })
      setMemoryEnabled(updated.memoryEnabled)
      setUser(updated)
    } catch {
      // Revert on error
    } finally {
      setToggling(false)
    }
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

        <section className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">
                AI Memory
              </h2>
              <p className="text-gray-500 text-sm mt-1">
                When enabled, the assistant remembers your skin type, preferences,
                and allergies to give personalized recommendations. You can view
                and delete stored memories below.
              </p>
            </div>
            <button
              onClick={handleMemoryToggle}
              disabled={toggling}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ml-4 ${
                memoryEnabled ? 'bg-primary-500' : 'bg-gray-300'
              } ${toggling ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              role="switch"
              aria-checked={memoryEnabled}
              aria-label="Allow AI to remember conversations"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  memoryEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </section>

        <AllergyManager />
        {memoryEnabled && <MemoryViewer />}
      </div>
    </div>
  )
}
