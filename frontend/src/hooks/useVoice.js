import { useCallback, useRef, useState } from 'react'

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

export function useVoiceInput({ onResult, onError } = {}) {
  const [isListening, setIsListening]   = useState(false)
  const [transcript, setTranscript]      = useState('')
  const [supported]                      = useState(!!SpeechRecognition)
  const recognitionRef                   = useRef(null)

  const start = useCallback(() => {
    if (!supported || isListening) return

    const rec = new SpeechRecognition()
    rec.continuous        = false
    rec.interimResults    = true
    rec.lang              = 'en-US'
    rec.maxAlternatives   = 1

    rec.onstart  = () => setIsListening(true)
    rec.onend    = () => setIsListening(false)
    rec.onerror  = (e) => {
      setIsListening(false)
      onError?.(e.error)
    }
    rec.onresult = (e) => {
      const t = Array.from(e.results)
        .map(r => r[0].transcript)
        .join('')
      setTranscript(t)
      if (e.results[e.results.length - 1].isFinal) {
        onResult?.(t)
      }
    }

    recognitionRef.current = rec
    rec.start()
  }, [supported, isListening, onResult, onError])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const toggle = useCallback(() => {
    isListening ? stop() : start()
  }, [isListening, start, stop])

  return { isListening, transcript, supported, start, stop, toggle, setTranscript }
}

const synth = window.speechSynthesis

export function speak(text, { rate = 1, pitch = 1, volume = 0.9, voice = null } = {}) {
  if (!synth) return
  synth.cancel()
  const utt = new SpeechSynthesisUtterance(text)
  utt.rate   = rate
  utt.pitch  = pitch
  utt.volume = volume
  if (voice) utt.voice = voice
  synth.speak(utt)
}

export function stopSpeaking() {
  synth?.cancel()
}

export function getVoices() {
  return synth ? synth.getVoices() : []
}
