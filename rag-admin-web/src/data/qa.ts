import type { IQAResult, RetrievalStrategy } from './types'

// --- 模拟问答知识库 ---
interface IQAEntry {
  keywords: string[]
  answer: string
  strategy: RetrievalStrategy
}

const qaBank: IQAEntry[] = [
  {
    keywords: ['RAG', '原理', '流程', '核心'],
    answer: `RAG 是 **检索增强生成**（Retrieval-Augmented Generation）的缩写，核心流程分为 6 步：

1. **文档解析** — PDF/TXT/MD 解析成纯文本
2. **递归分块** — 按 Token 长度切片，带 overlap 保持上下文连贯
3. **向量化入库** — BGE-M3 Embedding → ChromaDB
4. **混合检索** — 向量召回 + BM25 关键词召回，加权融合
5. **Rerank 精排** — BGE-Reranker-v2-m3 重排 Top-K
6. **生成** — 截断拼接上下文 → LLM 生成 → 返回回答 + 溯源

相比纯 LLM，RAG 的优势：① 知识时效性可控；② 回答可溯源；③ 幻觉风险显著降低。`
  },
  {
    keywords: ['混合', '检索', 'BM25', '向量', '权重'],
    answer: `混合检索通过加权融合向量得分和 BM25 得分实现互补：

- **向量召回** 擅长语义相似度匹配（"怎么处理数据" ≈ "数据处理的方法"）
- **BM25 关键词召回** 擅长精确术语匹配（"ChromaDB" 必须命中包含该词的分块）
- 默认权重：向量 0.7 + BM25 0.3，可在系统设置里调整
- 最终融合公式：\`score = w_vector * norm(vec) + w_bm25 * norm(bm25)\`

两种召回通道独立执行，归一化后加权求和，再取 Top-K 送入 Rerank。`
  },
  {
    keywords: ['ChromaDB', '向量库', '持久化', 'embedding'],
    answer: `ChromaDB 是一个轻量级嵌入式向量数据库，本项目用它存储：

- 集合名：\`rag_chunks\`
- 嵌入模型：**BGE-M3**（中国模型，对中文优化好）
- 持久化目录：后端 \`.env\` 里配置 \`CHROMA_PERSIST_DIR\`
- 返回元数据：\`filename / tag / chunk_index / upload_time\`

每次查询时用 \`collection.query(query_embeddings=[...], n_results=K)\` 返回最近邻。`
  },
  {
    keywords: ['架构', '技术栈', '用什么', '技术'],
    answer: `技术栈全景：

| 层 | 技术 |
|---|---|
| 前端 | Vue3 + Vite + Element-Plus + Pinia |
| 后端 | Python 3.11 + FastAPI + Uvicorn |
| ORM | SQLAlchemy + SQLite |
| 向量库 | ChromaDB |
| Embedding | BGE-M3 (bge-m3) |
| Rerank | BGE-Reranker-v2-m3 |
| LLM | 可配置（默认 Ollama / OpenAI 兼容） |
| 鉴权 | JWT (PyJWT) + bcrypt |
| 部署 | 单进程，支持 Docker 化 |`
  }
]

// --- 默认回答（关键词未命中时） ---
const defaultAnswer = `我在知识库里没有找到与你问题精确匹配的内容。可能的原因：

1. 相关文档尚未上传或解析完成
2. 问题表述过于模糊，尝试加入更多关键词
3. 可以尝试切换检索策略（纯向量 / 混合 / BM25）重新提问

如果你确定有相关文档但还是找不到，建议在系统设置里调整分块粒度或 BM25 权重。`

export function mockQA(question: string, strategy: RetrievalStrategy): IQAResult {
  const q = question.toLowerCase()
  const matched = qaBank.find(entry =>
    entry.keywords.some(k => q.includes(k.toLowerCase()))
  ) || qaBank[0]  // 没命中就用第一条（通用回答）

  const now = Date.now()
  const evidenceDocs = ['RAG系统架构白皮书.pdf', 'API接口规范.pdf', '技术FAQ.txt']
  const tagsList = [['架构', '核心'], ['API', '接口'], ['FAQ', '常见问题']]

  return {
    answer: matched.keywords.length ? matched.answer : defaultAnswer,
    strategy,
    references: [
      { documentName: 'RAG系统架构白皮书.pdf', pageNumber: 3,  paragraph: 'RAG（Retrieval-Augmented Generation）是一种将外部检索与大语言模型生成相结合的技术框架……' },
      { documentName: '技术FAQ.txt',          pageNumber: 1,  paragraph: '向量召回阶段采用 ChromaDB 作为向量存储后端……' },
      { documentName: 'API接口规范.pdf',       pageNumber: 12, paragraph: 'Rerank 阶段使用 BGE-Reranker-v2-m3 对 Top-K 候选进行精排序……' }
    ],
    evidence: evidenceDocs.map((name, i) => ({
      documentName: name,
      similarityScore: +(0.65 - i * 0.08 + Math.random() * 0.1).toFixed(2),
      rerankScore:     +(0.82 - i * 0.15 + Math.random() * 0.08).toFixed(2),
      pageNumber: [3, 1, 12][i],
      tags: tagsList[i]
    }))
  }
}