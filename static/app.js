// ========== 全局状态 ==========
const API_BASE = '';
let currentToken = localStorage.getItem('rag_token') || null;

// ========== Fetch 封装 ==========
async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (currentToken) headers['Authorization'] = 'Bearer ' + currentToken;
  const res = await fetch(API_BASE + path, { ...options, headers });
  return res.json().catch(() => ({ code: res.status, msg: res.statusText }));
}

// FormData 上传（不能手动设 Content-Type，浏览器会自动加 boundary）
async function apiForm(path, formData) {
  const headers = {};
  if (currentToken) headers['Authorization'] = 'Bearer ' + currentToken;
  const res = await fetch(API_BASE + path, { method: 'POST', headers, body: formData });
  return res.json().catch(() => ({ code: res.status }));
}

// ========== Toast ==========
function toast(msg, type = 'info') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'fixed top-20 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg text-sm z-50 shadow-lg fade-in ' +
    (type === 'success' ? 'bg-green-600 text-white' : type === 'error' ? 'bg-red-600 text-white' : 'bg-gray-800 text-white');
  t.classList.remove('hidden');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add('hidden'), 2500);
}

// ========== 登录弹窗 ==========
function toggleLogin() {
  const m = document.getElementById('login-modal');
  if (!m) return;
  m.classList.toggle('hidden');
  document.getElementById('login-err')?.classList.add('hidden');
}

async function doLogin() {
  const username = document.getElementById('login-user').value.trim() || 'admin';
  const password = document.getElementById('login-pwd').value;
  const errEl = document.getElementById('login-err');
  if (!password) {
    errEl.textContent = '请输入密码';
    errEl.classList.remove('hidden');
    return;
  }
  const data = await api('/api/user/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  if (data.code === 200) {
    currentToken = data.data.access_token;
    localStorage.setItem('rag_token', currentToken);
    toast('登录成功', 'success');
    toggleLogin();
    updateUserBadge();
    if (typeof window.onLoginSuccess === 'function') window.onLoginSuccess();
  } else {
    errEl.textContent = data.msg || '登录失败';
    errEl.classList.remove('hidden');
  }
}

function logout() {
  currentToken = null;
  localStorage.removeItem('rag_token');
  updateUserBadge();
  toast('已退出登录', 'info');
}

// ========== 登录检查 ==========
function ensureLogin() {
  if (!currentToken) {
    toast('请先登录', 'error');
    toggleLogin();
    return false;
  }
  return true;
}

function updateUserBadge() {
  const badge = document.getElementById('user-badge');
  const btn = document.getElementById('login-btn');
  if (!badge || !btn) return;
  if (currentToken) {
    try {
      const payload = JSON.parse(atob(currentToken.split('.')[1]));
      badge.textContent = payload.sub ? payload.sub : '已登录';
    } catch {
      badge.textContent = '已登录';
    }
    btn.textContent = '退出';
    btn.onclick = logout;
  } else {
    badge.textContent = '未登录';
    btn.textContent = '登录';
    btn.onclick = toggleLogin;
  }
}

// ========== 工具 ==========
function formatTime(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleString('zh-CN', { hour12: false });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

// ========== 导航高亮 ==========
function highlightNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('http')) return;
    if (href === path) {
      link.classList.add('active', 'text-blue-600');
    } else {
      link.classList.remove('active', 'text-blue-600');
    }
  });
}

// ========== 启动 ==========
document.addEventListener('DOMContentLoaded', () => {
  updateUserBadge();
  highlightNav();
});