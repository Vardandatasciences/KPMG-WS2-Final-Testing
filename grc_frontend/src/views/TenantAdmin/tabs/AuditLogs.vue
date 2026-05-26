<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Audit Logs</h3>
      <div class="header-controls">
        <select v-model="actionFilter" class="form-control filter-select" @change="fetchLogs">
          <option value="">All Actions</option>
          <option v-for="a in actionTypes" :key="a" :value="a">{{ a }}</option>
        </select>
        <button class="btn btn-outline btn-sm" @click="fetchLogs">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading logs...</div>
    <div v-else-if="error" class="error-state"><i class="fas fa-exclamation-circle"></i> {{ error }}</div>

    <table v-else class="data-table">
      <thead>
        <tr><th>Action</th><th>Entity</th><th>Performed By</th><th>IP Address</th><th>Timestamp</th><th>Details</th></tr>
      </thead>
      <tbody>
        <tr v-if="!logs.length"><td colspan="6" class="empty-row">No audit logs found</td></tr>
        <tr v-for="log in logs" :key="log.id">
          <td>
            <span class="action-badge" :class="`action-${(log.action_type || '').toLowerCase()}`">
              {{ log.action_type }}
            </span>
          </td>
          <td>
            <div class="entity-cell">
              <span class="entity-type">{{ log.entity_type }}</span>
              <span class="entity-name">{{ log.entity_name }}</span>
            </div>
          </td>
          <td>{{ log.performed_by_name || log.performed_by }}</td>
          <td><code>{{ log.ip_address || '—' }}</code></td>
          <td>{{ fmtDateTime(log.performed_at) }}</td>
          <td>
            <button class="icon-btn" @click="showDetails(log)"><i class="fas fa-eye"></i></button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="selectedLog" class="modal-overlay" @click.self="selectedLog = null">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">Audit Log Details</h3>
          <button class="close-btn" @click="selectedLog = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="detail-row" v-for="(val, key) in logDetails" :key="key">
          <span class="detail-key">{{ key }}</span>
          <span class="detail-val">{{ val }}</span>
        </div>
        <div class="changes-section" v-if="selectedLog.new_value">
          <h4>Changes</h4>
          <div class="changes-grid">
            <div>
              <div class="change-label">Before</div>
              <pre class="change-pre">{{ JSON.stringify(selectedLog.old_value, null, 2) }}</pre>
            </div>
            <div>
              <div class="change-label">After</div>
              <pre class="change-pre">{{ JSON.stringify(selectedLog.new_value, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
export default {
  name: 'AuditLogsTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      logs: [], loading: false, error: null,
      actionFilter: '', selectedLog: null,
      actionTypes: ['CREATE', 'UPDATE', 'DELETE', 'ACTIVATE', 'SUSPEND', 'ARCHIVE', 'MAP_USER', 'UNMAP_USER', 'ENABLE_MODULE', 'DISABLE_MODULE'],
    }
  },
  computed: {
    tenantId() { return this.tenant?.tenant_id ?? this.tenant?.id },
    logDetails() {
      if (!this.selectedLog) return {}
      return {
        'Action': this.selectedLog.action_type,
        'Entity Type': this.selectedLog.entity_type,
        'Entity Name': this.selectedLog.entity_name,
        'Performed By': this.selectedLog.performed_by_name,
        'IP Address': this.selectedLog.ip_address || '—',
        'Timestamp': this.fmtDateTime(this.selectedLog.performed_at),
        'User Agent': this.selectedLog.user_agent || '—',
      }
    },
  },
  mounted() { this.fetchLogs() },
  methods: {
    async fetchLogs() {
      this.loading = true; this.error = null
      try {
        const params = this.actionFilter ? { action_type: this.actionFilter } : {}
        const res = await tenantService.getTenantAuditLogs(this.tenantId, params)
        this.logs = res?.data?.audit_logs ?? res?.data?.logs ?? res?.data ?? []
      } catch (e) { this.error = e.message } finally { this.loading = false }
    },
    showDetails(log) { this.selectedLog = log },
    fmtDateTime(dt) { return dt ? new Date(dt).toLocaleString() : '—' },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; gap: 10px; flex-wrap: wrap; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.header-controls { display: flex; gap: 10px; }
.filter-select { padding: 7px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 11px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.action-badge { padding: 3px 9px; border-radius: 4px; font-size: 11px; font-weight: 700; font-family: monospace; text-transform: uppercase; background: #f0f0f0; color: #555; }
.action-create { background: #e8f5e9; color: #2e7d32; }
.action-update { background: #e3f2fd; color: #1565c0; }
.action-delete { background: #ffebee; color: #c62828; }
.action-activate { background: #e8f5e9; color: #2e7d32; }
.action-suspend { background: #fff3e0; color: #e65100; }
.action-archive { background: #efebe9; color: #4e342e; }
.entity-cell { display: flex; flex-direction: column; gap: 2px; }
.entity-type { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
.entity-name { font-size: 13px; color: #333; font-weight: 500; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 5px; border-radius: 5px; color: #555; font-size: 14px; }
.icon-btn:hover { background: #f0f0f0; }
.loading-state, .error-state, .empty-row { padding: 28px; text-align: center; color: #999; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: #fff; border-radius: 12px; padding: 28px; width: 560px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-title { font-size: 17px; font-weight: 700; margin: 0; }
.close-btn { background: none; border: none; cursor: pointer; font-size: 16px; color: #666; }
.detail-row { display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
.detail-key { width: 130px; color: #888; font-weight: 500; flex-shrink: 0; }
.detail-val { color: #333; }
.changes-section { margin-top: 16px; }
.changes-section h4 { font-size: 14px; font-weight: 700; color: #3f51b5; margin-bottom: 12px; }
.changes-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.change-label { font-size: 12px; font-weight: 600; color: #666; margin-bottom: 6px; }
.change-pre { background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 12px; overflow: auto; max-height: 200px; margin: 0; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-outline { background: transparent; border: 1px solid #ccc; color: #555; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
</style>
