import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const service = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// 请求拦截：自动带 Bearer Token
service.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  const url = config.url || ''
  // 登录/注册接口不带 token（url 可能合并了 baseURL，用 includes 更稳）
  const skipAuth = url.includes('/user/login') || url.includes('/user/register')
  if (token && !skipAuth) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：处理统一响应 { code, msg, data }
service.interceptors.response.use(
  (res) => {
    const body = res.data  // axios 已解包一层
    // 后端统一格式：{ code, msg, data }
    // 后端约定 code === 0 表示成功（utils/response.py 的 ApiResponse.success 默认 code=0）
    if (body && typeof body.code === 'number') {
      if (body.code === 0) {
        return body.data   // 直接把业务数据返回
      }
      // 业务错误（code != 0 即为业务异常，如 code=400 密码错误）
      ElMessage.error(body.msg || '请求失败')
      return Promise.reject(new Error(body.msg))
    }
    return body
  },
  (err) => {
    const status = err.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
      ElMessageBox.confirm('登录已失效，请重新登录', '提示', {
        confirmButtonText: '去登录',
        cancelButtonText: '关闭',
        type: 'warning'
      }).then(() => {
        // 跳转到登录弹窗（通过 EventBus 或直接弹窗，这里简化处理）
        window.dispatchEvent(new CustomEvent('need-login'))
      }).catch(() => {})
    } else if (status === 403) {
      ElMessage.error('没有权限，需要管理员账号')
    } else if (status === 500) {
      ElMessage.error('服务器内部错误')
    } else {
      ElMessage.error(err.message || '网络异常')
    }
    return Promise.reject(err)
  }
)

export default service