import request from './request'

export interface StatsData {
  doc_count: number
  chunk_count: number
  bm25_ready: boolean
  hybrid_enabled: boolean
  service_status: string
}

export interface ConfigData {
  hybrid_enabled: boolean
  hybrid_vector_weight: number
  hybrid_bm25_weight: number
  hybrid_bm25_top_k: number
  rag_top_k: number
  rag_rerank_top_n: number
  rag_max_context_token: number
  chunk_size: number
  chunk_overlap: number
  embedding_model: string
  llm_model: string
  chroma_persist_dir: string
  sqlite_database_url: string
}

// 首页统计：GET /api/stats（白名单）
export function getStatsApi(): Promise<StatsData> {
  return request({ url: '/stats', method: 'get' })
}

// 系统配置：GET /api/config（白名单）
export function getConfigApi(): Promise<ConfigData> {
  return request({ url: '/config', method: 'get' })
}