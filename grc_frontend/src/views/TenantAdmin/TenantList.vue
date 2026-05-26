<template>
  <div class="tenant-list-page">
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">
          <i class="fas fa-building"></i> Tenant Management
        </h1>
        <p class="page-subtitle">Manage all tenants in the platform</p>
      </div>
      <div class="page-header-right">
        <button class="btn btn-primary" @click="$router.push('/tenant-admin/create')">
          <i class="fas fa-plus"></i> New Tenant
        </button>
      </div>
    </div>

    <div class="filter-bar">
      <input
        v-model="search"
        type="text"
        class="search-input"
        placeholder="Search tenants..."
        @input="onSearch"
      />
      <select v-model="statusFilter" class="filter-select" @change="onSearch">
        <option value="">All Statuses</option>
        <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
    </div>

    <div class="table-card">
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading tenants...
      </div>

      <div v-else-if="error" class="error-state">
        <i class="fas fa-exclamation-circle"></i> {{ error }}
        <button class="btn btn-sm btn-outline ml-2" @click="fetchTenants">Retry</button>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Subdomain</th>
            <th>Status</th>
            <th>Industry</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredTenants.length === 0">
            <td colspan="6" class="empty-row">No tenants found</td>
          </tr>
          <tr v-for="tenant in filteredTenants" :key="tenant.id" class="data-row">
            <td>
              <div class="tenant-name">
                <span class="tenant-avatar">{{ initials(tenant.name) }}</span>
                <span>{{ tenant.name }}</span>
              </div>
            </td>
            <td><code>{{ tenant.subdomain }}</code></td>
            <td>
              <span class="status-badge" :class="`status-${tenant.status}`">
                {{ formatStatus(tenant.status) }}
              </span>
            </td>
            <td>{{ tenant.industry || '—' }}</td>
            <td>{{ formatDate(tenant.created_at) }}</td>
            <td class="actions-cell">
              <button class="icon-btn" title="View" @click="viewTenant(tenant)">
                <i class="fas fa-eye"></i>
              </button>
              <button
                v-if="tenant.status === 'configuration_pending' || tenant.status === 'draft'"
                class="icon-btn text-success"
                title="Activate"
                @click="activateTenant(tenant)"
              >
                <i class="fas fa-check-circle"></i>
              </button>
              <button
                v-if="tenant.status === 'active'"
                class="icon-btn text-warning"
                title="Suspend"
                @click="confirmSuspend(tenant)"
              >
                <i class="fas fa-pause-circle"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="showConfirmDialog = false">
      <div class="confirm-dialog">
        <h3>Suspend Tenant</h3>
        <p>Are you sure you want to suspend <strong>{{ selectedTenant?.name }}</strong>?</p>
        <div class="dialog-actions">
          <button class="btn btn-outline" @click="showConfirmDialog = false">Cancel</button>
          <button class="btn btn-danger" @click="doSuspend" :disabled="actionLoading">
            <i v-if="actionLoading" class="fas fa-spinner fa-spin"></i> Suspend
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'

export default {
  name: 'TenantList',
  data() {
    return {
      tenants: [],
      loading: false,
      error: null,
      search: '',
      statusFilter: '',
      actionLoading: false,
      showConfirmDialog: false,
      selectedTenant: null,
      statusOptions: [
        { value: 'draft', label: 'Draft' },
        { value: 'onboarding', label: 'Onboarding' },
        { value: 'configuration_pending', label: 'Config Pending' },
        { value: 'active', label: 'Active' },
        { value: 'suspended', label: 'Suspended' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'archived', label: 'Archived' },
      ],
    }
  },
  computed: {
    filteredTenants() {
      let list = this.tenants
      if (this.statusFilter) {
        list = list.filter((t) => t.status === this.statusFilter)
      }
      if (this.search.trim()) {
        const q = this.search.toLowerCase()
        list = list.filter(
          (t) =>
            t.name?.toLowerCase().includes(q) ||
            t.subdomain?.toLowerCase().includes(q) ||
            t.industry?.toLowerCase().includes(q)
        )
      }
      return list
    },
  },
  mounted() {
    this.fetchTenants()
  },
  methods: {
    async fetchTenants() {
      this.loading = true
      this.error = null
      try {
        const response = await tenantService.listTenants()
        this.tenants = response?.data?.tenants ?? response?.data ?? []
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    onSearch() {},
    viewTenant(tenant) {
      this.$router.push(`/tenant-admin/${tenant.tenant_id}`)
    },
    async activateTenant(tenant) {
      this.actionLoading = true
      try {
        await tenantService.activateTenant(tenant.tenant_id)
        await this.fetchTenants()
      } catch (e) {
        alert(e.message)
      } finally {
        this.actionLoading = false
      }
    },
    confirmSuspend(tenant) {
      this.selectedTenant = tenant
      this.showConfirmDialog = true
    },
    async doSuspend() {
      this.actionLoading = true
      try {
        await tenantService.suspendTenant(this.selectedTenant.tenant_id)
        this.showConfirmDialog = false
        await this.fetchTenants()
      } catch (e) {
        alert(e.message)
      } finally {
        this.actionLoading = false
      }
    },
    initials(name) {
      if (!name) return '?'
      return name
        .split(' ')
        .slice(0, 2)
        .map((w) => w[0])
        .join('')
        .toUpperCase()
    },
    formatStatus(status) {
      return (status || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    },
    formatDate(dt) {
      if (!dt) return '—'
      return new Date(dt).toLocaleDateString()
    },
  },
}
</script>

<style scoped>
.tenant-list-page { padding: 24px; margin-left: 236px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: #1a1a2e; margin: 0 0 4px; }
.page-subtitle { font-size: 14px; color: #666; margin: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.search-input { flex: 1; padding: 8px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.filter-select { padding: 8px 14px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; background: #fff; }
.table-card { background: #fff; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 12px 16px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 14px 16px; border-bottom: 1px solid #f0f0f0; color: #333; }
.data-row:hover td { background: #fafbff; }
.tenant-avatar { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; background: #e8eaf6; color: #3f51b5; font-weight: 700; font-size: 12px; margin-right: 10px; }
.tenant-name { display: flex; align-items: center; }
.status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
.status-active { background: #e8f5e9; color: #2e7d32; }
.status-suspended { background: #fff3e0; color: #e65100; }
.status-draft { background: #f3e5f5; color: #7b1fa2; }
.status-onboarding { background: #e3f2fd; color: #1565c0; }
.status-configuration_pending { background: #fce4ec; color: #c62828; }
.status-archived { background: #efebe9; color: #4e342e; }
.status-inactive { background: #eceff1; color: #546e7a; }
.actions-cell { display: flex; gap: 8px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 6px; border-radius: 6px; color: #555; font-size: 15px; transition: background 0.15s; }
.icon-btn:hover { background: #f0f0f0; }
.icon-btn.text-success { color: #2e7d32; }
.icon-btn.text-warning { color: #e65100; }
.empty-row { text-align: center; color: #999; padding: 32px; }
.loading-state, .error-state { padding: 32px; text-align: center; color: #666; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:hover { background: #303f9f; }
.btn-outline { background: transparent; border: 1px solid #ccc; color: #555; }
.btn-danger { background: #c62828; color: #fff; }
.btn-sm { padding: 4px 12px; font-size: 12px; }
.ml-2 { margin-left: 8px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.confirm-dialog { background: #fff; border-radius: 12px; padding: 28px; width: 380px; }
.confirm-dialog h3 { margin: 0 0 12px; font-size: 18px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
code { background: #f0f0f0; padding: 2px 7px; border-radius: 4px; font-size: 12px; }
</style>
