<template>
  <div class="my-approvals-container">
    <!-- Enhanced Header Section -->
    <div class="my-approvals-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="my-approvals-title">My Contract Approvals</h1>
          <p class="my-approvals-description">View and manage contract approvals assigned to you</p>
        </div>
      </div>
    </div>

    <!-- Enhanced Filters Section -->
    <div class="filters-section">
      <div class="filters-header">
        <div class="filters-title-section">
          <div class="filters-icon">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z"/>
            </svg>
          </div>
          <h3 class="filters-title">Filter & Search</h3>
          <p class="filters-subtitle">Refine your approvals view</p>
        </div>
        <div class="filters-actions">
          <button @click="clearFilters" class="clear-filters-btn">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
            Clear All
          </button>
        </div>
      </div>

      <div class="filters-content">
        <div class="filters-grid">
          <div class="filter-group">
            <label class="filter-label">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Status
            </label>
            <select v-model="filters.status" class="filter-select" @change="fetchMyApprovals">
            <option value="">All Statuses</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMMENTED">Commented</option>
            <option value="SKIPPED">Skipped</option>
            <option value="EXPIRED">Expired</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
          
          <div class="filter-group">
            <label class="filter-label">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
              Object Type
            </label>
            <select v-model="filters.object_type" class="filter-select" @change="fetchMyApprovals">
            <option value="">All Object Types</option>
              <option value="CONTRACT_CREATION">Contract Creation</option>
              <option value="CONTRACT_AMENDMENT">Contract Amendment</option>
              <option value="SUBCONTRACT_CREATION">Subcontract Creation</option>
              <option value="CONTRACT_RENEWAL">Contract Renewal</option>
          </select>
        </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <div class="tab-buttons">
        <button 
          @click="activeTab = 'assigned'" 
          :class="{ 'tab-button--active': activeTab === 'assigned' }"
          class="tab-button"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          My Assigned Tasks
          <span class="tab-badge">{{ assignedApprovals.length }}</span>
        </button>
        <button 
          @click="activeTab = 'reviews'" 
          :class="{ 'tab-button--active': activeTab === 'reviews' }"
          class="tab-button"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
          </svg>
          My Reviews
          <span class="tab-badge">{{ reviewApprovals.length }}</span>
        </button>
        </div>
      </div>

    <!-- Assigned Tasks Section -->
    <div v-if="activeTab === 'assigned'" class="approvals-section">
      <div class="approvals-card">
        <div class="approvals-header">
          <div class="approvals-title-section">
            <div class="approvals-icon">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
        </div>
            <div class="approvals-title-content">
              <h3 class="approvals-title">My Assigned Tasks</h3>
              <p class="approvals-subtitle">Complete your assigned contract approval tasks</p>
            </div>
          </div>
          <div class="approvals-count">
            <div class="count-badge">
              <span class="count-number">{{ isLoadingApprovals ? '...' : assignedApprovals.length }}</span>
              <span class="count-text">tasks assigned</span>
            </div>
          </div>
        </div>
        
        <div class="approvals-content">
          <!-- Loading State -->
          <div v-if="isLoadingApprovals" class="loading-state">
            <div class="loading-spinner"></div>
            <h4>Loading your approvals...</h4>
            <p>Please wait while we fetch your latest assignments</p>
          </div>
          
          <!-- Authentication Required -->
          <div v-else-if="!userInfo" class="empty-state">
            <div class="empty-icon">
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
          <div v-else-if="assignedApprovals.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
            <h4>No Approvals Assigned</h4>
            <p>You don't have any contract approvals at the moment.</p>
            <p class="empty-subtitle">Check back later or contact your administrator if you expect to see approvals here.</p>
        </div>
          
          <!-- Assigned Tasks Table -->
          <div v-else class="table-container">
            <div class="table-wrapper">
              <table class="approvals-table">
            <thead>
              <tr>
                    <th class="priority-col">Priority</th>
                    <th class="workflow-col">Workflow</th>
                    <th class="type-col">Type</th>
                    <th class="contract-col">Contract</th>
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
                  <div class="priority-indicator">
                    <div v-if="approval.is_overdue" class="priority-badge priority-badge--overdue">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                      </svg>
                          <span>Overdue</span>
                    </div>
                    <div v-else-if="approval.days_until_due <= 2 && approval.days_until_due > 0" class="priority-badge priority-badge--urgent">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                          <span>Urgent</span>
                    </div>
                    <div v-else-if="approval.days_until_due <= 7 && approval.days_until_due > 2" class="priority-badge priority-badge--normal">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                          <span>Normal</span>
                    </div>
                    <div v-else class="priority-badge priority-badge--low">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                          <span>Low</span>
                    </div>
                  </div>
                </td>
                    
                    <!-- Workflow Column -->
                    <td class="workflow-cell">
                      <div class="workflow-info">
                        <div class="workflow-name">{{ approval.workflow_name }}</div>
                        <div v-if="approval.comment_text" class="workflow-comment">
                          {{ approval.comment_text.substring(0, 40) }}{{ approval.comment_text.length > 40 ? '...' : '' }}
                        </div>
                  </div>
                </td>
                    
                    <!-- Type Column -->
                    <td class="type-cell">
                      <span class="type-badge">{{ approval.object_type }}</span>
                </td>
                    
                    <!-- Contract Column -->
                    <td class="contract-cell">
                      <div v-if="approval.contract_details" class="contract-info">
                        <div class="contract-title">{{ approval.contract_details.title }}</div>
                        <div class="contract-number">{{ approval.contract_details.number }}</div>
                      </div>
                      <div v-else class="contract-id">{{ approval.object_id }}</div>
                </td>
                    
                    <!-- Assigner Column -->
                    <td class="assigner-cell">
                      <div class="assigner-info">
                        <div class="assigner-name">{{ approval.assigner_name }}</div>
                      </div>
                </td>
                    
                    <!-- Status Column -->
                    <td class="status-cell">
                  <span class="status-badge" :class="`status-badge--${approval.status.toLowerCase().replace('_', '-')}`">
                    {{ approval.status.replace('_', ' ') }}
                  </span>
                </td>
                    
                    <!-- Timeline Column -->
                    <td class="timeline-cell">
                      <div class="timeline-info">
                        <div class="timeline-dates">
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
                        <div class="timeline-status">
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
                      <div class="action-buttons">
                    <button 
                      @click="viewApproval(approval)" 
                          class="action-btn action-btn--view"
                      title="View Details"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                    </button>
                    <button 
                      @click="updateStatus(approval, 'IN_PROGRESS')" 
                          class="action-btn action-btn--start"
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
    <div v-if="activeTab === 'reviews'" class="approvals-section">
      <div class="approvals-card">
        <div class="approvals-header">
          <div class="approvals-title-section">
            <div class="approvals-icon">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
              </svg>
            </div>
            <div class="approvals-title-content">
              <h3 class="approvals-title">My Reviews</h3>
              <p class="approvals-subtitle">Review and approve contracts assigned by you</p>
            </div>
          </div>
          <div class="approvals-count">
            <div class="count-badge">
              <span class="count-number">{{ isLoadingReviews ? '...' : reviewApprovals.length }}</span>
              <span class="count-text">reviews pending</span>
            </div>
          </div>
        </div>
        
        <div class="approvals-content">
          <!-- Loading State -->
          <div v-if="isLoadingReviews" class="loading-state">
            <div class="loading-spinner"></div>
            <h4>Loading your reviews...</h4>
            <p>Please wait while we fetch your review assignments</p>
          </div>
          
          <!-- No Reviews -->
          <div v-else-if="reviewApprovals.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
              </svg>
            </div>
            <h4>No Reviews Pending</h4>
            <p>You don't have any contract reviews at the moment.</p>
            <p class="empty-subtitle">Reviews will appear here when contracts are assigned to you for approval.</p>
          </div>
          
          <!-- Reviews Table -->
          <div v-else class="table-container">
            <div class="table-wrapper">
              <table class="approvals-table">
                <thead>
                  <tr>
                    <th class="priority-col">Priority</th>
                    <th class="workflow-col">Workflow</th>
                    <th class="type-col">Type</th>
                    <th class="contract-col">Contract</th>
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
                      <div class="priority-indicator">
                        <div v-if="approval.is_overdue" class="priority-badge priority-badge--overdue">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                          </svg>
                          <span>Overdue</span>
                        </div>
                        <div v-else-if="approval.days_until_due <= 2 && approval.days_until_due > 0" class="priority-badge priority-badge--urgent">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                          <span>Urgent</span>
                        </div>
                        <div v-else-if="approval.days_until_due <= 7 && approval.days_until_due > 2" class="priority-badge priority-badge--normal">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                          <span>Normal</span>
                        </div>
                        <div v-else class="priority-badge priority-badge--low">
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                          <span>Low</span>
                        </div>
                      </div>
                    </td>
                    
                    <!-- Workflow Column -->
                    <td class="workflow-cell">
                      <div class="workflow-info">
                        <div class="workflow-name">{{ approval.workflow_name }}</div>
                        <div v-if="approval.comment_text" class="workflow-comment">
                          {{ approval.comment_text.substring(0, 40) }}{{ approval.comment_text.length > 40 ? '...' : '' }}
                        </div>
                      </div>
                    </td>
                    
                    <!-- Type Column -->
                    <td class="type-cell">
                      <span class="type-badge">{{ approval.object_type }}</span>
                    </td>
                    
                    <!-- Contract Column -->
                    <td class="contract-cell">
                      <div v-if="approval.contract_details" class="contract-info">
                        <div class="contract-title">{{ approval.contract_details.title }}</div>
                        <div class="contract-number">{{ approval.contract_details.number }}</div>
                      </div>
                      <div v-else class="contract-id">{{ approval.object_id }}</div>
                    </td>
                    
                    <!-- Assignee Column -->
                    <td class="assigner-cell">
                      <div class="assigner-info">
                        <div class="assigner-name">{{ approval.assignee_name }}</div>
                      </div>
                    </td>
                    
                    <!-- Status Column -->
                    <td class="status-cell">
                      <span class="status-badge" :class="`status-badge--${approval.status.toLowerCase().replace('_', '-')}`">
                        {{ approval.status.replace('_', ' ') }}
                      </span>
                    </td>
                    
                    <!-- Timeline Column -->
                    <td class="timeline-cell">
                      <div class="timeline-info">
                        <div class="timeline-dates">
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
                        <div class="timeline-status">
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
                      <div class="action-buttons">
                    <button 
                          @click="viewContractForReview(approval)" 
                          class="action-btn action-btn--view"
                          title="Review Contract"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                          </svg>
                        </button>
                        <button 
                          @click="approveContract(approval)" 
                          class="action-btn action-btn--approve"
                          v-if="approval.status === 'COMMENTED'"
                          title="Approve Contract"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                        </button>
                        <button 
                          @click="rejectContract(approval)" 
                          class="action-btn action-btn--reject"
                          v-if="approval.status === 'COMMENTED'"
                          title="Reject Contract"
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
    <div v-if="showCommentModal" class="modal-overlay" @click="closeCommentModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Add Comment</h3>
          <button @click="closeCommentModal" class="modal-close">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
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
        <div class="modal-footer">
          <button @click="closeCommentModal" class="btn btn--outline">Cancel</button>
          <button @click="submitComment" class="btn btn--primary" :disabled="!commentText.trim()">
            Submit Comment
          </button>
        </div>
      </div>
    </div>

    <!-- View Details Modal -->
    <div v-if="showViewModal" class="modal-overlay" @click="closeViewModal">
      <div class="modal-content modal-content--large" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Approval Details</h3>
          <button @click="closeViewModal" class="modal-close">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="selectedApproval" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Workflow Name</label>
                  <p class="text-lg font-medium">{{ selectedApproval.workflow_name }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Object Type</label>
                  <span class="badge badge--outline">{{ selectedApproval.object_type }}</span>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Contract</label>
                  <div v-if="selectedApproval.contract_details">
                    <p class="font-medium">{{ selectedApproval.contract_details.title }}</p>
                    <p class="text-sm text-muted-foreground">{{ selectedApproval.contract_details.number }}</p>
                  </div>
                  <p v-else class="font-mono">{{ selectedApproval.object_id }}</p>
                </div>
              </div>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Assigned By</label>
                  <p>{{ selectedApproval.assigner_name }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Status</label>
                  <span class="status-badge" :class="`status-badge--${selectedApproval.status.toLowerCase().replace('_', '-')}`">
                    {{ selectedApproval.status.replace('_', ' ') }}
                  </span>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Assigned Date</label>
                  <p>{{ formatDate(selectedApproval.assigned_date) }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Due Date</label>
                  <p :class="{ 'text-red-600 font-medium': selectedApproval.is_overdue }">
                    {{ formatDate(selectedApproval.due_date) }}
                    <span v-if="selectedApproval.is_overdue" class="ml-2 text-sm">(Overdue)</span>
                  </p>
                </div>
              </div>
            </div>
            <div v-if="selectedApproval.comment_text">
              <label class="block text-sm font-medium text-muted-foreground mb-2">Comments</label>
              <div class="bg-muted p-4 rounded-lg">
                <p class="whitespace-pre-wrap">{{ selectedApproval.comment_text }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeViewModal" class="btn btn--outline">Close</button>
          <button @click="addComment(selectedApproval)" class="btn btn--secondary">Add Comment</button>
          <button 
            @click="updateStatus(selectedApproval, 'IN_PROGRESS')" 
            class="btn btn--primary"
            v-if="selectedApproval.status === 'ASSIGNED'"
          >
            Start Working
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import contractApprovalApi from '../../services/contractApprovalApi'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'

export default {
  name: 'MyApprovals',
  setup() {
    const store = useStore()
    const router = useRouter()
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()
    
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
    const showViewModal = ref(false)
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
        // Get current user from store
        const currentUser = store.getters['auth/currentUser']
        if (!currentUser) {
          console.warn('No current user found in store, waiting for authentication...')
          // Wait a bit and try again
          setTimeout(() => {
            if (store.getters['auth/currentUser']) {
              fetchMyApprovals()
            } else {
              console.error('Still no user found after waiting')
              assignedApprovals.value = []
              isLoadingApprovals.value = false
            }
          }, 1000)
          return
        }

        // Add current user's ID to filters to get only their assigned approvals
        // Try multiple possible user ID fields and ensure it's converted to number
        const userId = currentUser.userid || currentUser.user_id || currentUser.UserId
        if (!userId) {
          console.error('No user ID found in current user data:', currentUser)
          assignedApprovals.value = []
          return
        }

        // Convert to number to ensure type consistency with backend
        const userIdNum = typeof userId === 'string' ? parseInt(userId, 10) : userId
        if (isNaN(userIdNum)) {
          console.error('Invalid user ID format:', userId)
          assignedApprovals.value = []
          return
        }

        const filtersWithUser = {
          ...filters.value,
          assignee_id: userIdNum
        }
        
        console.log('🔍 Fetching assigned approvals for user ID:', userIdNum, 'with filters:', filtersWithUser)
        
        const response = await contractApprovalApi.getApprovals(filtersWithUser)
        
        console.log('📋 API Response for user', userIdNum, ':', response)
        console.log('📋 Response data:', response.data)
        console.log('📋 Number of approvals:', response.data?.length || 0)
        
        if (response.success && response.data) {
          // Extra safety: ensure we only show approvals where current user is the ASSIGNEE
          assignedApprovals.value = response.data.filter(a => {
            const assigneeId = a.assignee_id || a.assignee || a.assigneeId
            return String(assigneeId) === String(userIdNum)
          })

          console.log('✅ Assigned approvals set to:', assignedApprovals.value.length, 'items (filtered by assignee_id)')
          if (assignedApprovals.value.length > 0) {
            console.log('📄 Sample approval (assigned):', assignedApprovals.value[0])
          }
        } else {
          console.error('❌ Failed to fetch approvals:', response.message || 'Unknown error')
          assignedApprovals.value = []
        }
      } catch (error) {
        console.error('❌ Error fetching my approvals:', error)
        console.error('❌ Error details:', error.response?.data || error.message)
        assignedApprovals.value = []
      } finally {
        isLoadingApprovals.value = false
      }
    }

    const fetchMyReviews = async () => {
      isLoadingReviews.value = true
      try {
        // Get current user from store
        const currentUser = store.getters['auth/currentUser']
        if (!currentUser) {
          console.warn('No current user found in store for reviews')
          reviewApprovals.value = []
          return
        }

        // Add current user's ID to filters to get only their assigned reviews
        // Try multiple possible user ID fields and ensure it's converted to number
        const userId = currentUser.userid || currentUser.user_id || currentUser.UserId
        if (!userId) {
          console.error('No user ID found in current user data:', currentUser)
          reviewApprovals.value = []
          return
        }

        // Convert to number to ensure type consistency with backend
        const userIdNum = typeof userId === 'string' ? parseInt(userId, 10) : userId
        if (isNaN(userIdNum)) {
          console.error('Invalid user ID format:', userId)
          reviewApprovals.value = []
          return
        }

        const filtersWithUser = {
          ...filters.value,
          assigner_id: userIdNum
        }
        
        console.log('🔍 Fetching review approvals for assigner ID:', userIdNum, 'with filters:', filtersWithUser)
        
        const response = await contractApprovalApi.getAssignerApprovals(filtersWithUser)
        
        console.log('📋 API Response for assigner', userIdNum, ':', response)
        console.log('📋 Response data:', response.data)
        console.log('📋 Number of reviews:', response.data?.length || 0)
        
        if (response.success && response.data) {
          // Extra safety: ensure we only show approvals where current user is the ASSIGNER
          reviewApprovals.value = response.data.filter(a => {
            const assignerId = a.assigner_id || a.assigner || a.assignerId
            return String(assignerId) === String(userIdNum)
          })

          console.log('✅ Review approvals set to:', reviewApprovals.value.length, 'items (filtered by assigner_id)')
          if (reviewApprovals.value.length > 0) {
            console.log('📄 Sample review (assigner):', reviewApprovals.value[0])
          }
        } else {
          console.error('❌ Failed to fetch reviews:', response.message || 'Unknown error')
          reviewApprovals.value = []
        }
      } catch (error) {
        console.error('❌ Error fetching my reviews:', error)
        console.error('❌ Error details:', error.response?.data || error.message)
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
      // Navigate to contract detail page
      if (approval.contract_details && approval.contract_details.id) {
        router.push(`/contracts/${approval.contract_details.id}/detail`)
      } else if (approval.object_id) {
        router.push(`/contracts/${approval.object_id}/detail`)
      } else {
        console.error('No contract ID found for approval:', approval)
      }
    }

    const addComment = (approval) => {
      selectedApproval.value = approval
      commentText.value = approval.comment_text || ''
      showCommentModal.value = true
      if (showViewModal.value) {
        showViewModal.value = false
      }
    }

    const updateStatus = async (approval, newStatus) => {
      try {
        console.log(`Updating approval ${approval.approval_id} to status ${newStatus}`)
        
        // Call the API to update the approval status
        const response = await contractApprovalApi.updateApproval(approval.approval_id, { status: newStatus })
        
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
        const response = await contractApprovalApi.updateApproval(selectedApproval.value.approval_id, { 
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

    const closeViewModal = () => {
      showViewModal.value = false
      selectedApproval.value = null
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
      // Navigate to contract review page
      if (approval.contract_details && approval.contract_details.id) {
        router.push(`/contracts/${approval.contract_details.id}/review`)
      } else if (approval.object_id) {
        router.push(`/contracts/${approval.object_id}/review`)
      } else {
        console.error('No contract ID found for review:', approval)
      }
    }

    const approveContract = async (approval) => {
      try {
        console.log(`Approving contract for approval ${approval.approval_id}`)
        
        const response = await contractApprovalApi.approveContract(approval.approval_id)
        
        if (response.success) {
          // Update locally
          const index = reviewApprovals.value.findIndex(a => a.approval_id === approval.approval_id)
          if (index !== -1) {
            reviewApprovals.value[index].status = 'APPROVED'
          }
          console.log('Contract approved successfully')
          
          // Show success notification
          await showSuccess('Contract Approved', `Contract "${approval.contract_name}" has been approved successfully.`, {
            action: 'contract_approved',
            approval_id: approval.approval_id,
            contract_name: approval.contract_name
          })
          
          // Create notification service notification
          await notificationService.createContractApprovalNotification('approval_approved', {
            contract_id: approval.contract_id,
            approval_id: approval.approval_id
          })
        } else {
          console.error('Failed to approve contract:', response.message)
          
          // Show error notification
          await showError('Approval Failed', 'Failed to approve contract. Please try again.', {
            action: 'contract_approval_failed',
            approval_id: approval.approval_id,
            error_message: response.message
          })
          
          // Create error notification
          await notificationService.createContractErrorNotification('approve_contract', response.message, {
            title: 'Approval Failed',
            contract_id: approval.contract_id
          })
        }
      } catch (error) {
        console.error('Error approving contract:', error)
        
        // Show error notification
        await showError('Approval Failed', 'Error approving contract. Please try again.', {
          action: 'contract_approval_error',
          approval_id: approval.approval_id,
          error_message: error.message
        })
        
        // Create error notification
        await notificationService.createContractErrorNotification('approve_contract', error.message, {
          title: 'Approval Error',
          contract_id: approval.contract_id
        })
      }
    }

    const rejectContract = async (approval) => {
      const rejectionReason = prompt('Please provide a reason for rejection:')
      if (rejectionReason === null) return // User cancelled
      
      try {
        console.log(`Rejecting contract for approval ${approval.approval_id}`)
        
        const response = await contractApprovalApi.rejectContract(approval.approval_id, rejectionReason)
        
        if (response.success) {
          // Update locally
          const index = reviewApprovals.value.findIndex(a => a.approval_id === approval.approval_id)
          if (index !== -1) {
            reviewApprovals.value[index].status = 'REJECTED'
            reviewApprovals.value[index].comment_text = `REJECTED: ${rejectionReason}`
          }
          console.log('Contract rejected successfully')
          PopupService.success('Contract rejected successfully!', 'Contract Rejected')
          
          // Create notification
          await notificationService.createContractApprovalNotification('approval_rejected', {
            contract_id: approval.contract_id,
            approval_id: approval.approval_id,
            reason: rejectionReason
          })
        } else {
          console.error('Failed to reject contract:', response.message)
          PopupService.error('Failed to reject contract: ' + response.message, 'Rejection Failed')
          
          // Create error notification
          await notificationService.createContractErrorNotification('reject_contract', response.message, {
            title: 'Rejection Failed',
            contract_id: approval.contract_id
          })
        }
      } catch (error) {
        console.error('Error rejecting contract:', error)
        PopupService.error('Error rejecting contract: ' + error.message, 'Rejection Error')
        
        // Create error notification
        await notificationService.createContractErrorNotification('reject_contract', error.message, {
          title: 'Rejection Error',
          contract_id: approval.contract_id
        })
      }
    }


    // Lifecycle
    onMounted(async () => {
      console.log('MyContractApprovals component mounted')
      await loggingService.logPageView('Contract', 'My Contract Approvals')
      
      // Wait for authentication to be ready with more robust checking
      let attempts = 0
      const maxAttempts = 20 // Increased attempts
      
      while (attempts < maxAttempts) {
        const currentUser = store.getters['auth/currentUser']
        const isAuthenticated = store.getters['auth/isAuthenticated']
        
        console.log(`Attempt ${attempts + 1}: User=${!!currentUser}, Authenticated=${isAuthenticated}`)
        
        if (currentUser && isAuthenticated) {
          console.log('User found and authenticated, setting up component:', currentUser)
          
          // Set user info from store
          userInfo.value = {
            full_name: currentUser.full_name || `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.username,
            user_id: currentUser.userid || currentUser.user_id || currentUser.UserId,
            username: currentUser.username,
            role: currentUser.role || 'User'
          }
          console.log('Current user info:', userInfo.value)
          
          // Fetch both assigned tasks and reviews now that we have user data
          await Promise.all([
            fetchMyApprovals(),
            fetchMyReviews()
          ])
          break
        } else if (!currentUser && attempts === 0) {
          // Try to validate session on first attempt
          console.log('No user found, attempting to validate session...')
          try {
            await store.dispatch('auth/validateSession')
          } catch (error) {
            console.error('Session validation failed:', error)
          }
        }
        
        console.log(`Waiting for user authentication... (attempt ${attempts + 1}/${maxAttempts})`)
        await new Promise(resolve => setTimeout(resolve, 250)) // Reduced wait time
        attempts++
      }
      
      if (attempts >= maxAttempts) {
        console.error('Failed to get user authentication after maximum attempts')
        console.log('Store state:', store.state)
        console.log('Auth module state:', store.state.auth)
        console.log('Session token:', localStorage.getItem('session_token'))
        userInfo.value = null
        assignedApprovals.value = []
        reviewApprovals.value = []
      }
    })

    // Watch for authentication state changes
    watch(() => store.getters['auth/currentUser'], (newUser, oldUser) => {
      console.log('User authentication state changed:', { newUser, oldUser })
      if (newUser && !oldUser) {
        // User just logged in
        console.log('User logged in, setting up component')
        userInfo.value = {
          full_name: newUser.full_name || `${newUser.first_name || ''} ${newUser.last_name || ''}`.trim() || newUser.username,
          user_id: newUser.userid || newUser.user_id || newUser.UserId,
          username: newUser.username,
          role: newUser.role || 'User'
        }
        Promise.all([
          fetchMyApprovals(),
          fetchMyReviews()
        ])
      } else if (!newUser && oldUser) {
        // User logged out
        console.log('User logged out, clearing data')
        userInfo.value = null
        assignedApprovals.value = []
        reviewApprovals.value = []
      }
    }, { immediate: true })

    // Refresh approvals when component is activated (e.g., when navigating back to this page)
    onActivated(() => {
      console.log('MyContractApprovals component activated - refreshing approvals')
      Promise.all([
        fetchMyApprovals(),
        fetchMyReviews()
      ])
    })

    return {
      // Store
      store,
      
      // Data
      assignedApprovals,
      reviewApprovals,
      isLoadingApprovals,
      isLoadingReviews,
      userInfo,
      activeTab,
      filters,
      showCommentModal,
      showViewModal,
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
      closeViewModal,
      clearFilters,
      approveContract,
      rejectContract
    }
  }
}
</script>

<style src="./MyContractApprovals.css"></style>
