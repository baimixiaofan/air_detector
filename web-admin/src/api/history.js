import request from './request'

export function queryHistory(params) {
  return request.get('/admin/history/query', { params })
}

export function getComparisonData(params) {
  return request.get('/admin/history/comparison', { params })
}

export function getReportData(params) {
  return request.get('/admin/history/report', { params })
}

export function exportReport(params) {
  return request.get('/admin/history/report/export', { params, responseType: 'blob' })
}
