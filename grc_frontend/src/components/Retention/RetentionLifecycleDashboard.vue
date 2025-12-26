<template>
  <div class="retention-dashboard page-layout">
      <header class="page-header">
        <div>
          <h2>Data Retention Lifecycle</h2>
          <p class="page-subtitle">
            Monitor records approaching end-of-life, manage holds and archives, and review lifecycle audit activity.
          </p>
        </div>
      </header>
  
      <div class="cards">
        <div class="card" v-for="card in overviewCards" :key="card.label">
          <div class="card-top">
            <div class="card-label">{{ card.label }}</div>
            <div class="card-value">{{ card.value }}</div>
          </div>
          <div class="card-bar-track">
            <div
              class="card-bar-fill"
              :class="'state-' + card.label.toLowerCase()"
              :style="{ width: overviewPercent(card.value) + '%' }"
            ></div>
          </div>
        </div>
      </div>
  
      <section class="section">
        <header class="section-header">
          <h3>Expiring Records</h3>
          <div class="controls">
            <label>
              Days:
              <input type="number" v-model.number="expiringDays" min="1" max="365" />
            </label>
            <button class="btn btn-secondary btn-sm" @click="loadExpiring">
              <i class="fas fa-sync-alt"></i>
              <span>Refresh</span>
            </button>
          </div>
        </header>
        <div class="table-scroll" v-if="expiring.length">
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>ID</th>
                <th>Name</th>
                <th>Status</th>
                <th>End Date</th>
                <th>Days Left</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in expiring" :key="item.id">
                <td>{{ item.record_type }}</td>
                <td>{{ item.record_id }}</td>
                <td>{{ item.record_name || '-' }}</td>
                <td>{{ item.status }}</td>
                <td>{{ formatDate(item.retention_end_date) }}</td>
                <td>{{ item.days_until_expiry ?? '-' }}</td>
                <td class="actions">
                  <button class="btn btn-ghost btn-xs" @click="archive(item.id)">
                    <i class="fas fa-archive"></i>
                    <span>Archive</span>
                  </button>
                  <button class="btn btn-ghost btn-xs" @click="pause(item.id)">
                    <i class="fas fa-pause-circle"></i>
                    <span>Pause</span>
                  </button>
                  <button class="btn btn-ghost btn-xs" @click="extend(item.id, 30)">
                    <i class="fas fa-clock"></i>
                    <span>+30d</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="empty">No expiring records.</p>
      </section>
  
      <section class="section two-col">
        <div>
          <header class="section-header">
            <h3>Archived</h3>
            <button class="btn btn-secondary btn-sm" @click="loadArchived">
              <i class="fas fa-sync-alt"></i>
              <span>Refresh</span>
            </button>
          </header>
          <div class="table-scroll" v-if="archived.length">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Archived Date</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in archived" :key="item.id">
                  <td>{{ item.record_type }}</td>
                  <td>{{ item.record_id }}</td>
                  <td>{{ item.record_name || '-' }}</td>
                  <td>{{ formatDate(item.archived_date) }}</td>
                  <td>{{ item.archive_location || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty">No archived records.</p>
        </div>
  
        <div>
          <header class="section-header">
            <h3>Paused Deletions</h3>
            <button class="btn btn-secondary btn-sm" @click="loadPaused">
              <i class="fas fa-sync-alt"></i>
              <span>Refresh</span>
            </button>
          </header>
          <div class="table-scroll" v-if="paused.length">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>ID</th>
                  <th>Reason</th>
                  <th>Until</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in paused" :key="item.id">
                  <td>{{ item.record_type }}</td>
                  <td>{{ item.record_id }}</td>
                  <td>{{ item.pause_reason || '-' }}</td>
                  <td>{{ formatDate(item.pause_until) }}</td>
                  <td class="actions">
                    <button class="btn btn-ghost btn-xs" @click="resume(item.id)">
                      <i class="fas fa-play-circle"></i>
                      <span>Resume</span>
                    </button>
                    <button class="btn btn-ghost btn-xs" @click="archive(item.id)">
                      <i class="fas fa-archive"></i>
                      <span>Archive</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="empty">No paused deletions.</p>
        </div>
      </section>
  
      <section class="section">
        <header class="section-header">
          <h3>Audit Trail</h3>
          <div class="controls">
            <input v-model="auditRecordType" placeholder="record_type (optional)" />
            <input v-model="auditRecordId" placeholder="record_id (optional)" />
            <button class="btn btn-secondary btn-sm" @click="loadAudit">
              <i class="fas fa-sync-alt"></i>
              <span>Refresh</span>
            </button>
          </div>
        </header>
        <div class="table-scroll" v-if="auditLogs.length">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Type</th>
                <th>ID</th>
                <th>Name</th>
                <th>Before</th>
                <th>After</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in auditLogs" :key="log.id">
                <td>{{ formatDateTime(log.timestamp) }}</td>
                <td>{{ log.action_type }}</td>
                <td>{{ log.record_type }}</td>
                <td>{{ log.record_id }}</td>
                <td>{{ log.record_name || '-' }}</td>
                <td>{{ log.before_status || '-' }}</td>
                <td>{{ log.after_status || '-' }}</td>
                <td>{{ log.reason || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="empty">No audit entries.</p>
      </section>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  import { API_BASE_URL } from '@/config/api.js'
  
  export default {
    name: 'RetentionLifecycleDashboard',
    data() {
      return {
        overview: { active: 0, expiring: 0, archived: 0, paused: 0, disposed: 0 },
        expiring: [],
        archived: [],
        paused: [],
        auditLogs: [],
        expiringDays: 30,
        auditRecordType: '',
        auditRecordId: '',
        loadingAction: false,
      }
    },
    computed: {
      overviewCards() {
        return [
          { label: 'Active', value: this.overview.active },
          { label: 'Expiring', value: this.overview.expiring },
          { label: 'Archived', value: this.overview.archived },
          { label: 'Paused', value: this.overview.paused },
          { label: 'Disposed', value: this.overview.disposed },
        ]
      },
      maxOverviewValue() {
        const values = Object.values(this.overview || {})
        const max = Math.max(0, ...values)
        return max || 1
      }
    },
    mounted() {
      this.loadAll()
    },
    methods: {
      async apiPost(url, payload) {
        this.loadingAction = true
        try {
          const res = await axios.post(url, payload, { headers: this.authHeaders() })
          return res.data
        } finally {
          this.loadingAction = false
        }
      },
      async archive(timelineId) {
        await this.apiPost(`${API_BASE_URL}/api/retention/archive/`, {
          retention_timeline_id: timelineId,
          archived_by: localStorage.getItem('user_id'),
        })
        await this.loadAll()
      },
      async pause(timelineId) {
        await this.apiPost(`${API_BASE_URL}/api/retention/pause-deletion/`, {
          retention_timeline_id: timelineId,
          reason: 'Paused from dashboard',
          performed_by: localStorage.getItem('user_id'),
        })
        await this.loadAll()
      },
      async resume(timelineId) {
        await this.apiPost(`${API_BASE_URL}/api/retention/resume-deletion/`, {
          retention_timeline_id: timelineId,
          performed_by: localStorage.getItem('user_id'),
        })
        await this.loadAll()
      },
      async extend(timelineId, days) {
        await this.apiPost(`${API_BASE_URL}/api/retention/extend/`, {
          retention_timeline_id: timelineId,
          extra_days: days,
          performed_by: localStorage.getItem('user_id'),
        })
        await this.loadAll()
      },
      async loadAll() {
        try {
          await Promise.all([
            this.loadOverview(),
            this.loadExpiring(),
            this.loadArchived(),
            this.loadPaused(),
            this.loadAudit()
          ])
        } catch (error) {
          // Prevent unhandled promise rejections from breaking the app / dev overlay
          // and surface a concise console message instead.
          console.error('Error loading retention dashboard data:', error)
        }
      },
      authHeaders() {
        const token = localStorage.getItem('access_token')
        return token ? { Authorization: `Bearer ${token}` } : {}
      },
      async loadOverview() {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/overview`, {
            headers: this.authHeaders()
          })
          if (res.data?.status === 'success') {
            this.overview = res.data.data
          }
        } catch (error) {
          console.error('Error loading retention overview:', error)
        }
      },
      async loadExpiring() {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/expiring`, {
            params: { days: this.expiringDays, limit: 100 },
            headers: this.authHeaders()
          })
          if (res.data?.status === 'success') {
            this.expiring = res.data.data || []
          }
        } catch (error) {
          console.error('Error loading retention expiring data:', error)
        }
      },
      async loadArchived() {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/archived`, {
            params: { limit: 100 },
            headers: this.authHeaders()
          })
          if (res.data?.status === 'success') {
            this.archived = res.data.data || []
          }
        } catch (error) {
          console.error('Error loading retention archived data:', error)
        }
      },
      async loadPaused() {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/paused`, {
            params: { limit: 100 },
            headers: this.authHeaders()
          })
          if (res.data?.status === 'success') {
            this.paused = res.data.data || []
          }
        } catch (error) {
          console.error('Error loading retention paused data:', error)
        }
      },
      async loadAudit() {
        try {
          const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/audit-trail`, {
            params: {
              record_type: this.auditRecordType || undefined,
              record_id: this.auditRecordId || undefined,
              limit: 100
            },
            headers: this.authHeaders()
          })
          if (res.data?.status === 'success') {
            this.auditLogs = res.data.data || []
          }
        } catch (error) {
          console.error('Error loading retention audit log data:', error)
        }
      },
      overviewPercent(value) {
        const safe = typeof value === 'number' ? value : 0
        return Math.round((safe / this.maxOverviewValue) * 100)
      },
      formatDate(d) {
        if (!d) return '-'
        return new Date(d).toISOString().slice(0, 10)
      },
      formatDateTime(d) {
        if (!d) return '-'
        const dt = new Date(d)
        return dt.toISOString().replace('T', ' ').slice(0, 16)
      }
    }
  }
  </script>
  
  <style scoped>
  .page-layout {
    padding: 20px;
    margin-left: 230px; /* offset for sidebar */
    width: calc(100% - 230px);
    box-sizing: border-box;
    background: #f8fafc;
    min-height: 100vh;
  }
  @media (max-width: 1024px) {
    .page-layout {
      margin-left: 0;
      width: 100%;
      padding: 16px;
    }
  }
  .retention-dashboard {
    padding: 0;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 28px;
    gap: 16px;
  }
  
  .page-header h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
  }
  
  .page-subtitle {
    margin-top: 0;
    font-size: 14px;
    color: #64748b;
    line-height: 1.5;
  }
  
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 8px;
    border: none;
    font-size: 12px;
    font-weight: 500;
    padding: 7px 14px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    white-space: nowrap;
  }
  
  .btn i {
    font-size: 11px;
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: #fff;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
  }
  
  .btn-primary:hover:not(:disabled) {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
    transform: translateY(-1px);
  }
  
  .btn-secondary {
    background: #ffffff;
    color: #475569;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }
  
  .btn-secondary:hover:not(:disabled) {
    background: #f8fafc;
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  }
  
  .btn-ghost {
    background: transparent;
    color: #475569;
    border: 1px solid transparent;
    padding: 5px 10px;
  }
  
  .btn-ghost:hover:not(:disabled) {
    background: #f1f5f9;
    color: #334155;
    border-color: #e2e8f0;
  }
  
  .btn-sm {
    padding: 6px 12px;
    font-size: 11px;
  }
  
  .btn-xs {
    padding: 4px 8px;
    font-size: 10px;
  }
  
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
    transform: none;
  }
  
  .btn-refresh-all {
    white-space: nowrap;
  }
  
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin: 0 0 32px 0;
  }
  
  .card {
    background: linear-gradient(135deg, #ffffff, #f8fafc);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    border-color: #cbd5e1;
  }
  
  .card-label {
    font-size: 12px;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .card-value {
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1;
  }
  
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }
  
  .card-bar-track {
    position: relative;
    height: 4px;
    border-radius: 999px;
    background: #e2e8f0;
    overflow: hidden;
  }
  
  .card-bar-fill {
    position: absolute;
    inset: 0;
    width: 0;
    border-radius: 999px;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
  }
  
  .card-bar-fill.state-active {
    background: linear-gradient(90deg, #22c55e, #16a34a);
  }
  
  .card-bar-fill.state-expiring {
    background: linear-gradient(90deg, #f97316, #ea580c);
  }
  
  .card-bar-fill.state-archived {
    background: linear-gradient(90deg, #6366f1, #4f46e5);
  }
  
  .card-bar-fill.state-paused {
    background: linear-gradient(90deg, #eab308, #ca8a04);
  }
  
  .card-bar-fill.state-disposed {
    background: linear-gradient(90deg, #6b7280, #4b5563);
  }
  
  .section {
    margin-bottom: 24px;
    background: #ffffff;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    border: 1px solid #e2e8f0;
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 2px solid #f1f5f9;
  }
  
  .section-header h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
    letter-spacing: -0.01em;
  }
  
  .controls {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .controls label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
  }
  
  .controls input {
    padding: 6px 10px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 12px;
    width: 80px;
    transition: all 0.2s ease;
    background: #ffffff;
  }
  
  .controls input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  .controls input[type="text"] {
    width: 150px;
  }
  
  .table-scroll {
    overflow-x: auto;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  }
  
  .actions {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    justify-content: flex-start;
  }
  
  .actions .btn-xs {
    padding: 4px 7px;
    font-size: 9px;
  }
  
  .actions .btn-xs i {
    font-size: 10px;
    margin-right: 2px;
  }
  
  .actions .btn-xs span {
    font-size: 9px;
  }
  
  table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 10px;
    table-layout: auto;
  }
  
  th, td {
    padding: 6px 8px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 10px;
    text-align: left;
    line-height: 1.4;
  }
  
  th {
    background: linear-gradient(180deg, #f8fafc, #f1f5f9);
    color: #475569;
    font-weight: 600;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: 2px solid #e2e8f0;
    white-space: nowrap;
  }
  
  td {
    color: #334155;
    font-size: 10px;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  /* Allow wrapping for specific columns that might need it */
  td:nth-child(3), /* Name column */
  td:nth-child(5), /* Reason column */
  td:nth-child(8) { /* Reason column in audit */
    max-width: 200px;
    white-space: normal;
    word-break: break-word;
  }
  
  tbody tr {
    transition: background-color 0.15s ease;
  }
  
  tbody tr:hover {
    background-color: #f8fafc;
  }
  
  tbody tr:last-child td {
    border-bottom: none;
  }
  
  .empty {
    color: #94a3b8;
    font-size: 13px;
    padding: 24px;
    text-align: center;
    font-style: italic;
  }
  
  .two-col {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 16px;
  }
  
  @media (max-width: 768px) {
    .page-header h2 {
      font-size: 1.5rem;
    }
    
    .cards {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;
    }
    
    .card-value {
      font-size: 24px;
    }
    
    .two-col {
      grid-template-columns: 1fr;
      gap: 12px;
    }
    
    .section {
      padding: 12px;
    }
    
    th, td {
      padding: 5px 6px;
      font-size: 9px;
    }
    
    .section-header h3 {
      font-size: 1rem;
    }
  }
  
  /* Additional compact styles for better screen fit */
  @media (max-width: 1400px) {
    .page-layout {
      padding: 16px;
    }
    
    .section {
      padding: 14px;
    }
    
    th, td {
      padding: 5px 7px;
      font-size: 10px;
    }
    
    .two-col {
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 14px;
    }
  }
  </style>
  
  