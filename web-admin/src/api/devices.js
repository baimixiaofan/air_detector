import request from './request'

export function getDevices(params) {
  return request.get('/admin/devices', { params })
}

export function getDeviceDetail(id) {
  return request.get(`/admin/devices/${id}`)
}

export function createDevice(data) {
  return request.post('/admin/devices', data)
}

export function updateDevice(id, data) {
  return request.put(`/admin/devices/${id}`, data)
}

export function deleteDevice(id) {
  return request.delete(`/admin/devices/${id}`)
}

export function getDeviceStatus(id) {
  return request.get(`/admin/devices/${id}/status`)
}

export function getDeviceRealtimeData(id) {
  return request.get(`/admin/devices/${id}/realtime`)
}
