import request from './request'

export function getIntelligenceReports(params) {
  return request.get('/admin/reports', { params })
}

export function getReportDetail(id) {
  return request.get(`/admin/reports/${id}`)
}

export function generateReport(data) {
  return request.post('/admin/reports/generate', data)
}

export function deleteReport(id) {
  return request.delete(`/admin/reports/${id}`)
}
