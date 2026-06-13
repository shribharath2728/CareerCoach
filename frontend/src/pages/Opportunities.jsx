import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { getOpportunities } from '../services/api'
import { MdSchool, MdBusiness, MdTrendingUp, MdStars, MdAutoAwesome } from 'react-icons/md'

export default function Opportunities() {
  const { user, addToast } = useApp()
  const [opps, setOpps] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOpps()
  }, [])

  const fetchOpps = async () => {
    setLoading(true)
    try {
      const data = await getOpportunities(user.id)
      setOpps(data)
    } catch (err) {
      addToast('Failed to load career opportunities', 'error')
    } finally {
      setLoading(false)
    }
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  }

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div className="spinner" />
      <p style={{ marginTop: 16, color: 'var(--text-muted)' }}>Analyzing your background & mapping career paths...</p>
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="page-container">
      <header style={{ marginBottom: 32 }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <MdAutoAwesome style={{ color: 'var(--accent)' }}/> Career Opportunities for {user.field_of_study || 'You'}
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          AI-curated corporate pathways tailored to your academic background and skills.
        </p>
      </header>

      {!user.field_of_study && (
        <div className="card" style={{ background: 'rgba(238, 193, 112, 0.1)', border: '1px solid var(--warning)', marginBottom: 24 }}>
          <p style={{ fontSize: '0.9rem' }}>
            💡 <strong>Pro Tip:</strong> Setting your <strong>Field of Study</strong> in the Profile page will help Nova give you much more accurate career suggestions!
          </p>
        </div>
      )}

      {opps.length === 0 ? (
        <div className="empty-state">
           <div className="empty-icon">🔭</div>
           <h3>No insights yet</h3>
           <p>We're having trouble finding specific roles. Try updating your profile details.</p>
           <button className="btn btn-primary" onClick={fetchOpps}>Retry Analysis</button>
        </div>
      ) : (
        <motion.div 
          variants={container}
          initial="hidden"
          animate="show"
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}
        >
          {opps.map((opp, idx) => (
            <motion.div key={idx} variants={item} className="card opportunity-card" style={{ position: 'relative', overflow: 'hidden' }}>
              <div style={{ padding: '4px 10px', background: 'var(--accent)', color: 'white', fontSize: '0.65rem', fontWeight: 800, position: 'absolute', top: 0, right: 0, borderRadius: '0 0 0 8px' }}>
                MNC PATHWAY
              </div>
              
              <h3 style={{ color: 'var(--accent)', marginBottom: 10, fontSize: '1.2rem' }}>{opp.role_title}</h3>
              <p style={{ fontSize: '0.88rem', lineHeight: 1.6, marginBottom: 18, color: 'var(--text-primary)' }}>
                {opp.description}
              </p>

              <div style={{ marginBottom: 18 }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Key Skills to Highlight
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {opp.key_skills_to_highlight?.map(skill => (
                    <span key={skill} className="badge badge-info" style={{ fontSize: '0.7rem' }}>{skill}</span>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: 16, borderTop: '1px solid var(--border)' }}>
                 <div style={{ fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Salary: </span>
                    <span style={{ fontWeight: 700, color: 'var(--success)' }}>{opp.typical_salary_range}</span>
                 </div>
                 <div style={{ display: 'flex', gap: -6 }}>
                    {/* Fake company avatars */}
                    {opp.mnc_companies?.map((c, i) => (
                      <div key={i} title={c} style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--bg-card)', border: '2px solid var(--border)', fontSize: '0.6rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginLeft: i > 0 ? -8 : 0, fontWeight: 700 }}>
                        {c[0]}
                      </div>
                    ))}
                 </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}

      <footer style={{ marginTop: 48, textAlign: 'center', opacity: 0.6 }}>
        <p style={{ fontSize: '0.8rem' }}>
          Career suggestions are AI-generated based on global corporate trends.
        </p>
      </footer>
    </motion.div>
  )
}
