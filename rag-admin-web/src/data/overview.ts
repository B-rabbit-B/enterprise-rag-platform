import type { IDocument } from './types'

// --- KPI 指标 ---
export const kpiData = {
  docCount: 12,
  chunkCount: 1284,
  recallAt5: 86.5,
  serviceStatus: 'running' as const,
  bm25Ready: true,
  hybridEnabled: true
}

// --- 核心能力模块 ---
export interface ICapability {
  title: string
  description: string
  icon: string       // Element-Plus 图标名
  accent: string     // 主题色圆点
}

export const capabilities: ICapability[] = [
  {
    title: '文档解析',
    description: '支持 PDF / TXT / MD，递归分块 + 表格识别 + 乱码过滤',
    icon: 'Document',
    accent: '#0066cc'
  },
  {
    title: '混合检索',
    description: '向量召回（ChromaDB）+ BM25 关键词召回，可配权重',
    icon: 'Aim',
    accent: '#3a8fd6'
  },
  {
    title: 'Rerank 精排',
    description: 'BGE-Reranker-v2-m3 对 Top-K 候选重排序',
    icon: 'Rank',
    accent: '#4ab89e'
  },
  {
    title: '问答评估',
    description: '内置 Recall@K、MRR 指标，对比多策略效果',
    icon: 'DataAnalysis',
    accent: '#0d7a3a'
  }
]

// --- 技术栈 ---
export const techStack = [
  'Python', 'FastAPI', 'ChromaDB', 'SQLAlchemy',
  'BGE-M3', 'BGE-Reranker', 'LangChain', 'JWT',
  'Vue3', 'Element-Plus', 'Pinia'
]

// --- 最近文档（首页用） ---
export const recentDocs: Pick<IDocument, 'name' | 'uploadTime' | 'chunkCount'>[] = [
  { name: 'RAG系统架构白皮书.pdf', uploadTime: '2026-08-28 14:32', chunkCount: 156 },
  { name: '产品操作手册v2.md',    uploadTime: '2026-08-27 09:12', chunkCount: 89  },
  { name: '技术FAQ.txt',          uploadTime: '2026-08-25 18:45', chunkCount: 42  }
]