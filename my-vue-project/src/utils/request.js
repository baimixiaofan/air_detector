import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router' // 引入路由，方便 token 过期时跳转

// 1. 创建 Axios 实例
const service = axios.create({
  // 💡 注意这里：你队友在 flask_api_server.py 里给后台接口加了 /api/admin 前缀
  // 配合咱们 Vite 里的 /api 代理，基础路径就是下面这个：
  baseURL: '/api/admin',
  timeout: 10000,
})

// 2. 💡 请求拦截器：发请求前，自动戴上 "Bearer 徽章"
service.interceptors.request.use(
  (config) => {
    // 从浏览器的本地存储里拿出登录时存的 token
    const token = localStorage.getItem('token')
    if (token) {
      // 严格按照队友的要求，拼装 'Bearer ' 字符串
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 3. 💡 响应拦截器：拿到数据后，统一安检
service.interceptors.response.use(
  (response) => {
    // 队友返回的 JSON 结构是 { code: 200, data: {...}, msg: '...' }
    const res = response.data

    // 如果 code 不是 200，说明业务报错了（比如密码错误）
    if (res.code !== 200) {
      // 全局弹窗提示后端的报错信息
      ElMessage.error(res.msg || '系统内部错误')

      // 如果 code 是 401，说明 Token 没传、假造或者过期了
      if (res.code === 401) {
        localStorage.removeItem('token') // 清理假/废 token
        localStorage.removeItem('user')
        router.push('/login') // 强制踢回登录页
      }
      return Promise.reject(new Error(res.msg || 'Error'))
    }

    // 如果是 200 成功，前端页面不需要拿到外层的 code 和 msg，直接把最核心的 data 扒出来给页面用
    return res.data
  },
  (error) => {
    // 捕获 HTTP 网络级别的报错（比如后端服务器根本没开，报 502/404 等）
    const errorMsg = error.response?.data?.msg || '网络请求失败，请检查后端服务是否启动'
    ElMessage.error(errorMsg)
    return Promise.reject(error)
  },
)

export default service
