<template>
  <div class="space-y-6">
    <!-- Main Header - Hidden when plan detail is shown -->
    <div v-if="!showPlanDetail" class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-foreground">Plan Library — Strategies</h1>
        <p class="text-muted-foreground">Browse and manage BCP/DRP strategies and their plans</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn--outline" @click="toggleView">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
          </svg>
          {{ viewMode === 'strategy' ? 'Table View' : 'Strategy View' }}
        </button>
      </div>
    </div>

    <!-- Search & Filter Section - Hidden when plan detail is shown -->
    <div v-if="!showPlanDetail" class="card">
      <div class="card-header">
        <h3 class="card-title flex items-center gap-2">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
          </svg>
          Search & Filter
        </h3>
      </div>
      <div class="card-content">
        <div class="grid grid-cols-6 gap-4 mb-4">
          <div>
            <label class="block text-sm font-medium mb-2">Search</label>
            <div class="relative">
              <svg class="absolute left-3 top-3 h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input 
                class="input pl-10 w-full"
                placeholder="Search strategies or plans..."
                v-model="searchTerm"
              />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">Plan Type</label>
            <select class="input w-full" v-model="filters.planType">
              <option value="all">Any</option>
              <option value="BCP">BCP</option>
              <option value="DRP">DRP</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">Status</label>
            <select class="input w-full" v-model="filters.status">
              <option value="all">Any</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="OCR_IN_PROGRESS">OCR In Progress</option>
              <option value="OCR_COMPLETED">OCR Completed</option>
              <option value="ASSIGNED_FOR_EVALUATION">Assigned for Evaluation</option>
              <option value="UNDER_EVALUATION">Under Evaluation</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="REVISION_REQUESTED">Revision Requested</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">Vendor</label>
            <select class="input w-full" v-model="filters.vendor">
              <option value="all">Any</option>
              <option value="Mau">Mau</option>
              <option value="CoreNet">CoreNet</option>
              <option value="FinEdge">FinEdge</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">Scope</label>
            <select class="input w-full" v-model="filters.scope">
              <option value="all">Any</option>
              <option value="application">Application</option>
              <option value="network">Network</option>
              <option value="cloud">Cloud</option>
              <option value="physical_server">Physical Server</option>
              <option value="physical_device">Physical Device</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">Criticality</label>
            <select class="input w-full" v-model="filters.criticality">
              <option value="all">Any</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Plan Detail View -->
    <div v-if="showPlanDetail" class="plan-detail-view">
      <div class="plan-detail-header">
        <button class="btn btn--outline" @click="goBackToLibrary">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
          </svg>
          Back to {{ viewMode === 'strategy' ? 'Strategy' : 'Table' }} View
        </button>
        <div class="plan-detail-title">
          <h1 class="text-2xl font-bold text-foreground">{{ planDetailData?.plan_info?.plan_name }}</h1>
          <p class="text-muted-foreground">Plan ID: {{ planDetailData?.plan_info?.plan_id }} • {{ planDetailData?.plan_info?.plan_type }}</p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="planDetailLoading" class="flex items-center justify-center py-8">
        <div class="text-muted-foreground">Loading plan details...</div>
      </div>
      
      <!-- Error State -->
      <div v-else-if="planDetailError" class="flex items-center justify-center py-8">
        <div class="text-red-600">Error: {{ planDetailError }}</div>
      </div>
      
      <!-- Plan Detail Content -->
      <div v-else-if="planDetailData" class="plan-detail-content">
        <!-- Three Column Grid Layout -->
        <div class="plan-detail-grid">
          <!-- Plan Overview Column -->
          <div class="plan-detail-column">
            <div class="card">
              <div class="card-header">
                <h3 class="card-title">Plan Overview</h3>
              </div>
              <div class="card-content">
                <div class="space-y-3">
                  <div>
                    <label class="text-sm font-medium">Plan Type</label>
                    <p class="text-sm">{{ planDetailData.plan_info.plan_type }}</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Status</label>
                    <span :class="['badge', getStatusColor(planDetailData.plan_info.status)]">
                      {{ planDetailData.plan_info.status }}
                    </span>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Criticality</label>
                    <span :class="['badge', getCriticalityColor(planDetailData.plan_info.criticality)]">
                      {{ planDetailData.plan_info.criticality }}
                    </span>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Version</label>
                    <p class="text-sm">{{ planDetailData.plan_info.version }}</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Strategy</label>
                    <p class="text-sm">{{ planDetailData.plan_info.strategy_name }}</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Vendor</label>
                    <p class="text-sm">{{ planDetailData.plan_info.vendor_name }}</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Submitted</label>
                    <p class="text-sm">{{ formatDate(planDetailData.plan_info.submitted_at) }}</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Document Date</label>
                    <p class="text-sm">{{ formatDate(planDetailData.plan_info.document_date) }}</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Plan Scope</label>
                    <p class="text-sm">{{ planDetailData.plan_info.plan_scope || 'N/A' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Extracted Details Column -->
          <div class="plan-detail-column">
            <div v-if="planDetailData.extracted_details" class="card">
              <div class="card-header">
                <h3 class="card-title">Extracted Details</h3>
                <span class="text-sm text-muted-foreground">
                  Extracted: {{ formatDate(planDetailData.extracted_details.extracted_at) }}
                </span>
              </div>
              <div class="card-content">
                <!-- Purpose & Scope -->
                <div v-if="planDetailData.extracted_details.purpose_scope" class="mb-3">
                  <label class="text-sm font-medium">Purpose & Scope</label>
                  <p class="text-sm">{{ planDetailData.extracted_details.purpose_scope }}</p>
                </div>

                <!-- Regulatory References -->
                <div v-if="planDetailData.extracted_details.regulatory_references?.length" class="mb-3">
                  <label class="text-sm font-medium">Regulatory References</label>
                  <ul class="text-sm list-disc list-inside">
                    <li v-for="ref in planDetailData.extracted_details.regulatory_references" :key="ref">
                      {{ ref }}
                    </li>
                  </ul>
                </div>

                <!-- Critical Services/Systems -->
                <div v-if="planDetailData.plan_info.plan_type === 'BCP'">
                  <div v-if="planDetailData.extracted_details.critical_services?.length" class="mb-3">
                    <label class="text-sm font-medium">Critical Services</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="service in planDetailData.extracted_details.critical_services" :key="service">
                        {{ service }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="planDetailData.extracted_details.dependencies_internal?.length" class="mb-3">
                    <label class="text-sm font-medium">Internal Dependencies</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="dep in planDetailData.extracted_details.dependencies_internal" :key="dep">
                        {{ dep }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="planDetailData.extracted_details.dependencies_external?.length" class="mb-3">
                    <label class="text-sm font-medium">External Dependencies</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="dep in planDetailData.extracted_details.dependencies_external" :key="dep">
                        {{ dep }}
                      </li>
                    </ul>
                  </div>
                </div>
                <div v-else>
                  <div v-if="planDetailData.extracted_details.critical_systems?.length" class="mb-3">
                    <label class="text-sm font-medium">Critical Systems</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="system in planDetailData.extracted_details.critical_systems" :key="system">
                        {{ system }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="planDetailData.extracted_details.critical_applications?.length" class="mb-3">
                    <label class="text-sm font-medium">Critical Applications</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="app in planDetailData.extracted_details.critical_applications" :key="app">
                        {{ app }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="planDetailData.extracted_details.databases_list?.length" class="mb-3">
                    <label class="text-sm font-medium">Databases</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="db in planDetailData.extracted_details.databases_list" :key="db">
                        {{ db }}
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- Recovery Objectives -->
                <div v-if="planDetailData.extracted_details.rto_targets" class="mb-3">
                  <label class="text-sm font-medium">RTO Targets</label>
                  <div class="text-sm">
                    <div v-for="(value, key) in planDetailData.extracted_details.rto_targets" :key="key" class="flex justify-between">
                      <span>{{ key }}:</span>
                      <span>{{ value }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="planDetailData.extracted_details.rpo_targets" class="mb-3">
                  <label class="text-sm font-medium">RPO Targets</label>
                  <div class="text-sm">
                    <div v-for="(value, key) in planDetailData.extracted_details.rpo_targets" :key="key" class="flex justify-between">
                      <span>{{ key }}:</span>
                      <span>{{ value }}</span>
                    </div>
                  </div>
                </div>

                <!-- Procedures -->
                <div v-if="planDetailData.plan_info.plan_type === 'BCP'">
                  <div v-if="planDetailData.extracted_details.incident_types?.length" class="mb-3">
                    <label class="text-sm font-medium">Incident Types</label>
                    <ul class="text-sm list-disc list-inside">
                      <li v-for="type in planDetailData.extracted_details.incident_types" :key="type">
                        {{ type }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="planDetailData.extracted_details.communication_plan_internal" class="mb-3">
                    <label class="text-sm font-medium">Internal Communication Plan</label>
                    <p class="text-sm">{{ planDetailData.extracted_details.communication_plan_internal }}</p>
                  </div>
                </div>
                <div v-else>
                  <div v-if="planDetailData.extracted_details.failover_procedures" class="mb-3">
                    <label class="text-sm font-medium">Failover Procedures</label>
                    <p class="text-sm">{{ planDetailData.extracted_details.failover_procedures }}</p>
                  </div>
                  <div v-if="planDetailData.extracted_details.failback_procedures" class="mb-3">
                    <label class="text-sm font-medium">Failback Procedures</label>
                    <p class="text-sm">{{ planDetailData.extracted_details.failback_procedures }}</p>
                  </div>
                  <div v-if="planDetailData.extracted_details.data_backup_strategy" class="mb-3">
                    <label class="text-sm font-medium">Data Backup Strategy</label>
                    <p class="text-sm">{{ planDetailData.extracted_details.data_backup_strategy }}</p>
                  </div>
                </div>

                <!-- Testing & Maintenance -->
                <div v-if="planDetailData.extracted_details.training_testing_schedule" class="mb-3">
                  <label class="text-sm font-medium">Training & Testing Schedule</label>
                  <p class="text-sm">{{ planDetailData.extracted_details.training_testing_schedule }}</p>
                </div>
                <div v-if="planDetailData.extracted_details.testing_validation_schedule" class="mb-3">
                  <label class="text-sm font-medium">Testing & Validation Schedule</label>
                  <p class="text-sm">{{ planDetailData.extracted_details.testing_validation_schedule }}</p>
                </div>
                <div v-if="planDetailData.extracted_details.maintenance_review_cycle" class="mb-3">
                  <label class="text-sm font-medium">Maintenance & Review Cycle</label>
                  <p class="text-sm">{{ planDetailData.extracted_details.maintenance_review_cycle }}</p>
                </div>
              </div>
            </div>

            <!-- No Extracted Details Message -->
            <div v-else class="card">
              <div class="card-header">
                <h3 class="card-title">Extracted Details</h3>
              </div>
              <div class="card-content">
                <div class="text-center py-4">
                  <p class="text-muted-foreground">No extracted details available for this plan.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Evaluations Column -->
          <div class="plan-detail-column">
            <div v-if="planDetailData.evaluations?.length" class="card">
              <div class="card-header">
                <h3 class="card-title">Evaluations ({{ planDetailData.evaluation_count }})</h3>
              </div>
              <div class="card-content">
                <div class="space-y-3">
                  <div 
                    v-for="evaluation in planDetailData.evaluations" 
                    :key="evaluation.evaluation_id"
                    class="evaluation-item"
                  >
                    <div class="evaluation-header">
                      <div class="evaluation-info">
                        <h4 class="font-medium">Evaluation #{{ evaluation.evaluation_id }}</h4>
                        <p class="text-sm text-muted-foreground">
                          Assigned: {{ formatDate(evaluation.assigned_at) }} • 
                          Due: {{ formatDate(evaluation.due_date) }}
                        </p>
                      </div>
                      <div class="evaluation-status">
                        <span :class="['badge', getStatusColor(evaluation.status)]">
                          {{ evaluation.status }}
                        </span>
                      </div>
                    </div>
                    <div v-if="evaluation.overall_score !== null" class="evaluation-scores">
                      <div class="space-y-2">
                        <div>
                          <label class="text-sm font-medium">Overall Score</label>
                          <p class="text-lg font-bold text-green-600">{{ evaluation.overall_score }}/100</p>
                        </div>
                        <div>
                          <label class="text-sm font-medium">Quality</label>
                          <p class="text-sm">{{ evaluation.quality_score || 'N/A' }}</p>
                        </div>
                        <div>
                          <label class="text-sm font-medium">Coverage</label>
                          <p class="text-sm">{{ evaluation.coverage_score || 'N/A' }}</p>
                        </div>
                        <div>
                          <label class="text-sm font-medium">Compliance</label>
                          <p class="text-sm">{{ evaluation.compliance_score || 'N/A' }}</p>
                        </div>
                        <div>
                          <label class="text-sm font-medium">Weighted</label>
                          <p class="text-sm">{{ evaluation.weighted_score || 'N/A' }}</p>
                        </div>
                      </div>
                    </div>
                    <div v-if="evaluation.evaluator_comments" class="evaluation-comments">
                      <label class="text-sm font-medium">Evaluator Comments</label>
                      <p class="text-sm">{{ evaluation.evaluator_comments }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- No Evaluations Message -->
            <div v-else class="card">
              <div class="card-header">
                <h3 class="card-title">Evaluations</h3>
              </div>
              <div class="card-content">
                <div class="text-center py-4">
                  <p class="text-muted-foreground">No evaluations available for this plan.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Strategy View -->
    <div v-else-if="viewMode === 'strategy' && !showPlanDetail">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title flex items-center gap-2">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
            Strategies ({{ strategies.length }} strategies)
          </h3>
        </div>
        <div class="card-content">
          <!-- Loading State -->
          <div v-if="loading" class="flex items-center justify-center py-8">
            <div class="text-muted-foreground">Loading strategies...</div>
          </div>
          
          <!-- Error State -->
          <div v-else-if="error" class="flex items-center justify-center py-8">
            <div class="text-red-600">Error: {{ error }}</div>
          </div>
          
          <!-- Empty State -->
          <div v-else-if="strategies.length === 0" class="flex items-center justify-center py-8">
            <div class="text-muted-foreground">No strategies found matching your criteria.</div>
          </div>
          
          <!-- Strategy Cards -->
          <div v-else class="space-y-4 strategy-cards-container">
            <div 
              v-for="strategy in strategies" 
              :key="strategy.strategy_id"
              class="strategy-card"
              :class="{ 'strategy-card--expanded': expandedStrategies.includes(strategy.strategy_id) }"
            >
              <!-- Strategy Header -->
              <div class="strategy-header" @click="toggleStrategy(strategy.strategy_id)">
                <div class="strategy-header-content">
                  <div class="strategy-title-section">
                    <div class="strategy-title-row">
                      <h4 class="strategy-title">{{ strategy.strategy_name }}</h4>
                      <div class="strategy-status-badges">
                        <span 
                          v-for="(count, status) in strategy.status_summary" 
                          :key="status"
                          :class="['status-badge', getStatusColor(String(status))]"
                        >
                          {{ status }}: {{ count }}
                        </span>
                      </div>
                    </div>
                    <p class="strategy-subtitle">{{ strategy.vendor_name }} • Strategy ID: {{ strategy.strategy_id }}</p>
                  </div>
                  <div class="strategy-stats">
                    <div class="stat-item">
                      <span class="stat-number">{{ strategy.plan_count }}</span>
                      <span class="stat-label">Plans</span>
                    </div>
                  </div>
                  <div class="strategy-actions">
                    <svg 
                      class="expand-icon" 
                      :class="{ 'expanded': expandedStrategies.includes(strategy.strategy_id) }"
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                  </div>
                </div>
              </div>
              
              <!-- Expanded Plans Section -->
              <div v-if="expandedStrategies.includes(strategy.strategy_id)" class="strategy-plans">
                <div class="plans-header">
                  <h5 class="plans-title">Plans in this Strategy</h5>
                </div>
                <div class="plans-grid">
                  <div 
                    v-for="plan in strategy.plans" 
                    :key="plan.plan_id"
                    class="plan-card"
                  >
                    <div class="plan-header">
                      <div class="plan-title-section">
                        <h6 class="plan-title">{{ plan.plan_name }}</h6>
                        <p class="plan-id">Plan ID: {{ plan.plan_id }}</p>
                      </div>
                      <div class="plan-type-badge">
                        <span :class="plan.plan_type === 'BCP' ? 'badge badge--default' : 'badge badge--secondary'">
                          {{ plan.plan_type }}
                        </span>
                      </div>
                    </div>
                    <div class="plan-details">
                      <div class="plan-detail-row">
                        <span class="detail-label">Status:</span>
                        <span :class="['badge', getStatusColor(plan.status)]">
                          {{ plan.status }}
                        </span>
                      </div>
                      <div class="plan-detail-row">
                        <span class="detail-label">Criticality:</span>
                        <span :class="['badge', getCriticalityColor(plan.criticality)]">
                          {{ plan.criticality }}
                        </span>
                      </div>
                      <div class="plan-detail-row">
                        <span class="detail-label">Scope:</span>
                        <span class="detail-value">{{ plan.plan_scope || 'N/A' }}</span>
                      </div>
                      <div class="plan-detail-row">
                        <span class="detail-label">Submitted:</span>
                        <span class="detail-value">{{ formatDate(plan.submitted_at) }}</span>
                      </div>
                    </div>
                    <div class="plan-actions">
                      <button class="btn btn--ghost btn--sm" @click="handleViewPlan(plan)" title="View Plan">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                      </button>
                      <button class="btn btn--ghost btn--sm" @click="handleApprovalAssignment(plan)" title="Approval Assignment">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table View (Original) -->
    <div v-else-if="!showPlanDetail" class="card">
      <div class="card-header">
        <h3 class="card-title flex items-center gap-2">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Plans ({{ filteredData.length }} plans)
        </h3>
      </div>
      <div class="card-content">
        <!-- Loading State -->
        <div v-if="loading" class="flex items-center justify-center py-8">
          <div class="text-muted-foreground">Loading plans...</div>
        </div>
        
        <!-- Error State -->
        <div v-else-if="error" class="flex items-center justify-center py-8">
          <div class="text-red-600">Error: {{ error }}</div>
        </div>
        
        <!-- Empty State -->
        <div v-else-if="filteredData.length === 0" class="flex items-center justify-center py-8">
          <div class="text-muted-foreground">No plans found matching your criteria.</div>
        </div>
        
        <!-- Data Table -->
        <table v-else class="table">
          <thead>
            <tr>
              <th>Plan ID</th>
              <th>Plan Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Scope</th>
              <th>Vendor</th>
              <th>Criticality</th>
              <th>Strategy</th>
              <th>Last Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="plan in filteredData" :key="plan.plan_id">
              <td class="font-medium">{{ plan.plan_id }}</td>
              <td>{{ plan.plan_name }}</td>
              <td>
                <span :class="plan.plan_type === 'BCP' ? 'badge badge--default' : 'badge badge--secondary'">
                  {{ plan.plan_type }}
                </span>
              </td>
              <td>
                <span :class="['badge', getStatusColor(plan.status)]">
                  {{ plan.status }}
                </span>
              </td>
              <td>{{ plan.plan_scope }}</td>
              <td>{{ plan.vendor_name }}</td>
              <td>
                <span :class="['badge', getCriticalityColor(plan.criticality)]">
                  {{ plan.criticality }}
                </span>
              </td>
              <td>{{ plan.strategy_name || 'N/A' }}</td>
              <td>{{ formatDate(plan.submitted_at) }}</td>
              <td>
                <div class="flex gap-1">
                  <button class="btn btn--ghost btn--sm" @click="handleViewPlan(plan)" title="View Plan">
                    <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                  </button>
                  <button class="btn btn--ghost btn--sm" @click="handleApprovalAssignment(plan)" title="Approval Assignment">
                    <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Plan Details Modal -->
    <div v-if="selectedPlan" class="modal-overlay" @click.self="closeDetailModal">
      <div class="modal-content max-w-4xl">
        <button @click="closeDetailModal" class="absolute right-4 top-4 btn btn--ghost btn--sm modal-close-button">✕</button>
        <div class="modal-header">
          <h3 class="modal-title">Plan Details — {{ selectedPlan.plan_name }} (Plan ID: {{ selectedPlan.plan_id }})</h3>
        </div>
        <div class="p-6 space-y-6">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="text-sm font-medium">Plan Type</label>
              <p class="text-sm">{{ selectedPlan.plan_type }}</p>
            </div>
            <div>
              <label class="text-sm font-medium">Status</label>
              <span :class="['badge', getStatusColor(selectedPlan.status)]">
                {{ selectedPlan.status }}
              </span>
            </div>
            <div>
              <label class="text-sm font-medium">Vendor</label>
              <p class="text-sm">{{ selectedPlan.vendor_name }}</p>
            </div>
            <div>
              <label class="text-sm font-medium">Criticality</label>
              <span :class="['badge', getCriticalityColor(selectedPlan.criticality)]">
                {{ selectedPlan.criticality }}
              </span>
            </div>
          </div>

          <div class="tabs">
            <div class="tabs-list">
              <button 
                class="tabs-trigger"
                :data-state="activeTab === 'overview' ? 'active' : 'inactive'"
                @click="activeTab = 'overview'"
              >
                Overview
              </button>
              <button 
                class="tabs-trigger"
                :data-state="activeTab === 'documents' ? 'active' : 'inactive'"
                @click="activeTab = 'documents'"
              >
                Documents
              </button>
              <button 
                class="tabs-trigger"
                :data-state="activeTab === 'evaluation' ? 'active' : 'inactive'"
                @click="activeTab = 'evaluation'"
              >
                Evaluation
              </button>
              <button 
                class="tabs-trigger"
                :data-state="activeTab === 'testing' ? 'active' : 'inactive'"
                @click="activeTab = 'testing'"
              >
                Testing
              </button>
            </div>
            
            <div v-show="activeTab === 'overview'" class="tabs-content space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-sm font-medium">Plan Scope</label>
                  <p class="text-sm">{{ selectedPlan.plan_scope }}</p>
                </div>
                <div>
                  <label class="text-sm font-medium">Strategy</label>
                  <p class="text-sm">{{ selectedPlan.strategy_name || 'N/A' }}</p>
                </div>
                <div>
                  <label class="text-sm font-medium">Submitted At</label>
                  <p class="text-sm">{{ formatDate(selectedPlan.submitted_at) }}</p>
                </div>
              </div>
            </div>

            <div v-show="activeTab === 'documents'" class="tabs-content space-y-4">
              <div class="border rounded-lg p-4">
                <h4 class="font-medium mb-2">Plan Documents</h4>
                <table class="table">
                  <thead>
                    <tr>
                      <th>Document Name</th>
                      <th>Type</th>
                      <th>Uploaded By</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="doc in currentPlanDetails?.documents" :key="doc.id">
                      <td>{{ doc.name }}</td>
                      <td>{{ doc.type }}</td>
                      <td>{{ doc.uploadedBy }}</td>
                      <td>
                        <span :class="['badge', getStatusColor(doc.status)]">
                          {{ doc.status }}
                        </span>
                      </td>
                      <td>
                        <button class="btn btn--ghost btn--sm">
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                          </svg>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-show="activeTab === 'evaluation'" class="tabs-content space-y-4">
              <div class="border rounded-lg p-4">
                <h4 class="font-medium mb-2">Evaluation Summary</h4>
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <label class="text-sm font-medium">Overall Score</label>
                    <p class="text-lg font-bold text-green-600">88/100</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Quality</label>
                    <p class="text-sm">90</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Coverage</label>
                    <p class="text-sm">85</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Compliance</label>
                    <p class="text-sm">87</p>
                  </div>
                  <div>
                    <label class="text-sm font-medium">Recovery</label>
                    <p class="text-sm">90</p>
                  </div>
                </div>
                <div class="mt-4">
                  <label class="text-sm font-medium">Evaluator Notes</label>
                  <p class="text-sm text-muted-foreground">
                    Strong coverage of application recovery and RTO compliance, but lacks some clarity in RPO validation.
                  </p>
                </div>
              </div>
            </div>

            <div v-show="activeTab === 'testing'" class="tabs-content space-y-4">
              <div class="border rounded-lg p-4">
                <h4 class="font-medium mb-2">Test Assignments</h4>
                <table class="table">
                  <thead>
                    <tr>
                      <th>Test ID</th>
                      <th>Questionnaire Name</th>
                      <th>Assigned To</th>
                      <th>Due Date</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="test in currentPlanDetails?.testAssignments" :key="test.id">
                      <td>{{ test.id }}</td>
                      <td>{{ test.questionnaireName }}</td>
                      <td>{{ test.assignedTo }}</td>
                      <td>{{ test.dueDate }}</td>
                      <td>
                        <span :class="['badge', getStatusColor(test.status)]">
                          {{ test.status }}
                        </span>
                      </td>
                      <td>
                        <button class="btn btn--ghost btn--sm">
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                          </svg>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div class="mt-4">
                  <button class="btn btn--primary" @click="handleAssignTesting(selectedPlan)">
                    <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    Assign Testing
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>


  </div>
</template>

<script setup lang="ts">
import './PlanLibrary.css'
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import http from '../../api/http.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const searchTerm = ref("")
const filters = ref({
  planType: "all",
  status: "all",
  vendor: "all",
  region: "all",
  scope: "all",
  criticality: "all"
})
const selectedPlan = ref<any>(null)
const showAssignModal = ref(false)
const showTestingModal = ref(false)
const activeTab = ref("overview")

// View mode state
const viewMode = ref<'strategy' | 'table'>('strategy')
const expandedStrategies = ref<number[]>([])

// Plan detail view state
const showPlanDetail = ref(false)
const planDetailData = ref(null)
const planDetailLoading = ref(false)
const planDetailError = ref(null)

// Data state
const plans = ref([])
const strategies = ref([])
const loading = ref(false)
const error = ref(null)

// Fetch strategies from API
const fetchStrategies = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Build query parameters
    const params = new URLSearchParams()
    
    // Add filter parameters if they exist and are not 'all'
    if (searchTerm.value) params.append('search', searchTerm.value)
    if (filters.value.planType && filters.value.planType !== 'all') params.append('plan_type', filters.value.planType)
    if (filters.value.status && filters.value.status !== 'all') params.append('status', filters.value.status)
    if (filters.value.vendor && filters.value.vendor !== 'all') params.append('vendor', filters.value.vendor)
    if (filters.value.scope && filters.value.scope !== 'all') params.append('scope', filters.value.scope)
    if (filters.value.criticality && filters.value.criticality !== 'all') params.append('criticality', filters.value.criticality)
    
    const queryString = params.toString()
    const url = queryString ? `/bcpdrp/strategies/?${queryString}` : '/bcpdrp/strategies/'
    
    const response = await http.get(url)
    strategies.value = response.data.strategies || []
    
    // Show success notification
    await showSuccess('Strategies Loaded', `Successfully loaded ${strategies.value.length} strategies.`, {
      action: 'strategies_loaded',
      count: strategies.value.length,
      search_term: searchTerm.value,
      filters: filters.value
    })
    
    // Show success popup
    PopupService.success(`Successfully loaded ${strategies.value.length} strategies.`, 'Strategies Loaded')
  } catch (err) {
    error.value = err.message || 'Failed to fetch strategies'
    console.error('Error fetching strategies:', err)
    
    // Show error notification
    await showError('Loading Failed', 'Failed to fetch strategies. Please try again.', {
      action: 'strategies_loading_failed',
      error_message: err.message,
      search_term: searchTerm.value
    })
    
    // Show error popup
    PopupService.error('Failed to fetch strategies. Please try again.', 'Loading Failed')
  } finally {
    loading.value = false
  }
}

// Fetch plans from API
const fetchPlans = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Build query parameters
    const params = new URLSearchParams()
    
    // Add filter parameters if they exist and are not 'all'
    if (searchTerm.value) params.append('search', searchTerm.value)
    if (filters.value.planType && filters.value.planType !== 'all') params.append('plan_type', filters.value.planType)
    if (filters.value.status && filters.value.status !== 'all') params.append('status', filters.value.status)
    if (filters.value.vendor && filters.value.vendor !== 'all') params.append('vendor', filters.value.vendor)
    if (filters.value.scope && filters.value.scope !== 'all') params.append('scope', filters.value.scope)
    if (filters.value.criticality && filters.value.criticality !== 'all') params.append('criticality', filters.value.criticality)
    
    const queryString = params.toString()
    const url = queryString ? `/bcpdrp/plans/?${queryString}` : '/bcpdrp/plans/'
    
    const response = await http.get(url)
    plans.value = response.data.plans || []
  } catch (err) {
    error.value = err.message || 'Failed to fetch plans'
    console.error('Error fetching plans:', err)
  } finally {
    loading.value = false
  }
}

// Fetch data based on current view mode
const fetchData = async () => {
  if (viewMode.value === 'strategy') {
    await fetchStrategies()
  } else {
    await fetchPlans()
  }
}

// Toggle view mode
const toggleView = () => {
  viewMode.value = viewMode.value === 'strategy' ? 'table' : 'strategy'
  fetchData()
}

// Toggle strategy expansion
const toggleStrategy = (strategyId: number) => {
  const index = expandedStrategies.value.indexOf(strategyId)
  if (index > -1) {
    expandedStrategies.value.splice(index, 1)
  } else {
    expandedStrategies.value.push(strategyId)
  }
}

// Load data on component mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Plan Library')
  await fetchData()
})

// Watch for filter changes and refetch data
watch([searchTerm, filters], () => {
  fetchData()
}, { deep: true })

// Mock data for plan details (to be replaced with real API calls later)
const mockPlanDetails = {
  // This will be replaced with real API calls for plan details
}

const getStatusColor = (status: string) => {
  switch (status) {
    case "APPROVED": return "bg-green-100 text-green-800";
    case "REJECTED": return "bg-red-100 text-red-800";
    case "IN_PROGRESS": return "bg-blue-100 text-blue-800";
    case "SUBMITTED": return "bg-yellow-100 text-yellow-800";
    default: return "bg-gray-100 text-gray-800";
  }
}

const getCriticalityColor = (criticality: string) => {
  switch (criticality) {
    case "CRITICAL": return "bg-red-100 text-red-800";
    case "HIGH": return "bg-orange-100 text-orange-800";
    case "MEDIUM": return "bg-yellow-100 text-yellow-800";
    case "LOW": return "bg-green-100 text-green-800";
    default: return "bg-gray-100 text-gray-800";
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const filteredData = computed(() => {
  // Since we're now fetching filtered data from the API, we can return the plans directly
  // The filtering is handled on the backend
  return plans.value
})

const currentPlanDetails = computed(() => {
  return selectedPlan.value ? mockPlanDetails[selectedPlan.value.plan_id as keyof typeof mockPlanDetails] : null
})

// Fetch comprehensive plan details
const fetchPlanDetails = async (planId: number) => {
  planDetailLoading.value = true
  planDetailError.value = null
  
  try {
    const response = await http.get(`/bcpdrp/plans/${planId}/comprehensive/`)
    planDetailData.value = response.data
    showPlanDetail.value = true
  } catch (err) {
    planDetailError.value = err.message || 'Failed to fetch plan details'
    console.error('Error fetching plan details:', err)
  } finally {
    planDetailLoading.value = false
  }
}

// Navigate back to library view
const goBackToLibrary = () => {
  showPlanDetail.value = false
  planDetailData.value = null
  planDetailError.value = null
}

const handleViewPlan = (plan: any) => {
  fetchPlanDetails(plan.plan_id)
}



const handleApprovalAssignment = (plan: any) => {
  // Navigate to approval assignment screen and open assign approval form with plan data
  router.push({
    path: '/bcp/approval-assignment',
    query: {
      createNew: 'true',
      planId: plan.plan_id,
      objectId: plan.plan_id,
      objectType: 'PLAN',
      planType: plan.plan_type
    }
  })
}

const handleAssignTesting = (plan: any) => {
  // Navigate to testing assignment screen and open assign testing form with plan data
  router.push({
    path: '/bcp/plan-evaluation',
    query: {
      createNew: 'true',
      planId: plan.plan_id,
      objectId: plan.plan_id,
      objectType: 'PLAN',
      planType: plan.plan_type
    }
  })
}

const closeDetailModal = () => {
  selectedPlan.value = null
}
</script>
