import ReactECharts from 'echarts-for-react'

const SERIES = [
  { key: 'cpu',  label: 'CPU',   color: '#5E9E13', fill: '#5E9E1322' },
  { key: 'ram',  label: 'RAM',   color: '#0EA5E9', fill: '#0EA5E922' },
  { key: 'disk', label: 'Disco', color: '#F59E0B', fill: '#F59E0B22' },
]

function buildOption(series, data, isDark) {
  const textColor  = isDark ? '#71717A' : '#A1A1AA'
  const gridColor  = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)'
  const tooltipBg  = isDark ? '#18181B' : '#FFFFFF'
  const tooltipBdr = isDark ? '#3F3F46' : '#E4E4E7'
  const tooltipTx  = isDark ? '#E4E4E7' : '#09090B'

  const timestamps = data.map(d => {
    try {
      return new Date(d.timestamp).toLocaleTimeString('es-AR', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      })
    } catch { return d.timestamp }
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: tooltipBg,
      borderColor: tooltipBdr,
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: tooltipTx, fontSize: 12, fontFamily: 'JetBrains Mono, monospace' },
      formatter: params => {
        const p = params[0]
        return `<span style="color:${textColor};font-size:10px">${p.axisValue}</span><br/>` +
          `<span style="color:${series.color};font-weight:600">${series.label}</span>: ` +
          `<strong style="color:${tooltipTx}">${p.value?.toFixed(1)}%</strong>`
      },
    },
    grid: { top: 8, right: 12, bottom: 24, left: 40 },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLabel: {
        color: textColor,
        fontSize: 10,
        fontFamily: 'JetBrains Mono, monospace',
        interval: Math.max(0, Math.floor(timestamps.length / 5) - 1),
      },
      axisLine: { lineStyle: { color: gridColor } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0, max: 100,
      axisLabel: {
        color: textColor,
        fontSize: 10,
        fontFamily: 'JetBrains Mono, monospace',
        formatter: '{value}%',
      },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      name: series.label,
      type: 'line',
      data: data.map(d => d[series.key]),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: series.color, width: 1.5 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: series.fill.replace('22', '55') },
            { offset: 1, color: series.fill.replace('22', '00') },
          ],
        },
      },
    }],
  }
}

export default function MetricsChart({ data, loading }) {
  const isDark = document.documentElement.classList.contains('dark')

  if (loading) {
    return <div className="loading-row"><div className="spinner" /><span>Cargando historial de métricas…</span></div>
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ color: 'var(--tx-4)', fontSize: 13, padding: 24, textAlign: 'center' }}>
        Sin datos históricos aún. Los gráficos se actualizarán en los próximos segundos.
      </div>
    )
  }

  return (
    <div className="charts-section">
      {SERIES.map(s => (
        <div key={s.key} className="chart-box">
          <div className="chart-box-title">{s.label} (%)</div>
          <ReactECharts
            option={buildOption(s, data, isDark)}
            style={{ height: 130 }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      ))}
    </div>
  )
}
