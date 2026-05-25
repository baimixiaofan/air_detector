import request from './request'

export function getDashboardStats() {
  return request.get('/admin/dashboard/stats')
}

export function getDashboardRealtime() {
  return request.get('/admin/dashboard/realtime')
}

export function getAlertSummary() {
  return request.get('/admin/dashboard/alert-summary')
}

export function getDashboardTrend() {
  return request.get('/admin/dashboard/trend')
}

export function getDiagnostics() {
  return request.get('/admin/dashboard/diagnostics')
}

export function getDiagnosticsDetail(siteId) {
  return request.get(`/admin/dashboard/diagnostics/${siteId}`)
}
