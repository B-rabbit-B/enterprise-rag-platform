import type { IDocument, IChunk, DocType, DocStatus } from './types'

// --- 文档列表 ---
const _rawDocs: Omit<IDocument, 'id'>[] = [
  { name: 'RAG系统架构白皮书.pdf', type: 'pdf', uploadTime: '2026-08-28 14:32', status: 'success', chunkCount: 156, tags: ['架构', '核心'],     category: '产品文档' },
  { name: '产品操作手册v2.md',     type: 'md',  uploadTime: '2026-08-27 09:12', status: 'success', chunkCount: 89,  tags: ['操作', '指南'],     category: '产品文档' },
  { name: '技术FAQ.txt',           type: 'txt', uploadTime: '2026-08-25 18:45', status: 'success', chunkCount: 42,  tags: ['FAQ', '常见问题'],  category: '技术文档' },
  { name: 'API接口规范.pdf',       type: 'pdf', uploadTime: '2026-08-24 11:20', status: 'success', chunkCount: 73,  tags: ['API', '接口'],      category: '技术文档' },
  { name: '安全合规说明.md',       type: 'md',  uploadTime: '2026-08-23 16:05', status: 'parsing', chunkCount: 0,   tags: ['安全', '合规'],     category: '合规文档' },
  { name: '月度运营报告.pdf',      type: 'pdf', uploadTime: '2026-08-22 10:30', status: 'success', chunkCount: 214, tags: ['运营', '报告'],     category: '运营文档' },
  { name: '员工入职手册.docx.md',  type: 'md',  uploadTime: '2026-08-20 08:00', status: 'success', chunkCount: 101, tags: ['HR', '入职'],       category: '内部管理' },
  { name: '故障排查手册.txt',      type: 'txt', uploadTime: '2026-08-19 21:15', status: 'success', chunkCount: 67,  tags: ['运维', '故障'],     category: '技术文档' },
  { name: '版本更新日志.md',       type: 'md',  uploadTime: '2026-08-18 14:40', status: 'success', chunkCount: 28,  tags: ['版本', 'Changelog'],category: '技术文档' },
  { name: '数据备份策略.pdf',      type: 'pdf', uploadTime: '2026-08-16 13:00', status: 'failed',  chunkCount: 0,   tags: ['运维', '备份'],     category: '技术文档' },
  { name: '市场营销策略.pdf',      type: 'pdf', uploadTime: '2026-08-15 09:00', status: 'success', chunkCount: 178, tags: ['市场', '运营'],     category: '运营文档' },
  { name: '财务审批流程.md',       type: 'md',  uploadTime: '2026-08-12 15:30', status: 'success', chunkCount: 54,  tags: ['财务', '流程'],     category: '内部管理' }
]

export const documents: IDocument[] = _rawDocs.map((d, i) => ({
  ...d,
  id: `doc-${String(i + 1).padStart(3, '0')}`
}))

// --- 分类 ---
export const categories = ['全部', '产品文档', '技术文档', '合规文档', '运营文档', '内部管理']

// --- 标签云 ---
export const allTags = ['架构', '核心', '操作', '指南', 'FAQ', '常见问题', 'API', '接口', '安全', '合规', '运营', '报告', 'HR', '入职', '运维', '故障', '版本', 'Changelog', '备份', '市场', '财务', '流程']

// --- 文档分片（按文档 ID 关联，每个文档返回 5-8 条模拟分片） ---
export function getChunksByDocId(docId: string): IChunk[] {
  const doc = documents.find(d => d.id === docId)
  if (!doc) return []
  const count = Math.min(doc.chunkCount || 0, 8)
  const samples = [
    'RAG（Retrieval-Augmented Generation）是一种将外部检索与大语言模型生成相结合的技术框架……',
    '向量召回阶段采用 ChromaDB 作为向量存储后端，配合 BGE-M3 嵌入模型将文档分块映射到稠密向量空间……',
    'BM25 作为纯关键词召回的补充通道，在混合检索中通过权重参数与向量得分加权融合……',
    'Rerank 阶段使用 BGE-Reranker-v2-m3 对 Top-K 候选进行精排序，牺牲少量延迟换召回精度……',
    'Token 截断采用滑动窗口策略，对上下文拼接结果按模型最大上下文长度进行裁剪……',
    '溯源返回要求每个回答片段携带文档来源、页码和分块索引，方便用户验证真实性……',
    '权限模型基于 JWT + RBAC，管理员可执行文档删除和系统配置修改操作……',
    '服务端采用 FastAPI + Uvicorn 异步架构，SQLAlchemy + SQLite 存储元数据……'
  ]
  const chunks: IChunk[] = []
  for (let i = 0; i < count; i++) {
    const content = samples[i % samples.length]
    chunks.push({
      id: `${docId}-chunk-${i}`,
      documentId: docId,
      index: i + 1,
      content,
      charCount: content.length,
      pageNumber: doc.type === 'pdf' ? Math.floor(i / 4) + 1 : undefined
    })
  }
  return chunks
}

// --- 文档上传（前端模拟） ---
export function simulateUpload(file: File): IDocument {
  const ext = (file.name.split('.').pop() || 'txt').toLowerCase() as DocType
  const now = new Date()
  const uploadTime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  return {
    id: `doc-new-${Date.now()}`,
    name: file.name,
    type: ['pdf', 'txt', 'md'].includes(ext) ? ext : 'txt',
    uploadTime,
    status: 'parsing' as DocStatus,
    chunkCount: 0,
    tags: [],
    category: '未分类'
  }
}