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
      await Promise.all([
        this.loadOverview(),
        this.loadExpiring(),
        this.loadArchived(),
        this.loadPaused(),
        this.loadAudit()
      ])
    },
    authHeaders() {
      const token = localStorage.getItem('access_token')
      return token ? { Authorization: `Bearer ${token}` } : {}
    },
    async loadOverview() {
      const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/overview`, {
        headers: this.authHeaders()
      })
      if (res.data?.status === 'success') {
        this.overview = res.data.data
      }
    },
    async loadExpiring() {
      const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/expiring`, {
        params: { days: this.expiringDays, limit: 100 },
        headers: this.authHeaders()
      })
      if (res.data?.status === 'success') {
        this.expiring = res.data.data || []
      }
    },
    async loadArchived() {
      const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/archived`, {
        params: { limit: 100 },
        headers: this.authHeaders()
      })
      if (res.data?.status === 'success') {
        this.archived = res.data.data || []
      }
    },
    async loadPaused() {
      const res = await axios.get(`${API_BASE_URL}/api/retention/dashboard/paused`, {
        params: { limit: 100 },
        headers: this.authHeaders()
      })
      if (res.data?.status === 'success') {
        this.paused = res.data.data || []
      }
    },
    async loadAudit() {
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
  margin-left: 220px; /* offset for sidebar */
  width: calc(100% - 220px);
  box-sizing: border-box;
}
@media (max-width: 1024px) {
  .page-layout {
    margin-left: 0;
    width: 100%;
  }
}
.retention-dashboard {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.page-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  border: none;
  font-size: 13px;
  padding: 6px 14px;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.1s ease;
}

.btn i {
  font-size: 12px;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-ghost {
  background: transparent;
  color: #374151;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.btn-xs {
  padding: 3px 8px;
  font-size: 11px;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(15, 23, 42, 0.18);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-refresh-all {
  white-space: nowrap;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin: 12px 0 24px;
}
.card {
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
}
.card-label {
  font-size: 13px;
  color: #6b7280;
}
.card-value {
  font-size: 22px;
  font-weight: 600;
  color: #111827;
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.card-bar-track {
  position: relative;
  height: 6px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.card-bar-fill {
  position: absolute;
  inset: 0;
  width: 0;
  border-radius: 999px;
  transition: width 0.35s ease;
}

.card-bar-fill.state-active {
  background: #22c55e;
}

.card-bar-fill.state-expiring {
  background: #f97316;
}

.card-bar-fill.state-archived {
  background: #6366f1;
}

.card-bar-fill.state-paused {
  background: #eab308;
}

.card-bar-fill.state-disposed {
  background: #6b7280;
}
.section {
  margin-bottom: 24px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.controls {
  display: flex;
  gap: 8px;
  align-items: center;
}
.controls input {
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}
.controls button {
  padding: 6px 12px;
  border: none;
  background: #2563eb;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
}
.controls button:hover {
  background: #1d4ed8;
}
.table-scroll {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 10px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}
th {
  text-align: left;
  background: #f3f4f6;
  color: #374151;
}
.empty {
  color: #6b7280;
  font-size: 14px;
  padding: 8px 0;
}
.two-col {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}
</style>

