import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { createUser, loginUser, updateUserSettings } from '../services/api'
import { ALL_MODEL_OPTIONS, GROQ_MODEL_OPTIONS, MODEL_LABELS, normalizeGroqModel } from '../constants/groqModels'
import { MdPerson, MdEmail, MdLock, MdSmartToy, MdLanguage, MdSettingsVoice, MdArrowForward, MdClose } from 'react-icons/md'

const FEATURES = [
  { icon: '🗺ï¸', label: 'Career Path Planning' },
  { icon: '📄', label: 'Resume Analyzer' },
  { icon: '🎤', label: 'Interview Coach' },
  { icon: '🔍', label: 'Skill Gap Analysis' },
  { icon: '📊', label: 'Job Readiness Score' },
  { icon: '📈', label: 'Industry Trends' },
]

export default function Onboarding() {
  const { setUser, addToast } = useApp()
  const [step, setStep] = useState('landing') // 'landing' | 'auth' | 'config'
  const [authMode, setAuthMode] = useState('login') // 'login' | 'signup' | 'guest'
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [config, setConfig] = useState({ ai_model: 'llama-3.3-70b-versatile', ai_language: 'en-US', ai_voice: '', ai_name: 'Nova' })
  const [loading, setLoading] = useState(false)
  const [tempUser, setTempUser] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])

  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices()
      if (voices.length > 0) setAvailableVoices(voices)
    }
    loadVoices()
    window.speechSynthesis.onvoiceschanged = loadVoices
  }, [])

  const handleAuthSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      let user
      if (authMode === 'login') {
        user = await loginUser({ email: form.email, password: form.password })
        addToast(`Welcome back, ${user.full_name}!`, 'success')
      } else if (authMode === 'signup') {
        user = await createUser({ ...form, is_guest: false })
        addToast('Account created!', 'success')
      } else {
        const guestId = Math.floor(Math.random() * 1000000)
        user = await createUser({ full_name: `Guest ${guestId}`, email: `guest${guestId}@example.com`, password: '', is_guest: true })
        addToast('Continuing as guest', 'info')
      }
      setTempUser(user)
      setConfig(prev => ({
        ...prev,
        ai_name: user.ai_name || 'Nova',
        ai_model: normalizeGroqModel(user.ai_model || prev.ai_model),
        ai_language: user.ai_language || prev.ai_language,
        ai_voice: user.ai_voice || prev.ai_voice,
      }))
      setStep('config')
    } catch (err) {
      addToast(err.response?.data?.detail || 'Authentication failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleConfigSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const updatedUser = await updateUserSettings(tempUser.id, config)
      setUser(updatedUser)
    } catch {
      setUser(tempUser)
    } finally {
      setLoading(false)
    }
  }

  const setF = (key, val) => setForm(f => ({ ...f, [key]: val }))
  const setC = (key, val) => setConfig(c => ({ ...c, [key]: val }))

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', position: 'relative', overflow: 'hidden' }}>
      {/* Background orbs */}
      <div className="bg-orbs">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
      </div>

      {/* Landing Page */}
      <AnimatePresence mode="wait">
        {step === 'landing' && (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            style={{
              minHeight: '100vh',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px 24px',
              position: 'relative',
              zIndex: 1,
              textAlign: 'center',
            }}
          >
            {/* Logo */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              style={{ marginBottom: 32 }}
            >
              <div style={{
                width: 64,
                height: 64,
                background: 'linear-gradient(135deg, var(--primary), var(--accent))',
                borderRadius: 20,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.8rem',
                margin: '0 auto 16px',
                boxShadow: '0 0 60px var(--accent-glow)',
              }}>
                🧠
              </div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>
                CareerCoach AI
              </div>
            </motion.div>

            {/* Headline glow */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.3 }}
              transition={{ delay: 0.2 }}
              style={{
                position: 'absolute',
                width: 600,
                height: 300,
                background: `radial-gradient(ellipse at center, var(--primary) 0%, var(--accent) 50%, transparent 70%)`,
                opacity: 0.12,
                filter: 'blur(60px)',
                pointerEvents: 'none',
                borderRadius: '50%',
                zIndex: 0,
              }}
            />

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: 'clamp(2.5rem, 6vw, 4rem)',
                fontWeight: 800,
                lineHeight: 1.1,
                marginBottom: 20,
                maxWidth: 700,
                position: 'relative',
                zIndex: 1,
                color: 'var(--text-primary)',
              }}
            >
              Your Personal{' '}
              <span className="gradient-text">AI Career Coach</span>
            </motion.h1>

            {/* Subheading */}
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.5 }}
              style={{
                color: 'var(--text-secondary)',
                fontSize: 'clamp(0.95rem, 2vw, 1.1rem)',
                maxWidth: 560,
                lineHeight: 1.7,
                marginBottom: 36,
                position: 'relative',
                zIndex: 1,
              }}
            >
              Get personalized career guidance, skill roadmaps, resume analysis, interview preparation, and industry insights powered by AI.
            </motion.p>

            {/* Feature pills */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 10,
                justifyContent: 'center',
                marginBottom: 44,
                maxWidth: 600,
                position: 'relative',
                zIndex: 1,
              }}
            >
              {FEATURES.map((f) => (
                <span
                  key={f.label}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '7px 14px',
                    borderRadius: 99,
                    background: 'var(--surface)',
                    border: '1px solid var(--glass-border)',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    color: 'var(--text-secondary)',
                    backdropFilter: 'blur(8px)',
                  }}
                >
                  {f.icon} {f.label}
                </span>
              ))}
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              style={{ display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center', position: 'relative', zIndex: 1 }}
            >
              <button
                className="btn btn-primary btn-lg"
                onClick={() => { setAuthMode('signup'); setStep('auth') }}
                style={{ gap: 8, minWidth: 160 }}
              >
                Get Started <MdArrowForward />
              </button>
              <button
                className="btn btn-secondary btn-lg"
                onClick={() => { setAuthMode('login'); setStep('auth') }}
                style={{ minWidth: 130 }}
              >
                Sign In
              </button>
            </motion.div>
          </motion.div>
        )}

        {/* Auth Step — modal overlay on landing */}
        {step === 'auth' && (
          <motion.div
            key="auth"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              minHeight: '100vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
              position: 'relative',
              zIndex: 1,
            }}
          >
            <motion.div
              className="onboarding-card"
              initial={{ opacity: 0, scale: 0.96, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              style={{ position: 'relative' }}
            >
              {/* Close → back to landing */}
              <button
                className="btn btn-ghost btn-icon"
                onClick={() => setStep('landing')}
                aria-label="Back to landing"
                style={{ position: 'absolute', top: 16, right: 16 }}
              >
                <MdClose />
              </button>

              <div className="logo-big">🧠</div>
              <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: 800, textAlign: 'center', marginBottom: 4 }}>
                CareerCoach AI
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', textAlign: 'center', marginBottom: 24 }}>
                Your intelligent career companion
              </p>

              {/* Auth mode tabs */}
              <div style={{ display: 'flex', gap: 6, marginBottom: 24, background: 'var(--surface-2)', padding: 4, borderRadius: 'var(--radius-sm)' }}>
                {['login', 'signup', 'guest'].map(m => (
                  <button
                    key={m}
                    className={`btn btn-sm ${authMode === m ? 'btn-primary' : 'btn-ghost'}`}
                    style={{ flex: 1, textTransform: 'capitalize', minHeight: 36 }}
                    onClick={() => setAuthMode(m)}
                  >
                    {m === 'login' ? 'Sign In' : m === 'signup' ? 'Sign Up' : 'Guest'}
                  </button>
                ))}
              </div>

              <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {authMode === 'signup' && (
                  <div className="form-group">
                    <label><MdPerson style={{ verticalAlign: 'middle', marginRight: 4 }} />Full Name</label>
                    <input required type="text" placeholder="Alex Johnson" value={form.full_name} onChange={e => setF('full_name', e.target.value)} />
                  </div>
                )}

                {authMode !== 'guest' && (
                  <>
                    <div className="form-group">
                      <label><MdEmail style={{ verticalAlign: 'middle', marginRight: 4 }} />Email</label>
                      <input required type="email" placeholder="you@example.com" value={form.email} onChange={e => setF('email', e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label><MdLock style={{ verticalAlign: 'middle', marginRight: 4 }} />Password</label>
                      <input required type="password" placeholder="••••••••" value={form.password} onChange={e => setF('password', e.target.value)} />
                    </div>
                  </>
                )}

                {authMode === 'guest' && (
                  <div style={{ textAlign: 'center', padding: '10px 0', color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.6 }}>
                    Guest accounts are temporary. Data is lost after session ends.
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-primary btn-lg"
                  disabled={loading}
                  style={{ width: '100%', marginTop: 6 }}
                >
                  {loading ? <span className="spinner" /> : authMode === 'login' ? 'Sign In' : authMode === 'signup' ? 'Create Account' : 'Continue as Guest'}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}

        {/* Config Step */}
        {step === 'config' && (
          <motion.div
            key="config"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              minHeight: '100vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
              position: 'relative',
              zIndex: 1,
            }}
          >
            <motion.div className="onboarding-card" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}>
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{ fontSize: '2rem', marginBottom: 12 }}>⚙️</div>
                <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', fontWeight: 800, marginBottom: 4 }}>Configure Your AI</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Personalize your career coach experience</p>
              </div>

              <form onSubmit={handleConfigSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div className="form-group">
                  <label><MdSmartToy style={{ verticalAlign: 'middle', marginRight: 4 }} />AI Coach Name</label>
                  <input type="text" value={config.ai_name} onChange={e => setC('ai_name', e.target.value)} placeholder="Nova" />
                </div>

                <div className="form-group">
                  <label><MdSmartToy style={{ verticalAlign: 'middle', marginRight: 4 }} />AI Model</label>
                  <select value={normalizeGroqModel(config.ai_model)} onChange={e => setC('ai_model', e.target.value)}>
                    {GROQ_MODEL_OPTIONS.map(id => (
                      <option key={id} value={id}>{MODEL_LABELS[id]}</option>
                    ))}
                  </select>
                  <div style={{ fontSize: '0.72rem', color: 'rgba(0,245,255,0.45)', marginTop: 5 }}>
                    All models are powered by Groq free tier.
                  </div>
                </div>

                <div className="form-group">
                  <label><MdLanguage style={{ verticalAlign: 'middle', marginRight: 4 }} />Language</label>
                  <select value={config.ai_language} onChange={e => setC('ai_language', e.target.value)}>
                    <option value="en-US">English (US)</option>
                    <option value="ta-IN">Tamil</option>
                    <option value="te-IN">Telugu</option>
                    <option value="ml-IN">Malayalam</option>
                    <option value="kn-IN">Kannada</option>
                    <option value="hi-IN">Hindi</option>
                  </select>
                </div>

                <div className="form-group">
                  <label><MdSettingsVoice style={{ verticalAlign: 'middle', marginRight: 4 }} />Voice</label>
                  <select value={config.ai_voice} onChange={e => setC('ai_voice', e.target.value)}>
                    <option value="">Default System Voice</option>
                    {availableVoices.filter(v => v.lang.startsWith(config.ai_language.split('-')[0])).map((v, i) => (
                      <option key={i} value={v.name}>{v.name} ({v.lang})</option>
                    ))}
                  </select>
                </div>

                <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%', marginTop: 8 }}>
                  {loading ? <span className="spinner" /> : 'Launch Dashboard →'}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
