export default function SparkLine({ data, color, width = 200, height = 40 }) {
  if (!data || data.length < 2) return <div style={{ height }} />
  const vals = data.map(d => (typeof d === 'object' ? d.v : d))
  const min = Math.min(...vals), max = Math.max(...vals)
  const range = max - min || 1
  const pad = 4
  const pts = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * width
    const y = height - ((v - min) / range) * (height - pad * 2) - pad
    return `${x},${y}`
  })
  const area = `M${pts[0]} ` + pts.slice(1).map(p => `L${p}`).join(' ') + ` L${width},${height} L0,${height} Z`
  const line = `M${pts[0]} ` + pts.slice(1).map(p => `L${p}`).join(' ')
  const gid = `sg${color.replace(/[^a-z0-9]/gi, '')}`
  return (
    <svg width={width} height={height} style={{ overflow: 'visible', display: 'block' }}>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
