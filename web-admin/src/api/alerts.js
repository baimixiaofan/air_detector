import request from './request'

export function getAlertRecords(params) {
  return request.get('/admin/alerts/records', { params })
}

export function getAlertRules() {
  return request.get('/admin/alerts/rules')
}

export function createAlertRule(data) {
  return request.post('/admin/alerts/rules', data)
}

export function updateAlertRule(id, data) {
  return request.put(`/admin/alerts/rules/${id}`, data)
}

export function deleteAlertRule(id) {
  return request.delete(`/admin/alerts/rules/${id}`)
}

export function acknowledgeAlert(id) {
  return request.post(`/admin/alerts/records/${id}/acknowledge`)
}

export function resolveAlert(id) {
  return request.post(`/admin/alerts/records/${id}/resolve`)
}
