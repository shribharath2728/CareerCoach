import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { updateUserSettings } from '../services/api'
import { GROQ_MODEL_OPTIONS, normalizeGroqModel } from '../constants/groqModels'
import { MdSettings, MdPalette, MdLanguage, MdSmartToy, MdSettingsVoice } from 'react-icons/md'

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

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </form>
      </div>
    </motion.div>
  )
}
