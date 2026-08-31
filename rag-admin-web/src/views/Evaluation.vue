<template>
  <div class="eval-page">
    <!-- ========== 顶部控制区 ========== -->
    <div class="console-card eval-control">
      <div class="control-left">
        <h2 class="page-title">检索评估</h2>
        <span class="section-desc">对比不同检索策略的 Recall / MRR 指标</span>
      </div>
      <div class="control-right">
        <el-button :icon="Plus" @click="addCase">添加用例</el-button>
        <el-button type="primary" :loading="evaluating" :icon="VideoPlay" @click="runEvaluation">
          {{ evaluating ? '评估中...' : '开始评估' }}
        </el-button>
        <el-button :icon="Refresh" @click="reset">重置</el-button>
      </div>
    </div>

    <!-- ========== 主体：左表格 + 右报告 ========== -->
    <div class="eval-layout">
      <!-- ========== 左：表格 + 指标 ========== -->
      <div class="eval-left">
        <!-- 对比表格 -->
        <div class="console-card eval-table-card">
          <div class="table-head">
            <h3 class="card-title">测试用例对比</h3>
            <span class="section-desc font-mono">共 {{ cases.length }} 条</span>
          </div>

          <el-table :data="cases" size="default" stripe class="eval-table">
            <el-table-column prop="id" label="#" width="60">
              <template #default="{ row }">
                <span class="font-mono" style="color:var(--muted-foreground);">{{ row.id }}</span>
              </template>
            </el-table-column>
            <el-table-column label="问题" min-width="260">
              <template #default="{ row }">
                <span style="font-size:13px;">{{ row.question || '(未填写)' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="期望命中" width="180">
              <template #default="{ row }">
                <template v-if="row.expectedTag">
                  <el-tag
                    v-for="(t, i) in row.expectedTag.split(',').filter(Boolean)"
                    :key="i"
                    size="small"
                    effect="plain"
                    style="margin-right:4px;margin-bottom:2px;"
                  >{{ t }}</el-tag>
                </template>
                <span v-else style="font-size:12px;color:var(--muted-foreground);">(未设置)</span>
              </template>
            </el-table-column>
            <el-table-column label="纯向量" width="110">
              <template #default="{ row }">
                <span :class="['hit-indicator', row.vectorHit ? 'hit' : 'miss']">
                  {{ row.vectorHit ? '✓ 命中' : '✗ 漏' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="混合检索" width="110">
              <template #default="{ row }">
                <span :class="['hit-indicator', row.hybridHit ? 'hit' : 'miss']">
                  {{ row.hybridHit ? '✓ 命中' : '✗ 漏' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button size="small" link @click="openDialog(row.id)">编辑</el-button>
                <el-button size="small" link type="danger" @click="deleteCase(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 指标对比卡片 -->
        <div class="console-card metrics-card">
          <h3 class="card-title">指标对比</h3>
          <div class="metrics-grid">
            <div v-for="m in metricCards" :key="m.label" class="metric-item">
              <div class="metric-label">{{ m.label }}</div>
              <div class="metric-bars">
                <div class="metric-row">
                  <span class="metric-name">纯向量</span>
                  <div class="metric-bar-wrap">
                    <div class="metric-bar bar-vector" :style="{ width: m.vectorPct + '%' }" />
                  </div>
                  <span class="font-mono metric-val">{{ m.vectorVal }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-name">混合检索</span>
                  <div class="metric-bar-wrap">
                    <div class="metric-bar bar-hybrid" :style="{ width: m.hybridPct + '%' }" />
                  </div>
                  <span class="font-mono metric-val">{{ m.hybridVal }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========== 右：评估报告 ========== -->
      <aside class="console-card report-card">
        <h3 class="card-title">评估报告</h3>

        <!-- 汇总统计 -->
        <div class="report-stats">
          <div class="report-stat">
            <span class="report-num font-mono">{{ cases.length }}</span>
            <span class="report-lbl">测试样本</span>
          </div>
          <div class="report-stat">
            <span class="report-num font-mono" style="color:var(--success);">{{ hybridHitCount }}</span>
            <span class="report-lbl">混合命中</span>
          </div>
          <div class="report-stat">
            <span class="report-num font-mono" style="color:var(--destructive);">{{ cases.length - hybridHitCount }}</span>
            <span class="report-lbl">未命中</span>
          </div>
        </div>

        <!-- 命中对比 -->
        <div class="report-compare">
          <div class="compare-title">命中对比</div>
          <div class="compare-row">
            <span class="compare-name">纯向量</span>
            <el-progress
              :percentage="vectorHitRate"
              :stroke-width="14"
              :color="'#3a8fd6'"
              :format="() => `${vectorHitCount}/${cases.length}`"
            />
          </div>
          <div class="compare-row">
            <span class="compare-name">混合检索</span>
            <el-progress
              :percentage="hybridHitRate"
              :stroke-width="14"
              :color="'#4ab89e'"
              :format="() => `${hybridHitCount}/${cases.length}`"
            />
          </div>
        </div>

        <!-- 优化建议 -->
        <div class="report-suggestions">
          <div class="compare-title">优化建议</div>
          <div v-for="(s, i) in suggestions" :key="i" class="suggestion-item">
            <el-icon :size="14" style="flex-shrink:0;margin-top:2px;"><Warning /></el-icon>
            <span>{{ s }}</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- ========== 编辑/新增弹窗 ========== -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑测试用例' : '新增测试用例'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="测试问题">
          <el-input
            v-model="editForm.question"
            type="textarea"
            :rows="3"
            placeholder="输入你想测试的自然语言问题，比如「公司的主要业务是什么？」"
          />
        </el-form-item>
        <el-form-item label="期望命中" label-position="top">
          <el-select
            v-model="evalTags"
            multiple
            filterable
            allow-create
            clearable
            placeholder="下拉选择后端已有 tag，或直接输入新 tag 后回车"
            style="width:100%;"
          >
            <el-option
              v-for="t in availableTags"
              :key="t"
              :label="t"
              :value="t"
            />
          </el-select>
          <div class="tag-input-hint">
            命中任意一个 tag 就算召回成功。后端已有：
            <span v-if="availableTags.length">{{ availableTags.join('、') }}</span>
            <span v-else class="no-tags">（暂无，请先上传文档）</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFromDialog">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Refresh, Warning } from '@element-plus/icons-vue'
import request from '@/api/request'
import { evalCases as defaultCases, suggestions as _suggestions, type IEvalCase } from '@/data/evaluation'

const cases = ref<IEvalCase[]>([...defaultCases])
const selectedSet = ref('core')
const evaluating = ref(false)
const currentMeta = ref<{ total: number; top_k: number; vector: any; hybrid: any } | null>(null)
const availableTags = ref<string[]>([])
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const editForm = ref({ question: '', expectedTag: '' })

// 多标签管理：el-select multiple 直接绑定数组，不需要额外函数
const evalTags = ref<string[]>([])

const suggestions = _suggestions

// 计算属性
const vectorHitCount = computed(() => cases.value.filter(c => c.vectorHit).length)
const hybridHitCount = computed(() => cases.value.filter(c => c.hybridHit).length)
const vectorHitRate = computed(() => cases.value.length ? Math.round(vectorHitCount.value / cases.value.length * 100) : 0)
const hybridHitRate = computed(() => cases.value.length ? Math.round(hybridHitCount.value / cases.value.length * 100) : 0)

// 指标卡片（优先用后端真实数据）
const metricCards = computed(() => {
  const m = currentMeta.value
  if (m) {
    return [
      {
        label: `Recall@${m.top_k}`,
        vectorVal: `${m.vector.recall_at_k}%`,
        hybridVal: `${m.hybrid.recall_at_k}%`,
        vectorPct: m.vector.recall_at_k,
        hybridPct: m.hybrid.recall_at_k
      },
      {
        label: '平均召回耗时',
        vectorVal: `${m.vector.avg_cost_ms} ms`,
        hybridVal: `${m.hybrid.avg_cost_ms} ms`,
        vectorPct: Math.min(100, m.vector.avg_cost_ms / 5),
        hybridPct: Math.min(100, m.hybrid.avg_cost_ms / 5)
      },
      {
        label: '命中数',
        vectorVal: `${m.vector.hit_count}/${m.total}`,
        hybridVal: `${m.hybrid.hit_count}/${m.total}`,
        vectorPct: Math.round(m.vector.hit_count / m.total * 100),
        hybridPct: Math.round(m.hybrid.hit_count / m.total * 100)
      }
    ]
  }
  return [
    { label: 'Recall@5', vectorVal: '--', hybridVal: '--', vectorPct: 0, hybridPct: 0 },
    { label: '平均召回耗时', vectorVal: '--', hybridVal: '--', vectorPct: 0, hybridPct: 0 },
    { label: '命中数', vectorVal: '--', hybridVal: '--', vectorPct: 0, hybridPct: 0 }
  ]
})

async function runEvaluation() {
  evaluating.value = true
  try {
    const samples = cases.value.map(c => ({ question: c.question, expected_tag: c.expectedTag }))
    const res = await request.post<any, any>('/eval/run', { samples, top_k: 5 })
    currentMeta.value = res
    // 回填表格命中情况
    cases.value = cases.value.map((c, i) => ({
      ...c,
      vectorHit: res.vector.cases[i]?.recall_at_k ?? false,
      hybridHit: res.hybrid.cases[i]?.recall_at_k ?? false
    }))
    ElMessage.success(`评估完成，共 ${res.total} 条样本`)
  } catch (e: any) {
    ElMessage.error(e?.message || '评估失败')
  } finally {
    evaluating.value = false
  }
}

function reset() {
  cases.value = [...defaultCases]
  currentMeta.value = null
  evaluating.value = false
}

// 打开弹窗（编辑已有 or 新增）
function openDialog(id?: string) {
  if (id) {
    const row = cases.value.find(c => c.id === id)
    if (!row) return
    editingId.value = id
    editForm.value = { question: row.question, expectedTag: row.expectedTag }
    // 把逗号分隔的 expectedTag 拆成 evalTags 数组
    evalTags.value = row.expectedTag
      ? row.expectedTag.split(',').map(t => t.trim()).filter(Boolean)
      : []
  } else {
    editingId.value = null
    editForm.value = { question: '', expectedTag: '' }
    evalTags.value = []
  }
  dialogVisible.value = true
}

// 从弹窗保存
function saveFromDialog() {
  const q = editForm.value.question.trim()
  if (!q) {
    ElMessage.warning('问题不能为空')
    return
  }
  // evalTags 数组 → 逗号拼接存入 expectedTag
  const joinedTags = evalTags.value.join(',')
  if (editingId.value) {
    const idx = cases.value.findIndex(c => c.id === editingId.value)
    if (idx >= 0) {
      cases.value[idx] = {
        ...cases.value[idx],
        question: q,
        expectedTag: joinedTags
      }
    }
    ElMessage.success('已更新测试用例')
  } else {
    cases.value.push({
      id: 'c' + String(Date.now()).slice(-5),
      question: q,
      expectedTag: joinedTags,
      vectorHit: false,
      hybridHit: false
    })
    ElMessage.success('已新增测试用例')
  }
  dialogVisible.value = false
}

// 添加新测试用例（直接打开弹窗）
function addCase() {
  openDialog(undefined)
}

async function deleteCase(id: string) {
  const row = cases.value.find(c => c.id === id)
  if (!row) return
  try {
    await ElMessageBox.confirm(
      `确定删除这条测试用例吗？
「${row.question || '(未填写)'}」`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    cases.value = cases.value.filter(c => c.id !== id)
    if (editingRow.value === id) editingRow.value = null
    ElMessage.success('已删除')
  } catch (_e) {
    // 用户点取消，什么都不做
  }
}

// 自动适配：根据后端真实 tags 刷新 mock 用例的 expectedTag
async function autoFitToRealDocs() {
  try {
    // 优先用 eval/meta 接口拿真实 tags（如果 eval_router 已注册）
    const meta = await request.get<any, any>('/eval/meta')
    const tags: string[] = meta?.tags || []
    availableTags.value = tags

    if (tags.length > 0) {
      // 把 mock 用例的 expectedTag 循环替换成真实存在的 tag
      cases.value = cases.value.map((c, i) => ({
        ...c,
        expectedTag: tags[i % tags.length]
      }))
      ElMessage.success(`已自动适配 ${tags.length} 个真实文档标签`)
    }
  } catch (_e) {
    // eval/meta 不可用时降级：从 doc/list 间接获取 tags
    try {
      const docs = await request.get<any, any>('/doc/list')
      const docList: any[] = Array.isArray(docs) ? docs : (docs?.items || [])
      const tags = [...new Set(docList.map(d => d.tag).filter(Boolean))] as string[]
      availableTags.value = tags
      if (tags.length > 0) {
        cases.value = cases.value.map((c, i) => ({
          ...c,
          expectedTag: tags[i % tags.length]
        }))
        ElMessage.success(`已自动适配 ${tags.length} 个真实文档标签`)
      }
    } catch (_e2) { /* 还是拿不到就算了 */ }
  }
}

onMounted(async () => {
  await autoFitToRealDocs()
})
</script>

<style scoped>
/* ========== Control ========== */
.eval-control {
  padding: 16px 20px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.control-left { display: flex; align-items: baseline; gap: 10px; }
.page-title { margin: 0; font-size: 18px; font-weight: 700; }
.section-desc { font-size: 12px; color: var(--muted-foreground); }
.control-right { display: flex; gap: 10px; }

/* ========== Layout ========== */
.eval-layout {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
  height: calc(100vh - 180px);
}
.eval-left { display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }

/* ========== Table ========== */
.eval-table-card { padding: 18px; }
.table-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
}
.card-title {
  font-size: 14px; font-weight: 600; color: var(--foreground); margin: 0;
}
.eval-table th.el-table__cell {
  font-size: 11px !important;
}
.hit-indicator {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 3px;
}
.hit-indicator.hit {
  background: var(--success-bg);
  color: var(--success);
}
.hit-indicator.miss {
  background: var(--destructive-bg);
  color: var(--destructive);
}

/* ========== Metrics ========== */
.metrics-card { padding: 18px; }
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 14px;
}
.metric-item {
  background: var(--background);
  border-radius: var(--radius-md);
  padding: 14px 16px;
}
.metric-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--muted-foreground);
  margin-bottom: 10px;
}
.metric-bars { display: flex; flex-direction: column; gap: 8px; }
.metric-row {
  display: grid;
  grid-template-columns: 60px 1fr auto;
  gap: 8px;
  align-items: center;
}
.metric-name { font-size: 11px; color: var(--muted-foreground); }
.metric-bar-wrap {
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
}
.metric-bar { height: 100%; border-radius: 4px; transition: width 600ms ease; }
.bar-vector { background: #3a8fd6; }
.bar-hybrid { background: #4ab89e; }
.metric-val { font-size: 12px; font-weight: 600; color: var(--foreground); }

/* ========== Report ========== */
.report-card {
  padding: 20px 18px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.report-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 16px 0 18px;
  padding: 14px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.report-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.report-num { font-size: 22px; font-weight: 700; color: var(--foreground); }
.report-lbl { font-size: 11px; color: var(--muted-foreground); }
.report-compare { margin-bottom: 20px; }
.compare-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted-foreground);
  margin-bottom: 10px;
}
.compare-row {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}
.compare-name { font-size: 12px; color: var(--foreground); font-weight: 500; }

.report-suggestions .suggestion-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 12px;
  color: var(--foreground);
  line-height: 1.6;
  padding: 8px 10px;
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}
.report-suggestions .suggestion-item .el-icon {
  color: var(--warning);
}

/* ========== 多标签输入 ========== */
.tag-input-box {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  min-height: 40px;
}
.tag-input-box .tag-chip {
  border-radius: 4px;
}
.tag-inline-input {
  width: 140px;
  flex-shrink: 0;
}
.tag-input-hint {
  font-size: 11px;
  color: var(--muted-foreground);
  margin-top: 6px;
  line-height: 1.6;
}
.tag-input-hint .no-tags {
  color: var(--destructive);
}
</style>