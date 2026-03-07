import PulseDot from './PulseDot'

export default function StatusCards({ status }) {
  const conf = Number(status.confidence ?? 0)    // 0-100 from your backend
  // theft is ONLY true when backend model explicitly says theft=true (boolean)
  const isTheft = status.theft === true

  const cards = [
    {
      label: 'VOLTAGE',
      value: `${Number(status.voltage).toFixed(1)}V`,
      sub: 'Grid input',
      color: '#3b82f6',
      glow: 'glow-blue',
    },
    {
      label: 'CURRENT',
      value: `${Number(status.current).toFixed(2)}A`,
      sub: 'Load draw',
      color: '#06b6d4',
      glow: 'glow-cyan',
    },
    {
      label: 'AI CONFIDENCE',
      value: `${Number(conf).toFixed(1)}%`,
      sub: isTheft ? 'Anomaly found' : 'Within normal',
      color: isTheft ? '#ef4444' : '#22c55e',
      glow: isTheft ? 'glow-red' : 'glow-green',
    },
    {
      label: 'SYSTEM STATUS',
      value: isTheft ? 'ALERT' : 'NOMINAL',
      sub: isTheft ? 'Theft detected' : 'All clear',
      color: isTheft ? '#ef4444' : '#22c55e',
      glow: isTheft ? 'glow-red' : 'glow-green',
      flicker: isTheft,
    },
  ]

  return (
    <div className="status-grid">
      {cards.map(card => (
        <div key={card.label} className={`card stat-card ${card.glow}`}>
          <div className="stat-label">{card.label}</div>
          <div
            className="stat-value"
            style={{
              color: card.color,
              textShadow: `0 0 20px ${card.color}44`,
              animation: card.flicker ? 'flicker 0.8s ease-in-out infinite' : 'none',
            }}
          >
            {card.value}
          </div>
          <div className="stat-sub">{card.sub}</div>
          <div className="stat-dot">
            <PulseDot color={card.color} />
          </div>
        </div>
      ))}
    </div>
  )
}
