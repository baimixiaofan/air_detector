import request from './request'

export function login(username, password) {
  return request.post('/admin/login', { username, password })
}

export function getProfile() {
  return request.get('/admin/profile')
}

export function logout() {
  return request.post('/admin/logout')
}
