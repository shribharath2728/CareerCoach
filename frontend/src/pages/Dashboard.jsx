import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'

import { MdSchool, MdBarChart, MdChatBubbleOutline, MdTrendingUp, MdStar, MdFlashOn } from 'react-icons/md'

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, delay, ease: [0.4, 0, 0.2, 1] },
})

export default function Dashboard() {
  const { user, setActivePage } = useApp()
  const [data, setData] = useState({ total_interviews: 0, average_score: 0, best_score: 0, total_questions_answered: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    import('../services/api').then(({ getAnalytics }) => {
      getAnalytics(user.id)
        .then(res => setData(res))
        .catch(console.error)
        .finally(() => setLoading(false))
    })
  }, [user.id])

  const stats = [
    { icon: <MdSchool />,    label: 'Interviews Done',    value: data.total_interviews || 0, color: 'purple' },
    { icon: <MdBarChart />,  label: 'Avg. Score',         value: `${Math.round(data.average_score || 0)}%`, color: 'green'  },
    { icon: <MdStar />,      label: 'Best Score',         value: `${Math.round(data.best_score || 0)}%`, color: 'orange' },
    { icon: <MdFlashOn />,     label: 'Questions Answered', value: data.total_questions_answered || 0, color: 'blue'   },
  ]


  const quickActions = [
    { id: 'interview', label: 'Start Mock Interview', desc: 'AI-powered questions with instant feedback', icon: '🎯', color: 'var(--accent)' },
    { id: 'chat',      label: 'Chat with AI Coach',   desc: 'Ask career advice, get tips and guidance',   icon: '💬', color: 'var(--success)' },
    { id: 'voice',     label: 'Voice Practice Mode',  desc: 'Practice speaking answers hands-free',        icon: '🎤', color: 'var(--warning)' },
    { id: 'history',   label: 'Review History',       desc: 'See your past sessions and improvements',    icon: '📊', color: 'var(--info)'    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Welcome banner */}
      <motion.div {...fadeUp(0)}>
        <div style={{
          background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 50%, #2d1b9e 100%)',
          borderRadius: 'var(--radius-lg)',
          padding: '28px 32px',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <div style={{ position: 'absolute', right: 24, top: -20, fontSize: '8rem', opacity: 0.07 }}>🧠</div>
          <div>
            <div style={{ fontFamily: 'Outfit', fontSize: '1.5rem', fontWeight: 800, marginBottom: 6 }}>
              Hey, {user?.full_name?.split(' ')[0] || 'there'} 👋
            </div>
            <div style={{ opacity: 0.85, fontSize: '0.9rem', maxWidth: 420, lineHeight: 1.6 }}>
              Your AI coach <strong>{user?.ai_name || 'Nova'}</strong> is ready. Jump into a mock interview or chat for career advice.
            </div>
          </div>
          <button
            className="btn"
            style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.35)', flexShrink: 0 }}
            onClick={() => setActivePage('interview')}
          >
            <MdSchool /> Start Interview
          </button>
        </div>
      </motion.div>

      {/* Stats row */}
      <motion.div {...fadeUp(0.08)} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
        {stats.map((s, i) => (
          <div key={i} className="stat-card">
            <div className={`stat-icon ${s.color}`}>{s.icon}</div>
            <div className="stat-info">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Quick actions */}
      <motion.div {...fadeUp(0.16)}>
        <h2 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: 14 }}>Quick Actions</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14 }}>
          {quickActions.map(a => (
            <motion.button
              key={a.id}
              onClick={() => setActivePage(a.id)}
              className="card"
              style={{
                cursor: 'pointer', textAlign: 'left', display: 'flex', flexDirection: 'column',
                gap: 10, border: 'none', background: 'var(--bg-card)',
              }}
              whileHover={{ scale: 1.02, y: -3 }}
              whileTap={{ scale: 0.98 }}
            >
              <div style={{ fontSize: '2rem' }}>{a.icon}</div>
              <div>
                <div style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '0.95rem', color: a.color }}>
                  {a.label}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 3 }}>
                  {a.desc}
                </div>
              </div>
              <div style={{ color: a.color, fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                <MdTrendingUp /> Get Started →
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Tips */}
      <motion.div {...fadeUp(0.24)} className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <span style={{ fontSize: '1.2rem' }}>💡</span>
          <span style={{ fontWeight: 700, fontFamily: 'Outfit' }}>Pro Tips</span>
        </div>
        <ul style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[
            'Use STAR method: Situation, Task, Action, Result for behavioral questions.',
            'Enable Voice Mode to practice speaking out loud — great for nerves!',
            'Review your evaluation feedback carefully to identify growth areas.',
            'Try different difficulty levels and interview types to broaden your prep.',
          ].map((tip, i) => (
            <li key={i} style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{tip}</li>
          ))}
        </ul>
      </motion.div>
    </div>
  )
}
