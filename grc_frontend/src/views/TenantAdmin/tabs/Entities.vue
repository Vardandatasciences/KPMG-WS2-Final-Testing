<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Entities</h3>
      <button class="btn btn-primary btn-sm" @click="showForm = true">
        <i class="fas fa-plus"></i> Add Entity
      </button>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>
    <div v-else-if="error" class="error-state"><i class="fas fa-exclamation-circle"></i> {{ error }}</div>

    <table v-else class="data-table">
      <thead>
        <tr><th>Name</th><th>Code</th><th>Type</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-if="!entities.length"><td colspan="5" class="empty-row">No entities found</td></tr>
        <tr v-for="e in entities" :key="e.id">
          <td>{{ e.name }}</td>
          <td><code>{{ e.code }}</code></td>
          <td>{{ e.entity_type || '—' }}</td>
          <td><span class="badge" :class="e.status === 'active' ? 'badge-success' : 'badge-neutral'">{{ e.status }}</span></td>
          <td class="actions-cell">
            <button class="icon-btn" title="Edit" @click="editEntity(e)"><i class="fas fa-pencil-alt"></i></button>
            <button class="icon-btn text-danger" title="Delete" @click="deleteEntity(e)"><i class="fas fa-trash-alt"></i></button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="cancelForm">
      <div class="modal-card">
        <h3 class="modal-title">{{ editMode ? 'Edit Entity' : 'Add Entity' }}</h3>
        <div class="form-group">
          <label class="form-label">Name <span class="req">*</span></label>
          <input v-model="form.name" class="form-control" placeholder="Entity name" />
        </div>
        <div class="form-group">
          <label class="form-label">Code <span class="req">*</span></label>
          <input v-model="form.code" class="form-control" placeholder="e.g. HQ" />
        </div>
        <div class="form-group">
          <label class="form-label">Type</label>
          <select v-model="form.entity_type" class="form-control">
            <option value="">Select Type</option>
            <option value="headquarters">Headquarters</option>
            <option value="subsidiary">Subsidiary</option>
            <option value="branch">Branch</option>
            <option value="division">Division</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea v-model="form.description" class="form-control" rows="2"></textarea>
        </div>
        <div v-if="formError" class="alert-error">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="cancelForm">Cancel</button>
          <button class="btn btn-primary" @click="saveEntity" :disabled="saving">
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
  name: 'EntitiesTab',
  props: { tenant: { type: Object, required: true } },
  computed: {
    tenantId() { return this.tenant?.tenant_id ?? this.tenant?.id }
  },
  data() {
    return {
      entities: [], loading: false, error: null,
      showForm: false, editMode: false, saving: false, formError: null,
      form: { name: '', code: '', entity_type: '', description: '' },
      editId: null,
    }
  },
  mounted() { this.fetchEntities() },
  methods: {
    async fetchEntities() {
      this.loading = true; this.error = null
      try {
        if (!this.tenantId) return
        const res = await tenantService.listEntities(this.tenantId)
        this.entities = res?.data?.entities ?? res?.data ?? []
      } catch (e) { this.error = e.message } finally { this.loading = false }
    },
    editEntity(e) {
      this.editMode = true; this.editId = e.id
      this.form = { name: e.name, code: e.code, entity_type: e.entity_type || '', description: e.description || '' }
      this.showForm = true
    },
    async deleteEntity(e) {
      if (!confirm(`Delete entity "${e.name}"?`)) return
      try { await tenantService.deleteEntity(e.id); await this.fetchEntities() } catch (err) { alert(err.message) }
    },
    async saveEntity() {
      this.saving = true; this.formError = null
      try {
        if (this.editMode) await tenantService.updateEntity(this.editId, this.form)
        else await tenantService.createEntity(this.tenantId, this.form)
        this.cancelForm(); await this.fetchEntities()
      } catch (e) { this.formError = e.message } finally { this.saving = false }
    },
    cancelForm() { this.showForm = false; this.editMode = false; this.editId = null; this.formError = null; this.form = { name: '', code: '', entity_type: '', description: '' } },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 12px 14px; border-bottom: 1px solid #f0f0f0; }
.badge { padding: 3px 9px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-neutral { background: #f5f5f5; color: #666; }
.actions-cell { display: flex; gap: 6px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 5px; border-radius: 5px; color: #555; font-size: 14px; }
.icon-btn:hover { background: #f0f0f0; }
.icon-btn.text-danger { color: #c62828; }
.loading-state, .error-state, .empty-row { padding: 28px; text-align: center; color: #999; }
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
