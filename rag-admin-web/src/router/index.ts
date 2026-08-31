import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '总览' }
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/views/DocManage.vue'),
    meta: { title: '文档管理' }
  },
  {
    path: '/qa',
    name: 'QA',
    component: () => import('@/views/Chat.vue'),
    meta: { title: '知识库问答' }
  },
  {
    path: '/evaluation',
    name: 'Evaluation',
    component: () => import('@/views/Evaluation.vue'),
    meta: { title: '检索评估' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：需要登录的页面做拦截
router.beforeEach((to, _from, next) => {
  if (to.meta.needLogin) {
    const token = localStorage.getItem('token')
    if (!token) {
      // 派发事件让 App.vue 弹出登录对话框
      window.dispatchEvent(new CustomEvent('need-login', { detail: { redirect: to.fullPath } }))
      return next('/dashboard')
    }
  }
  next()
})

export default router