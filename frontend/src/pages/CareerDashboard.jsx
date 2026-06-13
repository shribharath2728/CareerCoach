import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { analyzeProfile } from '../services/api'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts'
import { MdAutoGraph, MdPsychology, MdTrendingUp, MdCheckCircle, MdRadioButtonUnchecked } from 'react-icons/md'

const CAREER_OPTIONS = [
  'AI Engineer', 'Data Scientist', 'Full Stack Developer', 'Cloud Engineer',
  'Cybersecurity Analyst', 'DevOps Engineer', 'Product Manager', 'UI/UX Designer'
]

function ScoreRing({ score, label, color, size = 120 }) {
  const r = size / 2 - 10
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
        <motion.circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color || 'var(--primary)'} strokeWidth={10} strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.4, ease: 'easeOut', delay: 0.2 }}
        />
        <text x={size / 2} y={size / 2 + 7} textAnchor="middle"
          fill="var(--text-primary)"
          style={{ fontSize: size > 100 ? 22 : 16, fontWeight: 800, fontFamily: 'var(--font-heading)', transform: 'rotate(90deg)', transformOrigin: `${size / 2}px ${size / 2}px` }}>
          {score}%
        </text>
      </svg>
      <span style={{ fontSize: '0.72rem', fontWeight: 600, color: color || 'var(--primary)', textAlign: 'center', maxWidth: size }}>{label}</span>
    </div>
  )
}

function ComponentScoreBar({ label, score, max, color }) {
  const pct = Math.round((score / max) * 100)
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color }}>{score}/{max}</span>
      </div>
      <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 99, overflow: 'hidden' }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
          style={{ height: '100%', background: color, borderRadius: 99 }}
        />
      </div>
    </div>
  )
}

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, delay, ease: [0.4, 0, 0.2, 1] },
})

export default function CareerDashboard() {
  const { agentProfile, lastAnalysis, storeAnalysisResult, careerMatch, skillGaps, roadmap, setActivePage } = useApp()
  const [loading, setLoading] = useState(false)
  const [localProfile, setLocalProfile] = useState({
    name: agentProfile?.name || '',
    career_goal: agentProfile?.career_goal || 'AI Engineer',
    skills: agentProfile?.skills?.join(', ') || '',
    certifications: agentProfile?.certifications?.join(', ') || '',
    projects: agentProfile?.projects?.join(', ') || '',
    cgpa: agentProfile?.cgpa || '',
    year: agentProfile?.year || '',
    branch: agentProfile?.branch || '',
  })
  const [analysis, setAnalysis] = useState(lastAnalysis)

  const runAnalysis = useCallback(async () => {
    if (!localProfile.career_goal) return
    setLoading(true)
    try {
      const profile = {
        ...localProfile,
        skills: localProfile.skills.split(',').map(s => s.trim()).filter(Boolean),
        certifications: localProfile.certifications.split(',').map(s => s.trim()).filter(Boolean),
        projects: localProfile.projects.split(',').map(s => s.trim()).filter(Boolean),
        career_goal: localProfile.career_goal,
      }
      const result = await analyzeProfile(profile)
      storeAnalysisResult(result)
      setAnalysis(result)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [localProfile, storeAnalysisResult])

  useEffect(() => {
    if (!analysis && agentProfile?.career_goal) runAnalysis()
  }, [])

  const conf = analysis?.confidence_score || careerMatch || {}
  const gaps = analysis?.skill_gaps || skillGaps || {}
  const profileAnalysis = analysis?.profile_analysis || {}
  const rd = analysis?.roadmap || roadmap || {}

  // Radar data
  const componentScores = conf.component_scores || {}
  const radarData = Object.entries(componentScores).map(([key, val]) => ({
    subject: val.label || key,
    score: Math.round((val.score / val.max) * 100),
    fullMark: 100,
  }))

  // Bar chart data for skill gaps
  const presentSkills = (gaps.current_skills_present || []).slice(0, 8)
  const missingSkills = (gaps.missing_critical_skills || []).slice(0, 8)
  const skillBarData = [
    ...presentSkills.map(s => ({ name: s.length > 12 ? s.slice(0, 12) + '…' : s, status: 'have', value: 1 })),
    ...missingSkills.map(s => ({ name: s.length > 12 ? s.slice(0, 12) + '…' : s, status: 'missing', value: 1 })),
  ]

  const matchPct = conf.overall_score || gaps.match_percentage || 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* Header */}
      <motion.div {...fadeUp(0)} style={{
        background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent) 60%, #7C3AED 100%)',
        borderRadius: 20, padding: '24px 28px', color: 'white', position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', right: 20, top: -20, fontSize: '7rem', opacity: 0.07 }}>📊</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', fontWeight: 800, color: 'white', marginBottom: 6 }}>
              Career Match Dashboard
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.875rem', maxWidth: 480 }}>
              AI-powered career analysis · Skill gap visualization · Confidence scoring
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <select
              value={localProfile.career_goal}
              onChange={e => setLocalProfile(p => ({ ...p, career_goal: e.target.value }))}
              style={{ background: 'var(--surface-3)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', borderRadius: 10, padding: '8px 14px', fontSize: '0.82rem', appearance: 'auto', outline: 'none', cursor: 'pointer' }}
            >
              {CAREER_OPTIONS.map(c => <option key={c} value={c} style={{ background: 'var(--surface-2)', color: 'var(--text-primary)' }}>{c}</option>)}
            </select>
            <button className="btn" onClick={runAnalysis} disabled={loading}
              style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}>
              {loading ? <span className="spinner" /> : '🔄 Analyze'}
            </button>
          </div>
        </div>
      </motion.div>

      {/* Quick Profile Input */}
      {!analysis && (
        <motion.div {...fadeUp(0.05)} className="card" style={{ border: '1px solid rgba(99,102,241,0.3)' }}>
          <h3 style={{ marginBottom: 14, fontFamily: 'var(--font-heading)' }}>📋 Enter Your Profile for Analysis</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {[
              { key: 'name', label: 'Name', placeholder: 'Your name' },
              { key: 'cgpa', label: 'CGPA', placeholder: '8.5' },
              { key: 'year', label: 'Year', placeholder: '3rd Year' },
              { key: 'branch', label: 'Branch', placeholder: 'Computer Science' },
            ].map(f => (
              <div key={f.key} className="form-group">
                <label>{f.label}</label>
                <input type="text" placeholder={f.placeholder} value={localProfile[f.key]} onChange={e => setLocalProfile(p => ({ ...p, [f.key]: e.target.value }))} />
              </div>
            ))}
            {[
              { key: 'skills', label: 'Skills (comma separated)', placeholder: 'Python, React, SQL...' },
              { key: 'projects', label: 'Projects (comma separated)', placeholder: 'Portfolio site, Chat app...' },
            ].map(f => (
              <div key={f.key} className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>{f.label}</label>
                <input type="text" placeholder={f.placeholder} value={localProfile[f.key]} onChange={e => setLocalProfile(p => ({ ...p, [f.key]: e.target.value }))} />
              </div>
            ))}
          </div>
          <button className="btn btn-primary" onClick={runAnalysis} disabled={loading} style={{ marginTop: 14, width: '100%' }}>
            {loading ? <><span className="spinner" /> Analyzing...</> : '🚀 Run Full Analysis'}
          </button>
        </motion.div>
      )}

      {analysis && (
        <>
          {/* Score Cards Row */}
          <motion.div {...fadeUp(0.06)} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '24px 20px' }}>
              <ScoreRing score={matchPct} label="Career Match" color={conf.color || 'var(--primary)'} size={120} />
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center' }}>{conf.label || 'Match Score'}</div>
            </div>
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '24px 20px' }}>
              <ScoreRing score={profileAnalysis.industry_readiness_score || 50} label="Industry Readiness" color="var(--info)" size={120} />
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center' }}>{profileAnalysis.readiness_level || 'Developing'}</div>
            </div>
            <div className="card" style={{ flex: 1, padding: '20px' }}>
              <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.88rem' }}>Score Breakdown</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.entries(componentScores).map(([key, val]) => (
                  <ComponentScoreBar
                    key={key} label={val.label || key}
                    score={val.score} max={val.max}
                    color={key === 'skills' ? 'var(--primary)' : key === 'projects' ? 'var(--success)' : key === 'certifications' ? 'var(--warning)' : 'var(--info)'}
                  />
                ))}
              </div>
            </div>
          </motion.div>

          {/* Charts Row */}
          <motion.div {...fadeUp(0.1)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Radar Chart */}
            {radarData.length > 0 && (
              <div className="card">
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 16, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <MdAutoGraph style={{ color: 'var(--primary)' }} /> Skill Coverage Radar
                </h4>
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="rgba(255,255,255,0.06)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar name="Score" dataKey="score" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.2} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Skill Gap Bar */}
            <div className="card">
              <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 16, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                <MdPsychology style={{ color: 'var(--accent)' }} /> Skill Gap Analysis
              </h4>
              <div style={{ display: 'flex', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--success)', marginBottom: 8, letterSpacing: '0.08em', textTransform: 'uppercase' }}>✅ Have ({presentSkills.length})</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                    {presentSkills.map(s => (
                      <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--success)', flexShrink: 0 }} />
                        {s}
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ width: 1, background: 'var(--glass-border)' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--danger)', marginBottom: 8, letterSpacing: '0.08em', textTransform: 'uppercase' }}>❌ Missing ({missingSkills.length})</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                    {missingSkills.map(s => (
                      <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--danger)', flexShrink: 0 }} />
                        {s}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Strengths & Weaknesses */}
          <motion.div {...fadeUp(0.14)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="card">
              <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.88rem', color: 'var(--success)' }}>💪 Strengths</h4>
              {(profileAnalysis.strengths || []).map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '6px 0', borderBottom: '1px solid var(--glass-border)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  <MdCheckCircle style={{ color: 'var(--success)', flexShrink: 0, marginTop: 1 }} />
                  {s}
                </div>
              ))}
            </div>
            <div className="card">
              <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.88rem', color: 'var(--warning)' }}>🔧 Areas to Improve</h4>
              {(profileAnalysis.weaknesses || []).map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, padding: '6px 0', borderBottom: '1px solid var(--glass-border)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  <MdRadioButtonUnchecked style={{ color: 'var(--warning)', flexShrink: 0, marginTop: 1 }} />
                  {s}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Reasoning */}
          {(analysis?.reasoning_chain || []).length > 0 && (
            <motion.div {...fadeUp(0.18)} className="card" style={{ border: '1px solid rgba(245,158,11,0.2)' }}>
              <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 14, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                💡 Agent Reasoning Chain — Why These Recommendations?
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {(analysis.reasoning_chain || []).map((r, i) => (
                  <motion.div key={i} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}
                    style={{ display: 'flex', gap: 12, padding: '10px 14px', background: 'rgba(245,158,11,0.04)', borderRadius: 10, border: '1px solid rgba(245,158,11,0.1)' }}>
                    <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--warning)', color: 'white', fontSize: '0.65rem', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{r.step}</div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{r.thought}</div>
                      {r.conclusion && <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--warning)', marginTop: 4 }}>→ {r.conclusion}</div>}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* CTA */}
          <motion.div {...fadeUp(0.2)} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => setActivePage('roadmap')}>🗺ï¸ View Full Roadmap</button>
            <button className="btn btn-secondary" onClick={() => setActivePage('simulation')}>🚀 Run Career Simulation</button>
            <button className="btn btn-secondary" onClick={() => setActivePage('resume_analyzer')}>📄 Analyze Resume</button>
            <button className="btn btn-secondary" onClick={() => setAnalysis(null)}>🔄 Re-analyze Profile</button>
          </motion.div>
        </>
      )}
    </div>
  )
}
