import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, UploadCloud, Database, Layers, Filter, RefreshCw, Plus, Edit2, Trash2,
  Download, FileSpreadsheet, CheckCircle, AlertCircle, X, ChevronLeft, ChevronRight,
  BarChart2, MapPin, Hash, Phone, User, Calendar, ShieldCheck, Tag, Globe
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('search'); // 'search', 'import', 'stats'
  
  // Data & Stats State
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  
  // Search & Filter State
  const [query, setQuery] = useState('');
  const [filterMake, setFilterMake] = useState('');
  const [filterPincode, setFilterPincode] = useState('');
  const [filterRto, setFilterRto] = useState('');
  const [filterSheet, setFilterSheet] = useState('');
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(50);
  const [sortBy, setSortBy] = useState('id');
  const [sortOrder, setSortOrder] = useState('ASC');
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Modals & Upload State
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle', 'processing', 'completed', 'error'
  const [toast, setToast] = useState(null);

  // Form State for Add/Edit
  const [formData, setFormData] = useState({
    reg_no: '', rto: '', reg_date: '', name: '', address: '', pincode: '', make: '', model_variant: '', mobile: ''
  });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Fetch Statistics
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  // Fetch Records with debounce/query params
  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        sort_by: sortBy,
        sort_order: sortOrder
      });

      if (query.trim()) params.append('query', query.trim());
      if (filterMake.trim()) params.append('make', filterMake.trim());
      if (filterPincode.trim()) params.append('pincode', filterPincode.trim());
      if (filterRto.trim()) params.append('rto', filterRto.trim());
      if (filterSheet.trim()) params.append('source_sheet', filterSheet.trim());

      const res = await fetch(`/api/search?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setRecords(data.data);
        setTotalRecords(data.total);
        setTotalPages(data.total_pages);
      }
    } catch (err) {
      console.error('Failed to search records:', err);
      showToast('Error searching database', 'error');
    } finally {
      setLoading(false);
      setInitialLoading(false);
    }
  }, [query, filterMake, filterPincode, filterRto, filterSheet, page, limit, sortBy, sortOrder]);

  useEffect(() => {
    fetchStats();
    fetchRecords();
  }, [fetchStats, fetchRecords]);

  // Handle File Upload with Real-Time Percentage Progress
  const handleFileUpload = async (filesToUpload) => {
    const files = filesToUpload || selectedFiles;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadPercent(5);
    setUploadStatus('processing');
    setUploadMessage('Uploading files to server...');

    const data = new FormData();
    for (let i = 0; i < files.length; i++) {
      data.append('files', files[i]);
    }

    try {
      const response = await fetch('/api/import', {
        method: 'POST',
        body: data
      });

      if (!response.ok) {
        showToast('Failed to start import service', 'error');
        setUploading(false);
        setUploadStatus('error');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.replace('data: ', ''));
              setUploadPercent(event.progress || 0);
              setUploadMessage(event.message || '');
              if (event.status) setUploadStatus(event.status);

              if (event.status === 'completed') {
                showToast(event.message || 'Ingestion completed successfully!');
                setSelectedFiles([]);
                fetchStats();
                fetchRecords();
              }
            } catch (err) {
              console.error('Failed to parse progress event:', err);
            }
          }
        }
      }
    } catch (err) {
      console.error('Import error:', err);
      showToast('Error during data import', 'error');
      setUploadStatus('error');
    } finally {
      setUploading(false);
    }
  };

  // Handle Record Add/Edit Submit
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingRecord ? `/api/records/${editingRecord.id}` : '/api/records';
      const method = editingRecord ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        showToast(editingRecord ? 'Record updated successfully!' : 'New record created!');
        setShowAddModal(false);
        setEditingRecord(null);
        fetchStats();
        fetchRecords();
      }
    } catch (err) {
      showToast('Error saving record', 'error');
    }
  };

  // Delete Record
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this record?')) return;
    try {
      const res = await fetch(`/api/records/${id}`, { method: 'DELETE' });
      if (res.ok) {
        showToast('Record deleted');
        fetchStats();
        fetchRecords();
      }
    } catch (err) {
      showToast('Error deleting record', 'error');
    }
  };

  // Clear Entire Database
  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete ALL data from the database? This cannot be undone.')) return;
    try {
      const res = await fetch('/api/clear', { method: 'POST' });
      if (res.ok) {
        showToast('Database cleared completely');
        fetchStats();
        fetchRecords();
      }
    } catch (err) {
      showToast('Error clearing database', 'error');
    }
  };

  // Export CSV/Excel
  const handleExport = (format) => {
    const params = new URLSearchParams({ format });
    if (query.trim()) params.append('query', query.trim());
    if (filterMake.trim()) params.append('make', filterMake.trim());
    if (filterPincode.trim()) params.append('pincode', filterPincode.trim());
    if (filterRto.trim()) params.append('rto', filterRto.trim());
    if (filterSheet.trim()) params.append('source_sheet', filterSheet.trim());

    window.open(`/api/export?${params.toString()}`, '_blank');
  };

  // Open Edit Modal
  const openEditModal = (rec) => {
    setEditingRecord(rec);
    setFormData({
      reg_no: rec.reg_no || '',
      rto: rec.rto || '',
      reg_date: rec.reg_date || '',
      name: rec.name || '',
      address: rec.address || '',
      pincode: rec.pincode || '',
      make: rec.make || '',
      model_variant: rec.model_variant || '',
      mobile: rec.mobile || ''
    });
    setShowAddModal(true);
  };

  // Open Add Modal
  const openAddModal = () => {
    setEditingRecord(null);
    setFormData({
      reg_no: '', rto: '', reg_date: '', name: '', address: '', pincode: '', make: '', model_variant: '', mobile: ''
    });
    setShowAddModal(true);
  };

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && (
        <div className={`toast ${toast.type === 'error' ? 'toast-error' : ''}`}>
          {toast.type === 'error' ? <AlertCircle size={18} color="#dc2626" /> : <CheckCircle size={18} color="#059669" />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header */}
      <header className="glass-panel app-header">
        <div className="brand-section">
          <div className="brand-icon">
            <Database size={24} />
          </div>
          <div className="brand-title">
            <h1>Universal Data Engine</h1>
            <p>High-Performance Ingestion & Instant Search for Large Datasets (DuckDB Powered)</p>
          </div>
        </div>

        <div className="header-actions">
          <nav className="nav-tabs">
            <button
              className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <Search size={16} /> Search & Records
            </button>
            <button
              className={`tab-btn ${activeTab === 'import' ? 'active' : ''}`}
              onClick={() => setActiveTab('import')}
            >
              <UploadCloud size={16} /> Ingest Data
            </button>
            <button
              className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveTab('stats')}
            >
              <BarChart2 size={16} /> Analytics
            </button>
          </nav>
        </div>
      </header>

      {/* Stats Overview */}
      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon"><Layers size={22} /></div>
          <div className="stat-info">
            <h3>{stats ? stats.total_records.toLocaleString() : 0}</h3>
            <p>Total Database Records</p>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon"><Tag size={22} /></div>
          <div className="stat-info">
            <h3>{stats ? stats.top_makes.length : 0}+</h3>
            <p>Unique Categories / Brands</p>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon"><MapPin size={22} /></div>
          <div className="stat-info">
            <h3>{stats ? stats.top_pincodes.length : 0}+</h3>
            <p>Location Clusters</p>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon"><FileSpreadsheet size={22} /></div>
          <div className="stat-info">
            <h3>{stats ? stats.sheets.length : 0} Sheets</h3>
            <p>Data Sources ({stats ? stats.db_size_mb : 0} MB)</p>
          </div>
        </div>
      </div>

      {/* TAB 1: SEARCH & DATA EXPLORER */}
      {activeTab === 'search' && (
        <>
          <div className="glass-panel search-controls">
            {/* Search Input Bar */}
            <div className="search-bar-row">
              <div className="search-input-wrapper">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Instant Search across Name, Mobile, Ref No, Address, Pincode, Category, Variant, or Sheet..."
                  value={query}
                  onChange={(e) => { setQuery(e.target.value); setPage(1); }}
                />
                {query && (
                  <button className="clear-search-btn" onClick={() => { setQuery(''); setPage(1); }}>
                    <X size={16} />
                  </button>
                )}
              </div>

              <button className="btn btn-primary" onClick={openAddModal}>
                <Plus size={16} /> Add Record
              </button>

              <button className="btn btn-secondary" onClick={() => handleExport('csv')}>
                <Download size={16} /> Export CSV
              </button>

              <button className="btn btn-secondary" onClick={() => handleExport('xlsx')}>
                <FileSpreadsheet size={16} /> Export Excel
              </button>
            </div>

            {/* Column Filters Row */}
            <div className="filter-row">
              <div className="filter-group">
                <label>Filter by Category</label>
                <select
                  className="filter-select"
                  value={filterMake}
                  onChange={(e) => { setFilterMake(e.target.value); setPage(1); }}
                >
                  <option value="">All Categories</option>
                  {stats?.top_makes.map(m => (
                    <option key={m.make} value={m.make}>{m.make} ({m.count.toLocaleString()})</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label>Filter by Pincode</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder="e.g. 411033"
                  value={filterPincode}
                  onChange={(e) => { setFilterPincode(e.target.value); setPage(1); }}
                />
              </div>

              <div className="filter-group">
                <label>Filter by Region / Code</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder="e.g. MH14"
                  value={filterRto}
                  onChange={(e) => { setFilterRto(e.target.value); setPage(1); }}
                />
              </div>

              <div className="filter-group">
                <label>Filter by Sheet</label>
                <select
                  className="filter-select"
                  value={filterSheet}
                  onChange={(e) => { setFilterSheet(e.target.value); setPage(1); }}
                >
                  <option value="">All Source Sheets</option>
                  {stats?.sheets.map(s => (
                    <option key={s.sheet} value={s.sheet}>{s.sheet} ({s.count.toLocaleString()} rows)</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label>Records Per Page</label>
                <select
                  className="filter-select"
                  value={limit}
                  onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}
                >
                  <option value={25}>25 Rows</option>
                  <option value={50}>50 Rows</option>
                  <option value={100}>100 Rows</option>
                  <option value={250}>250 Rows</option>
                </select>
              </div>
            </div>
          </div>

          {/* Data Table */}
          <div className="glass-panel data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>REF / REG NO</th>
                  <th>REGION</th>
                  <th>DATE</th>
                  <th>NAME / CONTACT PERSON</th>
                  <th>ADDRESS</th>
                  <th>PINCODE</th>
                  <th>CATEGORY</th>
                  <th>VARIANT / MODEL</th>
                  <th>MOBILE / CONTACT</th>
                  <th>SOURCE SHEET</th>
                  <th style={{ textAlign: 'center' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={11} style={{ textAlign: 'center', padding: '40px' }}>
                      <div className="spinner" style={{ margin: '0 auto 12px' }}></div>
                      <span style={{ color: 'var(--text-secondary)' }}>Executing instant search across DuckDB records...</span>
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={11} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                      No matching records found in database. Upload Excel files via the <strong>Ingest Data</strong> tab to get started.
                    </td>
                  </tr>
                ) : (
                  records.map((rec) => (
                    <tr key={rec.id}>
                      <td><strong>{rec.reg_no || '-'}</strong></td>
                      <td><span className="badge badge-rto">{rec.rto || '-'}</span></td>
                      <td>{rec.reg_date || '-'}</td>
                      <td><strong>{rec.name || '-'}</strong></td>
                      <td title={rec.address}>{rec.address || '-'}</td>
                      <td><span className="badge badge-pincode">{rec.pincode || '-'}</span></td>
                      <td><span className="badge badge-brand">{rec.make || '-'}</span></td>
                      <td>{rec.model_variant || '-'}</td>
                      <td><span style={{ color: 'var(--primary)', fontWeight: 600 }}>{rec.mobile || '-'}</span></td>
                      <td><span className="badge badge-sheet">{rec.source_sheet || '-'}</span></td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
                          <button className="btn btn-secondary btn-sm" onClick={() => openEditModal(rec)} title="Edit Record">
                            <Edit2 size={14} />
                          </button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(rec.id)} title="Delete Record">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination Controls */}
            <div className="pagination-bar">
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Showing <strong>{records.length > 0 ? (page - 1) * limit + 1 : 0}</strong> to <strong>{Math.min(page * limit, totalRecords)}</strong> of <strong>{totalRecords.toLocaleString()}</strong> matching records
              </div>

              <div className="page-controls">
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={page <= 1}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={16} /> Prev
                </button>
                <span style={{ fontSize: '0.88rem', padding: '0 8px' }}>
                  Page <strong>{page}</strong> of {totalPages}
                </span>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* TAB 2: INGEST DATA */}
      {activeTab === 'import' && (
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ marginBottom: '8px', fontSize: '1.4rem' }}>Ingest Excel & Data Files</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
            Drag & drop single or multiple Excel files (`.xlsx`, `.xls`, `.csv`) containing multiple sheets. The DuckDB engine automatically parses, normalizes headers, and combines them into an ultra-fast queryable database.
          </p>

          <div
            className="dropzone-container"
            onClick={() => document.getElementById('excel-file-input').click()}
          >
            <input
              id="excel-file-input"
              type="file"
              multiple
              accept=".xlsx,.xls,.csv"
              style={{ display: 'none' }}
              onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
            />
            <div className="dropzone-icon">
              <UploadCloud size={32} />
            </div>
            <h3>Click to Browse or Drag & Drop Data Files Here</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '6px' }}>
              Supports Excel Workbooks with multiple sheets (.xlsx, .xls, .csv)
            </p>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div style={{ marginTop: '24px' }}>
              <h4 style={{ marginBottom: '12px' }}>Selected Files for Ingestion ({selectedFiles.length}):</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedFiles.map((file, idx) => (
                  <div key={idx} className="glass-panel" style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <FileSpreadsheet color="var(--success)" size={22} />
                      <div>
                        <strong>{file.name}</strong>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {(file.size / (1024 * 1024)).toFixed(2)} MB
                        </div>
                      </div>
                    </div>
                    <button
                      className="clear-search-btn"
                      disabled={uploading}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFiles(selectedFiles.filter((_, i) => i !== idx));
                      }}
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
                <button
                  className="btn btn-primary"
                  disabled={uploading}
                  onClick={() => handleFileUpload()}
                >
                  {uploading ? (
                    <>
                      <div className="spinner"></div> Ingesting Data ({uploadPercent}%)...
                    </>
                  ) : (
                    <>
                      <UploadCloud size={18} /> Start Ingestion ({selectedFiles.length} files)
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* REAL-TIME PROGRESS BAR & PERCENTAGE BADGE */}
          {(uploading || uploadStatus !== 'idle') && (
            <div style={{ marginTop: '28px', padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #cbd5e1', boxShadow: 'var(--shadow-md)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {uploadStatus === 'completed' ? (
                    <CheckCircle size={24} color="var(--success)" />
                  ) : uploadStatus === 'error' ? (
                    <AlertCircle size={24} color="var(--danger)" />
                  ) : (
                    <div className="spinner" style={{ width: '22px', height: '22px' }}></div>
                  )}
                  <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                    {uploadStatus === 'completed' ? 'Ingestion Complete!' : uploadStatus === 'error' ? 'Ingestion Failed' : 'Ingesting Data into DuckDB...'}
                  </span>
                </div>

                <span style={{
                  fontWeight: 800,
                  fontSize: '1.1rem',
                  color: uploadStatus === 'completed' ? 'var(--success)' : 'var(--primary)',
                  background: uploadStatus === 'completed' ? '#f0fdf4' : '#eff6ff',
                  padding: '4px 14px',
                  borderRadius: '20px',
                  border: uploadStatus === 'completed' ? '1px solid #bbf7d0' : '1px solid #bfdbfe'
                }}>
                  {uploadPercent}%
                </span>
              </div>

              {/* Animated Progress Bar Track & Fill */}
              <div style={{ height: '12px', background: '#e2e8f0', borderRadius: '6px', overflow: 'hidden', marginBottom: '12px' }}>
                <div style={{
                  height: '100%',
                  width: `${uploadPercent}%`,
                  background: uploadStatus === 'completed' ? 'var(--success)' : uploadStatus === 'error' ? 'var(--danger)' : 'linear-gradient(90deg, var(--primary), var(--accent))',
                  borderRadius: '6px',
                  transition: 'width 0.35s ease-in-out'
                }}></div>
              </div>

              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', fontWeight: 500 }}>
                {uploadMessage || 'Processing data rows...'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: ANALYTICS */}
      {activeTab === 'stats' && stats && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* Top Categories */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Tag color="var(--primary)" size={20} /> Top Categories / Brands
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {stats.top_makes.map(m => (
                  <div key={m.make}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '4px' }}>
                      <span><strong>{m.make}</strong></span>
                      <span style={{ color: 'var(--text-secondary)' }}>{m.count.toLocaleString()} records</span>
                    </div>
                    <div style={{ height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${Math.min(100, (m.count / stats.total_records) * 100 * 3)}%`,
                        background: 'linear-gradient(90deg, var(--primary), var(--accent))',
                        borderRadius: '4px'
                      }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Pincodes */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <MapPin color="var(--success)" size={20} /> Top Location / Regional Clusters
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {stats.top_pincodes.map(p => (
                  <div key={p.pincode}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '4px' }}>
                      <span><strong>Location / Pincode {p.pincode}</strong></span>
                      <span style={{ color: 'var(--text-secondary)' }}>{p.count.toLocaleString()} entries</span>
                    </div>
                    <div style={{ height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${Math.min(100, (p.count / stats.total_records) * 100 * 3)}%`,
                        background: 'linear-gradient(90deg, var(--success), #34d399)',
                        borderRadius: '4px'
                      }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Database Reset Action Panel */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff1f2', border: '1px solid #fecdd3' }}>
            <div>
              <h4 style={{ color: '#9f1239', fontSize: '1.05rem', marginBottom: '4px' }}>Clear Database & Purge All Records</h4>
              <p style={{ color: '#991b1b', fontSize: '0.85rem' }}>Wipe all ingested records from the database file to start fresh.</p>
            </div>
            <button className="btn btn-danger" onClick={handleClearAll}>
              <Trash2 size={16} /> Purge All Data
            </button>
          </div>
        </div>
      )}

      {/* CREATE / EDIT MODAL */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingRecord ? 'Edit Record Details' : 'Add New Data Record'}</h3>
              <button className="clear-search-btn" onClick={() => setShowAddModal(false)}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleFormSubmit}>
              <div className="modal-grid">
                <div className="form-group">
                  <label>Reference / Reg Number</label>
                  <input
                    type="text"
                    value={formData.reg_no}
                    onChange={(e) => setFormData({ ...formData, reg_no: e.target.value })}
                    placeholder="e.g. REF-109480"
                  />
                </div>

                <div className="form-group">
                  <label>Region / Code</label>
                  <input
                    type="text"
                    value={formData.rto}
                    onChange={(e) => setFormData({ ...formData, rto: e.target.value })}
                    placeholder="e.g. REG-01"
                  />
                </div>

                <div className="form-group">
                  <label>Date / Period</label>
                  <input
                    type="text"
                    value={formData.reg_date}
                    onChange={(e) => setFormData({ ...formData, reg_date: e.target.value })}
                    placeholder="e.g. 2024-01-15"
                  />
                </div>

                <div className="form-group">
                  <label>Contact Name / Title</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Full Name / Person Name"
                  />
                </div>

                <div className="form-group full-width">
                  <label>Full Address / Location</label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Street, Suite, Area Address"
                  />
                </div>

                <div className="form-group">
                  <label>Pincode / Postal Code</label>
                  <input
                    type="text"
                    value={formData.pincode}
                    onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                    placeholder="e.g. 411033"
                  />
                </div>

                <div className="form-group">
                  <label>Category / Brand</label>
                  <input
                    type="text"
                    value={formData.make}
                    onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                    placeholder="e.g. CATEGORY A"
                  />
                </div>

                <div className="form-group">
                  <label>Model / Variant</label>
                  <input
                    type="text"
                    value={formData.model_variant}
                    onChange={(e) => setFormData({ ...formData, model_variant: e.target.value })}
                    placeholder="e.g. Standard Spec"
                  />
                </div>

                <div className="form-group">
                  <label>Mobile / Contact Number</label>
                  <input
                    type="text"
                    value={formData.mobile}
                    onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                    placeholder="e.g. +91 9876543210"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingRecord ? 'Update Record' : 'Save Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
