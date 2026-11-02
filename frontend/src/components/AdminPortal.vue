<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header glass-panel">
      <div class="brand-section">
        <div class="login-logo-circle" style="background: linear-gradient(135deg, #1e293b, #0f172a);">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        </div>
        <div>
          <h1 style="font-size: 1.35rem; line-height: 1.2;">Admin Management Portal</h1>
          <p style="font-size: 0.8rem; color: var(--text-muted);">Unified Search Engine • Ingestion • RBAC</p>
        </div>
      </div>

      <!-- Tab Switcher -->
      <div class="nav-tabs">
        <button
          class="nav-tab"
          :class="{ active: currentTab === 'users' }"
          @click="currentTab = 'users'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          User Access ({{ usersList.length }})
        </button>

        <button
          class="nav-tab"
          :class="{ active: currentTab === 'import' }"
          @click="currentTab = 'import'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          Data Ingestion
        </button>

        <button
          class="nav-tab"
          :class="{ active: currentTab === 'records' }"
          @click="currentTab = 'records'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          Browse Records
        </button>

        <button
          class="nav-tab"
          :class="{ active: currentTab === 'stats' }"
          @click="currentTab = 'stats'"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
          Analytics
        </button>
      </div>

      <div class="header-actions">
        <!-- Switch to Mobile Search View -->
        <button class="icon-btn" @click="$emit('switch-to-user')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
          <span>Mobile Search View</span>
        </button>

        <!-- Logout -->
        <button class="icon-btn danger" @click="$emit('logout')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span>Logout</span>
        </button>
      </div>
    </header>

    <!-- TAB 1: USERS & ACCESS MANAGEMENT -->
    <div v-if="currentTab === 'users'">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
          <h2 style="font-size: 1.4rem;">User Access Management</h2>
          <p style="color: var(--text-muted); font-size: 0.88rem;">
            Assign users via email, generate temporary one-time passwords, or revoke access anytime.
          </p>
        </div>
        <button class="primary-btn" @click="showAddUserModal = true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          <span>Add New User</span>
        </button>
      </div>

      <!-- Users Table -->
      <div class="glass-panel" style="overflow-x: auto;">
        <table class="data-table">
          <thead>
            <tr>
              <th>User Email</th>
              <th>Role</th>
              <th>Access Status</th>
              <th>Password Status</th>
              <th>Created Date</th>
              <th>Last Active</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="usersLoading">
              <td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted);">
                Loading users...
              </td>
            </tr>
            <tr v-else-if="usersList.length === 0">
              <td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted);">
                No users found. Click "Add New User" to assign access.
              </td>
            </tr>
            <tr v-else v-for="u in usersList" :key="u.id">
              <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-weight: 600; color: var(--text-primary);">{{ u.email }}</span>
                  <span v-if="u.id === user.id" style="font-size: 0.72rem; background: #e0f2fe; color: #0284c7; padding: 2px 6px; border-radius: 4px; font-weight: 600;">YOU</span>
                </div>
              </td>
              <td>
                <span :style="{ fontWeight: '600', color: u.role === 'admin' ? '#7c3aed' : '#2563eb' }">
                  {{ u.role === 'admin' ? 'Administrator' : 'Standard User' }}
                </span>
              </td>
              <td>
                <span class="user-status-badge" :class="u.is_active ? 'active' : 'revoked'">
                  ● {{ u.is_active ? 'Active' : 'Revoked' }}
                </span>
              </td>
              <td>
                <span class="password-status-badge" :class="u.must_change_password ? 'temporary' : 'permanent'">
                  {{ u.must_change_password ? 'Temporary OTP' : 'Permanent' }}
                </span>
              </td>
              <td style="font-size: 0.85rem; color: var(--text-secondary);">
                {{ formatDate(u.created_at) }}
              </td>
              <td style="font-size: 0.85rem; color: var(--text-secondary);">
                {{ u.last_login_at ? formatDate(u.last_login_at) : 'Never' }}
              </td>
              <td style="text-align: right;">
                <div style="display: inline-flex; gap: 6px;">
                  <!-- Toggle Active / Revoke Access -->
                  <button
                    v-if="u.id !== user.id"
                    class="icon-btn"
                    :class="u.is_active ? 'danger' : 'primary'"
                    :title="u.is_active ? 'Revoke user access' : 'Restore user access'"
                    @click="toggleUserActive(u)"
                  >
                    {{ u.is_active ? 'Revoke' : 'Activate' }}
                  </button>

                  <!-- Reset Password -->
                  <button
                    class="icon-btn"
                    title="Generate new temporary password"
                    @click="handleResetPassword(u)"
                  >
                    Reset OTP
                  </button>

                  <!-- Delete User -->
                  <button
                    v-if="u.id !== user.id"
                    class="icon-btn danger"
                    title="Delete user account"
                    @click="handleDeleteUser(u)"
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 2: DATA INGESTION (ADMIN ONLY) -->
    <div v-if="currentTab === 'import'">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.4rem;">Multi-Sheet Excel / CSV Ingestion Engine</h2>
        <p style="color: var(--text-muted); font-size: 0.88rem;">
          Drag and drop Excel files (.xlsx, .xls) with multiple sheets or CSV files. Automatically standardizes columns and updates search index.
        </p>
      </div>

      <div class="glass-panel" style="padding: 32px; margin-bottom: 24px;">
        <!-- Dropzone -->
        <div
          class="dropzone-area"
          :class="{ dragging: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
          @click="$refs.fileInput.click()"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".xlsx,.xls,.csv"
            style="display: none;"
            @change="handleFileSelect"
          />
          <div class="login-logo-circle" style="width: 54px; height: 54px; margin: 0 auto 14px;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          </div>
          <h3 style="font-size: 1.15rem; margin-bottom: 6px;">Choose Excel or CSV files to import</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem;">
            Supports 700,000+ records across multi-sheet workbooks. Click to browse or drag & drop files here.
          </p>
        </div>

        <!-- Selected Files List -->
        <div v-if="selectedFiles.length > 0" style="margin-top: 20px;">
          <h4 style="font-size: 0.95rem; margin-bottom: 10px;">Selected Files ({{ selectedFiles.length }}):</h4>
          <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px;">
            <div
              v-for="(f, idx) in selectedFiles"
              :key="idx"
              style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-color);"
            >
              <span style="font-weight: 500; font-size: 0.9rem;">📄 {{ f.name }}</span>
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="color: var(--text-muted); font-size: 0.8rem;">{{ (f.size / (1024*1024)).toFixed(2) }} MB</span>
                <button class="search-clear-btn" @click="removeSelectedFile(idx)">✕</button>
              </div>
            </div>
          </div>

          <button
            class="primary-btn"
            style="width: 100%; padding: 14px; font-size: 1rem;"
            :disabled="uploading"
            @click="startUpload"
          >
            {{ uploading ? 'Ingesting data into DuckDB...' : `Ingest ${selectedFiles.length} File(s)` }}
          </button>
        </div>

        <!-- Progress Indicator -->
        <div v-if="uploading || uploadStatus !== 'idle'" style="margin-top: 24px; padding: 18px; background: #f8fafc; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 600; font-size: 0.9rem;">{{ uploadMessage }}</span>
            <span style="font-weight: 700; color: var(--primary);">{{ uploadPercent }}%</span>
          </div>
          <div style="height: 10px; background: #e2e8f0; border-radius: 5px; overflow: hidden;">
            <div
              :style="{ width: `${uploadPercent}%`, background: uploadStatus === 'error' ? 'var(--danger)' : 'var(--primary)', height: '100%', transition: 'width 0.3s ease' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Danger Zone / Clear Database -->
      <div class="glass-panel" style="padding: 24px; border: 1px solid #fecaca; background: #fff5f5;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h3 style="color: #b91c1c; font-size: 1.1rem;">Clear Entire Database</h3>
            <p style="color: #7f1d1d; font-size: 0.85rem;">
              Permanently deletes all ingested records from DuckDB. User accounts will be preserved.
            </p>
          </div>
          <button class="icon-btn danger" style="padding: 10px 18px;" @click="showClearDbModal = true">
            Reset Database
          </button>
        </div>
      </div>
    </div>

    <!-- TAB 3: BROWSE RECORDS & CRUD -->
    <div v-if="currentTab === 'records'">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 10px;">
        <div style="display: flex; gap: 10px; align-items: center; flex: 1; max-width: 600px;">
          <input
            v-model="recordsSearchQuery"
            type="text"
            class="auth-input"
            style="padding-left: 14px;"
            placeholder="Search records by name, mobile, reg no, make..."
          />
        </div>

        <div style="display: flex; gap: 8px;">
          <button class="icon-btn" @click="exportData('csv')">Export CSV</button>
          <button class="icon-btn" @click="exportData('xlsx')">Export Excel</button>
          <button class="primary-btn" @click="openAddRecordModal">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Add Record
          </button>
        </div>
      </div>

      <!-- Desktop Data Grid -->
      <div class="glass-panel" style="overflow-x: auto;">
        <table class="data-table">
          <thead>
            <tr>
              <th>Reg No</th>
              <th>Make & Model</th>
              <th>Owner Name</th>
              <th>Mobile</th>
              <th>Pincode</th>
              <th>RTO</th>
              <th>Reg Date</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="recordsLoading">
              <td colspan="8" style="text-align: center; padding: 32px; color: var(--text-muted);">
                Searching records...
              </td>
            </tr>
            <tr v-else-if="recordsList.length === 0">
              <td colspan="8" style="text-align: center; padding: 32px; color: var(--text-muted);">
                No records found.
              </td>
            </tr>
            <tr v-else v-for="r in recordsList" :key="r.id">
              <td><span class="reg-no-badge">{{ r.reg_no || 'N/A' }}</span></td>
              <td><strong>{{ r.make }}</strong> {{ r.model_variant }}</td>
              <td>{{ r.name || 'N/A' }}</td>
              <td><a :href="`tel:${r.mobile}`" style="color: #2563eb; text-decoration: none; font-weight: 600;">{{ r.mobile || 'N/A' }}</a></td>
              <td>{{ r.pincode || 'N/A' }}</td>
              <td>{{ r.rto || 'N/A' }}</td>
              <td>{{ r.reg_date || 'N/A' }}</td>
              <td style="text-align: right;">
                <div style="display: inline-flex; gap: 6px;">
                  <button class="icon-btn" @click="openEditRecordModal(r)">Edit</button>
                  <button class="icon-btn danger" @click="deleteRecordItem(r.id)">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="recordsTotalPages > 1" style="display: flex; justify-content: space-between; align-items: center; margin-top: 18px;">
        <span style="font-size: 0.85rem; color: var(--text-secondary);">
          Total <strong>{{ recordsTotalCount.toLocaleString() }}</strong> records
        </span>
        <div style="display: flex; gap: 8px;">
          <button class="icon-btn" :disabled="recordsPage <= 1" @click="recordsPage--; fetchRecords()">Previous</button>
          <span style="padding: 6px 12px; font-weight: 600;">{{ recordsPage }} / {{ recordsTotalPages }}</span>
          <button class="icon-btn" :disabled="recordsPage >= recordsTotalPages" @click="recordsPage++; fetchRecords()">Next</button>
        </div>
      </div>
    </div>

    <!-- TAB 4: ANALYTICS -->
    <div v-if="currentTab === 'stats'">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.4rem;">System Analytics & Database Overview</h2>
        <p style="color: var(--text-muted); font-size: 0.88rem;">Real-time breakdown of records, storage, and brands.</p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px;">
        <div class="glass-panel" style="padding: 20px;">
          <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Total Records</span>
          <h3 style="font-size: 2rem; color: var(--primary); margin-top: 4px;">{{ stats?.total_records?.toLocaleString() || 0 }}</h3>
        </div>
        <div class="glass-panel" style="padding: 20px;">
          <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Database Size</span>
          <h3 style="font-size: 2rem; color: #10b981; margin-top: 4px;">{{ stats?.db_size_mb || 0 }} MB</h3>
        </div>
        <div class="glass-panel" style="padding: 20px;">
          <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Source Sheets</span>
          <h3 style="font-size: 2rem; color: #8b5cf6; margin-top: 4px;">{{ stats?.sheets?.length || 0 }}</h3>
        </div>
        <div class="glass-panel" style="padding: 20px;">
          <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">Imported Files</span>
          <h3 style="font-size: 2rem; color: #f59e0b; margin-top: 4px;">{{ stats?.files?.length || 0 }}</h3>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
        <!-- Top Makes -->
        <div class="glass-panel" style="padding: 20px;">
          <h4 style="font-size: 1rem; margin-bottom: 14px;">Top Vehicle Brands</h4>
          <div v-for="m in stats?.top_makes || []" :key="m.make" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9;">
            <span style="font-weight: 600;">{{ m.make }}</span>
            <span style="color: var(--text-muted);">{{ m.count.toLocaleString() }} leads</span>
          </div>
        </div>

        <!-- Top Pincodes -->
        <div class="glass-panel" style="padding: 20px;">
          <h4 style="font-size: 1rem; margin-bottom: 14px;">Top Area Pincodes</h4>
          <div v-for="p in stats?.top_pincodes || []" :key="p.pincode" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9;">
            <span style="font-weight: 600;">{{ p.pincode }}</span>
            <span style="color: var(--text-muted);">{{ p.count.toLocaleString() }} records</span>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL: ADD NEW USER -->
    <div v-if="showAddUserModal" class="modal-overlay" @click.self="showAddUserModal = false">
      <div class="modal-card glass-panel" style="max-width: 440px;">
        <div class="modal-header">
          <h3>Add New User</h3>
          <button class="search-clear-btn" @click="showAddUserModal = false">✕</button>
        </div>

        <div v-if="addUserError" class="auth-error-msg" style="margin: 14px 0 0;">
          {{ addUserError }}
        </div>

        <form @submit.prevent="submitAddUser" style="margin-top: 18px;">
          <div class="auth-form-group">
            <label>User Email Address</label>
            <input
              v-model="newUserEmail"
              type="email"
              class="auth-input"
              style="padding-left: 14px;"
              placeholder="e.g. employee@company.com"
              required
            />
          </div>

          <div class="auth-form-group">
            <label>Initial Password / OTP (Optional)</label>
            <input
              v-model="newUserPassword"
              type="text"
              class="auth-input"
              style="padding-left: 14px;"
              placeholder="Leave blank to auto-generate OTP"
            />
          </div>

          <div class="auth-form-group">
            <label>Access Role</label>
            <select v-model="newUserRole" class="auth-input" style="padding-left: 14px;">
              <option value="user">Standard User (Search Only)</option>
              <option value="admin">Administrator (Full Access)</option>
            </select>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px;">
            <button type="button" class="icon-btn" @click="showAddUserModal = false">Cancel</button>
            <button type="submit" class="primary-btn" :disabled="addUserLoading">
              {{ addUserLoading ? 'Creating...' : 'Create User' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: ONE TIME PASSWORD DISPLAY -->
    <div v-if="showOtpModal" class="modal-overlay" @click.self="showOtpModal = false">
      <div class="modal-card glass-panel" style="max-width: 460px; text-align: center;">
        <div class="login-logo-circle" style="background: linear-gradient(135deg, #10b981, #059669); margin: 0 auto 12px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <h3 style="font-size: 1.25rem;">{{ otpModalTitle }}</h3>
        <p style="color: var(--text-muted); font-size: 0.88rem; margin-top: 4px;">
          Share these login details with <strong>{{ otpModalEmail }}</strong>. They will be required to set a permanent password upon first login.
        </p>

        <div class="otp-box">
          <span style="font-size: 0.78rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">One-Time Password (OTP)</span>
          <div class="otp-code">{{ otpModalCode }}</div>
          <button class="icon-btn" style="margin: 0 auto;" @click="copyOtpCode">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            Copy OTP to Clipboard
          </button>
        </div>

        <button class="primary-btn" style="width: 100%; margin-top: 10px;" @click="showOtpModal = false">
          Done
        </button>
      </div>
    </div>

    <!-- MODAL: ADD / EDIT RECORD -->
    <div v-if="showRecordModal" class="modal-overlay" @click.self="showRecordModal = false">
      <div class="modal-card glass-panel" style="max-width: 560px;">
        <div class="modal-header">
          <h3>{{ editingRecordId ? 'Edit Record' : 'Add New Record' }}</h3>
          <button class="search-clear-btn" @click="showRecordModal = false">✕</button>
        </div>

        <form @submit.prevent="submitRecordForm" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 16px;">
          <div class="auth-form-group" style="margin: 0;">
            <label>Registration No</label>
            <input v-model="recordFormData.reg_no" type="text" class="auth-input" style="padding-left: 10px;" required />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>Owner Name</label>
            <input v-model="recordFormData.name" type="text" class="auth-input" style="padding-left: 10px;" required />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>Make / Brand</label>
            <input v-model="recordFormData.make" type="text" class="auth-input" style="padding-left: 10px;" required />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>Model Variant</label>
            <input v-model="recordFormData.model_variant" type="text" class="auth-input" style="padding-left: 10px;" />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>Mobile Number</label>
            <input v-model="recordFormData.mobile" type="text" class="auth-input" style="padding-left: 10px;" />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>Pincode</label>
            <input v-model="recordFormData.pincode" type="text" class="auth-input" style="padding-left: 10px;" />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>RTO Code</label>
            <input v-model="recordFormData.rto" type="text" class="auth-input" style="padding-left: 10px;" />
          </div>
          <div class="auth-form-group" style="margin: 0;">
            <label>Reg Date</label>
            <input v-model="recordFormData.reg_date" type="text" class="auth-input" style="padding-left: 10px;" />
          </div>
          <div class="auth-form-group" style="grid-column: span 2; margin: 0;">
            <label>Address</label>
            <textarea v-model="recordFormData.address" class="auth-input" style="padding: 10px; height: 60px;"></textarea>
          </div>

          <div style="grid-column: span 2; display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;">
            <button type="button" class="icon-btn" @click="showRecordModal = false">Cancel</button>
            <button type="submit" class="primary-btn">Save Record</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CLEAR DB CONFIRMATION -->
    <div v-if="showClearDbModal" class="modal-overlay" @click.self="showClearDbModal = false">
      <div class="modal-card glass-panel" style="max-width: 420px; text-align: center;">
        <div style="font-size: 2.4rem; margin-bottom: 8px;">⚠️</div>
        <h3 style="font-size: 1.2rem; color: #b91c1c;">Clear Entire Database?</h3>
        <p style="color: var(--text-muted); font-size: 0.88rem; margin: 10px 0 20px;">
          This will permanently delete all vehicle records. This action cannot be undone.
        </p>
        <div style="display: flex; gap: 10px;">
          <button class="icon-btn" style="flex: 1;" @click="showClearDbModal = false">Cancel</button>
          <button class="primary-btn" style="flex: 1; background: #dc2626;" @click="confirmClearDatabase">Yes, Clear All</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  token: { type: String, required: true },
  user: { type: Object, default: () => ({}) },
  apiBase: { type: String, default: '' }
})

const emit = defineEmits(['logout', 'switch-to-user', 'show-toast'])

const currentTab = ref('users') // 'users', 'import', 'records', 'stats'

// --- Users Management State ---
const usersList = ref([])
const usersLoading = ref(false)
const showAddUserModal = ref(false)
const newUserEmail = ref('')
const newUserPassword = ref('')
const newUserRole = ref('user')
const addUserLoading = ref(false)
const addUserError = ref('')

const showOtpModal = ref(false)
const otpModalTitle = ref('')
const otpModalEmail = ref('')
const otpModalCode = ref('')

// --- Ingestion State ---
const isDragging = ref(false)
const selectedFiles = ref([])
const uploading = ref(false)
const uploadPercent = ref(0)
const uploadMessage = ref('')
const uploadStatus = ref('idle')
const showClearDbModal = ref(false)

// --- Browse Records State ---
const recordsList = ref([])
const recordsLoading = ref(false)
const recordsSearchQuery = ref('')
const recordsPage = ref(1)
const recordsLimit = ref(50)
const recordsTotalCount = ref(0)
const recordsTotalPages = ref(1)

const showRecordModal = ref(false)
const editingRecordId = ref(null)
const recordFormData = ref({
  reg_no: '', rto: '', reg_date: '', name: '', address: '', pincode: '', make: '', model_variant: '', mobile: ''
})

// --- Stats State ---
const stats = ref(null)

const formatDate = (dt) => {
  if (!dt) return 'N/A'
  try {
    return new Date(dt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return dt
  }
}

// Fetch Users
const fetchUsers = async () => {
  usersLoading.value = true
  try {
    const res = await fetch(`${props.apiBase}/api/admin/users`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    if (res.status === 401 || res.status === 403) {
      emit('logout')
      return
    }
    const data = await res.json()
    usersList.value = data.users || []
  } catch (err) {
    console.error('Fetch users error:', err)
  } finally {
    usersLoading.value = false
  }
}

const submitAddUser = async () => {
  addUserError.value = ''
  addUserLoading.value = true
  try {
    const res = await fetch(`${props.apiBase}/api/admin/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify({
        email: newUserEmail.value.trim(),
        password: newUserPassword.value.trim() || null,
        role: newUserRole.value
      })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to create user')

    showAddUserModal.value = false
    newUserEmail.value = ''
    newUserPassword.value = ''
    newUserRole.value = 'user'

    otpModalTitle.value = 'User Created Successfully!'
    otpModalEmail.value = data.email
    otpModalCode.value = data.one_time_password
    showOtpModal.value = true

    fetchUsers()
  } catch (err) {
    addUserError.value = err.message
  } finally {
    addUserLoading.value = false
  }
}

const toggleUserActive = async (u) => {
  const newStatus = !u.is_active
  const actionName = newStatus ? 'activate' : 'revoke access for'
  if (!confirm(`Are you sure you want to ${actionName} ${u.email}?`)) return

  try {
    const res = await fetch(`${props.apiBase}/api/admin/users/${u.id}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify({ is_active: newStatus })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to update user status')

    emit('show-toast', newStatus ? 'User activated!' : 'User access revoked!')
    fetchUsers()
  } catch (err) {
    alert(err.message)
  }
}

const handleResetPassword = async (u) => {
  if (!confirm(`Generate a new temporary one-time password for ${u.email}?`)) return
  try {
    const res = await fetch(`${props.apiBase}/api/admin/users/${u.id}/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify({})
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to reset password')

    otpModalTitle.value = 'Password Reset Generated'
    otpModalEmail.value = u.email
    otpModalCode.value = data.one_time_password
    showOtpModal.value = true
    fetchUsers()
  } catch (err) {
    alert(err.message)
  }
}

const handleDeleteUser = async (u) => {
  if (!confirm(`Are you sure you want to permanently delete user ${u.email}?`)) return
  try {
    const res = await fetch(`${props.apiBase}/api/admin/users/${u.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to delete user')

    emit('show-toast', 'User deleted successfully!')
    fetchUsers()
  } catch (err) {
    alert(err.message)
  }
}

const copyOtpCode = () => {
  navigator.clipboard.writeText(otpModalCode.value)
  emit('show-toast', 'Copied OTP to clipboard!')
}

// --- Ingestion Logic ---
const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.name.match(/\.(xlsx|xls|csv)$/i))
  selectedFiles.value = [...selectedFiles.value, ...files]
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  selectedFiles.value = [...selectedFiles.value, ...files]
}

const removeSelectedFile = (idx) => {
  selectedFiles.value.splice(idx, 1)
}

const startUpload = async () => {
  if (selectedFiles.value.length === 0) return
  uploading.value = true
  uploadPercent.value = 5
  uploadStatus.value = 'processing'
  uploadMessage.value = 'Uploading files to server...'

  const formData = new FormData()
  selectedFiles.value.forEach(f => formData.append('files', f))

  try {
    const response = await fetch(`${props.apiBase}/api/import`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${props.token}` },
      body: formData
    })

    if (!response.ok) throw new Error('Ingestion failed')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.substring(6))
            uploadPercent.value = parsed.progress || 0
            uploadMessage.value = parsed.message || ''
            if (parsed.status === 'completed') {
              uploadStatus.value = 'completed'
              selectedFiles.value = []
              fetchStats()
              fetchRecords()
              emit('show-toast', 'Ingestion completed successfully!')
            } else if (parsed.status === 'error') {
              uploadStatus.value = 'error'
            }
          } catch (e) {
            console.error(e)
          }
        }
      }
    }
  } catch (err) {
    uploadStatus.value = 'error'
    uploadMessage.value = `Upload failed: ${err.message}`
  } finally {
    uploading.value = false
  }
}

const confirmClearDatabase = async () => {
  try {
    const res = await fetch(`${props.apiBase}/api/clear`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    if (res.ok) {
      showClearDbModal.value = false
      emit('show-toast', 'Database cleared successfully!')
      fetchStats()
      fetchRecords()
    }
  } catch (err) {
    alert('Failed to clear database')
  }
}

// --- Browse Records Logic ---
let recordsDebounce = null
watch(recordsSearchQuery, () => {
  clearTimeout(recordsDebounce)
  recordsDebounce = setTimeout(() => {
    recordsPage.value = 1
    fetchRecords()
  }, 250)
})

const fetchRecords = async () => {
  recordsLoading.value = true
  try {
    const params = new URLSearchParams()
    if (recordsSearchQuery.value.trim()) params.append('query', recordsSearchQuery.value.trim())
    params.append('page', recordsPage.value)
    params.append('limit', recordsLimit.value)

    const res = await fetch(`${props.apiBase}/api/search?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    const data = await res.json()
    recordsList.value = data.data || []
    recordsTotalCount.value = data.total || 0
    recordsTotalPages.value = data.total_pages || 1
  } catch (err) {
    console.error('Fetch records error:', err)
  } finally {
    recordsLoading.value = false
  }
}

const openAddRecordModal = () => {
  editingRecordId.value = null
  recordFormData.value = { reg_no: '', rto: '', reg_date: '', name: '', address: '', pincode: '', make: '', model_variant: '', mobile: '' }
  showRecordModal.value = true
}

const openEditRecordModal = (r) => {
  editingRecordId.value = r.id
  recordFormData.value = { ...r }
  showRecordModal.value = true
}

const submitRecordForm = async () => {
  try {
    const isEdit = !!editingRecordId.value
    const url = isEdit ? `${props.apiBase}/api/records/${editingRecordId.value}` : `${props.apiBase}/api/records`
    const method = isEdit ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.token}`
      },
      body: JSON.stringify(recordFormData.value)
    })
    if (res.ok) {
      showRecordModal.value = false
      emit('show-toast', isEdit ? 'Record updated!' : 'Record created!')
      fetchRecords()
    }
  } catch (err) {
    alert('Failed to save record')
  }
}

const deleteRecordItem = async (id) => {
  if (!confirm('Delete this record?')) return
  try {
    const res = await fetch(`${props.apiBase}/api/records/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    if (res.ok) {
      emit('show-toast', 'Record deleted!')
      fetchRecords()
    }
  } catch (err) {
    alert('Failed to delete')
  }
}

const exportData = (format) => {
  const q = recordsSearchQuery.value ? `&query=${encodeURIComponent(recordsSearchQuery.value)}` : ''
  window.open(`${props.apiBase}/api/export?format=${format}&token=${props.token}${q}`, '_blank')
}

// --- Fetch Stats ---
const fetchStats = async () => {
  try {
    const res = await fetch(`${props.apiBase}/api/stats`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    if (res.ok) {
      stats.value = await res.json()
    }
  } catch (err) {
    console.error('Stats fetch error:', err)
  }
}

onMounted(() => {
  fetchUsers()
  fetchStats()
  fetchRecords()
})
</script>

<style scoped>
.dropzone-area {
  border: 2px dashed #93c5fd;
  border-radius: var(--radius-lg);
  padding: 42px 20px;
  text-align: center;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropzone-area:hover, .dropzone-area.dragging {
  background: #eff6ff;
  border-color: var(--primary);
}
</style>
