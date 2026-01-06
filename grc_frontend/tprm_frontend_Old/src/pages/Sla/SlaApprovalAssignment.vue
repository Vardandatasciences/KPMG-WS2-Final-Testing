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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import slaApprovalApi from '../../services/slaApprovalApi.js'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'

const route = useRoute()

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


// Methods
const fetchUsers = async () => {
  isLoadingUsers.value = true
  try {
    console.log('Fetching users for SLA approval assignment')
    const response = await slaApprovalApi.getUsers()
    
    console.log('API response data:', response)
    
    if (response && Array.isArray(response)) {
      users.value = response
      console.log('Successfully fetched users:', response.length, 'records')
    } else if (response && response.results && Array.isArray(response.results)) {
      users.value = response.results
      console.log('Successfully fetched users:', response.results.length, 'records')
    } else {
      console.error('API returned no users data')
      users.value = []
    }
  } catch (error) {
    console.error('Error fetching users:', error)
    users.value = []
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
  if (!sla || !sla.sla_id) {
    PopupService.error('Invalid SLA data. Please try selecting the SLA again.', 'Invalid SLA')
    return
  }
  
  selectedContract.value = sla
  // Ensure sla_id is an integer
  const slaIdInt = parseInt(sla.sla_id, 10)
  form.value.object_id = slaIdInt
  form.value.sla_id = slaIdInt
  form.value.object_type = 'SLA_CREATION'
  
  // Add the selected SLA to the SLAs list if not already present
  const existingSLA = contracts.value.find(c => c.sla_id == slaIdInt)
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
  if (!form.value.object_id) {
    selectedContract.value = null
    form.value.sla_id = ''
    return
  }
  
  const slaIdInt = parseInt(form.value.object_id, 10)
  const sla = contracts.value.find(c => c.sla_id == slaIdInt)
  if (sla) {
    selectedContract.value = sla
    // Ensure sla_id is an integer
    form.value.sla_id = parseInt(sla.sla_id, 10)
    console.log('Selected SLA:', sla, 'with sla_id:', form.value.sla_id)
  } else {
    selectedContract.value = null
    form.value.sla_id = ''
    console.warn('SLA not found for object_id:', form.value.object_id)
  }
}

const createAssignment = async () => {
  isSubmitting.value = true
  
  try {
    // Validate that sla_id is set and is a valid integer
    if (!form.value.sla_id && !form.value.object_id) {
      PopupService.error('Please select an SLA before creating the assignment.', 'Missing SLA')
      isSubmitting.value = false
      return
    }
    
    // Prepare the data with proper type conversions
    const approvalData = {
      ...form.value,
      sla_id: form.value.sla_id ? parseInt(form.value.sla_id, 10) : (form.value.object_id ? parseInt(form.value.object_id, 10) : null),
      object_id: form.value.object_id ? parseInt(form.value.object_id, 10) : null,
      assigner_id: form.value.assigner_id ? parseInt(form.value.assigner_id, 10) : null,
      assignee_id: form.value.assignee_id ? parseInt(form.value.assignee_id, 10) : null,
      workflow_id: form.value.workflow_id ? parseInt(form.value.workflow_id, 10) : 1
    }
    
    // Remove empty or null values that might cause issues
    Object.keys(approvalData).forEach(key => {
      if (approvalData[key] === '' || approvalData[key] === null || approvalData[key] === undefined) {
        if (key !== 'comment_text') { // Allow empty comment_text
          delete approvalData[key]
        }
      }
    })
    
    console.log('Creating SLA approval assignment with prepared data:', approvalData)
    
    // Call the API to create the approval assignment
    const response = await slaApprovalApi.createApproval(approvalData)
    
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
    
    // Check for API response errors
    if (error.response?.data) {
      const errorData = error.response.data
      
      // Handle serializer validation errors
      if (errorData.errors) {
        const errorList = []
        for (const [field, messages] of Object.entries(errorData.errors)) {
          if (Array.isArray(messages)) {
            errorList.push(`${field}: ${messages.join(', ')}`)
          } else {
            errorList.push(`${field}: ${messages}`)
          }
        }
        errorMessage = errorList.join('\n')
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (errorData.error) {
        errorMessage = errorData.error
      }
    } else if (error.message) {
      errorMessage = error.message
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
      // Convert to integer for consistency
      const slaIdInt = parseInt(slaId, 10)
      form.value.object_id = slaIdInt
      form.value.sla_id = slaIdInt
      // Find and set the selected SLA
      const sla = contracts.value.find(c => c.sla_id == slaIdInt)
      if (sla) {
        selectedContract.value = sla
        form.value.sla_id = sla.sla_id // Ensure we use the actual sla_id from the SLA object
      }
      console.log('Auto-filled object_id and sla_id from URL parameter:', slaIdInt)
    }
    
    if (objectType) {
      form.value.object_type = objectType
      console.log('Auto-filled object_type from URL parameter:', objectType)
    }
  }
})
</script>
