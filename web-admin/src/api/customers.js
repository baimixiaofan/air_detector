import request from './request'

export function getCustomers(params) {
  return request.get('/admin/customers', { params })
}

export function createCustomer(data) {
  return request.post('/admin/customers', data)
}

export function updateCustomer(id, data) {
  return request.put(`/admin/customers/${id}`, data)
}

export function deleteCustomer(id) {
  return request.delete(`/admin/customers/${id}`)
}
