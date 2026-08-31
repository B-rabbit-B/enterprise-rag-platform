<template>
  <div class="doc-page">
    <!-- ========== 顶部工具条 ========== -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <h2 class="page-title">文档管理</h2>
        <span class="page-sub font-mono">{{ filteredDocs.length }} / {{ allDocs.length }} 篇</span>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文档名..."
          :prefix-icon="Search"
          clearable
          style="width: 220px;"
          size="default"
          @keyup.enter="searchKeyword = $event.target.value"
        />
        <el-button type="primary" :icon="UploadFilled" @click="showUpload = true">上传文档</el-button>
      </div>
    </div>

    <!-- ========== 三栏主体 ========== -->
    <div class="doc-layout">
      <!-- ========== 左栏：分类筛选 ========== -->
      <aside class="console-card filter-panel">
        <h3 class="panel-title">分类</h3>
        <div v-if="categories.length <= 1" style="font-size:12px;color:var(--muted-foreground);padding:4px;">
          暂无分类（上传文档时设置 tag）
        </div>
        <div v-else class="filter-tree">
          <div
            v-for="cat in categories"
            :key="cat"
            class="filter-item"
            :class="{ active: activeCategory === cat }"
            @click="activeCategory = cat"
          >
            <span>{{ cat }}</span>
            <span class="font-mono filter-count">{{ getCategoryCount(cat) }}</span>
          </div>
        </div>

        <h3 class="panel-title" style="margin-top:24px;">状态</h3>
        <div class="filter-tags">
          <el-tag
            size="small"
            :type="activeStatus === 'all' ? '' : activeStatus === 'success' ? 'success' : activeStatus === 'parsing' ? 'info' : 'danger'"
            :effect="activeStatus === 'all' ? 'dark' : 'plain'"
            class="filter-tag"
            @click="activeStatus = 'all'"
          >全部</el-tag>
          <el-tag
            size="small"
            effect="plain"
            class="filter-tag"
            :class="{ filterTagActive: activeStatus === 'success' }"
            @click="activeStatus = 'success'"
          >✅ 已解析</el-tag>
          <el-tag
            size="small"
            effect="plain"
            class="filter-tag"
            :class="{ filterTagActive: activeStatus === 'parsing' }"
            @click="activeStatus = 'parsing'"
          >⏳ 解析中</el-tag>
          <el-tag
            size="small"
            effect="plain"
            class="filter-tag"
            :class="{ filterTagActive: activeStatus === 'failed' }"
            @click="activeStatus = 'failed'"
          >❌ 失败</el-tag>
        </div>
      </aside>

      <!-- ========== 中栏：文档列表 ========== -->
      <section class="doc-list-panel">
        <div v-if="!filteredDocs.length" class="empty-state">
          <el-icon :size="48" color="var(--border)"><Document /></el-icon>
          <p style="margin-top:12px;color:var(--muted-foreground);">没有匹配的文档</p>
        </div>

        <div v-for="doc in filteredDocs" :key="doc.id"
             class="console-card doc-card"
             :class="{ selected: selectedDoc?.id === doc.id }"
             @click="selectDoc(doc)">
          <div class="doc-card-head">
            <div class="doc-name-row">
              <span class="doc-type-badge font-mono">{{ doc.file_type?.toUpperCase() }}</span>
              <span class="doc-name">{{ doc.filename }}</span>
            </div>
            <span :class="['status-badge', `status-${doc.parse_status}`]">
              <span class="dot" />
              {{ statusLabel(doc.parse_status) }}
            </span>
          </div>

          <div class="doc-card-meta">
            <span class="font-mono meta-item">ID: {{ doc.id }}</span>
            <span class="meta-item">· {{ doc.upload_time?.replace('T', ' ').slice(0, 19) }}</span>
          </div>

          <div class="doc-card-tags">
            <template v-if="doc.tag">
              <el-tag v-for="(t, i) in doc.tag.split(',').filter(Boolean)" :key="i"
                      size="small" class="doc-tag">{{ t }}</el-tag>
            </template>
            <el-tag size="small" effect="plain" style="margin-left:auto;color:var(--muted-foreground);">
              <span class="font-mono">{{ doc.chunk_count }}</span> 分片
            </el-tag>
          </div>

          <div class="doc-card-actions">
            <el-button text size="small" class="act-btn" @click.stop="reparse(doc)">
              <el-icon><Refresh /></el-icon> 刷新状态
            </el-button>
            <el-popconfirm
              title="确定删除？向量分片将一并清除。"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm.stop="removeDoc(doc)"
            >
              <template #reference>
                <el-button text size="small" class="act-btn act-danger">
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </section>

      <!-- ========== 右栏：分片预览 ========== -->
      <aside class="console-card chunk-panel">
        <div v-if="!selectedDoc" class="empty-state">
          <el-icon :size="40" color="var(--border)"><View /></el-icon>
          <p style="margin-top:12px;color:var(--muted-foreground);">请选择文档查看分片详情</p>
        </div>

        <template v-else>
          <div class="chunk-header">
            <h3 class="panel-title" style="margin:0;">{{ selectedDoc.filename }}</h3>
            <span class="font-mono" style="color:var(--muted-foreground);font-size:12px;">
              {{ chunks.length }} 个分片预览
            </span>
          </div>

          <!-- 解析状态条 -->
          <div class="chunk-status-bar">
            <span class="chunk-status-label">解析进度</span>
            <el-progress
              :percentage="selectedDoc.parse_status === 'success' ? 100 : 30"
              :color="selectedDoc.parse_status === 'success' ? 'var(--success)' : 'var(--primary)'"
              :show-text="false"
              style="flex:1;margin:0 12px;"
            />
            <span class="font-mono" style="font-size:12px;color:var(--muted-foreground);">
              {{ statusLabel(selectedDoc.parse_status) }}
            </span>
          </div>

          <!-- 分片列表 -->
          <div v-if="chunkLoading" class="chunk-list">
            <div v-for="i in 3" :key="i" class="console-card chunk-item">
              <div class="chunk-item-head">
                <div class="sk-line sk-title" style="width:30px;height:14px;" />
                <div class="sk-line sk-title" style="width:60px;height:12px;margin-left:auto;" />
              </div>
              <div class="sk-line" style="width:100%;margin-top:8px;" />
              <div class="sk-line" style="width:85%;margin-top:6px;" />
              <div class="sk-line sk-short" style="margin-top:6px;" />
            </div>
          </div>
          <div v-else-if="chunks.length" class="chunk-list">
            <div v-for="c in chunks" :key="c.chunk_id || c.index" class="console-card chunk-item">
              <div class="chunk-item-head">
                <span class="chunk-index font-mono">#{{ c.index }}</span>
                <span class="font-mono chunk-charcount">{{ c.char_count ?? c.charCount ?? 0 }} 字</span>
              </div>
              <div class="chunk-content">{{ c.content }}</div>
            </div>
          </div>
          <div v-else class="empty-state" style="padding:40px 20px;">
            <p style="color:var(--muted-foreground);font-size:12px;">该文档暂无分片（向量库可能为空）</p>
          </div>
        </template>
      </aside>
    </div>

    <!-- ========== 上传 Dialog ========== -->
    <el-dialog v-model="showUpload" title="上传文档" width="480px" :close-on-click-modal="false">
      <el-upload
        :show-file-list="false"
        :on-change="onFileChange"
        :auto-upload="false"
        accept=".pdf,.txt,.md"
        drag
        multiple
        ref="uploadRef"
      >
        <el-icon :size="40" color="var(--border)"><UploadFilled /></el-icon>
        <div style="margin-top:10px;color:var(--muted-foreground);font-size:13px;">拖拽或点击选择文件（支持多选）</div>
        <div style="margin-top:4px;font-size:11px;color:var(--muted-foreground);">支持 PDF / TXT / MD，单个 ≤ 50MB</div>
      </el-upload>

      <!-- 选中文件预览（多文件列表） -->
      <div v-if="pendingFiles.length" class="selected-files-list">
        <div v-for="(f, idx) in pendingFiles" :key="idx" class="selected-file-card">
          <el-icon :size="18" color="var(--primary)"><Document /></el-icon>
          <div class="selected-file-info">
            <span class="selected-file-name">{{ f.name }}</span>
            <span class="selected-file-size font-mono">({{ (f.size / 1024).toFixed(1) }} KB)</span>
          </div>
          <el-icon class="selected-file-clear" :size="18" @click="removePendingFile(idx)"><Close /></el-icon>
        </div>
        <div class="selected-files-actions">
          <span class="font-mono" style="font-size:11px;color:var(--muted-foreground);">共 {{ pendingFiles.length }} 个文件</span>
          <el-button size="small" text @click="pendingFiles = []">全部清除</el-button>
        </div>
      </div>

      <div style="margin-top:14px;">
        <div class="tag-input-wrap">
          <span class="tag-input-label">标签</span>
          <div class="tag-input-box">
            <el-tag v-for="(t, i) in uploadTags" :key="i" closable class="tag-chip" @close="removeUploadTag(i)">{{ t }}</el-tag>
            <el-input
              v-if="tagInputVisible"
              v-model="tagInputValue"
              size="small"
              class="tag-inline-input"
              ref="tagInputRef"
              @keyup.enter="commitTag"
              @blur="commitTag"
              placeholder="回车添加"
            />
            <el-button v-else size="small" text :icon="Plus" @click="showTagInput">+ 添加</el-button>
          </div>
          <span class="tag-input-hint font-mono">可添加多个标签，用逗号或回车分隔</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">
          {{ uploading ? '正在解析...' : '确认上传' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, type UploadUserFile, type UploadInstance } from 'element-plus'
import { UploadFilled, Search, Refresh, Delete, View, Document, Close, Plus } from '@element-plus/icons-vue'
import type { Ref } from 'vue'
import request from '@/api/request'

// ========== 后端接口类型 ==========
interface DocItem {
  id: number
  filename: string
  file_type: string
  tag: string
  preview: string
  upload_time: string
  uploader_id: number
  chunk_count: number
  parse_status: 'success' | 'pending'
}

interface ChunkSim {
  chunk_id?: string
  index: number
  content: string
  char_count?: number
  charCount?: number
}

// 后端 /chunks 返回的分片类型
interface DocChunk {
  chunk_id: string
  index: number
  content: string
  char_count: number
}

// ========== 状态 ==========
const docList = ref<DocItem[]>([])
const chunks = ref<ChunkSim[]>([])
const chunkLoading = ref(false)
const loadingList = ref(false)

// 筛选状态
const activeCategory = ref('全部')
const activeStatus = ref<'all' | 'success' | 'parsing' | 'failed'>('all')
const searchKeyword = ref('')

// 选中
const selectedDoc = ref<DocItem | null>(null)

// 上传
const tagInputRef = ref<HTMLInputElement | null>(null)
const showUpload = ref(false)
const uploading = ref(false)
const uploadRef = ref<UploadInstance>()
const pendingFiles = ref<File[]>([])

// 多标签管理
const uploadTags = ref<string[]>([])
const tagInputVisible = ref(false)
const tagInputValue = ref('')

function showTagInput() {
  tagInputVisible.value = true
  // 等 DOM 渲染后 focus
  setTimeout(() => tagInputRef.value?.focus?.(), 0)
}
function commitTag() {
  const val = tagInputValue.value.trim()
  if (val) {
    // 支持一次输多个用逗号/空格分隔
    val.split(/[,，\s]+/).forEach(t => {
      const v = t.trim()
      if (v && !uploadTags.value.includes(v)) {
        if (uploadTags.value.length < 10) uploadTags.value.push(v)
      }
    })
  }
  tagInputValue.value = ''
  tagInputVisible.value = false
}
function removeUploadTag(i: number) { uploadTags.value.splice(i, 1) }

// 从后端数据动态提取分类
const categories = computed(() => {
  const set = new Set<string>(['全部'])
  docList.value.forEach(d => {
    if (d.tag) d.tag.split(',').forEach(t => t && set.add(t))
  })
  return Array.from(set)
})
const allDocs = docList

// 过滤后的文档
const filteredDocs = computed(() => {
  let list = [...docList.value]
  if (activeCategory.value !== '全部') {
    list = list.filter(d => d.tag && d.tag.split(',').includes(activeCategory.value))
  }
  if (activeStatus.value !== 'all') {
    list = list.filter(d => d.parse_status === activeStatus.value)
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(d => d.filename.toLowerCase().includes(kw))
  }
  return list
})

function getCategoryCount(cat: string): number {
  if (cat === '全部') return docList.value.length
  return docList.value.filter(d => d.tag === cat).length
}

function statusLabel(s: string): string {
  return s === 'success' ? '已解析' : s === 'pending' ? '解析中' : s
}

async function selectDoc(doc: DocItem) {
  selectedDoc.value = doc
  chunkLoading.value = true
  chunks.value = []
  try {
    const res = await request.get<{ doc_id: number; total: number; items: DocChunk[] }>(`/doc/${doc.id}/chunks`)
    chunks.value = res.items.map((c, i) => ({
      chunk_id: c.chunk_id,
      index: c.index || i + 1,
      content: c.content,
      char_count: c.char_count,
      charCount: c.char_count,
    }))
  } catch (_e) {
    chunks.value = []
  } finally {
    chunkLoading.value = false
  }
}

async function reparse(doc: DocItem) {
  try {
    const res = await request.post<{ doc_id: number; chunk_count: number }>(`/doc/${doc.id}/reparse`)
    // 更新本地文档的分片数
    const target = docList.value.find(d => d.id === doc.id)
    if (target) {
      target.chunk_count = res.chunk_count
      target.parse_status = 'success'
    }
    ElMessage.success(`「${doc.filename}」重新解析完成，生成 ${res.chunk_count} 个分片`)
    // 如果当前选中的就是它，也刷新一下
    if (selectedDoc.value?.id === doc.id) {
      selectedDoc.value = { ...target! }
    }
  } catch (_e) {
    // 拦截器已弹错
  }
}

async function removeDoc(doc: DocItem) {
  try {
    await request.delete(`/doc/${doc.id}`)
    ElMessage.success(`「${doc.filename}」已删除`)
    if (selectedDoc.value?.id === doc.id) {
      selectedDoc.value = null
      chunks.value = []
    }
    await loadList()
  } catch (_e) { /* request 拦截器已提示 */ }
}

// ========== 核心：拉取后端 ==========
const route = useRoute()

async function loadList() {
  loadingList.value = true
  try {
    docList.value = await request.get<DocItem[]>('/doc/list')
  } catch (_e) {
    docList.value = []
  } finally {
    loadingList.value = false
  }
}

onMounted(async () => {
  await loadList()
  // 如果从问答页跳转过来带了 highlight 参数，自动选中对应文档
  const highlight = route.query.highlight as string
  if (highlight) {
    const target = docList.value.find(d => d.filename === highlight)
    if (target) {
      await selectDoc(target)
      // 左侧列表滚动到可视区域
      setTimeout(() => {
        const el = document.querySelector(`.doc-list-item[data-id="${target.id}"]`) as HTMLElement
        el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 100)
    }
  }
})

function onFileChange(file: any, files: any[]) {
  // Element-Plus multiple 时，每次选文件触发：file 是最新一个，files 是全量列表
  if (files && files.length) {
    // 只取原生 File 对象，去重（按 name+size）
    const rawFiles = files.map(f => f.raw).filter(Boolean) as File[]
    const seen = new Set<string>()
    pendingFiles.value = rawFiles.filter(f => {
      const key = `${f.name}-${f.size}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  }
}

function removePendingFile(idx: number) {
  pendingFiles.value.splice(idx, 1)
}

async function submitUpload() {
  if (!pendingFiles.value.length) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  let successCount = 0
  let failCount = 0
  const newDocs: DocItem[] = []

  for (const file of pendingFiles.value) {
    try {
      const fd = new FormData()
      fd.append('file', file)
    if (uploadTags.value.length) fd.append('tag', uploadTags.value.join(','))

      const result = await request.post<any>('/doc/upload', fd)
      newDocs.unshift({
        id: result.id,
        filename: result.filename,
        file_type: result.file_type,
        tag: result.tag || '',
        preview: result.preview || '',
        upload_time: result.upload_time || new Date().toISOString(),
        uploader_id: result.uploader_id || 0,
        chunk_count: result.chunk_count || 0,
        parse_status: 'success'
      })
      successCount++
    } catch (_e) {
      failCount++
    }
  }

  // 一次性插入成功的文档
  if (newDocs.length) {
    docList.value = [...newDocs, ...docList.value]
  }

  uploading.value = false
  showUpload.value = false
  pendingFiles.value = []
  uploadTags.value = []

  if (failCount === 0) {
    ElMessage.success(`全部上传成功（${successCount} 个文件）`)
  } else if (successCount === 0) {
    ElMessage.error(`全部失败（${failCount} 个）`)
  } else {
    ElMessage.warning(`部分成功：${successCount} ✓ / ${failCount} ✗`)
  }
}
</script>

<style scoped>
/* ========== Toolbar ========== */
.page-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar-left { display: flex; align-items: baseline; gap: 10px; }
.page-title { margin: 0; font-size: 18px; font-weight: 700; color: var(--foreground); }
.page-sub { color: var(--muted-foreground); font-size: 12px; }
.toolbar-right { display: flex; gap: 10px; }

/* ========== 三栏布局 ========== */
.doc-layout {
  display: grid;
  grid-template-columns: 200px 1fr 380px;
  gap: 16px;
  height: calc(100vh - 140px);
}

/* ========== 左栏：筛选 ========== */
.filter-panel { padding: 18px 16px; overflow-y: auto; }
.panel-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted-foreground);
  margin: 0 0 10px;
}
.filter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--foreground);
  cursor: pointer;
  margin-bottom: 2px;
  transition: all 150ms ease;
}
.filter-item:hover { background: var(--accent); }
.filter-item.active { background: var(--accent); color: var(--primary); font-weight: 500; }
.filter-count {
  font-size: 11px;
  color: var(--muted-foreground);
  padding: 1px 6px;
  background: var(--accent);
  border-radius: 3px;
}
.filter-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.filter-tag { cursor: pointer; }
.filterTagActive { outline: 1px solid var(--primary); }

/* ========== 中栏：文档列表 ========== */
.doc-list-panel {
  overflow-y: auto;
  padding: 2px;
}
.doc-list-panel::-webkit-scrollbar { width: 6px; }

.doc-card {
  padding: 16px 18px;
  margin-bottom: 12px;
  cursor: pointer;
}
.doc-card.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15), var(--shadow-md);
}
.doc-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.doc-name-row { display: flex; align-items: center; gap: 10px; min-width: 0; }
.doc-type-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 2px 6px;
  border-radius: 3px;
  background: var(--accent);
  color: var(--accent-foreground);
  flex-shrink: 0;
}
.doc-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--foreground);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-card-meta {
  margin-top: 8px;
  font-size: 11px;
  color: var(--muted-foreground);
}
.meta-item { margin-right: 4px; }
.doc-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
  align-items: center;
}
.doc-tag { font-size: 11px; }
.doc-card-actions {
  margin-top: 10px;
  display: flex;
  gap: 4px;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}
.act-btn { font-size: 12px; color: var(--muted-foreground) !important; }
.act-btn:hover { color: var(--primary) !important; }
.act-danger:hover { color: var(--destructive) !important; }

/* ========== Skeleton ========== */
.sk-line {
  height: 12px;
  background: var(--border);
  border-radius: 3px;
  width: 100%;
  animation: sk-pulse 1.4s ease-in-out infinite;
}
.sk-line.sk-short { width: 50%; }
.sk-line.sk-title { background: var(--border); }
@keyframes sk-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ========== 右栏：分片预览 ========== */
.chunk-panel { padding: 18px 16px; overflow-y: auto; }
.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.chunk-status-bar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: var(--background);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}
.chunk-status-label {
  font-size: 12px;
  color: var(--muted-foreground);
  font-weight: 500;
}
.chunk-list { display: flex; flex-direction: column; gap: 8px; }
.chunk-item {
  padding: 12px 14px;
}
.chunk-item-head {
  display: flex;
  gap: 10px;
  font-size: 11px;
  margin-bottom: 6px;
  color: var(--muted-foreground);
}
.chunk-index {
  color: var(--primary);
  font-weight: 600;
}
.chunk-content {
  font-size: 12px;
  color: var(--foreground);
  line-height: 1.6;
  background: var(--background);
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--primary);
  max-height: 120px;
  overflow-y: auto;
}

/* ========== 多标签输入 ========== */
.tag-input-wrap { display: flex; flex-direction: column; gap: 8px; }
.tag-input-label { font-size: 12px; font-weight: 500; color: var(--foreground); }
.tag-input-box {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding: 8px 10px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  min-height: 36px;
}
.tag-chip { flex-shrink: 0; }
.tag-inline-input {
  width: 120px; flex-shrink: 0;
}
.tag-input-hint { font-size: 11px; color: var(--muted-foreground); }

/* ========== 上传 Dialog 内部 ========== */
.selected-file-card {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  padding: 10px 14px;
  background: var(--accent);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}
.selected-file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 8px;
  align-items: center;
}
.selected-file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--foreground);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.selected-file-size {
  font-size: 11px;
  color: var(--muted-foreground);
  flex-shrink: 0;
}
.selected-file-clear {
  cursor: pointer;
  color: var(--muted-foreground);
  flex-shrink: 0;
  transition: color 150ms;
}
.selected-file-clear:hover { color: var(--destructive); }

/* ========== 空状态 ========== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>