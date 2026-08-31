import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const isAdmin = ref(localStorage.getItem('is_admin') === 'true')

  function setToken(t: string, user: { username: string; is_admin: boolean }) {
    token.value = t
    username.value = user.username
    isAdmin.value = user.is_admin
    localStorage.setItem('token', t)
    localStorage.setItem('username', user.username)
    localStorage.setItem('is_admin', String(user.is_admin))
  }

  function clearToken() {
    token.value = ''
    username.value = ''
    isAdmin.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('is_admin')
  }

  const isLoggedIn = () => !!token.value

  return { token, username, isAdmin, setToken, clearToken, isLoggedIn }
})