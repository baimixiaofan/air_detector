import request from './request'

export function getCaptcha() {
  return request.get('/admin/captcha')
}

export function login(username, password, captchaId, captchaAnswer) {
  return request.post('/admin/login', { username, password, captcha_id: captchaId, captcha_answer: captchaAnswer })
}

export function getProfile() {
  return request.get('/admin/profile')
}

export function logout() {
  return request.post('/admin/logout')
}
