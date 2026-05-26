<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Roles &amp; Permissions</h3>
    </div>
    <div class="roles-info">
      <p class="info-text">
        <i class="fas fa-info-circle"></i>
        Roles are assigned per user when mapping users to this tenant. The system supports the following predefined roles:
      </p>
    </div>
    <div class="roles-grid">
      <div class="role-card" v-for="role in roles" :key="role.name">
        <div class="role-icon" :style="{ background: role.color }">
          <i :class="role.icon"></i>
        </div>
        <div class="role-info">
          <div class="role-name">{{ role.name }}</div>
          <div class="role-desc">{{ role.description }}</div>
          <div class="role-perms">
            <span v-for="perm in role.permissions" :key="perm" class="perm-tag">{{ perm }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RolesTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      roles: [
        {
          name: 'GRC Administrator',
          icon: 'fas fa-crown',
          color: '#e8eaf6',
          description: 'Full access to all GRC modules and tenant settings',
          permissions: ['*'],
        },
        {
          name: 'Compliance Manager',
          icon: 'fas fa-clipboard-check',
          color: '#e3f2fd',
          description: 'Manage compliance frameworks, policies, and audits',
          permissions: ['view_compliance', 'create_compliance', 'edit_compliance', 'approve_compliance'],
        },
        {
          name: 'Risk Manager',
          icon: 'fas fa-shield-alt',
          color: '#fff3e0',
          description: 'Manage risk register, assessments, and mitigations',
          permissions: ['view_risk', 'create_risk', 'edit_risk', 'assign_risk'],
        },
        {
          name: 'Auditor',
          icon: 'fas fa-search',
          color: '#e8f5e9',
          description: 'Conduct audits, submit findings, and manage evidence',
          permissions: ['view_audit', 'conduct_audit', 'submit_findings'],
        },
        {
          name: 'Incident Manager',
          icon: 'fas fa-exclamation-triangle',
          color: '#fce4ec',
          description: 'Manage incidents, assign tasks, track resolution',
          permissions: ['view_incident', 'create_incident', 'assign_incident'],
        },
        {
          name: 'Viewer',
          icon: 'fas fa-eye',
          color: '#f5f5f5',
          description: 'Read-only access to all approved content',
          permissions: ['view_policy', 'view_compliance', 'view_risk', 'view_audit'],
        },
      ],
    }
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.info-text { font-size: 14px; color: #666; padding: 12px 16px; background: #f0f4ff; border-radius: 8px; border-left: 4px solid #3f51b5; margin-bottom: 24px; display: flex; align-items: flex-start; gap: 8px; }
.roles-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.role-card { display: flex; gap: 14px; padding: 16px; border: 1px solid #eee; border-radius: 10px; }
.role-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #555; flex-shrink: 0; }
.role-name { font-size: 15px; font-weight: 700; color: #333; margin-bottom: 4px; }
.role-desc { font-size: 13px; color: #666; margin-bottom: 10px; }
.role-perms { display: flex; flex-wrap: wrap; gap: 5px; }
.perm-tag { background: #f0f0f0; color: #555; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-family: monospace; }
</style>
