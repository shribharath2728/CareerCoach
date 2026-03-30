import { MdCheckCircle, MdInfo, MdStar } from 'react-icons/md'

export default function EvaluationPanel({ evaluation }) {
  if (!evaluation) return null

  const {
    overall_score,
    feedback_summary,
    strengths,
    improvements,
    missed_points,
    hiring_signal,
    difficulty_recommendation,
    problem_solving_score,
    technical_score,
    communication_score,
    structure_score,
    completeness_score,
    confidence_score,
  } = evaluation

  const scoreColor = (s) => 
    s >= 80 ? 'var(--success)' : 
    s >= 50 ? 'var(--warning)' : 
    'var(--danger)'

  return (
    <div className="card eval-panel" style={{ borderLeft: `4px solid ${scoreColor(overall_score)}` }}>
      <div className="eval-header">
        <div className="score-ring">
          <svg width="80" height="80">
            <circle cx="40" cy="40" r="32" fill="none" stroke="var(--border)" strokeWidth="6" />
            <circle 
              cx="40" cy="40" r="32" 
              fill="none" 
              stroke={scoreColor(overall_score)} 
              strokeWidth="6" 
              strokeDasharray="200" 
              strokeDashoffset={200 - (overall_score / 100) * 200}
              strokeLinecap="round" 
              style={{ transition: 'stroke-dashoffset 1s ease-out' }} 
            />
          </svg>
          <div className="score-ring-value" style={{ color: scoreColor(overall_score) }}>
            {overall_score}
          </div>
        </div>

        <div>
          <h3 style={{ fontFamily: 'Outfit', fontSize: '1.2rem', marginBottom: 4 }}>Evaluation Summary</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Hiring Signal: <strong style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{hiring_signal}</strong> |
            Recommended Diff.: <strong style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{difficulty_recommendation}</strong>
          </p>
        </div>
      </div>

      <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.6, marginTop: 8 }}>
        {feedback_summary}
      </p>

      <div className="divider" style={{ margin: '14px 0' }} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
        {/* Dimension Scores */}
        <div>
          <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>Score Breakdown</h4>
          <div className="eval-dims">
          {[
              { label: 'Technical', val: technical_score || 0 },
              { label: 'Problem Solving', val: problem_solving_score || 0 },
              { label: 'Communication', val: communication_score || 0 },
              { label: 'Structure', val: structure_score || 0 },
              { label: 'Completeness', val: completeness_score || 0 },
              { label: 'Confidence', val: confidence_score || 0 },
            ].map(d => (
              <div key={d.label} className="eval-dim-row">
                <span className="eval-dim-label">{d.label}</span>
                <div className="progress-wrap" style={{ flex: 1, height: 6 }}>
                  <div className="progress-fill" style={{ width: `${d.val}%`, background: scoreColor(d.val) }} />
                </div>
                <span className="eval-dim-score" style={{ color: scoreColor(d.val) }}>{d.val}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Feedback Points (Strengths, Improvements, Missed) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
           {strengths?.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 8 }}>
                <MdCheckCircle /> Strengths
              </h4>
             <ul style={{ paddingLeft: 18, color: 'var(--text-secondary)', fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {strengths.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
           )}

           {improvements?.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 8 }}>
                <MdInfo /> Areas for Improvement
              </h4>
               <ul style={{ paddingLeft: 18, color: 'var(--text-secondary)', fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {improvements.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
           )}

           {missed_points?.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 8 }}>
                <MdStar /> Missed Points
              </h4>
               <ul style={{ paddingLeft: 18, color: 'var(--text-secondary)', fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {missed_points.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
           )}
        </div>
      </div>
    </div>
  )
}
