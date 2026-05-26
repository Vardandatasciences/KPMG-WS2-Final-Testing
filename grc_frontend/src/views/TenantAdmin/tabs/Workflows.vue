<template>
  <div class="tab-panel">
    <div class="panel-header">
      <h3 class="panel-title">Approval Workflows</h3>
    </div>
    <div class="info-banner">
      <i class="fas fa-info-circle"></i>
      Workflow configurations are managed per module. Use the module-specific settings to configure approval chains.
    </div>
    <div class="workflow-grid">
      <div class="workflow-card" v-for="wf in workflows" :key="wf.module">
        <div class="wf-header">
          <i :class="wf.icon"></i>
          <span>{{ wf.module }}</span>
        </div>
        <div class="wf-steps">
          <div class="wf-step" v-for="(step, i) in wf.steps" :key="i">
            <span class="step-num">{{ i + 1 }}</span>
            <span>{{ step }}</span>
          </div>
        </div>
        <div class="wf-status">
          <span class="badge badge-success">Enabled</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WorkflowsTab',
  props: { tenant: { type: Object, required: true } },
  data() {
    return {
      workflows: [
        { module: 'Policy', icon: 'fas fa-file-alt', steps: ['Author → Review', 'Reviewer → Approve', 'Approver → Publish'] },
        { module: 'Compliance', icon: 'fas fa-clipboard-check', steps: ['Assessor → Submit', 'Manager → Approve'] },
        { module: 'Risk', icon: 'fas fa-shield-alt', steps: ['Risk Owner → Submit', 'Reviewer → Assess', 'Manager → Accept'] },
        { module: 'Audit', icon: 'fas fa-search', steps: ['Auditor → Submit Findings', 'Reviewer → Review', 'Manager → Sign-off'] },
        { module: 'Incident', icon: 'fas fa-exclamation-triangle', steps: ['Reporter → Assign', 'Handler → Resolve', 'Manager → Close'] },
        { module: 'Framework', icon: 'fas fa-cube', steps: ['Author → Review', 'Approver → Activate'] },
      ],
    }
  },
}
</script>

<style scoped>
.tab-panel { padding: 28px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-title { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
.info-banner { background: #f0f4ff; border-left: 4px solid #3f51b5; padding: 12px 16px; border-radius: 6px; font-size: 14px; color: #444; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
.workflow-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.workflow-card { border: 1px solid #e8eaf6; border-radius: 10px; padding: 16px; }
.wf-header { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; color: #3f51b5; margin-bottom: 14px; }
.wf-steps { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.wf-step { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #555; }
.step-num { width: 20px; height: 20px; background: #e8eaf6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #3f51b5; flex-shrink: 0; }
.badge { padding: 3px 9px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-success { background: #e8f5e9; color: #2e7d32; }
</style>
