/**
 * useFaceAnalysis.js
 * Real-time facial analysis hook using canvas pixel heuristics.
 * Produces confidence + clarity scores every interval.
 *
 * Metrics:
 *  - Brightness variance  → face present & illuminated
 *  - Frame-to-frame motion → fidget penalty (too much = nervous, too little = frozen)
 *  - Centre-of-mass drift  → posture / gaze stability
 *  - Skin-tone area ratio  → face coverage (proxy for camera alignment)
 */

import { useEffect, useRef, useState, useCallback } from 'react'

const CANVAS_W = 160
const CANVAS_H = 120
const INTERVAL_MS = 1200 // analyse every 1.2 s

function luma(r, g, b) {
  return 0.299 * r + 0.587 * g + 0.114 * b
}

function isSkinTone(r, g, b) {
  // Broad skin-tone heuristic (works across multiple ethnicities)
  return (
    r > 60 && g > 40 && b > 20 &&
    r > g && r > b &&
    Math.abs(r - g) > 10 &&
    r - Math.min(g, b) > 20
  )
}

function analyseFrame(prev, curr, width, height) {
  const len = width * height
  let lumaSum = 0
  let lumaMin = 255
  let lumaMax = 0
  let skinPixels = 0
  let motionSum = 0
  let cx = 0 // weighted centre-of-mass x
  let cy = 0

  for (let i = 0; i < len; i++) {
    const idx = i * 4
    const r = curr[idx], g = curr[idx + 1], b = curr[idx + 2]
    const l = luma(r, g, b)
    lumaSum += l
    if (l < lumaMin) lumaMin = l
    if (l > lumaMax) lumaMax = l

    if (isSkinTone(r, g, b)) {
      skinPixels++
      cx += (i % width)
      cy += Math.floor(i / width)
    }

    if (prev) {
      const pr = prev[idx], pg = prev[idx + 1], pb = prev[idx + 2]
      motionSum += Math.abs(r - pr) + Math.abs(g - pg) + Math.abs(b - pb)
    }
  }

  const lumaAvg = lumaSum / len
  const lumaRange = lumaMax - lumaMin
  const skinRatio = skinPixels / len
  const motionAvg = prev ? motionSum / (len * 3) : 0

  // centre-of-mass — normalised 0-1
  const faceCx = skinPixels > 0 ? cx / skinPixels / width : 0.5
  const faceCy = skinPixels > 0 ? cy / skinPixels / height : 0.5

  return { lumaAvg, lumaRange, skinRatio, motionAvg, faceCx, faceCy }
}

function computeScores(metrics, prevMetrics) {
  const { lumaAvg, lumaRange, skinRatio, motionAvg, faceCx, faceCy } = metrics

  // --- Face Presence (0-100) ---
  // Good skin ratio: 0.05 – 0.35 of frame
  const facePresence = Math.min(100, Math.max(0, (skinRatio - 0.01) / 0.30 * 100))

  // --- Lighting Quality (0-100) ---
  // Ideal luma avg 80-160, range > 40 means face detail
  const lightingScore = Math.min(100, Math.max(0,
    (lumaAvg > 40 && lumaAvg < 220 ? 60 : 20) +
    (lumaRange > 50 ? 40 : lumaRange > 25 ? 20 : 0)
  ))

  // --- Gaze / Posture Stability (0-100) ---
  // Face cx should be near 0.4-0.6 (centred), cy near 0.25-0.55
  const horzDev = Math.abs(faceCx - 0.5)  // 0 = centred
  const vertDev = Math.abs(faceCy - 0.4)
  const gazeScore = Math.max(0, 100 - horzDev * 200 - vertDev * 150)

  // --- Motion (nervousness) penalty (0-100) ---
  // motionAvg: 0 = still, ~15 = normal movement, >30 = fidgeting
  const IDEAL_MOTION_MIN = 1
  const IDEAL_MOTION_MAX = 12
  let motionScore
  if (motionAvg < 0.5) {
    // Completely still — might be frozen / no face
    motionScore = 40
  } else if (motionAvg <= IDEAL_MOTION_MAX) {
    // Comfortable zone
    motionScore = Math.min(100, 60 + (motionAvg / IDEAL_MOTION_MAX) * 40)
  } else {
    // Too much movement
    motionScore = Math.max(10, 100 - (motionAvg - IDEAL_MOTION_MAX) * 4)
  }

  // --- Confidence Score ---
  // Weighted: gaze stability (40%), motion quality (35%), face presence (25%)
  const confidence = Math.round(
    gazeScore * 0.40 +
    motionScore * 0.35 +
    facePresence * 0.25
  )

  // --- Clarity Score ---
  // Weighted: lighting (50%), face presence (30%), gaze (20%)
  const clarity = Math.round(
    lightingScore * 0.50 +
    facePresence * 0.30 +
    gazeScore * 0.20
  )

  return {
    confidence: Math.min(100, Math.max(0, confidence)),
    clarity: Math.min(100, Math.max(0, clarity)),
    facePresence: Math.round(facePresence),
    motionScore: Math.round(motionScore),
    gazeScore: Math.round(gazeScore),
    lightingScore: Math.round(lightingScore),
    skinRatio: Math.round(skinRatio * 100),
    motionAvg: Math.round(motionAvg * 10) / 10,
  }
}

function getFeedback(scores) {
  const tips = []

  if (scores.facePresence < 30) {
    tips.push({ type: 'warn', msg: 'Move closer to camera — face not fully visible.' })
  }
  if (scores.lightingScore < 45) {
    tips.push({ type: 'warn', msg: 'Improve lighting — face appears too dark or overexposed.' })
  }
  if (scores.gazeScore < 45) {
    tips.push({ type: 'warn', msg: 'Centre yourself — maintain eye contact with the camera.' })
  }
  if (scores.motionAvg > 18) {
    tips.push({ type: 'warn', msg: 'Reduce fidgeting — stay composed and still.' })
  } else if (scores.motionAvg < 0.8 && scores.facePresence > 20) {
    tips.push({ type: 'info', msg: 'Nod occasionally — natural movement shows engagement.' })
  }
  if (scores.confidence >= 75 && scores.clarity >= 70) {
    tips.push({ type: 'good', msg: 'Great posture and presence — keep it up!' })
  } else if (scores.confidence >= 55) {
    tips.push({ type: 'info', msg: 'Looking good — relax your shoulders and speak steadily.' })
  }

  return tips
}

export default function useFaceAnalysis(videoRef, enabled = true) {
  const canvasRef = useRef(document.createElement('canvas'))
  const prevPixelsRef = useRef(null)
  const intervalRef = useRef(null)
  const [scores, setScores] = useState(null)
  const [feedback, setFeedback] = useState([])
  const [history, setHistory] = useState([]) // last N scores for sparkline

  const analyse = useCallback(() => {
    const video = videoRef.current
    if (!video || video.readyState < 2) return

    const canvas = canvasRef.current
    canvas.width = CANVAS_W
    canvas.height = CANVAS_H
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    ctx.drawImage(video, 0, 0, CANVAS_W, CANVAS_H)

    const imageData = ctx.getImageData(0, 0, CANVAS_W, CANVAS_H)
    const pixels = imageData.data

    const metrics = analyseFrame(prevPixelsRef.current, pixels, CANVAS_W, CANVAS_H)
    const newScores = computeScores(metrics)
    const tips = getFeedback(newScores)

    prevPixelsRef.current = new Uint8ClampedArray(pixels)
    setScores(newScores)
    setFeedback(tips)
    setHistory(h => [...h.slice(-14), { confidence: newScores.confidence, clarity: newScores.clarity }])
  }, [videoRef])

  useEffect(() => {
    if (!enabled) {
      clearInterval(intervalRef.current)
      return
    }
    // Give camera time to warm up
    const startDelay = setTimeout(() => {
      intervalRef.current = setInterval(analyse, INTERVAL_MS)
    }, 1500)
    return () => {
      clearTimeout(startDelay)
      clearInterval(intervalRef.current)
    }
  }, [enabled, analyse])

  const reset = useCallback(() => {
    prevPixelsRef.current = null
    setScores(null)
    setFeedback([])
    setHistory([])
  }, [])

  return { scores, feedback, history, reset }
}
