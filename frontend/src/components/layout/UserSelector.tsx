import { useState, useRef, useEffect } from 'react'
import { ChevronDown, User as UserIcon } from 'lucide-react'
import { useUserStore } from '../../stores/userStore'
import { useAvailableUsers, useSwitchUser } from '../../hooks/useUser'
import { User } from '../../types'

function skinBadgeColor(skinType: string | null): string {
  switch (skinType) {
    case 'oily':
      return 'bg-yellow-100 text-yellow-700'
    case 'dry':
      return 'bg-blue-100 text-blue-700'
    case 'sensitive':
      return 'bg-red-100 text-red-700'
    case 'combination':
      return 'bg-purple-100 text-purple-700'
    case 'normal':
      return 'bg-green-100 text-green-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

export default function UserSelector() {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const currentUser = useUserStore((s) => s.user)
  const availableUsers = useUserStore((s) => s.availableUsers)
  const isLoadingUsers = useUserStore((s) => s.isLoadingUsers)
  const switchUser = useSwitchUser()

  const { data: fetchedUsers } = useAvailableUsers()

  // Auto-select first user when list loads and no user is selected
  useEffect(() => {
    if (!currentUser && fetchedUsers && fetchedUsers.length > 0) {
      switchUser(fetchedUsers[0])
    }
  }, [fetchedUsers, currentUser, switchUser])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (user: User) => {
    switchUser(user)
    setOpen(false)
  }

  const displayLabel = currentUser?.displayName || 'Select User'

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
      >
        <UserIcon className="w-4 h-4 text-gray-500" />
        <span className="text-gray-700 max-w-[140px] truncate">{displayLabel}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-50 py-1 max-h-80 overflow-y-auto">
          {isLoadingUsers ? (
            <div className="px-4 py-3 text-sm text-gray-500">Loading users...</div>
          ) : availableUsers.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500">
              No users found. Run <code className="bg-gray-100 px-1 rounded text-xs">generate_test_users.py</code> to create demo users.
            </div>
          ) : (
            availableUsers.map((user) => (
              <button
                key={user.id}
                onClick={() => handleSelect(user)}
                className={`w-full text-left px-4 py-2.5 hover:bg-gray-50 transition-colors ${
                  currentUser?.id === user.id ? 'bg-primary-50' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">
                    {user.displayName}
                  </span>
                  {user.skinType && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${skinBadgeColor(user.skinType)}`}>
                      {user.skinType}
                    </span>
                  )}
                </div>
                {user.allergies.length > 0 && (
                  <div className="text-xs text-gray-500 mt-0.5">
                    Allergies: {user.allergies.join(', ')}
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
