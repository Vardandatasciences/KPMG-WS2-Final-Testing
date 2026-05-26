<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Security Settings</h3>
      <button class="btn btn-primary btn-sm" @click="saveSettings" :disabled="saving">
        <i v-if="saving" class="fas fa-spinner fa-spin"></i>
        <i v-else class="fas fa-save"></i> Save
      </button>
    </div>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading...</div>

    <div v-else class="settings-form">
      <div class="settings-section">
        <h4 class="section-title">Multi-Factor Authentication</h4>
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-name">Require MFA</div>
            <div class="setting-desc">Force all users to set up MFA before accessing the system</div>
          </div>
          <label class="toggle"><input type="checkbox" v-model="form.mfa_required" /><span class="slider"></span></label>
        </div>
        <div class="setting-row" v-if="form.mfa_required">
          <div class="setting-info">
            <div class="setting-name">Allowed MFA Methods</div>
          </div>
          <div class="checkbox-group">
            <label v-for="method in mfaMethods" :key="method.value" class="checkbox-item">
              <input type="checkbox" :value="method.value" v-model="form.mfa_methods" />
              {{ method.label }}
            </label>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h4 class="section-title">Access Control</h4>
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-name">IP Restriction</div>
            <div class="setting-desc">Block access from unauthorized IP addresses</div>
          </div>
          <label class="toggle"><input type="checkbox" v-model="form.ip_restriction_enabled" /><span class="slider"></span></label>
        </div>
        <div v-if="form.ip_restriction_enabled" class="subsetting">
          <label class="form-label">Allowed IP Ranges (one per line, CIDR notation)</label>
          <textarea v-model="ipRangesText" class="form-control" rows="4" placeholder="192.168.1.0/24&#10;10.0.0.0/8"></textarea>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-name">Allowed Email Domains</div>
            <div class="setting-desc">Only users with these email domains can be added</div>
          </div>
        </div>
        <div class="subsetting">
          <textarea v-model="emailDomainsText" class="form-control" rows="3" placeholder="company.com&#10;subsidiary.org"></textarea>
        </div>
      </div>

      <div class="settings-section">
        <h4 class="section-title">Session &amp; Password</h4>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Session Timeout (minutes)</label>
            <input v-model.number="form.session_timeout_minutes" type="number" class="form-control" min="5" max="1440" />
          </div>
          <div class="form-group">
            <label class="form-label">Password Expiry (days)</label>
            <input v-model.number="form.password_expiry_days" type="number" class="form-control" min="0" max="365" />
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h4 class="section-title">Data Export</h4>
        <div class="setting-row">
          <div class="setting-info">
            <div class="setting-name">Allow Data Export</div>
          </div>
          <label class="toggle"><input type="checkbox" v-model="form.export_allowed" /><span class="slider"></span></label>
        </div>
        <div class="setting-row" v-if="form.export_allowed">
          <div class="setting-info">
            <div class="setting-name">Require Approval for Export</div>
          </div>
          <label class="toggle"><input type="checkbox" v-model="form.export_requires_approval" /><span class="slider"></span></label>
        </div>
      </div>

      <div v-if="saveMsg" class="save-msg" :class="saveMsgType">{{ saveMsg }}</div>
    </div>
  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
export default {
  name: 'SecurityTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      loading: false, saving: false, saveMsg: '', saveMsgType: '',
      ipRangesText: '', emailDomainsText: '',
      form: {
        mfa_required: false, mfa_methods: [], sso_enabled: false,
        ip_restriction_enabled: false, allowed_ip_ranges: [], allowed_email_domains: [],
        session_timeout_minutes: 30, password_expiry_days: 90,
        export_allowed: true, export_requires_approval: false,
      },
      mfaMethods: [{ value: 'email', label: 'Email OTP' }, { value: 'totp', label: 'TOTP App' }, { value: 'sms', label: 'SMS' }],
    }
  },
  mounted() { this.fetchSettings() },
  methods: {
    async fetchSettings() {
      this.loading = true
      try {
        const res = await tenantService.getSecuritySettings(this.tenant.tenant_id)
        const data = res?.data?.security_settings ?? res?.data ?? {}
        if (data && Object.keys(data).length) {
          Object.assign(this.form, data)
          this.ipRangesText = (data.allowed_ip_ranges || []).join('\n')
          this.emailDomainsText = (data.allowed_email_domains || []).join('\n')
        }
      } catch (e) { console.warn(e) } finally { this.loading = false }
    },
    async saveSettings() {
      this.saving = true; this.saveMsg = ''
      this.form.allowed_ip_ranges = this.ipRangesText.split('\n').map((s) => s.trim()).filter(Boolean)
      this.form.allowed_email_domains = this.emailDomainsText.split('\n').map((s) => s.trim()).filter(Boolean)
      try {
        await tenantService.updateSecuritySettings(this.tenant.tenant_id, this.form)
        this.saveMsg = 'Security settings saved'; this.saveMsgType = 'msg-success'
      } catch (e) { this.saveMsg = e.message; this.saveMsgType = 'msg-error' } finally { this.saving = false }
    },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.loading-state { padding: 28px; text-align: center; color: #999; }
.settings-section { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
.section-title { font-size: 14px; font-weight: 700; color: #3f51b5; margin: 0 0 16px; }
.setting-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; }
.setting-row:last-child { border-bottom: none; }
.setting-name { font-size: 14px; font-weight: 600; color: #333; }
.setting-desc { font-size: 12px; color: #888; margin-top: 2px; }
.subsetting { padding: 12px 0; }
.form-row { display: flex; gap: 20px; }
.form-group { flex: 1; }
.form-label { font-size: 13px; font-weight: 600; color: #444; display: block; margin-bottom: 6px; }
.form-control { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.checkbox-group { display: flex; gap: 16px; flex-wrap: wrap; }
.checkbox-item { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
.toggle { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.toggle input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; inset: 0; background: #ccc; border-radius: 24px; transition: 0.3s; }
.slider:before { content: ''; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s; }
input:checked + .slider { background: #3f51b5; }
input:checked + .slider:before { transform: translateX(20px); }
.save-msg { padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-top: 20px; }
.msg-success { background: #e8f5e9; color: #2e7d32; }
.msg-error { background: #ffebee; color: #c62828; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
</style>
