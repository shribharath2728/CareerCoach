import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { updateUserSettings } from '../services/api'
import { ALL_MODEL_OPTIONS, normalizeGroqModel, MODEL_LABELS } from '../constants/groqModels'
import { MdSettings, MdPalette, MdLanguage, MdSmartToy, MdSettingsVoice, MdPsychology } from 'react-icons/md'

export default function SettingsPage() {
  const { user, setUser, addToast } = useApp()
  const [config, setConfig] = useState({ ...user })
  const [loading, setLoading] = useState(false)
  const [voices, setVoices] = useState([])

  useEffect(() => {
    const v = window.speechSynthesis.getVoices()
    if (v.length > 0) setVoices(v)
    window.speechSynthesis.onvoiceschanged = () => setVoices(window.speechSynthesis.getVoices())
  }, [])

  useEffect(() => {
    setConfig({
      ...user,
      ai_model: normalizeGroqModel(user?.ai_model),
    })
  }, [user])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const updated = await updateUserSettings(user.id, config)
      setUser(updated)
      addToast('Settings updated successfully', 'success')
      document.body.setAttribute('data-theme', updated.theme)
    } catch (err) {
      addToast('Failed to update settings', 'error')
    } finally {
      setLoading(false)
    }
  }

  const setC = (key, val) => setConfig(c => ({ ...c, [key]: val }))

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-container" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div className="card">
        <h2><MdSettings /> App Settings</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20, marginTop: 24 }}>

          <div className="form-group">
            <label><MdPalette /> Theme</label>
            <select value={config.theme} onChange={e => setC('theme', e.target.value)}>
              <option value="light">Light Mode ☀️</option>
              <option value="dark">Dark Mode 🌙</option>
            </select>
          </div>

          <div className="form-group">
            <label><MdSmartToy /> AI Model Preference</label>
            <select
              value={normalizeGroqModel(config.ai_model)}
              onChange={e => setC('ai_model', e.target.value)}
            >
              {['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'meta-llama/llama-4-scout-17b-16e-instruct', 'meta-llama/llama-4-maverick-17b-128e-instruct'].map(id => (
                <option key={id} value={id}>{MODEL_LABELS[id]}</option>
              ))}
            </select>
            <div style={{ fontSize: '0.72rem', color: 'rgba(0,245,255,0.45)', marginTop: 5, fontFamily: "'Exo 2', sans-serif" }}>
              All models are powered by Groq free tier.
            </div>
          </div>

          <div className="form-group">
            <label><MdLanguage /> Preferred Language</label>
            <select value={config.ai_language || 'en-US'} onChange={e => setC('ai_language', e.target.value)}>
              <option value="en-US">English (US)</option>
              <option value="ta-IN">Tamil</option>
              <option value="te-IN">Telugu</option>
              <option value="ml-IN">Malayalam</option>
              <option value="kn-IN">Kannada</option>
              <option value="hi-IN">Hindi</option>
            </select>
          </div>

          <div className="form-group">
            <label><MdSettingsVoice /> TTS Voice</label>
            <select value={config.ai_voice || ''} onChange={e => setC('ai_voice', e.target.value)}>
              <option value="">Default OS Voice</option>
              {voices.filter(v => v.lang.startsWith((config.ai_language || 'en-US').split('-')[0])).map((v, i) => (
                <option key={i} value={v.name}>{v.name} ({v.lang})</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label><MdPsychology /> AI Coach Personality Mode</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginTop: 4 }}>
              {[
                { value: 'supportive', icon: '🤝', label: 'Supportive Mentor', desc: 'Encouraging & motivational' },
                { value: 'strict', icon: '🎯', label: 'Strict Corporate', desc: 'Harsh but realistic' },
                { value: 'academic', icon: '🎓', label: 'Academic Coach', desc: 'Structured & criteria-based' },
                { value: 'speed_drill', icon: '⚡', label: 'Speed Drill', desc: 'Rapid-fire short answers' },
              ].map(m => {
                const active = (config.coaching_style || 'supportive') === m.value
                return (
                  <button
                    key={m.value}
                    type="button"
                    onClick={() => setC('coaching_style', m.value)}
                    style={{
                      padding: '12px 14px', borderRadius: 12, textAlign: 'left',
                      border: `2px solid ${active ? 'var(--primary)' : 'var(--glass-border)'}`,
                      background: active ? 'rgba(99,102,241,0.08)' : 'var(--surface-2)',
                      cursor: 'pointer', transition: 'all 0.2s', display: 'flex', flexDirection: 'column', gap: 4,
                    }}
                  >
                    <span style={{ fontSize: '1.4rem' }}>{m.icon}</span>
                    <span style={{ fontWeight: 700, fontSize: '0.82rem', color: active ? 'var(--primary)' : 'var(--text-primary)' }}>{m.label}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{m.desc}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </form>
      </div>
    </motion.div>
  )
}
