import {
  ResponsiveContainer, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts'
import PulseDot from './PulseDot'

function Chart({ title, data, dataKey, color, unit }) {
  const vals = data.map(d => d.v)
  const min = vals.length ? Math.min(...vals) : 0
  const max = vals.length ? Math.max(...vals) : 0
  const now = vals.length ? vals[vals.length - 1] : 0

  const chartData = data.map((d, i) => ({ i, v: d.v }))

  return (
    <div className="card">
      <div className="chart-header">
        <span className="chart-title">{title}</span>
        <span className="chart-live">
          <PulseDot color={color} /> LIVE
        </span>
      </div>

      <ResponsiveContainer width="100%" height={90}>
        <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,60,100,0.3)" vertical={false} />
          <XAxis dataKey="i" hide />
          <YAxis domain={['auto', 'auto']} tick={{ fontSize: 8, fill: '#334155', fontFamily: 'Share Tech Mono, monospace' }} />
          <Tooltip
            contentStyle={{ background: '#080d18', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, fontSize: 10, fontFamily: 'Share Tech Mono, monospace' }}
            labelStyle={{ color: '#475569' }}
            itemStyle={{ color: color }}
            formatter={v => [`${v.toFixed(3)}${unit}`, dataKey.toUpperCase()]}
            labelFormatter={() => ''}
          />
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={2}
            fill={`url(#grad-${dataKey})`}
            dot={false}
            activeDot={{ r: 4, fill: color, strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        <span className="chart-stat">MIN: {min.toFixed(2)}{unit}</span>
        <span className="chart-stat">MAX: {max.toFixed(2)}{unit}</span>
        <span className="chart-stat" style={{ color }}>NOW: {now.toFixed(2)}{unit}</span>
      </div>
    </div>
  )
}

export default function EnergyChart({ voltSeries, currSeries }) {
  return (
    <div className="chart-grid">
      <Chart title="VOLTAGE OVER TIME" data={voltSeries} dataKey="voltage" color="#3b82f6" unit="V" />
      <Chart title="CURRENT OVER TIME" data={currSeries} dataKey="current" color="#06b6d4" unit="A" />
    </div>
  )
}
