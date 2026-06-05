import request from './request'

export function getRealtimeData() {
  return request.get('/admin/dashboard/realtime')
}

export function getRealtimeByDevice(deviceId) {
  return request.get(`/admin/dashboard/realtime/${deviceId}`)
}

export function getMapData() {
  return request.get('/admin/dashboard/map')
}
