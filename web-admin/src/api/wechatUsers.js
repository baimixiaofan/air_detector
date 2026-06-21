import request from './request'

export function getWechatUsers(params) {
  return request.get('/admin/users/wechat', { params })
}

export function getWechatUser(id) {
  return request.get(`/admin/users/wechat/${id}`)
}

export function updateWechatUser(id, data) {
  return request.put(`/admin/users/wechat/${id}`, data)
}

export function deleteWechatUser(id) {
  return request.delete(`/admin/users/wechat/${id}`)
}
