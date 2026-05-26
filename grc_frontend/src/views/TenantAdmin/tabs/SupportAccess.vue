<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Support Access</h3>
      <button class="btn btn-primary btn-sm" @click="showForm = true">
        <i class="fas fa-plus"></i> Request Access
      </button>
    </div>

    <div class="section-tabs">
      <button class="stab" :class="{ active: view === 'pending' }" @click="view = 'pending'">Pending Requests</button>
      <button class="stab" :class="{ active: view === 'history' }" @click="view = 'history'">Access History</button>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>

    <table v-else class="data-table">
      <thead>
        <tr><th>Support User</th><th>Reason</th><th>Requested</th><th>Status</th><th>Valid Until</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-if="!filteredRequests.length">
          <td colspan="6" class="empty-row">No requests found</td>
        </tr>
        <tr v-for="req in filteredRequests" :key="req.id">
          <td>{{ req.support_user_name || req.support_user }}</td>
          <td class="reason-cell">{{ req.request_reason }}</td>
          <td>{{ fmtDate(req.requested_at) }}</td>
          <td>
            <span class="badge" :class="statusClass(req.status)">{{ req.status }}</span>
          </td>
          <td>{{ fmtDate(req.valid_to) || '—' }}</td>
          <td class="actions-cell">
            <button
              v-if="req.status === 'pending'"
              class="icon-btn text-success"
              title="Approve"
              @click="approveRequest(req)"
            ><i class="fas fa-check"></i></button>
            <button
              v-if="req.status === 'approved'"
              class="icon-btn text-danger"
              title="Revoke"
              @click="revokeRequest(req)"
            ><i class="fas fa-ban"></i></button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-card">
        <h3 class="modal-title">Request Support Access</h3>
        <div class="form-group">
          <label class="form-label">Reason <span class="req">*</span></label>
          <textarea v-model="form.request_reason" class="form-control" rows="3" placeholder="Describe the reason for support access..."></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Access Duration (hours)</label>
          <input v-model.number="form.duration_hours" type="number" class="form-control" placeholder="24" min="1" max="168" />
        </div>
        <div v-if="formError" class="alert-error">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showForm = false">Cancel</button>
          <button class="btn btn-primary" @click="submitRequest" :disabled="saving">
            <i v-if="saving" class="fas fa-spinner fa-spin"></i> Submit
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
export default {
  name: 'SupportAccessTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      requests: [], loading: false, view: 'pending',
      showForm: false, saving: false, formError: null,
      form: { request_reason: '', duration_hours: 24 },
    }
  },
  computed: {
    filteredRequests() {
      if (this.view === 'pending') return this.requests.filter((r) => r.status === 'pending')
      return this.requests.filter((r) => r.status !== 'pending')
    },
  },
  mounted() { this.fetchRequests() },
  methods: {
    async fetchRequests() {
      this.loading = true
      try {
        const res = await tenantService.listSupportRequests(this.tenant.tenant_id)
        this.requests = res?.data?.requests ?? res?.data ?? []
      } catch (e) { console.warn(e) } finally { this.loading = false }
    },
    async approveRequest(req) {
      try { await tenantService.approveSupportRequest(req.id); await this.fetchRequests() } catch (e) { alert(e.message) }
    },
    async revokeRequest(req) {
      if (!confirm('Revoke this support access?')) return
      try { await tenantService.revokeSupportRequest(req.id); await this.fetchRequests() } catch (e) { alert(e.message) }
    },
    async submitRequest() {
      this.saving = true; this.formError = null
      try {
        await tenantService.requestSupportAccess({ ...this.form, tenant_id: this.tenant.tenant_id })
        this.showForm = false; this.form = { request_reason: '', duration_hours: 24 }
        await this.fetchRequests()
      } catch (e) { this.formError = e.message } finally { this.saving = false }
    },
    statusClass(s) {
      return { pending: 'badge-warning', approved: 'badge-success', revoked: 'badge-danger', expired: 'badge-neutral' }[s] || 'badge-neutral'
    },
    fmtDate(dt) { return dt ? new Date(dt).toLocaleDateString() : null },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.section-tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #eee; }
.stab { background: none; border: none; border-bottom: 3px solid transparent; padding: 8px 16px; cursor: pointer; font-size: 14px; font-weight: 600; color: #777; margin-bottom: -2px; }
.stab.active { color: #3f51b5; border-bottom-color: #3f51b5; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 11px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.reason-cell { max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.badge { padding: 3px 9px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-warning { background: #fff3e0; color: #e65100; }
.badge-danger { background: #ffebee; color: #c62828; }
.badge-neutral { background: #f5f5f5; color: #666; }
.actions-cell { display: flex; gap: 6px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 5px; border-radius: 5px; font-size: 14px; color: #555; }
.icon-btn:hover { background: #f0f0f0; }
.icon-btn.text-success { color: #2e7d32; }
.icon-btn.text-danger { color: #c62828; }
.loading-state, .empty-row { padding: 28px; text-align: center; color: #999; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: #fff; border-radius: 12px; padding: 28px; width: 440px; }
.modal-title { font-size: 17px; font-weight: 700; margin: 0 0 20px; }
.form-group { margin-bottom: 14px; }
.form-label { font-size: 13px; font-weight: 600; color: #444; display: block; margin-bottom: 5px; }
.req { color: #e53935; }
.form-control { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.form-control:focus { border-color: #3f51b5; outline: none; }
.alert-error { background: #ffebee; color: #c62828; border-radius: 6px; padding: 10px 14px; font-size: 13px; margin-bottom: 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-outline { background: transparent; border: 1px solid #ccc; color: #555; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
</style>
