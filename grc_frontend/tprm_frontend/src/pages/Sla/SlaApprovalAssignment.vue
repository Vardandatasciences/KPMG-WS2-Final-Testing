<template>
  <div class="SAA_container">
    <!-- Header Section -->
    <div class="SAA_approval-header">
      <div class="SAA_header-content">
        <div class="SAA_header-text">
          <h1 class="SAA_page-title">SLA Approval Assignment</h1>
          <p class="SAA_page-subtitle">Streamline SLA approval workflows and manage assignments efficiently</p>
        </div>
        <div class="SAA_header-actions">
          <div class="SAA_status-badge">
            <svg class="SAA_badge-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            Workflow Management
      </div>
        <button 
          @click="toggleFormView" 
            class="SAA_btn SAA_btn--primary btn--create"
          v-if="!showCreateForm"
        >
            <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
          </svg>
            Create Assignment
        </button>
        </div>
      </div>
    </div>

    <!-- PENDING SLAs TABLE -->
    <div v-if="!showCreateForm" class="space-y-6">
      <!-- Filters -->
      <div class="SAA_filters-card">
        <div class="SAA_filters-header">
          <div class="SAA_filters-title">
            <svg class="SAA_filters-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.414A1 1 0 013 6.707V4z"/>
            </svg>
            <h3>Advanced Filters</h3>
          </div>
          <div class="SAA_filters-count">
            <span class="SAA_count-badge">{{ pendingContracts.length }} SLAs</span>
          </div>
        </div>
        <div class="SAA_filters-content">
          <div class="SAA_filters-grid">
            <div class="SAA_filter-group">
              <label class="SAA_filter-label">
                <svg class="SAA_label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                Search SLAs
              </label>
              <input 
                v-model="filters.search" 
                type="text" 
                class="SAA_filter-input" 
                placeholder="Search by SLA name, type, or vendor..."
                @input="fetchAllSLAs"
              />
            </div>
            <div class="SAA_filter-group">
              <label class="SAA_filter-label">
                <svg class="SAA_label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                </svg>
                SLA Type
              </label>
              <select v-model="filters.sla_type" class="SAA_filter-select" @change="fetchAllSLAs">
                <option value="">All Types</option>
                <option value="AVAILABILITY">Availability</option>
                <option value="RESPONSE_TIME">Response Time</option>
                <option value="RESOLUTION_TIME">Resolution Time</option>
                <option value="QUALITY">Quality</option>
                <option value="CUSTOM">Custom</option>
              </select>
            </div>
            <div class="SAA_filter-group">
              <label class="SAA_filter-label">
                <svg class="SAA_label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
                Vendor
              </label>
              <select v-model="filters.vendor_id" class="SAA_filter-select" @change="fetchAllSLAs">
                <option value="">All Vendors</option>
                <option v-for="vendor in vendors" :key="vendor.vendor_id" :value="vendor.vendor_id">
                  {{ vendor.company_name }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- All SLAs Table -->
      <div class="SAA_contracts-card">
        <div class="SAA_contracts-header">
          <div class="SAA_contracts-title">
            <svg class="SAA_contracts-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <div>
              <h3>All SLAs</h3>
              <p class="SAA_contracts-subtitle">All SLAs from vendor_slas table - pending and approved</p>
            </div>
          </div>
          <div class="SAA_contracts-stats">
            <div class="SAA_stat-item">
              <span class="SAA_stat-number">{{ getPendingCount() }}</span>
              <span class="SAA_stat-label">Pending</span>
            </div>
            <div class="SAA_stat-item">
              <span class="SAA_stat-number">{{ getApprovedCount() }}</span>
              <span class="SAA_stat-label">Approved</span>
            </div>
            <div class="SAA_stat-item">
              <span class="SAA_stat-number">{{ pendingContracts.length }}</span>
              <span class="SAA_stat-label">Total</span>
            </div>
          </div>
        </div>
        <div class="SAA_contracts-content">
          <div v-if="isLoadingContracts" class="SAA_loading-state">
            <div class="SAA_loading-spinner"></div>
            <p class="SAA_loading-text">Loading SLAs...</p>
          </div>
          <div v-else-if="pendingContracts.length === 0" class="SAA_empty-state">
            <svg class="SAA_empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <h4>No SLAs Found</h4>
            <p>No SLAs found in the vendor_slas table. Create some SLAs first.</p>
          </div>
          <div v-else class="SAA_contracts-table-container">
            <table class="SAA_contracts-table">
              <thead>
                <tr>
                  <th class="col-id">ID</th>
                  <th class="col-title">SLA Details</th>
                  <th class="col-type">Type</th>
                  <th class="col-vendor">Vendor</th>
                  <th class="col-value">Priority</th>
                  <th class="col-date">Effective Date</th>
                  <th class="col-status">Approval Status</th>
                  <th class="col-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sla in pendingContracts" :key="sla.sla_id" class="SAA_contract-row">
                  <td class="col-id">
                    <span class="SAA_contract-id">#{{ sla.sla_id }}</span>
                  </td>
                  <td class="col-title">
                    <div class="SAA_contract-info">
                      <h4 class="SAA_contract-name">{{ sla.sla_name }}</h4>
                      <p class="SAA_contract-number">{{ sla.business_service_impacted }}</p>
                    </div>
                  </td>
                  <td class="col-type">
                    <span class="SAA_type-badge">{{ sla.sla_type }}</span>
                  </td>
                  <td class="col-vendor">
                    <div class="SAA_vendor-info">
                      <span class="SAA_vendor-name">{{ sla.vendor?.company_name || 'N/A' }}</span>
                    </div>
                  </td>
                  <td class="col-value">
                    <span class="SAA_value-amount">{{ sla.priority }}</span>
                  </td>
                  <td class="col-date">
                    <span class="SAA_date-text">{{ formatDate(sla.effective_date) }}</span>
                  </td>
                  <td class="col-status">
                    <span class="SAA_status-badge" :class="getApprovalStatusClass(sla.approval_status)">
                      <svg class="SAA_status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      {{ sla.approval_status }}
                    </span>
                  </td>
                  <td class="col-actions">
                    <div class="SAA_action-buttons">
                      <!-- Show Assign button only for PENDING SLAs that don't have existing approvals -->
                      <button 
                        v-if="sla.approval_status === 'PENDING' && !hasExistingApproval(sla.sla_id)"
                        @click="assignApproval(sla)" 
                        class="SAA_btn SAA_btn--primary btn--assign"
                        title="Assign Approval"
                      >
                        <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                        </svg>
                        Assign
                      </button>
                      <!-- Show status for SLAs with existing approvals -->
                      <button 
                        v-if="sla.approval_status === 'PENDING' && hasExistingApproval(sla.sla_id)"
                        class="SAA_btn SAA_btn--info btn--assigned"
                        title="Already Assigned"
                        disabled
                      >
                        <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        Assigned
                      </button>
                      <!-- Show View button for all SLAs -->
                      <button 
                        @click="viewSLA(sla)" 
                        class="SAA_btn SAA_btn--outline btn--view"
                        title="View SLA Details"
                      >
                        <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                        View
                      </button>
                      <!-- Show status-specific actions -->
                      <button 
                        v-if="sla.approval_status === 'APPROVED'"
                        class="SAA_btn SAA_btn--success btn--approved"
                        title="Already Approved"
                        disabled
                      >
                        <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Approved
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Existing Approvals Table -->
      <div class="SAA_approvals-card" v-if="approvals.length > 0">
        <div class="SAA_approvals-header">
          <div class="SAA_approvals-title">
            <svg class="SAA_approvals-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
            </svg>
            <div>
              <h3>Existing Approval Assignments</h3>
              <p class="SAA_approvals-subtitle">Active and completed approval workflows</p>
            </div>
          </div>
          <div class="SAA_approvals-count">
            <span class="SAA_count-badge">{{ approvals.length }} assignments</span>
          </div>
        </div>
        <div class="SAA_approvals-content">
          <div class="SAA_approvals-table-container">
            <table class="SAA_approvals-table">
              <thead>
                <tr>
                  <th class="col-id">ID</th>
                  <th class="col-workflow">Workflow</th>
                  <th class="col-type">Type</th>
                  <th class="col-contract">Contract</th>
                  <th class="col-assigner">Assigner</th>
                  <th class="col-assignee">Assignee</th>
                  <th class="col-status">Status</th>
                  <th class="col-dates">Timeline</th>
                  <th class="col-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="approval in approvals" :key="approval.approval_id" class="SAA_approval-row">
                  <td class="col-id">
                    <span class="SAA_approval-id">#{{ approval.approval_id }}</span>
                  </td>
                  <td class="col-workflow">
                    <div class="SAA_workflow-info">
                      <span class="SAA_workflow-name">{{ approval.workflow_name }}</span>
                    </div>
                  </td>
                  <td class="col-type">
                    <span class="SAA_type-badge type-creation">{{ approval.object_type }}</span>
                  </td>
                  <td class="col-contract">
                    <div v-if="approval.contract_details" class="SAA_contract-details">
                      <div class="SAA_contract-title">{{ approval.contract_details.title }}</div>
                      <div class="SAA_contract-number">{{ approval.contract_details.number }}</div>
                    </div>
                    <div v-else class="SAA_contract-id">{{ approval.object_id }}</div>
                  </td>
                  <td class="col-assigner">
                    <div class="SAA_user-info">
                      <span class="SAA_user-name">{{ approval.assigner_name }}</span>
                    </div>
                  </td>
                  <td class="col-assignee">
                    <div class="SAA_user-info">
                      <span class="SAA_user-name">{{ approval.assignee_name }}</span>
                    </div>
                  </td>
                  <td class="col-status">
                    <span class="SAA_status-badge" :class="getStatusClass(approval.status)">
                      <svg class="SAA_status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      {{ formatStatus(approval.status) }}
                    </span>
                  </td>
                  <td class="col-dates">
                    <div class="SAA_date-info">
                      <div class="SAA_date-item">
                        <span class="SAA_date-label">Assigned</span>
                        <span class="SAA_date-value">{{ formatDate(approval.assigned_date) }}</span>
                      </div>
                      <div class="SAA_date-item">
                        <span class="SAA_date-label">Due</span>
                        <span class="SAA_date-value">{{ formatDate(approval.due_date) }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="col-actions">
                    <div class="SAA_action-buttons">
                      <button class="SAA_btn SAA_btn--outline btn--view" title="View Details">
                        <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                      </button>
                      <button class="SAA_btn SAA_btn--outline btn--edit" title="Edit Assignment">
                        <svg class="SAA_btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- CREATE ASSIGNMENT FORM -->
    <div v-if="showCreateForm" class="space-y-6">
        <div class="SAA_card">
          <div class="SAA_card-header">
            <div class="flex items-center justify-between">
              <h3 class="SAA_card-title flex items-center gap-2">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                </svg>
                Create New Approval Assignment
              </h3>
              <button @click="toggleFormView" class="SAA_btn SAA_btn--outline">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                </svg>
                Back to List
              </button>
            </div>
          </div>
          <div class="SAA_card-content space-y-6">
            <!-- Selected SLA Information -->
            <div v-if="selectedContract" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-blue-900 mb-2">Selected SLA</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-blue-700"><strong>Name:</strong> {{ selectedContract.sla_name }}</p>
                  <p class="text-sm text-blue-700"><strong>Type:</strong> {{ selectedContract.sla_type }}</p>
                  <p class="text-sm text-blue-700"><strong>Business Service:</strong> {{ selectedContract.business_service_impacted }}</p>
                </div>
                <div>
                  <p class="text-sm text-blue-700"><strong>Vendor:</strong> {{ selectedContract.vendor?.company_name || 'N/A' }}</p>
                  <p class="text-sm text-blue-700"><strong>Priority:</strong> {{ selectedContract.priority }}</p>
                  <p class="text-sm text-blue-700"><strong>Status:</strong> {{ selectedContract.approval_status }}</p>
                </div>
              </div>
            </div>
            <form @submit.prevent="createAssignment" class="space-y-6">
              <!-- Workflow Information -->
              <div class="space-y-4">
                <h4 class="text-lg font-semibold text-foreground">Workflow Information</h4>
                <div class="form-grid-3">
                  <div class="space-y-2">
                    <label for="workflowName" class="block text-sm font-medium">Workflow Name <span class="text-destructive">*</span></label>
                    <input 
                      v-model="form.workflow_name" 
                      type="text" 
                      id="workflowName" 
                      class="SAA_input" 
                      required 
                      placeholder="Enter workflow name"
                    />
                  </div>
                  <div class="space-y-2">
                    <label for="objectType" class="block text-sm font-medium">Object Type <span class="text-destructive">*</span></label>
                    <select v-model="form.object_type" id="objectType" class="SAA_input" required>
                      <option value="">Select object type</option>
                      <option value="SLA_CREATION">SLA Creation</option>
                      <option value="SLA_AMENDMENT">SLA Amendment</option>
                      <option value="SLA_RENEWAL">SLA Renewal</option>
                      <option value="SLA_TERMINATION">SLA Termination</option>
                    </select>
                  </div>
                  <div class="space-y-2">
                    <label for="slaId" class="block text-sm font-medium">SLA <span class="text-destructive">*</span></label>
                    <select v-model="form.object_id" id="slaId" class="SAA_input" required @change="onSLAChange">
                      <option value="">Select SLA</option>
                      <option v-for="sla in contracts" :key="sla.sla_id" :value="sla.sla_id">
                        {{ sla.sla_name }} ({{ sla.sla_type }}) - {{ sla.vendor?.company_name || 'N/A' }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Assignment Details -->
              <div class="space-y-4">
                <h4 class="text-lg font-semibold text-foreground">Assignment Details</h4>
                <div class="form-grid-2">
                  <div class="space-y-2">
                    <label for="assignerId" class="block text-sm font-medium">Assigner <span class="text-destructive">*</span></label>
                    <select v-model="form.assigner_id" id="assignerId" class="SAA_input" required @change="onAssignerChange" :disabled="isLoadingUsers">
                      <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assigner' }}</option>
                      <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                        {{ user.name }}
                      </option>
                    </select>
                  </div>
                  <div class="space-y-2">
                    <label for="assigneeId" class="block text-sm font-medium">Assignee <span class="text-destructive">*</span></label>
                    <select v-model="form.assignee_id" id="assigneeId" class="SAA_input" required @change="onAssigneeChange" :disabled="isLoadingUsers">
                      <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assignee' }}</option>
                      <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                        {{ user.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Timeline -->
              <div class="space-y-4">
                <h4 class="text-lg font-semibold text-foreground">Timeline</h4>
                <div class="form-grid-3">
                  <div class="space-y-2">
                    <label for="dueDate" class="block text-sm font-medium">Due Date <span class="text-destructive">*</span></label>
                    <input 
                      v-model="form.due_date" 
                      type="datetime-local" 
                      id="dueDate" 
                      class="SAA_input" 
                      required
                    />
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex gap-4 pt-4">
                <button type="button" @click="resetForm" class="SAA_btn SAA_btn--outline">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Reset Form
                </button>
                <button type="submit" class="SAA_btn SAA_btn--primary" :disabled="isSubmitting">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                  </svg>
                  {{ isSubmitting ? 'Creating...' : 'Create Assignment' }}
                </button>
              </div>
            </form>
          </div>
        </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import './SlaApprovalAssignment.css'
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import slaApprovalApi from '../../services/slaApprovalApi.js'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'

const route = useRoute()
const store = useStore()

// Get current user from store
const currentUser = computed(() => store.getters['auth/currentUser'])

// Reactive data
const isSubmitting = ref(false)
const users = ref([])
const isLoadingUsers = ref(false)
const approvals = ref([])
const isLoadingApprovals = ref(false)
const showCreateForm = ref(false)
const pendingContracts = ref([])
const isLoadingContracts = ref(false)
const vendors = ref([])
const selectedContract = ref(null)

// Filters
const filters = ref({
  search: '',
  sla_type: '',
  vendor_id: '',
  status: '',
  object_type: '',
  assignee_id: '',
  is_overdue: false
})

// Form data
const form = ref({
  workflow_id: 1,
  workflow_name: 'SLA Review Workflow',
  assigner_id: '',
  assignee_id: '',
  object_type: 'SLA_CREATION',
  object_id: '',
  sla_id: '',
  due_date: '',
  comment_text: ''
})

// Additional data
const contracts = ref([])

// Watch for current user and users to auto-select assigner
watch([currentUser, users], ([newUser, newUsers]) => {
  // Only auto-select if no assigner is currently selected and both user and users list are available
  if (newUser && newUsers && newUsers.length > 0 && !form.value.assigner_id) {
    const currentUserId = newUser?.userid || newUser?.user_id || newUser?.id
    if (currentUserId) {
      // Check if current user exists in the users list
      const currentUserInUsers = newUsers.find(
        user => user.user_id == currentUserId || user.userid == currentUserId || user.id == currentUserId
      )
      if (currentUserInUsers) {
        form.value.assigner_id = currentUserInUsers.user_id || currentUserInUsers.userid || currentUserInUsers.id
        console.log('Auto-selected current user as assigner (via watcher):', form.value.assigner_id)
      }
    }
  }
}, { immediate: true })

// Methods
const fetchUsers = async () => {
  isLoadingUsers.value = true
  try {
    console.log('Fetching users for SLA approval assignment')
    const response = await slaApprovalApi.getUsers()
    
    console.log('API response data:', response)
    
    // Handle different response formats
    if (response && response.success && Array.isArray(response.data)) {
      users.value = response.data
      console.log('Successfully fetched users:', response.data.length, 'records')
    } else if (response && Array.isArray(response)) {
      users.value = response
      console.log('Successfully fetched users:', response.length, 'records')
    } else if (response && response.results && Array.isArray(response.results)) {
      users.value = response.results
      console.log('Successfully fetched users:', response.results.length, 'records')
    } else if (response && response.data && Array.isArray(response.data)) {
      users.value = response.data
      console.log('Successfully fetched users:', response.data.length, 'records')
    } else {
      console.error('API returned no users data:', response)
      users.value = []
      PopupService.error('Failed to load users. Please try again.', 'Loading Error')
    }
    
    // Automatically select current user as assigner if available
    if (currentUser.value && !form.value.assigner_id) {
      const currentUserId = currentUser.value?.userid || currentUser.value?.user_id || currentUser.value?.id
      if (currentUser.value.user && !currentUserId) { // Check nested user object
        const nestedUserId = currentUser.value.user.userid || currentUser.value.user.user_id || currentUser.value.user.UserId || currentUser.value.user.id
        if (nestedUserId) {
          const currentUserInUsers = users.value.find(
            user => user.user_id == nestedUserId || user.userid == nestedUserId || user.id == nestedUserId
          )
          if (currentUserInUsers) {
            form.value.assigner_id = currentUserInUsers.user_id || currentUserInUsers.userid || currentUserInUsers.id
            console.log('Auto-selected current user as assigner (from nested user):', form.value.assigner_id)
          }
        }
      } else if (currentUserId) {
        // Check if current user exists in the users list
        const currentUserInUsers = users.value.find(
          user => user.user_id == currentUserId || user.userid == currentUserId || user.id == currentUserId
        )
        if (currentUserInUsers) {
          form.value.assigner_id = currentUserInUsers.user_id || currentUserInUsers.userid || currentUserInUsers.id
          console.log('Auto-selected current user as assigner:', form.value.assigner_id)
        }
      }
    }
  } catch (error) {
    console.error('Error fetching users:', error)
    users.value = []
    PopupService.error(error.response?.data?.error || 'Failed to load users. Please try again.', 'Loading Error')
  } finally {
    isLoadingUsers.value = false
  }
}

const fetchAllSLAs = async () => {
  isLoadingContracts.value = true
  try {
    console.log('Fetching all SLAs from vendor_slas table with filters:', filters.value)
    const response = await slaApprovalApi.getAllSLAs(filters.value)
    
    console.log('API response data:', response)
    
    if (response && response.results && Array.isArray(response.results)) {
      pendingContracts.value = response.results
      console.log('Successfully fetched all SLAs:', response.results.length, 'records')
    } else if (response && Array.isArray(response)) {
      pendingContracts.value = response
      console.log('Successfully fetched all SLAs:', response.length, 'records')
    } else {
      console.error('API returned no SLAs data')
      pendingContracts.value = []
    }
  } catch (error) {
    console.error('Error fetching SLAs:', error)
    pendingContracts.value = []
  } finally {
    isLoadingContracts.value = false
  }
}

const fetchVendors = async () => {
  try {
    console.log('Fetching vendors for SLA approval assignment')
    const response = await slaApprovalApi.getVendors()
    
    console.log('API response data:', response)
    
    if (response && response.results && Array.isArray(response.results)) {
      vendors.value = response.results
      console.log('Successfully fetched vendors:', response.results.length, 'records')
    } else if (response && Array.isArray(response)) {
      vendors.value = response
      console.log('Successfully fetched vendors:', response.length, 'records')
    } else {
      console.error('API returned no vendors data')
      vendors.value = []
    }
  } catch (error) {
    console.error('Error fetching vendors:', error)
    vendors.value = []
  }
}

const fetchSLAsForDropdown = async () => {
  try {
    console.log('Fetching all SLAs for dropdown')
    const response = await slaApprovalApi.getSLAs()
    
    console.log('API response data:', response)
    
    if (response && response.results && Array.isArray(response.results)) {
      contracts.value = response.results
      console.log('Successfully fetched SLAs:', response.results.length, 'records')
    } else if (response && Array.isArray(response)) {
      contracts.value = response
      console.log('Successfully fetched SLAs:', response.length, 'records')
    } else {
      console.error('API returned no SLAs data')
      contracts.value = []
    }
  } catch (error) {
    console.error('Error fetching SLAs:', error)
    contracts.value = []
  }
}

const assignApproval = (sla) => {
  selectedContract.value = sla
  form.value.object_id = sla.sla_id
  form.value.sla_id = sla.sla_id
  form.value.object_type = 'SLA_CREATION'
  
  // Add the selected SLA to the SLAs list if not already present
  const existingSLA = contracts.value.find(c => c.sla_id === sla.sla_id)
  if (!existingSLA) {
    contracts.value.unshift(sla) // Add to the beginning of the list
  }
  
  showCreateForm.value = true
}

const viewSLA = (sla) => {
  // Navigate to SLA detail page
  window.open(`/slas/${sla.sla_id}`, '_blank')
}

const formatCurrency = (value) => {
  if (!value) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value)
}

const onAssignerChange = () => {
  // Names are now auto-populated by backend
  console.log('Assigner changed:', form.value.assigner_id)
}

const onAssigneeChange = () => {
  // Names are now auto-populated by backend
  console.log('Assignee changed:', form.value.assignee_id)
}

const onSLAChange = () => {
  const slaId = form.value.object_id
  const sla = contracts.value.find(c => {
    const contractSlaId = c.sla_id || c.id
    return contractSlaId == slaId
  })
  if (sla) {
    selectedContract.value = sla
    form.value.sla_id = sla.sla_id || sla.id
    console.log('Selected SLA:', sla)
  } else {
    selectedContract.value = null
    form.value.sla_id = ''
    // If we have an object_id but no matching SLA, try to fetch it
    if (slaId) {
      console.log('SLA not found in list for object_id:', slaId, 'attempting to fetch')
      slaApprovalApi.getSLAById(slaId).then(individualSLA => {
        if (individualSLA) {
          // Add to list if not present
          const existingSLA = contracts.value.find(c => {
            const contractSlaId = c.sla_id || c.id
            return contractSlaId == slaId
          })
          if (!existingSLA) {
            contracts.value.unshift(individualSLA)
          }
          selectedContract.value = individualSLA
          form.value.sla_id = individualSLA.sla_id || individualSLA.id
          console.log('Fetched and selected SLA:', individualSLA)
        }
      }).catch(error => {
        console.error('Error fetching SLA:', error)
      })
    }
  }
}

const createAssignment = async () => {
  isSubmitting.value = true
  
  try {
    console.log('Creating SLA approval assignment:', form.value)
    
    // Call the API to create the approval assignment
    const response = await slaApprovalApi.createApproval(form.value)
    
    console.log('Assignment created successfully:', response)
    
    // Reset form and go back to list view
    resetForm()
    showCreateForm.value = false
    selectedContract.value = null
    
    // Refresh the pending contracts and approvals lists
    await fetchAllSLAs()
    await fetchApprovals()
    
    PopupService.success(`SLA approval assignment created successfully! Approval ID: ${response.data.approval_id}. The SLA has been assigned for review. The assigned user can now see this approval in their "My Approvals" page.`, 'Assignment Created')
  } catch (error) {
    console.error('Error creating assignment:', error)
    
    // Handle different types of errors
    let errorMessage = 'Error creating assignment. Please try again.'
    if (error.message) {
      errorMessage = error.message
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    }
    
    PopupService.error(errorMessage, 'Assignment Failed')
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    workflow_id: 1,
    workflow_name: 'SLA Review Workflow',
    assigner_id: '',
    assignee_id: '',
    object_type: 'SLA_CREATION',
    object_id: '',
    sla_id: '',
    due_date: '',
    comment_text: ''
  }
  selectedContract.value = null
}

const fetchApprovals = async () => {
  isLoadingApprovals.value = true
  try {
    console.log('Fetching contract approvals with filters:', filters.value)
    const response = await slaApprovalApi.getApprovals(filters.value)
    
    console.log('API response:', response)
    
    if (response && response.data && Array.isArray(response.data)) {
      approvals.value = response.data
      console.log('Successfully fetched approvals:', response.data.length, 'records')
    } else if (response && response.results && Array.isArray(response.results)) {
      approvals.value = response.results
      console.log('Successfully fetched approvals:', response.results.length, 'records')
    } else if (response && Array.isArray(response)) {
      approvals.value = response
      console.log('Successfully fetched approvals:', response.length, 'records')
    } else {
      console.error('API returned no approvals data')
      approvals.value = []
    }
  } catch (error) {
    console.error('Error fetching approvals:', error)
    approvals.value = []
    PopupService.error(`Failed to load approvals: ${error.message}. Please check your connection and try again.`, 'Loading Error')
  } finally {
    isLoadingApprovals.value = false
  }
}

const toggleFormView = () => {
  showCreateForm.value = !showCreateForm.value
  if (!showCreateForm.value) {
    resetForm()
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    return 'Invalid Date'
  }
}

const formatStatus = (status) => {
  const statusMap = {
    'ASSIGNED': 'Assigned',
    'IN_PROGRESS': 'In Progress',
    'COMMENTED': 'Commented',
    'SKIPPED': 'Skipped',
    'EXPIRED': 'Expired',
    'CANCELLED': 'Cancelled'
  }
  return statusMap[status] || status
}

const getStatusClass = (status) => {
  const statusClasses = {
    'ASSIGNED': 'status-assigned',
    'IN_PROGRESS': 'status-in-progress',
    'COMMENTED': 'status-commented',
    'SKIPPED': 'status-skipped',
    'EXPIRED': 'status-expired',
    'CANCELLED': 'status-cancelled'
  }
  return statusClasses[status] || 'status-default'
}

const getApprovalStatusClass = (approvalStatus) => {
  const statusClasses = {
    'PENDING': 'status-pending',
    'APPROVED': 'status-approved',
    'REJECTED': 'status-rejected'
  }
  return statusClasses[approvalStatus] || 'status-default'
}

const getPendingCount = () => {
  return pendingContracts.value.filter(sla => sla.approval_status === 'PENDING').length
}

const getApprovedCount = () => {
  return pendingContracts.value.filter(sla => sla.approval_status === 'APPROVED').length
}

const hasExistingApproval = (slaId) => {
  // Check if there's already an approval record for this SLA
  return approvals.value.some(approval => approval.sla_id === slaId)
}


// Initialize form with default due date and fetch users
onMounted(async () => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  form.value.due_date = tomorrow.toISOString().slice(0, 16)
  
  // Fetch all data first
  await fetchUsers()
  await fetchVendors()
  await fetchSLAsForDropdown()
  await fetchAllSLAs()
  await fetchApprovals()
  
  // Check for URL parameters and auto-fill form (if any parameters, show form directly)
  const slaId = route.query.slaId
  const objectType = route.query.objectType
  
  if (slaId || objectType) {
    showCreateForm.value = true
    
    if (slaId) {
      // Convert to number for comparison
      const slaIdNum = parseInt(slaId)
      // Set as number (not string) to match the option values which are numbers
      form.value.object_id = slaIdNum
      form.value.sla_id = slaIdNum
      
      // Wait for SLAs to be loaded, then find and set the selected SLA
      // Use a watcher or check after a short delay to ensure contracts are loaded
      const checkAndSetSLA = async () => {
        const sla = contracts.value.find(c => {
          const contractSlaId = c.sla_id || c.id
          return contractSlaId == slaIdNum || contractSlaId == slaId
        })
        if (sla) {
          selectedContract.value = sla
          console.log('Auto-filled and selected SLA from URL parameter:', sla)
        } else {
          // If not found in contracts list, try fetching it individually from the API
          console.log('SLA not found in contracts list, attempting to fetch individual SLA from API')
          try {
            const individualSLA = await slaApprovalApi.getSLAById(slaIdNum)
            if (individualSLA) {
              // Ensure the SLA has sla_id field
              if (!individualSLA.sla_id && individualSLA.id) {
                individualSLA.sla_id = individualSLA.id
              }
              // Add the SLA to the contracts list if not already present
              const existingSLA = contracts.value.find(c => {
                const contractSlaId = c.sla_id || c.id
                return contractSlaId == slaIdNum || contractSlaId == slaId
              })
              if (!existingSLA) {
                contracts.value.unshift(individualSLA) // Add to the beginning of the list
              }
              selectedContract.value = individualSLA
              // Ensure form values are set correctly (use number to match option values)
              form.value.object_id = individualSLA.sla_id || individualSLA.id
              form.value.sla_id = individualSLA.sla_id || individualSLA.id
              console.log('Auto-filled and selected SLA after fetching individually:', individualSLA)
            } else {
              // If still not found, try refreshing the full list
              console.log('Individual SLA fetch returned no data, trying full list refresh')
              await fetchSLAsForDropdown()
              const slaAfterFetch = contracts.value.find(c => {
                const contractSlaId = c.sla_id || c.id
                return contractSlaId == slaIdNum || contractSlaId == slaId
              })
              if (slaAfterFetch) {
                selectedContract.value = slaAfterFetch
                // Ensure form values are set correctly
                form.value.object_id = slaAfterFetch.sla_id || slaAfterFetch.id
                form.value.sla_id = slaAfterFetch.sla_id || slaAfterFetch.id
                console.log('Auto-filled and selected SLA after fetching full list:', slaAfterFetch)
              } else {
                console.warn('SLA not found even after fetching. slaId:', slaId)
                PopupService.warning(`SLA with ID ${slaId} was not found. Please select it manually from the dropdown.`, 'SLA Not Found')
              }
            }
          } catch (error) {
            console.error('Error fetching individual SLA:', error)
            // Try refreshing the full list as fallback
            try {
              await fetchSLAsForDropdown()
              const slaAfterFetch = contracts.value.find(c => {
                const contractSlaId = c.sla_id || c.id
                return contractSlaId == slaIdNum || contractSlaId == slaId
              })
              if (slaAfterFetch) {
                selectedContract.value = slaAfterFetch
                // Ensure form values are set correctly
                form.value.object_id = slaAfterFetch.sla_id || slaAfterFetch.id
                form.value.sla_id = slaAfterFetch.sla_id || slaAfterFetch.id
                console.log('Auto-filled and selected SLA after fetching full list (fallback):', slaAfterFetch)
              } else {
                console.warn('SLA not found even after fetching. slaId:', slaId)
                PopupService.warning(`SLA with ID ${slaId} was not found. Please select it manually from the dropdown.`, 'SLA Not Found')
              }
            } catch (fetchError) {
              console.error('Error fetching SLAs list:', fetchError)
              PopupService.warning(`SLA with ID ${slaId} was not found. Please select it manually from the dropdown.`, 'SLA Not Found')
            }
          }
        }
      }
      
      // Check immediately and also after a short delay to handle async loading
      checkAndSetSLA()
      setTimeout(checkAndSetSLA, 500)
      
      console.log('Auto-filled object_id from URL parameter:', slaId)
    }
    
    if (objectType) {
      form.value.object_type = objectType
      console.log('Auto-filled object_type from URL parameter:', objectType)
    }
  }
})
</script>
