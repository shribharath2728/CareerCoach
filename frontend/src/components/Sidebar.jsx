import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { MdDashboard, MdWorkHistory, MdChatBubbleOutline, MdPerson, MdSettings, MdLightMode, MdDarkMode, MdLogout, MdMic, MdSchool, MdBarChart, MdClose, MdWork, MdDocumentScanner, MdFindInPage, MdCameraAlt } from 'react-icons/md'

const navItems = [
  { id: 'dashboard',  label: 'Dashboard',         icon: <MdDashboard /> },
  { id: 'interview',  label: 'Virtual Simulator', icon: <MdCameraAlt />,   badge: 'AI' },
  { id: 'chat',       label: 'AI Chat',           icon: <MdChatBubbleOutline /> },
  { id: 'job_tracker',label: 'Job Tracker',       icon: <MdWork /> },
  { id: 'resume',     label: 'Resume Builder',    icon: <MdDocumentScanner /> },
  { id: 'jd_analyzer',label: 'JD Analyzer',       icon: <MdFindInPage /> },
  { id: 'history',    label: 'History & Chat',    icon: <MdWorkHistory /> },
  { id: 'analytics',  label: 'Analytics',         icon: <MdBarChart /> },
  { id: 'voice',      label: 'Voice Assistant',   icon: <MdMic />,         badge: 'NEW' },
]

const bottomItems = [
  { id: 'profile',   label: 'Profile',   icon: <MdPerson /> },
  { id: 'settings',  label: 'Settings',  icon: <MdSettings /> },
]

export default function Sidebar({ mobileOpen, onMobileClose }) {
  const { activePage, setActivePage, theme, toggleTheme, user, logout } = useApp()

  const navigate = (id) => {
    setActivePage(id)
    onMobileClose?.()
  }

  // Close on escape
  useEffect(() => {
    const h = (e) => { if (e.key === 'Escape') onMobileClose?.() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onMobileClose])

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="modal-overlay"
            style={{ zIndex: 99 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onMobileClose}
          />
        )}
      </AnimatePresence>

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="logo-icon">🧠</div>
          <div>
            <div className="logo-text">SkillLens</div>
            <div className="logo-sub">Interview Coach</div>
          </div>
          <button
            className="btn btn-ghost btn-icon"
            style={{ marginLeft: 'auto', display: 'none' }}
            onClick={onMobileClose}
            aria-label="Close sidebar"
          >
            <MdClose />
          </button>
        </div>

        {/* User chip */}
        {user && (
          <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--accent), var(--accent-light))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'white', fontWeight: 700, fontSize: '0.9rem', flexShrink: 0,
              }}>
                {user.full_name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user.full_name}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{user.email}</div>
              </div>
            </div>
          </div>
        )}

        {/* Nav */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">Main</div>
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => navigate(item.id)}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          ))}

          <div className="nav-section-label" style={{ marginTop: 8 }}>Account</div>
          {bottomItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => navigate(item.id)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <button className="nav-item" onClick={toggleTheme}>
            {theme === 'dark' ? <MdLightMode /> : <MdDarkMode />}
            <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
          {user && (
            <button className="nav-item" onClick={logout} style={{ color: 'var(--danger)' }}>
              <MdLogout />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </aside>
    </>
  )
}
