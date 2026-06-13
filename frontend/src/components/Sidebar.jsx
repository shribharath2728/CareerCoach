import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import {
  MdDashboard, MdChatBubbleOutline, MdPerson, MdSettings,
  MdLogout, MdSchool, MdBarChart,
  MdClose, MdDocumentScanner, MdCameraAlt, MdRoute,
  MdPsychology, MdAutoGraph, MdSignalCellularAlt
} from 'react-icons/md'

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: <MdDashboard /> },
  { id: 'chat', label: 'AI Agent Chat', icon: <MdPsychology />, badge: 'AGENT' },
  { id: 'career_dashboard', label: 'Career Dashboard', icon: <MdAutoGraph /> },
  { id: 'simulation', label: 'Simulation & Roadmap', icon: <MdRoute /> },
  { id: 'resume_analyzer', label: 'Resume Analyzer', icon: <MdDocumentScanner /> },
  { id: 'interview', label: 'Mock Interview', icon: <MdCameraAlt />, badge: 'AI' },
  { id: 'analytics', label: 'Analytics', icon: <MdBarChart /> },
]

const bottomItems = [
  { id: 'profile', label: 'Profile', icon: <MdPerson /> },
  { id: 'settings', label: 'Settings', icon: <MdSettings /> },
]

export default function Sidebar({ mobileOpen, onMobileClose }) {
  const { activePage, setActivePage, user, logout } = useApp()

  const navigate = (id) => {
    setActivePage(id)
    onMobileClose?.()
  }

  useEffect(() => {
    const h = (e) => { if (e.key === 'Escape') onMobileClose?.() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onMobileClose])

  const initials = user?.full_name
    ? user.full_name.split(' ').filter(Boolean).slice(0, 2).map(n => n[0].toUpperCase()).join('')
    : 'U'

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)', zIndex: 99 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onMobileClose}
          />
        )}
      </AnimatePresence>

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`} aria-label="Main navigation">

        {/* ── Logo ──────────────────────────────────── */}
        <div className="sidebar-logo" style={{ position: 'relative' }}>
          {/* Scan line accent below logo */}
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0, height: '1px',
            background: 'linear-gradient(90deg,transparent,var(--cyber-cyan),transparent)',
            opacity: 0.4,
          }} />

          <div className="logo-icon" style={{ fontSize: '1.1rem' }}>🧠</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="logo-text">CareerCoach</div>
            <div className="logo-sub">AI · Reasoning Agent</div>
          </div>
          <button
            className="btn btn-ghost btn-icon"
            onClick={onMobileClose}
            aria-label="Close sidebar"
            style={{ display: 'none' }}
          >
            <MdClose />
          </button>
        </div>

        {/* ── User Chip ─────────────────────────────── */}
        {user && (
          <div style={{
            padding: '12px 14px',
            borderBottom: '1px solid var(--holo-border)',
            background: 'rgba(0,245,255,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                background: 'linear-gradient(135deg,rgba(0,245,255,0.2),rgba(124,58,237,0.3))',
                border: '1px solid rgba(0,245,255,0.4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: 'Orbitron,sans-serif', fontSize: '0.6rem', fontWeight: 700,
                color: 'var(--cyber-cyan)',
                boxShadow: '0 0 10px rgba(0,245,255,0.2)',
              }}>
                {initials}
              </div>
              <div style={{ overflow: 'hidden', minWidth: 0, flex: 1 }}>
                <div style={{
                  fontSize: '0.78rem', fontWeight: 600,
                  color: 'var(--text-primary)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  fontFamily: 'Exo 2,sans-serif',
                }}>
                  {user.full_name}
                </div>
                <div style={{
                  fontSize: '0.6rem',
                  color: 'rgba(0,245,255,0.4)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  fontFamily: 'Exo 2,sans-serif', letterSpacing: '0.04em',
                }}>
                  {user.email}
                </div>
              </div>
              {/* Online status dot */}
              <div style={{
                width: 7, height: 7, borderRadius: '50%',
                background: 'var(--cyber-green)',
                boxShadow: '0 0 6px rgba(0,255,136,0.8)',
                flexShrink: 0,
                animation: 'status-pulse 2s ease-in-out infinite',
              }} />
            </div>
          </div>
        )}

        {/* ── Nav ───────────────────────────────────── */}
        <nav className="sidebar-nav" aria-label="App navigation">
          <div className="nav-section-label">◈ NAVIGATION</div>

          {navItems.map(item => (
            <motion.button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => navigate(item.id)}
              aria-label={item.label}
              aria-current={activePage === item.id ? 'page' : undefined}
              whileHover={{ x: 2 }}
              transition={{ duration: 0.15 }}
            >
              {/* Active glow strip */}
              {activePage === item.id && (
                <motion.div
                  layoutId="activeNavGlow"
                  style={{
                    position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
                    background: 'var(--cyber-cyan)',
                    boxShadow: '0 0 10px rgba(0,245,255,0.8)',
                    borderRadius: '0 2px 2px 0',
                  }}
                />
              )}
              {item.icon}
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </motion.button>
          ))}

          <div className="nav-section-label" style={{ marginTop: 8 }}>◈ ACCOUNT</div>

          {bottomItems.map(item => (
            <motion.button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => navigate(item.id)}
              aria-label={item.label}
              aria-current={activePage === item.id ? 'page' : undefined}
              whileHover={{ x: 2 }}
              transition={{ duration: 0.15 }}
            >
              {activePage === item.id && (
                <motion.div
                  layoutId="activeNavGlow"
                  style={{
                    position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
                    background: 'var(--cyber-cyan)',
                    boxShadow: '0 0 10px rgba(0,245,255,0.8)',
                    borderRadius: '0 2px 2px 0',
                  }}
                />
              )}
              {item.icon}
              <span>{item.label}</span>
            </motion.button>
          ))}
        </nav>

        {/* ── Footer ────────────────────────────────── */}
        <div className="sidebar-footer">
          {/* System status indicator */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '6px 12px', marginBottom: 4,
            fontFamily: 'Exo 2,sans-serif', fontSize: '0.6rem', fontWeight: 700,
            color: 'rgba(0,245,255,0.4)', letterSpacing: '0.1em', textTransform: 'uppercase',
          }}>
            <MdSignalCellularAlt style={{ color: 'var(--cyber-green)', fontSize: '0.9rem' }} />
            SYSTEM NOMINAL
          </div>

          {user && (
            <button
              className="nav-item"
              onClick={logout}
              style={{ color: 'var(--danger)' }}
              aria-label="Sign out"
            >
              <MdLogout />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </aside>
    </>
  )
}
