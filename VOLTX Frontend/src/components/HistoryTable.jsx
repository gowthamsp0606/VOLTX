import { useState } from 'react'

export default function HistoryTable({ history }) {
  const [copiedTx, setCopiedTx] = useState(null)

  const copy = (tx) => {
    navigator.clipboard?.writeText(tx).catch(() => {})
    setCopiedTx(tx)
    setTimeout(() => setCopiedTx(null), 2000)
  }

  return (
    <div className="card" style={{ marginTop: 0 }}>
      <div className="history-header">
        <span className="history-title">EVENT HISTORY</span>
        <span className="history-meta">LAST {history.length} EVENTS · POLLING /history EVERY 2s</span>
      </div>

      <div className="history-scroll">
        <table className="history-table">
          <thead>
            <tr>
              {['#', 'VOLTAGE', 'CURRENT', 'CONFIDENCE', 'STATUS', 'TX HASH'].map(h => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {history.slice(0, 20).map((row, i) => (
              <tr key={i} className={row.theft ? 'theft-row' : ''}>
                <td style={{ color: '#334155' }}>{i + 1}</td>
                <td style={{ color: '#93c5fd' }}>{Number(row.voltage).toFixed(1)}V</td>
                <td style={{ color: '#67e8f9' }}>{Number(row.current).toFixed(2)}A</td>
                <td style={{ color: row.confidence > 50 ? '#ef4444' : '#22c55e' }}>
                  {Number(row.confidence).toFixed(1)}%
                </td>
                <td>
                  <span className={`status-pill ${row.theft ? 'theft' : 'normal'}`}>
                    {row.theft ? '⚠ THEFT' : '✓ NORMAL'}
                  </span>
                </td>
                <td>
                  {row.tx
                    ? (
                      <span className="tx-link" onClick={() => copy(row.tx)}>
                        {copiedTx === row.tx ? 'COPIED!' : `${row.tx.slice(0, 14)}...`}
                      </span>
                    )
                    : <span style={{ color: '#1e293b' }}>—</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
