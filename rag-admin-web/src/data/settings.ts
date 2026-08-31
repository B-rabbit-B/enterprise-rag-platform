import type { IRagSettings } from './types'

const STORAGE_KEY = '__rag_platform_settings'

// 与后端 config/settings.py + .env 实际配置对齐
// LLM: qwen3.7-plus（阿里云 DashScope），Embedding: all-MiniLM-L6-v2，Rerank: BAAI/bge-reranker-base
export const defaultSettings: IRagSettings = {
  defaultStrategy: 'hybrid',
  vectorWeight: 0.6,
  bm25Weight: 0.4,
  topK: 5,
  embeddingModel: 'all-MiniLM-L6-v2',
  rerankModel: 'BAAI/bge-reranker-base',
  llmModel: 'qwen3.7-plus',
  chunkMethod: 'recursive',
  chunkSize: 500,
  chunkOverlap: 50,
  filterGarbled: true,
  parseTables: true
}

export function loadSettings(): IRagSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      return { ...defaultSettings, ...JSON.parse(raw) }
    }
  } catch (_e) { /* ignore */ }
  return { ...defaultSettings }
}

export function saveSettings(s: IRagSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
}