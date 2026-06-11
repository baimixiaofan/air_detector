import request from './request'

/**
 * 获取空气质量差的用户列表
 */
export function getPoorAirUsers(params) {
  return request({
    url: '/api/admin/analytics/poor-air-users',
    method: 'get',
    params
  })
}

/**
 * 导出空气质量差用户 CSV
 */
export function exportPoorAirUsers(params) {
  return request({
    url: '/api/admin/analytics/poor-air-users/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
