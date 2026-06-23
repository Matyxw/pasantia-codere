import { useEffect, useRef } from 'react'
import ReactECharts from 'echarts-for-react'

const CHART_COLORS = {
  cpu:  ['#448aff', '#7c4dff'],
  ram:  ['#00bcd4', '#00e5ff'],
  disk: ['#ff9800', '#ffc107'],
}

function buildLineOption(title, data, color, unit = '%') {
  const timestamps = data.map(d => {
    try {
      return new Date(d.timestamp).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch { return d.timestamp }
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0e1320',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e8eaf6', fontSize: 12 },
      formatter: (params) => {
        const p = params[0]
        return `${p.axisValue}<br/><span style="color:${color[0]}">${title}</span>: <strong>${p.value?.toFixed(1)}${unit}</strong>`
      },
    },
    grid: { top: 10, right: 10, bottom: 28, left: 44 },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLabel: {
        color: '#4a5568',
        fontSize: 10,
        interval: Math.floor(timestamps.length / 5),
        rotate: 0,
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.07)' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: '#4a5568', fontSize: 10, formatter: `{value}${unit}` },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: [
      {
        name: title,
        type: 'line',
        data: data.map(d => d[title.toLowerCase() === 'cpu' ? 'cpu' : title.toLowerCase() === 'ram' ? 'ram' : 'disk']),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: color[0], width: 2 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: `${color[0]}33` },
              { offset: 1, color: `${color[0]}00` },
            ],
          },
        },
      },
    ],
  }
}

export default function MetricsChart({ data, loading }) {
  if (loading) {
    return (
      <div className="loading-row">
        <div className="spinner" />
        <span>Cargando historial de métricas…</span>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '16px', textAlign: 'center' }}>
        Sin datos históricos aún. Los gráficos se actualizarán en los próximos segundos.
      </div>
    )
  }

  return (
    <div className="charts-section">
      <div className="chart-container">
        <div className="chart-title">📈 CPU (%)</div>
        <ReactECharts
          option={buildLineOption('CPU', data, CHART_COLORS.cpu)}
          style={{ height: 140 }}
          opts={{ renderer: 'canvas' }}
        />
      </div>

      <div className="chart-container">
        <div className="chart-title">💾 RAM (%)</div>
        <ReactECharts
          option={buildLineOption('RAM', data, CHART_COLORS.ram)}
          style={{ height: 140 }}
          opts={{ renderer: 'canvas' }}
        />
      </div>

      <div className="chart-container">
        <div className="chart-title">💿 Disco (%)</div>
        <ReactECharts
          option={buildLineOption('DISK', data, CHART_COLORS.disk)}
          style={{ height: 140 }}
          opts={{ renderer: 'canvas' }}
        />
      </div>
    </div>
  )
}
