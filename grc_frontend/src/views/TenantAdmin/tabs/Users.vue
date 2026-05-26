<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">User Mappings</h3>
      <button class="btn btn-primary btn-sm" @click="showForm = true">
        <i class="fas fa-user-plus"></i> Map User
      </button>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>
    <div v-else-if="error" class="error-state"><i class="fas fa-exclamation-circle"></i> {{ error }}</div>

    <table v-else class="data-table">
      <thead>
        <tr><th>User</th><th>Role</th><th>Primary</th><th>Status</th><th>Assigned</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-if="!users.length"><td colspan="6" class="empty-row">No users mapped to this tenant</td></tr>
        <tr v-for="u in users" :key="u.id">
          <td>
            <div class="user-cell">
              <span class="user-avatar">{{ initials(u.user_name || u.username) }}</span>
              <div>
                <div class="user-name">{{ u.user_name || u.username }}</div>
                <div class="user-email">{{ u.user_email || u.email }}</div>
              </div>
            </div>
          </td>
          <td>{{ u.role }}</td>
          <td>
            <span v-if="u.is_primary" class="badge badge-primary">Primary</span>
            <span v-else class="badge badge-neutral">No</span>
          </td>
          <td><span class="badge" :class="u.status === 'active' ? 'badge-success' : 'badge-neutral'">{{ u.status }}</span></td>
          <td>{{ fmtDate(u.assigned_at) }}</td>
          <td class="actions-cell">
            <button v-if="!u.is_primary" class="icon-btn text-primary" title="Set Primary" @click="setPrimary(u)">
              <i class="fas fa-star"></i>
            </button>
            <button class="icon-btn text-danger" title="Remove" @click="unmapUser(u)">
              <i class="fas fa-user-minus"></i>
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-card">
        <h3 class="modal-title">Map User to Tenant</h3>
        <div class="form-group">
          <label class="form-label">User ID <span class="req">*</span></label>
          <input v-model="form.user_id" class="form-control" type="number" placeholder="Enter user ID" />
        </div>
        <div class="form-group">
          <label class="form-label">Role <span class="req">*</span></label>
          <select v-model="form.role" class="form-control">
            <option value="">Select role</option>
            <option value="GRC Administrator">GRC Administrator</option>
            <option value="Compliance Manager">Compliance Manager</option>
            <option value="Auditor">Auditor</option>
            <option value="Risk Manager">Risk Manager</option>
            <option value="Viewer">Viewer</option>
          </select>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.is_primary" />
            Set as primary tenant for this user
          </label>
        </div>
        <div v-if="formError" class="alert-error">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showForm = false">Cancel</button>
          <button class="btn btn-primary" @click="mapUser" :disabled="saving">
            <i v-if="saving" class="fas fa-spinner fa-spin"></i> Map User
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
export default {
  name: 'UsersTab',
  props: { tenant: { type: Object, required: true } },
  computed: {
    tenantId() { return this.tenant?.tenant_id ?? this.tenant?.id }
  },
  data() {
    return {
      users: [], loading: false, error: null,
      showForm: false, saving: false, formError: null,
      form: { user_id: '', role: '', is_primary: false },
    }
  },
  mounted() { this.fetchUsers() },
  methods: {
    async fetchUsers() {
      this.loading = true; this.error = null
      try {
        const res = await tenantService.listTenantUsers(this.tenantId)
        this.users = res?.data?.users ?? []
      } catch (e) { this.error = e.message } finally { this.loading = false }
    },
    async mapUser() {
      this.saving = true; this.formError = null
      try {
        await tenantService.mapUserToTenant(this.tenantId, this.form)
        this.showForm = false; this.form = { user_id: '', role: '', is_primary: false }
        await this.fetchUsers()
      } catch (e) { this.formError = e.message } finally { this.saving = false }
    },
    async unmapUser(u) {
      if (!confirm(`Remove ${u.user_name || u.username} from this tenant?`)) return
      try { await tenantService.unmapUserFromTenant(this.tenant.tenant_id, u.user_id ?? u.id); await this.fetchUsers() } catch (e) { alert(e.message) }
    },
    async setPrimary(u) {
      try { await tenantService.setPrimaryUser(this.tenant.tenant_id, u.user_id ?? u.id); await this.fetchUsers() } catch (e) { alert(e.message) }
    },
    initials(name) {
      if (!name) return '?'
      return name.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase()
    },
    fmtDate(dt) { return dt ? new Date(dt).toLocaleDateString() : '—' },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 12px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.user-cell { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 34px; height: 34px; border-radius: 50%; background: #e8eaf6; color: #3f51b5; font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.user-name { font-weight: 600; font-size: 14px; }
.user-email { font-size: 12px; color: #888; }
.badge { padding: 3px 9px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-primary { background: #e8eaf6; color: #3f51b5; }
.badge-neutral { background: #f5f5f5; color: #666; }
.actions-cell { display: flex; gap: 6px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 5px; border-radius: 5px; color: #555; font-size: 14px; }
.icon-btn:hover { background: #f0f0f0; }
.icon-btn.text-danger { color: #c62828; }
.icon-btn.text-primary { color: #3f51b5; }
.loading-state, .error-state, .empty-row { padding: 28px; text-align: center; color: #999; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: #fff; border-radius: 12px; padding: 28px; width: 420px; }
.modal-title { font-size: 17px; font-weight: 700; margin: 0 0 20px; }
.form-group { margin-bottom: 14px; }
.form-label { font-size: 13px; font-weight: 600; color: #444; display: block; margin-bottom: 5px; }
.req { color: #e53935; }
.form-control { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
.alert-error { background: #ffebee; color: #c62828; border-radius: 6px; padding: 10px 14px; font-size: 13px; margin-bottom: 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-outline { background: transparent; border: 1px solid #ccc; color: #555; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
</style>
