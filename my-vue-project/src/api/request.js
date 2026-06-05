import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器：自动带 token
request.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_user')
        window.location.href = '/admin/#/login'
        return Promise.reject(error)
      }
      ElMessage.error(data?.msg || '请求失败')
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request
