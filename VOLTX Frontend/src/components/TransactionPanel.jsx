import { useState } from 'react'
import PulseDot from './PulseDot'

export default function TransactionPanel({ status }) {
  const [copied, setCopied] = useState(false)
  const tx = status?.tx

  const copy = () => {
    navigator.clipboard?.writeText(tx).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`card ${tx ? 'glow-purple' : ''}`}>
      <div className="ai-section-title">BLOCKCHAIN REWARD</div>

      {tx ? (
        <>
          <div className="tx-submitted">
            <PulseDot color="#a78bfa" />
            TX SUBMITTED TO SOLANA
          </div>

          <div className="tx-hash-box">
            <div className="tx-hash-label">SIGNATURE</div>
            <div className="tx-hash-value">{tx.slice(0, 32)}...</div>
          </div>

          <div className="tx-actions">
            <button className="btn-tx" onClick={copy}>
              {copied ? '✓ COPIED!' : '⧉ COPY TX'}
            </button>
            <a
              className="btn-tx"
              href={`https://explorer.solana.com/tx/${tx}?cluster=devnet`}
              target="_blank"
              rel="noreferrer"
            >
              🔗 EXPLORER
            </a>
          </div>
        </>
      ) : (
        <div className="tx-empty">
          <span className="tx-empty-icon">🔗</span>
          <p>Awaiting theft detection<br />to trigger on-chain reward</p>
        </div>
      )}
    </div>
  )
}
