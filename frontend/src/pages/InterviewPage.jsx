import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { startInterview, generateQuestion, submitAnswer } from '../services/api'
import { useVoiceInput, speak, stopSpeaking } from '../hooks/useVoice'
import {
  MdMic, MdMicOff, MdStop, MdArrowForward, MdRefresh,
  MdVolumeUp, MdVolumeOff, MdCheckCircle, MdClose, MdCameraAlt
} from 'react-icons/md'
import EvaluationPanel from '../components/EvaluationPanel'

const ROLES = ['Software Engineer', 'Frontend Developer', 'Backend Engineer', 'Full Stack Developer',
               'Data Scientist', 'ML Engineer', 'DevOps Engineer', 'Product Manager', 'UX Designer', 'Data Analyst']
const TYPES = ['technical', 'behavioral', 'system_design', 'hr', 'mixed']
const DIFFICULTIES = ['easy', 'medium', 'hard']

// ---------- Setup Form ----------
function SetupForm({ onStart }) {
  const { user }  = useApp()
  const [form, setForm] = useState({ role: ROLES[0], interview_type: 'technical', difficulty: 'medium' })
  const [loading, setLoading] = useState(false)
  const { addToast } = useApp()
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleStart = async () => {
    setLoading(true)
    try {
      const session = await startInterview({ user_id: user.id, ...form })
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
      style={{ maxWidth: 600, margin: '0 auto' }}
    >
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{ fontSize: '2.8rem', marginBottom: 10 }}>🎯</div>
        <h2 style={{ fontFamily: 'Outfit', fontSize: '1.5rem' }}>Configure Your Interview</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 6 }}>
          Customize your practice session and let the AI challenge you.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div className="form-group">
          <label>Target Role</label>
          <select value={form.role} onChange={e => set('role', e.target.value)}>
            {ROLES.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>

        <div className="form-group">
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

        <button
          className="btn btn-primary btn-lg"
          style={{ justifyContent: 'center', marginTop: 8 }}
          onClick={handleStart}
          disabled={loading}
        >
          {loading ? <><span className="spinner" />Starting…</> : '🚀 Start Interview'}
        </button>
      </div>
    </motion.div>
  )
}

// ---------- Interview Session ----------
function InterviewSession({ session, config, onFinish }) {
  const { addToast } = useApp()
  const [question, setQuestion]   = useState(null)
  const [answer, setAnswer]       = useState('')
  const [evaluation, setEval]     = useState(null)
  const [loadingQ, setLoadingQ]   = useState(false)
  const [loadingA, setLoadingA]   = useState(false)
  const [qCount, setQCount]       = useState(0)
  const [ttsOn, setTtsOn]         = useState(true)
  const textareaRef               = useRef(null)

  // Voice input
  const { isListening, transcript, supported: voiceSupported, toggle: toggleVoice, setTranscript } = useVoiceInput({
    onResult: (t) => setAnswer(t),
    onError:  (e) => addToast(`Voice error: ${e}`, 'error'),
  })

  // Sync transcript to answer box
  useEffect(() => { if (transcript) setAnswer(transcript) }, [transcript])

  // Video ref and init
  const videoRef = useRef(null)
  
  useEffect(() => {
    let stream = null;
    const startCamera = async () => {
      if (!navigator?.mediaDevices?.getUserMedia) {
        addToast('Media devices not supported. Voice only mode.', 'warning')
        return
      }
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (err) {
        addToast('Camera access denied or unavailable. Voice only mode.', 'warning')
      }
    }

    startCamera()
    
    return () => {
      if (stream) {
        stream.getTracks().forEach(t => t.stop())
      }
    }
  }, [addToast])

  const fetchQuestion = async () => {
    setLoadingQ(true)
    setEval(null)
    setAnswer('')
    setTranscript('')
    try {
      const q = await generateQuestion(session.id)
      setQuestion(q)
      setQCount(c => c + 1)
      if (ttsOn) speak(q.question_text)
    } catch {
      addToast('Failed to generate question', 'error')
    } finally {
      setLoadingQ(false)
    }
  }

  const handleSubmit = async () => {
    if (!answer.trim()) { addToast('Please provide an answer', 'error'); return }
    setLoadingA(true)
    stopSpeaking()
    try {
      const result = await submitAnswer({ question_id: question.id, answer_text: answer })
      setEval(result.evaluation)
      if (ttsOn && result.evaluation?.feedback_summary) {
        speak(`Score: ${result.evaluation.overall_score} out of 100. ${result.evaluation.feedback_summary}`)
      }
      addToast('Answer evaluated! 🎉', 'success')
    } catch {
      addToast('Failed to evaluate answer', 'error')
    } finally {
      setLoadingA(false)
    }
  }

  const scoreColor = (s) => s >= 70 ? 'var(--success)' : s >= 45 ? 'var(--warning)' : 'var(--danger)'

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: 20, alignItems: 'start' }}>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Session header */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <span className="badge badge-accent">Session #{session.id}</span>
            <span className="badge badge-info">{config.role}</span>
            <span className="badge badge-warning" style={{ textTransform: 'capitalize' }}>{config.interview_type.replace('_',' ')}</span>
            <span className="badge badge-danger" style={{ textTransform: 'capitalize' }}>{config.difficulty}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Q{qCount} answered</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost btn-icon" onClick={() => setTtsOn(t => !t)} title="Toggle TTS">
              {ttsOn ? <MdVolumeUp /> : <MdVolumeOff />}
            </button>
            <button className="btn btn-danger btn-sm" onClick={onFinish}>
              <MdClose /> End
            </button>
          </div>
        </div>

      {/* Question box */}
      <div className="card">
        {!question && !loadingQ && (
          <div className="empty-state">
            <div className="empty-icon">🎯</div>
            <h3>Ready to begin?</h3>
            <p>Click below to get your first AI-generated question.</p>
            <button className="btn btn-primary" onClick={fetchQuestion}>
              <MdArrowForward /> Get First Question
            </button>
          </div>
        )}

        {loadingQ && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, padding: '40px 0' }}>
            <div className="ai-thinking"><span/><span/><span/></div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Generating your question…</p>
          </div>
        )}

        {question && !loadingQ && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {question.category && <span className="badge badge-info">{question.category}</span>}
                {question.difficulty && <span className="badge badge-warning" style={{ textTransform: 'capitalize' }}>{question.difficulty}</span>}
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => ttsOn && speak(question.question_text)}>
                <MdVolumeUp /> Read
              </button>
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
      {question && !loadingQ && (
        <motion.div className="card" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 700 }}>Your Answer</label>
            {voiceSupported && (
              <button
                className={`mic-btn ${isListening ? 'recording' : 'idle'}`}
                onClick={toggleVoice}
                title={isListening ? 'Stop recording' : 'Speak your answer'}
              >
                {isListening ? <MdMicOff /> : <MdMic />}
              </button>
            )}
          </div>

          {isListening && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, padding: '8px 12px', background: 'rgba(238, 193, 112, 0.1)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(238, 193, 112, 0.3)' }}>
              <div className="waveform">
                {Array(8).fill(0).map((_, i) => <div key={i} className="waveform-bar" style={{ background: 'var(--accent)' }} />)}
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--accent)' }}>Listening… speak clearly</span>
            </div>
          )}

          <textarea
            ref={textareaRef}
            placeholder="Type your answer here, or use the microphone to speak…"
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            style={{ minHeight: 140, width: '100%' }}
            disabled={loadingA}
          />

          <div style={{ display: 'flex', gap: 10, marginTop: 14, justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={() => setAnswer('')} disabled={loadingA || !answer}>
              Clear
            </button>
            <button className="btn btn-primary" onClick={handleSubmit} disabled={loadingA || !answer.trim()}>
              {loadingA
                ? <><span className="spinner" />Evaluating…</>
                : <><MdCheckCircle />Submit Answer</>
              }
            </button>
          </div>
        </motion.div>
      )}

      {/* Evaluation */}
      <AnimatePresence>
        {evaluation && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <EvaluationPanel evaluation={evaluation} />
            <div style={{ display: 'flex', gap: 10, marginTop: 14, justifyContent: 'center' }}>
              <button className="btn btn-primary" onClick={fetchQuestion}>
                <MdRefresh /> Next Question
              </button>
              <button className="btn btn-secondary" onClick={onFinish}>
                <MdStop /> End Session
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>

      {/* Camera Panel */}
      <div className="camera-container" style={{ position: 'sticky', top: 20 }}>
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          style={{ width: '100%', height: 225, backgroundColor: '#000', objectFit: 'cover', borderRadius: 'var(--radius)', border: '4px solid var(--border)' }}
        />
        <div style={{ marginTop: 10, fontSize: '0.86rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <MdCameraAlt style={{ verticalAlign: 'middle' }}/> Camera Active
        </div>
      </div>

    </motion.div>
  )
}

// ---------- Main Export ----------
export default function InterviewPage() {
  const [phase, setPhase]       = useState('setup')   // setup | session | done
  const [session, setSession]   = useState(null)
  const [config, setConfig]     = useState(null)
  const [qHistory, setQHistory] = useState([])

  const handleStart = (sess, cfg) => {
    setSession(sess)
    setConfig(cfg)
    setPhase('session')
  }

  if (phase === 'setup')   return <SetupForm onStart={handleStart} />
  if (phase === 'session') return (
    <InterviewSession
      session={session}
      config={config}
      onFinish={() => setPhase('done')}
    />
  )

  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
      className="card" style={{ maxWidth: 480, margin: '60px auto', textAlign: 'center', padding: 48 }}>
      <div style={{ fontSize: '4rem', marginBottom: 16 }}>🏆</div>
      <h2 style={{ fontFamily: 'Outfit', fontSize: '1.6rem', marginBottom: 8 }}>Session Complete!</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>
        Great work! Review your evaluations in Interview History.
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button className="btn btn-primary" onClick={() => setPhase('setup')}>
          <MdRefresh /> New Session
        </button>
      </div>
    </motion.div>
  )
}
