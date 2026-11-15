<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <div>
          <h3>Change Password</h3>
          <p class="modal-subtitle">Set your permanent account password</p>
        </div>
        <button class="modal-close-btn" @click="$emit('close')">✕</button>
      </div>

      <div v-if="errorMsg" class="auth-error-msg" style="margin: 0 0 16px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ errorMsg }}</span>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="modal-field">
          <label class="modal-label">Current Password</label>
          <input
            v-model="oldPassword"
            type="password"
            class="modal-input"
            placeholder="Enter current password"
            required
          />
        </div>

        <div class="modal-field">
          <label class="modal-label">New Password</label>
          <input
            v-model="newPassword"
            type="password"
            class="modal-input"
            placeholder="At least 6 characters"
            minlength="6"
            required
          />
        </div>

        <div class="modal-field">
          <label class="modal-label">Confirm New Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="modal-input"
            placeholder="Re-enter new password"
            minlength="6"
            required
          />
        </div>

        <div class="modal-footer">
          <button type="button" class="modal-btn-cancel" @click="$emit('close')">Cancel</button>
          <button type="submit" class="modal-btn-submit" :disabled="loading">
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
