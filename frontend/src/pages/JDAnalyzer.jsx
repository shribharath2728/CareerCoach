import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { analyzeJD } from '../services/api'
import { MdFindInPage, MdAutoGraph, MdCheckCircle, MdWarning } from 'react-icons/md'

export default function JDAnalyzer() {
  const { user, addToast } = useApp()
  const [jdText, setJdText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleAnalyze = async () => {
    if (!jdText.trim()) {
      addToast('Please paste a job description first', 'warning')
      return
    }

    setLoading(true)
    setResult(null)
    try {
      const data = await analyzeJD(user.id, { jd_text: jdText })
      setResult(data)
      addToast('Analysis complete!', 'success')
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to analyze JD', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2><MdFindInPage /> JD Match Analyzer</h2>
        <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading || !jdText.trim()}>
          {loading ? <span className="spinner" /> : <MdAutoGraph />} Analyze Match
        </button>
      </div>

      <div style={{ display: 'flex', gap: 20, flex: 1, overflow: 'hidden' }}>
        {/* Input panel */}
        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', background: 'var(--bg-tertiary)' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Paste the Job Description below. We will compare it with your saved Resume.
            </p>
          </div>
          <textarea 
            placeholder="Paste job description here..."
            value={jdText}
            onChange={e => setJdText(e.target.value)}
            style={{
               flex: 1, resize: 'none', border: 'none', padding: '20px',
               fontSize: '1rem', background: 'var(--bg-card)', 
               color: 'var(--text-primary)', outline: 'none'
            }}
          />
        </div>

        {/* Results panel */}
        <div style={{ width: 350, display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', paddingRight: 4 }}>
          <AnimatePresence>
            {!result && !loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="empty-state" style={{ height: '100%', justifyContent: 'center' }}>
                <div className="empty-icon">📝</div>
                <h3>Ready to Analyze</h3>
                <p>Paste a JD and click Analyze to see your ATS match score.</p>
              </motion.div>
            )}

            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="empty-state" style={{ height: '100%', justifyContent: 'center' }}>
                <div className="spinner" style={{ width: 40, height: 40, marginBottom: 16 }} />
                <h3>Analyzing your resume...</h3>
                <p>Using AI to extract keywords and evaluate match percentage.</p>
              </motion.div>
            )}

            {result && !loading && (
              <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
                {/* Match Score */}
                <div className="card" style={{ textAlign: 'center', padding: '30px 20px' }}>
                  <h4 style={{ color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1, fontSize: '0.8rem' }}>Match Score</h4>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    {result.match_percentage >= 75 ? (
                      <MdCheckCircle size={48} color="var(--success)" />
                    ) : (
                      <MdWarning size={48} color="var(--warning)" />
                    )}
                    <span style={{ fontSize: '3.5rem', fontWeight: 800, fontFamily: 'Outfit', color: result.match_percentage >= 75 ? 'var(--success)' : 'var(--warning)' }}>
                      {result.match_percentage}%
                    </span>
                  </div>
                </div>

                {/* Missing Keywords */}
                <div className="card" style={{ marginTop: 16 }}>
                  <h4 style={{ marginBottom: 12 }}>Missing Keywords</h4>
                  {result.missing_keywords && result.missing_keywords.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {result.missing_keywords.map((kw, i) => (
                        <span key={i} className="badge badge-danger" style={{ fontSize: '0.85rem' }}>{kw}</span>
                      ))}
                    </div>
                  ) : (
                     <p style={{ color: 'var(--success)', fontSize: '0.9rem' }}>Looks perfect, no significant keywords missing!</p>
                  )}
                </div>

                {/* Suggestions */}
                <div className="card" style={{ marginTop: 16, background: 'var(--bg-tertiary)' }}>
                  <h4 style={{ marginBottom: 12 }}>Suggestions</h4>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: 'var(--text-secondary)' }}>
                    {result.suggestions}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  )
}
