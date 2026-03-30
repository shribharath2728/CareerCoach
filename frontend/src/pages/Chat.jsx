import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { useApp } from '../context/AppContext'
import { useVoiceInput, speak, stopSpeaking } from '../hooks/useVoice'
import { MdSend, MdMic, MdStop, MdChatBubbleOutline } from 'react-icons/md'

function apiErrorMessage(err) {
  if (err.response?.data?.detail != null) {
    const d = err.response.data.detail
    if (typeof d === 'string') return d
    if (Array.isArray(d)) return d.map((e) => e?.msg || JSON.stringify(e)).join('; ')
  }
  if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
    return 'Request timed out. Check that the SkillLens API is running (port 8000).'
  }
  if (!err.response && err.message === 'Network Error') {
    return 'Cannot reach the API. Start the backend: `cd backend` then `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`. Keep the UI on `npm run dev` (Vite proxies /api). Then refresh.'
  }
  return err.message || 'Request failed'
}

export default function Chat() {
  const { user, addToast } = useApp()
  const [messages, setMessages] = useState([
    { id: 1, sender: 'ai', text: `Hi ${user.full_name.split(' ')[0]}! I'm ${user.ai_name}, your SkillLens coach. How can I help you today?` }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ttsOn, setTtsOn] = useState(false)
  
  const bottomRef = useRef(null)

  // API Integration for chat session
  const [sessions, setSessions] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [sessionLoading, setSessionLoading] = useState(true)
  const initialized = useRef(false)

  const handleSendRef = useRef(null)

  const { isListening, transcript, supported, toggle: toggleVoice } = useVoiceInput({
    onResult: (t) => {
      setInput(t)
      handleSendRef.current?.(t)
    },
    onError:  (e) => addToast(`Voice error: ${e}`, 'error'),
  })

  // Auto scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const loadSessions = useCallback(async () => {
    setSessionLoading(true)
    try {
      const { listChatSessions } = await import('../services/api')
      const sessList = await listChatSessions(user.id)
      setSessions(sessList)
      if (sessList.length > 0 && !sessionId) {
        setSessionId(sessList[0].id)
      }
    } catch (err) {
      addToast('Failed to load chat sessions', 'error')
    } finally {
      setSessionLoading(false)
    }
  }, [user.id, sessionId, addToast])

  const loadMessages = useCallback(async (sid) => {
    if (!sid) return
    setSessionLoading(true)
    try {
      const { listChatMessages } = await import('../services/api')
      const apiMessages = await listChatMessages(sid)
      const mapped = apiMessages.map(m => ({
        id: m.id,
        sender: m.sender === 'user' ? 'user' : 'ai',
        text: m.message
      }))
      setMessages(mapped.length > 0 ? mapped : [
        { id: 'welcome', sender: 'ai', text: `Hi ${user.full_name.split(' ')[0]}! I'm ${user.ai_name}, your SkillLens coach. How can I help you today?` }
      ])
    } catch (err) {
      addToast('Failed to load messages', 'error')
    } finally {
      setSessionLoading(false)
    }
  }, [user.id, user.ai_name, addToast])

  // Initial load
  useEffect(() => {
    if (initialized.current) return
    initialized.current = true
    loadSessions()
  }, [loadSessions])

  // Load messages when session changes
  useEffect(() => {
    if (sessionId) {
      loadMessages(sessionId)
    }
  }, [sessionId, loadMessages])

  const handleCreateSession = async () => {
    setSessionLoading(true)
    try {
      const { createChatSession } = await import('../services/api')
      const newSess = await createChatSession({ user_id: user.id, title: `Chat ${sessions.length + 1}` })
      setSessions(prev => [newSess, ...prev])
      setSessionId(newSess.id)
      setMessages([{ id: 'welcome', sender: 'ai', text: `Starting a new chat... How can I assist you?` }])
    } catch (err) {
      addToast('Failed to create new chat', 'error')
    } finally {
      setSessionLoading(false)
    }
  }

  const handleSend = useCallback(async (textOverride) => {
    const text = typeof textOverride === 'string' ? textOverride : input
    if (!text.trim()) return
    if (!sessionId) {
      addToast('Select a chat or start a new one first.', 'warning')
      return
    }

    const tempId = Date.now()
    const userMsg = { id: tempId, sender: 'user', text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    stopSpeaking()

    try {
      const { createChatMessage } = await import('../services/api')
      const result = await createChatMessage({
        session_id: sessionId,
        content: text,
        role: 'user',
      })

      const aiReply = result.assistant_message.message

      setMessages(prev => [
        ...prev.filter(m => m.id !== tempId),
        { id: result.user_message.id, sender: 'user', text },
        { id: result.assistant_message.id, sender: 'ai', text: aiReply }
      ])

      if (ttsOn) speak(aiReply)
    } catch (err) {
      setMessages(prev => prev.filter(m => m.id !== tempId))
      addToast(apiErrorMessage(err), 'error')
    } finally {
      setLoading(false)
    }
  }, [input, sessionId, ttsOn, addToast])

  handleSendRef.current = handleSend

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
       e.preventDefault()
       handleSend()
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', height: 'calc(100vh - 120px)', gap: 16 }}>
      
      {/* Session Sidebar */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 14px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--text-secondary)' }}>CHAT HISTORY</span>
          <button className="btn btn-sm btn-ghost" onClick={handleCreateSession} title="New Chat" style={{ padding: '4px 8px' }}>
            ＋ New
          </button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 8px', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setSessionId(s.id)}
              className={`nav-item ${sessionId === s.id ? 'active' : ''}`}
              style={{ padding: '8px 12px', fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
            >
              <MdChatBubbleOutline />
              {s.session_name || s.title || `Chat ${s.id}`}
            </button>
          ))}
          {!sessionLoading && sessions.length === 0 && (
            <div style={{ textAlign: 'center', padding: '20px 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              No chat history.
            </div>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-card)', zIndex: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="chat-avatar ai" style={{ width: 40, height: 40, fontSize: '1.2rem' }}>🧠</div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontFamily: 'Outfit', lineHeight: 1.1 }}>{user.ai_name}</h3>
              <span style={{ fontSize: '0.78rem', color: sessionLoading ? 'var(--text-muted)' : 'var(--success)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: sessionLoading ? 'var(--text-muted)' : 'var(--success)', display: 'inline-block' }}></span>{' '}
                {sessionLoading ? 'Loading Chat…' : 'Online'}
              </span>
            </div>
          </div>
          
          <button 
            className={`btn btn-sm ${ttsOn ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setTtsOn(!ttsOn); if(ttsOn) stopSpeaking() }}
          >
            {ttsOn ? '🔊 Voice On' : '🔇 Voice Off'}
          </button>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 24px', display: 'flex', flexDirection: 'column' }}>
          <AnimatePresence>
            {messages.map(m => (
              <motion.div 
                key={m.id}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`chat-message ${m.sender}`}
              >
                <div className={`chat-avatar ${m.sender}`}>
                  {m.sender === 'ai' ? '🧠' : user.full_name[0].toUpperCase()}
                </div>
                <div
                  className={`chat-bubble ${m.sender}${m.sender === 'ai' ? ' chat-bubble-md' : ''}`}
                >
                  {m.sender === 'ai' ? (
                    <ReactMarkdown>{m.text}</ReactMarkdown>
                  ) : (
                    m.text
                  )}
                </div>
              </motion.div>
            ))}
            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={`chat-message ai`}>
                <div className={`chat-avatar ai`}>🧠</div>
                <div className={`chat-bubble ai`} style={{ padding: '8px 16px' }}>
                  <div className="ai-thinking"><span/><span/><span/></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)', background: 'var(--bg-tertiary)', display: 'flex', gap: 10, alignItems: 'flex-end' }}>
          
          {supported && (
            <button 
              className={`mic-btn ${isListening ? 'recording' : 'idle'}`} 
              style={{ width: 46, height: 46, flexShrink: 0 }}
              onClick={toggleVoice}
              title={isListening ? 'Stop recording' : 'Speak'}
            >
              {isListening ? <MdStop /> : <MdMic />}
            </button>
          )}

          <div style={{ flex: 1, position: 'relative' }}>
             {isListening && (
              <div style={{ position: 'absolute', bottom: '100%', left: 0, marginBottom: 8, padding: '4px 12px', background: 'var(--danger)', color: 'white', borderRadius: 12, fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, animation: 'pulse-ring 1.5s infinite' }}>
                 Listening… {transcript && <span style={{ opacity: 0.8, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{transcript}</span>}
              </div>
            )}
            <textarea 
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isListening ? "Listening..." : "Message SkillLens... (Shift+Enter for new line)"}
              style={{ width: '100%', minHeight: 46, maxHeight: 120, resize: 'none', padding: '12px 16px', background: 'var(--bg-card)' }}
              disabled={loading || isListening || sessionLoading}
            />
          </div>

          <button 
            className="btn btn-primary" 
            style={{ width: 46, height: 46, borderRadius: 'var(--radius-sm)', padding: 0, justifyContent: 'center', flexShrink: 0 }}
            onClick={() => handleSend()}
            disabled={loading || !input.trim() || isListening || sessionLoading || !sessionId}
          >
            <MdSend style={{ fontSize: '1.2rem', marginLeft: 2 }} />
          </button>
        </div>
      </div>
    </div>
  )
}
