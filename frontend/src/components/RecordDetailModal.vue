<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card glass-panel" style="max-width: 520px; width: 95%;">
      <div class="modal-header">
        <div>
          <span class="reg-no-badge" style="font-size: 0.95rem; margin-bottom: 4px;">{{ record.reg_no || 'NO REG' }}</span>
          <h3 style="margin-top: 4px; font-size: 1.25rem;">{{ record.make }} {{ record.model_variant }}</h3>
        </div>
        <button class="search-clear-btn" @click="$emit('close')">✕</button>
      </div>

      <div style="margin: 20px 0; display: flex; flex-direction: column; gap: 14px;">
        <div class="card-details-grid" style="grid-template-columns: 1fr; background: #f8fafc; padding: 14px; gap: 12px;">
          <div class="card-detail-item">
            <span class="detail-label">Owner Name</span>
            <span class="detail-value" style="font-size: 1rem; color: #0f172a;">{{ record.name || 'N/A' }}</span>
          </div>

          <div class="card-detail-item">
            <span class="detail-label">Mobile Number</span>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px;">
              <span class="detail-value" style="font-size: 1.1rem; color: #1d4ed8; font-weight: 700;">{{ record.mobile || 'N/A' }}</span>
              <div v-if="record.mobile" style="display: flex; gap: 8px;">
                <button class="copy-btn" style="padding: 6px 10px;" @click="copyText(record.mobile)">Copy</button>
                <a :href="`tel:${record.mobile}`" class="call-btn" style="padding: 6px 12px; font-size: 0.85rem;">Call</a>
              </div>
            </div>
          </div>

          <div class="card-detail-item">
            <span class="detail-label">Address</span>
            <span class="detail-value" style="line-height: 1.4;">{{ record.address || 'N/A' }}</span>
          </div>
        </div>

        <div class="card-details-grid" style="grid-template-columns: repeat(3, 1fr);">
          <div class="card-detail-item">
            <span class="detail-label">Pincode</span>
            <span class="detail-value">{{ record.pincode || 'N/A' }}</span>
          </div>
          <div class="card-detail-item">
            <span class="detail-label">RTO Code</span>
            <span class="detail-value">{{ record.rto || 'N/A' }}</span>
          </div>
          <div class="card-detail-item">
            <span class="detail-label">Reg Date</span>
            <span class="detail-value">{{ record.reg_date || 'N/A' }}</span>
          </div>
        </div>

        <div style="font-size: 0.78rem; color: var(--text-muted); display: flex; justify-content: space-between; padding: 0 4px;">
          <span>Source: {{ record.source_sheet || 'N/A' }}</span>
          <span>File: {{ record.source_file || 'N/A' }}</span>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="icon-btn" @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  record: { type: Object, required: true }
})

const emit = defineEmits(['close', 'copied'])

const copyText = (txt) => {
  navigator.clipboard.writeText(txt)
  emit('copied', 'Copied to clipboard!')
}
</script>
