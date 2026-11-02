<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card glass-panel" style="max-width: 440px;">
      <div class="modal-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div class="login-logo-circle" style="width: 36px; height: 36px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </div>
          <h3>Change Password</h3>
        </div>
        <button class="search-clear-btn" @click="$emit('close')">✕</button>
      </div>

      <div v-if="errorMsg" class="auth-error-msg" style="margin: 16px 0 0;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ errorMsg }}</span>
      </div>

      <form @submit.prevent="handleSubmit" style="margin-top: 18px;">
        <div class="auth-form-group">
          <label>Current Password</label>
          <input
            v-model="oldPassword"
            type="password"
            class="auth-input"
            style="padding-left: 14px;"
            placeholder="Enter current password"
            required
          />
        </div>

        <div class="auth-form-group">
          <label>New Password</label>
          <input
            v-model="newPassword"
            type="password"
            class="auth-input"
            style="padding-left: 14px;"
            placeholder="At least 6 characters"
            minlength="6"
            required
          />
        </div>

        <div class="auth-form-group">
          <label>Confirm New Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="auth-input"
            style="padding-left: 14px;"
            placeholder="Re-enter new password"
            minlength="6"
            required
          />
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px;">
          <button type="button" class="icon-btn" @click="$emit('close')">Cancel</button>
          <button type="submit" class="primary-btn" :disabled="loading">
            <span v-if="!loading">Update Password</span>
            <span v-else>Updating...</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  token: { type: String, required: true },
  apiBase: { type: String, default: '' }
})

const emit = defineEmits(['close', 'success'])

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleSubmit = async () => {
  errorMsg.value = ''
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = 'New passwords do not match.'
    return
  }
  if (newPassword.value.length < 6) {
    errorMsg.value = 'Password must be at least 6 characters long.'
    return
  }

  loading.value = true
  try {
    const res = await fetch(`${props.apiBase}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify({
        old_password: oldPassword.value,
        new_password: newPassword.value
      })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to change password')
    }
    emit('success', 'Password updated successfully!')
    emit('close')
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    loading.value = false
  }
}
</script>
