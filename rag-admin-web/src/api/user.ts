import request from './request'

export interface LoginForm {
  username: string
  password: string
}

export interface LoginData {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  is_admin: boolean
}

// 登录：POST /api/user/login
export function loginApi(data: LoginForm): Promise<LoginData> {
  return request({ url: '/user/login', method: 'post', data })
}

// 注册：POST /api/user/register
export function registerApi(data: { username: string; password: string; is_admin?: boolean }) {
  return request({ url: '/user/register', method: 'post', data })
}

// 获取当前用户：GET /api/user/me
export function getMeApi(): Promise<UserInfo> {
  return request({ url: '/user/me', method: 'get' })
}