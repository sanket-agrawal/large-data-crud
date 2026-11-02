<template>
  <div>
    <!-- Not Logged In -->
    <LoginView
      v-if="!token || !user"
      @login-success="handleLoginSuccess"
    />

    <!-- Logged In as Regular User OR Admin viewing user search mode -->
    <UserSearchView
      v-else-if="user.role !== 'admin' || currentViewMode === 'user'"
      :token="token"
      :user="user"
      @logout="handleLogout"
      @switch-to-admin="currentViewMode = 'admin'"
      @show-toast="showToast"
    />

    <!-- Logged In as Admin in Admin Portal -->
    <AdminPortal
      v-else-if="user.role === 'admin'"
      :token="token"
      :user="user"
      @logout="handleLogout"
      @switch-to-user="currentViewMode = 'user'"
      @show-toast="showToast"
    />

    <!-- Toast Notification Banner -->
    <div
      v-if="toastMessage"
      class="toast"
      :class="toastType"
      style="position: fixed; bottom: 24px; right: 24px; z-index: 9999; animation: slideUp 0.3s ease;"
    >
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoginView from './components/LoginView.vue'
import UserSearchView from './components/UserSearchView.vue'
import AdminPortal from './components/AdminPortal.vue'

const token = ref(localStorage.getItem('token') || null)
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const currentViewMode = ref('admin') // 'admin' or 'user'

const toastMessage = ref('')
const toastType = ref('success')
let toastTimer = null

const showToast = (msg, type = 'success') => {
  toastMessage.value = msg
  toastType.value = type
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 3500)
}

const handleLoginSuccess = ({ token: newToken, user: newUser }) => {
  token.value = newToken
  user.value = newUser
  localStorage.setItem('token', newToken)
  localStorage.setItem('user', JSON.stringify(newUser))
  currentViewMode.value = newUser.role === 'admin' ? 'admin' : 'user'
  showToast(`Welcome back, ${newUser.email}!`)
}

const handleLogout = () => {
  if (token.value) {
    fetch('/api/auth/logout', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token.value}` }
    }).catch(() => {})
  }
  token.value = null
  user.value = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

// Verify current session on mount
onMounted(async () => {
  if (!token.value) return
  try {
    const res = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token.value}` }
    })
    if (!res.ok) {
      handleLogout()
      return
    }
    const userData = await res.json()
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
    if (userData.role !== 'admin') {
      currentViewMode.value = 'user'
    }
  } catch {
    // Network or server error
  }
})
</script>

<style>
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
