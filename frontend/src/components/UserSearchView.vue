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

    <!-- Strict Vehicle Number Search Box -->
    <div class="search-box-card">
      <form class="big-search-input-wrapper" @submit.prevent="handleSearch">
        <span class="big-search-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </span>
        <input
          v-model="searchQuery"
          type="text"
          class="big-search-input"
          placeholder="Enter Vehicle Number (e.g. MH12SM5430)..."
          autocomplete="off"
          autocorrect="off"
          spellcheck="false"
          @keyup.enter="handleSearch"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="search-clear-btn"
          title="Clear search"
          @click="clearSearch"
        >
          ✕
        </button>
        <button
          type="submit"
          class="btn-search-action"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner-small"></span>
          <span v-else>Search</span>
        </button>
      </form>

      <!-- Quick Example Chips -->
      <div class="quick-filter-bar">
        <span style="font-size: 0.76rem; color: #64748b; font-weight: 600; align-self: center; margin-right: 4px;">Examples:</span>
        <button
          type="button"
          class="filter-chip"
          @click="quickSearch('MH12SM5430')"
        >
          MH12SM5430
        </button>
        <button
          type="button"
          class="filter-chip"
          @click="quickSearch('MH 14 HZ 0747')"
        >
          MH 14 HZ 0747
        </button>
        <button
          type="button"
          class="filter-chip"
          @click="quickSearch('MH14HZ747')"
        >
          MH14HZ747
        </button>
        <button
          type="button"
          class="filter-chip"
          @click="quickSearch('14HZ7')"
        >
          14HZ7
        </button>
      </div>
    </div>

    <!-- STATE 1: Initial Prompt (No Search Performed Yet) -->
    <div v-if="!hasSearched && !loading" class="search-hero-prompt">
      <div class="search-hero-icon">🚗</div>
      <h2 class="search-hero-title">Vehicle Lookup Portal</h2>
      <p class="search-hero-subtitle">
        Enter the vehicle registration number above to look up owner, model, contact, and registration details.
      </p>

      <div class="hero-tips-grid">
        <div class="hero-tip-card">
          <div class="tip-icon">⚡</div>
          <div class="tip-body">
            <strong>Sub-10ms Instant Lookup</strong>
            <span>Direct index search on vehicle registration number</span>
          </div>
        </div>
        <div class="hero-tip-card">
          <div class="tip-icon">🔍</div>
          <div class="tip-body">
            <strong>Flexible Formatting</strong>
            <span>Works with or without spaces (e.g. MH12SM5430 or MH 12 SM 5430)</span>
          </div>
        </div>
        <div class="hero-tip-card">
          <div class="tip-icon">📱</div>
          <div class="tip-body">
            <strong>Direct Call & Copy</strong>
            <span>Quickly copy details or call the owner from your mobile</span>
          </div>
        </div>
      </div>
    </div>

    <!-- STATE 2: Loading State -->
    <div v-else-if="loading" class="search-loading-state">
      <div class="search-spinner-circle"></div>
      <p class="loading-text">Searching vehicle records...</p>
    </div>

    <!-- STATE 3: No Results Found State -->
    <div v-else-if="hasSearched && records.length === 0" class="no-results-card">
      <div class="no-results-icon">❌</div>
      <h3 class="no-results-title">No Vehicle Record Found</h3>
      <p class="no-results-query">
        No record matches vehicle number "<strong>{{ lastQueriedText }}</strong>"
      </p>

      <div class="no-results-tips">
        <div class="tips-heading">Tips for searching:</div>
        <ul>
          <li>Enter a valid vehicle registration number (e.g., <strong>MH12SM5430</strong>, <strong>MH 12 SM 5430</strong>, or <strong>MH-12-SM-5430</strong>).</li>
          <li>Edge cases like missing spaces, dashes, or missing leading zeros (e.g. <strong>MH14HZ7</strong> for <strong>MH14HZ0007</strong>) are automatically handled.</li>
          <li>General keywords, cities, or area names (e.g., "pune", "kharadi") are not permitted.</li>
        </ul>
      </div>

      <button class="btn btn-secondary" style="margin-top: 14px;" @click="clearSearch">
        Clear & Search Again
      </button>
    </div>

    <!-- STATE 4: Results Found State -->
    <div v-else class="results-container">
      <!-- Results Status Bar -->
      <div class="results-header-info">
        <span class="results-count-text">
          Vehicle Found: <strong>{{ totalCount.toLocaleString() }}</strong> record(s)
          <span class="latency-tag">({{ searchLatencyMs }}ms)</span>
        </span>

        <span v-if="totalPages > 1" style="font-size: 0.8rem; color: #64748b;">
          Page {{ page }} of {{ totalPages }}
        </span>
      </div>

      <!-- Results Cards List (Mobile-Optimized) -->
      <div class="cards-list">
        <div
          v-for="record in records"
          :key="record.id"
          class="record-mobile-card"
          @click="selectedRecord = record"
        >
          <!-- Card Header: Vehicle Model & Number Plate Badge -->
          <div class="card-top-row">
            <div class="vehicle-make-title">
              {{ record.make ? record.make + ' ' : '' }}{{ record.model_variant || 'Vehicle' }}
            </div>
            <div class="reg-no-plate-wrapper" @click.stop="copyText(record.reg_no, 'Vehicle Reg No')">
              <span class="reg-no-badge">{{ record.reg_no || 'NO REG' }}</span>
              <span class="plate-copy-icon" title="Copy Registration Number">📋</span>
            </div>
          </div>

          <!-- Owner Name -->
          <div class="owner-name-row">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--primary); flex-shrink: 0;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span class="owner-name-text">{{ record.name || 'Unknown Owner' }}</span>
          </div>

          <!-- Quick Details Badges (Pincode, RTO, Date) -->
          <div class="card-details-grid">
            <div class="card-detail-item">
              <span class="detail-label">RTO Code</span>
              <span class="detail-value">{{ record.rto || 'N/A' }}</span>
            </div>
            <div class="card-detail-item">
              <span class="detail-label">Pincode</span>
              <span class="detail-value">{{ record.pincode || 'N/A' }}</span>
            </div>
            <div class="card-detail-item" v-if="record.reg_date">
              <span class="detail-label">Reg Date</span>
              <span class="detail-value">{{ record.reg_date }}</span>
            </div>
          </div>

          <!-- Full Address -->
          <div v-if="record.address" class="card-address-row">
            <span class="address-pin-icon">📍</span>
            <span class="address-text">{{ record.address }}</span>
          </div>

          <!-- Call & Copy Actions -->
          <div class="card-action-bar" @click.stop>
            <a
              v-if="record.mobile"
              :href="`tel:${record.mobile}`"
              class="call-btn"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
              <span>Call {{ record.mobile }}</span>
            </a>
            <button
              v-if="record.mobile"
              type="button"
              class="copy-btn"
              title="Copy phone number"
              @click="copyPhone(record.mobile)"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <span>Copy</span>
            </button>
            <button
              type="button"
              class="btn-detail-link"
              title="View all record details"
              @click="selectedRecord = record"
            >
              Details
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile Pagination Bar -->
      <div v-if="totalPages > 1" class="mobile-pagination-bar">
        <button
          class="icon-btn"
          :disabled="page <= 1 || loading"
          @click="goToPage(page - 1)"
        >
          ← Previous
        </button>
        <span class="pagination-page-indicator">
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
    </div>

    <!-- Modals -->
    <RecordDetailModal
      v-if="selectedRecord"
      :record="selectedRecord"
      @close="selectedRecord = null"
      @copied="$emit('show-toast', $event, 'success')"
    />

    <ChangePasswordModal
      v-if="showChangePassword"
      :token="token"
      :api-base="apiBase"
      @close="showChangePassword = false"
      @success="$emit('show-toast', $event, 'success')"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import RecordDetailModal from './RecordDetailModal.vue'
import ChangePasswordModal from './ChangePasswordModal.vue'

const props = defineProps({
  token: { type: String, required: true },
  user: { type: Object, default: () => ({}) },
  apiBase: { type: String, default: '' }
})

const emit = defineEmits(['logout', 'switch-to-admin', 'show-toast'])

const searchQuery = ref('')
const lastQueriedText = ref('')
const hasSearched = ref(false)

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

const handleSearch = () => {
  const q = searchQuery.value.trim()

  if (!q) {
    emit('show-toast', 'Please enter a vehicle registration number.', 'error')
    return
  }

  const clean = q.replace(/[^A-Za-z0-9]/g, '').toUpperCase()
  const hasDigits = /\d/.test(clean)
  const hasLetters = /[A-Z]/.test(clean)

  // Validate format: vehicle numbers require digits, letters, and at least 4 alphanumeric chars
  if (clean.length < 4 || !hasDigits || !hasLetters) {
    emit('show-toast', 'Please enter a valid vehicle number (e.g. MH12SM5430).', 'error')
    records.value = []
    totalCount.value = 0
    hasSearched.value = true
    lastQueriedText.value = q
    return
  }

  hasSearched.value = true
  lastQueriedText.value = q
  fetchSearchResults()
}

const quickSearch = (term) => {
  searchQuery.value = term
  page.value = 1
  handleSearch()
}

const clearSearch = () => {
  searchQuery.value = ''
  records.value = []
  totalCount.value = 0
  hasSearched.value = false
  page.value = 1
}

const goToPage = (p) => {
  page.value = p
  fetchSearchResults()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const copyPhone = (phone) => {
  navigator.clipboard.writeText(phone)
  emit('show-toast', `Copied ${phone} to clipboard!`, 'success')
}

const copyText = (text, label) => {
  if (!text) return
  navigator.clipboard.writeText(text)
  emit('show-toast', `Copied ${label}: ${text}`, 'success')
}

const fetchSearchResults = async () => {
  loading.value = true
  const t0 = performance.now()
  try {
    const params = new URLSearchParams()
    if (searchQuery.value.trim()) params.append('query', searchQuery.value.trim())
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
    if (data.latency_ms !== undefined) {
      searchLatencyMs.value = data.latency_ms
    } else {
      const t1 = performance.now()
      searchLatencyMs.value = Math.round(t1 - t0)
    }

    // Trigger toast notification based on result
    if (records.value.length === 0) {
      emit('show-toast', `No record found for vehicle "${lastQueriedText.value}".`, 'error')
    } else {
      emit('show-toast', `Vehicle found: ${records.value[0].reg_no}`, 'success')
    }
  } catch (err) {
    console.error('Search error:', err)
    emit('show-toast', 'Error searching database.', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.btn-search-action {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: 10px 20px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  margin-left: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.btn-search-action:hover {
  background: var(--primary-hover);
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Hero Initial Prompt */
.search-hero-prompt {
  text-align: center;
  padding: 40px 20px 32px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  margin-top: 8px;
}

.search-hero-icon {
  font-size: 3.5rem;
  line-height: 1;
  margin-bottom: 12px;
}

.search-hero-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 8px;
}

.search-hero-subtitle {
  font-size: 0.92rem;
  color: #64748b;
  max-width: 440px;
  margin: 0 auto 24px;
  line-height: 1.45;
}

.hero-tips-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  text-align: left;
  max-width: 480px;
  margin: 0 auto;
}

.hero-tip-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: var(--radius-md);
  border: 1px solid #e2e8f0;
}

.tip-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.tip-body {
  display: flex;
  flex-direction: column;
}

.tip-body strong {
  font-size: 0.9rem;
  color: #1e293b;
}

.tip-body span {
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.3;
}

/* Loading State */
.search-loading-state {
  text-align: center;
  padding: 50px 20px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.search-spinner-circle {
  width: 44px;
  height: 44px;
  border: 4px solid #e2e8f0;
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
  margin: 0 auto 16px;
}

.loading-text {
  font-size: 0.95rem;
  font-weight: 600;
  color: #475569;
}

/* No Results Found State */
.no-results-card {
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid #fed7aa;
  padding: 32px 20px;
  text-align: center;
  box-shadow: var(--shadow-sm);
  margin-top: 8px;
}

.no-results-icon {
  font-size: 3rem;
  line-height: 1;
  margin-bottom: 12px;
}

.no-results-title {
  font-size: 1.3rem;
  font-weight: 800;
  color: #9a3412;
  margin-bottom: 6px;
}

.no-results-query {
  font-size: 0.92rem;
  color: #475569;
  margin-bottom: 20px;
}

.no-results-tips {
  background: #fff7ed;
  border: 1px solid #ffedd5;
  border-radius: var(--radius-md);
  padding: 16px 20px;
  text-align: left;
  max-width: 440px;
  margin: 0 auto;
}

.tips-heading {
  font-size: 0.82rem;
  font-weight: 700;
  color: #c2410c;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.no-results-tips ul {
  margin: 0;
  padding-left: 20px;
  font-size: 0.85rem;
  color: #7c2d12;
  line-height: 1.5;
}

/* Plate badge with copy icon */
.reg-no-plate-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.plate-copy-icon {
  font-size: 0.85rem;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.reg-no-plate-wrapper:hover .plate-copy-icon {
  opacity: 1;
}

.latency-tag {
  font-weight: 500;
  color: #059669;
  font-size: 0.8rem;
  background: #ecfdf5;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #a7f3d0;
  margin-left: 6px;
}

.owner-name-text {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.01em;
}

.card-address-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 0.82rem;
  color: #475569;
  line-height: 1.4;
  margin-bottom: 12px;
  background: #f8fafc;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}

.address-pin-icon {
  font-size: 0.95rem;
  flex-shrink: 0;
}

.btn-detail-link {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #334155;
  padding: 9px 14px;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
}

.btn-detail-link:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.mobile-pagination-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding-bottom: 16px;
}

.pagination-page-indicator {
  font-size: 0.85rem;
  font-weight: 700;
  color: #334155;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .mobile-hide {
    display: none;
  }
  .card-action-bar {
    flex-wrap: wrap;
  }
  .call-btn {
    width: 100%;
    order: 1;
  }
  .copy-btn {
    flex: 1;
    order: 2;
  }
  .btn-detail-link {
    flex: 1;
    order: 3;
  }
}
</style>