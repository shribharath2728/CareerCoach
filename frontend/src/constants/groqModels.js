/**
 * Available AI model IDs — all served via Groq.
 */

export const GROQ_MODEL_OPTIONS = [
  'llama-3.3-70b-versatile',
  'llama-3.1-8b-instant',
  'meta-llama/llama-4-scout-17b-16e-instruct',
  'meta-llama/llama-4-maverick-17b-128e-instruct',
]

// Keep alias for any imports that reference ALL_MODEL_OPTIONS
export const ALL_MODEL_OPTIONS = [...GROQ_MODEL_OPTIONS]

const DEFAULT_MODEL = 'llama-3.3-70b-versatile'

export function normalizeGroqModel(id) {
  if (!id || !ALL_MODEL_OPTIONS.includes(id)) return DEFAULT_MODEL
  return id
}

export const MODEL_LABELS = {
  'llama-3.3-70b-versatile': 'Llama 3.3 70B — balanced ✨',
  'llama-3.1-8b-instant': 'Llama 3.1 8B — fastest',
  'meta-llama/llama-4-scout-17b-16e-instruct': 'Llama 4 Scout — long context',
  'meta-llama/llama-4-maverick-17b-128e-instruct': 'Llama 4 Maverick — deep reasoning',
}
