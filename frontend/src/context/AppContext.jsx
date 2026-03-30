import { createContext, useContext, useState, useEffect } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [user, setUser]   = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) }
    catch { return null }
  })
  const [toasts, setToasts] = useState([])
  const [activePage, setActivePage] = useState('dashboard')

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

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  const addToast = (message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }

  const logout = () => {
    setUser(null)
    setActivePage('dashboard')
  }

  return (
    <AppContext.Provider value={{
      theme, toggleTheme,
      user, setUser,
      toasts, addToast,
      activePage, setActivePage,
      logout,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
