import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { getHistory } from '../services/api'
import { MdHistory, MdChatBubble, MdAccessTime } from 'react-icons/md'

export default function History() {
  const { user } = useApp()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHistory(user.id)
      .then(res => setSessions(res))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user.id])

  if (loading) return <div className="spinner" style={{ margin: 'auto' }} />

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <h2><MdHistory /> Your Interview History</h2>
      {sessions.length === 0 ? (
        <div className="empty-state">No past sessions found.</div>
      ) : (
        <div style={{ display: 'grid', gap: 16, marginTop: 20 }}>
          {sessions.map(s => (
            <div key={s.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0 }}>{s.role} ({s.difficulty})</h3>
                <span className="badge" style={{ marginTop: 8, display: 'inline-block' }}>{s.interview_type}</span>
              </div>
              <div style={{ color: 'var(--text-muted)' }}>
                <MdAccessTime style={{ verticalAlign: 'middle' }} /> {new Date(s.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  )
}
