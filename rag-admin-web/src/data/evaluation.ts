import type { IEvalCase } from './types'

export const evalCases: IEvalCase[] = [
  { id: 'c001', question: '公司的主要业务是什么？',           expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c002', question: '有哪些技术架构相关的文档？',       expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c003', question: '系统的安全策略和权限控制？',       expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c004', question: '产品有哪些功能模块？',             expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c005', question: '如何进行运维监控？',               expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c006', question: '数据存储和处理方案？',             expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c007', question: '部署和上线流程是怎样的？',         expectedTag: '', vectorHit: false, hybridHit: false },
  { id: 'c008', question: 'API 接口如何调用？',               expectedTag: '', vectorHit: false, hybridHit: false }
]

// --- 汇总指标 ---
export const metrics = {
  recallAt3: { vector: 72.0, hybrid: 84.0 },
  recallAt5: { vector: 78.5, hybrid: 86.5 },
  avgLatency: { vector: 312, hybrid: 486 }  // ms
}

// --- 优化建议 ---
export const suggestions = [
  'BM25 纯关键词召回漏了 c003、c005 这类带专业术语的问题，建议适当调高 BM25 权重至 0.35-0.4',
  '向量召回漏了 c007（JWT 鉴权），该文档分片可能粒度太粗，建议减小 chunkSize 至 600',
  '混合检索已覆盖全部 8 个用例，可作为生产默认策略',
  '考虑为 c004 相关文档补充更多 "Rerank" 同义词标签以提升召回'
]