import axios from 'axios'
import { ElMessage } from 'element-plus'

// 统一 axios 实例 / Shared axios instance
const http = axios.create({
  baseURL: '/',
  timeout: 120000,
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const detail = err.response?.data?.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : detail?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  },
)

export default http