import { useApp } from './context/AppContext'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import InterviewPage from './pages/InterviewPage'
import Chat from './pages/Chat'
import History from './pages/History'
import Analytics from './pages/Analytics'
import Profile from './pages/Profile'
import SettingsPage from './pages/SettingsPage'
import JobTracker from './pages/JobTracker'
import ResumeBuilder from './pages/ResumeBuilder'
import JDAnalyzer from './pages/JDAnalyzer'
import VoiceAssistant from './pages/VoiceAssistant'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import ToastContainer from './components/ToastContainer'
import { useState } from 'react'
import { AnimatePresence } from 'framer-motion'

export default function App() {
  const { user, activePage } = useApp()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // If no user is logged in, show the Onboarding flow.
  if (!user) {
    return (
      <>
        <Onboarding />
        <ToastContainer />
      </>
    )
  }

  // Determine which page to render based on activePage
  let pageContent = null
  switch (activePage) {
    case 'dashboard':
      pageContent = <Dashboard key="dashboard" />
      break
    case 'interview':
      pageContent = <InterviewPage key="interview" />
      break
    case 'chat':
      pageContent = <Chat key="chat" />
      break
    case 'history':
      pageContent = <History key="history" />
      break
    case 'analytics':
      pageContent = <Analytics key="analytics" />
      break
    case 'settings':
      pageContent = <SettingsPage key="settings" />
      break
    case 'profile':
      pageContent = <Profile key="profile" />
      break
    case 'job_tracker':
      pageContent = <JobTracker key="job" />
      break
    case 'resume':
      pageContent = <ResumeBuilder key="resume" />
      break
    case 'jd_analyzer':
      pageContent = <JDAnalyzer key="jd" />
      break
    case 'voice':
      pageContent = <VoiceAssistant key="voice" />
      break
    default:
      pageContent = (
        <div key="soon" className="empty-state">
          <div className="empty-icon">🚧</div>
          <h3>Coming Soon!</h3>
          <p>The <strong>{activePage.replace('_', ' ')}</strong> module is getting ready. Stay tuned!</p>
        </div>
      )
  }

  return (
    <div className="app-shell">
      <Sidebar 
        mobileOpen={mobileMenuOpen} 
        onMobileClose={() => setMobileMenuOpen(false)} 
      />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Topbar onMenuToggle={() => setMobileMenuOpen(o => !o)} />
        <main className="main-content">
          <AnimatePresence mode="wait">
            {pageContent}
          </AnimatePresence>
        </main>
      </div>
      <ToastContainer />
    </div>
  )
}
