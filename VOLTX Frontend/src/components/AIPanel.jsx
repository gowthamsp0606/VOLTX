export default function AIPanel({ status }) {
  const conf = Number(status.confidence ?? 0)   // 0-100 from your backend
  // ONLY show ANOMALY when backend explicitly returns theft: true
  const isTheft = status.theft === true
  const clampedConf = Math.min(Math.max(conf, 0), 100)

  return (
    <div className={`card ${isTheft ? 'glow-red' : 'glow-green'}`}>
      <div className="ai-section-title">AI DETECTION ENGINE</div>

      {/* Confidence bar */}
      <div className="confidence-bar-wrap">
        <div className="confidence-track">
          <div
            className="confidence-fill"
            style={{
              width: `${clampedConf}%`,
              background: conf > 50
                ? 'linear-gradient(90deg, #f97316, #ef4444)'
                : 'linear-gradient(90deg, #22c55e, #16a34a)',
              boxShadow: conf > 50 ? '0 0 10px #ef444455' : '0 0 10px #22c55e55',
            }}
          />
        </div>
        <div className="confidence-labels">
          <span>0%</span>
          <span className="conf-val" style={{ color: conf > 50 ? '#ef4444' : '#22c55e' }}>
            {clampedConf.toFixed(2)}%
          </span>
          <span>100%</span>
        </div>
      </div>

      {/* Result box */}
      <div className={`ai-result-box ${isTheft ? 'theft' : 'normal'}`}>
        <div className="ai-result-title" style={{ color: isTheft ? '#ef4444' : '#22c55e' }}>
          <span style={{ animation: isTheft ? 'flicker 0.8s infinite' : 'none' }}>
            {isTheft ? '⚠' : '✓'}
          </span>
          {isTheft ? 'ANOMALY DETECTED' : 'NORMAL OPERATION'}
        </div>
        <p className="ai-result-desc">
          {isTheft
            ? 'Unauthorized tap suspected on grid line. Blockchain reward triggered.'
            : 'All sensor readings within expected operational parameters.'}
        </p>
      </div>
    </div>
  )
}
