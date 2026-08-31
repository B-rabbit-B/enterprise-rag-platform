<template>
  <div class="app-shell">
    <!-- ========== 左侧 Sidebar ========== -->
    <aside class="app-sidebar">
      <!-- Logo + 品牌 -->
      <div class="sidebar-brand">
        <div class="brand-icon">
          <el-icon :size="20"><Reading /></el-icon>
        </div>
        <div class="brand-text">
          <div class="brand-title">RAG Console</div>
          <div class="brand-sub">企业知识库问答平台</div>
        </div>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 底部版本信息 -->
      <div class="sidebar-footer">
        <div class="footer-version">
          <span class="font-mono">v1.1.0</span>
          <span class="status-badge status-running" style="margin-left:8px;">
            <span class="dot" />运行中
          </span>
        </div>
      </div>
    </aside>

    <!-- ========== 右侧主体 ========== -->
    <div class="app-main-wrapper">
      <!-- Topbar -->
      <header class="app-topbar">
        <!-- 面包屑/页面标题 -->
        <div class="topbar-left">
          <span class="topbar-title">{{ currentTitle }}</span>
        </div>

        <!-- 右侧信息区 -->
        <div class="topbar-right">
          <!-- API 文档按钮 -->
          <el-button text class="topbar-btn" @click="showApiDoc = true">
            <el-icon><Document /></el-icon>
            <span style="margin-left:4px;">API 文档</span>
          </el-button>

          <!-- 环境标签 -->
          <span class="env-tag font-mono">dev</span>

          <!-- 状态指示灯 -->
          <span class="status-indicator">
            <span class="indicator-dot indicator-online" />
            <span class="font-mono">服务运行中</span>
          </span>

          <!-- 分隔线 -->
          <span class="topbar-divider" />

          <!-- 用户区 -->
          <template v-if="userStore.isLoggedIn()">
            <div class="user-info">
              <el-tag v-if="userStore.isAdmin" size="small" effect="dark" style="margin-right:6px;">ADMIN</el-tag>
              <el-icon style="vertical-align:-2px;"><User /></el-icon>
              <span class="username">{{ userStore.username }}</span>
            </div>
            <el-button text size="small" @click="handleLogout">
              <el-icon><Switch /></el-icon>
            </el-button>
          </template>
          <template v-else>
            <el-button type="primary" size="small" plain @click="showLogin = true">
              登录
            </el-button>
          </template>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>

  <!-- ========== API 文档抽屉 ========== -->
  <el-drawer
    v-model="showApiDoc"
    title="API 接口文档"
    size="560px"
    class="api-drawer"
  >
    <div v-for="group in apiGroups" :key="group.name" class="api-group">
      <div class="api-group-title">
        <span>{{ group.name }}</span>
        <span class="api-group-desc">{{ group.description }}</span>
      </div>
      <div
        v-for="ep in group.endpoints"
        :key="ep.path"
        class="api-endpoint console-card"
      >
        <div class="endpoint-head">
          <span class="method-tag" :class="`method-${ep.method.toLowerCase()}`">{{ ep.method }}</span>
          <span class="font-mono endpoint-path">{{ ep.path }}</span>
        </div>
        <div class="endpoint-desc">{{ ep.description }}</div>
        <div v-if="ep.params" class="endpoint-params">
          <span class="params-label">参数：</span>
          <span v-for="p in ep.params" :key="p" class="params-item font-mono">{{ p }}</span>
        </div>
      </div>
    </div>
  </el-drawer>

  <!-- ========== 登录弹窗 ========== -->
  <el-dialog v-model="showLogin" title="登录" width="380px" :close-on-click-modal="false">
    <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="60px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="loginForm.username" placeholder="请输入用户名" autocomplete="username" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password autocomplete="current-password" @keyup.enter="doLogin" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div style="flex:1;display:flex;justify-content:space-between;align-items:center;">
        <el-link type="primary" :underline="false" @click="switchToRegister">没有账号？去注册</el-link>
        <div>
          <el-button @click="showLogin = false">取消</el-button>
          <el-button type="primary" :loading="loginLoading" @click="doLogin">登录</el-button>
        </div>
      </div>
    </template>
  </el-dialog>

  <!-- ========== 注册弹窗 ========== -->
  <el-dialog v-model="showRegister" title="注册新用户" width="380px" :close-on-click-modal="false">
    <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-width="80px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="registerForm.username" placeholder="2-50 字符" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="registerForm.password" type="password" placeholder="至少 6 位" show-password />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm">
        <el-input v-model="registerForm.confirm" type="password" placeholder="再次输入密码" show-password @keyup.enter="doRegister" />
      </el-form-item>
      <el-form-item label="管理员">
        <el-switch v-model="registerForm.is_admin" />
        <span style="font-size:12px;color:var(--muted-foreground);margin-left:8px;">勾选则注册为管理员</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <div style="flex:1;display:flex;justify-content:space-between;align-items:center;">
        <el-link type="primary" :underline="false" @click="switchToLogin">已有账号？去登录</el-link>
        <div>
          <el-button @click="showRegister = false">取消</el-button>
          <el-button type="primary" :loading="registerLoading" @click="doRegister">注册</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { loginApi, getMeApi, registerApi } from '@/api/user'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { apiGroups } from '@/data/apiDocs'

const userStore = useUserStore()
const route = useRoute()

// 导航配置（Sidebar + 标题）
const navItems = [
  { path: '/dashboard',   label: '总览',      icon: 'DataBoard' },
  { path: '/documents',   label: '文档管理',  icon: 'Document' },
  { path: '/qa',          label: '知识库问答',icon: 'ChatDotRound' },
  { path: '/evaluation',  label: '检索评估',  icon: 'DataAnalysis' },
  { path: '/settings',    label: '系统设置',  icon: 'Setting' }
]

const currentTitle = computed(() => {
  const m = route.meta as { title?: string }
  return m?.title || 'RAG 控制台'
})

// API 文档抽屉
const showApiDoc = ref(false)

// 登录弹窗相关
const showLogin = ref(false)
const loginLoading = ref(false)
const loginFormRef = ref<FormInstance>()
const loginForm = ref({ username: 'admin', password: 'admin123456' })
const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册弹窗相关
const showRegister = ref(false)
const registerLoading = ref(false)
const registerFormRef = ref<FormInstance>()
const registerForm = ref({ username: '', password: '', confirm: '', is_admin: false })
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '2-50 字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '至少 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== registerForm.value.password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

function switchToRegister() {
  showLogin.value = false
  showRegister.value = true
}
function switchToLogin() {
  showRegister.value = false
  showLogin.value = true
}

async function doRegister() {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    registerLoading.value = true
    try {
      await registerApi({
        username: registerForm.value.username,
        password: registerForm.value.password,
        is_admin: registerForm.value.is_admin
      })
      ElMessage.success('注册成功，请登录')
      registerForm.value = { username: '', password: '', confirm: '', is_admin: false }
      registerFormRef.value.resetFields()
      switchToLogin()
    } catch (_e) {
      // request 拦截器已经弹过错误提示
    } finally {
      registerLoading.value = false
    }
  })
}

async function doLogin() {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loginLoading.value = true
    try {
      // 1. 调用登录接口拿 token
      const res = await loginApi(loginForm.value)
      // 2. 先把 token 存好（登录就算成功了）
      userStore.setToken(res.access_token, { username: '', is_admin: false })
      // 3. 尝试获取用户信息（失败也不影响登录状态）
      try {
        const me = await getMeApi()
        userStore.setToken(res.access_token, { username: me.username, is_admin: me.is_admin })
        ElMessage.success(`欢迎回来，${me.username}`)
      } catch (_e) {
        ElMessage.success('登录成功')
      }
      showLogin.value = false
    } catch (_err) {
      // loginApi 本身失败（密码错/用户名不存在），request 拦截器已经弹过错误提示
      // 这里什么都不做，等用户重新输入
    } finally {
      loginLoading.value = false
    }
  })
}

function handleLogout() {
  userStore.clearToken()
  ElMessage.success('已退出登录')
}

// 全局监听"需要登录"事件（路由守卫和 401 都会触发）
function onNeedLogin() {
  showLogin.value = true
}

onMounted(() => {
  window.addEventListener('need-login', onNeedLogin)
})
onUnmounted(() => {
  window.removeEventListener('need-login', onNeedLogin)
})
</script>

<style scoped>
/* ============ App Shell 布局 ============ */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ============ Sidebar ============ */
.app-sidebar {
  width: 232px;
  background: var(--card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--border);
}
.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.brand-title {
  font-weight: 700;
  font-size: 15px;
  color: var(--foreground);
  letter-spacing: -0.01em;
}
.brand-sub {
  font-size: 11px;
  color: var(--muted-foreground);
  margin-top: 2px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  color: var(--muted-foreground);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  margin-bottom: 2px;
  transition: all 150ms ease;
}
.nav-item:hover {
  background: var(--accent);
  color: var(--accent-foreground);
}
.nav-item.active {
  background: var(--accent);
  color: var(--primary);
  font-weight: 600;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
}
.footer-version {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--muted-foreground);
}

/* ============ Main Wrapper ============ */
.app-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ============ Topbar ============ */
.app-topbar {
  height: 56px;
  background: var(--card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}
.topbar-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--foreground);
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.topbar-btn {
  color: var(--muted-foreground) !important;
  font-size: 13px !important;
}
.topbar-btn:hover {
  color: var(--primary) !important;
}
.env-tag {
  padding: 2px 8px;
  background: var(--warning-bg);
  color: var(--warning);
  border: 1px solid var(--warning-border);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 500;
}
.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--muted-foreground);
}
.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.indicator-online {
  background: var(--success);
  box-shadow: 0 0 0 3px var(--success-bg);
}
.topbar-divider {
  width: 1px;
  height: 18px;
  background: var(--border);
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.username {
  color: var(--foreground);
  font-weight: 500;
}

/* ============ Content ============ */
.app-content {
  flex: 1;
  background: var(--background);
  padding: 20px 24px;
  overflow-y: auto;
}

/* ============ API 文档 ============ */
.api-group {
  margin-bottom: 24px;
}
.api-group-title {
  margin-bottom: 10px;
}
.api-group-title span:first-child {
  font-weight: 600;
  font-size: 14px;
  color: var(--foreground);
}
.api-group-desc {
  display: block;
  font-size: 12px;
  color: var(--muted-foreground);
  margin-top: 2px;
}
.api-endpoint {
  padding: 12px 14px;
  margin-bottom: 8px;
}
.endpoint-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.method-tag {
  padding: 2px 7px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.method-get    { background: #2f855a; }
.method-post   { background: #2b6cb0; }
.method-put    { background: #9b59b6; }
.method-delete { background: #c53030; }
.endpoint-path {
  font-size: 13px;
  color: var(--foreground);
  font-weight: 500;
}
.endpoint-desc {
  font-size: 12px;
  color: var(--muted-foreground);
  margin-bottom: 6px;
}
.endpoint-params {
  font-size: 11px;
  color: var(--muted-foreground);
}
.params-label {
  color: var(--muted-foreground);
}
.params-item {
  display: inline-block;
  background: var(--accent);
  color: var(--accent-foreground);
  padding: 1px 6px;
  border-radius: 3px;
  margin-right: 4px;
  margin-top: 2px;
  font-size: 11px;
}
</style>