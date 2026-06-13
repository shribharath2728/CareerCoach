import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { startInterview, generateQuestion, submitAnswer } from '../services/api'
import { useVoiceInput, speak, stopSpeaking } from '../hooks/useVoice'
import useFaceAnalysis from '../hooks/useFaceAnalysis'
import {
  MdMic, MdMicOff, MdStop, MdArrowForward, MdRefresh,
  MdVolumeUp, MdVolumeOff, MdCheckCircle, MdClose, MdCameraAlt,
  MdTimer, MdDownload, MdFace
} from 'react-icons/md'
import EvaluationPanel from '../components/EvaluationPanel'

const ROLES = ['Software Engineer', 'Frontend Developer', 'Backend Engineer', 'Full Stack Developer',
  'Data Scientist', 'ML Engineer', 'DevOps Engineer', 'Product Manager', 'UX Designer', 'Data Analyst']
const TYPES = ['technical', 'behavioral', 'system_design', 'hr', 'mixed']
const DIFFICULTIES = ['easy', 'medium', 'hard']
const TIMER_OPTIONS = [60, 120, 180, 300] // seconds

// ---------- Setup Form ----------
function SetupForm({ onStart }) {
  const { user } = useApp()
  const [form, setForm] = useState({
    role: user.recent_role || ROLES[0],
    interview_type: 'technical',
    difficulty: 'medium',
    field_of_study: user.field_of_study || '',
    timerEnabled: false,
    timerSeconds: 120,
    voiceAssistantMode: false,
  })
  const [loading, setLoading] = useState(false)
  const { addToast } = useApp()
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleStart = async () => {
    setLoading(true)
    try {
      const session = await startInterview({ 
        user_id: user.id, 
        role: form.role, 
        interview_type: form.interview_type, 
        difficulty: form.difficulty, 
        field_of_study: form.field_of_study 
      })
      onStart(session, form)
    } catch (err) {
      addToast(err.response?.data?.detail || 'Could not start interview', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{ maxWidth: 600, margin: '0 auto', border: '1px solid rgba(99,102,241,0.25)', position: 'relative' }}
    >
      {/* Cyber corners */}
      <div style={{ position: 'absolute', top: 10, left: 10, width: 8, height: 8, borderLeft: '2px solid var(--primary)', borderTop: '2px solid var(--primary)' }} />
      <div style={{ position: 'absolute', top: 10, right: 10, width: 8, height: 8, borderRight: '2px solid var(--primary)', borderTop: '2px solid var(--primary)' }} />

      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{ fontSize: '2.8rem', marginBottom: 10 }}>🎯</div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', textShadow: '0 0 10px rgba(99,102,241,0.3)' }}>Configure Your Practice</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 6 }}>
          Choose your settings or try the voice assistant practice
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div className="form-group">
          <label>Target Job Role</label>
          <input
            placeholder="e.g. Business Analyst, Content Manager, Software Engineer"
            value={form.role}
            onChange={e => set('role', e.target.value)}
          />
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
            {ROLES.slice(0, 5).map(r => (
              <button key={r} className="btn btn-xs btn-ghost" onClick={() => set('role', r)}>{r}</button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Field of Study (Context)</label>
          <input
            placeholder="e.g. Arts, Literature, Commerce"
            value={form.field_of_study}
            onChange={e => set('field_of_study', e.target.value)}
          />
        </div>

        <div className="form-group" style={{ opacity: form.voiceAssistantMode ? 0.5 : 1, pointerEvents: form.voiceAssistantMode ? 'none' : 'auto' }}>
          <label>Interview Type</label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {TYPES.map(t => (
              <button
                key={t}
                className={`btn btn-sm ${form.interview_type === t ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => set('interview_type', t)}
                type="button"
              >
                {t.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Difficulty</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {DIFFICULTIES.map(d => (
              <button
                key={d}
                className={`btn btn-sm ${form.difficulty === d ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => set('difficulty', d)}
                type="button"
                style={{ flex: 1 }}
              >
                {d === 'easy' ? '🌱 Easy' : d === 'medium' ? '⚡ Medium' : '🔥 Hard'}
              </button>
            ))}
          </div>
        </div>

        {/* Voice Assistant / Communication Mode Toggle */}
        <div className="card" style={{ 
          padding: '14px 18px', 
          background: form.voiceAssistantMode ? 'rgba(99,102,241,0.08)' : 'var(--bg-tertiary)', 
          border: `1px solid ${form.voiceAssistantMode ? 'var(--primary)' : 'var(--border)'}`, 
          transition: 'all 0.2s' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: '1.4rem' }}>🎙ï¸</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.88rem', color: form.voiceAssistantMode ? 'var(--primary)' : 'var(--text-primary)' }}>
                  Voice Assistant Mode
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Hands-free practice focused on improving communication skills
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                const nextVal = !form.voiceAssistantMode;
                setForm(f => ({
                  ...f,
                  voiceAssistantMode: nextVal,
                  interview_type: nextVal ? 'communication' : 'technical',
                  timerEnabled: nextVal ? false : f.timerEnabled
                }))
              }}
              style={{
                width: 44, height: 24, borderRadius: 99, border: 'none', cursor: 'pointer',
                background: form.voiceAssistantMode ? 'var(--primary)' : 'var(--border)',
                position: 'relative', transition: 'background 0.25s',
              }}
            >
              <span style={{
                position: 'absolute', top: 3, left: form.voiceAssistantMode ? 22 : 3,
                width: 18, height: 18, borderRadius: 50, background: 'white',
                transition: 'left 0.25s', boxShadow: '0 1px 4px rgba(0,0,0,0.25)',
              }} />
            </button>
          </div>
        </div>

        {/* Timed Mode Toggle (Only if not in Voice Assistant Mode) */}
        {!form.voiceAssistantMode && (
          <div className="card" style={{ padding: '14px 18px', background: form.timerEnabled ? 'rgba(15,118,110,0.08)' : 'var(--bg-tertiary)', border: `1px solid ${form.timerEnabled ? 'var(--accent)' : 'var(--border)'}`, transition: 'all 0.2s' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <MdTimer style={{ color: form.timerEnabled ? 'var(--accent)' : 'var(--text-muted)', fontSize: '1.3rem' }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: form.timerEnabled ? 'var(--accent)' : 'var(--text-primary)' }}>⏱️ Timed Interview Mode</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Real pressure — auto-submit when time runs out</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => set('timerEnabled', !form.timerEnabled)}
                style={{
                  width: 44, height: 24, borderRadius: 99, border: 'none', cursor: 'pointer',
                  background: form.timerEnabled ? 'var(--accent)' : 'var(--border)',
                  position: 'relative', transition: 'background 0.25s',
                }}
              >
                <span style={{
                  position: 'absolute', top: 3, left: form.timerEnabled ? 22 : 3,
                  width: 18, height: 18, borderRadius: 50, background: 'white',
                  transition: 'left 0.25s', boxShadow: '0 1px 4px rgba(0,0,0,0.25)',
                }} />
              </button>
            </div>
            {form.timerEnabled && (
              <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                {TIMER_OPTIONS.map(sec => (
                  <button
                    key={sec}
                    type="button"
                    className={`btn btn-sm ${form.timerSeconds === sec ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => set('timerSeconds', sec)}
                    style={{ flex: 1 }}
                  >
                    {sec < 60 ? `${sec}s` : `${sec / 60}m`}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <button
          className="btn btn-primary btn-lg"
          style={{ justifyContent: 'center', marginTop: 8, boxShadow: '0 4px 15px rgba(99,102,241,0.3)' }}
          onClick={handleStart}
          disabled={loading}
        >
          {loading ? <><span className="spinner" />Starting…</> : '🚀 Start Session'}
        </button>
      </div>
    </motion.div>
  )
}

// ---------- Countdown Timer ----------
function CountdownTimer({ totalSeconds, onTimeout }) {
  const [remaining, setRemaining] = useState(totalSeconds)
  const intervalRef = useRef(null)

  useEffect(() => {
    setRemaining(totalSeconds)
    intervalRef.current = setInterval(() => {
      setRemaining(prev => {
        if (prev <= 1) {
          clearInterval(intervalRef.current)
          onTimeout()
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(intervalRef.current)
  }, [totalSeconds, onTimeout])

  const pct = (remaining / totalSeconds) * 100
  const color = pct > 50 ? 'var(--success)' : pct > 20 ? 'var(--warning)' : 'var(--danger)'
  const mm = String(Math.floor(remaining / 60)).padStart(2, '0')
  const ss = String(remaining % 60).padStart(2, '0')

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '6px 14px', borderRadius: 99,
      border: `2px solid ${color}`,
      background: `${color}18`,
      transition: 'all 0.3s',
    }}>
      <MdTimer style={{ color, fontSize: '1.1rem' }} />
      <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: '1.1rem', color }}>{mm}:{ss}</span>
      <div style={{ width: 60, height: 4, borderRadius: 99, background: 'var(--border)', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, transition: 'width 1s linear, background 0.3s' }} />
      </div>
    </div>
  )
}

// ---------- Score Ring ----------
function ScoreRing({ value, label, color, size = 72 }) {
  const radius = (size - 10) / 2
  const circumference = 2 * Math.PI * radius
  const progress = (value / 100) * circumference

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={7}
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth={7}
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.4s' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: size > 60 ? '1.05rem' : '0.85rem',
          color,
        }}>
          {value}
        </div>
      </div>
      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textAlign: 'center' }}>
        {label}
      </span>
    </div>
  )
}

// ---------- Mini Sparkline ----------
function Sparkline({ data, color = 'var(--accent)', width = 220, height = 36 }) {
  if (!data || data.length < 2) return null
  const max = 100
  const min = 0
  const range = max - min || 1
  const step = width / (data.length - 1)

  const points = data.map((v, i) => [
    i * step,
    height - ((v - min) / range) * height
  ])

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')

  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={`${pathD} L${(data.length - 1) * step},${height} L0,${height} Z`}
        fill="url(#sparkGrad)"
      />
      <path d={pathD} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <circle cx={points[points.length - 1][0]} cy={points[points.length - 1][1]} r={3} fill={color} />
    </svg>
  )
}

// ---------- Holographic AI Voice Orb ----------
function AIVoiceOrb({ state }) {
  const stateColors = {
    idle: { color: 'var(--text-muted)', shadow: 'rgba(255,255,255,0.05)', label: 'READY', desc: 'Click "Get First Question" to begin' },
    speaking: { color: '#6366F1', shadow: 'rgba(99,102,241,0.5)', label: 'AI SPEAKING', desc: 'Listen carefully to the question...' },
    listening: { color: '#10B981', shadow: 'rgba(16,185,129,0.5)', label: 'LISTENING', desc: 'Speak your answer clearly' },
    evaluating: { color: '#F59E0B', shadow: 'rgba(245,158,11,0.5)', label: 'PROCESSING', desc: 'Analyzing communication fluency...' }
  }
  
  const current = stateColors[state] || stateColors.idle
  
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '36px 20px', background: 'rgba(11,18,35,0.45)', borderRadius: 16,
      border: '1px solid rgba(255,255,255,0.06)', backdropFilter: 'blur(12px)',
      boxShadow: 'inset 0 0 24px rgba(255,255,255,0.01)', position: 'relative', overflow: 'hidden'
    }}>
      {/* Laser line overlay */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: '100%', height: 1,
        background: `linear-gradient(90deg, transparent, ${current.color}, transparent)`,
        animation: 'scanLinePulse 2.5s infinite linear'
      }} />

      {/* Cyber corner borders */}
      <div style={{ position: 'absolute', top: 8, left: 8, width: 8, height: 8, borderLeft: `2px solid ${current.color}`, borderTop: `2px solid ${current.color}` }} />
      <div style={{ position: 'absolute', top: 8, right: 8, width: 8, height: 8, borderRight: `2px solid ${current.color}`, borderTop: `2px solid ${current.color}` }} />

      {/* Circular Glowing Orb */}
      <div style={{ position: 'relative', width: 140, height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
        {/* Outer Ring */}
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
          style={{
            position: 'absolute', width: 140, height: 140, borderRadius: '50%',
            border: `2px dashed ${current.color}`, opacity: 0.3,
            boxShadow: `0 0 15px ${current.shadow}`
          }}
        />
        {/* Inner Ring */}
        <motion.div 
          animate={{ rotate: -360 }}
          transition={{ duration: 7, repeat: Infinity, ease: 'linear' }}
          style={{
            position: 'absolute', width: 110, height: 110, borderRadius: '50%',
            border: `1px dashed ${current.color}`, opacity: 0.45,
            boxShadow: `0 0 10px ${current.shadow}`
          }}
        />
        {/* Center Pulsing Sphere */}
        <motion.div 
          animate={state === 'speaking' || state === 'listening' ? {
            scale: [1, 1.15, 1],
            opacity: [0.75, 0.95, 0.75]
          } : {
            scale: 1, opacity: 0.8
          }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            width: 76, height: 76, borderRadius: '50%',
            background: `radial-gradient(circle, ${current.color} 0%, rgba(10,10,20,0.85) 100%)`,
            boxShadow: `0 0 25px ${current.color}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 2
          }}
        >
          <span style={{ fontSize: '1.8rem' }}>
            {state === 'speaking' ? '🔊' : state === 'listening' ? '🎙ï¸' : state === 'evaluating' ? '⚙️' : '🧠'}
          </span>
        </motion.div>

        {/* Wave ripples */}
        {state === 'listening' && (
          <div style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none' }}>
            <motion.div animate={{ scale: [1, 2], opacity: [0.4, 0] }} transition={{ duration: 1.8, repeat: Infinity }} style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid var(--success)' }} />
            <motion.div animate={{ scale: [1, 1.5], opacity: [0.4, 0] }} transition={{ duration: 1.8, delay: 0.9, repeat: Infinity }} style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid var(--success)' }} />
          </div>
        )}
      </div>

      <div style={{ zIndex: 10, textAlign: 'center' }}>
        <div style={{ 
          fontFamily: 'var(--font-heading)', fontWeight: 900, fontSize: '0.85rem', 
          letterSpacing: '0.2em', color: current.color, textTransform: 'uppercase', marginBottom: 6
        }}>
          {current.label}
        </div>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {current.desc}
        </div>
      </div>

      <style>{`
        @keyframes scanLinePulse {
          0% { transform: translateY(0); opacity: 0; }
          15% { opacity: 0.8; }
          85% { opacity: 0.8; }
          100% { transform: translateY(220px); opacity: 0; }
        }
      `}</style>
    </div>
  )
}

// ---------- Face Analysis Panel ----------
function FaceAnalysisPanel({ scores, feedback, history }) {
  const getScoreColor = (v) => {
    if (v == null) return 'var(--text-muted)'
    if (v >= 72) return 'var(--success)'
    if (v >= 48) return 'var(--warning)'
    return 'var(--danger)'
  }

  const getLabel = (v) => {
    if (v == null) return '—'
    if (v >= 80) return 'Excellent'
    if (v >= 65) return 'Good'
    if (v >= 48) return 'Fair'
    return 'Needs Work'
  }

  return (
    <div style={{
      marginTop: 14,
      background: 'linear-gradient(135deg, rgba(15,118,110,0.06) 0%, rgba(0,0,0,0.3) 100%)',
      borderRadius: 'var(--radius)',
      border: '1px solid rgba(15,118,110,0.25)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        background: 'rgba(15,118,110,0.12)',
        borderBottom: '1px solid rgba(15,118,110,0.2)',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        <MdFace style={{ color: 'var(--accent)', fontSize: '1.1rem' }} />
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '0.82rem', color: 'var(--accent)' }}>
          AI Face Analysis
        </span>
        <span style={{
          marginLeft: 'auto', fontSize: '0.65rem', padding: '2px 7px',
          borderRadius: 99, background: scores ? 'rgba(15,118,110,0.2)' : 'rgba(255,255,255,0.05)',
          color: scores ? 'var(--accent)' : 'var(--text-muted)',
          fontWeight: 600,
        }}>
          {scores ? '● LIVE' : '○ WARMING UP…'}
        </span>
      </div>

      <div style={{ padding: '14px' }}>
        {!scores ? (
          <div style={{ textAlign: 'center', padding: '16px 0', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
            <div style={{ fontSize: '1.8rem', marginBottom: 6 }}>📷</div>
            Analysing your face…<br />
            <span style={{ fontSize: '0.7rem' }}>Make sure you are visible in the camera</span>
          </div>
        ) : (
          <>
            {/* Score Rings */}
            <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: 14 }}>
              <ScoreRing
                value={scores.confidence}
                label="Confidence"
                color={getScoreColor(scores.confidence)}
              />
              <ScoreRing
                value={scores.clarity}
                label="Clarity"
                color={getScoreColor(scores.clarity)}
              />
            </div>

            {/* Status labels */}
            <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 12 }}>
              <span style={{
                fontSize: '0.65rem', padding: '2px 8px', borderRadius: 99, fontWeight: 700,
                background: `${getScoreColor(scores.confidence)}20`,
                color: getScoreColor(scores.confidence),
              }}>
                {getLabel(scores.confidence)} Confidence
              </span>
              <span style={{
                fontSize: '0.65rem', padding: '2px 8px', borderRadius: 99, fontWeight: 700,
                background: `${getScoreColor(scores.clarity)}20`,
                color: getScoreColor(scores.clarity),
              }}>
                {getLabel(scores.clarity)} Clarity
              </span>
            </div>

            {/* Detailed metrics */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginBottom: 12 }}>
              {[
                { label: 'Gaze Stability', value: scores.gazeScore, icon: '👁️' },
                { label: 'Lighting', value: scores.lightingScore, icon: '💡' },
                { label: 'Composure', value: scores.motionScore, icon: '🧘' },
                { label: 'Face Coverage', value: scores.facePresence, icon: '🎭' },
              ].map(m => (
                <div key={m.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {m.icon} {m.label}
                    </span>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, color: getScoreColor(m.value) }}>
                      {m.value}%
                    </span>
                  </div>
                  <div style={{ height: 4, borderRadius: 99, background: 'rgba(255,255,255,0.07)', overflow: 'hidden' }}>
                    <div style={{
                      width: `${m.value}%`, height: '100%',
                      background: getScoreColor(m.value),
                      borderRadius: 99,
                      transition: 'width 0.8s ease, background 0.4s',
                    }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Sparkline trend */}
            {history.length > 2 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                  📈 Trend (last {history.length} readings)
                </div>
                <div style={{ display: 'flex', gap: 6, flexDirection: 'column' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: '0.6rem', color: 'var(--success)', minWidth: 56 }}>Confidence</span>
                    <Sparkline
                      data={history.map(h => h.confidence)}
                      color="var(--success)"
                      width={160}
                      height={28}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: '0.6rem', color: 'var(--accent)', minWidth: 56 }}>Clarity</span>
                    <Sparkline
                      data={history.map(h => h.clarity)}
                      color="var(--accent)"
                      width={160}
                      height={28}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Live feedback tips */}
            {feedback.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {feedback.map((tip, i) => {
                  const iconMap = { good: '✅', warn: '⚠️', info: 'ℹ️' }
                  const colorMap = {
                    good: 'rgba(16,185,129,0.12)',
                    warn: 'rgba(245,158,11,0.12)',
                    info: 'rgba(99,102,241,0.12)',
                  }
                  const borderMap = {
                    good: 'rgba(16,185,129,0.3)',
                    warn: 'rgba(245,158,11,0.3)',
                    info: 'rgba(99,102,241,0.3)',
                  }
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                      style={{
                        padding: '6px 9px',
                        borderRadius: 'var(--radius-sm)',
                        background: colorMap[tip.type],
                        border: `1px solid ${borderMap[tip.type]}`,
                        fontSize: '0.68rem',
                        color: 'var(--text-secondary)',
                        display: 'flex', alignItems: 'flex-start', gap: 6,
                      }}
                    >
                      <span style={{ flexShrink: 0 }}>{iconMap[tip.type]}</span>
                      <span>{tip.msg}</span>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ---------- PDF Download ----------
async function downloadSessionPDF(sessionData) {
  try {
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const W = doc.internal.pageSize.getWidth()
    let y = 20

    const addLine = (text, opts = {}) => {
      const { size = 11, bold = false, color = [30, 30, 30], indent = 0 } = opts
      doc.setFontSize(size)
      doc.setTextColor(...color)
      if (bold) doc.setFont('helvetica', 'bold')
      else doc.setFont('helvetica', 'normal')
      const lines = doc.splitTextToSize(text, W - 30 - indent)
      if (y + lines.length * (size * 0.4) > 270) { doc.addPage(); y = 20 }
      doc.text(lines, 15 + indent, y)
      y += lines.length * (size * 0.4) + 2
    }

    // Header
    doc.setFillColor(15, 118, 110)
    doc.rect(0, 0, W, 28, 'F')
    doc.setFontSize(18)
    doc.setTextColor(255, 255, 255)
    doc.setFont('helvetica', 'bold')
    doc.text('CareerCoach AI — Interview Session Report', 15, 18)
    y = 36

    addLine(`Role: ${sessionData.config.role}  |  Type: ${sessionData.config.interview_type}  |  Difficulty: ${sessionData.config.difficulty}`, { size: 10, color: [80, 80, 80] })
    addLine(`Date: ${new Date().toLocaleDateString('en-IN', { dateStyle: 'full' })}`, { size: 10, color: [80, 80, 80] })

    // Face Analysis Summary in PDF
    if (sessionData.faceHistory && sessionData.faceHistory.length > 0) {
      const avgConf = Math.round(sessionData.faceHistory.reduce((a, h) => a + h.confidence, 0) / sessionData.faceHistory.length)
      const avgClarity = Math.round(sessionData.faceHistory.reduce((a, h) => a + h.clarity, 0) / sessionData.faceHistory.length)
      addLine(`Face Analysis — Avg Confidence: ${avgConf}%  |  Avg Clarity: ${avgClarity}%`, { size: 10, color: [15, 118, 110] })
    }
    y += 4

    addLine('─'.repeat(90), { size: 8, color: [200, 200, 200] })
    y += 2

    sessionData.history.forEach((item, idx) => {
      addLine(`Q${idx + 1}. ${item.question}`, { size: 11, bold: true, color: [15, 118, 110] })
      y += 1
      addLine(`Your Answer: ${item.answer || '(no answer)'}`, { size: 10, indent: 4 })
      if (item.evaluation) {
        addLine(`Overall Score: ${item.evaluation.overall_score}/100  |  Hiring Signal: ${item.evaluation.hiring_signal || 'N/A'}`, { size: 10, bold: true, color: [50, 100, 150], indent: 4 })
        if (item.evaluation.feedback_summary) {
          addLine(`Feedback: ${item.evaluation.feedback_summary}`, { size: 9, color: [80, 80, 80], indent: 4 })
        }
      }
      y += 5
      if (idx < sessionData.history.length - 1) {
        addLine('─'.repeat(60), { size: 7, color: [220, 220, 220] })
        y += 2
      }
    })

    // Summary
    if (sessionData.history.length > 0) {
      const scored = sessionData.history.filter(h => h.evaluation?.overall_score != null)
      const avgScore = scored.length ? Math.round(scored.reduce((a, h) => a + (h.evaluation.overall_score || 0), 0) / scored.length) : 0
      if (y + 30 > 270) { doc.addPage(); y = 20 }
      y += 4
      doc.setFillColor(240, 253, 250)
      doc.roundedRect(14, y, W - 28, 24, 4, 4, 'F')
      doc.setTextColor(15, 118, 110)
      doc.setFontSize(13)
      doc.setFont('helvetica', 'bold')
      doc.text(`Session Average Score: ${avgScore}/100`, 20, y + 10)
      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(80, 80, 80)
      doc.text(`${sessionData.history.length} question(s) answered  |  Generated by CareerCoach AI`, 20, y + 18)
    }

    doc.save(`CareerCoach_Report_${sessionData.config.role.replace(/\s/g, '_')}_${Date.now()}.pdf`)
  } catch (e) {
    console.error('PDF generation failed', e)
    alert('PDF download failed. Please try again.')
  }
}

// ---------- Interview Session ----------
function InterviewSession({ session, config, onFinish }) {
  const { user, addToast } = useApp()
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [evaluation, setEval] = useState(null)
  const [loadingQ, setLoadingQ] = useState(false)
  const [loadingA, setLoadingA] = useState(false)
  const [qCount, setQCount] = useState(0)
  const [ttsOn, setTtsOn] = useState(true)
  const [sessionHistory, setHistory] = useState([]) // for PDF
  const [timerKey, setTimerKey] = useState(0) // reset timer per question
  const [aiState, setAiState] = useState('idle') // idle | speaking | listening | evaluating
  const textareaRef = useRef(null)

  // Submits the answer
  const handleSubmit = useCallback(async (timedOut = false, directAnswer = null) => {
    const ans = (directAnswer != null ? directAnswer : answer).trim() || (timedOut ? '(Time expired — no answer submitted)' : '')
    if (!ans && !timedOut) { addToast('Please provide an answer', 'error'); return }
    setLoadingA(true)
    if (config.voiceAssistantMode) setAiState('evaluating')
    stopSpeaking()
    try {
      const result = await submitAnswer({ question_id: question.id, answer_text: ans })
      setEval(result.evaluation)
      setHistory(h => [...h, { question: question.question_text, answer: ans, evaluation: result.evaluation }])
      
      if (config.voiceAssistantMode) {
        setAiState('speaking')
        speak(`Score: ${result.evaluation.overall_score} out of 100. ${result.evaluation.feedback_summary || ''}`, {
          voice: user?.ai_voice,
          onEnd: () => {
            setAiState('idle')
          }
        })
      } else if (ttsOn && result.evaluation?.feedback_summary) {
        speak(`Score: ${result.evaluation.overall_score} out of 100. ${result.evaluation.feedback_summary}`, { voice: user?.ai_voice })
      }
      
      if (timedOut) addToast('â° Time up! Answer auto-submitted.', 'warning')
      else addToast('Answer evaluated! 🎉', 'success')
    } catch {
      if (config.voiceAssistantMode) setAiState('idle')
      addToast('Failed to evaluate answer', 'error')
    } finally {
      setLoadingA(false)
    }
  }, [answer, question, ttsOn, config.voiceAssistantMode, user?.ai_voice, addToast])

  // Set up voice recognition hook
  const { isListening, transcript, supported: voiceSupported, toggle: toggleVoice, start: startVoice, stop: stopVoice, setTranscript } = useVoiceInput({
    onResult: (t) => {
      setAnswer(t)
      if (config.voiceAssistantMode) {
        // Auto-submit hands-free!
        handleSubmit(false, t)
      }
    },
    onError: (e) => addToast(`Voice error: ${e}`, 'error'),
  })

  useEffect(() => { if (transcript) setAnswer(transcript) }, [transcript])

  // Camera feed
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [videoActive, setVideoActive] = useState(false)

  // Initialize face analysis hook at parent level
  const { scores, feedback, history: faceHistory } = useFaceAnalysis(videoRef, videoActive && !!question)

  useEffect(() => {
    const startCamera = async () => {
      if (!navigator?.mediaDevices?.getUserMedia) return
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          setVideoActive(true)
        }
      } catch (err) {
        setVideoActive(false)
      }
    }
    startCamera()
    return () => {
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
      setVideoActive(false)
    }
  }, [])

  // Face analysis — capture history snapshot for PDF
  const faceHistoryRef = useRef([])

  useEffect(() => {
    if (scores && videoActive) {
      faceHistoryRef.current.push(scores)
    }
  }, [scores, videoActive])

  const fetchQuestion = async () => {
    setLoadingQ(true)
    setEval(null)
    setAnswer('')
    setTranscript('')
    setTimerKey(k => k + 1)
    if (config.voiceAssistantMode) setAiState('idle')
    try {
      const q = await generateQuestion(session.id)
      setQuestion(q)
      setQCount(c => c + 1)
      
      if (config.voiceAssistantMode) {
        setAiState('speaking')
        speak(q.question_text, {
          voice: user?.ai_voice,
          onEnd: () => {
            setAiState('listening')
            if (voiceSupported) {
              startVoice()
            }
          }
        })
      } else if (ttsOn) {
        speak(q.question_text, { voice: user?.ai_voice })
      }
    } catch {
      addToast('Failed to generate question', 'error')
    } finally {
      setLoadingQ(false)
    }
  }

  const handleTimeout = useCallback(() => {
    if (!evaluation && !loadingA) {
      handleSubmit(true)
    }
  }, [evaluation, loadingA, handleSubmit])

  const handleFinishAndDownload = async () => {
    if (sessionHistory.length > 0) {
      addToast('Preparing your PDF report…', 'info')
      await downloadSessionPDF({
        config,
        history: sessionHistory,
        faceHistory: faceHistoryRef.current,
      })
    }
    onFinish()
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: 20, alignItems: 'start' }}>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Session header */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', flexWrap: 'wrap', gap: 10, border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <span className="badge badge-accent">Session #{session.id}</span>
            <span className="badge badge-info">{config.role}</span>
            <span className="badge badge-warning" style={{ textTransform: 'capitalize' }}>
              {config.voiceAssistantMode ? '🎙ï¸ Voice Assistant' : config.interview_type.replace('_', ' ')}
            </span>
            <span className="badge badge-danger" style={{ textTransform: 'capitalize' }}>{config.difficulty}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Q{qCount} answered</span>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* Countdown Timer */}
            {config.timerEnabled && question && !evaluation && !loadingQ && !loadingA && (
              <CountdownTimer
                key={timerKey}
                totalSeconds={config.timerSeconds}
                onTimeout={handleTimeout}
              />
            )}
            {!config.voiceAssistantMode && (
              <button className="btn btn-ghost btn-icon" onClick={() => setTtsOn(t => !t)} title="Toggle TTS">
                {ttsOn ? <MdVolumeUp /> : <MdVolumeOff />}
              </button>
            )}
            <button className="btn btn-danger btn-sm" onClick={handleFinishAndDownload}>
              <MdClose /> End {sessionHistory.length > 0 ? '& Download PDF' : ''}
            </button>
          </div>
        </div>

        {/* Voice Assistant Orb if in Voice Assistant Mode */}
        {config.voiceAssistantMode && (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
            <AIVoiceOrb state={aiState} />
          </motion.div>
        )}

        {/* Question box */}
        <div className="card" style={{ position: 'relative', border: config.voiceAssistantMode && aiState === 'speaking' ? '1px solid var(--primary)' : '1px solid var(--glass-border)', transition: 'border 0.3s' }}>
          {config.voiceAssistantMode && aiState === 'speaking' && (
            <div style={{ position: 'absolute', top: 8, left: 8, width: 6, height: 6, borderRadius: '50%', background: 'var(--primary)', boxShadow: '0 0 6px var(--primary)', animation: 'pulse 1.5s infinite' }} />
          )}
          
          {!question && !loadingQ && (
            <div className="empty-state" style={{ padding: '30px 0' }}>
              <div className="empty-icon" style={{ fontSize: '3rem', marginBottom: 10 }}>🎯</div>
              <h3>Ready to begin?</h3>
              <p style={{ marginBottom: 18 }}>Click below to get your first AI-generated question.</p>
              <button className="btn btn-primary" onClick={fetchQuestion} style={{ boxShadow: '0 4px 15px rgba(99,102,241,0.3)' }}>
                <MdArrowForward /> Get First Question
              </button>
            </div>
          )}

          {loadingQ && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, padding: '40px 0' }}>
              <div className="ai-thinking"><span /><span /><span /></div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Generating your question…</p>
            </div>
          )}

          {question && !loadingQ && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {question.category && <span className="badge badge-info">{question.category}</span>}
                  {question.difficulty && <span className="badge badge-warning" style={{ textTransform: 'capitalize' }}>{question.difficulty}</span>}
                  {config.timerEnabled && <span className="badge badge-accent">⏱ Timed</span>}
                  {config.voiceAssistantMode && <span className="badge badge-primary">🎙ï¸ Communication Focus</span>}
                </div>
                {!config.voiceAssistantMode && (
                  <button className="btn btn-ghost btn-sm" onClick={() => ttsOn && speak(question.question_text, { voice: user?.ai_voice })}>
                    <MdVolumeUp /> Read
                  </button>
                )}
              </div>
              <p style={{ fontSize: '1.05rem', fontWeight: 600, lineHeight: 1.7, color: 'var(--text-primary)' }}>
                {question.question_text}
              </p>
              {question.expected_answer_points?.length > 0 && (
                <details style={{ marginTop: 14 }}>
                  <summary style={{ fontSize: '0.8rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                    💡 Hint — Expected concepts (expand after answering)
                  </summary>
                  <ul style={{ marginTop: 8, paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {question.expected_answer_points.map((p, i) => (
                      <li key={i} style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{p}</li>
                    ))}
                  </ul>
                </details>
              )}
            </motion.div>
          )}
        </div>

        {/* Answer box */}
        {question && !loadingQ && !evaluation && (
          <motion.div className="card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} style={{ border: aiState === 'listening' ? '1px solid var(--success)' : '1px solid var(--glass-border)', transition: 'border 0.3s' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                {config.voiceAssistantMode ? '🎙ï¸ Spoken Transcript' : 'Your Answer'}
              </label>
              {voiceSupported && (
                <button
                  className={`mic-btn ${isListening ? 'recording' : 'idle'}`}
                  onClick={toggleVoice}
                  title={isListening ? 'Stop recording' : 'Speak your answer'}
                  style={{
                    background: isListening ? 'var(--danger)' : 'var(--primary)',
                    boxShadow: isListening ? '0 0 10px rgba(239,68,68,0.4)' : 'none'
                  }}
                >
                  {isListening ? <MdMicOff /> : <MdMic />}
                </button>
              )}
            </div>

            {isListening && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, padding: '8px 12px', background: 'rgba(16,185,129,0.1)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16,185,129,0.25)' }}>
                <div className="waveform">
                  {Array(8).fill(0).map((_, i) => <div key={i} className="waveform-bar" style={{ background: 'var(--success)', height: 12, width: 3, margin: '0 2px', borderRadius: 99, display: 'inline-block', animation: 'wave 1s infinite alternate' }} />)}
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--success)' }}>Listening… speak clearly</span>
              </div>
            )}

            <textarea
              ref={textareaRef}
              placeholder={config.voiceAssistantMode ? "Transcribing voice input automatically..." : "Type your answer here, or use the microphone to speak…"}
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              style={{ minHeight: 120, width: '100%' }}
              disabled={loadingA}
            />

            {!config.voiceAssistantMode && (
              <div style={{ display: 'flex', gap: 10, marginTop: 14, justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setAnswer('')} disabled={loadingA || !answer}>
                  Clear
                </button>
                <button className="btn btn-primary" onClick={() => handleSubmit(false)} disabled={loadingA || !answer.trim()} style={{ boxShadow: '0 4px 12px rgba(99,102,241,0.25)' }}>
                  {loadingA
                    ? <><span className="spinner" />Evaluating…</>
                    : <><MdCheckCircle />Submit Answer</>
                  }
                </button>
              </div>
            )}
          </motion.div>
        )}

        {/* Evaluation */}
        <AnimatePresence>
          {evaluation && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <EvaluationPanel evaluation={evaluation} />
              <div style={{ display: 'flex', gap: 10, marginTop: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={fetchQuestion} style={{ boxShadow: '0 4px 15px rgba(99,102,241,0.3)' }}>
                  <MdRefresh /> Next Question
                </button>
                <button className="btn btn-secondary" onClick={handleFinishAndDownload}>
                  <MdStop /> End Session {sessionHistory.length > 0 ? '& Download PDF' : ''}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right panel: Camera + Face Analysis */}
      <div style={{ position: 'sticky', top: 20, display: 'flex', flexDirection: 'column', gap: 0 }}>
        {/* Camera feed with Cyberpunk borders and scanlines */}
        <div style={{
          borderRadius: 'var(--radius)',
          overflow: 'hidden',
          border: '2px solid rgba(15, 118, 110, 0.45)',
          boxShadow: '0 0 24px rgba(15, 118, 110, 0.2)',
          position: 'relative',
          background: '#040712'
        }}>
          {/* Scanning frame elements */}
          <div style={{ position: 'absolute', top: 6, left: 6, width: 8, height: 8, borderLeft: '2px solid var(--accent)', borderTop: '2px solid var(--accent)', zIndex: 10 }} />
          <div style={{ position: 'absolute', top: 6, right: 6, width: 8, height: 8, borderRight: '2px solid var(--accent)', borderTop: '2px solid var(--accent)', zIndex: 10 }} />
          <div style={{ position: 'absolute', bottom: 6, left: 6, width: 8, height: 8, borderLeft: '2px solid var(--accent)', borderBottom: '2px solid var(--accent)', zIndex: 10 }} />
          <div style={{ position: 'absolute', bottom: 6, right: 6, width: 8, height: 8, borderRight: '2px solid var(--accent)', borderBottom: '2px solid var(--accent)', zIndex: 10 }} />
          
          {/* Scanning Overlay Heuristic */}
          <div style={{
            position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
            background: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.2) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.05), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.05))',
            backgroundSize: '100% 4px, 6px 100%', pointerEvents: 'none', zIndex: 5, opacity: 0.35
          }} />

          {/* Facial Alignment Silhouette Overlay */}
          {videoActive && (
            <svg
              viewBox="0 0 200 150"
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 8,
                opacity: 0.65
              }}
            >
              {/* Head Outline */}
              <path
                d="M100,25 C70,25 55,48 55,75 C55,102 72,120 100,120 C128,120 145,102 145,75 C145,48 130,25 100,25 Z"
                fill="none"
                stroke={scores?.facePresence >= 30 ? 'var(--success)' : 'var(--accent)'}
                strokeWidth="1.5"
                strokeDasharray={scores?.facePresence >= 30 ? 'none' : '4, 4'}
                style={{ transition: 'stroke 0.3s, stroke-dasharray 0.3s' }}
              />
              
              {/* Shoulders Outline */}
              <path
                d="M40,145 C60,135 75,130 100,130 C125,130 140,135 160,145"
                fill="none"
                stroke={scores?.facePresence >= 30 ? 'var(--success)' : 'var(--accent)'}
                strokeWidth="1.2"
                opacity="0.6"
              />

              {/* Target scope corners around the face */}
              <path d="M 50,45 L 50,35 L 62,35" fill="none" stroke="var(--accent)" strokeWidth="1.5" />
              <path d="M 150,45 L 150,35 L 138,35" fill="none" stroke="var(--accent)" strokeWidth="1.5" />
              <path d="M 50,105 L 50,115 L 62,115" fill="none" stroke="var(--accent)" strokeWidth="1.5" />
              <path d="M 150,105 L 150,115 L 138,115" fill="none" stroke="var(--accent)" strokeWidth="1.5" />

              {/* Center Target Crosshair */}
              <circle cx="100" cy="75" r="5" fill="none" stroke="var(--accent)" strokeWidth="1" opacity="0.7" />
              <line x1="100" y1="62" x2="100" y2="88" stroke="var(--accent)" strokeWidth="0.8" opacity="0.5" />
              <line x1="87" y1="75" x2="113" y2="75" stroke="var(--accent)" strokeWidth="0.8" opacity="0.5" />

              {/* Eye alignment guide line */}
              <line
                x1="70" y1="65" x2="130" y2="65"
                stroke={scores?.gazeScore >= 50 ? 'var(--success)' : 'rgba(255,255,255,0.2)'}
                strokeWidth="1"
                strokeDasharray="2, 2"
              />
            </svg>
          )}

          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ width: '100%', height: 200, backgroundColor: '#070a13', objectFit: 'cover', display: 'block' }}
          />

          {videoActive ? (
            <>
              {/* Camera overlay badge */}
              <div style={{
                position: 'absolute', bottom: 8, left: 8,
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '3px 9px', borderRadius: 99,
                background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
                fontSize: '0.68rem', color: 'rgba(255,255,255,0.8)',
                zIndex: 10
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: 'var(--danger)',
                  boxShadow: '0 0 6px var(--danger)',
                  animation: 'pulse 1.5s infinite',
                  display: 'inline-block',
                }} />
                REC
              </div>
              {/* AI analysis badge */}
              <div style={{
                position: 'absolute', bottom: 8, right: 8,
                padding: '3px 9px', borderRadius: 99,
                background: 'rgba(15,118,110,0.75)', backdropFilter: 'blur(6px)',
                fontSize: '0.65rem', color: '#fff', fontWeight: 700,
                zIndex: 10
              }}>
                🤖 AI Active
              </div>
            </>
          ) : (
            <div style={{
              position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', background: 'rgba(7, 10, 19, 0.85)',
              color: 'var(--text-muted)', fontSize: '0.75rem', gap: 8, zIndex: 9
            }}>
              <span style={{ fontSize: '1.8rem' }}>📷</span>
              <span>Camera Feed Offline</span>
            </div>
          )}
        </div>

        {/* Face Analysis Panel */}
        {videoActive ? (
          <FaceAnalysisPanel scores={scores} feedback={feedback} history={faceHistory} />
        ) : (
          <div style={{
            marginTop: 14,
            padding: '14px',
            background: 'linear-gradient(135deg, rgba(239,68,68,0.06) 0%, rgba(0,0,0,0.3) 100%)',
            borderRadius: 'var(--radius)',
            border: '1px solid rgba(239,68,68,0.25)',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.78rem',
            lineHeight: 1.4
          }}>
            <span style={{ fontSize: '1.4rem', display: 'block', marginBottom: 6 }}>⚠️</span>
            <span>Camera is OFF. Enable camera access to unlock real-time AI composure, lighting, and confidence scoring.</span>
          </div>
        )}

        {/* Session stats panel */}
        {qCount > 0 && (
          <div style={{ marginTop: 14, padding: '14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', marginBottom: 8, fontFamily: 'var(--font-heading)' }}>Session Progress</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Questions</span>
                <span style={{ fontWeight: 700 }}>{qCount}</span>
              </div>
              {sessionHistory.length > 0 && (() => {
                const scored = sessionHistory.filter(h => h.evaluation?.overall_score != null)
                const avgScore = scored.length ? Math.round(scored.reduce((a, h) => a + (h.evaluation.overall_score || 0), 0) / scored.length) : 0
                const color = avgScore >= 70 ? 'var(--success)' : avgScore >= 45 ? 'var(--warning)' : 'var(--danger)'
                return (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Session Avg</span>
                      <span style={{ fontWeight: 700, color }}>{avgScore}%</span>
                    </div>
                  </>
                )
              })()}
            </div>
            {sessionHistory.length > 0 && (
              <button
                className="btn btn-sm"
                style={{ marginTop: 10, width: '100%', justifyContent: 'center', background: 'var(--accent)', color: 'white', border: 'none', boxShadow: '0 2px 8px rgba(139,92,246,0.3)' }}
                onClick={() => downloadSessionPDF({ config, history: sessionHistory, faceHistory: faceHistoryRef.current })}
              >
                <MdDownload /> Download Report
              </button>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); opacity: 0.9; }
          50% { transform: scale(1.2); opacity: 1; }
          100% { transform: scale(1); opacity: 0.9; }
        }
        @keyframes wave {
          0% { transform: scaleY(1); }
          100% { transform: scaleY(2.2); }
        }
      `}</style>
    </motion.div>
  )
}

// ---------- Main Export ----------
export default function InterviewPage() {
  const [phase, setPhase] = useState('setup')
  const [session, setSession] = useState(null)
  const [config, setConfig] = useState(null)

  const handleStart = (sess, cfg) => {
    setSession(sess)
    setConfig(cfg)
    setPhase('session')
  }

  if (phase === 'setup') return <SetupForm onStart={handleStart} />
  if (phase === 'session') return (
    <InterviewSession
      session={session}
      config={config}
      onFinish={() => setPhase('done')}
    />
  )

  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
      className="card" style={{ maxWidth: 480, margin: '60px auto', textAlign: 'center', padding: 48, border: '1px solid var(--border)' }}>
      <div style={{ fontSize: '4rem', marginBottom: 16 }}>🏆</div>
      <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', marginBottom: 8 }}>Session Complete!</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>
        Great work! Your PDF report was downloaded automatically.
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button className="btn btn-primary" onClick={() => setPhase('setup')} style={{ boxShadow: '0 4px 12px rgba(99,102,241,0.25)' }}>
          <MdRefresh /> New Session
        </button>
      </div>
    </motion.div>
  )
}
