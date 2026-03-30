import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { getJobs, createJob, updateJob, deleteJob } from '../services/api'
import { MdWork, MdAdd, MdDelete, MdEdit } from 'react-icons/md'

const STATUSES = ["Applied", "Interviewing", "Offered", "Rejected"]

export default function JobTracker() {
  const { user, addToast } = useApp()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  const [isAdding, setIsAdding] = useState(false)
  const [newJob, setNewJob] = useState({ company: '', role: '', status: 'Applied', linkedin_job_url: '' })

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = () => {
    setLoading(true)
    getJobs(user.id)
      .then(res => setJobs(res))
      .catch(err => addToast('Failed to load jobs', 'error'))
      .finally(() => setLoading(false))
  }

  const handleAddJob = async () => {
    if (!newJob.company || !newJob.role) return
    try {
      const added = await createJob({ user_id: user.id, ...newJob })
      setJobs([added, ...jobs])
      setIsAdding(false)
      setNewJob({ company: '', role: '', status: 'Applied' })
      addToast('Job added successfully', 'success')
    } catch (err) {
      addToast('Failed to add job', 'error')
    }
  }

  const handleStatusChange = async (jobId, newStatus) => {
    try {
      await updateJob(jobId, { status: newStatus })
      setJobs(jobs.map(j => j.id === jobId ? { ...j, status: newStatus } : j))
    } catch (err) {
      addToast('Failed to update status', 'error')
    }
  }

  const handleDelete = async (jobId) => {
    try {
      await deleteJob(jobId)
      setJobs(jobs.filter(j => j.id !== jobId))
      addToast('Job removed', 'success')
    } catch (err) {
      addToast('Failed to delete job', 'error')
    }
  }

  const statusColor = (s) => {
    switch(s) {
      case 'Applied': return 'var(--info)'
      case 'Interviewing': return 'var(--warning)'
      case 'Offered': return 'var(--success)'
      case 'Rejected': return 'var(--danger)'
      default: return 'var(--text-muted)'
    }
  }

  if (loading) return <div className="spinner" style={{ margin: 'auto' }} />

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2><MdWork /> Job Application Tracker</h2>
        <button className="btn btn-primary" onClick={() => setIsAdding(!isAdding)}>
          <MdAdd /> New Application
        </button>
      </div>

      {isAdding && (
        <div className="card" style={{ marginTop: 24, padding: 20 }}>
          <h3 style={{ marginBottom: 16 }}>Add New Application</h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <input 
              style={{ flex: 1 }}
              placeholder="Company Name" 
              value={newJob.company} 
              onChange={e => setNewJob({...newJob, company: e.target.value})} 
            />
            <input 
              style={{ flex: 1 }}
              placeholder="Role / Title" 
              value={newJob.role} 
              onChange={e => setNewJob({...newJob, role: e.target.value})} 
            />
            <select 
              value={newJob.status} 
              onChange={e => setNewJob({...newJob, status: e.target.value})}
            >
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button className="btn btn-primary" onClick={handleAddJob}>Save</button>
          </div>
        </div>
      )}

      {jobs.length === 0 ? (
         !isAdding && (
           <div className="empty-state" style={{ marginTop: 30 }}>
             <div className="empty-icon">🎒</div>
             <h3>No jobs tracked yet</h3>
             <p>Start applying and keep your pipeline organized!</p>
           </div>
         )
      ) : (
        <div style={{ display: 'grid', gap: 16, marginTop: 24 }}>
          {jobs.map(job => (
            <div key={job.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{job.role}</h3>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 4 }}>{job.company}</div>
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <span className="badge" style={{ background: statusColor(job.status) }}>{job.status}</span>
                <select 
                  value={job.status}
                  onChange={e => handleStatusChange(job.id, e.target.value)}
                  style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                >
                  {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
                <button className="btn btn-ghost btn-icon" onClick={() => handleDelete(job.id)} style={{ color: 'var(--danger)' }}>
                  <MdDelete />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  )
}
