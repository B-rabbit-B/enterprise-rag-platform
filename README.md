# 企业知识库 RAG 问答平台

> ⭐ **Star 一下** 支持持续迭代 | 面向学习 / 演示的完整 RAG 全链路项目

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4+-42b883.svg)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178c6.svg)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

### 🎉 v1.1 重大更新（2026-09）

- ✨ **新增可视化前端管理台** — Vite + Vue3 + Element-Plus 构建，文档管理 / 知识库问答 / 检索评估 / 系统设置
- 🔍 **混合检索** — BM25 关键词 + Chroma 向量加权融合，纯 Python 零依赖 BM25 实现
- 📝 **递归字符分块** — 段落 → 句子多层切分 + 块重叠窗口，PDF 表格规范化 + OCR 乱码清洗
- 🧪 **检索评估 API** — 量化对比纯向量 vs 混合检索的 Recall@K / 耗时，支持多 tag 匹配
- 🔐 **多标签文档** — 一个文档支持多个 tag，评估用例弹窗编辑 + 下拉选择

---

## 💡 项目简介

**企业私有知识库 RAG 平台** — FastAPI + Vue3 前后端分离实现，支持文档解析入库、向量 + BM25 混合检索、BGE-Reranker 重排、JWT 鉴权、多会话管理、检索效果量化评估。

> 完整 RAG 业务闭环 + 可视化操作界面：
> 注册登录 → 文档上传解析 → 分片预览 → 混合检索问答 → 引用溯源 → 检索评估 → 日志管理。

---

## ✨ 核心亮点

| # | 亮点 | 说明 |
|---|------|------|
| 1 | **完整 RAG 闭环** | 混合召回 → Rerank 精排 → Token 截断 → Prompt 组装 → LLM 生成 → 溯源引用 |
| 2 | **可视化管理台** | 三栏文档管理、会话历史自动滚动、评估弹窗编辑用例、多标签下拉选择 |
| 3 | **检索效果量化** | 内置评估 API + 评估脚本，对比不同检索策略 Recall@K，迭代有依据 |
| 4 | **空检索短路** | 0 条召回直接返回「未找到」，跳过 LLM 调用 → 省 Token、降时延、减幻觉 |
| 5 | **生产级工程化** | JWT 鉴权、权限分级、全局异常兜底、按天滚动结构化日志、双库删除一致性 |

---

## 🎯 使用场景

- 🏢 **企业内部知识库** — 产品文档、技术手册、规章制度等私有知识问答
- 📚 **技术文档助手** — 上传 PDF/TXT/MD，对文档内容进行精准问答 + 原文溯源
- 🧪 **RAG 技术学习** — 从零看懂完整 RAG 流水线代码，可直接用于简历项目
- 🔍 **检索策略对比** — 纯向量 vs BM25 vs 混合检索，量化评估选最优方案

---

---

## 🚀 Quick Start（5 分钟跑起来）

| 分类 | 技术 | 说明 |
| --- | --- | --- |
| Web 框架 | FastAPI | 高性能异步框架，自动生成 OpenAPI / Swagger 文档 |
| 数据库 | SQLAlchemy + SQLite | 轻量关系型存储用户 / 会话 / 消息 / 文档元数据 |
| 向量库 | ChromaDB | 本地向量存储与语义检索 |
| 文档处理 | LangChain / PyPDF | PDF / TXT / MD 解析与分块 |
| 向量模型 | sentence-transformers（all-MiniLM-L6-v2） | 通用 Embedding，支持多语言 |
| 重排序 | BGE-Reranker（bge-reranker-base） | Cross-encoder 语义精排 |
| 大模型 | 阿里 DashScope（qwen 系列） | 支持兼容 OpenAI 协议的任意 LLM |
| 鉴权 | python-jose + passlib(bcrypt) | JWT Token 鉴权 + 密码加盐哈希 |
| 配置 | pydantic-settings + python-dotenv | `.env` 配置管理 |
| 日志 | 自研 logger（按天滚动） | 结构化字段：user_id / query / hit_count / cost_sec |
| **前端框架** | Vite + Vue3 + TypeScript | SPA 单页应用，开发热更新 |
| **UI 组件** | Element-Plus | 企业级 UI 组件库 |
| **状态管理** | Pinia | 用户 / 全局状态 |
| **HTTP** | Axios | 统一请求拦截、JWT 自动注入 |
| **路由** | Vue Router | 哈希路由 |

---

## ✨ 项目特性

- ✅ **完整 RAG 闭环**：用户问题 → 混合检索（向量 + BM25）(top_k) → Rerank 重排(top_n) → Token 截断 → Prompt 组装 → LLM 调用 → 返回答案 + 文档溯源
- ✅ **JWT 鉴权 + 权限分级**：普通用户仅访问自身会话；管理员才可上传 / 删除文档；权限校验读取数据库真实字段，不信任 JWT 载荷
- ✅ **Rerank 重排优化**：Cross-encoder 语义精排，降低误召回，显著提升回答质量
- ✅ **Token 截断防溢出**：基于 `tiktoken` 统计 token，动态截断上下文，防止超出模型上下文窗口
- ✅ **空检索短路优化（简历亮点）**：检索 0 条直接返回「未找到相关信息」，跳过 LLM 网络调用，降低时延、节约 Token、规避幻觉
- ✅ **全局统一响应格式**：`{code, msg, data}`，便于前端统一解析
- ✅ **全局异常兜底**：异常中间件捕获参数、鉴权、LLM 网络异常，返回结构化 JSON，服务不堆栈崩溃
- ✅ **结构化日志**：记录 `user_id`、`query`、`hit_count`、`cost_sec`，便于问题排查
- ✅ **双库删除一致性**：删除文档时同步清理 SQLite 元数据与 Chroma 向量分片
- ✅ **HuggingFace 国内镜像适配**：解决国内网络下载模型报错
- ✅ **lifespan 生命周期管理**：Reranker 仅加载一次，避免 `reload` 重复加载
- ✅ **递归字符分块 + 块重叠（v1.1）**：按段落 → 句子优先级多层递归切分，搭配重叠窗口缓解语义硬截断；PDF 表格规范化、OCR 乱码过滤
- ✅ **混合检索 BM25 + 向量（v1.1）**：纯 Python BM25 零依赖实现，向量语义召回 + BM25 关键词精准命中加权融合，支持配置开关一键回退纯向量
- ✅ **RAG 评估脚本（v1.1）**：无 LLM 依赖，自动对比不同检索方案 Recall@K，输出评估报告
- ✅ **可视化前端管理台**：文档管理（三栏布局 + 分片预览）、知识库问答（会话历史 + 引用溯源 + 自动滚动）、检索评估（弹窗编辑用例 + 多标签 + 对比报告）、系统设置
- ✅ **检索评估 API**：`POST /api/eval/run` 量化对比纯向量 vs 混合检索的 Recall@K / 耗时
- ✅ **日志路由**：`/api/log` 记录用户操作与 RAG 问答耗时
- ✅ **多标签文档管理**：支持一个文档打多个 tag，检索评估支持多 tag 匹配（命中任意一个即算）

---

> **💡 配置分两类**：
> - **必填**：必须正确填写才能跑起来
> - **可选**：有默认值，不配置也能跑（除非你想自定义）

## 📦 环境要求

- Python **3.10+**（推荐 3.11 / 3.13）
- Windows / macOS / Linux
- 可访问互联网（首次运行需下载 Embedding + Reranker 模型，约 1~2 GB）

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/B-rabbit-B/enterprise-rag-platform.git
cd enterprise-rag-platform
```

### 2. 创建虚拟环境 & 安装依赖

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
# python3 -m venv venv
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# Windows
copy .env.example .env

# macOS / Linux
# cp .env.example .env
```

编辑 `.env`：

```ini
# ════════════════════════════════════════════
# 🔴 必选配置
# ════════════════════════════════════════════

# ---- LLM（任选一种兼容 OpenAI 协议的服务商）----
# 阿里 DashScope（示例）
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# OpenAI（示例）
# LLM_API_KEY=sk-proj-xxxxxxxx
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4o-mini

# ─────────────────────────────────────────────
# 🟢 可选配置（有默认值，不填也能跑）
# ─────────────────────────────────────────────

# ---- JWT ----
JWT_SECRET_KEY=please_change_me_to_a_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# ---- SQLite ----
SQLITE_DATABASE_URL=sqlite:///./rag_app.db

# ---- 混合检索权重 ----
HYBRID_ENABLE=true
HYBRID_VECTOR_WEIGHT=0.6
HYBRID_BM25_WEIGHT=0.4
HYBRID_BM25_TOP_K=5

# ---- HuggingFace 国内镜像（强烈推荐中国大陆用户开启）----
HF_ENDPOINT=https://hf-mirror.com
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

### 4. 启动服务

```bash
python main.py
```

首次启动会自动：
- 建立 SQLite 数据库表
- 预热 Reranker 模型（首次需下载，较慢；后续秒开）
- 监听 `http://127.0.0.1:8000`

### 5. 启动前端（另开一个终端）

```bash
cd rag-admin-web
npm install       # 首次运行需安装依赖
npm run dev
```

前端运行在 <http://127.0.0.1:5173>，已配置代理自动转发 `/api/*` 到后端 8000 端口。

### 6. 访问接口文档

- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

---

---

## 📖 功能详解

### RAG 执行流水线

```
用户提问
  │
  ▼
┌──────────────────────────────────┐
│  混合检索召回                    │
│  • Chroma 向量语义召回 (top_k*2) │
│  • BM25 关键词精确召回 (top_k)   │
│  • 加权融合 (0.6 : 0.4)          │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  BGE-Reranker 重排序             │
│  Cross-encoder 精排 → top_n=3    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  tiktoken 截断 + Prompt 组装     │
└──────────────┬───────────────────┘
               │
               ▼
         LLM 生成 → 返回答案 + 溯源引用
```

### 前端页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 📊 概览 Dashboard | `/dashboard` | 文档数 / 分片数 / 最近问答统计 |
| 📁 文档管理 | `/documents` | 三栏布局：标签筛选 / 文档列表 / 分片预览；支持多文件上传 + 多 tag |
| 💬 知识库问答 | `/qa` | 左会话列表 / 中答案区（自动滚动到底部）/ 右引用溯源；点击参考文档跳转高亮 |
| 🧪 检索评估 | `/evaluation` | 弹窗编辑测试用例 / 多 tag 下拉选择 / 对比纯向量 vs 混合检索 Recall@K |
| ⚙️ 系统设置 | `/settings` | 后端配置查看 / 日志 / 用户管理 |

---

## 📡 API 接口文档

除注册 / 登录接口外，其余接口均需在请求头携带 JWT：

```
Authorization: Bearer <token>
```

统一返回格式：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

### 1. 用户模块 `/api/user`

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/user/register` | 用户注册 | 公开 |
| POST | `/api/user/login` | 用户登录，返回 JWT | 公开 |
| GET | `/api/user/me` | 获取当前登录用户信息 | 登录 |

### 2. 会话模块 `/api/chat`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/chat/session` | 创建会话（请求体：`{ "session_name": "..." }`） |
| GET | `/api/chat/session` | 获取当前用户会话列表 |
| DELETE | `/api/chat/session/{session_id}` | 删除会话（级联删除消息） |
| GET | `/api/chat/session/{session_id}/messages` | 获取会话历史消息 |
| POST | `/api/chat/session/{session_id}/rag` | RAG 问答，返回答案 + 溯源片段（请求体：`{ "question": "...", "tag": "..." }`） |
| POST | `/api/chat/session/{session_id}/message` | 基础检索问答（Day4 版，用于对比调试） |

### 3. 文档 & 向量模块 `/api/doc`（仅管理员 `is_admin=true`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/doc/upload` | 上传文档（form-data：`file` + 可选 `tag`），自动切片、向量化入库 |
| GET | `/api/doc/list` | 获取文档元数据列表 |
| GET | `/api/doc/search` | 调试：按标签检索向量片段（`query` + 可选 `tag` + `top_k`） |
| GET | `/api/doc/{doc_id}/chunks` | 获取文档的实时分片（前端预览用） |
| POST | `/api/doc/{doc_id}/reparse` | 重新解析文档（重新切片 + 重新向量化） |
| DELETE | `/api/doc/{doc_id}` | 删除文档，同步清理 SQLite 与 Chroma |

### 4. 检索评估模块 `/api/eval`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/eval/meta` | 获取当前向量库中所有已入库的 tag 列表 |
| POST | `/api/eval/run` | 执行评估，对比纯向量 vs 混合检索的 Recall@K / 耗时 |

### 5. 日志模块 `/api/log`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/log/list` | 查询用户操作日志 |

### RAG 执行流程

```
用户提问
 → 混合检索：向量召回(top_k*2) + BM25关键词召回(top_k) → 加权融合 (默认 0.6:0.4)
 → BGE-Reranker 重排序 (top_n=3)
 → tiktoken 上下文截断
 → 组装 Prompt（携带文档片段）
 → 调用 LLM
 → 返回回答 + 溯源引用片段
```

---

## 🧪 5 分钟全流程 Demo

> 仓库 **不包含私有业务数据**，请自行准备公开文档（PDF / TXT / MD）。

```
步骤 1：注册管理员账号
  POST /api/user/register  { username, password, is_admin: true }

步骤 2：上传文档（可同时上传多个，支持多 tag）
  POST /api/doc/upload  →  form-data: file + tag="技术架构,安全"
  后端自动：解析 → 递归分块 → Embedding → 写入 Chroma

步骤 3：查看分片预览（前端文档管理页第三栏）
  GET /api/doc/{id}/chunks

步骤 4：开始 RAG 问答
  前端：知识库问答页 → 新建会话 → 提问
  后端执行完整流水线 → 返回答案 + 引用原文片段

步骤 5：量化评估检索效果
  前端：检索评估页 → 添加/编辑测试用例 → 开始评估
  后端：纯向量 vs 混合检索 → Recall@K + 耗时对比表
```

---

## 📁 项目目录结构

```
enterprise-rag-platform/
├── config/              # 配置管理（settings.py）
├── core/                # 数据库基类（db_base.py）
├── middleware/          # JWT 鉴权中间件、全局异常处理
├── models/              # SQLAlchemy ORM 模型（user / chat / doc / log）
├── routers/             # 路由：user / chat / doc / eval / log
├── schemas/             # Pydantic 请求 / 响应模型
├── service/             # 业务逻辑层（chat / doc / rag）
├── static/              # 静态资源（fastapi 模板用）
├── templates/           # Jinja2 模板
├── tests/               # 测试脚本（含 RAG 检索效果评估）
├── utils/               # jwt / logger / rerank / response / bm25 / token_counter
│
├── rag-admin-web/       # 🖥️ 前端（Vite + Vue3 + TS）
│   ├── src/
│   │   ├── api/         # Axios 请求模块（chat / doc / request / stats / user）
│   │   ├── data/        # Mock 数据（documents / evaluation / qa / overview）
│   │   ├── router/      # Vue Router 路由
│   │   ├── stores/      # Pinia 状态管理
│   │   ├── styles/      # 主题 CSS（theme.css）
│   │   ├── views/       # 页面（Dashboard / DocManage / Chat / Evaluation / Settings）
│   │   ├── components/  # 公共组件
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts   # 含 /api 代理到后端 8000
│   ├── tsconfig*.json
│   └── package.json
│
├── .env.example         # 环境变量模板（提交到仓库）
├── .gitignore
├── deps.py              # FastAPI 依赖注入（DB session / 当前用户）
├── init_db.py           # 数据库初始化脚本（可选）
├── main.py              # 应用入口
├── requirements.txt
└── README.md
```

---

## 🔧 常见问题 FAQ

**Q1：首次启动很慢？**
首次下载 Embedding + Reranker 模型约 1~2 GB，后续启动读取本地缓存。

**Q2：如何重置向量库？**
直接删除 `chroma_db/` 目录，同时删除 `rag_app.db` 可完全重置数据库。

**Q3：接口返回 401？**
请在请求头正确携带 `Authorization: Bearer <你的token>`；`/api/user/register`、`/api/user/login`、`/docs` 为公开接口。

**Q4：Windows 下 HuggingFace 符号链接警告？**
已在 `main.py` 与 `.env.example` 中设置 `HF_HUB_DISABLE_SYMLINKS_WARNING=1` 屏蔽。

**Q5：为什么管理员接口 403？**
请在注册时设置 `is_admin=true`，或直接在 SQLite 中将 `user.is_admin` 置为 1。

---

## 🛠 完整技术栈

### 后端

| 分类 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步，自动生成 Swagger / ReDoc |
| 数据库 | SQLAlchemy + SQLite | 用户 / 会话 / 消息 / 文档元数据 |
| 向量库 | ChromaDB | 本地向量存储与语义检索 |
| 文档处理 | LangChain / PyPDF | PDF / TXT / MD 解析 + 递归分块 |
| Embedding | all-MiniLM-L6-v2 | 多语言通用向量 |
| Reranker | bge-reranker-base | Cross-encoder 语义精排 |
| LLM | 兼容 OpenAI 协议（qwen / gpt 等） | `.env` 可切换 |
| 鉴权 | python-jose + passlib(bcrypt) | JWT + 密码加盐 |
| 配置 | pydantic-settings + python-dotenv | `.env` 管理 |
| 日志 | 自研按天滚动 logger | 结构化字段：user_id / query / hit_count / cost_sec |

### 前端

| 分类 | 技术 | 说明 |
|------|------|------|
| 构建 | Vite | 秒级热更新 |
| 框架 | Vue 3.4 + TypeScript | Composition API |
| UI | Element-Plus | 企业级组件库 + 深蓝主题 |
| 状态 | Pinia | 用户状态管理 |
| HTTP | Axios | 统一拦截 + JWT 自动注入 |
| 路由 | Vue Router | 哈希路由 |

---

## 🚧 Roadmap

### ✅ 已完成
- [x] JWT 鉴权 + 管理员权限分级
- [x] 文档上传 / 删除 / 重新解析
- [x] 递归字符分块 + PDF 乱码清洗
- [x] BM25 + 向量混合检索（纯 Python 零依赖 BM25）
- [x] BGE-Reranker 重排
- [x] 空检索短路优化
- [x] 可视化前端管理台（5 个页面）
- [x] 检索评估 API + 前端弹窗编辑用例
- [x] 多标签文档管理 + 多 tag 匹配

### 📋 待迭代
- [ ] 部分接口返回裸 ORM 对象，统一 `{code, msg, data}` 格式
- [ ] SSE 流式问答输出（前端答案气泡已预留）
- [ ] Dockerfile + docker-compose 容器化
- [ ] 单元测试用例 + CI
- [ ] 评估报告导出（PDF / CSV）
- [ ] 文档在线预览（PDF.js）

---

## ⚠️ 边界说明

| 项目 | 说明 |
|------|------|
| **开发模式** | 本项目用于学习 / 演示，未做生产级性能测试与安全加固 |
| **数据库** | 默认 SQLite 单文件，生产建议切换 PostgreSQL / MySQL |
| **向量库** | 默认 ChromaDB 本地持久化，数据量 >10w 建议 Milvus / Qdrant |
| **LLM 密钥** | `.env` 包含真实 API Key，切勿提交到公开仓库（.gitignore 已排除） |
| **模型下载** | 首次启动需下载 Embedding + Reranker（~1.2 GB），开启 `HF_ENDPOINT=https://hf-mirror.com` 加速 |

---

## 🤝 贡献指南

欢迎 Issue / PR！开发流程：

```bash
# 1. Fork 仓库 → 克隆到本地
git clone https://github.com/B-rabbit-B/enterprise-rag-platform.git

# 2. 创建特性分支
git checkout -b feat/your-feature

# 3. 提交代码（commit message 遵循 Conventional Commits）
git commit -m "feat: 新增 xxx 功能"

# 4. 推送到你的 Fork → 提交 Pull Request
git push origin feat/your-feature
```

提交前请确保：
- [ ] 后端代码通过 `ruff` / `pylint` 检查
- [ ] 前端代码通过 `npm run lint` 检查
- [ ] 新功能添加了对应的测试或使用说明

---

## 📄 License

[MIT License](LICENSE) © 2026 B-rabbit-B

> 如果你觉得这个项目有用，请点个 ⭐ Star，这对持续迭代是最大的鼓励！

---

### ⭐ Star History

[![Star History](https://api.star-history.com/svg?repos=B-rabbit-B/enterprise-rag-platform&type=Date)](https://star-history.com/#B-rabbit-B/enterprise-rag-platform&Date)
```