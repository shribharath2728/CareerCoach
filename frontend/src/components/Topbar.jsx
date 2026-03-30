import { useApp } from '../context/AppContext'
import { MdMenu, MdLightMode, MdDarkMode, MdNotificationsNone } from 'react-icons/md'

const pageTitles = {
  dashboard:   { title: 'Dashboard',         subtitle: 'Welcome back! Ready to ace your next interview?' },
  interview:   { title: 'Virtual Simulator', subtitle: 'Practice with AI-generated questions via camera' },
  chat:        { title: 'AI Chat',           subtitle: 'Chat freely with your AI companion' },
  job_tracker: { title: 'Job Tracker',       subtitle: 'Track your applications and statuses' },
  resume:      { title: 'Resume Builder',    subtitle: 'Build and tailor your ATS-friendly resume' },
  jd_analyzer: { title: 'JD Analyzer',       subtitle: 'Analyze job descriptions for keyword matches' },
  history:     { title: 'History & Chat',    subtitle: 'Review past sessions and conversations' },
  analytics:   { title: 'Analytics',         subtitle: 'Insights into your performance over time' },
  voice:       { title: 'Voice Assistant',   subtitle: 'Talk to your AI coach — hands-free practice' },
  profile:     { title: 'Profile',           subtitle: 'Manage your account and preferences' },
  settings:    { title: 'Settings',          subtitle: 'Configure application settings' },
}

export default function Topbar({ onMenuToggle }) {
  const { activePage, theme, toggleTheme } = useApp()
  const info = pageTitles[activePage] || pageTitles.dashboard

  return (
    <header className="topbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <button className="btn btn-ghost btn-icon" onClick={onMenuToggle} aria-label="Toggle sidebar">
          <MdMenu style={{ fontSize: '1.3rem' }} />
        </button>
        <div className="topbar-left">
          <div className="topbar-title">{info.title}</div>
          <div className="topbar-subtitle">{info.subtitle}</div>
        </div>
      </div>

      <div className="topbar-actions">
        <button
          className="btn btn-ghost btn-icon"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark'
            ? <MdLightMode style={{ fontSize: '1.2rem' }} />
            : <MdDarkMode  style={{ fontSize: '1.2rem' }} />
          }
        </button>
        <button className="btn btn-ghost btn-icon" aria-label="Notifications">
          <MdNotificationsNone style={{ fontSize: '1.2rem' }} />
        </button>
      </div>
    </header>
  )
}
