<template>
  <div>
    <!-- ============ Hero 区 ============ -->
    <section class="page-hero dotted-grid-bg">
      <div class="hero-inner">
        <div class="hero-title-row">
          <h1 class="hero-title">企业知识库 RAG 问答平台</h1>
          <span class="font-mono hero-version">v1.1.0 · FastAPI + ChromaDB + BGE-Reranker</span>
        </div>
        <p class="hero-sub">
          端到端检索增强生成引擎，支持向量 / BM25 混合召回、Rerank 精排、Token 截断生成与溯源返回
        </p>

        <!-- RAG 链路渐变条 -->
        <div class="rag-pipeline-visual">
          <div class="pipeline-label-row">
            <span>文档解析</span><span>混合检索</span><span>Rerank 精排</span><span>LLM 生成</span>
          </div>
          <div class="rag-pipeline-bar">
            <div class="seg-1" /><div class="seg-2" /><div class="seg-3" /><div class="seg-4" />
          </div>
        </div>
      </div>
    </section>

    <!-- ============ KPI 指标 ============ -->
    <section class="kpi-row">
      <div v-for="k in kpiCards" :key="k.label" class="console-card kpi-card">
        <div class="kpi-head">
          <span class="kpi-label">{{ k.label }}</span>
          <span class="kpi-badge" :style="{ background: k.bg, color: k.fg }">
            <el-icon :size="14"><component :is="k.icon" /></el-icon>
          </span>
        </div>
        <div class="kpi-value font-mono">{{ k.value }}</div>
        <div class="kpi-foot" v-if="k.trend">
          <span :class="k.trend >= 0 ? 'trend-up' : 'trend-down'">
            {{ k.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(k.trend) }}
          </span>
          <span class="kpi-sub">{{ k.sub }}</span>
        </div>
      </div>
    </section>

    <!-- ============ 核心能力 ============ -->
    <section class="section">
      <div class="section-head">
        <h2 class="section-title">核心能力模块</h2>
        <span class="section-desc">四大引擎构成 RAG 链路</span>
      </div>
      <div class="capability-grid">
        <div v-for="c in capabilities" :key="c.title" class="console-card cap-card">
          <div class="cap-icon" :style="{ background: c.accent + '18', color: c.accent }">
            <el-icon :size="22"><component :is="c.icon" /></el-icon>
          </div>
          <h3 class="cap-title">{{ c.title }}</h3>
          <p class="cap-desc">{{ c.description }}</p>
        </div>
      </div>
    </section>

    <!-- ============ 下半部分：技术栈 + 快速操作 ============ -->
    <section class="bottom-grid">
      <!-- 技术栈 -->
      <div class="console-card bottom-card">
        <div class="bottom-head">
          <h3 class="bottom-title">技术栈</h3>
          <span class="section-desc">{{ techStack.length }} 项</span>
        </div>
        <div class="tech-tags">
          <span v-for="t in techStack" :key="t" class="tech-tag font-mono">{{ t }}</span>
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="console-card bottom-card">
        <div class="bottom-head">
          <h3 class="bottom-title">快速操作</h3>
          <span class="section-desc">跳转到对应功能</span>
        </div>
        <div class="quick-actions">
          <router-link to="/documents" class="console-card action-card">
            <el-icon :size="20" color="#0066cc"><UploadFilled /></el-icon>
            <span>上传文档</span>
          </router-link>
          <router-link to="/qa" class="console-card action-card">
            <el-icon :size="20" color="#0066cc"><ChatDotRound /></el-icon>
            <span>测试问答</span>
          </router-link>
          <router-link to="/evaluation" class="console-card action-card">
            <el-icon :size="20" color="#0066cc"><DataAnalysis /></el-icon>
            <span>检索评估</span>
          </router-link>
          <el-button text class="console-card action-card action-open" @click="showApiDoc = true">
            <el-icon :size="20" color="#0066cc"><Document /></el-icon>
            <span>API 文档</span>
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { kpiData, capabilities, techStack } from '@/data/overview'

const router = useRouter()
const showApiDoc = ref(false)

// 动态 KPI 状态（后端 /api/stats 会覆盖 docCount / chunkCount）
const kpiState = reactive({
  docCount: kpiData.docCount,
  chunkCount: kpiData.chunkCount
})

onMounted(async () => {
  try {
    const resp = await fetch('/api/stats')
    if (resp.ok) {
      const data = await resp.json()
      const s = data.data || data
      if (typeof s.doc_count === 'number') kpiState.docCount = s.doc_count
      if (typeof s.chunk_count === 'number') kpiState.chunkCount = s.chunk_count
    }
  } catch {
    // 后端没启动，用 mock
  }
})

// KPI 卡片配置（computed 包装，value 为普通字符串）
const kpiCards = computed(() => [
  {
    label: '知识库文档数',
    value: String(kpiState.docCount),
    trend: 12,
    sub: '较上周',
    icon: 'Document',
    bg: '#0066cc',
    fg: '#ffffff'
  },
  {
    label: '向量分片数量',
    value: kpiState.chunkCount.toLocaleString(),
    trend: 8,
    sub: '本周新增',
    icon: 'Files',
    bg: '#4ab89e',
    fg: '#ffffff'
  },
  {
    label: 'Recall@5 (混合检索)',
    value: kpiData.recallAt5.toFixed(1) + '%',
    trend: 2.3,
    sub: '较纯向量',
    icon: 'Aim',
    bg: '#a85c18',
    fg: '#ffffff'
  }
])
</script>

<style scoped>
/* ============ Hero ============ */
.page-hero {
  border-radius: var(--radius-md);
  background: var(--card);
  border: 1px solid var(--border);
  margin-bottom: 20px;
  padding: 28px 32px;
  position: relative;
  overflow: hidden;
}
.hero-title-row {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 10px;
}
.hero-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--foreground);
  margin: 0;
  letter-spacing: -0.01em;
}
.hero-version {
  font-size: 12px;
  color: var(--muted-foreground);
  background: var(--accent);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}
.hero-sub {
  font-size: 14px;
  color: var(--muted-foreground);
  margin: 0 0 20px;
  line-height: 1.6;
  max-width: 640px;
}
.rag-pipeline-visual {
  max-width: 520px;
}
.pipeline-label-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 11px;
  color: var(--muted-foreground);
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* ============ KPI ============ */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.kpi-card {
  padding: 20px 22px;
}
.kpi-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.kpi-label {
  font-size: 13px;
  color: var(--muted-foreground);
  font-weight: 500;
}
.kpi-badge {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}
.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--foreground);
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.kpi-foot {
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted-foreground);
  display: flex;
  gap: 6px;
  align-items: center;
}
.trend-up { color: var(--success); font-weight: 600; }
.trend-down { color: var(--destructive); font-weight: 600; }

/* ============ 能力 ============ */
.section { margin-bottom: 28px; }
.section-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 14px;
}
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--foreground);
  margin: 0;
}
.section-desc {
  font-size: 12px;
  color: var(--muted-foreground);
}
.capability-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.cap-card {
  padding: 18px 20px;
  min-height: 132px;
}
.cap-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.cap-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--foreground);
  margin: 0 0 6px;
}
.cap-desc {
  font-size: 12px;
  color: var(--muted-foreground);
  margin: 0;
  line-height: 1.6;
}

/* ============ 底部双栏 ============ */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.bottom-card { padding: 20px 22px; }
.bottom-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 14px;
}
.bottom-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--foreground);
  margin: 0;
}
.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.tech-tag {
  font-size: 11px;
  background: var(--accent);
  color: var(--accent-foreground);
  padding: 3px 10px;
  border-radius: 9999px;
  font-weight: 500;
}
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.action-card {
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  font-size: 12px;
  color: var(--muted-foreground);
  cursor: pointer;
  border: 1px solid var(--border);
}
.action-card:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.action-open { background: none; }
</style>