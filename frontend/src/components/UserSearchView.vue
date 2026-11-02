<template>
  <div class="mobile-search-container">
    <!-- Top Mobile Header -->
    <header class="mobile-header">
      <div class="user-profile-badge">
        <div class="user-avatar">
          {{ userEmailInitial }}
        </div>
        <div class="user-info-text">
          <span class="user-email-text" :title="user?.email">{{ user?.email }}</span>
          <span class="user-role-tag">{{ user?.role === 'admin' ? 'Administrator' : 'Standard User' }}</span>
        </div>
      </div>

      <div class="mobile-header-actions">
        <!-- Switch to Admin View if User is Admin -->
        <button
          v-if="user?.role === 'admin'"
          class="icon-btn primary"
          title="Open Admin Management Portal"
          @click="$emit('switch-to-admin')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          <span class="mobile-hide">Admin</span>
        </button>

        <!-- Change Password Button -->
        <button
          class="icon-btn"
          title="Change Password"
          @click="showChangePassword = true"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        </button>

        <!-- Logout Button -->
        <button
          class="icon-btn danger"
          title="Sign Out"
          @click="$emit('logout')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        </button>
      </div>
    </header>

    <!-- Prominent Mobile Search Box -->
    <div class="search-box-card">
      <div class="big-search-input-wrapper">
        <span class="big-search-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        <input
          v-model="searchQuery"
          type="text"
          class="big-search-input"
          placeholder="Search Name, Reg No, Mobile, City, Make..."
          autocomplete="off"
          autocorrect="off"
          spellcheck="false"
        />
        <button
          v-if="searchQuery"
          class="search-clear-btn"
          title="Clear search"
          @click="clearSearch"
        >
          ✕
        </button>
      </div>

      <!-- Quick Column Filters Toggle Bar -->
      <div class="quick-filter-bar">
        <button
          class="filter-chip"
          :class="{ active: filterMake === '' && filterPincode === '' && filterRto === '' }"
          @click="resetFilters"
        >
          All
        </button>
        <button
          class="filter-chip"
          :class="{ active: showFiltersModal }"
          @click="showFiltersModal = !showFiltersModal"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline; margin-right:4px;"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
          Filters {{ activeFilterCount ? `(${activeFilterCount})` : '' }}
        </button>
      </div>

      <!-- Expandable Filters Row -->
      <div v-if="showFiltersModal" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #f1f5f9;">
        <input
          v-model="filterMake"
          type="text"
          placeholder="Make (e.g. Maruti)"
          class="auth-input"
          style="padding: 8px 10px; font-size: 0.85rem;"
        />
        <input
          v-model="filterPincode"
          type="text"
          placeholder="Pincode (e.g. 411033)"
          class="auth-input"
          style="padding: 8px 10px; font-size: 0.85rem;"
        />
        <input
          v-model="filterRto"
          type="text"
          placeholder="RTO (e.g. MH14)"
          class="auth-input"
          style="padding: 8px 10px; font-size: 0.85rem;"
        />
      </div>
    </div>

    <!-- Results Status Bar -->
    <div class="results-header-info">
      <span class="results-count-text">
        <span v-if="loading">Searching database...</span>
        <span v-else-if="records.length > 0">
          Found <strong>{{ totalCount.toLocaleString() }}</strong> records
          <span style="font-weight: 400; color: #64748b; font-size: 0.8rem;">({{ searchLatencyMs }}ms)</span>
        </span>
        <span v-else-if="searchQuery">No matching records found</span>
        <span v-else>Ready to search</span>
      </span>

      <span v-if="records.length > 0" style="font-size: 0.8rem; color: #64748b;">
        Page {{ page }} of {{ totalPages }}
      </span>
    </div>

    <!-- Loading Spinner / Skeleton -->
    <div v-if="loading" style="text-align: center; padding: 48px 0;">
      <div class="search-logo-circle" style="margin: 0 auto 12px; animation: spin 1s linear infinite;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>
      </div>
      <p style="color: var(--text-muted); font-size: 0.9rem;">Querying 700,000+ records...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="records.length === 0" style="text-align: center; padding: 48px 16px; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--border-color);">
      <div style="font-size: 2.2rem; margin-bottom: 8px;">🔍</div>
      <h3 style="font-size: 1.1rem; color: var(--text-primary); margin-bottom: 6px;">
        {{ searchQuery ? 'No records match your query' : 'Type to search records' }}
      </h3>
      <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 320px; margin: 0 auto;">
        {{ searchQuery ? 'Try searching by a single term like owner name, phone number, vehicle make or registration number.' : 'Instant search across 700,000+ rows with auto-filtering.' }}
      </p>
    </div>

    <!-- Results Cards List -->
    <div v-else class="cards-list">
      <div
        v-for="record in records"
        :key="record.id"
        class="record-mobile-card"
        @click="selectedRecord = record"
      >
        <div class="card-top-row">
          <div class="vehicle-make-title">
            {{ record.make }} {{ record.model_variant }}
          </div>
          <span class="reg-no-badge">{{ record.reg_no || 'NO REG' }}</span>
        </div>

        <div class="owner-name-row">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--primary);"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>{{ record.name || 'Unknown Owner' }}</span>
        </div>

        <div class="card-details-grid">
          <div class="card-detail-item">
            <span class="detail-label">Pincode</span>
            <span class="detail-value">{{ record.pincode || 'N/A' }}</span>
          </div>
          <div class="card-detail-item">
            <span class="detail-label">RTO</span>
            <span class="detail-value">{{ record.rto || 'N/A' }}</span>
          </div>
        </div>

        <div v-if="record.address" style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 10px; line-height: 1.3; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
          📍 {{ record.address }}
        </div>

        <!-- Call & Copy Action Row -->
        <div class="card-action-bar" @click.stop>
          <a
            v-if="record.mobile"
            :href="`tel:${record.mobile}`"
            class="call-btn"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            <span>Call {{ record.mobile }}</span>
          </a>
          <button
            v-if="record.mobile"
            class="copy-btn"
            title="Copy phone number"
            @click="copyPhone(record.mobile)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Pagination Bar -->
    <div v-if="totalPages > 1" style="display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 24px;">
      <button
        class="icon-btn"
        :disabled="page <= 1 || loading"
        @click="goToPage(page - 1)"
      >
        ← Previous
      </button>
      <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);">
        {{ page }} / {{ totalPages }}
      </span>
      <button
        class="icon-btn"
        :disabled="page >= totalPages || loading"
        @click="goToPage(page + 1)"
      >
        Next →
      </button>
    </div>

    <!-- Modals -->
    <RecordDetailModal
      v-if="selectedRecord"
      :record="selectedRecord"
      @close="selectedRecord = null"
      @copied="$emit('show-toast', $event)"
    />

    <ChangePasswordModal
      v-if="showChangePassword"
      :token="token"
      :api-base="apiBase"
      @close="showChangePassword = false"
      @success="$emit('show-toast', $event)"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import RecordDetailModal from './RecordDetailModal.vue'
import ChangePasswordModal from './ChangePasswordModal.vue'

const props = defineProps({
  token: { type: String, required: true },
  user: { type: Object, default: () => ({}) },
  apiBase: { type: String, default: '' }
})

const emit = defineEmits(['logout', 'switch-to-admin', 'show-toast'])

const searchQuery = ref('')
const debouncedQuery = ref('')
const filterMake = ref('')
const filterPincode = ref('')
const filterRto = ref('')
const showFiltersModal = ref(false)

const records = ref([])
const totalCount = ref(0)
const totalPages = ref(1)
const page = ref(1)
const limit = ref(50)
const loading = ref(false)
const searchLatencyMs = ref(0)

const selectedRecord = ref(null)
const showChangePassword = ref(false)

const userEmailInitial = computed(() => {
  return (props.user?.email || 'U').charAt(0).toUpperCase()
})

const activeFilterCount = computed(() => {
  let count = 0
  if (filterMake.value) count++
  if (filterPincode.value) count++
  if (filterRto.value) count++
  return count
})

let debounceTimer = null
watch([searchQuery, filterMake, filterPincode, filterRto], () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    fetchSearchResults()
  }, 250)
})

const clearSearch = () => {
  searchQuery.value = ''
  page.value = 1
  fetchSearchResults()
}

const resetFilters = () => {
  filterMake.value = ''
  filterPincode.value = ''
  filterRto.value = ''
  showFiltersModal.value = false
  page.value = 1
  fetchSearchResults()
}

const goToPage = (p) => {
  page.value = p
  fetchSearchResults()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const copyPhone = (phone) => {
  navigator.clipboard.writeText(phone)
  emit('show-toast', `Copied ${phone} to clipboard!`)
}

const fetchSearchResults = async () => {
  loading.value = true
  const t0 = performance.now()
  try {
    const params = new URLSearchParams()
    if (searchQuery.value.trim()) params.append('query', searchQuery.value.trim())
    if (filterMake.value.trim()) params.append('make', filterMake.value.trim())
    if (filterPincode.value.trim()) params.append('pincode', filterPincode.value.trim())
    if (filterRto.value.trim()) params.append('rto', filterRto.value.trim())
    params.append('page', page.value)
    params.append('limit', limit.value)

    const res = await fetch(`${props.apiBase}/api/search?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${props.token}`
      }
    })

    if (res.status === 401 || res.status === 403) {
      emit('logout')
      return
    }

    const data = await res.json()
    records.value = data.data || []
    totalCount.value = data.total || 0
    totalPages.value = data.total_pages || 1
  } catch (err) {
    console.error('Search error:', err)
  } finally {
    const t1 = performance.now()
    searchLatencyMs.value = Math.round(t1 - t0)
    loading.value = false
  }
}

onMounted(() => {
  fetchSearchResults()
})
</script>

<style scoped>
@keyframes spin {
  100% { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .mobile-hide {
    display: none;
  }
}
</style>
