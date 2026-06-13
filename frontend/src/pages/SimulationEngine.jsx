import { useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { simulateCareer } from '../services/api'
import * as MdIcons from 'react-icons/md'

const {
  MdPlayArrow: PlayIcon, MdTrendingUp: TrendIcon, MdWorkOutline: WorkIcon,
  MdAttachMoney: MoneyIcon, MdSchool: SchoolIcon, MdAssignment: TaskIcon,
  MdLink: LinkIcon, MdCheckCircle: CheckIcon, MdChevronRight: ChevronIcon,
  MdInfo: InfoIcon, MdWarning: WarnIcon
} = MdIcons

const fadeUp = (d = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay: d }
})

const CAREER_OPTIONS = [
  'AI Engineer', 'Data Scientist', 'Full Stack Developer', 'Cloud Engineer',
  'Cybersecurity Analyst', 'DevOps Engineer', 'Product Manager', 'UI/UX Designer'
]

const PIPELINE_STAGES = [
  { key: 'current', label: 'Current State', icon: '👤', color: 'var(--cyber-cyan)' },
  { key: 'learning', label: 'Learning Path', icon: '📚', color: 'var(--cyber-blue)' },
  { key: 'projects', label: 'Projects Built', icon: '🛠️', color: 'var(--cyber-violet)' },
  { key: 'skills', label: 'Skills Gained', icon: '⚡', color: 'var(--cyber-orange)' },
  { key: 'roles', label: 'Expected Roles', icon: '💼', color: 'var(--cyber-cyan)' },
  { key: 'salary', label: 'Salary Range', icon: '💰', color: 'var(--cyber-green)' },
]

const SIMULATION_STEPS = [
  "Initializing Career Matrix Simulation engine...",
  "Mapping candidate skill vector alignment...",
  "Calculating hourly learning rates and study duration bounds...",
  "Predicting month-by-month milestone trajectories...",
  "Running project portfolio compatibility simulation...",
  "Analyzing target job market demand curves...",
  "Calculating expected salary ranges...",
  "Synthesizing final job readiness scores...",
  "Finalizing study & practice roadmap..."
]

function renderResourceLink(r) {
  let url = '';
  const lowercase = r.toLowerCase();

  const urlMatch = r.match(/https?:\/\/[^\s]+/i);
  if (urlMatch) {
    url = urlMatch[0];
  } else {
    const query = encodeURIComponent(r);
    if (lowercase.includes('udemy')) {
      url = `https://www.udemy.com/courses/search/?q=${query}`;
    } else if (lowercase.includes('coursera')) {
      url = `https://www.coursera.org/search?query=${query}`;
    } else if (lowercase.includes('youtube')) {
      url = `https://www.youtube.com/results?search_query=${query}`;
    } else {
      url = `https://www.google.com/search?q=${query}`;
    }
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        color: 'var(--cyber-cyan)',
        textDecoration: 'underline',
        fontWeight: '600',
        transition: 'color 0.2s',
        display: 'inline-block',
        fontFamily: "'Exo 2', sans-serif",
        fontSize: '0.78rem',
      }}
      onMouseOver={(e) => e.target.style.color = 'var(--cyber-magenta)'}
      onMouseOut={(e) => e.target.style.color = 'var(--cyber-cyan)'}
    >
      {r}
    </a>
  );
}

const PHASE_STYLES = {
  '30': { color: 'var(--cyber-cyan)', bg: 'rgba(0,245,255,0.04)', border: 'rgba(0,245,255,0.2)', icon: '🌱', label: '30 Days' },
  '90': { color: 'var(--cyber-violet)', bg: 'rgba(124,58,237,0.04)', border: 'rgba(124,58,237,0.2)', icon: '⚡', label: '90 Days' },
  '180': { color: 'var(--cyber-green)', bg: 'rgba(0,255,136,0.04)', border: 'rgba(0,255,136,0.2)', icon: '🏆', label: '180 Days' },
}

// Corner bracket decoration helper
function CyberCorners({ color = 'var(--cyber-cyan)', size = 10, thickness = 2 }) {
  const s = {
    position: 'absolute',
    width: size,
    height: size,
  }
  const b = `${thickness}px solid ${color}`
  return (
    <>
      <span style={{ ...s, top: 8, left: 8, borderLeft: b, borderTop: b }} />
      <span style={{ ...s, top: 8, right: 8, borderRight: b, borderTop: b }} />
      <span style={{ ...s, bottom: 8, left: 8, borderLeft: b, borderBottom: b }} />
      <span style={{ ...s, bottom: 8, right: 8, borderRight: b, borderBottom: b }} />
    </>
  )
}

function PhaseCard({ phaseKey, data, checkedTasks, toggleTask }) {
  const [expanded, setExpanded] = useState(phaseKey === '30')
  const style = PHASE_STYLES[phaseKey]
  if (!data) return null

  const tasks = data.daily_tasks || []
  const checkedCount = tasks.filter((_, idx) => checkedTasks[`${phaseKey}-${idx}`]).length
  const progressPercent = tasks.length > 0 ? Math.round((checkedCount / tasks.length) * 100) : 0

  return (
    <motion.div
      style={{
        border: `1px solid ${style.border}`,
        background: `rgba(6,10,22,0.88)`,
        backdropFilter: 'blur(20px)',
        overflow: 'hidden',
        position: 'relative',
        borderRadius: 14,
        padding: '16px 16px 0 16px',
      }}
      whileHover={{ y: -2, boxShadow: `0 8px 24px ${style.border}` }}
      transition={{ duration: 0.2 }}
    >
      <CyberCorners color={style.color} size={8} thickness={2} />

      {/* Left accent bar with glow */}
      <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: 3, background: style.color, boxShadow: `0 0 8px ${style.color}` }} />

      <button
        onClick={() => setExpanded(e => !e)}
        style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', padding: '4px 0 0 10px' }}
      >
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: `linear-gradient(135deg, ${style.color}30, ${style.color}10)`,
          border: `1px solid ${style.color}50`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', flexShrink: 0,
          boxShadow: `0 0 15px ${style.border}`
        }}>
          {style.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: "'Exo 2', sans-serif", fontWeight: 800, fontSize: '0.95rem', color: style.color }}>
            {style.label} Phase — {data.theme || 'Growth Stage'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'rgba(0,245,255,0.5)', marginTop: 2 }}>
            Target Milestone: {data.milestone || 'Skill acquisition'}
          </div>
        </div>
        <div style={{ fontSize: '1rem', color: style.color, paddingRight: 10 }}>
          {expanded ? '▲' : '▼'}
        </div>
      </button>

      {/* Progress Bar */}
      <div style={{ margin: '12px 14px 4px 60px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: '0.68rem', fontWeight: 600, color: 'rgba(0,245,255,0.4)' }}>
          <span>Phase Checklist Progress</span>
          <span style={{ color: style.color }}>{progressPercent}% ({checkedCount}/{tasks.length})</span>
        </div>
        <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 99, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${progressPercent}%`, background: 'linear-gradient(90deg, var(--cyber-cyan), var(--cyber-violet))', borderRadius: 99, transition: 'width 0.3s ease' }} />
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 12, paddingLeft: 60, paddingRight: 14, paddingBottom: 14 }}>
              {/* Focus Skills */}
              {data.focus_skills?.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: style.color, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>🎯 Key Skills to Target</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {data.focus_skills.map((s, i) => (
                      <span key={i} style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: 99, background: `${style.color}18`, color: style.color, border: `1px solid ${style.color}30`, fontWeight: 600, fontFamily: "'Exo 2', sans-serif" }}>{s}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Checklist */}
              {tasks.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'rgba(0,245,255,0.5)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>📅 Actionable Learning Tasks</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {tasks.map((t, i) => {
                      const isChecked = !!checkedTasks[`${phaseKey}-${i}`];
                      return (
                        <div
                          key={i}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 8,
                            padding: '6px 10px',
                            background: isChecked ? 'rgba(0,255,136,0.05)' : 'rgba(0,245,255,0.02)',
                            borderRadius: 6,
                            border: `1px solid ${isChecked ? 'rgba(0,255,136,0.2)' : 'rgba(0,245,255,0.08)'}`,
                            cursor: 'pointer',
                            transition: 'all 0.15s'
                          }}
                          onClick={() => toggleTask(phaseKey, i)}
                          onMouseOver={e => { if (!isChecked) e.currentTarget.style.border = '1px solid rgba(0,245,255,0.25)'; }}
                          onMouseOut={e => { if (!isChecked) e.currentTarget.style.border = '1px solid rgba(0,245,255,0.08)'; }}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => { }}
                            style={{ marginTop: 2, cursor: 'pointer', accentColor: 'var(--cyber-cyan)' }}
                          />
                          <span style={{ fontSize: '0.74rem', color: isChecked ? 'rgba(0,245,255,0.4)' : 'rgba(255,255,255,0.75)', textDecoration: isChecked ? 'line-through' : 'none', transition: 'all 0.15s', lineHeight: 1.4, fontFamily: "'Exo 2', sans-serif" }}>
                            {t}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function CertCard({ cert, i }) {
  const priority = cert.priority === 'high'
  const query = encodeURIComponent(`${cert.name} ${cert.platform || ''}`);
  const url = `https://www.google.com/search?q=${query}`;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.05 }}
      style={{
        border: priority ? '1px solid rgba(0,245,255,0.25)' : '1px solid rgba(0,245,255,0.1)',
        position: 'relative',
        overflow: 'hidden',
        background: 'rgba(6,10,22,0.88)',
        backdropFilter: 'blur(20px)',
        borderRadius: 14,
        padding: '16px',
        boxShadow: priority ? '0 0 20px rgba(0,245,255,0.08)' : 'none',
      }}
    >
      <CyberCorners color={priority ? 'var(--cyber-cyan)' : 'rgba(0,245,255,0.3)'} size={7} thickness={1} />
      {priority && (
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: 'linear-gradient(90deg, var(--cyber-cyan), var(--cyber-violet))' }} />
      )}
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <div style={{ fontSize: '1.4rem' }}>🎓</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: '0.82rem', fontFamily: "'Exo 2', sans-serif" }}>
            <a href={url} target="_blank" rel="noopener noreferrer"
              style={{ color: 'rgba(255,255,255,0.9)', textDecoration: 'underline', transition: 'color 0.2s' }}
              onMouseOver={e => e.target.style.color = 'var(--cyber-cyan)'}
              onMouseOut={e => e.target.style.color = 'rgba(255,255,255,0.9)'}>
              {cert.name}
            </a>
          </div>
          <div style={{ fontSize: '0.7rem', color: 'rgba(0,245,255,0.5)', marginTop: 4, fontFamily: "'Exo 2', sans-serif" }}>
            Platform: {cert.platform} · duration: {cert.duration}
          </div>
        </div>
        <span style={{
          fontSize: '0.6rem', fontWeight: 700, padding: '2px 8px', borderRadius: 99,
          background: priority ? 'rgba(0,245,255,0.12)' : 'rgba(255,255,255,0.05)',
          color: priority ? 'var(--cyber-cyan)' : 'rgba(255,255,255,0.4)',
          textTransform: 'uppercase', letterSpacing: '0.05em',
          border: priority ? '1px solid rgba(0,245,255,0.25)' : '1px solid rgba(255,255,255,0.1)',
          boxShadow: priority ? '0 0 8px rgba(0,245,255,0.2)' : 'none',
          fontFamily: "'Exo 2', sans-serif",
        }}>{cert.priority}</span>
      </div>
    </motion.div>
  )
}

function SimulationMatrixLoader() {
  const [currentStepIdx, setCurrentStepIdx] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIdx(prev => {
        if (prev < SIMULATION_STEPS.length - 1) return prev + 1
        return prev
      })
    }, 450)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{
      textAlign: 'center', padding: 48,
      background: 'rgba(2,5,16,0.97)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(0,245,255,0.3)',
      position: 'relative',
      overflow: 'hidden',
      boxShadow: '0 0 40px rgba(0,245,255,0.12)',
      borderRadius: 20
    }}>
      {/* Laser line effect */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: '100%', height: 2,
        background: 'linear-gradient(90deg, transparent, var(--cyber-cyan), transparent)',
        animation: 'matrixLine 2s infinite linear'
      }} />

      {/* Cyber Corners */}
      <div style={{ position: 'absolute', top: 12, left: 12, width: 12, height: 12, borderLeft: '2px solid var(--cyber-cyan)', borderTop: '2px solid var(--cyber-cyan)' }} />
      <div style={{ position: 'absolute', top: 12, right: 12, width: 12, height: 12, borderRight: '2px solid var(--cyber-cyan)', borderTop: '2px solid var(--cyber-cyan)' }} />
      <div style={{ position: 'absolute', bottom: 12, left: 12, width: 12, height: 12, borderLeft: '2px solid var(--cyber-cyan)', borderBottom: '2px solid var(--cyber-cyan)' }} />
      <div style={{ position: 'absolute', bottom: 12, right: 12, width: 12, height: 12, borderRight: '2px solid var(--cyber-cyan)', borderBottom: '2px solid var(--cyber-cyan)' }} />

      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        style={{
          width: 60, height: 60, borderRadius: '50%',
          border: '3px solid rgba(0,245,255,0.15)',
          borderTopColor: 'var(--cyber-cyan)',
          boxShadow: '0 0 20px rgba(0,245,255,0.3)',
          margin: '0 auto 24px'
        }}
      />
      <h3 style={{ fontFamily: 'Orbitron, sans-serif', marginBottom: 12, letterSpacing: '0.1em', color: 'var(--cyber-cyan)', fontWeight: 900, fontSize: '1.1rem', textShadow: '0 0 20px rgba(0,245,255,0.5)' }}>
        SYSTEM GENERATING SIMULATION
      </h3>

      <div style={{
        maxWidth: 460, margin: '0 auto',
        background: '#020510',
        borderRadius: 8,
        padding: '16px 20px',
        border: '1px solid rgba(0,245,255,0.12)',
        textAlign: 'left',
        fontFamily: 'monospace',
        fontSize: '0.75rem',
        minHeight: 130,
        lineHeight: 1.5
      }}>
        {SIMULATION_STEPS.slice(0, currentStepIdx + 1).map((s, idx) => (
          <div key={idx} style={{ color: idx === currentStepIdx ? 'var(--cyber-cyan)' : 'rgba(0,255,136,0.6)', marginBottom: 6, display: 'flex', gap: 8 }}>
            <span style={{ color: idx === currentStepIdx ? 'var(--cyber-cyan)' : 'var(--cyber-green)' }}>
              {idx === currentStepIdx ? "⚡" : "✓"}
            </span>
            <span>{s}</span>
          </div>
        ))}
      </div>
      <p style={{ color: 'rgba(0,245,255,0.45)', fontSize: '0.8rem', marginTop: 18, fontFamily: "'Exo 2', sans-serif" }}>The reasoning agent is mapping your career growth projection...</p>

      <style>{`
        @keyframes matrixLine {
          0% { transform: translateY(0); opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { transform: translateY(280px); opacity: 0; }
        }
      `}</style>
    </div>
  )
}

function PipelineFlow({ result, visible }) {
  if (!result) return null
  const finalState = result.final_state || {}

  const stageData = {
    current: { content: ['Current skill set', `CGPA: N/A`, 'Starting point'] },
    learning: { content: (result.monthly_milestones || []).slice(0, 3).map(m => `Month ${m.month}: ${m.project_built || 'Learning'}`) },
    projects: { content: (finalState.projects_portfolio || []).slice(0, 4) },
    skills: { content: (finalState.skills_gained || []).slice(0, 5) },
    roles: { content: (finalState.expected_job_roles || []) },
    salary: { content: [finalState.salary_range || 'Competitive', `${finalState.job_readiness || 0}% Job Ready`] },
  }

  return (
    <div style={{ display: 'flex', alignItems: 'stretch', gap: 0, overflowX: 'auto', padding: '0 4px' }}>
      {PIPELINE_STAGES.map((stage, i) => (
        <div key={stage.key} style={{ display: 'flex', alignItems: 'center', flex: 1, minWidth: 140 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={visible ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: i * 0.12, duration: 0.5 }}
            style={{
              flex: 1,
              background: 'rgba(6,10,22,0.88)',
              backdropFilter: 'blur(20px)',
              borderRadius: 14,
              border: `1px solid ${stage.color}30`,
              padding: '16px 14px',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: visible ? `0 0 15px ${stage.color}18` : 'none',
              transition: 'box-shadow 0.5s ease'
            }}
          >
            <CyberCorners color={stage.color} size={7} thickness={1} />
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: stage.color, borderRadius: '14px 14px 0 0', boxShadow: `0 0 8px ${stage.color}` }} />
            <div style={{ fontSize: '1.4rem', marginBottom: 6, marginTop: 4 }}>{stage.icon}</div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: stage.color, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8, fontFamily: "'Exo 2', sans-serif" }}>{stage.label}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {(stageData[stage.key]?.content || []).map((item, j) => (
                <div key={j} style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.6)', lineHeight: 1.4, display: 'flex', gap: 5, fontFamily: "'Exo 2', sans-serif" }}>
                  <span style={{ color: stage.color, flexShrink: 0 }}>•</span>{item}
                </div>
              ))}
            </div>
          </motion.div>
          {i < PIPELINE_STAGES.length - 1 && (
            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              animate={visible ? { scaleX: 1, opacity: 1 } : {}}
              transition={{ delay: i * 0.12 + 0.25 }}
              style={{ width: 20, height: 2, background: `linear-gradient(90deg, ${stage.color}, ${PIPELINE_STAGES[i + 1].color})`, flexShrink: 0, position: 'relative', boxShadow: `0 0 6px ${stage.color}` }}
            >
              <div style={{ position: 'absolute', right: -4, top: -4, width: 10, height: 10, borderRight: `2px solid ${PIPELINE_STAGES[i + 1].color}`, borderTop: `2px solid ${PIPELINE_STAGES[i + 1].color}`, transform: 'rotate(45deg)' }} />
            </motion.div>
          )}
        </div>
      ))}
    </div>
  )
}

function MilestoneTimeline({ milestones }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {milestones.map((m, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.06 }}
          style={{
            display: 'flex', gap: 14, padding: '12px 16px',
            background: 'rgba(6,10,22,0.85)',
            borderRadius: 12,
            border: '1px solid rgba(0,245,255,0.12)',
            position: 'relative',
          }}
        >
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, var(--cyber-cyan), var(--cyber-violet))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 800, fontSize: '0.8rem', flexShrink: 0, boxShadow: '0 0 12px rgba(0,245,255,0.3)' }}>
            M{m.month}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'rgba(255,255,255,0.9)', marginBottom: 4, fontFamily: "'Exo 2', sans-serif" }}>Month {m.month}</div>
            {m.project_built && <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', fontFamily: "'Exo 2', sans-serif" }}>🛠️ Project focus: {m.project_built}</div>}
            {(m.skills_gained || []).length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                {m.skills_gained.map((s, j) => (
                  <span key={j} style={{ fontSize: '0.65rem', padding: '2px 7px', borderRadius: 99, background: 'rgba(0,245,255,0.08)', color: 'var(--cyber-cyan)', border: '1px solid rgba(0,245,255,0.15)', fontWeight: 500, fontFamily: "'Exo 2', sans-serif" }}>{s}</span>
                ))}
              </div>
            )}
            {m.readiness_boost && <div style={{ fontSize: '0.7rem', color: 'var(--cyber-green)', marginTop: 4, fontWeight: 600, fontFamily: "'Exo 2', sans-serif" }}>📈 Readiness boost: {m.readiness_boost}</div>}
          </div>
        </motion.div>
      ))}
    </div>
  )
}

export default function SimulationEngine() {
  const { agentProfile } = useApp()
  const [form, setForm] = useState({
    career_goal: agentProfile?.career_goal || 'AI Engineer',
    hours_per_day: 3,
    months: 6,
    skills: agentProfile?.skills?.join(', ') || '',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pipelineVisible, setPipelineVisible] = useState(false)
  const [tab, setTab] = useState('pipeline')
  const [checkedTasks, setCheckedTasks] = useState({})
  const [simError, setSimError] = useState('')

  const toggleTask = useCallback((phaseKey, idx) => {
    setCheckedTasks(prev => ({
      ...prev,
      [`${phaseKey}-${idx}`]: !prev[`${phaseKey}-${idx}`]
    }))
  }, [])

  const runSimulation = useCallback(async () => {
    setLoading(true)
    setResult(null)
    setSimError('')
    setPipelineVisible(false)
    try {
      const profile = {
        ...agentProfile,
        skills: form.skills.split(',').map(s => s.trim()).filter(Boolean),
        career_goal: form.career_goal,
      }
      const res = await simulateCareer({
        profile,
        career_goal: form.career_goal,
        hours_per_day: parseFloat(form.hours_per_day),
        months: parseInt(form.months),
      })
      if (!res || Object.keys(res).length === 0) {
        setSimError('The simulation returned empty results. Make sure the backend is running and try again.')
      } else {
        setResult(res)
        setTimeout(() => setPipelineVisible(true), 300)
      }
    } catch (err) {
      console.error('Simulation error:', err)
      const msg = err?.response?.data?.detail || err?.message || 'Unknown error'
      setSimError(`Simulation failed: ${msg}. Please ensure the backend server is running.`)
    } finally {
      setLoading(false)
    }
  }, [form, agentProfile])

  const fs = result?.final_state || {}
  const totalHours = form.hours_per_day * 30 * form.months

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* ── Header Banner ── */}
      <motion.div {...fadeUp(0)} style={{
        background: 'linear-gradient(135deg, rgba(0,8,20,0.97) 0%, rgba(5,0,20,0.97) 100%)',
        borderRadius: 20, padding: '28px 32px', position: 'relative', overflow: 'hidden',
        border: '1px solid rgba(0,245,255,0.25)',
        boxShadow: '0 0 40px rgba(0,245,255,0.08)'
      }}>
        {/* Cyber corner brackets */}
        <CyberCorners color="var(--cyber-cyan)" size={14} thickness={3} />

        {/* Neon grid overlay */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none',
          backgroundImage: 'linear-gradient(rgba(0,245,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,245,255,0.03) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }} />

        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 80% 50%, rgba(124,58,237,0.15) 0%, transparent 60%)', zIndex: 0 }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          {/* Label with pulsing dot */}
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--cyber-cyan)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 10, fontFamily: "'Exo 2', sans-serif", display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: 'var(--cyber-cyan)', boxShadow: '0 0 8px var(--cyber-cyan)', animation: 'pulseDot 1.5s infinite' }} />
            ◈ AI CAREER SIMULATOR
          </div>
          <h1 style={{
            fontFamily: 'Orbitron, sans-serif',
            fontSize: '1.75rem', fontWeight: 900,
            background: 'linear-gradient(90deg, var(--cyber-cyan), var(--cyber-violet))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: 8, lineHeight: 1.1
          }}>
            Integrated Career Projection Portal
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.875rem', maxWidth: 580, lineHeight: 1.6, marginBottom: 20, fontFamily: "'Exo 2', sans-serif" }}>
            Simulate your growth over <strong style={{ color: 'rgba(255,255,255,0.9)' }}>{form.hours_per_day} hours/day for {form.months} months</strong>.
            The engine generates your career pipeline, customized checklists, modules, projects, and key certifications.
          </p>

          {/* Preset Buttons */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ color: 'rgba(0,245,255,0.5)', fontSize: '0.72rem', display: 'block', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, fontFamily: "'Exo 2', sans-serif" }}>Quick study presets:</label>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {[
                { label: '🌱 Part-Time', hrs: 1.5, desc: 'Casual learning' },
                { label: '🎓 Student', hrs: 3, desc: 'Steady focus' },
                { label: '⚡ Bootcamp', hrs: 5, desc: 'Immersive study' },
                { label: '🚀 Hardcore', hrs: 8, desc: 'Max acceleration' }
              ].map(p => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, hours_per_day: p.hrs }))}
                  style={{
                    background: form.hours_per_day === p.hrs
                      ? 'linear-gradient(135deg, var(--cyber-cyan), var(--cyber-violet))'
                      : 'rgba(0,245,255,0.06)',
                    color: form.hours_per_day === p.hrs ? '#000' : 'var(--cyber-cyan)',
                    border: form.hours_per_day === p.hrs ? 'none' : '1px solid rgba(0,245,255,0.2)',
                    borderRadius: 20,
                    fontSize: '0.72rem',
                    padding: '6px 14px',
                    cursor: 'pointer',
                    fontFamily: "'Exo 2', sans-serif",
                    fontWeight: 700,
                    boxShadow: form.hours_per_day === p.hrs ? '0 0 14px rgba(0,245,255,0.35)' : 'none',
                    transition: 'all 0.2s'
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sliders */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24, marginBottom: 20 }}>
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <label style={{ color: 'rgba(255,255,255,0.6)', fontFamily: "'Exo 2', sans-serif", fontSize: '0.82rem' }}>Hours per Day</label>
                <span style={{ fontSize: '0.85rem', color: 'var(--cyber-cyan)', fontWeight: 800, fontFamily: 'Orbitron, sans-serif' }}>{form.hours_per_day} hrs</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="12"
                step="0.5"
                value={form.hours_per_day}
                onChange={e => setForm(f => ({ ...f, hours_per_day: parseFloat(e.target.value) }))}
                style={{ width: '100%', accentColor: 'var(--cyber-cyan)', cursor: 'pointer', height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3 }}
              />
            </div>
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <label style={{ color: 'rgba(255,255,255,0.6)', fontFamily: "'Exo 2', sans-serif", fontSize: '0.82rem' }}>Study Duration</label>
                <span style={{ fontSize: '0.85rem', color: 'var(--cyber-violet)', fontWeight: 800, fontFamily: 'Orbitron, sans-serif' }}>{form.months} months</span>
              </div>
              <input
                type="range"
                min="1"
                max="12"
                step="1"
                value={form.months}
                onChange={e => setForm(f => ({ ...f, months: parseInt(e.target.value) }))}
                style={{ width: '100%', accentColor: 'var(--cyber-violet)', cursor: 'pointer', height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3 }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20, marginBottom: 20 }}>
            <div className="form-group">
              <label style={{ color: 'rgba(255,255,255,0.6)', fontFamily: "'Exo 2', sans-serif", fontSize: '0.82rem' }}>Career Goal</label>
              <select value={form.career_goal} onChange={e => setForm(f => ({ ...f, career_goal: e.target.value }))}
                style={{ background: '#0d1525', border: '1px solid rgba(0,245,255,0.2)', color: 'rgba(255,255,255,0.9)', borderRadius: 10, padding: '8px 14px', fontSize: '0.82rem', appearance: 'auto', outline: 'none', cursor: 'pointer', fontFamily: "'Exo 2', sans-serif" }}>
                {CAREER_OPTIONS.map(c => <option key={c} value={c} style={{ background: '#0d1525', color: 'rgba(255,255,255,0.9)' }}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label style={{ color: 'rgba(255,255,255,0.6)', fontFamily: "'Exo 2', sans-serif", fontSize: '0.82rem' }}>Current Skills</label>
              <input type="text" placeholder="Python, React, SQL..." value={form.skills}
                onChange={e => setForm(f => ({ ...f, skills: e.target.value }))}
                style={{ background: '#0d1525', border: '1px solid rgba(0,245,255,0.2)', color: 'rgba(255,255,255,0.9)', borderRadius: 10, padding: '8px 14px', fontSize: '0.82rem', outline: 'none', fontFamily: "'Exo 2', sans-serif" }} />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button
              onClick={runSimulation}
              disabled={loading}
              style={{
                minWidth: 200,
                padding: '10px 24px',
                background: 'linear-gradient(135deg, var(--cyber-cyan), var(--cyber-violet))',
                border: 'none',
                borderRadius: 10,
                color: '#000',
                fontWeight: 800,
                fontSize: '0.88rem',
                fontFamily: "'Exo 2', sans-serif",
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 20px rgba(0,245,255,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                transition: 'all 0.2s',
                opacity: loading ? 0.7 : 1,
              }}>
              {loading ? <><span className="spinner" /> Simulating...</> : <><PlayIcon style={{ fontSize: '1.2rem', marginRight: 4 }} /> Run Growth Engine</>}
            </button>
            <div style={{ fontSize: '0.75rem', color: 'rgba(0,245,255,0.5)', fontFamily: "'Exo 2', sans-serif" }}>
              Total Commitment: <strong style={{ color: 'rgba(0,245,255,0.85)' }}>{totalHours.toFixed(0)} study hours</strong>
            </div>
          </div>
        </div>
      </motion.div>

      {loading && <SimulationMatrixLoader />}

      {simError && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            padding: '16px 20px',
            borderRadius: 12,
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.25)',
            color: '#f87171',
            fontSize: '0.82rem',
            lineHeight: 1.6,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10,
          }}
        >
          <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>⚠️</span>
          <div>
            <div style={{ fontWeight: 700, marginBottom: 4, fontFamily: "'Exo 2', sans-serif" }}>Simulation Error</div>
            <div style={{ color: 'rgba(255,255,255,0.6)', fontFamily: "'Exo 2', sans-serif" }}>{simError}</div>
            <div style={{ marginTop: 8, fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', fontFamily: "'Exo 2', sans-serif" }}>
              💡 Tip: Make sure the backend is running at <code>http://localhost:8000</code> and your <code>GROQ_API_KEY</code> is set in the <code>.env</code> file.
            </div>
          </div>
        </motion.div>
      )}

      {result && (
        <>
          {/* ── Summary Stat Cards ── */}
          <motion.div {...fadeUp(0.05)} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14 }}>
            {[
              { label: 'Job Readiness', value: `${fs.job_readiness || 0}%`, icon: '🎯', color: 'var(--cyber-cyan)' },
              { label: 'Skills Gained', value: (fs.skills_gained || []).length, icon: '⚡', color: 'var(--cyber-orange)' },
              { label: 'Projects Built', value: (fs.projects_portfolio || []).length, icon: '🛠️', color: 'var(--cyber-violet)' },
              { label: 'Target Roles', value: (fs.expected_job_roles || []).length, icon: '💼', color: 'var(--cyber-blue)' },
              { label: 'Study Hours', value: totalHours.toFixed(0), icon: '⏱️', color: 'var(--cyber-green)' },
            ].map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                style={{
                  background: 'rgba(6,10,22,0.88)',
                  backdropFilter: 'blur(20px)',
                  border: `1px solid ${s.color}25`,
                  borderRadius: 14,
                  padding: '16px',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: `0 0 18px ${s.color}10`,
                }}
              >
                {/* radial glow orb */}
                <div style={{ position: 'absolute', top: -20, right: -20, width: 80, height: 80, borderRadius: '50%', background: `radial-gradient(circle, ${s.color}20 0%, transparent 70%)`, pointerEvents: 'none' }} />
                <CyberCorners color={s.color} size={7} thickness={1} />
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: 2, background: `linear-gradient(90deg, transparent, ${s.color}, transparent)` }} />
                <div style={{ fontSize: '1.4rem', marginBottom: 8 }}>{s.icon}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 900, color: s.color, fontFamily: 'Orbitron, sans-serif', lineHeight: 1 }}>{s.value}</div>
                <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)', marginTop: 4, fontFamily: "'Exo 2', sans-serif", fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
              </motion.div>
            ))}
          </motion.div>

          {/* ── HUD Tab Strip ── */}
          <div style={{
            display: 'flex', gap: 4, flexWrap: 'wrap',
            background: 'rgba(4,8,18,0.9)',
            backdropFilter: 'blur(16px)',
            padding: 4,
            borderRadius: 12,
            border: '1px solid rgba(0,245,255,0.12)',
            alignSelf: 'flex-start'
          }}>
            {[
              { key: 'pipeline', label: '⚡ Career Pipeline' },
              { key: 'roadmap', label: '🗺️ Interactive Roadmap' },
              { key: 'study_guide', label: '📚 Study & Practice Guide' },
              { key: 'certifications', label: '🎓 Certifications' },
              { key: 'reasoning', label: '💡 Trajectory Analysis' },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                style={{
                  fontSize: '0.78rem',
                  padding: '7px 14px',
                  borderRadius: 9,
                  border: 'none',
                  cursor: 'pointer',
                  fontFamily: "'Exo 2', sans-serif",
                  fontWeight: 700,
                  transition: 'all 0.2s',
                  background: tab === t.key
                    ? 'linear-gradient(135deg, var(--cyber-cyan), var(--cyber-violet))'
                    : 'transparent',
                  color: tab === t.key ? '#000' : 'rgba(0,245,255,0.6)',
                  boxShadow: tab === t.key
                    ? '0 0 14px rgba(0,245,255,0.3)'
                    : 'none',
                }}>
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'pipeline' && (
            <motion.div {...fadeUp(0.08)} style={{
              background: 'rgba(6,10,22,0.88)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(0,245,255,0.15)',
              borderRadius: 14,
              padding: '20px',
              position: 'relative',
            }}>
              <CyberCorners color="var(--cyber-cyan)" size={10} thickness={2} />
              <h4 style={{ fontFamily: 'Orbitron, sans-serif', marginBottom: 20, fontSize: '0.88rem', color: 'var(--cyber-cyan)', letterSpacing: '0.06em' }}>
                🚀 Career Growth Pipeline Trajectory
              </h4>
              <PipelineFlow result={result} visible={pipelineVisible} />

              <div style={{ marginTop: 24, borderTop: '1px solid rgba(0,245,255,0.08)', paddingTop: 20 }}>
                <h4 style={{ fontFamily: 'Orbitron, sans-serif', marginBottom: 14, fontSize: '0.82rem', color: 'var(--cyber-cyan)', letterSpacing: '0.05em' }}>📅 Month-by-Month Projection</h4>
                {(result.monthly_milestones || []).length > 0
                  ? <MilestoneTimeline milestones={result.monthly_milestones} />
                  : <p style={{ color: 'rgba(0,245,255,0.4)', fontSize: '0.82rem', fontFamily: "'Exo 2', sans-serif" }}>Detailed timeline projection not available.</p>}
              </div>

              {fs.salary_range && (
                <motion.div {...fadeUp(0.15)} style={{ marginTop: 20, padding: '16px 20px', background: 'rgba(0,255,136,0.06)', borderRadius: 12, border: '1px solid rgba(0,255,136,0.2)', display: 'flex', alignItems: 'center', gap: 12 }}>
                  <MoneyIcon style={{ fontSize: '1.5rem', color: 'var(--cyber-green)' }} />
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'rgba(0,255,136,0.6)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, fontFamily: "'Exo 2', sans-serif" }}>Estimated Salary Range</div>
                    <div style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '1.2rem', fontWeight: 800, color: 'var(--cyber-green)', textShadow: '0 0 12px rgba(0,255,136,0.4)' }}>{fs.salary_range}</div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

          {tab === 'roadmap' && (
            <motion.div {...fadeUp(0.05)} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0,245,255,0.15)', borderRadius: 14, padding: '18px 20px', position: 'relative' }}>
                <CyberCorners color="var(--cyber-cyan)" size={8} thickness={1} />
                <h4 style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '0.88rem', marginBottom: 6, color: 'var(--cyber-cyan)', letterSpacing: '0.05em' }}>🗺️ Your Actionable Learning Roadmap</h4>
                <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: '0.78rem', lineHeight: 1.5, fontFamily: "'Exo 2', sans-serif" }}>
                  This roadmap splits your path into 30-day, 90-day, and 180-day phases. Complete each daily task checklist to track your readiness in real time.
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <PhaseCard phaseKey="30" data={result.phase_30_days} checkedTasks={checkedTasks} toggleTask={toggleTask} />
                <PhaseCard phaseKey="90" data={result.phase_90_days} checkedTasks={checkedTasks} toggleTask={toggleTask} />
                <PhaseCard phaseKey="180" data={result.phase_180_days} checkedTasks={checkedTasks} toggleTask={toggleTask} />
              </div>

              {(fs.expected_job_roles || []).length > 0 && (
                <div style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 14, padding: '18px 20px', position: 'relative' }}>
                  <CyberCorners color="var(--cyber-green)" size={8} thickness={1} />
                  <h4 style={{ fontFamily: 'Orbitron, sans-serif', marginBottom: 12, fontSize: '0.85rem', color: 'var(--cyber-green)', letterSpacing: '0.05em' }}>🎯 Job Titles to Target</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {fs.expected_job_roles.map((t, i) => (
                      <span key={i} style={{ padding: '4px 12px', borderRadius: 99, background: 'rgba(0,255,136,0.08)', color: 'var(--cyber-green)', border: '1px solid rgba(0,255,136,0.2)', fontSize: '0.75rem', fontWeight: 600, fontFamily: "'Exo 2', sans-serif" }}>{t}</span>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {tab === 'study_guide' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* Section 1: Courses & Modules */}
              <motion.div {...fadeUp(0.05)} style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0,245,255,0.2)', borderRadius: 14, padding: '20px', position: 'relative' }}>
                <CyberCorners color="var(--cyber-cyan)" size={9} thickness={2} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, borderBottom: '1px solid rgba(0,245,255,0.08)', paddingBottom: 10 }}>
                  <span style={{ fontSize: '1.4rem' }}>📚</span>
                  <div>
                    <h4 style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '0.95rem', fontWeight: 800, color: 'var(--cyber-cyan)', letterSpacing: '0.05em' }}>Courses & Modules to Study</h4>
                    <p style={{ fontSize: '0.75rem', color: 'rgba(0,245,255,0.45)', fontFamily: "'Exo 2', sans-serif" }}>Personalized curricular topics mapped to your target duration</p>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
                  {(result.courses_and_modules || []).map((course, idx) => (
                    <div key={idx} style={{ background: 'rgba(0,245,255,0.03)', padding: 16, borderRadius: 12, border: '1px solid rgba(0,245,255,0.1)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                        <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'rgba(255,255,255,0.9)', fontFamily: "'Exo 2', sans-serif" }}>{course.name}</div>
                        <span className="badge badge-info" style={{ flexShrink: 0, fontSize: '0.62rem' }}>{course.difficulty}</span>
                      </div>

                      {course.duration && (
                        <div style={{ fontSize: '0.7rem', color: 'rgba(0,245,255,0.5)', display: 'flex', alignItems: 'center', gap: 4, fontFamily: "'Exo 2', sans-serif" }}>
                          ⏱️ study time: <strong style={{ color: 'rgba(0,245,255,0.8)' }}>{course.duration}</strong>
                        </div>
                      )}

                      {course.topics && course.topics.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                          {course.topics.map((topic, i) => (
                            <span key={i} style={{ fontSize: '0.64rem', padding: '1px 6px', borderRadius: 99, background: 'rgba(0,245,255,0.07)', color: 'var(--cyber-cyan)', border: '1px solid rgba(0,245,255,0.15)', fontWeight: 500, fontFamily: "'Exo 2', sans-serif" }}>
                              {topic}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Section 2: Projects to Build */}
              <motion.div {...fadeUp(0.08)} style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(124,58,237,0.25)', borderRadius: 14, padding: '20px', position: 'relative' }}>
                <CyberCorners color="var(--cyber-violet)" size={9} thickness={2} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, borderBottom: '1px solid rgba(124,58,237,0.1)', paddingBottom: 10 }}>
                  <span style={{ fontSize: '1.4rem' }}>🛠️</span>
                  <div>
                    <h4 style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '0.95rem', fontWeight: 800, color: 'var(--cyber-violet)', letterSpacing: '0.05em' }}>Portfolio Projects to Build</h4>
                    <p style={{ fontSize: '0.75rem', color: 'rgba(124,58,237,0.6)', fontFamily: "'Exo 2', sans-serif" }}>Build real-world evidence of your learning pathway</p>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {(result.projects_to_build || []).map((project, idx) => (
                    <div key={idx} style={{ background: 'rgba(124,58,237,0.04)', padding: 16, borderRadius: 12, border: '1px solid rgba(124,58,237,0.12)', display: 'grid', gridTemplateColumns: '1fr auto', gap: 14 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'rgba(255,255,255,0.9)', marginBottom: 4, fontFamily: "'Exo 2', sans-serif" }}>{project.title}</div>
                        <p style={{ fontSize: '0.76rem', color: 'rgba(255,255,255,0.55)', lineHeight: 1.4, fontFamily: "'Exo 2', sans-serif" }}>{project.description}</p>

                        {project.skills_applied && project.skills_applied.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                            {project.skills_applied.map((skill, i) => (
                              <span key={i} style={{ fontSize: '0.64rem', padding: '1px 6px', borderRadius: 4, background: 'rgba(124,58,237,0.08)', color: 'var(--cyber-violet)', border: '1px solid rgba(124,58,237,0.2)', fontFamily: "'Exo 2', sans-serif" }}>
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'flex-start' }}>
                        <span className="badge badge-accent" style={{ fontSize: '0.62rem' }}>{project.complexity}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Section 3: Sources to Refer */}
              <motion.div {...fadeUp(0.11)} style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 14, padding: '20px', position: 'relative' }}>
                <CyberCorners color="var(--cyber-green)" size={9} thickness={2} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, borderBottom: '1px solid rgba(0,255,136,0.08)', paddingBottom: 10 }}>
                  <span style={{ fontSize: '1.4rem' }}>🔗</span>
                  <div>
                    <h4 style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '0.95rem', fontWeight: 800, color: 'var(--cyber-green)', letterSpacing: '0.05em' }}>Sources & Resources to Refer</h4>
                    <p style={{ fontSize: '0.75rem', color: 'rgba(0,255,136,0.5)', fontFamily: "'Exo 2', sans-serif" }}>Handpicked learning documentation, courses, and tools</p>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
                  {(result.sources_to_refer || []).map((source, idx) => (
                    <div key={idx} style={{ background: 'rgba(0,255,136,0.03)', padding: 14, borderRadius: 12, border: '1px solid rgba(0,255,136,0.1)', display: 'flex', flexDirection: 'column', gap: 8, justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          <span style={{ fontSize: '0.6rem', padding: '1px 5px', borderRadius: 99, background: 'rgba(0,255,136,0.1)', color: 'var(--cyber-green)', fontWeight: 600, textTransform: 'uppercase', fontFamily: "'Exo 2', sans-serif" }}>
                            {source.type}
                          </span>
                          <span style={{ fontSize: '0.66rem', color: 'rgba(255,255,255,0.5)', fontFamily: "'Exo 2', sans-serif" }}>{source.focus}</span>
                        </div>
                        <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'rgba(255,255,255,0.9)', marginBottom: 4, fontFamily: "'Exo 2', sans-serif" }}>
                          {source.resource}
                        </div>
                        <p style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.5)', fontFamily: "'Exo 2', sans-serif" }}>
                          <strong>Platform:</strong> {source.link_or_platform}
                        </p>
                      </div>

                      {renderResourceLink(source.resource)}
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>
          )}

          {tab === 'certifications' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0,245,255,0.15)', borderRadius: 14, padding: '18px 20px', position: 'relative' }}>
                <CyberCorners color="var(--cyber-cyan)" size={8} thickness={1} />
                <h4 style={{ fontFamily: 'Orbitron, sans-serif', fontSize: '0.88rem', marginBottom: 6, color: 'var(--cyber-cyan)', letterSpacing: '0.05em' }}>🎓 Recommended Industry Certifications</h4>
                <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: '0.78rem', lineHeight: 1.5, fontFamily: "'Exo 2', sans-serif" }}>
                  These certifications are highly valued by employers for {form.career_goal}. Completing them will significantly boost your credibility and resume score.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
                {(result.certifications || []).length === 0 ? (
                  <p style={{ color: 'rgba(0,245,255,0.4)', fontSize: '0.8rem', fontFamily: "'Exo 2', sans-serif" }}>No specific certifications recommended for this commitment level.</p>
                ) : result.certifications.map((c, i) => <CertCard key={i} cert={c} i={i} />)}
              </div>
            </motion.div>
          )}

          {tab === 'reasoning' && (
            <motion.div {...fadeUp(0.05)} style={{ background: 'rgba(6,10,22,0.88)', backdropFilter: 'blur(20px)', border: '1px solid rgba(249,115,22,0.2)', borderRadius: 14, padding: '20px', position: 'relative' }}>
              <CyberCorners color="var(--cyber-orange)" size={9} thickness={2} />
              <h4 style={{ fontFamily: 'Orbitron, sans-serif', marginBottom: 16, fontSize: '0.88rem', color: 'var(--cyber-orange)', letterSpacing: '0.05em' }}>💡 Why This Prediction?</h4>
              <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.8, marginBottom: 16, fontFamily: "'Exo 2', sans-serif" }}>{result.reasoning || result.simulation_summary}</p>

              {(result.acceleration_tips || []).length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.78rem', marginBottom: 8, color: 'var(--cyber-green)', display: 'flex', alignItems: 'center', gap: 6, fontFamily: "'Exo 2', sans-serif" }}>
                    <CheckIcon style={{ fontSize: '0.9rem' }} /> Acceleration Tips
                  </div>
                  {result.acceleration_tips.map((t, i) => (
                    <div key={i} style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)', padding: '4px 0', paddingLeft: 14, fontFamily: "'Exo 2', sans-serif" }}>• {t}</div>
                  ))}
                </div>
              )}

              {(result.risk_factors || []).length > 0 && (
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.78rem', marginBottom: 8, color: '#f87171', display: 'flex', alignItems: 'center', gap: 6, fontFamily: "'Exo 2', sans-serif" }}>
                    <WarnIcon style={{ fontSize: '0.9rem' }} /> Potential Risk Factors
                  </div>
                  {result.risk_factors.map((t, i) => (
                    <div key={i} style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)', padding: '4px 0', paddingLeft: 14, fontFamily: "'Exo 2', sans-serif" }}>• {t}</div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </>
      )}

      <style>{`
        @keyframes pulseDot {
          0%, 100% { opacity: 1; box-shadow: 0 0 8px var(--cyber-cyan); }
          50% { opacity: 0.4; box-shadow: 0 0 3px var(--cyber-cyan); }
        }
      `}</style>
    </div>
  )
}
