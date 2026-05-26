<template>
  <div class="tenant-detail-page">

    <!-- Breadcrumb -->
    <div class="breadcrumb-bar">
      <span class="breadcrumb-link" @click="$router.push('/tenant-admin')">
        <i class="fas fa-building"></i> Tenant Administration
      </span>
      <i class="fas fa-chevron-right breadcrumb-sep"></i>
      <span class="breadcrumb-current">{{ tenant ? tenant.name : '...' }}</span>
    </div>

    <!-- Tenant Banner -->
    <div class="tenant-banner" v-if="tenant">
      <div class="banner-avatar">{{ initials(tenant.name) }}</div>
      <div class="banner-info">
        <h1 class="banner-title">{{ tenant.name }}</h1>
        <div class="banner-meta">
          <span class="meta-chip"><i class="fas fa-globe"></i> {{ tenant.subdomain }}.riskavaire.com</span>
          <span class="status-pill" :class="`s-${tenant.status}`">
            <span class="status-dot"></span>{{ formatStatus(tenant.status) }}
          </span>
          <span class="meta-chip" v-if="tenant.subscription_tier">
            <i class="fas fa-layer-group"></i> {{ tenant.subscription_tier }}
          </span>
        </div>
      </div>
      <div class="banner-section-label" v-if="activeTabLabel">
        <i :class="activeTabIcon" class="section-icon"></i>
        <span>{{ activeTabLabel }}</span>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div class="banner-skeleton" v-else-if="loading">
      <div class="skel-avatar"></div>
      <div class="skel-lines">
        <div class="skel-line wide"></div>
        <div class="skel-line narrow"></div>
      </div>
    </div>

    <div v-if="error" class="alert-error">
      <i class="fas fa-exclamation-triangle"></i> {{ error }}
    </div>

    <!-- Content panel -->
    <div class="content-panel" v-if="tenant">
      <OverviewTab      v-if="activeTab === 'overview'"       :tenant="tenant" @refresh="fetchTenant" />
      <EntitiesTab      v-if="activeTab === 'entities'"       :tenant="tenant" />
      <BusinessUnitsTab v-if="activeTab === 'business_units'" :tenant="tenant" />
      <DepartmentsTab   v-if="activeTab === 'departments'"    :tenant="tenant" />
      <UsersTab         v-if="activeTab === 'users'"          :tenant="tenant" />
      <RolesTab         v-if="activeTab === 'roles'"          :tenant="tenant" />
      <ModulesTab       v-if="activeTab === 'modules'"        :tenant="tenant" />
      <SecurityTab      v-if="activeTab === 'security'"       :tenant="tenant" />
      <BrandingTab      v-if="activeTab === 'branding'"       :tenant="tenant" />
      <WorkflowsTab     v-if="activeTab === 'workflows'"      :tenant="tenant" />
      <LicenseTab       v-if="activeTab === 'license'"        :tenant="tenant" />
      <AuditLogsTab     v-if="activeTab === 'audit_logs'"     :tenant="tenant" />
      <SupportAccessTab v-if="activeTab === 'support'"        :tenant="tenant" />
    </div>

  </div>
</template>

<script>
import tenantService from '@/services/tenantService.js'
import OverviewTab      from './tabs/Overview.vue'
import EntitiesTab      from './tabs/Entities.vue'
import BusinessUnitsTab from './tabs/BusinessUnits.vue'
import DepartmentsTab   from './tabs/Departments.vue'
import UsersTab         from './tabs/Users.vue'
import RolesTab         from './tabs/Roles.vue'
import ModulesTab       from './tabs/Modules.vue'
import SecurityTab      from './tabs/Security.vue'
import BrandingTab      from './tabs/Branding.vue'
import WorkflowsTab     from './tabs/Workflows.vue'
import LicenseTab       from './tabs/License.vue'
import AuditLogsTab     from './tabs/AuditLogs.vue'
import SupportAccessTab from './tabs/SupportAccess.vue'

export default {
  name: 'TenantDetail',
  components: {
    OverviewTab, EntitiesTab, BusinessUnitsTab, DepartmentsTab,
    UsersTab, RolesTab, ModulesTab, SecurityTab, BrandingTab,
    WorkflowsTab, LicenseTab, AuditLogsTab, SupportAccessTab,
  },
  computed: {
    activeTab() {
      return this.$route.query.tab || 'overview'
    },
    activeTabLabel() {
      const map = { overview:'Overview', entities:'Entities', business_units:'Business Units',
        departments:'Departments', users:'Users', roles:'Roles', modules:'Modules',
        security:'Security', branding:'Branding', workflows:'Workflows',
        license:'License', audit_logs:'Audit Logs', support:'Support Access' }
      return map[this.activeTab] || ''
    },
    activeTabIcon() {
      const map = { overview:'fas fa-info-circle', entities:'fas fa-sitemap',
        business_units:'fas fa-layer-group', departments:'fas fa-users',
        users:'fas fa-user', roles:'fas fa-shield-alt', modules:'fas fa-th-large',
        security:'fas fa-lock', branding:'fas fa-palette', workflows:'fas fa-project-diagram',
        license:'fas fa-certificate', audit_logs:'fas fa-history', support:'fas fa-headset' }
      return map[this.activeTab] || 'fas fa-circle'
    }
  },
  data() {
    return {
      tenant: null,
      loading: false,
      error: null,
    }
  },
  watch: {
    '$route.params.tenantId'() { this.fetchTenant() }
  },
  mounted() {
    this.fetchTenant()
  },
  methods: {
    async fetchTenant() {
      this.loading = true
      this.error = null
      try {
        const response = await tenantService.getTenant(this.$route.params.tenantId)
        this.tenant = response?.data?.tenant ?? response?.data ?? response
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    initials(name) {
      if (!name) return '?'
      return name.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase()
    },
    formatStatus(status) {
      return (status || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    },
  },
}
</script>

<style scoped>
.tenant-detail-page {
  padding: 24px 28px;
  margin-left: 236px;
  min-height: 100vh;
  background: #f4f6fb;
}

/* Breadcrumb */
.breadcrumb-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #888;
  margin-bottom: 18px;
}
.breadcrumb-link {
  color: #003399;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.breadcrumb-link:hover { text-decoration: underline; }
.breadcrumb-sep { font-size: 10px; color: #bbb; }
.breadcrumb-current { color: #444; font-weight: 600; }

/* Tenant Banner */
.tenant-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  background: #ffffff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  border: 1px solid #e8eaed;
  border-left: 4px solid #003399;
}
.banner-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 10px;
  background: #eef1fb;
  color: #003399;
  font-size: 18px;
  font-weight: 800;
  flex-shrink: 0;
  letter-spacing: -1px;
}
.banner-info { flex: 1; min-width: 0; }
.banner-title {
  font-size: 19px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 7px;
  letter-spacing: -0.2px;
}
.banner-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.meta-chip {
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 5px;
  border: 1px solid #e5e7eb;
}
.meta-chip i { color: #6b7280; font-size: 11px; }
.status-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  text-transform: capitalize;
  background: #dcfce7;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #16a34a;
  display: inline-block;
}
.s-suspended .status-pill { background: #fff7ed; color: #c2410c; border-color: #fed7aa; }
.s-suspended .status-dot { background: #ea580c; }
.s-archived .status-pill { background: #f3f4f6; color: #6b7280; border-color: #d1d5db; }
.s-archived .status-dot { background: #9ca3af; }
.s-draft .status-pill { background: #faf5ff; color: #7c3aed; border-color: #e9d5ff; }
.s-draft .status-dot { background: #8b5cf6; }
.banner-section-label {
  display: flex;
  align-items: center;
  gap: 7px;
  background: #f8f9ff;
  border: 1px solid #dde1f5;
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #003399;
  white-space: nowrap;
  flex-shrink: 0;
}
.section-icon { font-size: 13px; color: #003399; }

/* Skeleton */
.banner-skeleton {
  display: flex;
  align-items: center;
  gap: 18px;
  background: #fff;
  border-radius: 14px;
  padding: 22px 28px;
  margin-bottom: 24px;
}
.skel-avatar { width: 58px; height: 58px; border-radius: 14px; background: #e9ecef; animation: pulse 1.4s infinite; }
.skel-lines { display: flex; flex-direction: column; gap: 10px; }
.skel-line { height: 14px; border-radius: 6px; background: #e9ecef; animation: pulse 1.4s infinite; }
.skel-line.wide { width: 200px; }
.skel-line.narrow { width: 120px; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.45; } }

/* Error */
.alert-error {
  background: #fff1f1;
  color: #c62828;
  border: 1px solid #fca5a5;
  border-radius: 10px;
  padding: 12px 18px;
  font-size: 14px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Content panel */
.content-panel {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  min-height: 400px;
  overflow: hidden;
}
</style>
