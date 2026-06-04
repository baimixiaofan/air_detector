export const AQI_LEVELS = [
  { min: 0, max: 50, label: '优', color: '#00b894', bg: 'rgba(0,184,148,0.1)' },
  { min: 51, max: 100, label: '良', color: '#fdcb6e', bg: 'rgba(253,203,110,0.15)' },
  { min: 101, max: 150, label: '轻度污染', color: '#e17055', bg: 'rgba(225,112,85,0.1)' },
  { min: 151, max: 200, label: '中度污染', color: '#d63031', bg: 'rgba(214,48,49,0.1)' },
  { min: 201, max: 300, label: '重度污染', color: '#8f3f97', bg: 'rgba(143,63,151,0.1)' },
  { min: 301, max: 500, label: '严重污染', color: '#7e0023', bg: 'rgba(126,0,35,0.1)' }
]

export const POLLUTANTS = [
  { key: 'pm25', label: 'PM2.5', unit: 'μg/m³' },
  { key: 'pm10', label: 'PM10', unit: 'μg/m³' },
  { key: 'no2', label: 'NO₂', unit: 'μg/m³' },
  { key: 'so2', label: 'SO₂', unit: 'μg/m³' },
  { key: 'o3', label: 'O₃', unit: 'μg/m³' },
  { key: 'co', label: 'CO', unit: 'mg/m³' }
]

export const SITE_TYPES = [
  { value: 'national', label: '国控站' },
  { value: 'provincial', label: '省控站' },
  { value: 'municipal', label: '市控站' },
  { value: 'enterprise', label: '企业站' }
]

export const ROLES = {
  admin: { label: '管理员', color: '#e17055', tagType: 'warning' },
  ops: { label: '运维', color: '#74b9ff', tagType: '' },
  viewer: { label: '查看者', color: '#b2bec3', tagType: 'info' }
}

export const ALERT_SEVERITY = {
  critical: { label: '严重', color: '#d63031', tagType: 'danger' },
  warning: { label: '警告', color: '#e17055', tagType: 'warning' },
  info: { label: '提示', color: '#74b9ff', tagType: '' }
}

export const ALERT_STATUS = {
  pending: { label: '待处理', color: '#e17055', tagType: 'warning' },
  acknowledged: { label: '已确认', color: '#74b9ff', tagType: '' },
  resolved: { label: '已解决', color: '#00b894', tagType: 'success' }
}

export const DEVICE_STATUS = {
  online: { label: '在线', color: '#00b894' },
  offline: { label: '离线', color: '#b2bec3' }
}
