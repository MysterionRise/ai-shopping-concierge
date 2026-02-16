import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import ChatView from './components/chat/ChatView'
import UserProfile from './components/profile/UserProfile'
import PersonaMonitor from './components/persona/PersonaMonitor'

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<ChatView />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="/persona" element={<PersonaMonitor />} />
      </Route>
    </Routes>
  )
}
