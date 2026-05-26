<template>
  <div class="tenant-create-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <i class="fas fa-arrow-left"></i> Back
      </button>
      <h1 class="page-title">Create New Tenant</h1>
    </div>

    <div class="form-card">
      <form @submit.prevent="handleSubmit">
        <div class="form-section">
          <h3 class="section-title">Basic Information</h3>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Tenant Name <span class="required">*</span></label>
              <input v-model="form.name" type="text" class="form-control" placeholder="e.g. Acme Corporation" required />
            </div>
            <div class="form-group">
              <label class="form-label">Subdomain <span class="required">*</span></label>
              <div class="input-addon">
                <input v-model="form.subdomain" type="text" class="form-control" placeholder="acme" required @input="slugify" />
                <span class="addon-suffix">.platform.com</span>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Industry</label>
              <select v-model="form.industry" class="form-control">
                <option value="">Select Industry</option>
                <option v-for="ind in industries" :key="ind" :value="ind">{{ ind }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Country</label>
              <input v-model="form.country" type="text" class="form-control" placeholder="e.g. India" />
            </div>
            <div class="form-group full-width">
              <label class="form-label">Description</label>
              <textarea v-model="form.description" class="form-control" rows="3" placeholder="Brief description of this tenant..."></textarea>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">Contact Information</h3>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Primary Contact Name</label>
              <input v-model="form.primary_contact_name" type="text" class="form-control" placeholder="Full name" />
            </div>
            <div class="form-group">
              <label class="form-label">Primary Contact Email</label>
              <input v-model="form.primary_contact_email" type="email" class="form-control" placeholder="admin@company.com" />
            </div>
            <div class="form-group">
              <label class="form-label">Primary Contact Phone</label>
              <input v-model="form.primary_contact_phone" type="text" class="form-control" placeholder="+1-xxx-xxx-xxxx" />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">License & Plan</h3>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">License Type</label>
              <select v-model="form.license_type" class="form-control">
                <option value="trial">Trial</option>
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Max Users</label>
              <input v-model.number="form.max_users" type="number" class="form-control" placeholder="50" min="1" />
            </div>
            <div class="form-group">
              <label class="form-label">Initial Status</label>
              <select v-model="form.status" class="form-control">
                <option value="draft">Draft</option>
                <option value="onboarding">Onboarding</option>
                <option value="configuration_pending">Configuration Pending</option>
              </select>
            </div>
          </div>
        </div>

        <div v-if="error" class="alert-error">
          <i class="fas fa-exclamation-triangle"></i> {{ error }}
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" @click="$router.back()">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-plus"></i>
            Create Tenant
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'

export default {
  name: 'TenantCreate',
  data() {
    return {
      loading: false,
      error: null,
      form: {
        name: '',
        subdomain: '',
        industry: '',
        country: '',
        description: '',
        primary_contact_name: '',
        primary_contact_email: '',
        primary_contact_phone: '',
        license_type: 'professional',
        max_users: null,
        status: 'draft',
      },
      industries: [
        'Banking & Finance', 'Insurance', 'Healthcare', 'Technology',
        'Manufacturing', 'Retail', 'Government', 'Education',
        'Energy & Utilities', 'Telecommunications', 'Consulting', 'Other',
      ],
    }
  },
  methods: {
    slugify() {
      this.form.subdomain = this.form.subdomain
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '')
    },
    async handleSubmit() {
      this.loading = true
      this.error = null
      try {
        const response = await tenantService.createTenant(this.form)
        const tenantId = response?.data?.id ?? response?.data?.tenant_id
        if (tenantId) {
          this.$router.push(`/tenant-admin/${tenantId}`)
        } else {
          this.$router.push('/tenant-admin')
        }
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.tenant-create-page { padding: 24px; max-width: 900px; margin: 0 auto 0 236px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 28px; }
.back-btn { background: none; border: 1px solid #ddd; border-radius: 6px; padding: 6px 14px; cursor: pointer; color: #555; font-size: 14px; display: flex; align-items: center; gap: 6px; }
.back-btn:hover { background: #f5f5f5; }
.page-title { font-size: 22px; font-weight: 700; color: #1a1a2e; margin: 0; }
.form-card { background: #fff; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.07); padding: 32px; }
.form-section { margin-bottom: 32px; }
.section-title { font-size: 16px; font-weight: 700; color: #3f51b5; margin: 0 0 20px; padding-bottom: 10px; border-bottom: 2px solid #e8eaf6; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.full-width { grid-column: 1 / -1; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 13px; font-weight: 600; color: #444; }
.required { color: #e53935; }
.form-control { padding: 9px 13px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; transition: border-color 0.2s; }
.form-control:focus { border-color: #3f51b5; box-shadow: 0 0 0 3px rgba(63,81,181,0.1); }
textarea.form-control { resize: vertical; }
.input-addon { display: flex; align-items: center; border: 1px solid #ddd; border-radius: 6px; overflow: hidden; }
.input-addon .form-control { border: none; flex: 1; }
.input-addon .form-control:focus { box-shadow: none; }
.addon-suffix { padding: 9px 12px; background: #f5f5f5; color: #888; font-size: 13px; white-space: nowrap; border-left: 1px solid #ddd; }
.alert-error { background: #ffebee; color: #c62828; border-radius: 6px; padding: 12px 16px; font-size: 14px; margin-bottom: 16px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; padding-top: 20px; border-top: 1px solid #f0f0f0; }
.btn { padding: 10px 22px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #303f9f; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-outline { background: transparent; border: 1px solid #ccc; color: #555; }
</style>
