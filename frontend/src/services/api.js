import axios from 'axios'

/**
 * API base URL:
 * - Default: `/api` → Vite dev/preview proxies to FastAPI (same origin = no CORS / fewer Windows issues).
 * - Override: set `VITE_API_BASE_URL=http://127.0.0.1:8000` in `frontend/.env` to call the API directly.
 */
function resolveApiBase() {
  const explicit = import.meta.env.VITE_API_BASE_URL
  if (explicit != null && String(explicit).trim() !== '') {
    return String(explicit).replace(/\/$/, '')
  }
  return '/api'
}

const BASE = resolveApiBase()

const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120_000,
})

// ── User ────────────────────────────────────────────────────────────
export const createUser         = (data) => api.post('/users', data).then(r => r.data)
export const loginUser          = (data) => api.post('/users/login', data).then(r => r.data)
export const getUser            = (id)   => api.get(`/users/${id}`).then(r => r.data)
export const listUsers          = ()     => api.get('/users').then(r => r.data)
export const updateUserSettings = (id, data) => api.put(`/users/${id}/settings`, data).then(r => r.data)

// ── Chat ────────────────────────────────────────────────────────────
export const createChatSession  = (data)      => api.post('/chat/sessions', data).then(r => r.data)
export const listChatSessions   = (userId)    => api.get(`/chat/sessions/${userId}`).then(r => r.data)
export const createChatMessage  = (data)      => api.post('/chat/messages', data).then(r => r.data)
export const listChatMessages   = (sessionId) => api.get(`/chat/messages/${sessionId}`).then(r => r.data)

// ── Interview ───────────────────────────────────────────────────────
export const startInterview    = (data)      => api.post('/interview/start', data).then(r => r.data)
export const generateQuestion  = (sessionId) => api.post('/interview/generate-question', { session_id: sessionId }).then(r => r.data)
export const submitAnswer      = (data)      => api.post('/interview/submit-answer', data).then(r => r.data)

export const getHistory        = (userId)    => api.get(`/interview/user/${userId}/history`).then(r => r.data)
export const getAnalytics      = (userId)    => api.get(`/interview/user/${userId}/analytics`).then(r => r.data)
export const getUserStreak     = (userId)    => api.get(`/interview/user/${userId}/analytics`).then(r => r.data)

// ── Job Tracker ───────────────────────────────────────────────────────
export const createJob         = (data)      => api.post('/jobs/', data).then(r => r.data)
export const getJobs           = (userId)    => api.get(`/jobs/user/${userId}`).then(r => r.data)
export const updateJob         = (id, data)  => api.put(`/jobs/${id}`, data).then(r => r.data)
export const deleteJob         = (id)        => api.delete(`/jobs/${id}`).then(r => r.data)

// ── Resume Builder ────────────────────────────────────────────────────
export const getResume         = (userId)    => api.get(`/resumes/user/${userId}`).then(r => r.data)
export const upsertResume      = (data)      => api.put('/resumes/', data).then(r => r.data)
export const analyzeJD         = (userId, data) => api.post(`/resumes/user/${userId}/analyze`, data).then(r => r.data)

// ── LinkedIn ─────────────────────────────────────────────────────────
export const getLinkedInProfile    = (userId)    => api.get(`/linkedin/user/${userId}`).then(r => r.data)
export const createLinkedInProfile = (data)      => api.post('/linkedin/', data).then(r => r.data)
export const upsertLinkedInProfile = (userId, data) => api.put(`/linkedin/user/${userId}`, data).then(r => r.data)
export const deleteLinkedInProfile = (userId)    => api.delete(`/linkedin/user/${userId}`).then(r => r.data)
// ── Opportunities ────────────────────────────────────────────────────────
export const getOpportunities = (userId) => api.get(`/opportunities/${userId}/discover`).then(r => r.data)

// ── Reasoning Agent ──────────────────────────────────────────────────────
export const analyzeProfile      = (data)   => api.post('/agent/analyze', data).then(r => r.data)
export const simulateCareer      = (data)   => api.post('/agent/simulate', data).then(r => r.data)
export const analyzeResumeText   = (data)   => api.post('/agent/resume-analyze', data).then(r => r.data)
export const uploadResumePDF     = (formData) => api.post('/agent/resume-upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
}).then(r => r.data)
export const getJobReadiness     = (data)   => api.post('/agent/job-readiness', data).then(r => r.data)
export const getProjectMentor    = (data)   => api.post('/agent/project-mentor', data).then(r => r.data)
export const agentChat           = (data)   => api.post('/agent/chat', data).then(r => r.data)
export const listCareers         = ()       => api.get('/agent/careers').then(r => r.data)

export { api }
