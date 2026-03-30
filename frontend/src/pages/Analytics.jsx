import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { getAnalytics } from '../services/api'
import { MdTrendingUp, MdCheckCircle, MdSchool } from 'react-icons/md'

export default function Analytics() {
  const { user } = useApp()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAnalytics(user.id)
      .then(res => setStats(res))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user.id])

  if (loading) return <div className="spinner" style={{ margin: 'auto' }} />

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <h2>Performance Analytics</h2>
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginTop: 24 }}>
          <div className="card stat-card">
            <MdSchool size={30} color="var(--accent)" />
            <h3>{stats.total_interviews}</h3>
            <p>Total Interviews</p>
          </div>
          <div className="card stat-card">
            <MdCheckCircle size={30} color="var(--success)" />
            <h3>{stats.total_questions_answered}</h3>
            <p>Questions Answered</p>
          </div>
          <div className="card stat-card">
            <MdTrendingUp size={30} color="var(--warning)" />
            <h3>{stats.average_score.toFixed(1)} / 100</h3>
            <p>Average Score</p>
          </div>
        </div>
      )}
    </motion.div>
  )
}
