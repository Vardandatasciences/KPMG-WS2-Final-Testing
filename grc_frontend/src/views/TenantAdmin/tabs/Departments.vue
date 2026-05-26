<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Departments</h3>
      <div class="header-controls">
        <select v-model="selectedBuId" class="form-control filter-select" @change="fetchDepts">
          <option value="">Select Business Unit</option>
          <option v-for="bu in businessUnits" :key="bu.id" :value="bu.id">{{ bu.name }}</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="showForm = true" :disabled="!selectedBuId">
          <i class="fas fa-plus"></i> Add Department
        </button>
      </div>
    </div>

    <div v-if="!selectedBuId" class="placeholder-state">
      <i class="fas fa-users fa-2x"></i>
      <p>Select a business unit to view departments</p>
    </div>
    <div v-else-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>

    <table v-else class="data-table">
      <thead>
        <tr><th>Name</th><th>Code</th><th>Head</th><th>Users</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-if="!departments.length"><td colspan="6" class="empty-row">No departments found</td></tr>
        <tr v-for="d in departments" :key="d.id">
          <td>{{ d.name }}</td>
          <td><code>{{ d.code }}</code></td>
          <td>{{ d.head_name || '—' }}</td>
          <td>{{ d.user_count ?? 0 }}</td>
          <td><span class="badge" :class="d.status === 'active' ? 'badge-success' : 'badge-neutral'">{{ d.status }}</span></td>
          <td class="actions-cell">
            <button class="icon-btn" @click="editDept(d)"><i class="fas fa-pencil-alt"></i></button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="cancelForm">
      <div class="modal-card">
        <h3 class="modal-title">{{ editMode ? 'Edit Department' : 'Add Department' }}</h3>
        <div class="form-group">
          <label class="form-label">Name <span class="req">*</span></label>
          <input v-model="form.name" class="form-control" placeholder="Department name" />
        </div>
        <div class="form-group">
          <label class="form-label">Code</label>
          <input v-model="form.code" class="form-control" placeholder="e.g. DEPT-001" />
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea v-model="form.description" class="form-control" rows="2"></textarea>
        </div>
        <div v-if="formError" class="alert-error">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="cancelForm">Cancel</button>
          <button class="btn btn-primary" @click="saveDept" :disabled="saving">
            <i v-if="saving" class="fas fa-spinner fa-spin"></i> Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
export default {
  name: 'DepartmentsTab',
  props: { tenant: { type: Object, required: true } },
  computed: {
    tenantId() { return this.tenant?.tenant_id ?? this.tenant?.id }
  },
  data() {
    return {
      businessUnits: [], departments: [], selectedBuId: '',
      loading: false, error: null,
      showForm: false, editMode: false, saving: false, formError: null, editId: null,
      form: { name: '', code: '', description: '' },
    }
  },
  mounted() { this.fetchAllBUs() },
  methods: {
    async fetchAllBUs() {
      try {
        const res = await tenantService.listEntities(this.tenantId)
        const entities = res?.data?.entities ?? res?.data ?? []
        const allBus = []
        for (const e of entities) {
          const r = await tenantService.listBusinessUnits(e.id).catch(() => ({ data: [] }))
          allBus.push(...(r?.data?.business_units ?? r?.data ?? []))
        }
        this.businessUnits = allBus
      } catch (e) { console.warn(e) }
    },
    async fetchDepts() {
      if (!this.selectedBuId) return
      this.loading = true
      try {
        const res = await tenantService.listDepartments(this.selectedBuId)
        this.departments = res?.data?.departments ?? res?.data ?? []
      } catch (e) { this.error = e.message } finally { this.loading = false }
    },
    editDept(d) { this.editMode = true; this.editId = d.id; this.form = { name: d.name, code: d.code || '', description: d.description || '' }; this.showForm = true },
    async saveDept() {
      this.saving = true; this.formError = null
      try {
        if (this.editMode) await tenantService.updateDepartment(this.editId, this.form)
        else await tenantService.createDepartment(this.selectedBuId, this.form)
        this.cancelForm(); await this.fetchDepts()
      } catch (e) { this.formError = e.message } finally { this.saving = false }
    },
    cancelForm() { this.showForm = false; this.editMode = false; this.editId = null; this.formError = null; this.form = { name: '', code: '', description: '' } },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.header-controls { display: flex; gap: 10px; align-items: center; }
.filter-select { padding: 7px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 12px 14px; border-bottom: 1px solid #f0f0f0; }
.badge { padding: 3px 9px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-neutral { background: #f5f5f5; color: #666; }
.actions-cell { display: flex; gap: 6px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 5px; border-radius: 5px; color: #555; font-size: 14px; }
.icon-btn:hover { background: #f0f0f0; }
.placeholder-state, .loading-state, .empty-row { padding: 40px; text-align: center; color: #aaa; }
.placeholder-state i { color: #d0d0d0; margin-bottom: 12px; display: block; }
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
code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
</style>
