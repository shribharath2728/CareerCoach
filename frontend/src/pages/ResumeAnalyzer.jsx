import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { uploadResumePDF, analyzeResumeText } from '../services/api'
import { MdUpload, MdDocumentScanner, MdCheckCircle, MdCancel, MdLightbulb } from 'react-icons/md'

const CAREER_OPTIONS = [
  'AI Engineer', 'Data Scientist', 'Full Stack Developer', 'Cloud Engineer',
  'Cybersecurity Analyst', 'DevOps Engineer', 'Product Manager', 'UI/UX Designer'
]

function ATSRing({ score }) {
  const r = 54
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 80 ? 'var(--success)' : score >= 60 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
      <svg width="130" height="130" viewBox="0 0 130 130" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="65" cy="65" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="12" />
        <motion.circle cx="65" cy="65" r={r} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
        <text x="65" y="72" textAnchor="middle" fill="var(--text-primary)"
          style={{ fontSize: 26, fontWeight: 900, fontFamily: 'var(--font-heading)', transform: 'rotate(90deg)', transformOrigin: '65px 65px' }}>
          {score}
        </text>
      </svg>
      <div>
        <div style={{ textAlign: 'center', fontSize: '0.88rem', fontWeight: 700, color, fontFamily: 'var(--font-heading)' }}>
          {score >= 80 ? '🟢 Strong ATS Score' : score >= 60 ? '🟡 Moderate Score' : '🔴 Needs Improvement'}
        </div>
        <div style={{ textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>ATS Compatibility Score</div>
      </div>
    </div>
  )
}

function ScoreRow({ label, score, max = 10 }) {
  const pct = (score / max) * 100
  const color = pct >= 70 ? 'var(--success)' : pct >= 40 ? 'var(--warning)' : 'var(--danger)'
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color }}>{score}/{max}</span>
      </div>
      <div style={{ height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 99 }}>
        <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.9, ease: 'easeOut', delay: 0.2 }}
          style={{ height: '100%', background: color, borderRadius: 99 }} />
      </div>
    </div>
  )
}

const fadeUp = (d = 0) => ({ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4, delay: d } })

export default function ResumeAnalyzer() {
  const { agentProfile } = useApp()
  const [careerGoal, setCareerGoal] = useState(agentProfile?.career_goal || 'AI Engineer')
  const [resumeText, setResumeText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [fileName, setFileName] = useState(null)
  const [mode, setMode] = useState('upload') // 'upload' | 'paste'
  const fileRef = useRef(null)

  const analyze = useCallback(async (file = null) => {
    setLoading(true)
    setResult(null)
    try {
      let res
      if (file) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('career_goal', careerGoal)
        res = await uploadResumePDF(formData)
      } else {
        if (!resumeText.trim()) return
        res = await analyzeResumeText({ resume_text: resumeText, career_goal: careerGoal })
      }
      setResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [careerGoal, resumeText])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file?.type === 'application/pdf') {
      setFileName(file.name)
      analyze(file)
    }
  }, [analyze])

  const onFileChange = (e) => {
    const file = e.target.files[0]
    if (file) { setFileName(file.name); analyze(file) }
  }

  const sections = result?.section_scores || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* Header */}
      <motion.div {...fadeUp(0)} style={{
        background: 'linear-gradient(135deg, #1E3A5F 0%, #1a1a2e 50%, #16213e 100%)',
        borderRadius: 20, padding: '24px 28px', position: 'relative', overflow: 'hidden',
        border: '1px solid rgba(59,130,246,0.3)',
      }}>
        <div style={{ position: 'absolute', right: 20, top: -10, fontSize: '7rem', opacity: 0.06 }}>📄</div>
        <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', fontWeight: 800, color: 'white', marginBottom: 6 }}>Resume Analyzer</h1>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.875rem', marginBottom: 16 }}>
          Upload your PDF resume — the agent extracts skills, detects missing keywords, calculates ATS score & suggests improvements.
        </p>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', textTransform: 'none', letterSpacing: 0, fontWeight: 400 }}>Target Role:</label>
          <select value={careerGoal} onChange={e => setCareerGoal(e.target.value)}
            style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.25)', color: 'white', borderRadius: 10, padding: '8px 14px', fontSize: '0.82rem' }}>
            {CAREER_OPTIONS.map(c => <option key={c} value={c} style={{ color: '#111' }}>{c}</option>)}
          </select>
          <div style={{ display: 'flex', gap: 4 }}>
            {['upload', 'paste'].map(m => (
              <button key={m} className={`btn btn-sm ${mode === m ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setMode(m)} style={{ textTransform: 'capitalize', fontSize: '0.78rem', minHeight: 34 }}>
                {m === 'upload' ? '📤 Upload PDF' : '📝 Paste Text'}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Upload Zone */}
      <motion.div {...fadeUp(0.05)}>
        {mode === 'upload' ? (
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            style={{
              border: `2px dashed ${dragOver ? 'var(--primary)' : 'var(--glass-border)'}`,
              borderRadius: 16, padding: '48px 32px', textAlign: 'center', cursor: 'pointer',
              background: dragOver ? 'rgba(99,102,241,0.05)' : 'var(--surface)',
              transition: 'all 0.25s ease',
            }}
          >
            <input ref={fileRef} type="file" accept=".pdf" onChange={onFileChange} style={{ display: 'none' }} />
            <motion.div animate={dragOver ? { scale: 1.1 } : { scale: 1 }} style={{ fontSize: '3rem', marginBottom: 14 }}>
              {loading ? 'â³' : fileName ? '✅' : '📄'}
            </motion.div>
            <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '1rem', marginBottom: 6 }}>
              {loading ? 'Analyzing...' : fileName ? fileName : 'Drop your PDF resume here'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {loading ? 'AI is reading your resume' : 'or click to browse · PDF only'}
            </div>
            {!loading && (
              <button className="btn btn-primary" style={{ marginTop: 20, pointerEvents: 'none' }}>
                <MdUpload /> Upload Resume
              </button>
            )}
          </div>
        ) : (
          <div className="card">
            <div className="form-group">
              <label>Paste Resume Text</label>
              <textarea value={resumeText} onChange={e => setResumeText(e.target.value)}
                placeholder="Paste the full text of your resume here..."
                style={{ minHeight: 200, fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }} />
            </div>
            <button className="btn btn-primary" onClick={() => analyze()} disabled={loading || !resumeText.trim()} style={{ marginTop: 12, width: '100%' }}>
              {loading ? <><span className="spinner" /> Analyzing...</> : '🔍 Analyze Resume'}
            </button>
          </div>
        )}
      </motion.div>

      {/* Results */}
      {result && (
        <AnimatePresence>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

            {/* ATS Score + Section Scores */}
            <motion.div {...fadeUp(0)} style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 24, alignItems: 'center' }} className="card">
              <ATSRing score={result.ats_score || 0} />
              <div>
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 14, fontSize: '0.88rem' }}>Section Scores</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {Object.entries(sections).map(([k, v]) => (
                    <ScoreRow key={k} label={k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} score={v} max={k === 'experience' ? 30 : k === 'education' ? 20 : k === 'skills' ? 25 : k === 'projects' ? 15 : 10} />
                  ))}
                </div>
                <div style={{ marginTop: 10, padding: '8px 12px', background: 'rgba(99,102,241,0.08)', borderRadius: 8, fontSize: '0.75rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                  {result.overall_verdict || result.action_verb_quality && `Action Verb Quality: ${result.action_verb_quality}`}
                </div>
              </div>
            </motion.div>

            {/* Extracted Skills & Missing Keywords */}
            <motion.div {...fadeUp(0.06)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div className="card">
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.85rem', color: 'var(--success)' }}>✅ Skills Detected</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {(result.extracted_skills || []).map(s => (
                    <span key={s} style={{ fontSize: '0.7rem', padding: '2px 9px', borderRadius: 99, background: 'rgba(16,185,129,0.1)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.2)', fontWeight: 500 }}>{s}</span>
                  ))}
                  {(result.extracted_skills || []).length === 0 && <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>No skills detected</span>}
                </div>
              </div>
              <div className="card">
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.85rem', color: 'var(--danger)' }}>❌ Missing Keywords</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {(result.missing_keywords || []).map(s => (
                    <span key={s} style={{ fontSize: '0.7rem', padding: '2px 9px', borderRadius: 99, background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.2)', fontWeight: 500 }}>{s}</span>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Improvements */}
            {(result.improvements || []).length > 0 && (
              <motion.div {...fadeUp(0.1)} className="card" style={{ border: '1px solid rgba(245,158,11,0.2)' }}>
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 14, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <MdLightbulb style={{ color: 'var(--warning)' }} /> Improvement Suggestions
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.improvements.map((imp, i) => (
                    <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}
                      style={{ padding: '10px 14px', background: 'rgba(245,158,11,0.04)', borderRadius: 10, border: '1px solid rgba(245,158,11,0.12)' }}>
                      <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--warning)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{imp.section || 'General'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 4 }}>â— {imp.issue}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: 600 }}>✅ Fix: {imp.fix}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Missing Sections */}
            {(result.missing_sections || []).length > 0 && (
              <motion.div {...fadeUp(0.14)} className="card">
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.88rem' }}>📋 Missing Sections to Add</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {result.missing_sections.map(s => (
                    <span key={s} style={{ fontSize: '0.78rem', padding: '5px 14px', borderRadius: 99, background: 'rgba(239,68,68,0.08)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.2)', fontWeight: 600 }}>+ {s}</span>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Rewrite Suggestions */}
            {(result.rewrite_suggestions || []).length > 0 && (
              <motion.div {...fadeUp(0.18)} className="card" style={{ border: '1px solid rgba(99,102,241,0.2)' }}>
                <h4 style={{ fontFamily: 'var(--font-heading)', marginBottom: 12, fontSize: '0.88rem', color: 'var(--primary)' }}>✍️ Rewrite Suggestions</h4>
                {result.rewrite_suggestions.map((s, i) => (
                  <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--glass-border)', fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>• {s}</div>
                ))}
              </motion.div>
            )}

          </div>
        </AnimatePresence>
      )}
    </div>
  )
}
