import { Link } from 'react-router-dom'
import { Sparkles, User, Activity } from 'lucide-react'
import UserSelector from './UserSelector'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <Link to="/" className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-primary-500" />
          <span className="text-xl font-semibold text-gray-900">
            Beauty Concierge
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <nav className="flex items-center gap-4">
            <Link
              to="/"
              className="text-sm text-gray-600 hover:text-primary-600 transition-colors"
            >
              Chat
            </Link>
            <Link
              to="/profile"
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-primary-600 transition-colors"
            >
              <User className="w-4 h-4" />
              Profile
            </Link>
            <Link
              to="/persona"
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-primary-600 transition-colors"
            >
              <Activity className="w-4 h-4" />
              Persona
            </Link>
          </nav>
          <div className="w-px h-5 bg-gray-200" />
          <UserSelector />
        </div>
      </div>
    </header>
  )
}
