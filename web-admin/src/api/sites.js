import request from './request'

export function getSites(params) {
  return request.get('/admin/sites', { params })
}

export function getSiteDetail(id) {
  return request.get(`/admin/sites/${id}`)
}

export function createSite(data) {
  return request.post('/admin/sites', data)
}

export function updateSite(id, data) {
  return request.put(`/admin/sites/${id}`, data)
}

export function deleteSite(id) {
  return request.delete(`/admin/sites/${id}`)
}

export function getSiteDevices(siteId) {
  return request.get(`/admin/sites/${siteId}/devices`)
}

export function bindSiteDevice(siteId, deviceId) {
  return request.post(`/admin/sites/${siteId}/devices`, { device_id: deviceId })
}

export function unbindSiteDevice(siteId, deviceId) {
  return request.delete(`/admin/sites/${siteId}/devices/${deviceId}`)
}
