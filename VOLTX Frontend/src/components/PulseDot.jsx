export default function PulseDot({ color }) {
  return (
    <span className="pulse-dot">
      <span className="ring" style={{ background: color }} />
      <span className="core" style={{ background: color }} />
    </span>
  )
}
