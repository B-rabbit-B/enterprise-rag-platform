import request from './request'

export interface ChatSession {
  session_id: number
  session_name: string
  create_time: string
  update_time: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  extra_json?: any
  create_time: string
}

// 新建会话
export function createSessionApi(session_name: string): Promise<ChatSession> {
  return request({ url: '/chat/session', method: 'post', data: { session_name } })
}

// 会话列表
export function listSessionsApi(): Promise<ChatSession[]> {
  return request({ url: '/chat/session', method: 'get' })
}

// 删除会话
export function deleteSessionApi(session_id: number) {
  return request({ url: `/chat/session/${session_id}`, method: 'delete' })
}

// 获取会话消息
export function listMessagesApi(session_id: number): Promise<ChatMessage[]> {
  return request({ url: `/chat/session/${session_id}/messages`, method: 'get' })
}

// RAG 问答
export function ragChatApi(session_id: number, params: {
  question: string
  tag?: string
  retrieve_mode?: 'hybrid' | 'vector' | 'bm25'
  use_rerank?: boolean
}) {
  return request({
    url: `/chat/session/${session_id}/rag`,
    method: 'post',
    data: params
  })
}