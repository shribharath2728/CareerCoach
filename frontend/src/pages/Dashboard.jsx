import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import {
  MdSchool, MdBarChart, MdTrendingUp, MdStar, MdFlashOn,
  MdLocalFireDepartment, MdAutoGraph, MdRoute,
  MdPlayCircleFilled, MdDocumentScanner,
  MdPsychology, MdArrowForward, MdWifiTethering
} from 'react-icons/md'

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 28 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] },
})

const COACHING_LABELS = {
  strict: { icon: '🎯', label: 'Strict Corporate', color: 'var(--danger)' },
  supportive: { icon: '🤝', label: 'Supportive Mentor', color: 'var(--cyber-green)' },
  academic: { icon: '🎓', label: 'Academic Coach', color: 'var(--cyber-blue)' },
  speed_drill: { icon: '⚡', label: 'Speed Drill', color: 'var(--warning)' },
}

// Thin animated border that traces the card edge
function NeonBorderCard({ children, style, glowColor = 'var(--cyber-cyan)', ...props }) {
  return (
    <motion.div
      {...props}
      style={{
        position: 'relative',
        background: 'rgba(6, 10, 22, 0.85)',
        border: '1px solid rgba(0,245,255,0.15)',
        borderRadius: 'var(--radius)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        overflow: 'hidden',
        ...style,
      }}
    >
      {/* top-left bracket */}
      <span style={{
        position: 'absolute', top: 8, left: 8,
        width: 16, height: 16,
        borderTop: `2px solid ${glowColor}`,
        borderLeft: `2px solid ${glowColor}`,
        opacity: 0.7, pointerEvents: 'none',
      }} />
      {/* bottom-right bracket */}
      <span style={{
        position: 'absolute', bottom: 8, right: 8,
        width: 16, height: 16,
        borderBottom: `2px solid ${glowColor}`,
        borderRight: `2px solid ${glowColor}`,
        opacity: 0.7, pointerEvents: 'none',
      }} />
      {children}
    </motion.div>
  )
}

export default function Dashboard() {
  const { user, setActivePage } = useApp()
  const [data, setData] = useState({
    total_interviews: 0, average_score: 0,
    best_score: 0, total_questions_answered: 0, streak_count: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    import('../services/api').then(({ getAnalytics }) => {
      getAnalytics(user.id)
        .then(res => setData(res))
        .catch(console.error)
        .finally(() => setLoading(false))
    })
  }, [user.id])

  const coachStyle = COACHING_LABELS[user?.coaching_style] || COACHING_LABELS.supportive
  const streak = data.streak_count || 0

  const stats = [
    { icon: <MdSchool />, label: 'Interviews', value: data.total_interviews || 0, color: 'purple', glow: 'rgba(0,245,255,0.25)' },
    { icon: <MdBarChart />, label: 'Avg. Score', value: `${Math.round(data.average_score || 0)}%`, color: 'green', glow: 'rgba(0,255,136,0.25)' },
    { icon: <MdStar />, label: 'Best Score', value: `${Math.round(data.best_score || 0)}%`, color: 'orange', glow: 'rgba(249,115,22,0.25)' },
    { icon: <MdFlashOn />, label: 'Q&A Answered', value: data.total_questions_answered || 0, color: 'blue', glow: 'rgba(14,165,233,0.25)' },
    { icon: <MdLocalFireDepartment />, label: 'Day Streak', value: streak, color: 'red', glow: 'rgba(239,68,68,0.25)' },
  ]

  const quickActions = [
    {
      id: 'chat', label: 'AI Agent Chat', icon: '🧠',
      desc: 'Reasoning agent · skill gap detection · career planning',
      accent: 'var(--cyber-cyan)', borderColor: 'rgba(0,245,255,0.3)',
      tag: 'AGENT',
    },
    {
      id: 'career_dashboard', label: 'Career Dashboard', icon: '📊',
      desc: 'Radar chart · match score · skill gap analysis',
      accent: 'var(--cyber-violet)', borderColor: 'rgba(124,58,237,0.3)',
      tag: 'ANALYTICS',
    },
    {
      id: 'roadmap', label: 'Career Roadmap', icon: '🗺️',
      desc: '30 / 90 / 180-day personalized learning paths',
      accent: 'var(--cyber-blue)', borderColor: 'rgba(14,165,233,0.3)',
      tag: 'PLAN',
    },
    {
      id: 'simulation', label: 'Career Simulator', icon: '🚀',
      desc: 'Simulate study hours · predict salary & roles',
      accent: 'var(--cyber-magenta)', borderColor: 'rgba(232,121,249,0.3)',
      tag: 'SIM',
    },
    {
      id: 'resume_analyzer', label: 'ATS Resume Analyzer', icon: '📄',
      desc: 'ATS score · keyword gaps · improvement tips',
      accent: 'var(--cyber-green)', borderColor: 'rgba(0,255,136,0.3)',
      tag: 'SCAN',
    },
    {
      id: 'interview', label: 'Mock Interview', icon: '🎤',
      desc: 'AI interviewer · voice mode · instant evaluation',
      accent: 'var(--cyber-orange)', borderColor: 'rgba(249,115,22,0.3)',
      tag: 'LIVE',
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

      {/* ── HUD Welcome Banner ─────────────────────────────── */}
      <motion.div {...fadeUp(0)}>
        <div style={{
          position: 'relative',
          background: 'linear-gradient(135deg, rgba(0,20,40,0.95) 0%, rgba(10,5,30,0.95) 60%, rgba(0,15,35,0.95) 100%)',
          borderRadius: 'var(--radius-lg)',
          padding: '32px 36px',
          overflow: 'hidden',
          border: '1px solid rgba(0,245,255,0.2)',
          boxShadow: '0 0 60px rgba(0,245,255,0.06), 0 20px 60px rgba(0,0,0,0.5)',
        }}>
          {/* Corner brackets */}
          <span style={{ position: 'absolute', top: 10, left: 10, width: 22, height: 22, borderTop: '2px solid var(--cyber-cyan)', borderLeft: '2px solid var(--cyber-cyan)', opacity: 0.7 }} />
          <span style={{ position: 'absolute', top: 10, right: 10, width: 22, height: 22, borderTop: '2px solid var(--cyber-cyan)', borderRight: '2px solid var(--cyber-cyan)', opacity: 0.7 }} />
          <span style={{ position: 'absolute', bottom: 10, left: 10, width: 22, height: 22, borderBottom: '2px solid var(--cyber-cyan)', borderLeft: '2px solid var(--cyber-cyan)', opacity: 0.7 }} />
          <span style={{ position: 'absolute', bottom: 10, right: 10, width: 22, height: 22, borderBottom: '2px solid var(--cyber-cyan)', borderRight: '2px solid var(--cyber-cyan)', opacity: 0.7 }} />

          {/* Neon grid overlay inside banner */}
          <div style={{
            position: 'absolute', inset: 0,
            backgroundImage: 'linear-gradient(rgba(0,245,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,245,255,0.03) 1px,transparent 1px)',
            backgroundSize: '32px 32px',
            borderRadius: 'var(--radius-lg)',
            pointerEvents: 'none',
          }} />

          {/* Glowing orb */}
          <div style={{
            position: 'absolute', right: -60, top: -60,
            width: 280, height: 280,
            background: 'radial-gradient(circle,rgba(0,245,255,0.12) 0%,transparent 70%)',
            borderRadius: '50%',
            pointerEvents: 'none',
          }} />
          <div style={{
            position: 'absolute', left: '40%', bottom: -80,
            width: 240, height: 240,
            background: 'radial-gradient(circle,rgba(124,58,237,0.1) 0%,transparent 70%)',
            borderRadius: '50%',
            pointerEvents: 'none',
          }} />

          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
            <div>
              {/* System label */}
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                background: 'rgba(0,245,255,0.08)',
                border: '1px solid rgba(0,245,255,0.2)',
                borderRadius: 99, padding: '3px 12px',
                fontFamily: 'Exo 2, sans-serif', fontSize: '0.62rem', fontWeight: 700,
                color: 'var(--cyber-cyan)', letterSpacing: '0.18em', textTransform: 'uppercase',
                marginBottom: 12,
              }}>
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--cyber-green)', boxShadow: '0 0 6px rgba(0,255,136,0.8)', animation: 'status-pulse 2s ease-in-out infinite' }} />
                Neural System · Online
              </div>

              <div style={{
                fontFamily: 'Orbitron,sans-serif',
                fontSize: 'clamp(1.3rem,3vw,1.8rem)',
                fontWeight: 900,
                letterSpacing: '0.04em',
                background: 'linear-gradient(135deg,var(--cyber-cyan),var(--cyber-violet))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                marginBottom: 8,
                lineHeight: 1.2,
              }}>
                WELCOME BACK, {(user?.full_name?.split(' ')[0] || 'AGENT').toUpperCase()}
              </div>

              <div style={{
                fontFamily: 'Exo 2,sans-serif',
                fontSize: '0.88rem',
                color: 'rgba(0,245,255,0.65)',
                maxWidth: 440,
                lineHeight: 1.7,
                letterSpacing: '0.02em',
              }}>
                Coach <span style={{ color: 'var(--cyber-cyan)', fontWeight: 700 }}>{user?.ai_name || 'Nova'}</span>
                {' '}·{' '}
                <span style={{ color: coachStyle.color }}>{coachStyle.icon} {coachStyle.label}</span>
                {' '}— ready to accelerate your career.
              </div>

              {streak > 0 && (
                <div style={{
                  marginTop: 14, display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: 'linear-gradient(135deg,rgba(249,115,22,0.15),rgba(239,68,68,0.1))',
                  border: '1px solid rgba(249,115,22,0.35)',
                  padding: '5px 14px', borderRadius: 99,
                  fontFamily: 'Exo 2,sans-serif', fontSize: '0.78rem', fontWeight: 700,
                  color: 'var(--cyber-orange)', letterSpacing: '0.06em',
                }}>
                  🔥 {streak}-DAY STREAK — KEEP IT UP
                </div>
              )}
            </div>

            <motion.button
              className="btn btn-primary"
              onClick={() => setActivePage('interview')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.97 }}
              style={{ flexShrink: 0, fontFamily: 'Orbitron,sans-serif', letterSpacing: '0.08em', fontSize: '0.78rem' }}
            >
              <MdPlayCircleFilled /> LAUNCH INTERVIEW
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* ── Stats HUD Row ───────────────────────────────────── */}
      <motion.div {...fadeUp(0.08)} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 14 }}>
        {stats.map((s, i) => (
          <motion.div
            key={i}
            whileHover={{ y: -4, scale: 1.03 }}
            style={{
              position: 'relative',
              background: 'rgba(6,10,22,0.9)',
              border: '1px solid rgba(0,245,255,0.12)',
              borderRadius: 'var(--radius)',
              padding: '18px 16px',
              display: 'flex', alignItems: 'center', gap: 12,
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              overflow: 'hidden',
              cursor: 'default',
              transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
              boxShadow: `0 0 0 0 ${s.glow}`,
            }}
            whileHover_boxShadow={`0 0 30px ${s.glow}`}
          >
            {/* Glow sweep on hover */}
            <div style={{
              position: 'absolute', inset: 0,
              background: `radial-gradient(circle at 30% 50%, ${s.glow} 0%, transparent 65%)`,
              opacity: 0.5, pointerEvents: 'none',
            }} />

            {/* corner bracket top-left */}
            <span style={{ position: 'absolute', top: 5, left: 5, width: 10, height: 10, borderTop: `1.5px solid ${s.glow.replace('0.25', '0.7')}`, borderLeft: `1.5px solid ${s.glow.replace('0.25', '0.7')}`, pointerEvents: 'none' }} />

            <div className={`stat-icon ${s.color}`} style={{ position: 'relative', zIndex: 1 }}>
              {s.icon}
            </div>
            <div className="stat-info" style={{ position: 'relative', zIndex: 1 }}>
              <div className="stat-value">{loading ? '—' : s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Quick Actions Grid ──────────────────────────────── */}
      <motion.div {...fadeUp(0.16)}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
        }}>
          <div style={{
            fontFamily: 'Orbitron,sans-serif', fontSize: '0.72rem', fontWeight: 700,
            color: 'var(--cyber-cyan)', letterSpacing: '0.22em', textTransform: 'uppercase',
            opacity: 0.7,
          }}>
            ◈ MISSION MODULES
          </div>
          <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg,rgba(0,245,255,0.3),transparent)' }} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 14 }}>
          {quickActions.map((a, i) => (
            <motion.button
              key={a.id}
              onClick={() => setActivePage(a.id)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.18 + i * 0.06 }}
              whileHover={{ y: -4, scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              style={{
                position: 'relative',
                background: 'rgba(6,10,22,0.88)',
                border: `1px solid ${a.borderColor}`,
                borderRadius: 'var(--radius)',
                padding: '22px 20px',
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex', flexDirection: 'column', gap: 10,
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                overflow: 'hidden',
                transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
                outline: 'none',
              }}
            >
              {/* Glow orb behind icon */}
              <div style={{
                position: 'absolute', top: -20, left: -20,
                width: 100, height: 100,
                background: `radial-gradient(circle,${a.borderColor} 0%,transparent 70%)`,
                opacity: 0.6, pointerEvents: 'none',
              }} />

              {/* Corner brackets */}
              <span style={{ position: 'absolute', top: 7, left: 7, width: 12, height: 12, borderTop: `1.5px solid ${a.accent}`, borderLeft: `1.5px solid ${a.accent}`, opacity: 0.6, pointerEvents: 'none' }} />
              <span style={{ position: 'absolute', bottom: 7, right: 7, width: 12, height: 12, borderBottom: `1.5px solid ${a.accent}`, borderRight: `1.5px solid ${a.accent}`, opacity: 0.6, pointerEvents: 'none' }} />

              {/* Tag badge */}
              <div style={{
                position: 'absolute', top: 12, right: 12,
                fontFamily: 'Exo 2,sans-serif', fontSize: '0.52rem', fontWeight: 800,
                color: '#000', letterSpacing: '0.12em',
                background: `linear-gradient(135deg,${a.accent},rgba(0,0,0,0.3))`,
                padding: '2px 7px', borderRadius: 99,
                boxShadow: `0 0 8px ${a.borderColor}`,
              }}>
                {a.tag}
              </div>

              {/* Icon */}
              <div style={{
                fontSize: '2rem',
                position: 'relative', zIndex: 1,
                filter: `drop-shadow(0 0 8px ${a.borderColor})`,
              }}>
                {a.icon}
              </div>

              {/* Text */}
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{
                  fontFamily: 'Exo 2,sans-serif', fontWeight: 700, fontSize: '0.9rem',
                  color: a.accent, letterSpacing: '0.04em', marginBottom: 5,
                }}>
                  {a.label}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'rgba(140,170,190,0.85)', lineHeight: 1.5 }}>
                  {a.desc}
                </div>
              </div>

              {/* CTA arrow */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontFamily: 'Exo 2,sans-serif', fontSize: '0.72rem', fontWeight: 700,
                color: a.accent, letterSpacing: '0.06em',
                position: 'relative', zIndex: 1,
              }}>
                <MdArrowForward /> ACCESS MODULE
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ── System Tips Panel ──────────────────────────────── */}
      <motion.div {...fadeUp(0.32)}>
        <div style={{
          position: 'relative',
          background: 'rgba(6,10,22,0.88)',
          border: '1px solid rgba(0,245,255,0.14)',
          borderLeft: '3px solid var(--cyber-cyan)',
          borderRadius: 'var(--radius)',
          padding: '22px 24px',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          overflow: 'hidden',
        }}>
          {/* Glow behind the left stripe */}
          <div style={{
            position: 'absolute', left: 0, top: 0, bottom: 0, width: 60,
            background: 'linear-gradient(90deg,rgba(0,245,255,0.06),transparent)',
            pointerEvents: 'none',
          }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <MdWifiTethering style={{ color: 'var(--cyber-cyan)', fontSize: '1.2rem' }} />
            <span style={{
              fontFamily: 'Orbitron,sans-serif', fontSize: '0.72rem', fontWeight: 700,
              color: 'var(--cyber-cyan)', letterSpacing: '0.18em', textTransform: 'uppercase',
            }}>
              TACTICAL TIPS
            </span>
          </div>

          <ul style={{ paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: 8, listStyle: 'none' }}>
            {[
              'Use the STAR method: Situation → Task → Action → Result for behavioral questions.',
              'Enable Voice Mode to practice speaking aloud — critical for reducing interview nerves.',
              'Switch on Timed Mode to simulate real interview pressure and improve response speed.',
              'Adjust your Coach Personality in Settings to match your learning style.',
              'Check your Skill Radar in Analytics to identify and target your weakest dimensions.',
            ].map((tip, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <span style={{
                  fontFamily: 'Orbitron,sans-serif', fontSize: '0.6rem', fontWeight: 700,
                  color: 'var(--cyber-cyan)', opacity: 0.6, marginTop: 3, flexShrink: 0,
                  letterSpacing: '0.1em',
                }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.65 }}>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      </motion.div>

    </div>
  )
}
