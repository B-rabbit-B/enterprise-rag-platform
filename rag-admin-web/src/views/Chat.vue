<template>
  <div class="qa-page">
    <!-- 顶部标题 -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <h2 class="page-title">知识库问答</h2>
        <span class="page-sub">
          当前会话：<span class="font-mono" style="color:var(--primary);">{{ currentSessionName }}</span>
        </span>
      </div>
      <div class="toolbar-right">
        <el-button size="small" :icon="Plus" @click="createNewSession">新建会话</el-button>
      </div>
    </div>

    <!-- ========== 三栏主体 ========== -->
    <div class="qa-layout">
      <!-- ========== 左：会话列表 + 问题输入 ========== -->
      <aside class="console-card qa-input-panel">
        <!-- 会话切换 -->
        <div class="session-section">
          <h3 class="panel-title">会话</h3>
          <div v-if="!sessions.length" class="font-mono" style="font-size:12px;color:var(--muted-foreground);">加载中...</div>
          <div v-for="s in sessions" :key="s.session_id"
               class="session-item"
               :class="{ active: s.session_id === currentSessionId }"
               @click="switchSession(s.session_id)">
            <span class="session-name">{{ s.session_name }}</span>
            <el-icon class="session-del" @click.stop="deleteSession(s.session_id)"><Close /></el-icon>
          </div>
        </div>

        <el-divider style="margin:14px 0;" />

        <h3 class="panel-title">问题输入</h3>

        <el-input
          v-model="question"
          type="textarea"
          :autosize="{ minRows: 6, maxRows: 10 }"
          placeholder="在此输入你的问题，比如：RAG 的完整流程是什么？"
          resize="none"
        />

        <!-- 检索策略 -->
        <div class="strategy-row">
          <span class="strategy-label">检索策略</span>
          <el-radio-group v-model="strategy" size="small">
            <el-radio-button value="hybrid">混合检索</el-radio-button>
            <el-radio-button value="vector">纯向量</el-radio-button>
            <el-radio-button value="bm25">BM25 关键词</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 快捷问题 -->
        <div class="quick-questions">
          <span class="quick-label">试试这些：</span>
          <span
            v-for="q in quickQuestions"
            :key="q"
            class="quick-chip font-mono"
            @click="question = q"
          >{{ q }}</span>
        </div>

        <!-- 提交按钮 -->
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!question.trim()"
          class="submit-btn"
          @click="submit"
        >
          <el-icon><Promotion /></el-icon>
          提交问答
        </el-button>
      </aside>

      <!-- ========== 中：消息气泡列表 ========== -->
      <section class="qa-answer-panel" ref="answerPanelRef">
        <div v-if="!messages.length && !loading" class="empty-state">
          <el-icon :size="48" color="var(--border)"><ChatDotRound /></el-icon>
          <p style="margin-top:12px;color:var(--muted-foreground);">请输入问题开始问答</p>
        </div>

        <!-- Loading 骨架（仅首次） -->
        <div v-else-if="loading && messages.length === 0" class="answer-skeleton">
          <div class="sk-line sk-title" />
          <div class="sk-line" />
          <div class="sk-line" />
          <div class="sk-line sk-short" />
          <div class="sk-line" />
          <div class="sk-line sk-short" />
        </div>

        <!-- 消息气泡列表 -->
        <template v-else>
          <div v-for="m in messages" :key="m.id" class="msg-bubble" :class="m.role">
            <!-- user -->
            <template v-if="m.role === 'user'">
              <div class="msg-avatar user-avatar">U</div>
              <div class="msg-body user-body">
                <div class="msg-content">{{ m.content }}</div>
                <div class="msg-time font-mono">{{ formatTime(m.create_time) }}</div>
              </div>
            </template>

            <!-- assistant -->
            <template v-else>
              <div class="msg-avatar assistant-avatar">AI</div>
              <div class="msg-body assistant-body">
                <pre class="msg-content answer-text">{{ m.content }}</pre>
                <div class="msg-time font-mono">{{ formatTime(m.create_time) }}</div>

                <!-- 参考片段（仅 RAG 回答有） -->
                <div v-if="m.extra_json?.references?.length" class="refs-block">
                  <div class="refs-title">
                    <el-icon :size="14"><Link /></el-icon>
                    <span>参考片段（{{ m.extra_json.references.length }}）</span>
                  </div>
                  <div v-for="(r, i) in m.extra_json.references" :key="i"
                       class="ref-item clickable"
                       @click="gotoDoc(r)"
                       @mouseenter="hoverRef = i"
                       @mouseleave="hoverRef = -1">
                    <span class="ref-idx font-mono">[{{ i + 1 }}]</span>
                    <span class="ref-doc font-mono">{{ r.metadata?.filename || '-' }}</span>
                    <span class="ref-sim font-mono">{{ (r.similarity || 0).toFixed(2) }}</span>
                    <span class="ref-text">{{ r.document?.slice(0, 60) }}...</span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- 正在回答的骨架（追加在最后一条 assistant 之后） -->
          <div v-if="loading" class="msg-bubble assistant">
            <div class="msg-avatar assistant-avatar">AI</div>
            <div class="answer-skeleton skeleton-inline">
              <div class="sk-line" />
              <div class="sk-line" />
              <div class="sk-line sk-short" />
            </div>
          </div>
        </template>
      </section>

      <!-- ========== 右：溯源证据 ========== -->
      <aside class="console-card qa-evidence-panel">
        <h3 class="panel-title">溯源证据</h3>
        <p v-if="!result || !result.references?.length" class="section-desc">提交问答后展示召回详情</p>

        <div v-else class="evidence-list">
          <div v-for="(e, i) in result.references" :key="i"
               class="evidence-card console-card clickable"
               :class="{ active: hoverRef === i }"
               @click="gotoDoc(e)">
            <div class="evidence-head">
              <span class="evidence-rank font-mono">#{{ i + 1 }}</span>
              <span class="evidence-doc font-mono">{{ e.metadata?.filename || 'unknown' }}</span>
            </div>
            <div class="evidence-scores">
              <div class="score-row">
                <span class="score-label">相似度</span>
                <div class="score-bar-wrap">
                  <div class="score-bar score-vec" :style="{ width: ((e.similarity || 0) * 100) + '%' }" />
                </div>
                <span class="score-val font-mono">{{ (e.similarity || 0).toFixed(2) }}</span>
              </div>
              <div class="score-row">
                <span class="score-label">Rerank</span>
                <div class="score-bar-wrap">
                  <div class="score-bar score-rerank" :style="{ width: ((e.rerank_score || 0) * 100) + '%' }" />
                </div>
                <span class="score-val font-mono">{{ (e.rerank_score || 0).toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion, Link, ChatDotRound, Plus, Close } from '@element-plus/icons-vue'
import request from '@/api/request'

// ========== 接口类型 ==========
interface Session {
  session_id: number
  session_name: string
  create_time: string
  update_time: string
}
interface RefItem {
  document: string
  metadata: { filename?: string; doc_id?: number; [k: string]: any }
  similarity: number
  rerank_score: number
}
interface RAGResult {
  success: boolean
  answer: string
  references: RefItem[]
  message_id?: number
}

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  extra_json?: {
    references?: RefItem[]
    strategy?: string
  } | null
  create_time: string
}

type RetrievalStrategy = 'hybrid' | 'vector' | 'bm25'

// ========== 状态 ==========
const sessions = ref<Session[]>([])
const currentSessionId = ref<number | null>(null)
const question = ref('')
const strategy = ref<RetrievalStrategy>('hybrid')
const loading = ref(false)
const result = ref<RAGResult | null>(null)
const hoverRef = ref(-1)
const messages = ref<ChatMessage[]>([])
const answerPanelRef = ref<HTMLElement | null>(null)

function autoScrollBottom() {
  nextTick(() => {
    const el = answerPanelRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

const currentSessionName = computed(() => {
  return sessions.value.find(s => s.session_id === currentSessionId.value)?.session_name || '未选择'
})

const quickQuestions = [
  'RAG 的完整流程是什么？',
  '混合检索怎么配置权重？',
  '项目用了什么技术栈？',
  '支持哪些文档格式？'
]

function strategyLabel(s: RetrievalStrategy) {
  return { vector: '纯向量检索', hybrid: '混合检索', bm25: 'BM25 关键词检索' }[s]
}

function formatTime(t: string): string {
  if (!t) return ''
  const d = new Date(t)
  if (isNaN(d.getTime())) return t.slice(0, 19).replace('T', ' ')
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ========== 会话管理 ==========
async function loadSessions() {
  try {
    sessions.value = await request.get<Session[]>('/chat/session')
    if (sessions.value.length) {
      currentSessionId.value = sessions.value[0].session_id
      await loadMessages(sessions.value[0].session_id)
    } else {
      await createNewSession('新会话')
    }
  } catch (_e) { /* 拦截器已提示 */ }
}

async function loadMessages(sessionId: number) {
  try {
    messages.value = await request.get<ChatMessage[]>(`/chat/session/${sessionId}/messages`)
    autoScrollBottom()
    // 如果最后一条是 assistant，用它的 references 展示在右栏
    const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAssistant?.extra_json?.references) {
      result.value = {
        success: true,
        answer: lastAssistant.content,
        references: lastAssistant.extra_json.references
      }
    } else {
      result.value = null
    }
  } catch (_e) {
    messages.value = []
    result.value = null
  }
}

async function createNewSession(name?: string) {
  try {
    const sessName = name || `会话 ${sessions.value.length + 1}`
    const sess = await request.post<Session>('/chat/session', { session_name: sessName })
    sessions.value.unshift(sess)
    currentSessionId.value = sess.session_id
    messages.value = []
    result.value = null
    question.value = ''
  } catch (_e) { /* */ }
}

async function deleteSession(id: number) {
  try {
    await ElMessageBox.confirm('确定删除此会话？', '提示', { type: 'warning' })
    await request.delete(`/chat/session/${id}`)
    sessions.value = sessions.value.filter(s => s.session_id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value[0]?.session_id || null
      result.value = null
    }
  } catch (_e) { /* 取消或拦截器 */ }
}

function switchSession(id: number) {
  currentSessionId.value = id
  loadMessages(id)
}

// ========== 跳转：点击参考文档跳转到文档管理并高亮 ==========
const router = useRouter()
function gotoDoc(item: any) {
  const filename = item?.metadata?.filename
  if (filename) {
    router.push({ path: '/documents', query: { highlight: filename } })
  }
}

// ========== 核心：RAG 问答 ==========
async function submit() {
  if (!question.value.trim() || !currentSessionId.value) return

  // 先把用户问题 push 到消息列表（乐观更新）
  const userMsg: ChatMessage = {
    id: Date.now(),
    role: 'user',
    content: question.value,
    create_time: new Date().toISOString()
  }
  messages.value.push(userMsg)
    autoScrollBottom()
  const q = question.value
  question.value = ''

  loading.value = true
  autoScrollBottom()
  try {
    const data = await request.post<RAGResult>(`/chat/session/${currentSessionId.value}/rag`, {
      question: q,
      retrieve_mode: strategy.value,
      use_rerank: true
    })

    // 构建 assistant 消息
    const assistantMsg: ChatMessage = {
      id: data.message_id || Date.now() + 1,
      role: 'assistant',
      content: data.answer || '(无回答)',
      extra_json: {
        references: data.reference || [],
        strategy: strategy.value
      },
      create_time: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    autoScrollBottom()

    // 更新 result 让右栏溯源同步
    result.value = {
      success: data.success ?? true,
      answer: assistantMsg.content,
      references: data.reference || []
    }
  } catch (_e) {
    // 失败时回滚 user 消息 + 弹错
    messages.value = messages.value.filter(m => m.id !== userMsg.id)
  } finally {
    loading.value = false
  }
}

onMounted(loadSessions)
</script>

<style scoped>
/* ========== Toolbar ========== */
.page-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.toolbar-left { display: flex; align-items: baseline; gap: 10px; }
.page-title { margin: 0; font-size: 18px; font-weight: 700; color: var(--foreground); }
.page-sub { color: var(--muted-foreground); font-size: 12px; }

/* ========== 三栏 ========== */
.qa-layout {
  display: grid;
  grid-template-columns: 320px 1fr 340px;
  gap: 16px;
  height: calc(100vh - 140px);
}

/* ========== 左：输入 ========== */
.qa-input-panel { padding: 20px 18px; display: flex; flex-direction: column; overflow-y: auto; }
.panel-title {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--muted-foreground); margin: 0 0 12px;
}

/* 会话列表 */
.session-section { }
.session-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; margin-bottom: 4px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  color: var(--foreground);
  transition: all 150ms;
}
.session-item:hover { background: var(--accent); }
.session-item.active {
  background: var(--accent);
  color: var(--primary);
  font-weight: 500;
  outline: 1px solid var(--primary);
}
.session-name {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
}
.session-del {
  opacity: 0; transition: opacity 150ms;
  font-size: 14px; color: var(--muted-foreground);
}
.session-item:hover .session-del { opacity: 1; }
.session-del:hover { color: var(--destructive) !important; }
.strategy-row { margin-top: 16px; display: flex; flex-direction: column; gap: 8px; }
.strategy-label { font-size: 12px; color: var(--muted-foreground); font-weight: 500; }
.quick-questions { margin-top: 16px; }
.quick-label { font-size: 12px; color: var(--muted-foreground); display: block; margin-bottom: 8px; }
.quick-chip {
  display: inline-block;
  font-size: 11px;
  padding: 4px 10px;
  background: var(--accent);
  color: var(--accent-foreground);
  border-radius: 9999px;
  margin: 0 4px 6px 0;
  cursor: pointer;
  transition: all 120ms;
}
.quick-chip:hover { background: var(--primary); color: #fff; }
.submit-btn { margin-top: auto; width: 100%; }

/* ========== 中：回答 ========== */
.qa-answer-panel {
  padding: 20px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.answer-meta {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
}
.answer-body { margin-bottom: 20px; }
.answer-text {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  margin: 0;
  color: var(--foreground);
  background: var(--background);
  padding: 16px 20px;
  border-radius: var(--radius-md);
  border-left: 3px solid var(--primary);
}

/* 骨架屏 */
.answer-skeleton { padding: 4px 0; }
.sk-line {
  height: 14px;
  background: linear-gradient(90deg, var(--accent) 25%, #f0f4fa 50%, var(--accent) 75%);
  background-size: 200% 100%;
  animation: sk-pulse 1.4s infinite;
  border-radius: 4px;
  margin-bottom: 10px;
}
.sk-title { height: 20px; width: 40%; margin-bottom: 18px; }
.sk-short { width: 60%; }
@keyframes sk-pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 参考片段 */
.refs-block { border-top: 1px solid var(--border); padding-top: 16px; }
.refs-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 600; color: var(--foreground);
  margin-bottom: 10px;
}
.ref-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
  background: var(--background);
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
  font-size: 12px;
  cursor: pointer;
}
.ref-item.clickable { cursor: pointer; }
.ref-item:hover { background: var(--accent); }
.ref-idx { color: var(--primary); font-weight: 600; }
.ref-doc { color: var(--foreground); font-weight: 500; flex-shrink: 0; }
.ref-sim { color: var(--success); font-size: 11px; flex-shrink: 0; }
.ref-text { color: var(--muted-foreground); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ========== 右：溯源 ========== */
.qa-evidence-panel { padding: 20px 16px; overflow-y: auto; }
.section-desc { font-size: 12px; color: var(--muted-foreground); margin: 0 0 16px; }
.evidence-list { display: flex; flex-direction: column; gap: 10px; }
.evidence-card {
  padding: 12px 14px;
}
.evidence-card.active {
  border-color: var(--primary);
  box-shadow: var(--shadow-md);
}
.evidence-card.clickable { cursor: pointer; }
.evidence-card.clickable:hover {
  border-color: var(--primary);
  transform: translateX(-2px);
}
.evidence-card.clickable { cursor: pointer; }
.evidence-card.clickable:hover {
  border-color: var(--primary);
  transform: translateX(-2px);
}
.evidence-card.clickable { cursor: pointer; }
.evidence-card.clickable:hover {
  border-color: var(--primary);
  transform: translateX(-2px);
}
.evidence-head {
  display: flex; gap: 8px; align-items: center; margin-bottom: 8px;
}
.evidence-rank {
  background: var(--primary); color: #fff;
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.evidence-doc { font-size: 12px; font-weight: 500; color: var(--foreground); }
.evidence-scores { margin-bottom: 8px; }
.score-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 5px;
}
.score-label { font-size: 11px; color: var(--muted-foreground); width: 52px; flex-shrink: 0; }
.score-bar-wrap {
  flex: 1; height: 6px; background: var(--background); border-radius: 3px; overflow: hidden;
}
.score-bar { height: 100%; border-radius: 3px; transition: width 400ms ease; }
.score-vec { background: var(--rag-retrieve); }
.score-rerank { background: var(--rag-rerank); }
.score-val { font-size: 11px; width: 34px; text-align: right; flex-shrink: 0; }

/* ========== 空状态 ========== */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%;
}

/* ========== 消息气泡 ========== */
.msg-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: msgFadeIn 200ms ease;
}
@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.user-avatar {
  background: var(--primary); color: #fff;
}
.assistant-avatar {
  background: var(--success-bg); color: var(--success);
}

.msg-body {
  flex: 1;
  max-width: calc(100% - 60px);
}
.msg-bubble.user {
  flex-direction: row-reverse;
}
.msg-bubble.user .msg-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.msg-content {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.user-body .msg-content {
  background: var(--primary);
  color: #fff;
  border-bottom-right-radius: var(--radius-sm);
}
.assistant-body .msg-content {
  background: var(--background);
  border: 1px solid var(--success-border, #b8e1d2);
  border-bottom-left-radius: var(--radius-sm);
}

.msg-time {
  font-size: 11px;
  color: var(--muted-foreground);
  margin-top: 6px;
}

.skeleton-inline {
  padding: 12px 16px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  border-bottom-left-radius: var(--radius-sm);
}
</style>