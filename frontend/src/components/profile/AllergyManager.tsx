import { useState } from 'react'
import { AlertTriangle, Plus, X } from 'lucide-react'
import { useUserStore } from '../../stores/userStore'

export default function AllergyManager() {
  const user = useUserStore((s) => s.user)
  const [allergies, setAllergies] = useState<string[]>(user?.allergies || [])
  const [newAllergy, setNewAllergy] = useState('')

  const addAllergy = () => {
    const trimmed = newAllergy.trim().toLowerCase()
    if (trimmed && !allergies.includes(trimmed)) {
      setAllergies([...allergies, trimmed])
      setNewAllergy('')
    }
  }

  const removeAllergy = (allergy: string) => {
    setAllergies(allergies.filter((a) => a !== allergy))
  }

  return (
    <section className="bg-white rounded-xl border border-red-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-red-500" />
        <h2 className="text-lg font-medium text-gray-900">
          Allergies & Sensitivities
        </h2>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        Products containing these ingredients will be automatically filtered out.
      </p>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={newAllergy}
          onChange={(e) => setNewAllergy(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addAllergy()}
          placeholder="e.g., paraben, sulfate, fragrance"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
        />
        <button
          onClick={addAllergy}
          disabled={!newAllergy.trim()}
          className="px-3 py-2 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50 transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {allergies.map((allergy) => (
          <span
            key={allergy}
            className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-red-50 text-red-700 border border-red-200"
          >
            {allergy}
            <button
              onClick={() => removeAllergy(allergy)}
              className="hover:text-red-900"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        {allergies.length === 0 && (
          <span className="text-sm text-gray-400">No allergies added yet</span>
        )}
      </div>
    </section>
  )
}
