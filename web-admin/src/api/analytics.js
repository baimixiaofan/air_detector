import request from './request'

export function getPoorAirUsers(params) {
  return request({
    url: '/admin/analytics/poor-air-users',
    method: 'get',
    params
  })
}

export function exportPoorAirUsers(params) {
  return request({
    url: '/admin/analytics/poor-air-users/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
