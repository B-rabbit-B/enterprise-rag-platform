// PRD 里的接口定义统一放在这里

export type DocType = 'pdf' | 'txt' | 'md'
export type DocStatus = 'success' | 'parsing' | 'failed'
export type RetrievalStrategy = 'vector' | 'hybrid' | 'bm25'

export interface IDocument {
  id: string
  name: string
  type: DocType
  uploadTime: string
  status: DocStatus
  chunkCount: number
  tags: string[]
  category: string
}

export interface IChunk {
  id: string
  documentId: string
  index: number
  content: string
  charCount: number
  pageNumber?: number
}

export interface IQAResult {
  answer: string
  strategy: RetrievalStrategy
  references: {
    documentName: string
    pageNumber: number
    paragraph: string
  }[]
  evidence: {
    documentName: string
    similarityScore: number
    rerankScore: number
    pageNumber: number
    tags: string[]
  }[]
}

export interface IEvalCase {
  id: string
  question: string
  expectedTag: string
  vectorHit: boolean
  hybridHit: boolean
}

export interface IRagSettings {
  defaultStrategy: RetrievalStrategy
  vectorWeight: number
  bm25Weight: number
  topK: number
  embeddingModel: string
  rerankModel: string
  llmModel: string
  chunkMethod: string
  chunkSize: number
  chunkOverlap: number
  filterGarbled: boolean
  parseTables: boolean
}

export interface IApiDoc {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string
  description: string
  params?: string[]
}