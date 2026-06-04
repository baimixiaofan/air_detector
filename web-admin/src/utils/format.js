export function formatNumber(n) {
  if (n === null || n === undefined) return '--'
  return Number(n).toLocaleString()
}

export function formatPercent(n) {
  if (n === null || n === undefined) return '--'
  const sign = n > 0 ? '+' : ''
  return `${sign}${n}%`
}

export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '--'
  const d = new Date(date)
  const map = {
    'YYYY': d.getFullYear(),
    'MM': String(d.getMonth() + 1).padStart(2, '0'),
    'DD': String(d.getDate()).padStart(2, '0'),
    'HH': String(d.getHours()).padStart(2, '0'),
    'mm': String(d.getMinutes()).padStart(2, '0'),
    'ss': String(d.getSeconds()).padStart(2, '0')
  }
  let result = format
  for (const [key, val] of Object.entries(map)) {
    result = result.replace(key, val)
  }
  return result
}

export function formatDateTime(date) {
  return formatDate(date, 'YYYY-MM-DD HH:mm:ss')
}

export function aqiLevel(aqi) {
  if (aqi <= 50) return { label: '优', color: '#00b894', bgClass: 'aqi-bg-good' }
  if (aqi <= 100) return { label: '良', color: '#fdcb6e', bgClass: 'aqi-bg-moderate' }
  if (aqi <= 150) return { label: '轻度污染', color: '#e17055', bgClass: 'aqi-bg-unhealthy-sensitive' }
  if (aqi <= 200) return { label: '中度污染', color: '#d63031', bgClass: 'aqi-bg-unhealthy' }
  if (aqi <= 300) return { label: '重度污染', color: '#8f3f97', bgClass: '' }
  return { label: '严重污染', color: '#7e0023', bgClass: '' }
}

export function riskColor(score) {
  if (score <= 30) return '#00b894'
  if (score <= 50) return '#fdcb6e'
  if (score <= 70) return '#e17055'
  return '#d63031'
}

export function downloadFile(data, filename, type = 'text/csv') {
  const blob = new Blob([data], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function exportToCSV(data, columns, filename) {
  const header = columns.map(c => c.label).join(',')
  const rows = data.map(row =>
    columns.map(c => {
      const val = row[c.key]
      if (typeof val === 'string' && val.includes(',')) return `"${val}"`
      return val ?? ''
    }).join(',')
  )
  const csv = '﻿' + header + '\n' + rows.join('\n')
  downloadFile(csv, filename, 'text/csv;charset=utf-8')
}
