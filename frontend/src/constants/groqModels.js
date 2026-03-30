/** IDs that match Groq’s currently supported chat models (see console.groq.com). */
export const GROQ_MODEL_OPTIONS = [
  'llama-3.3-70b-versatile',
  'llama-3.1-8b-instant',
  'meta-llama/llama-4-scout-17b-16e-instruct',
  'meta-llama/llama-4-maverick-17b-128e-instruct',
]

const DEFAULT_MODEL = 'llama-3.3-70b-versatile'

export function normalizeGroqModel(id) {
  if (!id || !GROQ_MODEL_OPTIONS.includes(id)) return DEFAULT_MODEL
  return id
}
