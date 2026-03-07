import { useState, useEffect } from 'react'

export default function TheftAlert({ event, onDismiss }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 30)
    return () => clearTimeout(t)
  }, [])

  const dismiss = () => {
    setVisible(false)
    setTimeout(onDismiss, 400)
  }

  return (
    <div className={`theft-alert ${visible ? 'visible' : ''}`}>
      <div className="alert-header">
        <div className="alert-title">
          <span className="alert-icon">⚠</span>
          THEFT DETECTED
        </div>
        <button className="btn-dismiss" onClick={dismiss}>✕</button>
      </div>

      <div className="alert-body">
        <div>Confidence: <span className="val-red">{Number(event.confidence).toFixed(1)}%</span></div>
        <div>Voltage: <span className="val-amber">{Number(event.voltage).toFixed(1)}V</span></div>
        <div>Current: <span className="val-amber">{Number(event.current).toFixed(2)}A</span></div>
      </div>

      {event.tx && (
        <div className="alert-tx">
          ✓ On-chain reward TX submitted
        </div>
      )}
    </div>
  )
}
