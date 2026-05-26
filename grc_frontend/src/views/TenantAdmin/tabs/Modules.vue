<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Module Configuration</h3>
      <button class="btn btn-primary btn-sm" @click="saveModules" :disabled="saving || !dirty">
        <i v-if="saving" class="fas fa-spinner fa-spin"></i>
        <i v-else class="fas fa-save"></i>
        Save Changes
      </button>
    </div>
    <p class="section-desc">Enable or disable GRC modules for this tenant. Disabled modules are blocked at the API level.</p>

    <div v-if="loading" class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading modules...</div>

    <div v-else class="modules-grid">
      <div
        v-for="mod in modules"
        :key="mod.module_code"
        class="module-card"
        :class="{ enabled: mod.is_enabled, disabled: !mod.is_enabled }"
      >
        <div class="module-header">
          <div class="module-icon"><i :class="moduleIcon(mod.module_code)"></i></div>
          <div class="module-info">
            <div class="module-name">{{ moduleLabel(mod.module_code) }}</div>
            <div class="module-tier">{{ mod.license_tier || 'basic' }}</div>
          </div>
          <label class="toggle">
            <input type="checkbox" v-model="mod.is_enabled" @change="dirty = true" />
            <span class="slider"></span>
          </label>
        </div>
        <div class="module-limits" v-if="mod.is_enabled">
          <div class="limit-row">
            <span class="limit-label">User Limit</span>
            <input v-model.number="mod.user_limit" type="number" class="limit-input" placeholder="Unlimited" @input="dirty = true" />
          </div>
          <div class="limit-row">
            <span class="limit-label">API Limit</span>
            <input v-model.number="mod.api_limit" type="number" class="limit-input" placeholder="Unlimited" @input="dirty = true" />
          </div>
          <div class="limit-row">
            <span class="limit-label">AI Limit</span>
            <input v-model.number="mod.ai_limit" type="number" class="limit-input" placeholder="Unlimited" @input="dirty = true" />
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
  name: 'ModulesTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      modules: [], loading: false, saving: false, dirty: false,
      saveMsg: '', saveMsgType: '',
    }
  },
  mounted() { this.fetchModules() },
  methods: {
    async fetchModules() {
      this.loading = true
      try {
        const res = await tenantService.getTenantModules(this.tenant.tenant_id)
        const raw = res?.data?.modules ?? res?.data ?? []
        const defaultModules = ['framework', 'policy', 'compliance', 'audit', 'risk', 'incident', 'event']
        if (raw.length) {
          this.modules = raw
        } else {
          this.modules = defaultModules.map((code) => ({ module_code: code, is_enabled: true, license_tier: 'basic', user_limit: null, api_limit: null, ai_limit: null }))
        }
      } catch (e) {
        const defaultModules = ['framework', 'policy', 'compliance', 'audit', 'risk', 'incident', 'event']
        this.modules = defaultModules.map((code) => ({ module_code: code, is_enabled: true, license_tier: 'basic', user_limit: null, api_limit: null, ai_limit: null }))
      } finally { this.loading = false }
    },
    async saveModules() {
      this.saving = true; this.saveMsg = ''
      try {
        await tenantService.updateTenantModules(this.tenant.tenant_id, { modules: this.modules })
        this.dirty = false; this.saveMsg = 'Module settings saved successfully'; this.saveMsgType = 'msg-success'
      } catch (e) { this.saveMsg = e.message; this.saveMsgType = 'msg-error' } finally { this.saving = false }
    },
    moduleLabel(code) {
      const labels = { framework: 'Framework', policy: 'Policy', compliance: 'Compliance', audit: 'Audit', risk: 'Risk', incident: 'Incident', event: 'Event' }
      return labels[code] || code
    },
    moduleIcon(code) {
      const icons = { framework: 'fas fa-cube', policy: 'fas fa-file-alt', compliance: 'fas fa-clipboard-check', audit: 'fas fa-search', risk: 'fas fa-shield-alt', incident: 'fas fa-exclamation-triangle', event: 'fas fa-calendar-alt' }
      return icons[code] || 'fas fa-th'
    },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.section-desc { font-size: 14px; color: #666; margin: 0 0 24px; }
.loading-state { padding: 28px; text-align: center; color: #999; }
.modules-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.module-card { border: 2px solid #eee; border-radius: 12px; padding: 18px; transition: border-color 0.2s; }
.module-card.enabled { border-color: #c5cae9; background: #fafbff; }
.module-card.disabled { opacity: 0.7; background: #f9f9f9; }
.module-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.module-icon { width: 40px; height: 40px; background: #e8eaf6; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #3f51b5; font-size: 18px; flex-shrink: 0; }
.module-info { flex: 1; }
.module-name { font-size: 15px; font-weight: 700; color: #333; }
.module-tier { font-size: 12px; color: #888; text-transform: capitalize; }
.module-limits { display: flex; flex-direction: column; gap: 8px; padding-top: 12px; border-top: 1px solid #eee; }
.limit-row { display: flex; align-items: center; justify-content: space-between; }
.limit-label { font-size: 13px; color: #666; }
.limit-input { width: 110px; padding: 5px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 13px; }
.toggle { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.toggle input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; inset: 0; background: #ccc; border-radius: 24px; transition: 0.3s; }
.slider:before { content: ''; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s; }
input:checked + .slider { background: #3f51b5; }
input:checked + .slider:before { transform: translateX(20px); }
.save-msg { margin-top: 20px; padding: 12px 16px; border-radius: 8px; font-size: 14px; }
.msg-success { background: #e8f5e9; color: #2e7d32; }
.msg-error { background: #ffebee; color: #c62828; }
.btn { padding: 8px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.btn-primary { background: #3f51b5; color: #fff; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-sm { padding: 6px 14px; font-size: 13px; }
</style>
