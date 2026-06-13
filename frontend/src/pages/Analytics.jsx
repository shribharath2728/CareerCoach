import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { getAnalytics } from '../services/api'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip
} from 'recharts'
import { MdTrendingUp, MdCheckCircle, MdSchool, MdStar, MdLocalFireDepartment, MdEmojiEvents } from 'react-icons/md'

const BADGES = [
  { id: 'first_step', icon: '🌱', label: 'First Step', desc: '1+ interview done', cond: (s) => s.total_interviews >= 1 },
  { id: 'consistent', icon: '🔥', label: 'On Fire', desc: '3-day streak', cond: (s) => (s.streak_count || 0) >= 3 },
  { id: 'warrior', icon: '⚡', label: 'Interview Warrior', desc: '7-day streak', cond: (s) => (s.streak_count || 0) >= 7 },
  { id: 'job_ready', icon: '🏆', label: 'Job Ready', desc: '30-day streak', cond: (s) => (s.streak_count || 0) >= 30 },
  { id: 'high_scorer', icon: '🎯', label: 'High Scorer', desc: 'Avg score â‰¥ 70', cond: (s) => (s.average_score || 0) >= 70 },
  { id: 'perfectionist', icon: '💎', label: 'Perfectionist', desc: 'Best score â‰¥ 90', cond: (s) => (s.best_score || 0) >= 90 },
  { id: 'practitioner', icon: '🧪', label: 'Practitioner', desc: '20+ questions answered', cond: (s) => s.total_questions_answered >= 20 },
  { id: 'pro', icon: '🚀', label: 'Career Pro', desc: '10+ interviews done', cond: (s) => s.total_interviews >= 10 },
]

function CustomRadarTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--glass-border)',
        borderRadius: 10, padding: '8px 14px', fontSize: '0.82rem',
        color: 'var(--text-primary)', boxShadow: 'var(--shadow-md)',
      }}>
        <strong>{payload[0].payload.skill}</strong>: {payload[0].value}
      </div>
    )
  }
  return null
}

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

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
      <div className="spinner" style={{ width: 40, height: 40 }} />
    </div>
  )

  if (!stats) return (
    <div className="empty-state">
      <div className="empty-icon">📊</div>
      <h3>No analytics yet</h3>
      <p>Complete your first interview to see your performance data.</p>
    </div>
  )

  const dims = stats.dimension_averages || {}
  const radarData = [
    { skill: 'Technical', value: Math.round(dims.technical_score || 0) },
    { skill: 'Problem Solving', value: Math.round(dims.problem_solving_score || 0) },
    { skill: 'Communication', value: Math.round(dims.communication_score || 0) },
    { skill: 'Structure', value: Math.round(dims.structure_score || 0) },
    { skill: 'Completeness', value: Math.round(dims.completeness_score || 0) },
    { skill: 'Confidence', value: Math.round(dims.confidence_score || 0) },
  ]

  const unlockedBadges = BADGES.filter(b => b.cond(stats))
  const lockedBadges = BADGES.filter(b => !b.cond(stats))

  const hasRadarData = radarData.some(d => d.value > 0)

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', marginBottom: 4 }}>Performance Analytics</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Track your progress across all skill dimensions</p>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14 }}>
        {[
          { icon: <MdSchool />, label: 'Interviews', value: stats.total_interviews, color: 'purple' },
          { icon: <MdCheckCircle />, label: 'Questions Done', value: stats.total_questions_answered, color: 'green' },
          { icon: <MdTrendingUp />, label: 'Avg Score', value: `${(stats.average_score || 0).toFixed(1)}`, color: 'blue' },
          { icon: <MdStar />, label: 'Best Score', value: `${stats.best_score || 0}`, color: 'orange' },
          { icon: <MdLocalFireDepartment />, label: 'Streak', value: `${stats.streak_count || 0}🔥`, color: 'red' },
        ].map((s, i) => (
          <motion.div key={i} className="stat-card" whileHover={{ y: -2, scale: 1.01 }}>
            <div className={`stat-icon ${s.color}`}>{s.icon}</div>
            <div className="stat-info">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Radar Chart */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">🎯 Skill Radar</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Based on all evaluated answers</span>
        </div>
        {hasRadarData ? (
          <div style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis
                  dataKey="skill"
                  tick={{ fill: 'var(--text-secondary)', fontSize: 12, fontFamily: 'Inter' }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                  tickCount={5}
                />
                <Radar
                  name="Score"
                  dataKey="value"
                  stroke="var(--primary)"
                  fill="var(--primary)"
                  fillOpacity={0.25}
                  strokeWidth={2}
                />
                <Tooltip content={<CustomRadarTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="empty-state" style={{ padding: '40px 20px' }}>
            <div className="empty-icon">📡</div>
            <h3>No data yet</h3>
            <p>Complete and submit interview answers to populate your skill radar.</p>
          </div>
        )}
      </div>

      {/* Dimension Breakdown bars */}
      {hasRadarData && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📊 Score Breakdown</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {radarData.map(d => {
              const color = d.value >= 70 ? 'var(--success)' : d.value >= 45 ? 'var(--warning)' : 'var(--danger)'
              return (
                <div key={d.skill} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600, width: 130, flexShrink: 0 }}>{d.skill}</span>
                  <div className="progress-wrap" style={{ flex: 1, height: 8 }}>
                    <motion.div
                      className="progress-fill"
                      style={{ width: `${d.value}%`, background: color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${d.value}%` }}
                      transition={{ duration: 0.8, delay: 0.1 }}
                    />
                  </div>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color, width: 32, textAlign: 'right' }}>{d.value}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Badges */}
      <div className="card">
        <div className="card-header">
          <div className="card-title"><MdEmojiEvents style={{ verticalAlign: 'middle', marginRight: 6 }} />Achievements</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{unlockedBadges.length}/{BADGES.length} unlocked</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12 }}>
          {BADGES.map(badge => {
            const unlocked = badge.cond(stats)
            return (
              <motion.div
                key={badge.id}
                whileHover={{ scale: 1.04 }}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                  padding: '14px 10px', borderRadius: 14,
                  border: `1px solid ${unlocked ? 'var(--primary)' : 'var(--glass-border)'}`,
                  background: unlocked ? 'rgba(99,102,241,0.08)' : 'var(--surface-2)',
                  opacity: unlocked ? 1 : 0.45,
                  transition: 'all 0.3s',
                  filter: unlocked ? 'none' : 'grayscale(80%)',
                  cursor: 'default',
                }}
                title={badge.desc}
              >
                <span style={{ fontSize: '1.8rem' }}>{badge.icon}</span>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: unlocked ? 'var(--primary)' : 'var(--text-muted)', textAlign: 'center', lineHeight: 1.3 }}>{badge.label}</span>
                {unlocked && <span style={{ fontSize: '0.6rem', color: 'var(--success)', fontWeight: 600 }}>✓ UNLOCKED</span>}
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Locked hints */}
      {lockedBadges.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--primary)' }}>
          <div style={{ fontWeight: 700, fontFamily: 'var(--font-heading)', marginBottom: 10, fontSize: '0.9rem' }}>
            🎯 Next Achievements to Unlock
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {lockedBadges.slice(0, 3).map(b => (
              <div key={b.id} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <span>{b.icon}</span>
                <strong>{b.label}</strong> — {b.desc}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
