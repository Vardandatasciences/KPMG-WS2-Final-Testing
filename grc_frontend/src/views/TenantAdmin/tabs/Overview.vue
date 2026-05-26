<template>
  <div class="tab-panel">
    <div class="overview-grid">
      <div class="info-card">
        <h3 class="card-title"><i class="fas fa-info-circle"></i> General Info</h3>
        <div class="info-row" v-for="row in generalFields" :key="row.label">
          <span class="info-label">{{ row.label }}</span>
          <span class="info-value">{{ row.value || '—' }}</span>
        </div>
      </div>

      <div class="info-card">
        <h3 class="card-title"><i class="fas fa-address-card"></i> Contact</h3>
        <div class="info-row" v-for="row in contactFields" :key="row.label">
          <span class="info-label">{{ row.label }}</span>
          <span class="info-value">{{ row.value || '—' }}</span>
        </div>
      </div>

      <div class="info-card">
        <h3 class="card-title"><i class="fas fa-certificate"></i> License</h3>
        <div class="info-row" v-for="row in licenseFields" :key="row.label">
          <span class="info-label">{{ row.label }}</span>
          <span class="info-value">{{ row.value || '—' }}</span>
        </div>
      </div>

      <div class="info-card actions-card">
        <h3 class="card-title"><i class="fas fa-bolt"></i> Quick Actions</h3>
        <div class="action-list">
          <button
            v-if="tenant.status === 'configuration_pending' || tenant.status === 'draft'"
            class="action-btn success"
            @click="doAction('activate')"
            :disabled="actionLoading"
          >
            <i class="fas fa-check-circle"></i> Activate Tenant
          </button>
          <button
            v-if="tenant.status === 'active'"
            class="action-btn warning"
            @click="doAction('suspend')"
            :disabled="actionLoading"
          >
            <i class="fas fa-pause-circle"></i> Suspend Tenant
          </button>
          <button
            v-if="tenant.status === 'suspended' || tenant.status === 'inactive'"
            class="action-btn danger"
            @click="doAction('archive')"
            :disabled="actionLoading"
          >
            <i class="fas fa-archive"></i> Archive Tenant
          </button>
        </div>
        <div v-if="actionMsg" class="action-msg" :class="actionMsgType">
          {{ actionMsg }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'

export default {
  name: 'OverviewTab',
  props: {
    tenant: { type: Object, required: true },
  },
  emits: ['refresh'],
  data() {
    return {
      actionLoading: false,
      actionMsg: '',
      actionMsgType: '',
    }
  },
  computed: {
    generalFields() {
      return [
        { label: 'Name', value: this.tenant.name },
        { label: 'Subdomain', value: this.tenant.subdomain },
        { label: 'Status', value: this.formatStatus(this.tenant.status) },
        { label: 'Industry', value: this.tenant.industry },
        { label: 'Country', value: this.tenant.country },
        { label: 'Created', value: this.fmtDate(this.tenant.created_at) },
        { label: 'Description', value: this.tenant.description },
      ]
    },
    contactFields() {
      return [
        { label: 'Contact Name', value: this.tenant.primary_contact_name },
        { label: 'Email', value: this.tenant.primary_contact_email },
        { label: 'Phone', value: this.tenant.primary_contact_phone },
      ]
    },
    licenseFields() {
      return [
        { label: 'License Type', value: this.tenant.license_type },
        { label: 'Max Users', value: this.tenant.max_users },
        { label: 'License Start', value: this.fmtDate(this.tenant.license_start) },
        { label: 'License End', value: this.fmtDate(this.tenant.license_end) },
      ]
    },
  },
  methods: {
    async doAction(action) {
      this.actionLoading = true
      this.actionMsg = ''
      try {
        if (action === 'activate') await tenantService.activateTenant(this.tenant.tenant_id)
        if (action === 'suspend') await tenantService.suspendTenant(this.tenant.tenant_id)
        if (action === 'archive') await tenantService.archiveTenant(this.tenant.tenant_id)
        this.actionMsg = `Tenant ${action}d successfully`
        this.actionMsgType = 'msg-success'
        this.$emit('refresh')
      } catch (e) {
        this.actionMsg = e.message
        this.actionMsgType = 'msg-error'
      } finally {
        this.actionLoading = false
      }
    },
    formatStatus(s) {
      return (s || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    },
    fmtDate(dt) {
      if (!dt) return null
      return new Date(dt).toLocaleDateString()
    },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.overview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.info-card { background: #f8f9fa; border-radius: 10px; padding: 20px; }
.card-title { font-size: 14px; font-weight: 700; color: #3f51b5; margin: 0 0 16px; display: flex; align-items: center; gap: 8px; }
.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-size: 14px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: #777; font-weight: 500; }
.info-value { color: #333; font-weight: 500; text-align: right; max-width: 60%; }
.actions-card { display: flex; flex-direction: column; }
.action-list { display: flex; flex-direction: column; gap: 10px; }
.action-btn { padding: 10px 16px; border: none; border-radius: 7px; cursor: pointer; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.action-btn.success { background: #e8f5e9; color: #2e7d32; }
.action-btn.success:hover { background: #c8e6c9; }
.action-btn.warning { background: #fff3e0; color: #e65100; }
.action-btn.warning:hover { background: #ffe0b2; }
.action-btn.danger { background: #ffebee; color: #c62828; }
.action-btn.danger:hover { background: #ffcdd2; }
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.action-msg { margin-top: 14px; padding: 10px 14px; border-radius: 6px; font-size: 13px; }
.msg-success { background: #e8f5e9; color: #2e7d32; }
.msg-error { background: #ffebee; color: #c62828; }
</style>
