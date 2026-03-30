import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { useVoiceInput, speak, stopSpeaking } from '../hooks/useVoice'
import { MdMic, MdMicOff, MdStop, MdVolumeUp } from 'react-icons/md'

export default function VoiceAssistant() {
  const { user, addToast } = useApp()
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentText, setCurrentText] = useState('')
  const [aiResponse, setAiResponse] = useState(`Hi ${user.full_name.split(' ')[0]}! I'm your AI Voice Assistant. Speak to me anytime.`)
  const initialized = useRef(false)

  // Auto-speak initial greeting once mounted
  useEffect(() => {
    if (!initialized.current) {
        speak(aiResponse)
    }
  }, [aiResponse])

  // Fetch or create a dedicated voice session on mount
  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    import('../services/api').then(({ listChatSessions, createChatSession }) => {
      // Find a specific "Voice Assistant" session, or create one
      listChatSessions(user.id)
        .then(sessions => {
          const voiceSession = sessions.find(s => (s.session_name || s.title) === 'Voice Assistant')
          if (voiceSession) {
            setSessionId(voiceSession.id)
          } else {
            return createChatSession({ user_id: user.id, title: "Voice Assistant" })
              .then(sess => {
                setSessionId(sess.id)
              })
          }
        })
        .catch(err => {
          const msg = err.response?.data?.detail || err.message || String(err)
          addToast('Failed to init voice session: ' + msg, 'error')
        })
    })

    // Stop speaking when leaving the page
    return () => stopSpeaking()
  }, [user.id, addToast])

  const handleSend = async (text) => {
    if (!text.trim() || !sessionId) return

    setCurrentText(text)
    setLoading(true)
    stopSpeaking()

    try {
      const { createChatMessage } = await import('../services/api')
      const result = await createChatMessage({
        session_id: sessionId,
        content: text,
        role: 'user',
      })

      const reply = result.assistant_message.message
      setAiResponse(reply)
      speak(reply)

    } catch (err) {
      const detail = err.response?.data?.detail;
      const errMsg = typeof detail === 'string' ? detail : "Voice API failed";
      addToast(errMsg, "error")
    } finally {
      setLoading(false)
    }
  }

  // Set up voice
  const { isListening, transcript, supported, toggle: toggleVoice } = useVoiceInput({
    onResult: (t) => {
        handleSend(t)
    },
    onError:  (e) => addToast(`Voice recognition error: ${e}`, 'error'),
  })

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 120px)', position: 'relative', overflow: 'hidden' }}>
      
      {/* Background ripples */}
      {isListening && (
        <div style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <motion.div animate={{ scale: [1, 2.5, 3], opacity: [0.3, 0.1, 0] }} transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }} style={{ width: 100, height: 100, borderRadius: '50%', background: 'var(--accent)', position: 'absolute' }} />
          <motion.div animate={{ scale: [1, 2, 2.8], opacity: [0.3, 0.1, 0] }} transition={{ duration: 2, delay: 0.5, repeat: Infinity, ease: 'easeOut' }} style={{ width: 100, height: 100, borderRadius: '50%', background: 'var(--accent)', position: 'absolute' }} />
        </div>
      )}

      <div style={{ zIndex: 10, textAlign: 'center', maxWidth: 600, width: '100%' }}>
        <h2 style={{ fontFamily: 'Outfit', fontSize: '2.4rem', marginBottom: 10 }}>Voice Assistant</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: 40, fontSize: '1.1rem' }}>Tap the microphone and start speaking</p>

        {/* Central Orb / Button */}
        <button 
          onClick={() => {
              if (loading) return
              toggleVoice()
          }}
          disabled={loading}
          style={{
            width: 140, height: 140, borderRadius: '50%',
            background: isListening ? 'var(--danger)' : loading ? 'var(--warning)' : 'var(--primary)',
            color: 'white', border: 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '3.5rem', cursor: loading ? 'not-allowed' : 'pointer',
            boxShadow: isListening ? '0 0 40px rgba(220, 53, 69, 0.6)' : '0 10px 25px rgba(0,0,0,0.1)',
            margin: '0 auto 40px auto', transition: 'all 0.3s ease'
          }}
        >
          {loading ? <span className="spinner" style={{ width: 40, height: 40, borderBottomColor: 'white' }} /> : isListening ? <MdStop /> : <MdMic />}
        </button>

        {/* Transcript Box */}
        <div style={{ minHeight: 120, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)', padding: 24, textAlign: 'left', border: '1px solid var(--border)' }}>
          {isListening ? (
             <div>
               <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 8, fontWeight: 600 }}>Listening...</p>
               <p style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>{transcript || "..."}</p>
             </div>
          ) : currentText && (
             <div style={{ marginBottom: 16 }}>
               <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 8, fontWeight: 600 }}>You asked:</p>
               <p style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>{currentText}</p>
             </div>
          )}
          
          <AnimatePresence>
            {!isListening && aiResponse && (
               <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ marginTop: 24, paddingTop: 24, borderTop: '1px solid var(--border)' }}>
                 <p style={{ color: 'var(--accent)', fontSize: '0.9rem', marginBottom: 8, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                   <MdVolumeUp /> Assistant
                 </p>
                 <p style={{ fontSize: '1.1rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>{aiResponse}</p>
               </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </div>
  )
}
