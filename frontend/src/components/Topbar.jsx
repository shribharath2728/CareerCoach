import { useApp } from '../context/AppContext'
import { MdMenu } from 'react-icons/md'

const pageTitles = {
  dashboard: { title: 'DASHBOARD', subtitle: 'Command Center · Career Overview' },
  interview: { title: 'MOCK INTERVIEW', subtitle: 'AI-Powered Interview Simulation' },
  chat: { title: 'AI AGENT CHAT', subtitle: 'Neural Reasoning · Skill Gap Detection' },
  job_tracker: { title: 'JOB TRACKER', subtitle: 'Application Pipeline Management' },
  resume: { title: 'RESUME BUILDER', subtitle: 'ATS-Optimized Resume Construction' },
  jd_analyzer: { title: 'JD ANALYZER', subtitle: 'Job Description Intelligence Scan' },
  history: { title: 'SESSION HISTORY', subtitle: 'Past Sessions · Conversation Logs' },
  analytics: { title: 'ANALYTICS', subtitle: 'Performance Insights · Skill Radar' },
  opportunities: { title: 'OPPORTUNITIES', subtitle: 'Curated Jobs · Learning Paths' },
  profile: { title: 'PROFILE', subtitle: 'Identity · Account Management' },
  settings: { title: 'SETTINGS', subtitle: 'System Configuration' },
  career_dashboard: { title: 'CAREER DASHBOARD', subtitle: 'Radar · Match Score · Skill Gaps' },
  simulation: { title: 'CAREER SIMULATOR', subtitle: 'Roadmap · Salary Projection' },
  resume_analyzer: { title: 'RESUME ANALYZER', subtitle: 'ATS Score · Keyword Intelligence' },
}

export default function Topbar({ onMenuToggle }) {
  const { activePage, user } = useApp()
  const info = pageTitles[activePage] || pageTitles.dashboard

  const initials = user?.full_name
    ? user.full_name.split(' ').filter(Boolean).slice(0, 2).map(n => n[0].toUpperCase()).join('')
    : 'U'

  return (
    <header className="topbar" role="banner" style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Subtle scan line at bottom of topbar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: '1px',
        background: 'linear-gradient(90deg,transparent 0%,var(--cyber-cyan) 30%,var(--cyber-violet) 70%,transparent 100%)',
        opacity: 0.3,
      }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <button
          className="btn btn-ghost btn-icon"
          onClick={onMenuToggle}
          aria-label="Toggle sidebar"
          style={{ color: 'var(--cyber-cyan)', border: '1px solid var(--holo-border)' }}
        >
          <MdMenu style={{ fontSize: '1.2rem' }} />
        </button>

        <div>
          <div className="topbar-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Blinking cursor accent */}
            <span style={{
              width: 3, height: 14,
              background: 'var(--cyber-cyan)',
              boxShadow: '0 0 6px rgba(0,245,255,0.8)',
              borderRadius: 2,
              display: 'inline-block',
              animation: 'neon-flicker 3s ease-in-out infinite',
              verticalAlign: 'middle',
            }} />
            {info.title}
          </div>
          <div className="topbar-subtitle">{info.subtitle}</div>
        </div>
      </div>

      <div className="topbar-actions">
        {/* Avatar chip */}
        {user && (
          <div className="avatar-chip">
            <div className="avatar-circle">{initials}</div>
            <div>
              <span className="avatar-name">{user.full_name}</span>
              <div style={{
                fontSize: '0.58rem', fontFamily: 'Exo 2,sans-serif',
                color: 'var(--cyber-green)', letterSpacing: '0.1em',
                display: 'flex', alignItems: 'center', gap: 4,
              }}>
                <span style={{
                  width: 5, height: 5, borderRadius: '50%',
                  background: 'var(--cyber-green)',
                  boxShadow: '0 0 5px rgba(0,255,136,0.8)',
                  display: 'inline-block',
                }} />
                ONLINE
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
