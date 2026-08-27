# 企业知识库 RAG 问答平台

基于 FastAPI + LangChain + Chroma 构建的轻量级企业级 RAG（Retrieval-Augmented Generation，检索增强生成）后端服务。

用户可上传公开技术文档构建私有知识库，通过 「向量检索 + Rerank 重排 + Token 截断 + LLM 生成」 实现带文档溯源的智能问答。

> 面向学习 / 演示场景，支持完整 RAG 业务闭环：
> 鉴权 → 文档入库 → 向量化 → 检索召回 → Rerank 精排 → Token 截断 → Prompt 组装 → LLM 生成 → 结果溯源。

---

## 🛠 技术栈

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

---

## ✨ 项目特性

- ✅ **完整 RAG 闭环**：用户问题 → 向量检索(top_k) → Rerank 重排(top_n) → Token 截断 → Prompt 组装 → LLM 调用 → 返回答案 + 文档溯源
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

---

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

编辑 `.env`，填入你自己的信息：

```ini
# ================ LLM 配置（必填） ================
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# ================ JWT 配置 ================
JWT_SECRET_KEY=please_change_me_to_a_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# ================ SQLite 数据库 ================
SQLITE_DATABASE_URL=sqlite:///./rag_app.db

# ================ 可选：HuggingFace 国内镜像 ================
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

### 5. 访问接口文档

- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

---

## 📡 接口简要说明

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
| DELETE | `/api/doc/{doc_id}` | 删除文档，同步清理 SQLite 与 Chroma |

### RAG 执行流程

```
用户提问
 → 向量检索 (top_k=5)
 → BGE-Reranker 重排序 (top_n=3)
 → tiktoken 上下文截断
 → 组装 Prompt（携带文档片段）
 → 调用 LLM
 → 返回回答 + 溯源引用片段
```

---

## 🧪 测试数据源说明

仓库 **不包含任何私有业务数据**。

测试请自行准备公开技术文档，例如：
- Python / FastAPI / LangChain 官方文档（PDF / TXT / MD）
- 开源项目 README、技术博客导出内容
- 任何你希望作为「企业知识库」的公开资料

上传文档后（`POST /api/doc/upload`），针对文档内容提问，即可得到带文档溯源的回答。

---

## 📁 项目目录结构

```
enterprise-rag-platform/
├── config/              # 配置管理（settings.py）
├── core/                # 数据库基类（db_base.py）
├── middleware/          # JWT 鉴权中间件、全局异常处理
├── models/              # SQLAlchemy ORM 模型（user / chat / doc）
├── routers/             # 路由：user / chat / doc
├── schemas/             # Pydantic 请求 / 响应模型
├── service/             # 业务逻辑层（chat / doc / rag）
├── tests/               # 测试用例
├── utils/               # jwt / logger / rerank / response / token_counter
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

## 🚧 待迭代优化点

- [x] ~~创建会话硬编码标题「新会话」~~（已修复，改为使用前端传入的 `session_name`）
- [ ] 部分会话接口仍返回裸 ORM 对象，可进一步统一为 `code/msg/data` 响应格式
- [ ] 支持 SSE 流式问答输出
- [ ] Dockerfile 容器化部署 + docker-compose
- [ ] 增加单元测试用例

---

## 📄 License

MIT License. 欢迎 Fork / Star / PR。
```