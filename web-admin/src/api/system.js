import request from './request'

export function getCompanyInfo() {
  return request.get('/admin/company-info')
}

export function updateCompanyInfo(data) {
  return request.put('/admin/company-info', data)
}

export function getAdminUsers(params) {
  return request.get('/admin/users', { params })
}

export function createAdminUser(data) {
  return request.post('/admin/users', data)
}

export function updateAdminUser(id, data) {
  return request.put(`/admin/users/${id}`, data)
}

export function deleteAdminUser(id) {
  return request.delete(`/admin/users/${id}`)
}

export function getOperationLogs(params) {
  return request.get('/admin/operation-logs', { params })
}
