import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: '/api/v1/admin',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('crossvideo_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.message || '网络请求发生错误'

    if (status === 401) {
      localStorage.removeItem('crossvideo_token')
      localStorage.removeItem('crossvideo_username')
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        ElMessage.error('登录已过期或未授权，请重新登录')
        window.location.href = '/admin/login'
      }
    } else if (status === 429) {
      ElMessage.warning(`操作太频繁：${message}`)
    } else if (status !== 404) {
      ElMessage.error(typeof message === 'string' ? message : JSON.stringify(message))
    }

    return Promise.reject(error)
  }
)

export default apiClient
