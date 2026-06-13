import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { useApp } from '../context/AppContext'
import {
  MdSend, MdMic, MdStop, MdPsychology, MdAutoGraph, MdCheckCircle,
  MdRadioButtonUnchecked, MdPendingActions, MdClose, MdExpandMore,
  MdExpandLess, MdLightbulb, MdSpeed
} from 'react-icons/md'
import { analyzeProfile } from '../services/api'

// ── Profile Collection Form ────────────────────────────────────────────────
const CAREER_OPTIONS = [
  'AI Engineer', 'Data Scientist', 'Full Stack Developer', 'Cloud Engineer',
  'Cybersecurity Analyst', 'DevOps Engineer', 'Product Manager', 'UI/UX Designer'
]

const STEP_ICONS = { complete: '✅', processing: '⚙️', pending: '○', error: '❌' }
const STEP_COLORS = {
  complete: 'var(--success)',
  processing: 'var(--primary)',
  pending: 'var(--text-muted)',
  error: 'var(--danger)',
}

function ThinkingPanel({ steps, isVisible, onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 40, width: 0 }}
      animate={{ opacity: isVisible ? 1 : 0, x: isVisible ? 0 : 40, width: isVisible ? 320 : 0 }}
      transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
      style={{
        overflow: 'hidden',
        background: 'var(--surface)',
        borderLeft: '1px solid var(--glass-border)',
        display: 'flex', flexDirection: 'column',
        flexShrink: 0,
      }}
    >
      <div style={{
        padding: '14px 16px', borderBottom: '1px solid var(--glass-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <MdPsychology style={{ color: 'var(--primary)', fontSize: '1.1rem' }} />
          <span style={{ fontWeight: 700, fontSize: '0.82rem', fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
            Agent Thinking Panel
          </span>
        </div>
        <button className="btn btn-ghost btn-icon" onClick={onClose} style={{ width: 28, height: 28, minHeight: 28, minWidth: 28 }}>
          <MdClose style={{ fontSize: '0.9rem' }} />
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '14px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {steps.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
            <MdPsychology style={{ fontSize: '2.5rem', marginBottom: 8, opacity: 0.3, display: 'block', margin: '0 auto 10px' }} />
            Reasoning steps will appear here when the agent analyzes your profile.
          </div>
        ) : (
          steps.map((step, i) => (
            <motion.div
              key={step.step}
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              style={{
                display: 'flex', gap: 10, padding: '10px 12px',
                borderRadius: 10,
                background: step.status === 'complete'
                  ? 'rgba(16,185,129,0.06)'
                  : step.status === 'processing'
                    ? 'rgba(99,102,241,0.1)'
                    : 'transparent',
                border: `1px solid ${step.status === 'complete' ? 'rgba(16,185,129,0.2)' : step.status === 'processing' ? 'rgba(99,102,241,0.25)' : 'transparent'}`,
                transition: 'all 0.3s ease',
              }}
            >
              <div style={{ flexShrink: 0, marginTop: 1 }}>
                {step.status === 'processing' ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid var(--primary)', borderTopColor: 'transparent' }}
                  />
                ) : (
                  <span style={{ fontSize: '0.75rem' }}>{STEP_ICONS[step.status]}</span>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: STEP_COLORS[step.status], marginBottom: 2 }}>
                  Step {step.step}: {step.title}
                </div>
                {step.detail && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {step.detail}
                  </div>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  )
}

function ConfidenceRing({ score, label, color }) {
  const radius = 38
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <svg width="100" height="100" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="50" cy="50" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        <motion.circle
          cx="50" cy="50" r={radius}
          fill="none" stroke={color || 'var(--primary)'} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
        <text x="50" y="56" textAnchor="middle" fill="var(--text-primary)"
          style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--font-heading)', transform: 'rotate(90deg)', transformOrigin: '50% 50%' }}>
          {score}%
        </text>
      </svg>
      <div style={{ fontSize: '0.72rem', fontWeight: 600, color: color || 'var(--primary)', textAlign: 'center' }}>{label}</div>
    </div>
  )
}

function SkillGapCard({ gaps }) {
  if (!gaps) return null
  const present = gaps.current_skills_present || []
  const missing = gaps.missing_critical_skills || []

  return (
    <div className="card" style={{ margin: '8px 0', border: '1px solid rgba(99,102,241,0.25)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <MdAutoGraph style={{ color: 'var(--primary)', fontSize: '1.1rem' }} />
        <span style={{ fontWeight: 700, fontSize: '0.88rem', fontFamily: 'var(--font-heading)' }}>Skill Gap Analysis</span>
        <span style={{ marginLeft: 'auto', fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: 99, background: `rgba(99,102,241,0.15)`, color: 'var(--primary)' }}>
          {gaps.match_percentage || 0}% Match
        </span>
      </div>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--success)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>✅ You Have</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {present.map(s => (
              <span key={s} style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 99, background: 'rgba(16,185,129,0.1)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.2)', fontWeight: 500 }}>{s}</span>
            ))}
            {present.length === 0 && <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>None yet</span>}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--danger)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>❌ Missing</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {missing.map(s => (
              <span key={s} style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 99, background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.2)', fontWeight: 500 }}>{s}</span>
            ))}
          </div>
        </div>
      </div>
      {gaps.gap_summary && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--glass-border)', lineHeight: 1.5 }}>
          💡 {gaps.gap_summary}
        </p>
      )}
    </div>
  )
}

function ReasoningChain({ chain }) {
  const [expanded, setExpanded] = useState(false)
  if (!chain || chain.length === 0) return null

  return (
    <div className="card" style={{ margin: '8px 0', border: '1px solid rgba(245,158,11,0.2)' }}>
      <button
        onClick={() => setExpanded(e => !e)}
        style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', padding: 0 }}
      >
        <MdLightbulb style={{ color: 'var(--warning)', fontSize: '1.1rem' }} />
        <span style={{ fontWeight: 700, fontSize: '0.88rem', fontFamily: 'var(--font-heading)', color: 'var(--text-primary)', flex: 1 }}>Reasoning Chain</span>
        {expanded ? <MdExpandLess style={{ color: 'var(--text-muted)' }} /> : <MdExpandMore style={{ color: 'var(--text-muted)' }} />}
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden', marginTop: 12 }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {chain.map((r, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, padding: '8px 10px', background: 'rgba(245,158,11,0.05)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.1)' }}>
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--warning)', color: 'white', fontSize: '0.62rem', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{r.step}</div>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{r.thought}</div>
                    {r.conclusion && <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--warning)', marginTop: 3 }}>→ {r.conclusion}</div>}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ProfileForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    name: '', degree: '', branch: '', year: '', cgpa: '',
    skills: '', certifications: '', projects: '', interests: '', career_goal: ''
  })
  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const profile = {
      ...form,
      skills: form.skills.split(',').map(s => s.trim()).filter(Boolean),
      certifications: form.certifications.split(',').map(s => s.trim()).filter(Boolean),
      projects: form.projects.split(',').map(s => s.trim()).filter(Boolean),
      interests: form.interests.split(',').map(s => s.trim()).filter(Boolean),
    }
    onSubmit(profile)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{ margin: '16px', border: '1px solid rgba(99,102,241,0.3)', background: 'linear-gradient(135deg, rgba(99,102,241,0.05), rgba(139,92,246,0.05))' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, var(--primary), var(--accent))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>🧠</div>
        <div>
          <div style={{ fontWeight: 800, fontSize: '0.95rem', fontFamily: 'var(--font-heading)' }}>Start Deep Analysis</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Fill your profile for personalized reasoning & roadmap</div>
        </div>
      </div>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {[
          { label: 'Full Name', key: 'name', placeholder: 'Rahul Sharma', type: 'text' },
          { label: 'Career Goal', key: 'career_goal', placeholder: 'AI Engineer', type: 'select' },
          { label: 'Degree', key: 'degree', placeholder: 'B.Tech', type: 'text' },
          { label: 'Branch', key: 'branch', placeholder: 'Computer Science', type: 'text' },
          { label: 'Year of Study', key: 'year', placeholder: '3rd Year', type: 'text' },
          { label: 'CGPA', key: 'cgpa', placeholder: '8.5', type: 'text' },
        ].map(f => (
          <div key={f.key} className="form-group">
            <label>{f.label}</label>
            {f.type === 'select' ? (
              <select value={form[f.key]} onChange={e => setF(f.key, e.target.value)} required>
                <option value="">Select Career Goal</option>
                {CAREER_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            ) : (
              <input type="text" value={form[f.key]} onChange={e => setF(f.key, e.target.value)} placeholder={f.placeholder} required={['name', 'career_goal'].includes(f.key)} />
            )}
          </div>
        ))}
        {[
          { label: 'Current Skills (comma separated)', key: 'skills', placeholder: 'Python, React, SQL...' },
          { label: 'Certifications (comma separated)', key: 'certifications', placeholder: 'AWS Cloud Practitioner...' },
          { label: 'Projects Built (comma separated)', key: 'projects', placeholder: 'Portfolio website, Chat app...' },
          { label: 'Areas of Interest', key: 'interests', placeholder: 'Machine Learning, Web Dev...' },
        ].map(f => (
          <div key={f.key} className="form-group" style={{ gridColumn: '1 / -1' }}>
            <label>{f.label}</label>
            <input type="text" value={form[f.key]} onChange={e => setF(f.key, e.target.value)} placeholder={f.placeholder} />
          </div>
        ))}
        <button type="submit" className="btn btn-primary" style={{ gridColumn: '1 / -1', marginTop: 4 }} disabled={loading}>
          {loading ? <span className="spinner" /> : '🚀 Analyze My Profile & Generate Roadmap'}
        </button>
      </form>
    </motion.div>
  )
}

// ── Main AgentChat Component ───────────────────────────────────────────────
export default function AgentChat() {
  const { user, addToast, agentProfile, updateAgentProfile, reasoningSteps, setReasoningSteps, careerMatch, setCareerMatch, skillGaps, setSkillGaps, storeAnalysisResult, lastAnalysis } = useApp()
  const [messages, setMessages] = useState([
    {
      id: 1, sender: 'ai',
      text: `## 👋 Hey! I'm your CareerCoach AI\n\nI'm here to help you **chase your dreams** — whether that's cracking into AI, landing your first job, building a killer portfolio, acing interviews, or figuring out what to do next.\n\nJust tell me what's on your mind. You can start with something like:\n- *"I want to become a Data Scientist, where do I start?"*\n- *"What skills do I need for full stack dev?"*\n- *"How do I crack off-campus placements with a low CGPA?"*\n- *"I know Python and SQL — how close am I to being a Data Scientist?"*\n\nOr ask me anything — I'm not just a career bot! 😄`,
      type: 'welcome',
      ragGrounded: false,
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [thinkingOpen, setThinkingOpen] = useState(true)
  const [showProfileForm, setShowProfileForm] = useState(false)
  const [sessions, setSessions] = useState([])
  const [sessionId, setSessionId] = useState(null)

  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Initialize session
  useEffect(() => {
    const init = async () => {
      try {
        const { listChatSessions, createChatSession } = await import('../services/api')
        let sessList = await listChatSessions(user.id)
        if (sessList.length === 0) {
          const s = await createChatSession({ user_id: user.id, title: 'Agent Chat 1' })
          sessList = [s]
        }
        setSessions(sessList)
        setSessionId(sessList[0].id)
      } catch (err) {
        console.error('Session init error', err)
      }
    }
    init()
  }, [user.id])

  const runFullAnalysis = useCallback(async (profile) => {
    setAnalyzing(true)
    setThinkingOpen(true)

    // Animate reasoning steps
    const steps = [
      { step: 1, title: 'Understanding Your Profile', status: 'processing', detail: '' },
      { step: 2, title: 'Analyzing Skills & Experience', status: 'pending', detail: '' },
      { step: 3, title: 'Detecting Skill Gaps', status: 'pending', detail: '' },
      { step: 4, title: 'Creating Personalized Roadmap', status: 'pending', detail: '' },
      { step: 5, title: 'Generating Reasoning Chain', status: 'pending', detail: '' },
      { step: 6, title: 'Calculating Career Match Score', status: 'pending', detail: '' },
      { step: 7, title: 'Assembling Recommendations', status: 'pending', detail: '' },
    ]
    setReasoningSteps(steps)

    // Animate step-by-step progress
    const animateStep = (idx, delay) => {
      setTimeout(() => {
        setReasoningSteps(prev => prev.map((s, i) => i === idx ? { ...s, status: 'processing' } : s))
      }, delay)
    }

    for (let i = 1; i < 7; i++) animateStep(i, i * 800)

    try {
      const result = await analyzeProfile({ ...profile, career_goal: profile.career_goal })
      storeAnalysisResult(result)
      updateAgentProfile(profile)

      // Mark all steps complete
      if (result.reasoning_steps) {
        setReasoningSteps(result.reasoning_steps)
      } else {
        setReasoningSteps(steps.map(s => ({ ...s, status: 'complete' })))
      }

      // Build rich response card
      const conf = result.confidence_score || {}
      const gaps = result.skill_gaps || {}
      const roadmap = result.roadmap || {}
      const chain = result.reasoning_chain || []

      const responseMsg = {
        id: Date.now(),
        sender: 'ai',
        type: 'analysis',
        text: `## 🎯 Career Analysis Complete for ${profile.name || 'You'}\n\n**Goal:** ${profile.career_goal} | **Match Score:** ${conf.overall_score || 0}%\n\n### 📊 Skills You Have\n${(gaps.current_skills_present || []).map(s => `- ✅ ${s}`).join('\n') || '- Building foundation'}\n\n### ❌ Critical Missing Skills\n${(gaps.missing_critical_skills || []).slice(0, 6).map(s => `- ❌ ${s}`).join('\n')}\n\n### 🗺ï¸ Your 30-Day Focus\n${roadmap.phase_30_days?.milestone || 'Build foundation skills'}\n\n### 💡 My Reasoning\n${chain[0]?.thought || ''} → ${chain[0]?.conclusion || ''}\n\n> 💬 Ask me anything about your roadmap, or head to the **Roadmap** or **Career Dashboard** pages for full visual analysis!`,
        analysisData: result,
        gaps: result.skill_gaps,
        chain: result.reasoning_chain,
        confidence: result.confidence_score,
      }

      setMessages(prev => [...prev, responseMsg])
    } catch (err) {
      addToast('Analysis failed: ' + (err.message || 'Unknown error'), 'error')
      setReasoningSteps(steps.map(s => ({ ...s, status: s.status === 'processing' ? 'error' : s.status })))
    } finally {
      setAnalyzing(false)
    }
  }, [storeAnalysisResult, updateAgentProfile, setReasoningSteps, addToast])

  const handleSend = useCallback(async (textOverride) => {
    const text = typeof textOverride === 'string' ? textOverride : input
    if (!text.trim() || loading) return
    if (!sessionId) { addToast('Creating session...', 'info'); return }

    const tempId = Date.now()
    const userMsg = { id: tempId, sender: 'user', text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setThinkingOpen(true)

    // Initialize standard message processing steps
    const steps = [
      { step: 1, title: 'Receiving User Message', status: 'complete', detail: `Received: "${text.slice(0, 30)}${text.length > 30 ? '...' : ''}"` },
      { step: 2, title: 'Parsing Intent & Constraints', status: 'processing', detail: 'Deconstructing query keywords...' },
      { step: 3, title: 'RAG Knowledge Retrieval', status: 'pending', detail: 'Searching career knowledge base...' },
      { step: 4, title: 'Generating AI Agent Reasoning', status: 'pending', detail: 'Computing step-by-step career logic...' },
      { step: 5, title: 'Formatting Structured Answer', status: 'pending', detail: 'Applying professional formatting guidelines...' }
    ]
    setReasoningSteps(steps)

    // Animate step transitions
    const stepTimers = [
      setTimeout(() => {
        setReasoningSteps(prev => prev.map((s, i) => i === 1 ? { ...s, status: 'complete', detail: 'Intent parsed: Career query evaluated' } : i === 2 ? { ...s, status: 'processing', detail: 'Searching career knowledge base...' } : s))
      }, 600),
      setTimeout(() => {
        setReasoningSteps(prev => prev.map((s, i) => i === 2 ? { ...s, status: 'complete', detail: '📚 Relevant knowledge retrieved' } : i === 3 ? { ...s, status: 'processing' } : s))
      }, 1200),
      setTimeout(() => {
        setReasoningSteps(prev => prev.map((s, i) => i === 3 ? { ...s, status: 'complete', detail: 'Reasoning chain formulated' } : i === 4 ? { ...s, status: 'processing' } : s))
      }, 1800)
    ]

    try {
      const { createChatMessage } = await import('../services/api')
      const result = await createChatMessage({ session_id: sessionId, content: text, role: 'user' })
      const aiReply = result.assistant_message?.message || result.assistant_message?.content || ''
      const isRagGrounded = result.assistant_message?.rag_sources === true

      // Clear timers and mark all complete
      stepTimers.forEach(clearTimeout)
      setReasoningSteps([
        { step: 1, title: 'Receiving User Message', status: 'complete', detail: 'Message received' },
        { step: 2, title: 'Parsing Intent & Constraints', status: 'complete', detail: 'Intent parsed: Career query evaluated' },
        { step: 3, title: 'RAG Knowledge Retrieval', status: 'complete', detail: isRagGrounded ? '📚 Career knowledge retrieved & injected' : 'Knowledge search complete' },
        { step: 4, title: 'Generating AI Agent Reasoning', status: 'complete', detail: 'Reasoning chain formulated' },
        { step: 5, title: 'Formatting Structured Answer', status: 'complete', detail: `Response generated (${aiReply.length} chars)` }
      ])

      setMessages(prev => [
        ...prev.filter(m => m.id !== tempId),
        { id: result.user_message.id, sender: 'user', text },
        { id: result.assistant_message.id, sender: 'ai', text: aiReply, type: 'chat', ragGrounded: isRagGrounded }
      ])
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      setReasoningSteps(prev => prev.map(s => s.status === 'processing' ? { ...s, status: 'error', detail: err.message || 'Error occurred' } : s))
      setMessages(prev => prev.filter(m => m.id !== tempId))
      addToast('Message failed: ' + (err.message || 'Check backend'), 'error')
    } finally {
      setLoading(false)
    }
  }, [input, sessionId, loading, addToast, setReasoningSteps, setThinkingOpen])

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 120px)', gap: 0, overflow: 'hidden', borderRadius: 16, border: '1px solid var(--glass-border)', background: 'var(--surface)' }}>

      {/* Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>

        {/* Header */}
        <div style={{
          padding: '14px 20px', borderBottom: '1px solid var(--glass-border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05))',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, var(--cyber-cyan), var(--cyber-violet))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', boxShadow: '0 0 20px rgba(0,245,255,0.4)' }}>🧠</div>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontFamily: 'Orbitron, sans-serif', lineHeight: 1.1, color: 'var(--cyber-cyan)', letterSpacing: '0.06em' }}>CareerCoach AI</h3>
              <span style={{ fontSize: '0.7rem', color: 'var(--cyber-green)', display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'Exo 2, sans-serif', letterSpacing: '0.06em' }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--cyber-green)', display: 'inline-block', boxShadow: '0 0 6px rgba(0,255,136,0.8)' }} /> Active · Reasoning Mode
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-sm btn-secondary" onClick={() => setShowProfileForm(p => !p)} style={{ fontSize: '0.75rem' }}>
              📋 {showProfileForm ? 'Hide Form' : 'Quick Profile'}
            </button>
            <button
              className={`btn btn-sm ${thinkingOpen ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setThinkingOpen(o => !o)}
              style={{ fontSize: '0.75rem' }}
            >
              <MdPsychology /> Thinking Panel
            </button>
          </div>
        </div>

        {/* Profile Form (collapsible) */}
        <AnimatePresence>
          {showProfileForm && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: 'hidden', flexShrink: 0 }}>
              <div style={{ overflowY: 'auto', maxHeight: '45vh' }}>
                <ProfileForm onSubmit={(profile) => { setShowProfileForm(false); runFullAnalysis(profile) }} loading={analyzing} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <AnimatePresence>
            {messages.map(m => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`chat-message ${m.sender}`}
                style={{ alignItems: 'flex-start' }}
              >
                <div className={`chat-avatar ${m.sender}`} style={{ fontSize: m.sender === 'ai' ? '1.1rem' : '0.8rem' }}>
                  {m.sender === 'ai' ? '🧠' : (user.full_name?.[0] || 'U').toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className={`chat-bubble ${m.sender}`} style={{ padding: m.sender === 'ai' ? '14px 18px' : '10px 14px' }}>
                    {m.sender === 'ai' ? (
                      <>
                        <ReactMarkdown>{m.text}</ReactMarkdown>
                        {m.ragGrounded && (
                          <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 5 }}>
                            <span style={{
                              fontSize: '0.6rem', padding: '2px 8px', borderRadius: 99,
                              background: 'rgba(99,102,241,0.12)', color: 'var(--primary)',
                              border: '1px solid rgba(99,102,241,0.25)', fontWeight: 700,
                              letterSpacing: '0.05em', textTransform: 'uppercase'
                            }}>📚 RAG</span>
                            <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
                              Knowledge-grounded response
                            </span>
                          </div>
                        )}
                      </>
                    ) : (
                      <span style={{ fontSize: '0.875rem' }}>{m.text}</span>
                    )}
                  </div>
                  {/* Rich Analysis Cards */}
                  {m.type === 'analysis' && m.gaps && <SkillGapCard gaps={m.gaps} />}
                  {m.type === 'analysis' && m.chain && <ReasoningChain chain={m.chain} />}
                  {m.type === 'analysis' && m.confidence && (
                    <div className="card" style={{ margin: '8px 0', display: 'flex', alignItems: 'center', gap: 20, border: '1px solid rgba(99,102,241,0.2)' }}>
                      <ConfidenceRing score={m.confidence.overall_score || 0} label={m.confidence.label || 'Score'} color={m.confidence.color} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, fontSize: '0.88rem', fontFamily: 'var(--font-heading)', marginBottom: 8 }}>Career Match Score</div>
                        {(m.confidence.reasons || []).map((r, i) => (
                          <div key={i} style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>• {r}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
            {(loading || analyzing) && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="chat-message ai">
                <div className="chat-avatar ai">🧠</div>
                <div className="chat-bubble ai" style={{ padding: '10px 16px' }}>
                  <div className="ai-thinking"><span /><span /><span /></div>
                  {analyzing && <div style={{ fontSize: '0.7rem', color: 'var(--primary)', marginTop: 6, fontWeight: 600 }}>Analyzing profile... check Thinking Panel →</div>}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: '14px 20px', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: 10, alignItems: 'flex-end', flexShrink: 0 }}>
          <div style={{ flex: 1 }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
              placeholder="Ask about your career, skills, roadmap... or describe your situation"
              style={{ width: '100%', minHeight: 46, maxHeight: 100, resize: 'none', padding: '12px 16px', background: 'var(--surface-2)', borderRadius: 10 }}
              disabled={loading || analyzing}
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: 46, height: 46, padding: 0, borderRadius: 10, flexShrink: 0 }}
            onClick={() => handleSend()}
            disabled={loading || !input.trim() || analyzing}
          >
            <MdSend style={{ fontSize: '1.1rem' }} />
          </button>
        </div>
      </div>

      {/* Thinking Panel */}
      <ThinkingPanel steps={reasoningSteps} isVisible={thinkingOpen} onClose={() => setThinkingOpen(false)} />
    </div>
  )
}
