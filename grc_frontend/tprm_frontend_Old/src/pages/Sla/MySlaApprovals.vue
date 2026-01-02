<template>
  <div class="sla-approvals-container">
    <!-- Enhanced Header Section -->
    <div class="sla-approvals-header">
      <div class="sla-approvals-header-content">
        <div class="sla-approvals-header-left">
          <div class="sla-approvals-header-icon">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
          <div class="sla-approvals-header-text">
            <div class="sla-approvals-title-row">
              <h1 class="sla-approvals-title">SLA Approvals Management</h1>
              <span class="sla-approvals-admin-badge">ADMIN</span>
            </div>
            <p class="sla-approvals-description">Admin view - Manage all SLA approvals and assignments</p>
            </div>
          </div>
        <div class="sla-approvals-header-actions">
          <div class="sla-approvals-approval-count">
            <div class="sla-approvals-count-icon">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
              </svg>
            </div>
            <div class="sla-approvals-count-text">
              <span class="sla-approvals-count-number">{{ isLoadingApprovals ? '...' : (assignedApprovals.length + reviewApprovals.length) }}</span>
              <span class="sla-approvals-count-label">total approvals</span>
            </div>
          </div>
          <button 
            @click="fetchMyApprovals" 
            class="sla-approvals-refresh-btn"
            :disabled="isLoadingApprovals"
            title="Refresh Approvals"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            {{ isLoadingApprovals ? 'Refreshing...' : 'Refresh' }}
          </button>
            </div>
            </div>
          </div>



    <!-- Admin Statistics Section -->
    <div class="sla-approvals-admin-stats-section">
      <div class="sla-approvals-admin-stats-card">
        <div class="sla-approvals-admin-stats-header">
          <div class="sla-approvals-admin-stats-icon">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <div class="sla-approvals-admin-stats-title">
            <h3>System Overview</h3>
            <p>Complete SLA approval system statistics</p>
          </div>
        </div>
        <div class="sla-approvals-admin-stats-grid">
          <div class="sla-approvals-admin-stat-item">
            <div class="sla-approvals-stat-icon sla-approvals-stat-icon--primary">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <div class="sla-approvals-stat-content">
              <div class="sla-approvals-stat-value">{{ totalApprovals }}</div>
              <div class="sla-approvals-stat-label">Total Approvals</div>
            </div>
          </div>
          <div class="sla-approvals-admin-stat-item">
            <div class="sla-approvals-stat-icon sla-approvals-stat-icon--warning">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="sla-approvals-stat-content">
              <div class="sla-approvals-stat-value">{{ pendingApprovals }}</div>
              <div class="sla-approvals-stat-label">Pending</div>
            </div>
          </div>
          <div class="sla-approvals-admin-stat-item">
            <div class="sla-approvals-stat-icon sla-approvals-stat-icon--danger">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              </svg>
            </div>
            <div class="sla-approvals-stat-content">
              <div class="sla-approvals-stat-value">{{ overdueApprovals }}</div>
              <div class="sla-approvals-stat-label">Overdue</div>
            </div>
          </div>
          <div class="sla-approvals-admin-stat-item">
            <div class="sla-approvals-stat-icon sla-approvals-stat-icon--success">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="sla-approvals-stat-content">
              <div class="sla-approvals-stat-value">{{ completedApprovals }}</div>
              <div class="sla-approvals-stat-label">Completed</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Filters Section -->
    <div class="sla-approvals-filters-section">
      <div class="sla-approvals-filters-card">
        <div class="sla-approvals-filters-header">
          <div class="sla-approvals-filters-title-section">
            <div class="sla-approvals-filters-icon">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z"/>
              </svg>
            </div>
            <h3 class="sla-approvals-filters-title">Filter & Search</h3>
            <p class="sla-approvals-filters-subtitle">Refine your approvals view</p>
            </div>
          <div class="sla-approvals-filters-actions">
            <button @click="clearFilters" class="sla-approvals-clear-filters-btn">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
              Clear All
            </button>
      </div>
    </div>

        <div class="sla-approvals-filters-content">
          <div class="sla-approvals-filters-grid">
            <div class="sla-approvals-filter-group">
              <label class="sla-approvals-filter-label">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                Search
              </label>
              <div class="sla-approvals-search-input-wrapper">
            <input 
              v-model="filters.search" 
              type="text" 
                  class="sla-approvals-search-input" 
                  placeholder="Search by workflow name or assigner..."
              @input="fetchMyApprovals"
            />
                <div class="sla-approvals-search-icon">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                  </svg>
          </div>
              </div>
          </div>
            
            <div class="sla-approvals-filter-group">
              <label class="sla-approvals-filter-label">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Status
              </label>
              <select v-model="filters.status" class="sla-approvals-filter-select" @change="fetchMyApprovals">
              <option value="">All Statuses</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMMENTED">Commented</option>
              <option value="SKIPPED">Skipped</option>
              <option value="EXPIRED">Expired</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
            
            <div class="sla-approvals-filter-group">
              <label class="sla-approvals-filter-label">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                </svg>
                Object Type
              </label>
              <select v-model="filters.object_type" class="sla-approvals-filter-select" @change="fetchMyApprovals">
              <option value="">All Object Types</option>
                <option value="SLA_CREATION">SLA Creation</option>
                <option value="SLA_AMENDMENT">SLA Amendment</option>
                <option value="SLA_RENEWAL">SLA Renewal</option>
                <option value="SLA_TERMINATION">SLA Termination</option>
            </select>
          </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="sla-approvals-tab-navigation">
      <div class="sla-approvals-tab-buttons">
        <button 
          @click="activeTab = 'assigned'" 
          :class="{ 'sla-approvals-tab-button--active': activeTab === 'assigned' }"
          class="sla-approvals-tab-button"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          All Assigned Tasks
          <span class="sla-approvals-tab-badge">{{ assignedApprovals.length }}</span>
        </button>
        <button 
          @click="activeTab = 'reviews'" 
          :class="{ 'sla-approvals-tab-button--active': activeTab === 'reviews' }"
          class="sla-approvals-tab-button"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
          </svg>
          All Reviews
          <span class="sla-approvals-tab-badge">{{ reviewApprovals.length }}</span>
        </button>
        </div>
      </div>

    <!-- Assigned Tasks Section -->
    <div v-if="activeTab === 'assigned'" class="sla-approvals-section">
      <div class="sla-approvals-card">
        <div class="sla-approvals-approvals-header">
          <div class="sla-approvals-approvals-title-section">
            <div class="sla-approvals-approvals-icon">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
        </div>
            <div class="sla-approvals-approvals-title-content">
              <h3 class="sla-approvals-approvals-title">All Assigned Tasks</h3>
              <p class="sla-approvals-approvals-subtitle">View all SLA approval tasks across the system</p>
            </div>
          </div>
          <div class="sla-approvals-approvals-count">
            <div class="sla-approvals-count-badge">
              <span class="count-number">{{ isLoadingApprovals ? '...' : assignedApprovals.length }}</span>
              <span class="count-text">tasks in system</span>
            </div>
          </div>
        </div>
        
        <div class="sla-approvals-approvals-content">
          <!-- Loading State -->
          <div v-if="isLoadingApprovals" class="sla-approvals-loading-state">
            <div class="sla-approvals-loading-spinner"></div>
            <h4>Loading your approvals...</h4>
            <p>Please wait while we fetch your latest assignments</p>
          </div>
          
          <!-- Authentication Required -->
          <div v-else-if="!userInfo" class="sla-approvals-empty-state">
            <div class="sla-approvals-empty-icon">
              <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              </svg>
            </div>
            <h4>Authentication Required</h4>
            <p>Please log in to access your contract approvals.</p>
            <button @click="fetchMyApprovals" class="retry-btn">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              Try Again
            </button>
          </div>
          
          <!-- No Approvals -->
          <div v-else-if="assignedApprovals.length === 0" class="sla-approvals-empty-state">
            <div class="sla-approvals-empty-icon">
              <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
            <h4>No Approvals Found</h4>
            <p>There are no SLA approvals in the system at the moment.</p>
            <p class="sla-approvals-empty-subtitle">SLA approvals will appear here when they are created and assigned.</p>
        </div>
          
          <!-- Assigned Tasks Table -->
          <div v-else class="sla-approvals-table-container">
            <div class="sla-approvals-table-wrapper">
              <table class="sla-approvals-table">
            <thead>
              <tr>
                    <th class="priority-col">Priority</th>
                    <th class="workflow-col">Workflow</th>
                    <th class="type-col">Type</th>
                    <th class="contract-col">SLA</th>
                    <th class="assigner-col">Assigned By</th>
                    <th class="status-col">Status</th>
                    <th class="dates-col">Timeline</th>
                    <th class="actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
                  <tr v-for="approval in assignedApprovals" :key="approval.approval_id" 
                      :class="{ 
                        'approval-row--overdue': approval.is_overdue, 
                        'approval-row--urgent': approval.days_until_due <= 2 && approval.days_until_due > 0,
                        'approval-row--completed': approval.status === 'COMMENTED' || approval.status === 'SKIPPED'
                      }">
                    <!-- Priority Column -->
                    <td class="priority-cell">
                  <div class="sla-approvals-priority-indicator">
                    <div v-if="approval.is_overdue" class="sla-approvals-priority-badge priority-badge--overdue">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                      </svg>
                          <span>Overdue</span>
                    </div>
                    <div v-else-if="approval.days_until_due <= 2 && approval.days_until_due > 0" class="sla-approvals-priority-badge priority-badge--urgent">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                          <span>Urgent</span>
                    </div>
                    <div v-else-if="approval.days_until_due <= 7 && approval.days_until_due > 2" class="sla-approvals-priority-badge priority-badge--normal">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                          <span>Normal</span>
                    </div>
                    <div v-else class="sla-approvals-priority-badge priority-badge--low">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                          <span>Low</span>
                    </div>
                  </div>
                </td>
                    
                    <!-- Workflow Column -->
                    <td class="workflow-cell">
                      <div class="sla-approvals-workflow-info">
                        <div class="sla-approvals-workflow-name">{{ approval.workflow_name }}</div>
                        <div v-if="approval.comment_text" class="sla-approvals-workflow-comment">
                          {{ approval.comment_text.substring(0, 40) }}{{ approval.comment_text.length > 40 ? '...' : '' }}
                        </div>
                  </div>
                </td>
                    
                    <!-- Type Column -->
                    <td class="type-cell">
                      <span class="sla-approvals-type-badge">{{ approval.object_type }}</span>
                </td>
                    
                    <!-- SLA Column -->
                    <td class="contract-cell">
                      <div v-if="approval.sla_details" class="sla-approvals-contract-info">
                        <div class="sla-approvals-contract-title">{{ approval.sla_details.sla_name }}</div>
                        <div class="sla-approvals-contract-number">SLA #{{ approval.sla_details.sla_id }}</div>
                      </div>
                      <div v-else class="sla-approvals-contract-id">SLA #{{ approval.sla_id }}</div>
                </td>
                    
                    <!-- Assigner Column -->
                    <td class="assigner-cell">
                      <div class="sla-approvals-assigner-info">
                        <div class="sla-approvals-assigner-name">{{ approval.assigner_name }}</div>
                      </div>
                </td>
                    
                    <!-- Status Column -->
                    <td class="status-cell">
                  <span class="sla-approvals-status-badge" :class="`status-badge--${approval.status.toLowerCase().replace('_', '-')}`">
                    {{ approval.status.replace('_', ' ') }}
                  </span>
                </td>
                    
                    <!-- Timeline Column -->
                    <td class="timeline-cell">
                      <div class="sla-approvals-timeline-info">
                        <div class="sla-approvals-timeline-dates">
                          <div class="date-item">
                            <span class="date-label">Assigned:</span>
                            <span class="date-value">{{ formatDate(approval.assigned_date) }}</span>
                          </div>
                          <div class="date-item">
                            <span class="date-label">Due:</span>
                            <span class="date-value" :class="{ 'date-overdue': approval.is_overdue }">
                              {{ formatDate(approval.due_date) }}
                            </span>
                          </div>
                        </div>
                        <div class="sla-approvals-timeline-status">
                          <span v-if="approval.is_overdue" class="days-overdue">
                    {{ Math.abs(approval.days_until_due) }} days overdue
                  </span>
                  <span v-else-if="approval.days_until_due !== null" 
                                :class="{ 
                                  'days-urgent': approval.days_until_due <= 2, 
                                  'days-warning': approval.days_until_due <= 7 
                                }">
                    {{ approval.days_until_due }} days left
                  </span>
                          <span v-else class="days-none">No due date</span>
                        </div>
                      </div>
                </td>
                    
                    <!-- Actions Column -->
                    <td class="actions-cell">
                      <div class="sla-approvals-action-buttons">
                    <button 
                      @click="viewApproval(approval)" 
                          class="sla-approvals-action-btn action-btn--view"
                      title="View Details"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                    </button>
                    <button 
                      @click="updateStatus(approval, 'IN_PROGRESS')" 
                          class="sla-approvals-action-btn action-btn--start"
                      v-if="approval.status === 'ASSIGNED'"
                      title="Start Working"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293H15M9 10V9a2 2 0 012-2h2a2 2 0 012 2v1m-6 0V9a2 2 0 012-2h2a2 2 0 012 2v1"/>
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
    </div>

    <!-- Reviews Section -->
    <div v-if="activeTab === 'reviews'" class="sla-approvals-section">
      <div class="sla-approvals-card">
        <div class="sla-approvals-approvals-header">
          <div class="sla-approvals-approvals-title-section">
            <div class="sla-approvals-approvals-icon">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
              </svg>
            </div>
            <div class="sla-approvals-approvals-title-content">
              <h3 class="sla-approvals-approvals-title">All Reviews</h3>
              <p class="sla-approvals-approvals-subtitle">View all SLA review assignments across the system</p>
            </div>
          </div>
          <div class="sla-approvals-approvals-count">
            <div class="sla-approvals-count-badge">
              <span class="count-number">{{ isLoadingReviews ? '...' : reviewApprovals.length }}</span>
              <span class="count-text">reviews pending</span>
            </div>
          </div>
        </div>
        
        <div class="sla-approvals-approvals-content">
          <!-- Loading State -->
          <div v-if="isLoadingReviews" class="sla-approvals-loading-state">
            <div class="sla-approvals-loading-spinner"></div>
            <h4>Loading your reviews...</h4>
            <p>Please wait while we fetch your review assignments</p>
          </div>
          
          <!-- No Reviews -->
          <div v-else-if="reviewApprovals.length === 0" class="sla-approvals-empty-state">
            <div class="sla-approvals-empty-icon">
              <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
              </svg>
            </div>
            <h4>No Reviews Found</h4>
            <p>There are no SLA reviews in the system at the moment.</p>
            <p class="sla-approvals-empty-subtitle">Reviews will appear here when SLAs are assigned for approval.</p>
          </div>
          
          <!-- Reviews Table -->
          <div v-else class="sla-approvals-table-container">
            <div class="sla-approvals-table-wrapper">
              <table class="sla-approvals-table">
                <thead>
                  <tr>
                    <th class="priority-col">Priority</th>
                    <th class="workflow-col">Workflow</th>
                    <th class="type-col">Type</th>
                    <th class="contract-col">SLA</th>
                    <th class="assignee-col">Assigned To</th>
                    <th class="status-col">Status</th>
                    <th class="dates-col">Timeline</th>
                    <th class="actions-col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="approval in reviewApprovals" :key="approval.approval_id" 
                      :class="{ 
                        'approval-row--overdue': approval.is_overdue, 
                        'approval-row--urgent': approval.days_until_due <= 2 && approval.days_until_due > 0,
                        'approval-row--commented': approval.status === 'COMMENTED'
                      }">
                    <!-- Priority Column -->
                    <td class="priority-cell">
                      <div class="sla-approvals-priority-indicator">
                        <div v-if="approval.is_overdue" class="sla-approvals-priority-badge priority-badge--overdue">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                          </svg>
                          <span>Overdue</span>
                        </div>
                        <div v-else-if="approval.days_until_due <= 2 && approval.days_until_due > 0" class="sla-approvals-priority-badge priority-badge--urgent">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                          <span>Urgent</span>
                        </div>
                        <div v-else-if="approval.days_until_due <= 7 && approval.days_until_due > 2" class="sla-approvals-priority-badge priority-badge--normal">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                          <span>Normal</span>
                        </div>
                        <div v-else class="sla-approvals-priority-badge priority-badge--low">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                          <span>Low</span>
                        </div>
                      </div>
                    </td>
                    
                    <!-- Workflow Column -->
                    <td class="workflow-cell">
                      <div class="sla-approvals-workflow-info">
                        <div class="sla-approvals-workflow-name">{{ approval.workflow_name }}</div>
                        <div v-if="approval.comment_text" class="sla-approvals-workflow-comment">
                          {{ approval.comment_text.substring(0, 40) }}{{ approval.comment_text.length > 40 ? '...' : '' }}
                        </div>
                      </div>
                    </td>
                    
                    <!-- Type Column -->
                    <td class="type-cell">
                      <span class="sla-approvals-type-badge">{{ approval.object_type }}</span>
                    </td>
                    
                    <!-- SLA Column -->
                    <td class="contract-cell">
                      <div v-if="approval.sla_details" class="sla-approvals-contract-info">
                        <div class="sla-approvals-contract-title">{{ approval.sla_details.sla_name }}</div>
                        <div class="sla-approvals-contract-number">SLA #{{ approval.sla_details.sla_id }}</div>
                      </div>
                      <div v-else class="sla-approvals-contract-id">SLA #{{ approval.sla_id }}</div>
                    </td>
                    
                    <!-- Assignee Column -->
                    <td class="assigner-cell">
                      <div class="sla-approvals-assigner-info">
                        <div class="sla-approvals-assigner-name">{{ approval.assignee_name }}</div>
                      </div>
                    </td>
                    
                    <!-- Status Column -->
                    <td class="status-cell">
                      <span class="sla-approvals-status-badge" :class="`status-badge--${approval.status.toLowerCase().replace('_', '-')}`">
                        {{ approval.status.replace('_', ' ') }}
                      </span>
                    </td>
                    
                    <!-- Timeline Column -->
                    <td class="timeline-cell">
                      <div class="sla-approvals-timeline-info">
                        <div class="sla-approvals-timeline-dates">
                          <div class="date-item">
                            <span class="date-label">Assigned:</span>
                            <span class="date-value">{{ formatDate(approval.assigned_date) }}</span>
                          </div>
                          <div class="date-item">
                            <span class="date-label">Due:</span>
                            <span class="date-value" :class="{ 'date-overdue': approval.is_overdue }">
                              {{ formatDate(approval.due_date) }}
                            </span>
                          </div>
                        </div>
                        <div class="sla-approvals-timeline-status">
                          <span v-if="approval.is_overdue" class="days-overdue">
                            {{ Math.abs(approval.days_until_due) }} days overdue
                          </span>
                          <span v-else-if="approval.days_until_due !== null" 
                                :class="{ 
                                  'days-urgent': approval.days_until_due <= 2, 
                                  'days-warning': approval.days_until_due <= 7 
                                }">
                            {{ approval.days_until_due }} days left
                          </span>
                          <span v-else class="days-none">No due date</span>
                        </div>
                      </div>
                    </td>
                    
                    <!-- Actions Column -->
                    <td class="actions-cell">
                      <div class="sla-approvals-action-buttons">
                    <button 
                          @click="viewContractForReview(approval)" 
                          class="sla-approvals-action-btn action-btn--view"
                          title="Review SLA"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                          </svg>
                        </button>
                        <button 
                          @click="approveSLA(approval)" 
                          class="sla-approvals-action-btn action-btn--approve"
                          v-if="approval.status === 'COMMENTED'"
                          title="Approve SLA"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                        </button>
                        <button 
                          @click="rejectSLA(approval)" 
                          class="sla-approvals-action-btn action-btn--reject"
                          v-if="approval.status === 'COMMENTED'"
                          title="Reject SLA"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
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
    </div>

    <!-- Comment Modal -->
    <div v-if="showCommentModal" class="sla-approvals-modal-overlay" @click="closeCommentModal">
      <div class="sla-approvals-modal-content" @click.stop>
        <div class="sla-approvals-modal-header">
          <h3 class="sla-approvals-modal-title">Add Comment</h3>
          <button @click="closeCommentModal" class="sla-approvals-modal-close">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="sla-approvals-modal-body">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-2">Workflow: {{ selectedApproval?.workflow_name }}</label>
              <p class="text-sm text-muted-foreground">Assigned by: {{ selectedApproval?.assigner_name }}</p>
            </div>
            <div class="space-y-2">
              <label class="block text-sm font-medium">Your Comment</label>
              <textarea 
                v-model="commentText" 
                class="input min-h-[100px]" 
                placeholder="Enter your comment or feedback here..."
                rows="4"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="sla-approvals-modal-footer">
          <button @click="closeCommentModal" class="btn btn--outline">Cancel</button>
          <button @click="submitComment" class="btn btn--primary" :disabled="!commentText.trim()">
            Submit Comment
          </button>
        </div>
      </div>
    </div>

  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { useRouter } from 'vue-router'
import slaApprovalApi from '../../services/slaApprovalApi.js'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { usePermissions } from '@/composables/usePermissions'
import loggingService from '@/services/loggingService'

export default {
  name: 'MyApprovals',
  components: {
    PopupModal
  },
  setup() {
    const router = useRouter()
    const { withPermissionCheck } = usePermissions()
    
    // Reactive data
    const assignedApprovals = ref([])
    const reviewApprovals = ref([])
    const isLoadingApprovals = ref(false)
    const isLoadingReviews = ref(false)
    const userInfo = ref(null)
    const activeTab = ref('assigned')
    const filters = ref({
      search: '',
      status: '',
      object_type: ''
    })
    
    // Modal states
    const showCommentModal = ref(false)
    const selectedApproval = ref(null)
    const commentText = ref('')

    // Computed properties for statistics
    const totalApprovals = computed(() => assignedApprovals.value.length)
    const pendingApprovals = computed(() => 
      assignedApprovals.value.filter(a => a.status === 'ASSIGNED' || a.status === 'IN_PROGRESS').length
    )
    const overdueApprovals = computed(() => 
      assignedApprovals.value.filter(a => a.is_overdue).length
    )
    const completedApprovals = computed(() => 
      assignedApprovals.value.filter(a => a.status === 'COMMENTED' || a.status === 'SKIPPED').length
    )

    // Methods
    const fetchMyApprovals = async () => {
      isLoadingApprovals.value = true
      try {
        // Check if token exists before making request
        const token = localStorage.getItem('session_token')
        if (!token) {
          console.warn('No authentication token found. Please log in.')
          assignedApprovals.value = []
          return
        }
        
        // Admin view - fetch all approvals without user filtering
        const response = await withPermissionCheck(
          () => slaApprovalApi.getAllApprovals(filters.value),
          { redirectOnError: false }
        )
        
        console.log('API Response for all approvals:', response)
        
        if (response && response.success && response.data) {
          assignedApprovals.value = response.data
          console.log('All approvals set to:', assignedApprovals.value)
        } else {
          console.error('Failed to fetch approvals:', response?.message || 'Unknown error')
          assignedApprovals.value = []
        }
      } catch (error) {
        console.error('Error fetching all approvals:', error)
        
        // Handle authentication errors
        if (error.status === 401 || error.code === 'AUTH_REQUIRED') {
          console.warn('Authentication required. Redirecting to login...')
          localStorage.removeItem('session_token')
          localStorage.removeItem('current_user')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
        
        assignedApprovals.value = []
      } finally {
        isLoadingApprovals.value = false
      }
    }

    const fetchMyReviews = async () => {
      isLoadingReviews.value = true
      try {
        // Check if token exists before making request
        const token = localStorage.getItem('session_token')
        if (!token) {
          console.warn('No authentication token found. Please log in.')
          reviewApprovals.value = []
          return
        }
        
        // Admin view - fetch all reviews without user filtering
        const response = await slaApprovalApi.getAllReviews(filters.value)
        
        if (response && response.success && response.data) {
          reviewApprovals.value = response.data
        } else {
          console.error('Failed to fetch reviews:', response?.message || 'Unknown error')
          reviewApprovals.value = []
        }
      } catch (error) {
        console.error('Error fetching all reviews:', error)
        
        // Handle authentication errors
        if (error.status === 401 || error.code === 'AUTH_REQUIRED') {
          console.warn('Authentication required. Redirecting to login...')
          localStorage.removeItem('session_token')
          localStorage.removeItem('current_user')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
        
        reviewApprovals.value = []
      } finally {
        isLoadingReviews.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return 'Invalid Date'
      }
    }

    const viewApproval = (approval) => {
      // Navigate to SLA review page
      router.push(`/slas/approvals/${approval.approval_id}/review`)
    }

    const addComment = (approval) => {
      selectedApproval.value = approval
      commentText.value = approval.comment_text || ''
      showCommentModal.value = true
    }

    const updateStatus = async (approval, newStatus) => {
      try {
        console.log(`Updating approval ${approval.approval_id} to status ${newStatus}`)
        
        // Call the API to update the approval status
        const response = await slaApprovalApi.updateApproval(approval.approval_id, { status: newStatus })
        
        if (response.success) {
          // Update locally
          const index = assignedApprovals.value.findIndex(a => a.approval_id === approval.approval_id)
          if (index !== -1) {
            assignedApprovals.value[index].status = newStatus
          }
          console.log(`Approval status updated to ${newStatus.replace('_', ' ')}`)
        } else {
          console.error('Failed to update approval status:', response.message)
        }
      } catch (error) {
        console.error('Error updating approval status:', error)
      }
    }

    const submitComment = async () => {
      if (!commentText.value.trim()) return

      try {
        console.log(`Submitting comment for approval ${selectedApproval.value.approval_id}:`, commentText.value)
        
        // Call the API to update the approval with comment
        const response = await slaApprovalApi.updateApproval(selectedApproval.value.approval_id, { 
          comment_text: commentText.value,
          status: 'COMMENTED'
        })
        
        if (response.success) {
          // Update locally
          const index = assignedApprovals.value.findIndex(a => a.approval_id === selectedApproval.value.approval_id)
          if (index !== -1) {
            assignedApprovals.value[index].comment_text = commentText.value
            assignedApprovals.value[index].status = 'COMMENTED'
          }
          console.log('Comment submitted successfully')
          closeCommentModal()
        } else {
          console.error('Failed to submit comment:', response.message)
        }
      } catch (error) {
        console.error('Error submitting comment:', error)
      }
    }

    const closeCommentModal = () => {
      showCommentModal.value = false
      selectedApproval.value = null
      commentText.value = ''
    }


    const clearFilters = () => {
      filters.value = {
        search: '',
        status: '',
        object_type: ''
      }
      if (activeTab.value === 'assigned') {
        fetchMyApprovals()
      } else {
        fetchMyReviews()
      }
    }

    const viewContractForReview = (approval) => {
      // Navigate to SLA review page
      router.push(`/slas/approvals/${approval.approval_id}/review`)
    }

    const approveSLA = async (approval) => {
      try {
        console.log(`Approving SLA for approval ${approval.approval_id}`)
        
        const response = await withPermissionCheck(
          () => slaApprovalApi.approveSLA(approval.approval_id)
        )
        
        if (response.success) {
          // Update locally
          const index = reviewApprovals.value.findIndex(a => a.approval_id === approval.approval_id)
          if (index !== -1) {
            reviewApprovals.value[index].status = 'APPROVED'
          }
          console.log('SLA approved successfully')
          PopupService.success('SLA approved successfully!', 'Approval Successful')
        } else {
          console.error('Failed to approve SLA:', response.message)
          PopupService.error('Failed to approve SLA: ' + response.message, 'Approval Failed')
        }
      } catch (error) {
        console.error('Error approving SLA:', error)
        PopupService.error('Error approving SLA: ' + error.message, 'Approval Error')
      }
    }

    const rejectSLA = async (approval) => {
      PopupService.comment(
        'Please provide a reason for rejection:',
        'Reject SLA',
        async (rejectionReason) => {
          if (!rejectionReason || !rejectionReason.trim()) return
          
          try {
            console.log(`Rejecting SLA for approval ${approval.approval_id}`)
            
            const response = await withPermissionCheck(
              () => slaApprovalApi.rejectSLA(approval.approval_id, rejectionReason)
            )
            
            if (response.success) {
              // Update locally
              const index = reviewApprovals.value.findIndex(a => a.approval_id === approval.approval_id)
              if (index !== -1) {
                reviewApprovals.value[index].status = 'REJECTED'
                reviewApprovals.value[index].comment_text = `REJECTED: ${rejectionReason}`
              }
              console.log('SLA rejected successfully')
              PopupService.success('SLA rejected successfully!', 'Rejection Successful')
            } else {
              console.error('Failed to reject SLA:', response.message)
              PopupService.error('Failed to reject SLA: ' + response.message, 'Rejection Failed')
            }
          } catch (error) {
            console.error('Error rejecting SLA:', error)
            PopupService.error('Error rejecting SLA: ' + error.message, 'Rejection Error')
          }
        }
      )
    }


    // Lifecycle
    onMounted(async () => {
      console.log('MySlaApprovals component mounted')
      await loggingService.logPageView('SLA', 'My SLA Approvals')
      
      // Set default user info without authentication dependency
      userInfo.value = {
        full_name: 'System User',
        user_id: 1,
        username: 'system',
        role: 'User'
      }
      
      // Load data without authentication dependency
      await Promise.all([
        fetchMyApprovals(),
        fetchMyReviews()
      ])
    })

    // No authentication watchers needed

    // Refresh approvals when component is activated (e.g., when navigating back to this page)
    onActivated(() => {
      console.log('MySlaApprovals component activated - refreshing approvals')
      Promise.all([
        fetchMyApprovals(),
        fetchMyReviews()
      ])
    })

    return {
      
      // Data
      assignedApprovals,
      reviewApprovals,
      isLoadingApprovals,
      isLoadingReviews,
      userInfo,
      activeTab,
      filters,
      showCommentModal,
      selectedApproval,
      commentText,
      
      // Computed
      totalApprovals,
      pendingApprovals,
      overdueApprovals,
      completedApprovals,
      
      // Methods
      fetchMyApprovals,
      fetchMyReviews,
      formatDate,
      viewApproval,
      viewContractForReview,
      addComment,
      updateStatus,
      submitComment,
      closeCommentModal,
      clearFilters,
      approveSLA,
      rejectSLA
    }
  }
}
</script>

<style src="./MySlaApprovals.css"></style>
