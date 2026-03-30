import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { getResume, upsertResume, getLinkedInProfile } from '../services/api'
import { MdDocumentScanner, MdSave, MdDownload } from 'react-icons/md'

export default function ResumeBuilder() {
  const { user, addToast } = useApp()
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    getResume(user.id)
      .then(res => setContent(res.content || ''))
      .catch(err => {
         // 404 is fine, means no resume yet
      })
      .finally(() => setLoading(false))
  }, [user.id])

  const handleSave = async () => {
    setSaving(true)
    try {
      await upsertResume({ user_id: user.id, content })
      addToast('Resume saved successfully', 'success')
    } catch (err) {
      addToast('Failed to save resume', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleImportFromLinkedIn = async () => {
    setGenerating(true)
    try {
      const linkedin = await getLinkedInProfile(user.id)
      if (!linkedin.summary && !linkedin.experience) {
        addToast('No LinkedIn profile data found. Please add your LinkedIn profile in the Profile section.', 'warning')
        return
      }
      // Simple concatenation, in real app use AI to format
      const resumeText = `
# ${user.full_name}

## Summary
${linkedin.summary || 'No summary provided.'}

## Experience
${linkedin.experience || 'No experience provided.'}

## Education
${linkedin.education || 'No education provided.'}

## Skills
${linkedin.skills || 'No skills provided.'}
      `.trim()
      setContent(resumeText)
      addToast('Resume imported from LinkedIn', 'success')
    } catch (err) {
      addToast('Failed to import from LinkedIn', 'error')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <div className="spinner" style={{ margin: 'auto' }} />

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2><MdDocumentScanner /> Resume Builder</h2>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-secondary" onClick={handleImportFromLinkedIn} disabled={generating}>
            {generating ? <span className="spinner" /> : <MdDownload />} Import from LinkedIn
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <span className="spinner" /> : <MdSave />} Save Resume
          </button>
        </div>
      </div>

      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', background: 'var(--bg-tertiary)' }}>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Draft your resume in markdown or plain text here. Your AI coach will be able to review it!
          </p>
        </div>
        <textarea 
          placeholder="# John Doe

## Summary
Software Engineer with 5 years experience...

## Experience
- Google (2020-2024)..."
          value={content}
          onChange={e => setContent(e.target.value)}
          style={{
             flex: 1, width: '100%', resize: 'none', border: 'none', padding: '24px',
             fontFamily: 'monospace', fontSize: '1rem', background: 'var(--bg-card)', 
             color: 'var(--text-primary)', outline: 'none'
          }}
        />
      </div>
    </motion.div>
  )
}
