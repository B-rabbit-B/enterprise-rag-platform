<template>
  <div class="settings-page">
    <!-- ========== 顶部 ========== -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <h2 class="page-title">系统设置</h2>
        <span class="page-sub">参数修改后自动保存到浏览器 localStorage</span>
      </div>
      <div class="toolbar-right">
        <el-button :icon="Refresh" @click="resetAll">恢复默认</el-button>
        <el-button type="primary" :icon="Check" @click="saveAll">保存全部</el-button>
      </div>
    </div>

    <!-- ========== 四组卡片 ========== -->
    <div class="settings-grid">
      <!-- 1. 检索设置 -->
      <div class="console-card settings-card">
        <div class="card-head">
          <div class="card-head-icon" style="background:#0066cc18;color:#0066cc;">
            <el-icon :size="18"><Aim /></el-icon>
          </div>
          <div>
            <h3 class="card-title">检索设置</h3>
            <p class="card-sub">混合检索策略与权重参数</p>
          </div>
        </div>

        <div class="settings-form">
          <div class="form-row">
            <span class="form-label">默认检索方式</span>
            <el-radio-group v-model="settings.defaultStrategy">
              <el-radio-button value="hybrid">混合检索</el-radio-button>
              <el-radio-button value="vector">纯向量</el-radio-button>
              <el-radio-button value="bm25">BM25</el-radio-button>
            </el-radio-group>
          </div>

          <div class="form-row">
            <span class="form-label">向量权重 <span class="font-mono" style="color:var(--muted-foreground);">{{ settings.vectorWeight.toFixed(1) }}</span></span>
            <el-slider v-model="settings.vectorWeight" :min="0" :max="1" :step="0.05" :show-tooltip="false" />
          </div>

          <div class="form-row">
            <span class="form-label">BM25 权重 <span class="font-mono" style="color:var(--muted-foreground);">{{ settings.bm25Weight.toFixed(1) }}</span></span>
            <el-slider v-model="settings.bm25Weight" :min="0" :max="1" :step="0.05" :show-tooltip="false" />
          </div>

          <div class="form-row">
            <span class="form-label">Top K 召回数量</span>
            <el-input-number v-model="settings.topK" :min="1" :max="20" size="default" />
          </div>
        </div>
      </div>

      <!-- 2. 模型设置 -->
      <div class="console-card settings-card">
        <div class="card-head">
          <div class="card-head-icon" style="background:#4ab89e18;color:#0d7a3a;">
            <el-icon :size="18"><Cpu /></el-icon>
          </div>
          <div>
            <h3 class="card-title">模型设置</h3>
            <p class="card-sub">Embedding / Rerank / LLM 模型名称</p>
          </div>
        </div>

        <div class="settings-form">
          <div class="form-row">
            <span class="form-label">Embedding 模型</span>
            <el-input v-model="settings.embeddingModel" size="default" />
          </div>
          <div class="form-row">
            <span class="form-label">Rerank 模型</span>
            <el-input v-model="settings.rerankModel" size="default" />
          </div>
          <div class="form-row">
            <span class="form-label">LLM 模型</span>
            <el-input v-model="settings.llmModel" size="default" />
          </div>
        </div>
      </div>

      <!-- 3. 文档解析设置 -->
      <div class="console-card settings-card">
        <div class="card-head">
          <div class="card-head-icon" style="background:#a85c1818;color:#a85c18;">
            <el-icon :size="18"><Document /></el-icon>
          </div>
          <div>
            <h3 class="card-title">文档解析设置</h3>
            <p class="card-sub">分块方式 / 块大小 / 重叠参数</p>
          </div>
        </div>

        <div class="settings-form">
          <div class="form-row">
            <span class="form-label">分块方式</span>
            <el-select v-model="settings.chunkMethod" size="default" style="width:200px;">
              <el-option label="递归分块（推荐）" value="recursive" />
              <el-option label="固定长度" value="fixed" />
              <el-option label="按段落" value="paragraph" />
            </el-select>
          </div>
          <div class="form-row">
            <span class="form-label">块大小（Token）</span>
            <el-input-number v-model="settings.chunkSize" :min="100" :max="4096" :step="64" size="default" />
          </div>
          <div class="form-row">
            <span class="form-label">重叠大小（Token）</span>
            <el-input-number v-model="settings.chunkOverlap" :min="0" :max="500" :step="10" size="default" />
          </div>
          <div class="form-row">
            <span class="form-label">过滤乱码字符</span>
            <el-switch v-model="settings.filterGarbled" />
          </div>
          <div class="form-row">
            <span class="form-label">解析表格为文本</span>
            <el-switch v-model="settings.parseTables" />
          </div>
        </div>
      </div>

      <!-- 4. 权限设置 -->
      <div class="console-card settings-card">
        <div class="card-head">
          <div class="card-head-icon" style="background:#b3232318;color:#b32323;">
            <el-icon :size="18"><Lock /></el-icon>
          </div>
          <div>
            <h3 class="card-title">权限设置</h3>
            <p class="card-sub">用户、角色、知识库权限管理</p>
          </div>
        </div>

        <div class="perm-grid">
          <div v-for="p in permEntries" :key="p.key" class="perm-item console-card" @click="openPerm(p.key)">
            <el-icon :size="20" style="color:var(--primary);margin-bottom:8px;"><component :is="p.icon" /></el-icon>
            <div class="perm-label">{{ p.label }}</div>
            <div class="font-mono" style="font-size:11px;color:var(--success);">可用 ↗</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== Drawer: 用户管理 ========== -->
    <el-drawer v-model="drawerUser" title="用户管理" size="620px" class="perm-drawer">
      <div class="drawer-toolbar">
        <el-button size="small" @click="loadUsers" :icon="Refresh">刷新</el-button>
      </div>
      <el-table :data="users" stripe size="small" empty-text="暂无用户">
        <el-table-column prop="id" label="ID" width="60" class-name="font-mono" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">{{ row.is_admin ? '管理员' : '普通用户' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="170" class-name="font-mono" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="toggleAdmin(row)">{{ row.is_admin ? '取消管理' : '设为管理' }}</el-button>
            <el-button link type="danger" size="small" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- ========== Drawer: 角色管理 ========== -->
    <el-drawer v-model="drawerRole" title="角色管理" size="520px" class="perm-drawer">
      <div class="role-desc">
        本平台采用 <b>两级角色</b>：<span class="font-mono">管理员</span> / <span class="font-mono">普通用户</span>。
        管理员可管理用户、查看日志；普通用户仅能使用文档上传与问答功能。
      </div>
      <el-table :data="roleStats" stripe size="small" style="margin-top:16px;">
        <el-table-column prop="role" label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="row.role === '管理员' ? 'danger' : 'info'" size="small">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="count" label="用户数" class-name="font-mono" />
        <el-table-column prop="desc" label="权限说明" />
      </el-table>
    </el-drawer>

    <!-- ========== Drawer: 知识库权限 ========== -->
    <el-drawer v-model="drawerKbPerm" title="知识库权限" size="520px" class="perm-drawer">
      <div class="role-desc">
        当前所有用户可访问全部知识库文档。如需按用户隔离，可在此配置。<br/>
        <span style="color:var(--warning);">⚠️ 此模块暂为预览功能，数据为本地模拟。</span>
      </div>
      <el-table :data="kbPermMock" stripe size="small" style="margin-top:16px;">
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column label="可访问知识库">
          <template #default="{ row }">
            <el-tag v-for="k in row.kbs" :key="k" size="small" style="margin-right:4px;">{{ k }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="编辑" width="80">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="editKbPerm(row)">设置</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- ========== Drawer: 操作日志 ========== -->
    <el-drawer v-model="drawerLog" title="操作日志" size="720px" class="perm-drawer">
      <div class="drawer-toolbar">
        <el-select v-model="logActionFilter" placeholder="全部操作" clearable size="small" style="width:160px;">
          <el-option label="登录" value="login" />
          <el-option label="文档上传" value="upload" />
          <el-option label="删除文档" value="delete_doc" />
          <el-option label="问答" value="chat" />
        </el-select>
        <el-button size="small" @click="loadLogs" :icon="Refresh">查询</el-button>
      </div>
      <el-table :data="logs" stripe size="small" empty-text="暂无日志">
        <el-table-column prop="id" label="#" width="60" class-name="font-mono" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-tag size="small">{{ logActionLabel(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="对象" min-width="140" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="120" class-name="font-mono" />
        <el-table-column prop="create_time" label="时间" width="170" class-name="font-mono" />
      </el-table>
      <div class="log-pager">
        <el-pagination
          background layout="prev, pager, next, total"
          :total="logTotal"
          v-model:current-page="logPage"
          :page-size="logPageSize"
          @current-change="loadLogs"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Check } from '@element-plus/icons-vue'
import { loadSettings, saveSettings, defaultSettings } from '@/data/settings'
import type { IRagSettings } from '@/data/types'

const settings = reactive<IRagSettings>(loadSettings())

// ========== 鉴权工具 ==========
function authHeaders(): Record<string, string> {
  const t = localStorage.getItem('token') || ''
  return { Authorization: `Bearer ${t}`, 'Content-Type': 'application/json' }
}

// ========== Drawer 开关 ==========
const drawerUser = ref(false)
const drawerRole = ref(false)
const drawerKbPerm = ref(false)
const drawerLog = ref(false)

const permEntries = [
  { key: 'user',   label: '用户管理',  icon: 'User' },
  { key: 'role',   label: '角色管理',  icon: 'UserFilled' },
  { key: 'kbperm', label: '知识库权限',icon: 'Key' },
  { key: 'log',    label: '操作日志',  icon: 'Tickets' }
]

function openPerm(key: string) {
  if (key === 'user')   { drawerUser.value = true; loadUsers() }
  if (key === 'role')   { drawerRole.value = true }
  if (key === 'kbperm') { drawerKbPerm.value = true }
  if (key === 'log')    { drawerLog.value = true; loadLogs() }
}

// ========== 用户管理 ==========
interface IUser { id: number; username: string; is_admin: boolean; create_time: string }
const users = ref<IUser[]>([])

async function loadUsers() {
  try {
    const r = await fetch('/api/user/list', { headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) { users.value = j.data; updateRoleStats() }
    else ElMessage.warning(j.msg || '获取用户列表失败')
  } catch { ElMessage.warning('后端未连接') }
}

async function toggleAdmin(row: IUser) {
  try {
    const r = await fetch(`/api/user/${row.id}/toggle-admin`, { method: 'POST', headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) { ElMessage.success('已更新'); loadUsers() }
    else ElMessage.error(j.msg)
  } catch { ElMessage.error('请求失败') }
}

async function deleteUser(row: IUser) {
  try {
    await ElMessageBox.confirm(`确认删除用户 "${row.username}"？`, '危险操作', { type: 'warning' })
    const r = await fetch(`/api/user/${row.id}`, { method: 'DELETE', headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) { ElMessage.success('已删除'); loadUsers() }
    else ElMessage.error(j.msg)
  } catch (_) { /* 用户取消 */ }
}

// ========== 角色管理（两级）==========
const roleStats = ref<{ role: string; count: number; desc: string }[]>([ 
  { role: '管理员', count: 0, desc: '可管理用户 / 查看日志 / 管理知识库' },
  { role: '普通用户', count: 0, desc: '上传文档 / 发起问答 / 查看自己的会话' }
])

function updateRoleStats() {
  const adminCount = users.value.filter(u => u.is_admin).length
  roleStats.value[0].count = adminCount
  roleStats.value[1].count = users.value.length - adminCount
}

// ========== 知识库权限（mock）==========
const kbPermMock = ref([
  { username: 'admin',    kbs: ['全部知识库'] },
  { username: 'alice',    kbs: ['产品手册', '技术规范'] },
  { username: 'bob',      kbs: ['财务报表'] },
  { username: 'charlie',  kbs: ['产品手册', '技术规范', '财务报表'] }
])
function editKbPerm(row: any) { ElMessage.info(`编辑 ${row.username} 的知识库权限（开发中）`) }

// ========== 操作日志 ==========
interface ILog { id: number; username: string | null; action: string; target: string | null; ip: string | null; create_time: string | null }
const logs = ref<ILog[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = 50
const logActionFilter = ref('')

function logActionLabel(a: string) {
  const map: Record<string, string> = { login: '登录', upload: '文档上传', delete_doc: '删除文档', chat: '问答', register: '注册' }
  return map[a] || a
}

async function loadLogs() {
  try {
    const url = `/api/logs?page=${logPage.value}&page_size=${logPageSize}${logActionFilter.value ? '&action=' + logActionFilter.value : ''}`
    const r = await fetch(url, { headers: authHeaders() })
    const j = await r.json()
    if (j.code === 0) {
      logs.value = j.data.items || []
      logTotal.value = j.data.total || 0
    } else ElMessage.warning(j.msg || '获取日志失败')
  } catch { ElMessage.warning('后端未连接') }
}

// ========== 页面按钮 ==========
function saveAll() {
  saveSettings(settings)
  ElMessage.success('设置已保存')
}
function resetAll() {
  Object.assign(settings, defaultSettings)
  saveSettings(settings)
  ElMessage.success('已恢复默认设置')
}

// ========== 启动 ==========
onMounted(async () => {
  try {
    const resp = await fetch('/api/config')
    if (resp.ok) {
      const data = await resp.json()
      const cfg = data.data || data
      if (cfg.embedding_model) settings.embeddingModel = cfg.embedding_model
      if (cfg.llm_model) settings.llmModel = cfg.llm_model
      if (cfg.chunk_size) settings.chunkSize = cfg.chunk_size
      if (cfg.chunk_overlap) settings.chunkOverlap = cfg.chunk_overlap
      if (cfg.hybrid_vector_weight !== undefined) settings.vectorWeight = cfg.hybrid_vector_weight
      if (cfg.hybrid_bm25_weight !== undefined) settings.bm25Weight = cfg.hybrid_bm25_weight
    }
  } catch { /* 后端没启动 */ }

  // 权重自动归一化
  const updateWeights = () => {
    const total = settings.vectorWeight + settings.bm25Weight
    if (total > 1) {
      if (settings.vectorWeight >= settings.bm25Weight) settings.bm25Weight = +(1 - settings.vectorWeight).toFixed(2)
      else settings.vectorWeight = +(1 - settings.bm25Weight).toFixed(2)
    }
  }
  let lastV = settings.vectorWeight, lastB = settings.bm25Weight
  setInterval(() => {
    if (settings.vectorWeight !== lastV || settings.bm25Weight !== lastB) {
      updateWeights()
      lastV = settings.vectorWeight
      lastB = settings.bm25Weight
    }
  }, 200)
})
</script>

<style scoped>
/* ========== Toolbar ========== */
.page-toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}
.toolbar-left { display: flex; align-items: baseline; gap: 10px; }
.page-title { margin: 0; font-size: 18px; font-weight: 700; }
.page-sub { color: var(--muted-foreground); font-size: 12px; }
.toolbar-right { display: flex; gap: 10px; }

/* ========== 布局 ========== */
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  max-width: 1200px;
}

/* ========== 卡片 ========== */
.settings-card { padding: 20px 22px; }
.card-head {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}
.card-head-icon {
  width: 36px; height: 36px; border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.card-title { margin: 0; font-size: 14px; font-weight: 600; color: var(--foreground); }
.card-sub { margin: 2px 0 0; font-size: 12px; color: var(--muted-foreground); }

/* ========== 表单 ========== */
.settings-form { display: flex; flex-direction: column; gap: 18px; }
.form-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 14px;
  align-items: center;
}
.form-label { font-size: 13px; color: var(--foreground); font-weight: 500; }

/* ========== 权限入口 ========== */
.perm-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.perm-item {
  padding: 18px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  text-align: center;
}
.perm-item:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
}
.perm-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--foreground);
  margin-bottom: 4px;
}

/* ========== Drawer 样式 ========== */
.role-desc {
  font-size: 13px;
  line-height: 1.7;
  color: var(--foreground);
  background: var(--background);
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}
.drawer-toolbar {
  display: flex; gap: 8px; margin-bottom: 12px;
}
.log-pager {
  display: flex; justify-content: flex-end; margin-top: 14px;
}
</style>