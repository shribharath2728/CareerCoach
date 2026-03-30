import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { MdPerson, MdEmail, MdVpnKey, MdLink } from 'react-icons/md'
import { getLinkedInProfile, upsertLinkedInProfile } from '../services/api'

export default function Profile() {
  const { user, setUser, addToast } = useApp()
  const [linkedin, setLinkedin] = useState({ profile_url: '', summary: '', experience: '', education: '', skills: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getLinkedInProfile(user.id)
      .then(res => setLinkedin(res))
      .catch(err => {
        // 404 is fine, no profile yet
      })
      .finally(() => setLoading(false))
  }, [user.id])

  const handleSave = async () => {
    setSaving(true)
    try {
      await upsertLinkedInProfile(user.id, linkedin)
      addToast('LinkedIn profile saved', 'success')
    } catch (err) {
      addToast('Failed to save LinkedIn profile', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    setUser(null)
  }

  if (loading) return <div className='spinner' style={{ margin: 'auto' }} />

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className='page-container' style={{ maxWidth: 600, margin: '0 auto' }}>
      <div className='card' style={{ textAlign: 'center' }}>
        <div style={{ width: 80, height: 80, background: 'var(--accent)', borderRadius: '50%', margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, color: '#fff' }}>
          {user.full_name.charAt(0).toUpperCase()}
        </div>
        <h2>{user.full_name}</h2>
        <p style={{ color: 'var(--text-muted)' }}><MdEmail style={{ verticalAlign: 'middle' }}/> {user.email}</p>
        
        {user.is_guest && (
          <div style={{ background: 'rgba(247, 127, 0, 0.1)', color: 'var(--warning)', padding: 12, borderRadius: 8, marginTop: 20 }}>
            You are currently using a Guest Session. Data will not persist permanently.
          </div>
        )}

        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '24px 0' }} />

        <div style={{ textAlign: 'left' }}>
          <h3><MdLink /> LinkedIn Profile</h3>
          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input 
              placeholder='LinkedIn Profile URL' 
              value={linkedin.profile_url} 
              onChange={e => setLinkedin({...linkedin, profile_url: e.target.value})} 
            />
            <textarea 
              placeholder='Summary' 
              value={linkedin.summary} 
              onChange={e => setLinkedin({...linkedin, summary: e.target.value})} 
              rows={3}
            />
            <textarea 
              placeholder='Experience' 
              value={linkedin.experience} 
              onChange={e => setLinkedin({...linkedin, experience: e.target.value})} 
              rows={4}
            />
            <textarea 
              placeholder='Education' 
              value={linkedin.education} 
              onChange={e => setLinkedin({...linkedin, education: e.target.value})} 
              rows={3}
            />
            <textarea 
              placeholder='Skills' 
              value={linkedin.skills} 
              onChange={e => setLinkedin({...linkedin, skills: e.target.value})} 
              rows={3}
            />
            <button className='btn btn-primary' onClick={handleSave} disabled={saving}>
              {saving ? <span className='spinner' /> : 'Save LinkedIn Profile'}
            </button>
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '24px 0' }} />

        <button onClick={handleLogout} className='btn btn-danger' style={{ width: '100%', justifyContent: 'center' }}>
          Log Out
        </button>
      </div>
    </motion.div>
  )
}
