<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card" style="max-width: 520px;">
      <div class="modal-header">
        <div>
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span class="reg-no-badge" style="font-size: 1rem; font-weight: 800;">{{ record.reg_no || 'NO REG' }}</span>
            <button
              v-if="record.reg_no"
              class="copy-btn"
              style="padding: 4px 8px; font-size: 0.75rem;"
              @click="copyText(record.reg_no, 'Registration Number')"
            >
              Copy
            </button>
          </div>
          <h3 style="font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0;">
            {{ record.make ? record.make + ' ' : '' }}{{ record.model_variant || 'Vehicle Record' }}
          </h3>
        </div>
        <button class="modal-close-btn" @click="$emit('close')">✕</button>
      </div>

      <div style="margin: 18px 0; display: flex; flex-direction: column; gap: 14px;">
        <div class="card-details-grid" style="grid-template-columns: 1fr; background: #f8fafc; padding: 14px; gap: 12px; border-radius: var(--radius-md);">
          <!-- Owner Name -->
          <div class="card-detail-item">
            <span class="detail-label">Owner Name</span>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px;">
              <span class="detail-value" style="font-size: 1.05rem; color: #0f172a; font-weight: 700;">{{ record.name || 'N/A' }}</span>
              <button
                v-if="record.name"
                class="copy-btn"
                style="padding: 4px 8px; font-size: 0.75rem;"
                @click="copyText(record.name, 'Owner Name')"
              >
                Copy
              </button>
            </div>
          </div>

          <!-- Mobile Number -->
          <div class="card-detail-item">
            <span class="detail-label">Mobile Number</span>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px;">
              <span class="detail-value" style="font-size: 1.15rem; color: #1d4ed8; font-weight: 800; font-family: monospace;">{{ record.mobile || 'N/A' }}</span>
              <div v-if="record.mobile" style="display: flex; gap: 8px;">
                <button class="copy-btn" style="padding: 6px 12px; font-size: 0.82rem;" @click="copyText(record.mobile, 'Mobile Number')">Copy</button>
                <a :href="`tel:${record.mobile}`" class="call-btn" style="padding: 6px 14px; font-size: 0.85rem;">📞 Call</a>
              </div>
            </div>
          </div>

          <!-- Complete Address -->
          <div class="card-detail-item">
            <span class="detail-label">Complete Address</span>
            <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-top: 4px;">
              <span class="detail-value" style="line-height: 1.45; font-size: 0.88rem; color: #334155;">{{ record.address || 'N/A' }}</span>
              <button
                v-if="record.address"
                class="copy-btn"
                style="padding: 4px 8px; font-size: 0.75rem; flex-shrink: 0;"
                @click="copyText(record.address, 'Address')"
              >
                Copy
              </button>
            </div>
          </div>
        </div>

        <!-- Metadata Grid -->
        <div class="card-details-grid" style="grid-template-columns: repeat(3, 1fr); gap: 10px;">
          <div class="card-detail-item">
            <span class="detail-label">Pincode</span>
            <span class="detail-value" style="font-weight: 700; color: #0f172a;">{{ record.pincode || 'N/A' }}</span>
          </div>
          <div class="card-detail-item">
            <span class="detail-label">RTO Code</span>
            <span class="detail-value" style="font-weight: 700; color: #0f172a;">{{ record.rto || 'N/A' }}</span>
          </div>
          <div class="card-detail-item">
            <span class="detail-label">Reg Date</span>
            <span class="detail-value">{{ record.reg_date || 'N/A' }}</span>
          </div>
        </div>

        <!-- Vehicle Details Grid -->
        <div class="card-details-grid" style="grid-template-columns: repeat(2, 1fr); gap: 10px;">
          <div class="card-detail-item">
            <span class="detail-label">Vehicle Make</span>
            <span class="detail-value">{{ record.make || 'N/A' }}</span>
          </div>
          <div class="card-detail-item">
            <span class="detail-label">Model / Variant</span>
            <span class="detail-value">{{ record.model_variant || 'N/A' }}</span>
          </div>
        </div>

        <div style="font-size: 0.76rem; color: #94a3b8; display: flex; justify-content: space-between; padding: 0 4px; border-top: 1px solid #f1f5f9; padding-top: 8px;">
          <span>Sheet: {{ record.source_sheet || 'N/A' }}</span>
          <span>Source: {{ record.source_file || 'N/A' }}</span>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn btn-secondary" @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  record: { type: Object, required: true }
})

const emit = defineEmits(['close', 'copied'])

const copyText = (txt, label) => {
  if (!txt) return
  navigator.clipboard.writeText(txt)
  emit('copied', `Copied ${label || 'text'} to clipboard!`)
}
</script>