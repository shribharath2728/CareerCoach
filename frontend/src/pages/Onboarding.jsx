import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { createUser, loginUser, updateUserSettings } from '../services/api'
import { GROQ_MODEL_OPTIONS, normalizeGroqModel } from '../constants/groqModels'
import { MdPerson, MdEmail, MdLock, MdSmartToy, MdLanguage, MdSettingsVoice } from 'react-icons/md'

export default function Onboarding() {
  const { setUser, addToast } = useApp()
  const [step, setStep] = useState('auth') // 'auth' | 'config'
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
        addToast(`Welcome back, ${user.full_name}! 👋`, 'success')
      } else if (authMode === 'signup') {
        user = await createUser({ ...form, is_guest: false })
        addToast(`Account created! 🎉`, 'success')
      } else {
        // Guest Create
        const guestId = Math.floor(Math.random() * 1000000)
        user = await createUser({
          full_name: `Guest ${guestId}`,
          email: `guest${guestId}@example.com`,
          password: '',
          is_guest: true
        })
        addToast('Logged in as Guest 🥸', 'info')
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
    } catch (err) {
      addToast('Failed to save AI settings', 'error')
      // fallback just log them in
      setUser(tempUser)
    } finally {
      setLoading(false)
    }
  }

  const setF = (key, val) => setForm(f => ({ ...f, [key]: val }))
  const setC = (key, val) => setConfig(c => ({ ...c, [key]: val }))

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: 20 }}>
      {step === 'auth' ? (
        <motion.div className="onboarding-card" initial={{ opacity: 0, y: 32 }} animate={{ opacity: 1, y: 0 }}>
          <div className="logo-big">🧠</div>
          <h1 style={{ fontFamily: 'Outfit', fontSize: '1.7rem', marginBottom: 6 }}>SkillLens</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 24 }}>Your intelligent skills and career companion.</p>

          <div style={{ display: 'flex', gap: 10, marginBottom: 24, background: 'var(--bg-tertiary)', padding: 4, borderRadius: 'var(--radius-sm)' }}>
            {['login', 'signup', 'guest'].map(m => (
              <button key={m} className={`btn btn-sm ${authMode === m ? 'btn-primary' : 'btn-ghost'}`} style={{ flex: 1, textTransform: 'capitalize' }} onClick={() => setAuthMode(m)}>
                {m}
              </button>
            ))}
          </div>

          <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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
              <div style={{ textAlign: 'center', padding: '10px 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Guest accounts are temporary. Data may be lost after session ends.
              </div>
            )}

            <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%', justifyContent: 'center', marginTop: 10 }}>
              {loading ? <span className="spinner" /> : authMode === 'login' ? 'Sign In' : authMode === 'signup' ? 'Create Account' : 'Continue as Guest'}
            </button>
          </form>
        </motion.div>
      ) : (
        <motion.div className="onboarding-card" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
          <h2 style={{ fontFamily: 'Outfit', fontSize: '1.4rem', marginBottom: 20 }}>Configure Your AI Assistant 🤖</h2>
          <form onSubmit={handleConfigSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            
            <div className="form-group">
              <label><MdSmartToy style={{ verticalAlign: 'middle', marginRight: 4 }} />AI Name & Persona</label>
              <input type="text" value={config.ai_name} onChange={e => setC('ai_name', e.target.value)} />
            </div>

            <div className="form-group">
              <label><MdSmartToy style={{ verticalAlign: 'middle', marginRight: 4 }} />AI Model</label>
              <select
                value={normalizeGroqModel(config.ai_model)}
                onChange={e => setC('ai_model', e.target.value)}
              >
                {GROQ_MODEL_OPTIONS.map((id) => (
                  <option key={id} value={id}>
                    {id === 'llama-3.3-70b-versatile' && 'Llama 3.3 70B — balanced (recommended)'}
                    {id === 'llama-3.1-8b-instant' && 'Llama 3.1 8B — fastest'}
                    {id === 'meta-llama/llama-4-scout-17b-16e-instruct' && 'Llama 4 Scout — long context'}
                    {id === 'meta-llama/llama-4-maverick-17b-128e-instruct' && 'Llama 4 Maverick — deeper reasoning'}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label><MdLanguage style={{ verticalAlign: 'middle', marginRight: 4 }} />Native Language</label>
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
              <label><MdSettingsVoice style={{ verticalAlign: 'middle', marginRight: 4 }} />Voice Model</label>
              <select value={config.ai_voice} onChange={e => setC('ai_voice', e.target.value)}>
                <option value="">Default System Voice</option>
                {availableVoices.filter(v => v.lang.startsWith(config.ai_language.split('-')[0])).map((v, i) => (
                  <option key={i} value={v.name}>{v.name} ({v.lang})</option>
                ))}
              </select>
            </div>

            <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%', justifyContent: 'center', marginTop: 10 }}>
              {loading ? <span className="spinner" /> : 'Launch Dashboard 🚀'}
            </button>
          </form>
        </motion.div>
      )}
    </div>
  )
}
