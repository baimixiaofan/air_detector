import request from './request'

export function getReports(params) {
  return request.get('/admin/reports', { params })
}

// 兼容旧名称
export const getIntelligenceReports = getReports

export function getReportDetail(id) {
  return request.get(`/admin/reports/${id}`)
}

export function generateReport(data) {
  return request.post('/admin/reports/generate', data)
}

export function generateEnterpriseReport(data) {
  return request.post('/admin/reports/enterprise', data)
}

export function previewReport(id) {
  return request.get(`/admin/reports/${id}/preview`)
}

export function deleteReport(id) {
  return request.delete(`/admin/reports/${id}`)
}
