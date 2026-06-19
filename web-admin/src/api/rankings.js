import request from './request'

export function getRankings(params) {
  return request.get('/admin/rankings', { params })
}

export function getRankingTrend(params) {
  return request.get('/admin/rankings/trend', { params })
}

export function getRankingAreas(params) {
  return request.get('/admin/rankings/areas', { params })
}
