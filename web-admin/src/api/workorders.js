import request from './request'

export function getWorkOrders(params) {
  return request.get('/admin/workorders', { params })
}

export function createWorkOrder(data) {
  return request.post('/admin/workorders', data)
}

export function updateWorkOrder(id, data) {
  return request.put(`/admin/workorders/${id}`, data)
}

export function deleteWorkOrder(id) {
  return request.delete(`/admin/workorders/${id}`)
}
