<template>
  <div class="login-wrapper">
    <div class="login-card glass-panel">
      <!-- Normal Login Mode -->
      <div v-if="!forcedPasswordChange">
        <div class="login-header">
          <div class="login-logo-circle">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <h2>Data Engine Portal</h2>
          <p>Sign in to access search & database tools</p>
        </div>

        <div v-if="errorMessage" class="auth-error-msg">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{{ errorMessage }}</span>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="auth-form-group">
            <label>Email Address</label>
            <div class="auth-input-wrapper">
              <span class="auth-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              </span>
              <input
                v-model="email"
                type="email"
                class="auth-input"
                placeholder="name@company.com"
                required
                autocomplete="email"
              />
            </div>
          </div>

          <div class="auth-form-group">
            <label>Password / One-Time Password</label>
            <div class="auth-input-wrapper">
              <span class="auth-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </span>
              <input
                v-model="password"
                type="password"
                class="auth-input"
                placeholder="Enter password or OTP"
                required
                autocomplete="current-password"
              />
            </div>
          </div>

          <button type="submit" class="primary-btn login-btn" :disabled="loading">
            <span v-if="!loading">Sign In</span>
            <span v-else>Signing in...</span>
          </button>
        </form>
      </div>

      <!-- Forced Password Change Mode (First Login / OTP) -->
      <div v-else>
        <div class="login-header">
          <div class="login-logo-circle" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h2>Set Permanent Password</h2>
          <p>You logged in with a temporary password. Please set a new password to continue.</p>
        </div>

        <div v-if="changeErrorMessage" class="auth-error-msg">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{{ changeErrorMessage }}</span>
        </div>

        <form @submit.prevent="handleChangePassword">
          <div class="auth-form-group">
            <label>Current / One-Time Password</label>
            <div class="auth-input-wrapper">
              <span class="auth-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </span>
              <input
                v-model="oldPassword"
                type="password"
                class="auth-input"
                placeholder="Temporary password used to log in"
                required
              />
            </div>
          </div>

          <div class="auth-form-group">
            <label>New Permanent Password</label>
            <div class="auth-input-wrapper">
              <span class="auth-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </span>
              <input
                v-model="newPassword"
                type="password"
                class="auth-input"
                placeholder="At least 6 characters"
                minlength="6"
                required
              />
            </div>
          </div>

          <div class="auth-form-group">
            <label>Confirm New Password</label>
            <div class="auth-input-wrapper">
              <span class="auth-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              </span>
              <input
                v-model="confirmPassword"
                type="password"
                class="auth-input"
                placeholder="Re-enter new password"
                minlength="6"
                required
              />
            </div>
          </div>

          <button type="submit" class="primary-btn login-btn" :disabled="changeLoading">
            <span v-if="!changeLoading">Save & Continue</span>
            <span v-else>Saving...</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  apiBase: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['login-success'])

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const forcedPasswordChange = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const changeLoading = ref(false)
const changeErrorMessage = ref('')
const savedToken = ref('')
const savedUser = ref(null)

const handleLogin = async () => {
  errorMessage.value = ''
  loading.value = true
  try {
    const res = await fetch(`${props.apiBase}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value.trim(),
        password: password.value
      })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Login failed')
    }

    // Check if user must change one-time password
    if (data.user && data.user.must_change_password) {
      savedToken.value = data.token
      savedUser.value = data.user
      oldPassword.value = password.value
      forcedPasswordChange.value = true
      return
    }

    emit('login-success', { token: data.token, user: data.user })
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

const handleChangePassword = async () => {
  changeErrorMessage.value = ''
  if (newPassword.value !== confirmPassword.value) {
    changeErrorMessage.value = 'New passwords do not match.'
    return
  }
  if (newPassword.value.length < 6) {
    changeErrorMessage.value = 'Password must be at least 6 characters.'
    return
  }

  changeLoading.value = true
  try {
    const res = await fetch(`${props.apiBase}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${savedToken.value}`
      },
      body: JSON.stringify({
        old_password: oldPassword.value,
        new_password: newPassword.value
      })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to update password')
    }

    savedUser.value.must_change_password = false
    emit('login-success', { token: savedToken.value, user: savedUser.value })
  } catch (err) {
    changeErrorMessage.value = err.message
  } finally {
    changeLoading.value = false
  }
}
</script>
