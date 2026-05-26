<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Branding</h3>
      <button class="btn btn-primary btn-sm" @click="saveBranding" :disabled="saving">
        <i v-if="saving" class="fas fa-spinner fa-spin"></i>
        <i v-else class="fas fa-save"></i> Save
      </button>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>

    <div v-else class="branding-layout">
      <div class="branding-form">
        <div class="settings-section">
          <h4 class="section-title">Logo & Favicon</h4>
          <div class="logo-upload-area">
            <div class="logo-preview" v-if="form.logo_url">
              <img :src="form.logo_url" alt="Logo" />
            </div>
            <div class="logo-placeholder" v-else>
              <i class="fas fa-image fa-2x"></i>
              <span>No logo uploaded</span>
            </div>
            <div class="upload-controls">
              <input ref="logoInput" type="file" accept="image/*" style="display:none" @change="onLogoSelect" />
              <button class="btn btn-outline btn-sm" @click="$refs.logoInput.click()">
                <i class="fas fa-upload"></i> Upload Logo
              </button>
              <div class="form-group mt-8">
                <label class="form-label">Or paste logo URL</label>
                <input v-model="form.logo_url" class="form-control" placeholder="https://..." />
              </div>
              <div class="form-group mt-8">
                <label class="form-label">Favicon URL</label>
                <input v-model="form.favicon_url" class="form-control" placeholder="https://..." />
              </div>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <h4 class="section-title">Brand Colors</h4>
          <div class="color-row">
            <div class="color-group" v-for="c in colorFields" :key="c.key">
              <label class="form-label">{{ c.label }}</label>
              <div class="color-input-wrap">
                <input type="color" v-model="form[c.key]" class="color-picker" />
                <input type="text" v-model="form[c.key]" class="form-control color-text" placeholder="#1976D2" />
              </div>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <h4 class="section-title">Email</h4>
          <div class="form-group">
            <label class="form-label">Email Logo URL</label>
            <input v-model="form.email_template_logo" class="form-control" placeholder="https://..." />
          </div>
          <div class="form-group mt-12">
            <label class="form-label">Email Footer Text</label>
            <textarea v-model="form.email_footer_text" class="form-control" rows="2"></textarea>
          </div>
        </div>
      </div>

      <div class="preview-panel">
        <h4 class="section-title">Live Preview</h4>
        <div class="preview-card" :style="{ borderTop: `4px solid ${form.primary_color}` }">
          <div class="preview-header" :style="{ background: form.primary_color }">
            <img v-if="form.logo_url" :src="form.logo_url" class="preview-logo" alt="logo" />
            <span v-else class="preview-logo-text">{{ tenant.name }}</span>
          </div>
          <div class="preview-body">
            <div class="preview-nav">
              <span class="nav-item active-item" :style="{ background: form.accent_color }">Dashboard</span>
              <span class="nav-item">Policy</span>
              <span class="nav-item">Risk</span>
            </div>
            <div class="preview-content">
              <div class="preview-btn" :style="{ background: form.primary_color }">Action Button</div>
              <div class="preview-btn secondary" :style="{ background: form.secondary_color }">Secondary</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="saveMsg" class="save-msg" :class="saveMsgType">{{ saveMsg }}</div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
export default {
  name: 'BrandingTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      loading: false, saving: false, saveMsg: '', saveMsgType: '',
      form: { logo_url: '', favicon_url: '', primary_color: '#1976D2', secondary_color: '#424242', accent_color: '#82B1FF', email_template_logo: '', email_footer_text: '' },
      colorFields: [
        { key: 'primary_color', label: 'Primary Color' },
        { key: 'secondary_color', label: 'Secondary Color' },
        { key: 'accent_color', label: 'Accent Color' },
      ],
    }
  },
  mounted() { this.fetchBranding() },
  methods: {
    async fetchBranding() {
      this.loading = true
      try {
        const res = await tenantService.getTenantBranding(this.tenant.tenant_id)
        const data = res?.data?.branding ?? res?.data ?? {}
        if (data && Object.keys(data).length) Object.assign(this.form, data)
      } catch (e) { console.warn(e) } finally { this.loading = false }
    },
    async saveBranding() {
      this.saving = true; this.saveMsg = ''
      try {
        await tenantService.updateTenantBranding(this.tenant.tenant_id, this.form)
        this.saveMsg = 'Branding saved successfully'; this.saveMsgType = 'msg-success'
      } catch (e) { this.saveMsg = e.message; this.saveMsgType = 'msg-error' } finally { this.saving = false }
    },
    async onLogoSelect(e) {
      const file = e.target.files[0]
      if (!file) return
      const formData = new FormData()
      formData.append('logo', file)
      try {
        const res = await tenantService.uploadBrandingLogo(this.tenant.tenant_id, formData)
        this.form.logo_url = res?.data?.logo_url ?? ''
      } catch (err) { alert(err.message) }
    },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.loading-state { padding: 28px; text-align: center; color: #999; }
.branding-layout { display: grid; grid-template-columns: 1fr 320px; gap: 24px; }
.settings-section { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 700; color: #3f51b5; margin: 0 0 14px; }
.logo-upload-area { display: flex; gap: 16px; align-items: flex-start; }
.logo-preview img { width: 80px; height: 80px; object-fit: contain; border: 2px dashed #ddd; border-radius: 8px; padding: 4px; }
.logo-placeholder { width: 80px; height: 80px; border: 2px dashed #ddd; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #ccc; font-size: 12px; gap: 4px; flex-shrink: 0; }
.upload-controls { flex: 1; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-label { font-size: 13px; font-weight: 600; color: #444; }
.form-control { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.color-row { display: flex; gap: 16px; flex-wrap: wrap; }
.color-group { display: flex; flex-direction: column; gap: 6px; }
.color-input-wrap { display: flex; align-items: center; gap: 8px; }
.color-picker { width: 40px; height: 38px; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; padding: 2px; }
.color-text { width: 100px; }
.mt-8 { margin-top: 8px; }
.mt-12 { margin-top: 12px; }
.preview-panel { position: sticky; top: 24px; }
.preview-card { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 16px rgba(0,0,0,0.1); }
.preview-header { padding: 16px; min-height: 56px; display: flex; align-items: center; }
.preview-logo { height: 32px; object-fit: contain; }
.preview-logo-text { color: #fff; font-weight: 700; font-size: 14px; }
.preview-body { background: #fff; }
.preview-nav { display: flex; gap: 4px; padding: 12px 12px 0; }
.nav-item { padding: 6px 12px; border-radius: 6px 6px 0 0; font-size: 12px; cursor: default; color: #555; }
.active-item { color: #fff; }
.preview-content { padding: 16px; display: flex; gap: 10px; }
.preview-btn { padding: 8px 14px; border-radius: 6px; color: #fff; font-size: 12px; font-weight: 600; }
.save-msg { padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-top: 20px; }
.msg-success { background: #e8f5e9; color: #2e7d32; }
.msg-error { background: #ffebee; color: #c62828; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-outline { background: transparent; border: 1px solid #ccc; color: #555; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
</style>
