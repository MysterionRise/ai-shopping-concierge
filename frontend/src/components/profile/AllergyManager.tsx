import { useState, useRef } from 'react'
import { AlertTriangle, Plus, X, Loader2, Check } from 'lucide-react'
import { useUserStore } from '../../stores/userStore'
import { useUpdateUser } from '../../hooks/useUser'

export default function AllergyManager() {
  const user = useUserStore((s) => s.user)
  const setUser = useUserStore((s) => s.setUser)
  const [allergies, setAllergies] = useState<string[]>(user?.allergies || [])
  const [newAllergy, setNewAllergy] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)
  const updateUser = useUpdateUser()
  const prevUserIdRef = useRef(user?.id)

  // Reset local state when the user identity changes (e.g. user selector switch)
  if (user?.id !== prevUserIdRef.current) {
    prevUserIdRef.current = user?.id
    setAllergies(user?.allergies || [])
    setNewAllergy('')
    setSaveSuccess(false)
  }

  const isDirty =
    JSON.stringify([...allergies].sort()) !==
    JSON.stringify([...(user?.allergies || [])].sort())

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

  const handleSave = () => {
    if (!user || !isDirty) return
    setSaveSuccess(false)
    updateUser.mutate(
      { userId: user.id, data: { allergies } },
      {
        onSuccess: (updated) => {
          setUser(updated)
          setSaveSuccess(true)
          setTimeout(() => setSaveSuccess(false), 2000)
        },
      },
    )
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

      {isDirty && (
        <div className="flex items-center gap-3 mt-4 pt-4 border-t border-red-100">
          <button
            onClick={handleSave}
            disabled={updateUser.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {updateUser.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : null}
            {updateUser.isPending ? 'Saving...' : 'Save Allergies'}
          </button>
          {updateUser.isError && (
            <span className="text-sm text-red-600">
              Failed to save. Please try again.
            </span>
          )}
        </div>
      )}

      {saveSuccess && !isDirty && (
        <div className="flex items-center gap-2 mt-3 text-sm text-green-600">
          <Check className="w-4 h-4" />
          Allergies saved successfully.
        </div>
      )}
    </section>
  )
}
