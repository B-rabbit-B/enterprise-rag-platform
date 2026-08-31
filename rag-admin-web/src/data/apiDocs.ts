import type { IApiDoc } from './types'

export interface IApiGroup {
  name: string
  description: string
  endpoints: IApiDoc[]
}

export const apiGroups: IApiGroup[] = [
  {
    name: '用户模块',
    description: '登录、注册、用户信息查询（JWT 鉴权）',
    endpoints: [
      { method: 'POST', path: '/api/user/login',    description: '用户登录，返回 access_token', params: ['username: str', 'password: str'] },
      { method: 'POST', path: '/api/user/register', description: '注册新用户（管理员可注册 admin）', params: ['username', 'password', 'is_admin?'] },
      { method: 'GET',  path: '/api/user/me',       description: '获取当前登录用户信息（需鉴权）' }
    ]
  },
  {
    name: '文档管理',
    description: '文档上传、列表查询、删除、分片解析',
    endpoints: [
      { method: 'POST',   path: '/api/doc/upload',   description: '上传文档（multipart/form-data）', params: ['file: File', 'tag?: str'] },
      { method: 'GET',    path: '/api/doc/list',     description: '获取已上传文档列表（含分片数/状态）' },
      { method: 'DELETE', path: '/api/doc/{id}',     description: '删除指定文档及其向量分片' },
      { method: 'GET',    path: '/api/doc/search',   description: '关键词搜索文档分片（BM25）' }
    ]
  },
  {
    name: '会话与问答',
    description: 'RAG 会话管理 + 混合检索问答',
    endpoints: [
      { method: 'POST', path: '/api/chat/session',                     description: '新建对话会话', params: ['session_name: str'] },
      { method: 'GET',  path: '/api/chat/session',                     description: '获取当前用户的会话列表' },
      { method: 'DELETE', path: '/api/chat/session/{id}',              description: '删除会话' },
      { method: 'GET',  path: '/api/chat/session/{id}/messages',       description: '获取会话历史消息' },
      { method: 'POST', path: '/api/chat/session/{id}/message',        description: '普通对话（不传 RAG）', params: ['question: str'] },
      { method: 'POST', path: '/api/chat/session/{id}/rag',            description: 'RAG 问答（核心接口）', params: ['question', 'tag?', 'retrieve_mode?', 'use_rerank?'] }
    ]
  },
  {
    name: '配置与统计',
    description: '白名单接口，无需登录即可访问',
    endpoints: [
      { method: 'GET', path: '/api/stats', description: '平台概览统计（文档数/分片数/BM25状态等）' },
      { method: 'GET', path: '/api/config', description: '当前后端运行配置（模型/分块/权重参数）' }
    ]
  }
]