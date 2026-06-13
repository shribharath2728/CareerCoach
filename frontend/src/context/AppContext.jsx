import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [user, setUser]   = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) }
    catch { return null }
  })
  const [toasts, setToasts] = useState([])
  const [activePage, setActivePage] = useState('dashboard')

  // ── Agent Memory & State ──────────────────────────────────────────
  const [agentProfile, setAgentProfile] = useState(() => {
    try { return JSON.parse(localStorage.getItem('agentProfile')) || {} }
    catch { return {} }
  })
  const [agentMemory, setAgentMemory] = useState({
    profileCollected: false,
    careerGoalSet: false,
    analysisRun: false,
  })
  const [reasoningSteps, setReasoningSteps] = useState([])
  const [careerMatch, setCareerMatch] = useState(null)
  const [skillGaps, setSkillGaps] = useState(null)
  const [roadmap, setRoadmap] = useState(null)
  const [lastAnalysis, setLastAnalysis] = useState(null)

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  // Persist user
  useEffect(() => {
    if (user) localStorage.setItem('user', JSON.stringify(user))
    else localStorage.removeItem('user')
  }, [user])

  // Persist agent profile
  useEffect(() => {
    if (agentProfile && Object.keys(agentProfile).length > 0) {
      localStorage.setItem('agentProfile', JSON.stringify(agentProfile))
    }
  }, [agentProfile])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  const addToast = (message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }

  const logout = () => {
    setUser(null)
    setActivePage('dashboard')
    setAgentProfile({})
    setAgentMemory({ profileCollected: false, careerGoalSet: false, analysisRun: false })
    setReasoningSteps([])
    setCareerMatch(null)
    setSkillGaps(null)
    setRoadmap(null)
    setLastAnalysis(null)
  }

  const updateAgentProfile = useCallback((updates) => {
    setAgentProfile(prev => {
      const next = { ...prev, ...updates }
      // Auto-detect memory flags
      const hasProfile = !!(next.name && next.skills?.length > 0)
      const hasGoal = !!next.career_goal
      setAgentMemory(m => ({
        ...m,
        profileCollected: hasProfile,
        careerGoalSet: hasGoal,
      }))
      return next
    })
  }, [])

  const storeAnalysisResult = useCallback((result) => {
    if (!result) return
    setLastAnalysis(result)
    if (result.reasoning_steps) setReasoningSteps(result.reasoning_steps)
    if (result.confidence_score) setCareerMatch(result.confidence_score)
    if (result.skill_gaps) setSkillGaps(result.skill_gaps)
    if (result.roadmap) setRoadmap(result.roadmap)
    setAgentMemory(m => ({ ...m, analysisRun: true }))
  }, [])

  return (
    <AppContext.Provider value={{
      theme, toggleTheme,
      user, setUser,
      toasts, addToast,
      activePage, setActivePage,
      logout,
      // Agent state
      agentProfile, updateAgentProfile, setAgentProfile,
      agentMemory, setAgentMemory,
      reasoningSteps, setReasoningSteps,
      careerMatch, setCareerMatch,
      skillGaps, setSkillGaps,
      roadmap, setRoadmap,
      lastAnalysis, storeAnalysisResult,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
