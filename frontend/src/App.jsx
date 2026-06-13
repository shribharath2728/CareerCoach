import { useApp } from './context/AppContext'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import InterviewPage from './pages/InterviewPage'
import AgentChat from './pages/AgentChat'
import CareerDashboard from './pages/CareerDashboard'
import SimulationEngine from './pages/SimulationEngine'
import ResumeAnalyzer from './pages/ResumeAnalyzer'
import History from './pages/History'
import Analytics from './pages/Analytics'
import Profile from './pages/Profile'
import SettingsPage from './pages/SettingsPage'
import JobTracker from './pages/JobTracker'
import ResumeBuilder from './pages/ResumeBuilder'
import JDAnalyzer from './pages/JDAnalyzer'
import Opportunities from './pages/Opportunities'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import ToastContainer from './components/ToastContainer'
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

const pageVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
}

export default function App() {
  const { user, activePage } = useApp()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  if (!user) {
    return (
      <>
        <Onboarding />
        <ToastContainer />
      </>
    )
  }

  let pageContent = null
  switch (activePage) {
    case 'dashboard': pageContent = <Dashboard key="dashboard" />; break
    case 'interview': pageContent = <InterviewPage key="interview" />; break
    case 'chat': pageContent = <AgentChat key="chat" />; break
    case 'career_dashboard': pageContent = <CareerDashboard key="career_dashboard" />; break
    case 'roadmap': pageContent = <SimulationEngine key="simulation" />; break
    case 'simulation': pageContent = <SimulationEngine key="simulation" />; break
    case 'resume_analyzer': pageContent = <ResumeAnalyzer key="resume_analyzer" />; break
    case 'history': pageContent = <History key="history" />; break
    case 'analytics': pageContent = <Analytics key="analytics" />; break
    case 'settings': pageContent = <SettingsPage key="settings" />; break
    case 'profile': pageContent = <Profile key="profile" />; break
    case 'job_tracker': pageContent = <JobTracker key="job" />; break
    case 'resume': pageContent = <ResumeBuilder key="resume" />; break
    case 'jd_analyzer': pageContent = <JDAnalyzer key="jd" />; break
    case 'opportunities': pageContent = <Opportunities key="opps" />; break
    default:
      pageContent = (
        <div key="soon" className="empty-state">
          <div className="empty-icon">🚧</div>
          <h3>Coming Soon</h3>
          <p>The <strong>{activePage.replace('_', ' ')}</strong> module is being built. Check back soon.</p>
        </div>
      )
  }

  return (
    <div className="app-shell">
      {/* Layer 1: Animated grid scanlines */}
      <div className="cyber-grid" />
      {/* Layer 2: HUD scanline sweep */}
      <div className="hud-scanline" />
      {/* Layer 3: Nebula orbs */}
      <div className="bg-orbs">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
      </div>

      <Sidebar
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Topbar onMenuToggle={() => setMobileMenuOpen(o => !o)} />
        <main className="main-content" role="main" id="main-content">
          <AnimatePresence mode="wait">
            <motion.div
              key={activePage}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              style={{ height: '100%' }}
            >
              {pageContent}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <ToastContainer />
    </div>
  )
}
