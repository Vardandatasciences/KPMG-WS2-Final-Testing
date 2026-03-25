<template>
  <div :class="['sidebar', { collapsed: isCollapsed }]">
    <div class="sidebar-header">
      <div class="logo-container">
        <div class="logo-wrapper" @click="navigate('/home')">
          <img :src="logo" alt="RiskaVaire Logo" class="logo-image" />
        </div>
        <button v-if="!isCollapsed" class="toggle" @click="toggleCollapse">
          {{ isCollapsed ? '»' : '«' }}
        </button>
      </div>
    </div>

    <!-- Expand button for collapsed view -->
    <div v-if="isCollapsed" class="expand-button-container">
      <button class="expand-button" @click="toggleCollapse" title="Expand Sidebar">
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <nav class="menu">
      <!-- Policy Section -->
      <div @click="toggleSubmenu('policy')" class="menu-item has-submenu" :class="{'expanded': openMenus.policy}">
        <i class="fas fa-file-alt icon"></i>
        <span v-if="!isCollapsed">Policy</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.policy" class="submenu">
        <!-- 1. Policy Creation -->
        <div @click="toggleSubmenu('policyCreation')" class="menu-item has-submenu" :class="{'expanded': openMenus.policyCreation}">
          <i class="fas fa-plus-square icon"></i>
          <span>Policy Creation</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.policyCreation" class="submenu">
          <div class="menu-item" @click="navigate('/create-policy/create')" :class="{'active': isActive('/create-policy/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create New Policy</span>
          </div>
          <!-- <div class="menu-item" @click="navigate('/create-policy/framework')">
            <i class="fas fa-sitemap icon"></i>
            <span>Create Framework</span>
          </div> -->
          <div class="menu-item" @click="navigate('/create-policy/upload-framework')" :class="{'active': isActive('/create-policy/upload-framework')}">
            <i class="fas fa-upload icon"></i>
            <span>AI Policy Creation</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/tailoring')" :class="{'active': isActive('/create-policy/tailoring')}">
            <i class="fas fa-edit icon"></i>
            <span>Tailoring & Templating</span>
          </div>
          <div class="menu-item" @click="navigate('/create-policy/versioning')" :class="{'active': isActive('/create-policy/versioning')}">
            <i class="fas fa-code-branch icon"></i>
            <span>Versioning</span>
          </div>
        </div>

        <!-- 2. Policies List -->
        <!-- <div class="menu-item" @click="navigate('/policies-list/all')" :class="{'active': isActive('/policies-list/all')}">
          <i class="fas fa-list-alt icon"></i>
          <span>All Policies</span>
        </div> -->

        <div @click="navigate('/framework-explorer')" class="menu-item" :class="{'active': isActive('/framework-explorer')}">
            <i class="fas fa-cubes icon"></i>
            <span>Framework Explorer</span>
          </div>
        
        <div @click="navigate('/domains')" class="menu-item" :class="{'active': isActive('/domains')}">
            <i class="fas fa-sitemap icon"></i>
            <span>Domains</span>
          </div>

        <!-- 3. Policy Approval -->
        <div class="menu-item" @click="navigate('/policy/approval')" :class="{'active': isActive('/policy/approval')}">
          <i class="fas fa-check-circle icon"></i>
          <span>Policy Approval</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-approval')" :class="{'active': isActive('/framework-approval')}">
          <i class="fas fa-check-circle icon"></i>
          <span>Framework Approval</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-status-changes')" :class="{'active': isActive('/framework-status-changes')}">
          <i class="fas fa-exchange-alt icon"></i>
          <span>Status Change Requests</span>
        </div>
        <div class="menu-item" @click="navigate('/policy/data-workflow')" :class="{'active': isActive('/policy/data-workflow')}">
          <i class="fas fa-project-diagram icon"></i>
          <span>Data Workflow</span>
        </div>

        <!-- 4. Performance Analysis -->
        <div @click="toggleSubmenu('performanceAnalysis')" class="menu-item has-submenu" :class="{'expanded': openMenus.performanceAnalysis}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.performanceAnalysis" class="submenu">
          <div class="menu-item" @click="navigate('/policy/performance/kpis')" :class="{'active': isActive('/policy/performance/kpis')}">
            <i class="fas fa-chart-bar icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/policy/performance/dashboard')" :class="{'active': isActive('/policy/performance/dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>User Dashboard</span>
          </div>
        </div>

        <!-- 5. Data Workflow -->
        
      </div>

      
      
<!-- Compliance Section -->
      <div @click="toggleSubmenu('compliances')" class="menu-item has-submenu" :class="{'expanded': openMenus.compliances}">
        <i class="fas fa-check-circle icon"></i>
        <span v-if="!isCollapsed">Compliance</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.compliances" class="submenu">
        <!-- 1. Control Management -->
        <div @click="toggleSubmenu('complianceList')" class="menu-item has-submenu" :class="{'expanded': openMenus.complianceList}">
          <i class="fas fa-list icon"></i>
          <span>Control Management</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.complianceList" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/list')" :class="{'active': isActive('/compliance/list')}">
            <i class="fas fa-shield-alt icon"></i>
            <span>Controls</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/organizational-controls')" :class="{'active': isActive('/compliance/organizational-controls')}">
            <i class="fas fa-sitemap icon"></i>
            <span>Organizational Controls</span>
          </div>
        </div>

        <!-- 2. Compliance Management -->
        <div @click="toggleSubmenu('complianceManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.complianceManagement}">
          <i class="fas fa-clipboard-check icon"></i>
          <span>Compliance Management</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.complianceManagement" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/audit-management')" :class="{'active': isActive('/compliance/audit-management')}">
            <i class="fas fa-clipboard-check icon"></i>
            <span>Compliances</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/approver')" :class="{'active': isActive('/compliance/approver')}">
            <i class="fas fa-check-double icon"></i>
            <span>Compliance Approval</span>
          </div>
        </div>

        <!-- 3. Compliance Creation -->
        <div @click="toggleSubmenu('complianceCreation')" class="menu-item has-submenu" :class="{'expanded': openMenus.complianceCreation}">
          <i class="fas fa-plus-square icon"></i>
          <span>Compliance Creation</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.complianceCreation" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/create')" :class="{'active': isActive('/compliance/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Compliance</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/tailoring')" :class="{'active': isActive('/compliance/tailoring')}">
            <i class="fas fa-edit icon"></i>
            <span>Tailoring & Templating</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/versioning')" :class="{'active': isActive('/compliance/versioning')}">
            <i class="fas fa-code-branch icon"></i>
            <span>Versioning</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/baseline-configuration')" :class="{'active': isActive('/compliance/baseline-configuration')}">
            <i class="fas fa-sliders-h icon"></i>
            <span>Baseline Configuration</span>
          </div>
        </div>

        <!-- 4. Performance Analysis -->
        <div @click="toggleSubmenu('compliancePerformance')" class="menu-item has-submenu" :class="{'expanded': openMenus.compliancePerformance}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.compliancePerformance" class="submenu">
          <div class="menu-item" @click="navigate('/compliance/user-dashboard')" :class="{'active': isActive('/compliance/user-dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Compliance Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/compliance/kpi-dashboard')" :class="{'active': isActive('/compliance/kpi-dashboard')}">
            <i class="fas fa-chart-bar icon"></i>
            <span>Compliance KPI</span>
          </div>
        </div>
      </div>

      <!-- Auditor Section -->
      <div @click="toggleSubmenu('auditor')" class="menu-item has-submenu" :class="{'expanded': openMenus.auditor}">
        <i class="fas fa-user-tie icon"></i>
        <span v-if="!isCollapsed">Auditor</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.auditor" class="submenu">
        <div class="menu-item" @click="navigate('/auditor/dashboard')" :class="{'active': isActive('/auditor/dashboard')}">
          <i class="fas fa-th-large icon"></i>
          <span>Audits</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/assign')" :class="{'active': isActive('/auditor/assign')}">
          <i class="fas fa-check-square icon"></i>
          <span>Assign Audit</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/ai-audit/2075/upload')" :class="{'active': isActive('/auditor/ai-audit')}">
          <i class="fas fa-robot icon"></i>
          <span>AI Audit Upload</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/reviews')" :class="{'active': isActive('/auditor/reviews')}">
          <i class="fas fa-tasks icon"></i>
          <span>Review Audits</span>
        </div>
        <div class="menu-item" @click="navigate('/auditor/reports')" :class="{'active': isActive('/auditor/reports')}">
          <i class="fas fa-file-alt icon"></i>
          <span>Audit Reports</span>
        </div>
        <div @click="toggleSubmenu('performance')" class="menu-item has-submenu" :class="{'expanded': openMenus.performance}">
          <i class="fas fa-chart-bar icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.performance" class="submenu">
          <div class="menu-item" @click="navigate('/auditor/performance/kpi')" :class="{'active': isActive('/auditor/performance/kpi')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/auditor/performance/userdashboard')" :class="{'active': isActive('/auditor/performance/userdashboard')}">
            <i class="fas fa-chart-line icon"></i>
            <span>Dashboard</span>
          </div>
        </div>
      </div>
      <!-- Incident Section -->
      <div @click="toggleSubmenu('incident')" class="menu-item has-submenu" :class="{'expanded': openMenus.incident}">
        <i class="fas fa-exclamation-circle icon"></i>
        <span v-if="!isCollapsed">Incident</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.incident" class="submenu">
        <div @click="toggleSubmenu('incidentManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.incidentManagement}">
          <i class="fas fa-clipboard-list icon"></i>
          <span>Incident Management</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.incidentManagement" class="submenu">
          <div class="menu-item" @click="navigate('/incident/incident')" :class="{'active': isActive('/incident/incident')}">
            <i class="fas fa-list icon"></i>
            <span>Incident List</span>
          </div>
          <div class="menu-item" @click="navigate('/incident/create')" :class="{'active': isActive('/incident/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Incident</span>
          </div>
          <!-- Audit Findings List -->
          <div class="menu-item" @click="navigate('/incident/audit-findings')" :class="{'active': isActive('/incident/audit-findings')}">
            <i class="fas fa-search icon"></i>
            <span>Audit Findings</span>
          </div>
          <!-- User Tasks -->
          <div class="menu-item" @click="navigate('/incident/user-tasks')" :class="{'active': isActive('/incident/user-tasks')}">
            <i class="fas fa-user-check icon"></i>
            <span>Incident Handling</span>
          </div>
          <!-- AI Import -->
          <div class="menu-item" @click="navigate('/incident/ai-import')" :class="{'active': isActive('/incident/ai-import')}">
            <i class="fas fa-robot icon"></i>
            <span>Incident AI Import</span>
          </div>
        </div>
        <div @click="toggleSubmenu('incidentPerformance')" class="menu-item has-submenu" :class="{'expanded': openMenus.incidentPerformance}">
          <i class="fas fa-chart-line icon"></i>
          <span>Performance Analysis</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.incidentPerformance" class="submenu">
          <div class="menu-item" @click="navigate('/incident/dashboard')" :class="{'active': isActive('/incident/dashboard')}">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPIs Analysis</span>
          </div>
          <div class="menu-item" @click="navigate('/incident/performance/dashboard')" :class="{'active': isActive('/incident/performance/dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Dashboard</span>
          </div>
        </div>
      </div>
      <!-- Risk Section -->
      <div @click="toggleSubmenu('risk')" class="menu-item has-submenu" :class="{'expanded': openMenus.risk}">
        <i class="fas fa-exclamation-triangle icon"></i>
        <span v-if="!isCollapsed">Risk</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.risk" class="submenu">
        
        
        <!-- Risk Register with nested submenu -->
        <div @click="toggleSubmenu('riskRegister')" class="menu-item has-submenu" :class="{'expanded': openMenus.riskRegister}">
          <i class="fas fa-clipboard-list icon"></i>
          <span>Risk Register</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.riskRegister" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskregister-list')" :class="{'active': isActive('/risk/riskregister-list')}">
            <i class="fas fa-list icon"></i>
            <span>Risk Register List</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/create-risk')" :class="{'active': isActive('/risk/create-risk')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Risk</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/ai-document-upload')" :class="{'active': isActive('/risk/ai-document-upload')}">
            <i class="fas fa-file-upload icon"></i>
          <span>Risk Register AI</span>
        </div>
        </div>
        
        <!-- Risk Instances with nested submenu -->
        <div @click="toggleSubmenu('riskInstances')" class="menu-item has-submenu" :class="{'expanded': openMenus.riskInstances}">
          <i class="fas fa-th-list icon"></i>
          <span>Risk Instances</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.riskInstances" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskinstances-list')" :class="{'active': isActive('/risk/riskinstances-list')}">
            <i class="fas fa-list icon"></i>
            <span>Risk Incidents</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/create-instance')" :class="{'active': isActive('/risk/create-instance')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Risk Incident</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/ai-instance-upload')" :class="{'active': isActive('/risk/ai-instance-upload')}">
            <i class="fas fa-robot icon"></i>
            <span>Risk Instance AI</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/scoring')" :class="{'active': isActive('/risk/scoring')}">
            <i class="fas fa-chart-line icon"></i>
            <span>Risk Scoring</span>
          </div>
        </div>
        
        <!-- Risk Handling section -->
        <div @click="navigate('/risk/resolution')" class="menu-item" :class="{'active': isActive('/risk/resolution')}">
          <i class="fas fa-cogs icon"></i>
          <span>Risk Handling</span>
        </div>

        <!-- Risk AI Document Upload -->
        

        <!-- Risk Analytics with collapsible submenu -->
        <div @click="toggleSubmenu('riskAnalytics')" class="menu-item has-submenu" :class="{'expanded': openMenus.riskAnalytics}">
          <i class="fas fa-chart-bar icon"></i>
          <span>Risk Analytics</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="openMenus.riskAnalytics" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/risk/riskdashboard')" :class="{'active': isActive('/risk/riskdashboard')}">
            <i class="fas fa-th-large icon"></i>
            <span>Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/risk/riskkpi')" :class="{'active': isActive('/risk/riskkpi')}">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPI Dashboard</span>
          </div>
          <div v-if="isBaselFramework" class="menu-item" @click="navigate('/risk/baselkpis')" :class="{'active': isActive('/risk/baselkpis')}">
            <i class="fas fa-university icon"></i>
            <span>Basel KPIs</span>
          </div>
        </div>
        <div class="menu-item" @click="navigate('/risk/system-identified-risks')" :class="{'active': isActive('/risk/system-identified-risks')}">
          <i class="fas fa-robot icon"></i>
          <span>System Identified Risks</span>
        </div>
      </div>

      <!-- Integration Section -->
      <div @click="toggleSubmenu('integration')" class="menu-item has-submenu" :class="{'expanded': openMenus.integration}">
        <i class="fas fa-plug icon"></i>
        <span v-if="!isCollapsed">Integration</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.integration" class="submenu">
        <div class="menu-item" @click="navigate('/integration/external')" :class="{'active': isActive('/integration/external')}">
          <i class="fas fa-external-link-alt icon"></i>
          <span>External Integrations</span>
        </div>
        <div class="menu-item" @click="navigate('/integration/streamline')" :class="{'active': isActive('/integration/streamline')}">
          <i class="fas fa-stream icon"></i>
          <span>Streamline</span>
        </div>
      </div>

      <!-- Document Handling Section -->
      <div @click="navigate('/document-handling')" class="menu-item" :class="{'active': isActive('/document-handling')}">
        <i class="fas fa-folder-open icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Document Handling</span>
      </div>
      <!-- Data Retention Dashboard -->
      <div @click="navigate('/retention/dashboard')" class="menu-item" :class="{'active': isActive('/retention/dashboard')}">
        <i class="fas fa-database icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Data Retention</span>
      </div>
      <!-- KPI Dashboard Section -->
      <div @click="navigate('/kpis')" class="menu-item" :class="{'active': isActive('/kpis')}">
        <i class="fas fa-chart-line icon"></i>
        <span v-if="!isCollapsed" class="bold-text">{{ kpiLabel }}</span>
      </div>

      <!-- Data Analysis Section -->
      <div @click="toggleSubmenu('dataAnalysis')" class="menu-item has-submenu" :class="{'expanded': openMenus.dataAnalysis}">
        <i class="fas fa-chart-pie icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Data Analysis</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.dataAnalysis" class="submenu">
        <div class="menu-item" @click="navigate('/data-analysis')" :class="{'active': isActive('/data-analysis')}">
          <i class="fas fa-chart-pie icon"></i>
          <span>Data Inventory</span>
        </div>
        <div class="menu-item" @click="navigate('/ai-privacy-analysis')" :class="{'active': isActive('/ai-privacy-analysis')}">
          <i class="fas fa-robot icon"></i>
          <span>AI Privacy Analysis</span>
        </div>
      </div>

            <!-- Migration Gap Analysis Section -->
            <div @click="toggleSubmenu('frameworkMigration')" class="menu-item has-submenu" :class="{'expanded': openMenus.frameworkMigration}">
        <i class="fas fa-exchange-alt icon"></i>
        <span v-if="!isCollapsed">Change Management</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.frameworkMigration" class="submenu">
        <div class="menu-item" @click="navigate('/framework-migration')" :class="{'active': isActive('/framework-migration')}">
          <i class="fas fa-tachometer-alt icon"></i>
          <span>Overview</span>
        </div>
        <div class="menu-item" @click="navigate('/framework-migration/comparison')" :class="{'active': isActive('/framework-migration/comparison')}">
          <i class="fas fa-balance-scale icon"></i>
          <span>Framework Comparison</span>
        </div>
        <div class="menu-item" @click="navigate('/compliance/cross-framework-mapping')" :class="{'active': isActive('/compliance/cross-framework-mapping')}">
          <i class="fas fa-route icon"></i>
          <span>Gap Analysis</span>
        </div>
      </div>
      <!-- Event Handling Section -->
       <div @click="toggleSubmenu('eventHandling')" class="menu-item has-submenu" :class="{'expanded': openMenus.eventHandling}">
         <i class="fas fa-calendar-alt icon"></i>
         <span v-if="!isCollapsed">Event Handling</span>
         <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
       </div>
       <div v-if="!isCollapsed && openMenus.eventHandling" class="submenu">
         <!-- Event Management -->
         <div @click="toggleSubmenu('eventManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.eventManagement}">
           <i class="fas fa-clipboard-list icon"></i>
           <span>Event Management</span>
           <i class="fas fa-chevron-right submenu-arrow"></i>
         </div>
         <div v-if="!isCollapsed && openMenus.eventManagement" class="submenu">
           <div class="menu-item" @click="navigate('/event-handling/list')" :class="{'active': isActive('/event-handling/list')}">
             <i class="fas fa-list icon"></i>
             <span>Events List</span>
           </div>
           <div class="menu-item" @click="navigate('/event-handling/create')" :class="{'active': isActive('/event-handling/create')}">
             <i class="fas fa-plus icon"></i>
             <span>Create Event</span>
           </div>
           <div class="menu-item" @click="navigate('/event-handling/queue')" :class="{'active': isActive('/event-handling/queue')}">
             <i class="fas fa-clock icon"></i>
             <span>Events Queue</span>
           </div>
           <!-- <div class="menu-item" @click="navigate('/event-handling/evidence-attachment')" :class="{'active': isActive('/event-handling/evidence-attachment')}">
             <i class="fas fa-paperclip icon"></i>
             <span>Evidence Attachment</span>
           </div> -->
         </div>

         <!-- Event Calendar -->
         <div class="menu-item" @click="navigate('/event-handling/calendar')" :class="{'active': isActive('/event-handling/calendar')}">
           <i class="fas fa-calendar icon"></i>
           <span>Calendar</span>
         </div>

         <!-- Event Approval -->
         <div class="menu-item" @click="navigate('/event-handling/approval')" :class="{'active': isActive('/event-handling/approval')}">
           <i class="fas fa-check-circle icon"></i>
           <span>Approval</span>
         </div>

         <!-- Event Archive -->
         <div class="menu-item" @click="navigate('/event-handling/archived')" :class="{'active': isActive('/event-handling/archived')}">
           <i class="fas fa-archive icon"></i>
           <span>Archived</span>
         </div>

         <!-- Event Dashboard -->
         <div class="menu-item" @click="navigate('/event-handling/dashboard')" :class="{'active': isActive('/event-handling/dashboard')}">
           <i class="fas fa-tachometer-alt icon"></i>
           <span>Event Dashboard</span>
         </div>
       </div>

      <!-- TPRM Section -->
      <!-- TPRM Section -->
      <div @click="toggleSubmenu('tprm')" class="menu-item has-submenu menu-section-header" :class="{'expanded': openMenus.tprm}">
        <i class="fas fa-handshake icon"></i>
        <span v-if="!isCollapsed">TPRM</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.tprm" class="submenu tprm-submenu">
      <!-- Global Search -->
      <div class="menu-item" @click="navigate('/tprm-app/global-search')" :class="{'active': isActive('/tprm-app/global-search')}">
        <i class="fas fa-search icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Global Search</span>
      </div>
      <div class="menu-item" @click="navigate('/tprm-app/questionnaire-templates')" :class="{'active': isActive('/tprm-app/questionnaire-templates')}">
        <i class="fas fa-clipboard-check icon"></i>
        <span v-if="!isCollapsed" class="bold-text">Questionnaire Templates</span>
      </div>

      <!-- Procurement Section -->
      <div @click="toggleSubmenu('procurement')" class="menu-item has-submenu" :class="{'expanded': openMenus.procurement}">
        <i class="fas fa-shopping-cart icon"></i>
        <span v-if="!isCollapsed">Procurement</span>
        <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.procurement" class="submenu">
        <!-- RFP -->
        <div @click="toggleSubmenu('rfpManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.rfpManagement}">
          <i class="fas fa-file-alt icon"></i>
          <span>RFP</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.rfpManagement" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/rfp-dashboard')" :class="{'active': isActive('/tprm-app/rfp')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>RFP Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfp-list')" :class="{'active': isActive('/tprm-app/rfp-list')}">
            <i class="fas fa-list icon"></i>
            <span>Select RFP</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfp-workflow')" :class="{'active': isActive('/tprm-app/rfp-workflow')}">
            <i class="fas fa-project-diagram icon"></i>
            <span>Workflow</span>
          </div>
          <div @click="toggleSubmenu('rfpWorkflow')" class="menu-item has-submenu" :class="{'expanded': openMenus.rfpWorkflow}">
            <i class="fas fa-sitemap icon"></i>
            <span>RFP Workflow</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.rfpWorkflow" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/rfp-creation')" :class="{'active': isActive('/tprm-app/rfp-creation')}">
              <i class="fas fa-plus icon"></i>
              <span>Step 1: RFP Creation</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-approval')" :class="{'active': isActive('/tprm-app/rfp-approval')}">
              <i class="fas fa-check-circle icon"></i>
              <span>Step 2: RFP Approval</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-vendor-selection')" :class="{'active': isActive('/tprm-app/rfp-vendor-selection')}">
              <i class="fas fa-users icon"></i>
              <span>Step 3: Vendor Selection</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-url-generation')" :class="{'active': isActive('/tprm-app/rfp-url-generation')}">
              <i class="fas fa-link icon"></i>
              <span>Step 4: URL Generation</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-evaluation')" :class="{'active': isActive('/tprm-app/rfp-evaluation')}">
              <i class="fas fa-clipboard-check icon"></i>
              <span>Step 5: Evaluation</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-comparison')" :class="{'active': isActive('/tprm-app/rfp-comparison')}">
              <i class="fas fa-balance-scale icon"></i>
              <span>Step 6: Comparison</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-consensus')" :class="{'active': isActive('/tprm-app/rfp-consensus')}">
              <i class="fas fa-trophy icon"></i>
              <span>Step 7: Consensus & Award</span>
            </div>
          </div>
          <div @click="toggleSubmenu('rfpEvaluation')" class="menu-item has-submenu" :class="{'expanded': openMenus.rfpEvaluation}">
            <i class="fas fa-tasks icon"></i>
            <span>Evaluation Workflow</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.rfpEvaluation" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/approval-management')" :class="{'active': isActive('/tprm-app/approval-management')}">
              <i class="fas fa-plus icon"></i>
              <span>Workflow Creation</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/my-approvals')" :class="{'active': isActive('/tprm-app/my-approvals')}">
              <i class="fas fa-user icon"></i>
              <span>My Approvals</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/all-approvals')" :class="{'active': isActive('/tprm-app/all-approvals')}">
              <i class="fas fa-check-square icon"></i>
              <span>All Approvals</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/rfp-approval/change-request-manager')" :class="{'active': isActive('/tprm-app/rfp-approval/change-request-manager')}">
              <i class="fas fa-edit icon"></i>
              <span>Change Requests</span>
            </div>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfp-analytics')" :class="{'active': isActive('/tprm-app/rfp-analytics')}">
            <i class="fas fa-chart-bar icon"></i>
            <span>KPI Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/draft-manager')" :class="{'active': isActive('/tprm-app/draft-manager')}">
            <i class="fas fa-file-alt icon"></i>
            <span>Drafts</span>
          </div>
        </div>
        <!-- RFI -->
        <div @click="toggleSubmenu('rfiManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.rfiManagement}">
          <i class="fas fa-question-circle icon"></i>
          <span>RFI</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.rfiManagement" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/rfi-dashboard')" :class="{'active': isActive('/tprm-app/rfi')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>RFI Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfi-creation')" :class="{'active': isActive('/tprm-app/rfi-creation')}">
            <i class="fas fa-plus icon"></i>
            <span>Create RFI</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfi-list')" :class="{'active': isActive('/tprm-app/rfi-list')}">
            <i class="fas fa-list icon"></i>
            <span>Select RFI</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfi-responses')" :class="{'active': isActive('/tprm-app/rfi-responses')}">
            <i class="fas fa-reply icon"></i>
            <span>RFI Responses</span>
          </div>
        </div>
        <!-- RFQ -->
        <div @click="toggleSubmenu('rfqManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.rfqManagement}">
          <i class="fas fa-file-invoice-dollar icon"></i>
          <span>RFQ</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.rfqManagement" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/rfq-dashboard')" :class="{'active': isActive('/tprm-app/rfq')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>RFQ Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfq-creation')" :class="{'active': isActive('/tprm-app/rfq-creation')}">
            <i class="fas fa-plus icon"></i>
            <span>Create RFQ</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/rfq-list')" :class="{'active': isActive('/tprm-app/rfq-list')}">
            <i class="fas fa-list icon"></i>
            <span>Select RFQ</span>
          </div>
        </div>
        <!-- Auction -->
        <div @click="toggleSubmenu('auctionManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.auctionManagement}">
          <i class="fas fa-gavel icon"></i>
          <span>Auction</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.auctionManagement" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/auction-dashboard')" :class="{'active': isActive('/tprm-app/auction')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Auction Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/auction-creation')" :class="{'active': isActive('/tprm-app/auction-creation')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Auction</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/auction-list')" :class="{'active': isActive('/tprm-app/auction-list')}">
            <i class="fas fa-list icon"></i>
            <span>Select Auction</span>
          </div>
        </div>
        <!-- Direct -->
        <div @click="toggleSubmenu('directManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.directManagement}">
          <i class="fas fa-handshake icon"></i>
          <span>Direct</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.directManagement" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/direct-dashboard')" :class="{'active': isActive('/tprm-app/direct')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Direct Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/direct-creation')" :class="{'active': isActive('/tprm-app/direct-creation')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Direct Procurement</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/direct-list')" :class="{'active': isActive('/tprm-app/direct-list')}">
            <i class="fas fa-list icon"></i>
            <span>Select Direct</span>
          </div>
        </div>
        
        <!-- Emergency -->
        <div @click="toggleSubmenu('emergencyManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.emergencyManagement}">
          <i class="fas fa-exclamation-triangle icon"></i>
          <span>Emergency</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.emergencyManagement" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/emergency-dashboard')" :class="{'active': isActive('/tprm-app/emergency')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Emergency Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/emergency-creation')" :class="{'active': isActive('/tprm-app/emergency-creation')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Emergency Procurement</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/emergency-list')" :class="{'active': isActive('/tprm-app/emergency-list')}">
            <i class="fas fa-list icon"></i>
            <span>Select Emergency</span>
          </div>
        </div>
      </div>

      <div @click="toggleSubmenu('vendorManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.vendorManagement}">
        <i class="fas fa-building icon"></i>
        <span>Due Diligence</span>
        <i class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.vendorManagement" class="submenu">
        <div class="menu-item" @click="navigate('/tprm-app/vendor-dashboard')" :class="{'active': isActive('/tprm-app/vendor-dashboard')}">
          <i class="fas fa-tachometer-alt icon"></i>
          <span>Dashboard</span>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/vendor-kpi-dashboard')" :class="{'active': isActive('/tprm-app/vendor-kpi-dashboard')}">
          <i class="fas fa-chart-pie icon"></i>
          <span>KPI Dashboard</span>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/vendor-registration')" :class="{'active': isActive('/tprm-app/vendor-registration')}">
          <i class="fas fa-plus icon"></i>
          <span>Vendor Registration</span>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/vendor-verification')" :class="{'active': isActive('/tprm-app/vendor-verification')}">
          <i class="fas fa-search icon"></i>
          <span>External Screening</span>
        </div>
        <div @click="toggleSubmenu('vendorQuestionnaire')" class="menu-item has-submenu" :class="{'expanded': openMenus.vendorQuestionnaire}">
          <i class="fas fa-clipboard-check icon"></i>
          <span>Questionnaire Management</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.vendorQuestionnaire" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/vendor-questionnaire')" :class="{'active': isActive('/tprm-app/vendor-questionnaire')}">
            <i class="fas fa-tools icon"></i>
            <span>Builder</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/vendor-questionnaire-assignment')" :class="{'active': isActive('/tprm-app/vendor-questionnaire-assignment')}">
            <i class="fas fa-user-check icon"></i>
            <span>Assignment</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/vendor-questionnaire-response')" :class="{'active': isActive('/tprm-app/vendor-questionnaire-response')}">
            <i class="fas fa-reply icon"></i>
            <span>Response</span>
          </div>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/vendor-risk-scoring')" :class="{'active': isActive('/tprm-app/vendor-risk-scoring')}">
          <i class="fas fa-shield-alt icon"></i>
          <span>Risk Scoring</span>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/vendor-lifecycle')" :class="{'active': isActive('/tprm-app/vendor-lifecycle')}">
          <i class="fas fa-sync-alt icon"></i>
          <span>Lifecycle Tracker</span>
        </div>
        <div @click="toggleSubmenu('vendorApproval')" class="menu-item has-submenu" :class="{'expanded': openMenus.vendorApproval}">
          <i class="fas fa-check-circle icon"></i>
          <span>Vendor Approval</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.vendorApproval" class="submenu nested-submenu">
          <div class="menu-item" @click="navigate('/tprm-app/vendor-approval-dashboard')" :class="{'active': isActive('/tprm-app/vendor-approval-dashboard')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Approval Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/vendor-approval-workflow-creator')" :class="{'active': isActive('/tprm-app/vendor-approval-workflow-creator')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Workflow</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/vendor-my-approvals')" :class="{'active': isActive('/tprm-app/vendor-my-approvals')}">
            <i class="fas fa-user icon"></i>
            <span>My Approvals</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/vendor-all-approvals')" :class="{'active': isActive('/tprm-app/vendor-all-approvals')}">
            <i class="fas fa-check-square icon"></i>
            <span>All Approvals</span>
          </div>
        </div>
      </div>
      <div @click="toggleSubmenu('vendorMgmtModule')" class="menu-item has-submenu" :class="{'expanded': openMenus.vendorMgmtModule}">
        <i class="fas fa-building icon"></i>
        <span>Vendor Management</span>
        <i class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.vendorMgmtModule" class="submenu">
        <div class="menu-item" @click="navigate('/tprm-app/add-vendor')" :class="{'active': isActive('/tprm-app/add-vendor')}">
          <i class="fas fa-plus icon"></i>
          <span>Add Vendor</span>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/all-vendors')" :class="{'active': isActive('/tprm-app/all-vendors')}">
          <i class="fas fa-list icon"></i>
          <span>All Vendors</span>
        </div>
        <div class="menu-item" @click="navigate('/tprm-app/vendor-risks')" :class="{'active': isActive('/tprm-app/vendor-risks')}">
          <i class="fas fa-shield-alt icon"></i>
          <span>Vendor Risks</span>
        </div>
      </div>
      <div @click="toggleSubmenu('contractManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.contractManagement}">
        <i class="fas fa-file-contract icon"></i>
        <span>Contract Management</span>
        <i class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.contractManagement" class="submenu">
        <!-- contract content -->
          <div class="menu-item" @click="navigate('/tprm-app/contractdashboard')" :class="{'active': isActive('/tprm-app/contract')}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Contract Dashboard</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/contracts')" :class="{'active': isActive('/tprm-app/contracts')}">
            <i class="fas fa-list icon"></i>
            <span>All Contracts</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/contracts/create')" :class="{'active': isActive('/tprm-app/contracts/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create Contract</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/vendors')" :class="{'active': isActive('/tprm-app/vendors')}">
            <i class="fas fa-building icon"></i>
            <span>Vendor Contracts</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/contract-approval-assignment')" :class="{'active': isActive('/tprm-app/contract-approval-assignment')}">
            <i class="fas fa-user-check icon"></i>
            <span>Approval Assignment</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/my-contract-approvals')" :class="{'active': isActive('/tprm-app/my-contract-approvals')}">
            <i class="fas fa-check-circle icon"></i>
            <span>My Approvals</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/archive')" :class="{'active': isActive('/tprm-app/archive')}">
            <i class="fas fa-archive icon"></i>
            <span>Archive</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/search')" :class="{'active': isActive('/tprm-app/search')}">
            <i class="fas fa-search icon"></i>
            <span>Search</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/contract-comparison')" :class="{'active': isActive('/tprm-app/contract-comparison')}">
            <i class="fas fa-balance-scale icon"></i>
            <span>Contract Comparison</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/analytics')" :class="{'active': isActive('/tprm-app/analytics')}">
            <i class="fas fa-chart-bar icon"></i>
            <span>Analytics</span>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/contract-kpi-dashboard')" :class="{'active': isActive('/tprm-app/contract-kpi-dashboard')}">
            <i class="fas fa-chart-pie icon"></i>
            <span>KPI Dashboard</span>
          </div>
          <div @click="toggleSubmenu('contractAudit')" class="menu-item has-submenu" :class="{'expanded': openMenus.contractAudit}">
            <i class="fas fa-eye icon"></i>
            <span>Audit</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.contractAudit" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/audit/dashboard')" :class="{'active': isActive('/tprm-app/audit/dashboard')}">
              <i class="fas fa-tachometer-alt icon"></i>
              <span>Audit Dashboard</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/contract-audit/all')" :class="{'active': isActive('/tprm-app/contract-audit/all')}">
              <i class="fas fa-list icon"></i>
              <span>All Audits</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/contract-audit/create')" :class="{'active': isActive('/tprm-app/contract-audit/create')}">
              <i class="fas fa-plus icon"></i>
              <span>Create Audit</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/contract-audit/reports')" :class="{'active': isActive('/tprm-app/contract-audit/reports')}">
              <i class="fas fa-file-alt icon"></i>
              <span>Audit Reports</span>
            </div>
          </div>
      </div>

      <div @click="toggleSubmenu('slaManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.slaManagement}">
        <i class="fas fa-handshake icon"></i>
        <span>Service Level Agreement</span>
        <i class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.slaManagement" class="submenu">
        <!-- SLA content -->
          <div @click="toggleSubmenu('slaDashboard')" class="menu-item has-submenu" :class="{'expanded': openMenus.slaDashboard}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>SLA Dashboard</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.slaDashboard" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/dashboard')" :class="{'active': isActive('/tprm-app/dashboard')}">
              <i class="fas fa-chart-line icon"></i>
              <span>SLA Overview</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/performance')" :class="{'active': isActive('/tprm-app/performance')}">
              <i class="fas fa-chart-bar icon"></i>
              <span>Performance Summary</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/kpi-dashboard')" :class="{'active': isActive('/tprm-app/kpi-dashboard')}">
              <i class="fas fa-chart-pie icon"></i>
              <span>KPI Dashboard</span>
            </div>
          </div>
          <div @click="toggleSubmenu('slaList')" class="menu-item has-submenu" :class="{'expanded': openMenus.slaList}">
            <i class="fas fa-list icon"></i>
            <span>SLA Management</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.slaList" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/slas')" :class="{'active': isActive('/tprm-app/slas')}">
              <i class="fas fa-list-alt icon"></i>
              <span>All SLAs</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/slas/active')" :class="{'active': isActive('/tprm-app/slas/active')}">
              <i class="fas fa-check-circle icon"></i>
              <span>Active SLAs</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/slas/expiring')" :class="{'active': isActive('/tprm-app/slas/expiring')}">
              <i class="fas fa-clock icon"></i>
              <span>Expiring SLAs</span>
            </div>
          </div>
          <div class="menu-item" @click="navigate('/tprm-app/slas/create')" :class="{'active': isActive('/tprm-app/slas/create')}">
            <i class="fas fa-plus icon"></i>
            <span>Create/Upload SLA</span>
          </div>
          <div @click="toggleSubmenu('slaAudit')" class="menu-item has-submenu" :class="{'expanded': openMenus.slaAudit}">
            <i class="fas fa-clipboard-check icon"></i>
            <span>Audit Management</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.slaAudit" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/audit')" :class="{'active': isActive('/tprm-app/audit')}">
              <i class="fas fa-tachometer-alt icon"></i>
              <span>Audit Dashboard</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/audit/create')" :class="{'active': isActive('/tprm-app/audit/create')}">
              <i class="fas fa-plus icon"></i>
              <span>Create Audit</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/audit/my-audits')" :class="{'active': isActive('/tprm-app/audit/my-audits')}">
              <i class="fas fa-user icon"></i>
              <span>My Audits</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/audit/reports')" :class="{'active': isActive('/tprm-app/audit/reports')}">
              <i class="fas fa-file-alt icon"></i>
              <span>Audit Reports</span>
            </div>
          </div>
          <div @click="toggleSubmenu('slaApprovals')" class="menu-item has-submenu" :class="{'expanded': openMenus.slaApprovals}">
            <i class="fas fa-check-double icon"></i>
            <span>SLA Approvals</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.slaApprovals" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/slas/approvals')" :class="{'active': isActive('/tprm-app/slas/approvals')}">
              <i class="fas fa-user icon"></i>
              <span>My Approvals</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/slas/approval-assignment')" :class="{'active': isActive('/tprm-app/slas/approval-assignment')}">
              <i class="fas fa-user-check icon"></i>
              <span>Assign Approvals</span>
            </div>
          </div>
      </div>

      <div @click="toggleSubmenu('bcpManagement')" class="menu-item has-submenu" :class="{'expanded': openMenus.bcpManagement}">
        <i class="fas fa-shield-alt icon"></i>
        <span>BCP/DRP Management</span>
        <i class="fas fa-chevron-right submenu-arrow"></i>
      </div>
      <div v-if="!isCollapsed && openMenus.bcpManagement" class="submenu">
        <!-- BCP content -->
          <div @click="toggleSubmenu('bcpPlan')" class="menu-item has-submenu" :class="{'expanded': openMenus.bcpPlan}">
            <i class="fas fa-upload icon"></i>
            <span>Plan Phase</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.bcpPlan" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/bcp/vendor-upload')" :class="{'active': isActive('/tprm-app/bcp/vendor-upload')}">
              <i class="fas fa-upload icon"></i>
              <span>Upload Plans</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/plan-submission-ocr')" :class="{'active': isActive('/tprm-app/bcp/plan-submission-ocr')}">
              <i class="fas fa-file-upload icon"></i>
              <span>Plan Submission & OCR</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/evaluation')" :class="{'active': isActive('/tprm-app/bcp/evaluation')}">
              <i class="fas fa-clipboard-check icon"></i>
              <span>Plan Evaluation</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/library')" :class="{'active': isActive('/tprm-app/bcp/library')}">
              <i class="fas fa-book icon"></i>
              <span>Plan Library</span>
            </div>
          </div>
          <div @click="toggleSubmenu('bcpTesting')" class="menu-item has-submenu" :class="{'expanded': openMenus.bcpTesting}">
            <i class="fas fa-vial icon"></i>
            <span>Testing Phase</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.bcpTesting" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/bcp/questionnaire-workflow')" :class="{'active': isActive('/tprm-app/bcp/questionnaire-workflow')}">
              <i class="fas fa-project-diagram icon"></i>
              <span>Questionnaire Creation</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/questionnaire-builder')" :class="{'active': isActive('/tprm-app/bcp/questionnaire-builder')}">
              <i class="fas fa-edit icon"></i>
              <span>Questionnaire Review</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/questionnaire-library')" :class="{'active': isActive('/tprm-app/bcp/questionnaire-library')}">
              <i class="fas fa-book icon"></i>
              <span>Questionnaire Library</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/questionnaire-assignment-workflow')" :class="{'active': isActive('/tprm-app/bcp/questionnaire-assignment-workflow')}">
              <i class="fas fa-user-check icon"></i>
              <span>Questionnaire Assignment</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/questionnaire-assignment')" :class="{'active': isActive('/tprm-app/bcp/questionnaire-assignment')}">
              <i class="fas fa-reply icon"></i>
              <span>Questionnaire Answering</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/approval-assignment')" :class="{'active': isActive('/tprm-app/bcp/approval-assignment')}">
              <i class="fas fa-user-check icon"></i>
              <span>Approval Assignment</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/my-approvals')" :class="{'active': isActive('/tprm-app/bcp/my-approvals')}">
              <i class="fas fa-user icon"></i>
              <span>My Approvals</span>
            </div>
          </div>
          <div @click="toggleSubmenu('bcpConsole')" class="menu-item has-submenu" :class="{'expanded': openMenus.bcpConsole}">
            <i class="fas fa-tachometer-alt icon"></i>
            <span>Owner Console</span>
            <i class="fas fa-chevron-right submenu-arrow"></i>
          </div>
          <div v-if="!isCollapsed && openMenus.bcpConsole" class="submenu nested-submenu">
            <div class="menu-item" @click="navigate('/tprm-app/bcp/dashboard')" :class="{'active': isActive('/tprm-app/bcp/dashboard')}">
              <i class="fas fa-chart-line icon"></i>
              <span>Analytics Dashboard</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/kpi-dashboard')" :class="{'active': isActive('/tprm-app/bcp/kpi-dashboard')}">
              <i class="fas fa-chart-pie icon"></i>
              <span>KPI Dashboard</span>
            </div>
            <div class="menu-item" @click="navigate('/tprm-app/bcp/risk-analytics')" :class="{'active': isActive('/tprm-app/bcp/risk-analytics')}">
              <i class="fas fa-shield-alt icon"></i>
              <span>Risk Analytics</span>
            </div>
          </div>
      </div>
      </div>

    </nav>

    <div class="bottom-section">
      <!-- System Logs Tab -->
      <div @click="navigate('/system-logs')" class="system-logs-menu-item" :class="{'active': isActive('/system-logs')}">
        <i class="fas fa-file-alt icon"></i>
        <span v-if="!isCollapsed" class="bold-text">System Logs</span>
      </div>

      <!-- User Profile Menu Item -->
       <div @click="toggleSubmenu('userProfile')" class="menu-item has-submenu" :class="{'active': isActive('/user-profile')}">
         <i class="fas fa-user icon"></i>
         <span v-if="!isCollapsed">{{ username }}</span>
         <i v-if="!isCollapsed" class="fas fa-chevron-right submenu-arrow"></i>
       </div>
       <div v-if="!isCollapsed && openMenus.userProfile" class="submenu">
         <!-- User Profile Link -->
         <div class="menu-item" @click="navigate('/user-profile')" :class="{'active': isActive('/user-profile')}">
           <i class="fas fa-user-circle icon"></i>
           <span>My Profile</span>
         </div>
         
        <!-- Help Section -->
        <div @click="toggleSubmenu('help')" class="menu-item has-submenu" :class="{'expanded': openMenus.help}">
          <i class="fas fa-question-circle icon"></i>
          <span>Help</span>
          <i class="fas fa-chevron-right submenu-arrow"></i>
        </div>
        <div v-if="!isCollapsed && openMenus.help" class="submenu">
          <div class="menu-item" @click="navigate('/help/contact-us')" :class="{'active': isActive('/help/contact-us')}">
            <i class="fas fa-phone-alt icon"></i>
            <span>Contact Us</span>
          </div>
          <div class="menu-item" @click="navigate('/help/faqs')" :class="{'active': isActive('/help/faqs')}">
            <i class="fas fa-question icon"></i>
            <span>FAQs (Frequently Asked Questions)</span>
          </div>
          <div class="menu-item" @click="navigate('/help/user-manual')" :class="{'active': isActive('/help/user-manual')}">
            <i class="fas fa-book icon"></i>
            <span>User Manual</span>
          </div>
          <div class="menu-item" @click="navigate('/help/privacy-security')" :class="{'active': isActive('/help/privacy-security')}">
            <i class="fas fa-shield-alt icon"></i>
            <span>Privacy & Security</span>
          </div>
          <div class="menu-item" @click="navigate('/help/help-us-improve')" :class="{'active': isActive('/help/help-us-improve')}">
            <i class="fas fa-lightbulb icon"></i>
            <span>Feedback</span>
          </div>
          <div class="menu-item" @click="navigate('/help/acknowledgement')" :class="{'active': isActive('/help/acknowledgement')}">
            <i class="fas fa-handshake icon"></i>
            <span>Acknowledgement</span>
          </div>
        </div>

         <!-- Settings -->
         <div @click="navigate('/settings')" class="menu-item" :class="{'active': isActive('/settings')}">
           <i class="fas fa-cog icon"></i>
           <span>Settings</span>
         </div>
       </div>
     </div>
      
      <!-- RBAC Test -->
      <!-- <div class="menu-item" @click="navigate('/rbac-test')" :class="{'active': isActive('/rbac-test')}">
        <i class="fas fa-shield-alt icon"></i>
        <span v-if="!isCollapsed">🔐 RBAC Test</span>
      </div> -->
      
      <!-- Logout Button -->
      <!-- <div class="logout-button" @click="handleLogoutClick">
        <i class="fas fa-sign-out-alt icon"></i>
        <span v-if="!isCollapsed">Logout</span>
      </div> -->
    </div>
</template>

<script>
import {  API_ENDPOINTS } from '../../config/api.js'
import axios from 'axios'
import authService from '../../services/authService.js'

import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import logo from '../../assets/RiskaVaire.png'
import '@fortawesome/fontawesome-free/css/all.min.css'
import eventBus, { LOGOUT_EVENT } from '../../utils/eventBus.js'

export default {
  name: 'PolicySidebar',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()
    const isCollapsed = ref(false)
    const themeMenuOpen = ref(false)
    const currentTheme = ref('light')
    const isBottomSectionCollapsed = ref(true) // Default to collapsed)
    const currentColorblindMode = ref(null)
    const username = ref('User')
    
    // Compute current route path for active highlighting
    const currentPath = computed(() => route.path)
    const selectedFrameworkName = computed(() => {
      const framework = store.getters['framework/selectedFramework']
      const name = framework?.name?.trim()
      return name && name.toLowerCase() !== 'all frameworks' ? name : 'All Frameworks'
    })
    const kpiLabel = computed(() => {
      return selectedFrameworkName.value === 'All Frameworks'
        ? 'KPIs'
        : `${selectedFrameworkName.value} KPIs`
    })
     // Check if Basel III framework is selected
     const isBaselFramework = computed(() => {
      const frameworkName = selectedFrameworkName.value.toLowerCase()
      return frameworkName.includes('basel') && (frameworkName.includes('iii') || frameworkName.includes('3'))
    })
    
    const openMenus = ref({
      policy: false,
      policyCreation: false,
      performanceAnalysis: false,
      frameworkMigration: false,
      integration: false,
      compliance: false,
      risk: false,
      riskRegister: false,
      riskInstances: false,
      riskAnalytics: false,
      auditor: false,
      incident: false,
      incidentManagement: false,
      incidentPerformance: false,
      dashboard: false,
      complianceDashboard: false,
      policyManagement: false,
      createPolicy: false,
      performance: false,
      auditFindings: false,
      dataAnalysis: false,
      compliances: false,
      compliancesView: false,
      complianceCreation: false,
      complianceList: false,
      complianceManagement: false,
      compliancePerformance: false,
      // TPRM Menu States
      rfpManagement: false,
      rfpWorkflow: false,
      rfpEvaluation: false,
      vendorManagement: false,
      vendorQuestionnaire: false,
      vendorApproval: false,
      contractManagement: false,
      contractAudit: false,
      slaManagement: false,
      slaDashboard: false,
      slaList: false,
      slaAudit: false,
      slaApprovals: false,
      bcpManagement: false,
      bcpPlan: false,
      bcpTesting: false,
      bcpConsole: false,
      eventHandling: false,
      eventManagement: false,
      help: false,
      domains: false
    })

    // Check if route is active
    const isActive = (path) => {
      // Exact match
      if (currentPath.value === path) {
        return true
      }
     
      // Special handling for framework migration routes
      // Only match parent route if we're exactly on it, not on child routes
      if (path === '/framework-migration') {
        return currentPath.value === '/framework-migration'
      }
     
      // For other routes, check if current path starts with the given path
      return currentPath.value.startsWith(path + '/')
    }
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    const toggleBottomSection = () => {
      isBottomSectionCollapsed.value = !isBottomSectionCollapsed.value
    }

    const toggleSubmenu = (section) => {
      openMenus.value[section] = !openMenus.value[section]
    }

    // Close all open menus
    const closeAllMenus = () => {
      Object.keys(openMenus.value).forEach(key => {
        openMenus.value[key] = false
      })
    }

    const toggleThemeMenu = () => {
      themeMenuOpen.value = !themeMenuOpen.value
    }

    const setTheme = async (theme) => {
      try {
        const userId = localStorage.getItem('user_id')
        const hasUpdateThemeApi = API_ENDPOINTS && typeof API_ENDPOINTS.UPDATE_USER_THEME === 'function'
        if (userId && hasUpdateThemeApi) {
          // Save to backend
          await axios.put(API_ENDPOINTS.UPDATE_USER_THEME(userId), {
            theme: theme
          }, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          })
        } else if (userId && !hasUpdateThemeApi) {
          console.log('Theme API endpoint not configured; applying theme locally only')
        }
        
        // Apply theme globally to all root elements
        currentTheme.value = theme
        document.documentElement.setAttribute('data-theme', theme)
        document.body.setAttribute('data-theme', theme)
        const appElement = document.getElementById('app')
        if (appElement) {
          appElement.setAttribute('data-theme', theme)
        }
        
        // Save to localStorage as backup
        localStorage.setItem('selected-theme', theme)
        
        // Note: Color-blindness mode is independent of theme
        // If color-blindness is active, it will still work with the new theme
      } catch (error) {
        console.error('Error setting theme:', error)
        // Still apply theme locally even if backend fails
        currentTheme.value = theme
        document.documentElement.setAttribute('data-theme', theme)
        document.body.setAttribute('data-theme', theme)
        const appElement = document.getElementById('app')
        if (appElement) {
          appElement.setAttribute('data-theme', theme)
        }
        localStorage.setItem('selected-theme', theme)
      }
    }

    // Set color-blindness mode
    const setColorblindMode = async (mode) => {
      try {
        // Remove existing color-blindness attributes
        document.documentElement.removeAttribute('data-colorblind')
        document.body.removeAttribute('data-colorblind')
        const appElement = document.getElementById('app')
        if (appElement) {
          appElement.removeAttribute('data-colorblind')
        }
        
        // Apply new color-blindness mode if provided
        if (mode) {
          currentColorblindMode.value = mode
          document.documentElement.setAttribute('data-colorblind', mode)
          document.body.setAttribute('data-colorblind', mode)
          if (appElement) {
            appElement.setAttribute('data-colorblind', mode)
          }
          localStorage.setItem('selected-colorblind', mode)
          console.log(`✅ Color-blindness mode activated: ${mode}`)
        } else {
          // Disable color-blindness mode
          currentColorblindMode.value = null
          localStorage.removeItem('selected-colorblind')
          console.log('✅ Color-blindness mode disabled')
        }
        
        // Save to backend if user is logged in
        const userId = localStorage.getItem('user_id')
        const hasUpdateThemeApi = API_ENDPOINTS && typeof API_ENDPOINTS.UPDATE_USER_THEME === 'function'
        if (userId && hasUpdateThemeApi) {
          try {
            await axios.put(API_ENDPOINTS.UPDATE_USER_THEME(userId), {
              theme: currentTheme.value,
              colorblind: mode || null
            }, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
              }
            })
          } catch (backendError) {
            console.log('Could not save color-blindness preference to backend:', backendError)
          }
        } else if (userId && !hasUpdateThemeApi) {
          console.log('Theme API endpoint not configured; skipping backend color-blindness save')
        }
      } catch (error) {
        console.error('Error setting color-blindness mode:', error)
        // Still apply locally even if backend fails
        if (mode) {
          currentColorblindMode.value = mode
          document.documentElement.setAttribute('data-colorblind', mode)
          document.body.setAttribute('data-colorblind', mode)
          const appElement = document.getElementById('app')
          if (appElement) {
            appElement.setAttribute('data-colorblind', mode)
          }
          localStorage.setItem('selected-colorblind', mode)
        } else {
          currentColorblindMode.value = null
          localStorage.removeItem('selected-colorblind')
        }
      }
    }
    
    // Load theme preference from backend or local storage (unused function)
    // const loadUserTheme = async () => {
    //   try {
    //     const userId = localStorage.getItem('user_id')
    //     let theme = 'light'
    //     let colorblind = null
    //     
    //     if (userId) {
    //       try {
    //         // Try to load from backend
    //         const response = await axios.get(API_ENDPOINTS.GET_USER_THEME(userId), {
    //           headers: {
    //             'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    //             'Content-Type': 'application/json'
    //           }
    //         })
    //         
    //         if (response.data && response.data.status === 'success') {
    //           theme = response.data.theme || 'light'
    //           colorblind = response.data.colorblind || null
    //         }
    //       } catch (backendError) {
    //         console.log('Could not load theme from backend, using localStorage:', backendError)
    //         // Fallback to localStorage
    //         theme = localStorage.getItem('selected-theme') || 'light'
    //         colorblind = localStorage.getItem('selected-colorblind') || null
    //       }
    //     } else {
    //       // No user ID, use localStorage
    //       theme = localStorage.getItem('selected-theme') || 'light'
    //       colorblind = localStorage.getItem('selected-colorblind') || null
    //     }
    //     
    //     // Apply theme globally to all root elements
    //     currentTheme.value = theme
    //     document.documentElement.setAttribute('data-theme', theme)
    //     document.body.setAttribute('data-theme', theme)
    //     const appElement = document.getElementById('app')
    //     if (appElement) {
    //       appElement.setAttribute('data-theme', theme)
    //     }
    //     localStorage.setItem('selected-theme', theme)
    //     
    //     // Apply color-blindness mode if set
    //     if (colorblind) {
    //       currentColorblindMode.value = colorblind
    //       document.documentElement.setAttribute('data-colorblind', colorblind)
    //       document.body.setAttribute('data-colorblind', colorblind)
    //       if (appElement) {
    //         appElement.setAttribute('data-colorblind', colorblind)
    //       }
    //       localStorage.setItem('selected-colorblind', colorblind)
    //       console.log(`✅ Loaded color-blindness mode: ${colorblind}`)
    //     } else {
    //       // Ensure color-blindness is disabled
    //       currentColorblindMode.value = null
    //       document.documentElement.removeAttribute('data-colorblind')
    //       document.body.removeAttribute('data-colorblind')
    //       if (appElement) {
    //         appElement.removeAttribute('data-colorblind')
    //       }
    //     }
    //   } catch (error) {
    //     console.error('Error loading theme:', error)
    //     // Default to light theme if error
    //     const fallbackTheme = localStorage.getItem('selected-theme') || 'light'
    //     const fallbackColorblind = localStorage.getItem('selected-colorblind') || null
    //     currentTheme.value = fallbackTheme
    //     document.documentElement.setAttribute('data-theme', fallbackTheme)
    //     document.body.setAttribute('data-theme', fallbackTheme)
    //     const appElement = document.getElementById('app')
    //     if (appElement) {
    //       appElement.setAttribute('data-theme', fallbackTheme)
    //     }
    //     
    //     if (fallbackColorblind) {
    //       currentColorblindMode.value = fallbackColorblind
    //       document.documentElement.setAttribute('data-colorblind', fallbackColorblind)
    //       document.body.setAttribute('data-colorblind', fallbackColorblind)
    //       if (appElement) {
    //         appElement.setAttribute('data-colorblind', fallbackColorblind)
    //       }
    //     }
    //   }
    // }

    const handleDashboardClick = () => {
      toggleSubmenu('dashboard')
      if (!openMenus.value.dashboard) {
        router.push('/policy/dashboard')
      }
    }

    const navigate = (path) => {
      // Simple navigation without interceptor interference
      router.push(path)
    }

    // Get logged in username
    const fetchUsername = async () => {
      try {
        // Prefer explicit name keys set during auth/profile flows
        const storedUserName = localStorage.getItem('user_name')
        const storedFullName = localStorage.getItem('fullName')
        const storedUsername = localStorage.getItem('username')

        // Fallback to any stored user object
        const userData = localStorage.getItem('current_user') || localStorage.getItem('user')
        let fallback = 'User'

        if (userData) {
          try {
            const userObj = JSON.parse(userData)
            fallback =
              userObj.full_name ||
              userObj.firstName && userObj.lastName ? `${userObj.firstName} ${userObj.lastName}` :
              userObj.UserName ||
              userObj.user_name ||
              userObj.username ||
              fallback
          } catch (e) {
            console.error('Error parsing user data:', e)
          }
        }
        if (storedFullName && storedFullName !== 'null') {
          username.value = storedFullName
        } else if (storedUsername && storedUsername !== 'null') {
          username.value = storedUsername
        } else if (storedUserName && storedUserName !== 'null') {
          username.value = storedUserName
        } else {
          username.value = fallback
        }
      } catch (e) {
        console.error('Error fetching username:', e)
        username.value = 'User'
      }
    }

    // Handle logout event
    const handleLogout = () => {
    }

    // Handle login event
    const handleLogin = () => {
      // Handle login event if needed
    }

    // Handle logout click
    const handleLogoutClick = async () => {
      try {
        console.log('🔄 Logging out...')
        await authService.logout()
        console.log('✅ Logout successful')
        router.push('/login')
      } catch (error) {
        console.error('❌ Logout error:', error)
        // Force redirect to login even if logout fails
        router.push('/login')
      }
    }

    onMounted(() => {
      fetchUsername();
      const savedTheme = localStorage.getItem('selected-theme') || 'light'
      setTheme(savedTheme)
      
      // Listen for user data updates
      window.addEventListener('userDataUpdated', fetchUsername)
      
      // Listen for authentication events
      window.addEventListener('authChanged', handleLogin)
      eventBus.on(LOGOUT_EVENT, handleLogout)
      
      // Listen for clicks outside sidebar to close all menus
      const handleClickOutside = (event) => {
        const sidebar = document.querySelector('.sidebar')
        const clickedElement = event.target
        
        // Check if click is outside the sidebar
        if (sidebar && !sidebar.contains(clickedElement)) {
          closeAllMenus()
        }
      }
      
      // Add click listener to document
      document.addEventListener('click', handleClickOutside)
      
      // Store handler for cleanup
      window.sidebarClickHandler = handleClickOutside
    })
    onUnmounted(() => {
      window.removeEventListener('userDataUpdated', fetchUsername)
      window.removeEventListener('authChanged', handleLogin)
      eventBus.off(LOGOUT_EVENT, handleLogout)
      
      // Remove click outside listener
      if (window.sidebarClickHandler) {
        document.removeEventListener('click', window.sidebarClickHandler)
        delete window.sidebarClickHandler
      }
    })

    return {
      isCollapsed,
      openMenus,
      themeMenuOpen,
      currentTheme,
      logo,
      username,
      toggleCollapse,
      toggleSubmenu,
      toggleThemeMenu,
      setTheme,
      currentColorblindMode,
      toggleBottomSection,
      setColorblindMode,
      navigate,
      handleDashboardClick,
      isActive,
      handleLogoutClick,
      kpiLabel,
      isBaselFramework
    }
  }
}
</script>

<style scoped>
/* Import the existing CSS file */
@import './sidebar.css';

/* System Logs menu item style */
.system-logs-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}
.system-logs-menu-item:hover {
  background: #f0f4ff;
}
.system-logs-menu-item .icon {
  margin-right: 12px;
  font-size: 1.2rem;
  color: #575757 !important;
}
.system-logs-menu-item.active {
  background-color: rgba(0, 51, 153, 0.1);
  color: #003399 !important;
  font-weight: 600;
  border-left: 3px solid #003399;
}
.system-logs-menu-item.active .icon {
  color: #003399 !important;
}
/* Help menu item style */
.help-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
  font-weight: 600;
}
.help-menu-item:hover {
  background: #f0f4ff;
}
.help-menu-item .icon {
  margin-right: 12px;
  font-size: 1.2rem;
  color: #575757 !important;
}
.help-theme {
  color: #646464 !important;
}
.help-submenu {
  background: #f8f9fa;
  border-left: 3px solid #007bff;
}
.help-submenu .help-menu-item {
  padding: 10px 20px 10px 40px;
  font-weight: 500;
  font-size: 0.8rem;
}
.help-submenu .help-menu-item:hover {
  background: #e5e7eb; /* Ash/gray color instead of blue */
}
.help-submenu .help-menu-item.active {
  background: #007bff;
  color: white !important;
}
.help-submenu .help-menu-item.active .icon {
  color: white !important;
}

/* Color Blindness Menu Styling */
.colorblind-divider {
  padding: 8px 20px 8px 40px !important;
  margin-top: 8px;
  margin-bottom: 4px;
  cursor: default !important;
  border-top: 1px solid #e5e7eb;
  padding-top: 12px !important;
}

.colorblind-divider:hover {
  background: transparent !important;
}

.colorblind-divider span {
  color: #6b7280;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
}

.theme-menu-item[data-colorblind] {
  position: relative;
}

.theme-menu-item.active {
  background: #007bff;
  color: white !important;
}

.theme-menu-item.active .icon {
  color: white !important;
}



/* Expand button styles */
.expand-button-container {
  display: flex;
  justify-content: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color, #333);
  flex-shrink: 0;
  background-color: #ffffff;
}

.expand-button {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: var(--hover-bg, #333);
  border: 1px solid var(--border-color, #333);
  color: var(--text-primary, #ffffff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.expand-button:hover {
  background-color: var(--active-bg, #4a90e2);
  transform: scale(1.1);
}

.expand-button i {
  font-size: 0.9rem;
}

/* Active menu item styles */
.menu-item.active {
  background-color: rgba(0, 51, 153, 0.1);
  color: #003399 !important;
  font-weight: 600;
  border-left: 3px solid #003399;
}

.menu-item.active .icon {
  color: #003399 !important;
}

/* Dark theme active item adjustments */
[data-theme="dark"] .menu-item.active {
  background-color: rgba(64, 115, 255, 0.2);
  color: #4073ff !important;
  border-left: 3px solid #4073ff;
}

[data-theme="dark"] .menu-item.active .icon {
  color: #4073ff !important;
}

/* Blue theme active item adjustments */
[data-theme="blue"] .menu-item.active {
  background-color: rgba(255, 255, 255, 0.15);
  color: #ffffff !important;
  border-left: 3px solid #ffffff;
}

[data-theme="blue"] .menu-item.active .icon {
  color: #ffffff !important;
}

/* Logout button styles */
.logout-button {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s;
  color: #ff4757;
  border-top: 1px solid #e0e0e0;
  margin-top: auto;
}

.logout-button:hover {
  background: #fff5f5;
}

.logout-button .icon {
  margin-right: 12px;
  font-size: 1.2rem;
  color: #ff4757 !important;
}

.logout-button span {
  font-weight: 500;
  color: #ff4757;
}

/* Bold text class */
.bold-text {
  font-weight: bold !important;
}
</style> 