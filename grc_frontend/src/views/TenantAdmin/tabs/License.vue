<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">License &amp; Subscription</h3>
    </div>

    <div class="license-overview">
      <div class="license-card current-plan">
        <div class="plan-badge">Current Plan</div>
        <div class="plan-name">{{ currentPlan }}</div>
        <div class="plan-tier" :class="`tier-${tenant.license_type || 'basic'}`">
          {{ tenant.license_type || 'basic' }}
        </div>
        <div class="plan-dates" v-if="tenant.license_start || tenant.license_end">
          <div v-if="tenant.license_start">
            <span class="date-label">Start:</span> {{ fmtDate(tenant.license_start) }}
          </div>
          <div v-if="tenant.license_end">
            <span class="date-label">End:</span> {{ fmtDate(tenant.license_end) }}
          </div>
        </div>
      </div>

      <div class="license-stats">
        <div class="stat-card">
          <i class="fas fa-users stat-icon"></i>
          <div class="stat-value">{{ tenant.max_users || 'Unlimited' }}</div>
          <div class="stat-label">Max Users</div>
        </div>
        <div class="stat-card">
          <i class="fas fa-hdd stat-icon"></i>
          <div class="stat-value">{{ tenant.storage_limit_gb || 'Unlimited' }}</div>
          <div class="stat-label">Storage (GB)</div>
        </div>
        <div class="stat-card">
          <i class="fas fa-plug stat-icon"></i>
          <div class="stat-value">{{ tenant.api_limit || 'Unlimited' }}</div>
          <div class="stat-label">API Calls/day</div>
        </div>
        <div class="stat-card">
          <i class="fas fa-robot stat-icon"></i>
          <div class="stat-value">{{ tenant.ai_limit || 'Unlimited' }}</div>
          <div class="stat-label">AI Credits/mo</div>
        </div>
      </div>
    </div>

    <div class="plans-table">
      <h4 class="section-title">Available Plans</h4>
      <table class="data-table">
        <thead><tr><th>Plan</th><th>Users</th><th>Storage</th><th>API Calls</th><th>AI Credits</th><th>Modules</th></tr></thead>
        <tbody>
          <tr v-for="plan in plans" :key="plan.name" :class="{ 'current-row': plan.name.toLowerCase() === (tenant.license_type || 'basic') }">
            <td><strong>{{ plan.name }}</strong></td>
            <td>{{ plan.users }}</td>
            <td>{{ plan.storage }}</td>
            <td>{{ plan.api }}</td>
            <td>{{ plan.ai }}</td>
            <td>{{ plan.modules }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LicenseTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      plans: [
        { name: 'Trial', users: '5', storage: '5 GB', api: '1,000', ai: '50', modules: 'All (30 days)' },
        { name: 'Basic', users: '25', storage: '20 GB', api: '10,000', ai: '200', modules: 'Framework, Policy' },
        { name: 'Professional', users: '100', storage: '100 GB', api: '100,000', ai: '1,000', modules: 'All except Event' },
        { name: 'Enterprise', users: 'Unlimited', storage: 'Unlimited', api: 'Unlimited', ai: 'Unlimited', modules: 'All Modules' },
      ],
    }
  },
  computed: {
    currentPlan() {
      const t = this.tenant.license_type || 'basic'
      return t.charAt(0).toUpperCase() + t.slice(1)
    },
  },
  methods: {
    fmtDate(dt) { return dt ? new Date(dt).toLocaleDateString() : '—' },
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.license-overview { display: flex; gap: 20px; margin-bottom: 32px; flex-wrap: wrap; }
.license-card { background: linear-gradient(135deg, #3f51b5 0%, #303f9f 100%); color: #fff; border-radius: 14px; padding: 24px; min-width: 200px; }
.plan-badge { font-size: 12px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.plan-name { font-size: 26px; font-weight: 800; margin-bottom: 8px; }
.plan-tier { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; background: rgba(255,255,255,0.2); text-transform: capitalize; }
.plan-dates { margin-top: 16px; font-size: 13px; opacity: 0.9; }
.date-label { opacity: 0.7; }
.license-stats { display: flex; gap: 14px; flex-wrap: wrap; flex: 1; }
.stat-card { flex: 1; min-width: 100px; background: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e8eaf6; }
.stat-icon { font-size: 22px; color: #3f51b5; margin-bottom: 8px; display: block; }
.stat-value { font-size: 20px; font-weight: 700; color: #333; margin-bottom: 4px; }
.stat-label { font-size: 12px; color: #888; }
.plans-table { margin-top: 8px; }
.section-title { font-size: 14px; font-weight: 700; color: #3f51b5; margin-bottom: 14px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e9ecef; }
.data-table td { padding: 11px 14px; border-bottom: 1px solid #f0f0f0; }
.current-row td { background: #e8eaf6; font-weight: 600; }
</style>
