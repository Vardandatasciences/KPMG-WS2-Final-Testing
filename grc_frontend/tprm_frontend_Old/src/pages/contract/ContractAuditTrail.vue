<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Audit Trail</h1>
        <p class="text-muted-foreground">Contract compliance auditing and monitoring</p>
      </div>
      <button @click="showCreateAudit = true" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
        <Plus class="w-4 h-4" />
        Schedule Audit
      </button>
    </div>

    <!-- Search and Filters -->
    <div class="flex flex-col md:flex-row gap-4">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <input
          v-model="searchTerm"
          placeholder="Search contracts, vendors, or auditors..."
          class="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background text-foreground"
        />
      </div>
      <select v-model="filterStatus" @change="handleStatusFilterChange" class="w-full md:w-48 px-3 py-2 border border-input rounded-md bg-background text-foreground">
        <option value="all">All Statuses</option>
        <option value="scheduled">Scheduled</option>
        <option value="in_progress">In Progress</option>
        <option value="completed">Completed</option>
        <option value="overdue">Overdue</option>
      </select>
      <select v-model="filterFrequency" @change="handleFrequencyFilterChange" class="w-full md:w-48 px-3 py-2 border border-input rounded-md bg-background text-foreground">
        <option value="all">All Frequencies</option>
        <option value="monthly">Monthly</option>
        <option value="quarterly">Quarterly</option>
        <option value="annually">Annually</option>
      </select>
    </div>

    <!-- Tabs -->
    <div class="space-y-6">
      <div class="flex border-b">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          :class="[
            'px-4 py-2 border-b-2 transition-colors',
            activeTab === tab.value
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div v-if="activeTab === 'overview'" class="space-y-6">
        <!-- Key Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium">Total Audits</h3>
              <FileCheck class="h-4 w-4 text-muted-foreground" />
            </div>
            <div class="text-2xl font-bold mt-2">{{ auditSchedules.length }}</div>
            <p class="text-xs text-muted-foreground">Scheduled audits</p>
          </div>

          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium">Overdue Audits</h3>
              <AlertTriangle class="h-4 w-4 text-warning" />
            </div>
            <div class="text-2xl font-bold text-warning mt-2">
              {{ overdueAuditsCount }}
            </div>
            <p class="text-xs text-muted-foreground">Require attention</p>
          </div>

          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium">Avg Compliance</h3>
              <CheckCircle class="h-4 w-4 text-success" />
            </div>
            <div class="text-2xl font-bold text-success mt-2">
              {{ averageComplianceScore }}%
            </div>
            <p class="text-xs text-muted-foreground">Across all contracts</p>
          </div>

          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium">Next Audit</h3>
              <Calendar class="h-4 w-4 text-muted-foreground" />
            </div>
            <div class="text-2xl font-bold mt-2">
              {{ scheduledAuditsCount }}
            </div>
            <p class="text-xs text-muted-foreground">Scheduled this month</p>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="border rounded-lg bg-card">
          <div class="p-6 border-b">
            <h3 class="text-lg font-semibold">Recent Audit Activity</h3>
            <p class="text-sm text-muted-foreground">Latest audit updates and findings</p>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div v-for="schedule in recentAudits" :key="schedule.id" class="flex items-center justify-between p-3 border rounded-lg">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    <FileCheck class="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p class="font-medium">{{ schedule.contract_title }}</p>
                    <p class="text-sm text-muted-foreground">
                      {{ schedule.vendor_name }} • {{ schedule.frequency }} audit
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span :class="getStatusBadgeClass(schedule.status)">
                    {{ getStatusText(schedule.status) }}
                  </span>
                  <div class="text-right">
                    <p class="text-sm font-medium">
                      {{ schedule.compliance_score }}% compliant
                    </p>
                    <p class="text-xs text-muted-foreground">
                      Next: {{ schedule.next_audit_date }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Audit Schedules Tab -->
      <div v-if="activeTab === 'schedules'" class="space-y-6">
        <div class="border rounded-lg bg-card">
          <div class="p-6 border-b">
            <h3 class="text-lg font-semibold">Audit Schedules</h3>
            <p class="text-sm text-muted-foreground">Upcoming and overdue contract audits</p>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div v-for="schedule in auditSchedules" :key="schedule.id" class="flex items-center justify-between p-4 border rounded-lg">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                    <FileCheck class="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 class="font-medium">{{ schedule.contract_title }}</h3>
                    <p class="text-sm text-muted-foreground">
                      {{ schedule.contract_id }} • {{ schedule.vendor_name }}
                    </p>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="px-2 py-1 text-xs border rounded-full">{{ schedule.frequency }}</span>
                      <span class="text-xs text-muted-foreground">
                        Assigned to {{ schedule.assigned_auditor }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="flex items-center gap-4">
                  <div class="text-right">
                    <p class="text-sm font-medium">
                      {{ schedule.compliance_score }}% compliant
                    </p>
                    <p class="text-xs text-muted-foreground">
                      Last: {{ schedule.last_audit_date }}
                    </p>
                    <p class="text-xs text-muted-foreground">
                      Next: {{ schedule.next_audit_date }}
                    </p>
                  </div>
                  
                  <div class="flex items-center gap-2">
                    <span :class="getStatusBadgeClass(schedule.status)">
                      {{ getStatusText(schedule.status) }}
                    </span>
                    <button class="px-3 py-1 text-sm border rounded-md hover:bg-muted">
                      <Eye class="w-4 h-4 mr-2" />
                      View
                    </button>
                    <button class="px-3 py-1 text-sm border rounded-md hover:bg-muted">
                      <Edit class="w-4 h-4 mr-2" />
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Completed Audits Tab -->
      <div v-if="activeTab === 'audits'" class="space-y-6">
        <div class="border rounded-lg bg-card">
          <div class="p-6 border-b">
            <h3 class="text-lg font-semibold">Completed Audits</h3>
            <p class="text-sm text-muted-foreground">Historical audit results and findings</p>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div v-for="audit in contractAudits" :key="audit.id" class="flex items-center justify-between p-4 border rounded-lg">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                    <FileCheck class="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 class="font-medium">{{ audit.contract_title }}</h3>
                    <p class="text-sm text-muted-foreground">
                      {{ audit.contract_id }} • {{ audit.vendor_name }}
                    </p>
                    <div class="flex items-center gap-2 mt-1">
                      <span :class="getRiskBadgeClass(audit.risk_assessment)">
                        {{ audit.risk_assessment.toUpperCase() }}
                      </span>
                      <span class="text-xs text-muted-foreground">
                        Audited by {{ audit.auditor }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="flex items-center gap-4">
                  <div class="text-right">
                    <p :class="getComplianceScoreColor(audit.overall_compliance_score)" class="text-lg font-bold">
                      {{ audit.overall_compliance_score }}%
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ audit.audit_date }}
                    </p>
                    <span :class="getStatusBadgeClass(audit.status)">
                      {{ getStatusText(audit.status) }}
                    </span>
                  </div>
                  
                  <div class="flex items-center gap-2">
                    <button @click="viewAuditDetails(audit)" class="px-3 py-1 text-sm border rounded-md hover:bg-muted">
                      <Eye class="w-4 h-4 mr-2" />
                      View Details
                    </button>
                    <button class="px-3 py-1 text-sm border rounded-md hover:bg-muted">
                      <Download class="w-4 h-4 mr-2" />
                      Report
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Terms & Clauses Tab -->
      <div v-if="activeTab === 'terms-clauses'" class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 class="text-2xl font-bold text-foreground">Terms & Clauses Auditing</h2>
            <p class="text-muted-foreground">Comprehensive auditing of contract terms and legal clauses for compliance and risk assessment</p>
          </div>
          <div class="flex items-center gap-2">
            <button class="px-4 py-2 border rounded-md hover:bg-muted">
              <Scale class="w-4 h-4 mr-2" />
              Audit Templates
            </button>
            <button class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
              <Gavel class="w-4 h-4 mr-2" />
              Start New Audit
            </button>
          </div>
        </div>

        <!-- Terms & Clauses Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium text-blue-700">Total Audits</h3>
              <BookOpen class="h-4 w-4 text-blue-600" />
            </div>
            <div class="text-3xl font-bold text-blue-700 mt-2">{{ termsClausesAuditSummaries.length }}</div>
            <p class="text-xs text-muted-foreground">Terms & clauses audits</p>
            <div class="mt-2 text-xs text-blue-600">
              {{ overdueTermsAuditsCount }} overdue
            </div>
          </div>

          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium text-orange-700">Critical Findings</h3>
              <AlertTriangle class="h-4 w-4 text-orange-600" />
            </div>
            <div class="text-3xl font-bold text-orange-600 mt-2">
              {{ totalCriticalFindings }}
            </div>
            <p class="text-xs text-muted-foreground">Require immediate attention</p>
            <div class="mt-2 text-xs text-orange-600">
              {{ totalHighRiskItems }} high risk
            </div>
          </div>

          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium text-green-700">Avg Compliance</h3>
              <CheckCircle class="h-4 w-4 text-green-600" />
            </div>
            <div class="text-3xl font-bold text-green-600 mt-2">
              {{ averageTermsComplianceScore }}%
            </div>
            <p class="text-xs text-muted-foreground">Terms & clauses compliance</p>
            <div class="mt-2 text-xs text-green-600">
              {{ highComplianceContractsCount }} contracts ≥90%
            </div>
          </div>

          <div class="border rounded-lg bg-card p-6">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium text-purple-700">Total Items</h3>
              <Target class="h-4 w-4 text-purple-600" />
            </div>
            <div class="text-3xl font-bold text-purple-700 mt-2">
              {{ totalAuditedItems }}
            </div>
            <p class="text-xs text-muted-foreground">Terms & clauses audited</p>
            <div class="mt-2 text-xs text-purple-600">
              {{ totalRecommendations }} recommendations
            </div>
          </div>
        </div>

        <!-- Terms & Clauses Audit List -->
        <div class="border rounded-lg bg-card">
          <div class="p-6 border-b">
            <h3 class="text-lg font-semibold flex items-center gap-2">
              <BookOpen class="w-5 h-5" />
              Terms & Clauses Audit History
            </h3>
            <p class="text-sm text-muted-foreground">Detailed audit results for contract terms and legal clauses</p>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div v-for="auditSummary in termsClausesAuditSummaries" :key="auditSummary.contract_id" class="flex items-center justify-between p-4 border rounded-lg">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <BookOpen class="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 class="font-medium">{{ auditSummary.contract_title }}</h3>
                    <p class="text-sm text-muted-foreground">
                      {{ auditSummary.contract_id }} • {{ auditSummary.vendor_name }}
                    </p>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="px-2 py-1 text-xs border rounded-full">
                        {{ auditSummary.terms_audited }} Terms
                      </span>
                      <span class="px-2 py-1 text-xs border rounded-full">
                        {{ auditSummary.clauses_audited }} Clauses
                      </span>
                      <span class="text-xs text-muted-foreground">
                        Audited by {{ auditSummary.auditor }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="flex items-center gap-4">
                  <div class="text-right">
                    <p :class="getComplianceScoreColor(auditSummary.overall_compliance_score)" class="text-lg font-bold">
                      {{ auditSummary.overall_compliance_score }}%
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ auditSummary.audit_date }}
                    </p>
                    <div class="flex items-center gap-1 mt-1">
                      <span v-if="auditSummary.critical_findings > 0" class="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                        {{ auditSummary.critical_findings }} Critical
                      </span>
                      <span v-if="auditSummary.high_risk_items > 0" class="px-2 py-1 text-xs border border-orange-600 text-orange-600 rounded-full">
                        {{ auditSummary.high_risk_items }} High Risk
                      </span>
                    </div>
                  </div>
                  
                  <div class="flex items-center gap-2">
                    <button @click="viewTermsClausesDetails(auditSummary)" class="px-3 py-1 text-sm border rounded-md hover:bg-muted">
                      <Eye class="w-4 h-4 mr-2" />
                      View Details
                    </button>
                    <button class="px-3 py-1 text-sm border rounded-md hover:bg-muted">
                      <Download class="w-4 h-4 mr-2" />
                      Report
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Reports Tab -->
      <div v-if="activeTab === 'reports'" class="space-y-6">
        <div class="border rounded-lg bg-card">
          <div class="p-6 border-b">
            <h3 class="text-lg font-semibold">Audit Reports</h3>
            <p class="text-sm text-muted-foreground">Generate and download audit reports</p>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div class="border rounded-lg bg-card p-6 cursor-pointer hover:shadow-md transition-shadow">
                <h3 class="text-lg font-semibold">Compliance Summary</h3>
                <p class="text-sm text-muted-foreground">Overall compliance status report</p>
                <button class="w-full mt-4 px-4 py-2 border rounded-md hover:bg-muted">
                  <Download class="w-4 h-4 mr-2" />
                  Generate Report
                </button>
              </div>

              <div class="border rounded-lg bg-card p-6 cursor-pointer hover:shadow-md transition-shadow">
                <h3 class="text-lg font-semibold">Risk Assessment</h3>
                <p class="text-sm text-muted-foreground">Contract risk analysis report</p>
                <button class="w-full mt-4 px-4 py-2 border rounded-md hover:bg-muted">
                  <Download class="w-4 h-4 mr-2" />
                  Generate Report
                </button>
              </div>

              <div class="border rounded-lg bg-card p-6 cursor-pointer hover:shadow-md transition-shadow">
                <h3 class="text-lg font-semibold">Audit Schedule</h3>
                <p class="text-sm text-muted-foreground">Upcoming audit calendar</p>
                <button class="w-full mt-4 px-4 py-2 border rounded-md hover:bg-muted">
                  <Download class="w-4 h-4 mr-2" />
                  Generate Report
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
         </div>

    <!-- Create Audit Dialog -->
    <div v-if="showCreateAudit" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click="closeDialog">
      <div class="bg-background border rounded-lg max-w-6xl max-h-[90vh] overflow-y-auto w-full mx-4" @click.stop>
        <div class="p-6 border-b">
          <h2 class="text-xl font-semibold flex items-center gap-2">
            <FileCheck class="w-5 h-5" />
            Schedule New Audit
          </h2>
          <p class="text-sm text-muted-foreground">Create a new audit schedule for contract compliance review with custom questionnaire</p>
        </div>
        
        <div class="p-6 space-y-6">
          <!-- Basic Audit Information -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Primary Audit Information</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-sm font-medium">Contract Selection *</label>
                <select class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                  <option value="">Select contract to audit</option>
                  <option value="CNT-2024-001">CNT-2024-001 - Cloud Infrastructure Services</option>
                  <option value="CNT-2024-002">CNT-2024-002 - Software Development Services</option>
                  <option value="CNT-2024-003">CNT-2024-003 - Consulting Services</option>
                </select>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium">Audit Frequency *</label>
                <select class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                  <option value="">Select frequency</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="annually">Annually</option>
                </select>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium">Next Audit Date *</label>
                <input type="date" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium">Assigned Auditor *</label>
                <select class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                  <option value="">Select auditor</option>
                  <option value="sarah">Sarah Johnson</option>
                  <option value="mike">Mike Chen</option>
                  <option value="lisa">Lisa Wang</option>
                </select>
              </div>
            </div>

            <div class="space-y-2 mt-4">
              <label class="text-sm font-medium">Audit Scope & Objectives</label>
              <textarea 
                placeholder="Describe the scope and objectives of this audit..."
                rows="4"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
              ></textarea>
            </div>
          </div>

          <!-- Compliance Frameworks -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Compliance Frameworks to Review</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div v-for="framework in complianceFrameworks" :key="framework" class="flex items-center space-x-2">
                <input type="checkbox" :id="framework" class="rounded border-gray-300" />
                <label :for="framework" class="text-sm">{{ framework }}</label>
              </div>
            </div>
          </div>

          <!-- Questionnaire Builder -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Audit Questionnaire Builder</h3>
            <p class="text-sm text-muted-foreground mb-4">Select from standard templates or create custom questions for this audit</p>
            
            <!-- Template Selection -->
            <div class="space-y-4 mb-6">
              <label class="text-base font-medium">Select Questionnaire Template</label>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div v-for="template in questionnaireTemplates" :key="template.id" class="flex items-center space-x-2">
                  <input
                    type="radio"
                    :id="template.id"
                    name="template"
                    :value="template.id"
                    v-model="selectedTemplate"
                    class="rounded border-gray-300"
                  />
                  <label :for="template.id" class="flex-1 cursor-pointer">
                    <div class="font-medium">{{ template.name }}</div>
                    <div class="text-sm text-muted-foreground">
                      {{ template.category }} • {{ template.questions.length }} questions
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <!-- Template Questions Preview -->
            <div v-if="selectedTemplate" class="space-y-3 mb-6">
              <label class="text-base font-medium">Template Questions</label>
              <div class="border rounded-lg p-4 bg-muted/30">
                <div v-for="(question, index) in selectedTemplateQuestions" :key="index" class="flex items-start gap-3 py-2">
                  <div class="w-6 h-6 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center mt-0.5">
                    {{ index + 1 }}
                  </div>
                  <div class="flex-1 text-sm">{{ question }}</div>
                </div>
              </div>
            </div>

            <!-- Custom Questions -->
            <div class="space-y-4 mb-6">
              <label class="text-base font-medium">Add Custom Questions</label>
              <div class="flex gap-2">
                <input
                  v-model="newQuestion"
                  placeholder="Enter a custom question..."
                  @keypress="e => e.key === 'Enter' && addCustomQuestion()"
                  class="flex-1 px-3 py-2 border border-input rounded-md bg-background text-foreground"
                />
                <button @click="addCustomQuestion" class="px-4 py-2 border rounded-md hover:bg-muted">
                  Add Question
                </button>
              </div>

              <div v-if="customQuestions.length > 0" class="space-y-2">
                <label class="text-sm font-medium">Custom Questions Added</label>
                <div class="border rounded-lg p-4 bg-muted/30">
                  <div v-for="(question, index) in customQuestions" :key="index" class="flex items-start gap-3 py-2">
                    <div class="w-6 h-6 rounded-full bg-orange-100 text-orange-600 text-xs flex items-center justify-center mt-0.5">
                      C{{ index + 1 }}
                    </div>
                    <div class="flex-1 text-sm">{{ question }}</div>
                    <button
                      @click="removeCustomQuestion(index)"
                      class="text-red-500 hover:text-red-700"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Question Summary -->
            <div v-if="allQuestions.length > 0" class="space-y-3">
              <label class="text-base font-medium">Question Summary</label>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border rounded-lg bg-muted/30">
                <div class="text-center">
                  <div class="text-2xl font-bold text-primary">
                    {{ allQuestions.length }}
                  </div>
                  <div class="text-sm text-muted-foreground">Total Questions</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-blue-600">
                    {{ selectedTemplateQuestions.length }}
                  </div>
                  <div class="text-sm text-muted-foreground">Template Questions</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-orange-600">
                    {{ customQuestions.length }}
                  </div>
                  <div class="text-sm text-muted-foreground">Custom Questions</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Advanced Settings -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Advanced Settings</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-sm font-medium">Evidence Requirements</label>
                <select class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                  <option value="">Select evidence level</option>
                  <option value="minimal">Minimal - Primary documentation</option>
                  <option value="standard">Standard - Moderate documentation</option>
                  <option value="comprehensive">Comprehensive - Extensive documentation</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium">Risk Assessment Level</label>
                <select class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                  <option value="">Select risk level</option>
                  <option value="low">Low Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk</option>
                  <option value="critical">Critical Risk</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t flex justify-end gap-2">
          <button @click="handleCancel" class="px-4 py-2 border rounded-md hover:bg-muted">
            Cancel
          </button>
          <button @click="handleScheduleAudit" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
            Schedule Audit
          </button>
        </div>
      </div>
    </div>

    <!-- Audit Details Dialog -->
    <div v-if="showAuditDetails" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-background border rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto w-full mx-4">
        <div class="p-6 border-b">
          <h2 class="text-xl font-semibold flex items-center gap-2">
            <FileCheck class="w-5 h-5" />
            Audit Details - {{ selectedAudit?.contract_title }}
          </h2>
          <p class="text-sm text-muted-foreground">Comprehensive audit results and findings</p>
        </div>
        
        <div v-if="selectedAudit" class="p-6 space-y-6">
          <!-- Contract Information -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Contract Information</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span class="font-medium">Contract ID:</span>
                <p class="text-muted-foreground">{{ selectedAudit.contract_id }}</p>
              </div>
              <div>
                <span class="font-medium">Vendor:</span>
                <p class="text-muted-foreground">{{ selectedAudit.vendor_name }}</p>
              </div>
              <div>
                <span class="font-medium">Audit Date:</span>
                <p class="text-muted-foreground">{{ selectedAudit.audit_date }}</p>
              </div>
              <div>
                <span class="font-medium">Auditor:</span>
                <p class="text-muted-foreground">{{ selectedAudit.auditor }}</p>
              </div>
            </div>
          </div>

          <!-- Audit Results -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Audit Results</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="text-center">
                <div :class="getComplianceScoreColor(selectedAudit.overall_compliance_score)" class="text-3xl font-bold">
                  {{ selectedAudit.overall_compliance_score }}%
                </div>
                <div class="text-sm text-muted-foreground">Compliance Score</div>
              </div>
              <div class="text-center">
                <div :class="getRiskBadgeClass(selectedAudit.risk_assessment)" class="text-2xl font-bold">
                  {{ selectedAudit.risk_assessment.toUpperCase() }}
                </div>
                <div class="text-sm text-muted-foreground">Risk Level</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">
                  {{ selectedAudit.next_audit_date }}
                </div>
                <div class="text-sm text-muted-foreground">Next Audit Date</div>
              </div>
            </div>
          </div>

          <!-- Findings & Recommendations -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Findings & Recommendations</h3>
            <div class="space-y-4">
              <div>
                <h4 class="font-medium mb-2">Key Findings</h4>
                <p class="text-sm text-muted-foreground">{{ selectedAudit.findings }}</p>
              </div>
              <div>
                <h4 class="font-medium mb-2">Recommendations</h4>
                <p class="text-sm text-muted-foreground">{{ selectedAudit.recommendations }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t flex justify-end">
          <button @click="showAuditDetails = false" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Terms & Clauses Details Dialog -->
    <div v-if="showTermsClausesDetails" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-background border rounded-lg max-w-5xl max-h-[90vh] overflow-y-auto w-full mx-4">
        <div class="p-6 border-b">
          <h2 class="text-xl font-semibold flex items-center gap-2">
            <BookOpen class="w-5 h-5" />
            Terms & Clauses Details - {{ selectedTermsClausesAudit?.contract_title }}
          </h2>
          <p class="text-sm text-muted-foreground">Detailed audit results for contract terms and legal clauses</p>
        </div>
        
        <div v-if="selectedTermsClausesAudit" class="p-6 space-y-6">
          <!-- Contract Information -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Contract Information</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span class="font-medium">Contract ID:</span>
                <p class="text-muted-foreground">{{ selectedTermsClausesAudit.contract_id }}</p>
              </div>
              <div>
                <span class="font-medium">Vendor:</span>
                <p class="text-muted-foreground">{{ selectedTermsClausesAudit.vendor_name }}</p>
              </div>
              <div>
                <span class="font-medium">Audit Date:</span>
                <p class="text-muted-foreground">{{ selectedTermsClausesAudit.audit_date }}</p>
              </div>
              <div>
                <span class="font-medium">Auditor:</span>
                <p class="text-muted-foreground">{{ selectedTermsClausesAudit.auditor }}</p>
              </div>
            </div>
          </div>

          <!-- Audit Summary -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Audit Summary</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">
                  {{ selectedTermsClausesAudit.terms_audited }}
                </div>
                <div class="text-sm text-muted-foreground">Terms Audited</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-purple-600">
                  {{ selectedTermsClausesAudit.clauses_audited }}
                </div>
                <div class="text-sm text-muted-foreground">Clauses Audited</div>
              </div>
              <div class="text-center">
                <div :class="getComplianceScoreColor(selectedTermsClausesAudit.overall_compliance_score)" class="text-2xl font-bold">
                  {{ selectedTermsClausesAudit.overall_compliance_score }}%
                </div>
                <div class="text-sm text-muted-foreground">Compliance Score</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-orange-600">
                  {{ selectedTermsClausesAudit.critical_findings }}
                </div>
                <div class="text-sm text-muted-foreground">Critical Findings</div>
              </div>
            </div>
          </div>

          <!-- Risk Assessment -->
          <div class="border rounded-lg p-6">
            <h3 class="text-lg font-semibold mb-4">Risk Assessment</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium">High Risk Items:</span>
                <span class="text-lg font-bold text-orange-600">{{ selectedTermsClausesAudit.high_risk_items }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium">Recommendations:</span>
                <span class="text-lg font-bold text-blue-600">{{ selectedTermsClausesAudit.recommendations_count }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium">Next Review Date:</span>
                <span class="text-lg font-bold text-green-600">{{ selectedTermsClausesAudit.next_review_date }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t flex justify-end">
          <button @click="showTermsClausesDetails = false" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'
import { 
  Search, Filter, Calendar, FileText, CheckCircle, AlertTriangle, 
  XCircle, Upload, Plus, Eye, Edit, Trash2, Download, Clock, 
  Shield, BarChart3, FileCheck, AlertCircle, Scale, Gavel, 
  BookOpen, Target 
} from 'lucide-vue-next'

// Reactive state
const activeTab = ref('overview')
const showCreateAudit = ref(false)
const showQuestionnaire = ref(false)
const showTermsClausesAudit = ref(false)
const showAuditDetails = ref(false)
const showTermsClausesDetails = ref(false)
const selectedAudit = ref(null)
const selectedTermsClausesAudit = ref(null)
const searchTerm = ref('')
const filterStatus = ref('all')
const filterFrequency = ref('all')
const showQuestionnaireBuilder = ref(false)
const selectedTemplate = ref('')
const customQuestions = ref([])
const newQuestion = ref('')

// Tab configuration
const tabs = [
  { value: 'overview', label: 'Overview' },
  { value: 'schedules', label: 'Audit Schedules' },
  { value: 'audits', label: 'Completed Audits' },
  { value: 'terms-clauses', label: 'Terms & Clauses' },
  { value: 'reports', label: 'Reports' }
]

// Mock data for audit schedules
const auditSchedules = ref([
  {
    id: "1",
    contract_id: "CNT-2024-001",
    contract_title: "Cloud Infrastructure Services",
    vendor_name: "TechCloud Solutions",
    frequency: "quarterly",
    next_audit_date: "2024-04-15",
    last_audit_date: "2024-01-15",
    status: "scheduled",
    assigned_auditor: "Sarah Johnson",
    compliance_score: 85
  },
  {
    id: "2",
    contract_id: "CNT-2024-002",
    contract_title: "Software Development Services",
    vendor_name: "DevCorp Inc",
    frequency: "monthly",
    next_audit_date: "2024-03-20",
    last_audit_date: "2024-02-20",
    status: "overdue",
    assigned_auditor: "Mike Chen",
    compliance_score: 72
  },
  {
    id: "3",
    contract_id: "CNT-2024-003",
    contract_title: "Consulting Services",
    vendor_name: "ConsultPro",
    frequency: "annually",
    next_audit_date: "2024-12-01",
    last_audit_date: "2023-12-01",
    status: "completed",
    assigned_auditor: "Lisa Wang",
    compliance_score: 94
  }
])

// Mock questionnaire templates
const questionnaireTemplates = ref([
  {
    id: "template-1",
    name: "SOC2 Compliance",
    category: "Security",
    questions: [
      "Does the vendor have a documented information security policy?",
      "Are security controls implemented and monitored?",
      "Is there a process for security incident response?",
      "Are access controls properly implemented?",
      "Is there regular security training for staff?"
    ],
    is_standard: true
  },
  {
    id: "template-2",
    name: "GDPR Compliance",
    category: "Privacy",
    questions: [
      "Does the vendor process personal data in compliance with GDPR?",
      "Are data subject rights properly implemented?",
      "Is there a data processing agreement in place?",
      "Are data retention policies documented and followed?",
      "Is there a process for data breach notification?"
    ],
    is_standard: true
  },
  {
    id: "template-3",
    name: "Financial Controls",
    category: "Financial",
    questions: [
      "Are financial controls properly documented?",
      "Is there segregation of duties in financial processes?",
      "Are financial reports reviewed and approved?",
      "Is there a process for expense approval?",
      "Are financial records maintained accurately?"
    ],
    is_standard: true
  },
  {
    id: "template-4",
    name: "Operational Excellence",
    category: "Operational",
    questions: [
      "Are operational procedures documented?",
      "Is there a quality management system?",
      "Are performance metrics tracked and reported?",
      "Is there a process for continuous improvement?",
      "Are staff properly trained on procedures?"
    ],
    is_standard: true
  }
])

// Mock contract audits
const contractAudits = ref([
  {
    id: "1",
    contract_id: "CNT-2024-001",
    contract_title: "Cloud Infrastructure Services",
    vendor_name: "TechCloud Solutions",
    audit_date: "2024-01-15",
    auditor: "Sarah Johnson",
    overall_compliance_score: 85,
    status: "completed",
    risk_assessment: "medium",
    findings: "Minor compliance gaps in data retention policies",
    recommendations: "Update data retention procedures and retrain staff",
    next_audit_date: "2024-04-15",
    questionnaires: [],
    evidence: []
  }
])

// Mock data for Terms and Clauses auditing
const termsClausesAuditSummaries = ref([
  {
    contract_id: "CNT-2024-001",
    contract_title: "Cloud Infrastructure Services",
    vendor_name: "TechCloud Solutions",
    audit_date: "2024-01-15",
    auditor: "Sarah Johnson",
    terms_audited: 15,
    clauses_audited: 22,
    overall_compliance_score: 87,
    critical_findings: 2,
    high_risk_items: 5,
    recommendations_count: 8,
    next_review_date: "2024-04-15"
  },
  {
    contract_id: "CNT-2024-002",
    contract_title: "Software Development Services",
    vendor_name: "DevCorp Inc",
    audit_date: "2024-02-20",
    auditor: "Mike Chen",
    terms_audited: 12,
    clauses_audited: 18,
    overall_compliance_score: 73,
    critical_findings: 4,
    high_risk_items: 8,
    recommendations_count: 12,
    next_review_date: "2024-03-20"
  },
  {
    contract_id: "CNT-2024-003",
    contract_title: "Consulting Services",
    vendor_name: "ConsultPro",
    audit_date: "2023-12-01",
    auditor: "Lisa Wang",
    terms_audited: 8,
    clauses_audited: 14,
    overall_compliance_score: 96,
    critical_findings: 0,
    high_risk_items: 1,
    recommendations_count: 3,
    next_review_date: "2024-12-01"
  }
])

// Compliance frameworks
const complianceFrameworks = ['SOC2', 'GDPR', 'ISO27001', 'PCI DSS', 'HIPAA', 'CCPA']

// Computed properties
const overdueAuditsCount = computed(() => {
  return auditSchedules.value.filter(a => a.status === 'overdue').length
})

const scheduledAuditsCount = computed(() => {
  return auditSchedules.value.filter(a => a.status === 'scheduled').length
})

const averageComplianceScore = computed(() => {
  if (auditSchedules.value.length === 0) return 0
  return Math.round(auditSchedules.value.reduce((sum, a) => sum + a.compliance_score, 0) / auditSchedules.value.length)
})

const recentAudits = computed(() => {
  return auditSchedules.value.slice(0, 5)
})

const overdueTermsAuditsCount = computed(() => {
  return termsClausesAuditSummaries.value.filter(a => new Date(a.next_review_date) < new Date()).length
})

const totalCriticalFindings = computed(() => {
  return termsClausesAuditSummaries.value.reduce((sum, a) => sum + a.critical_findings, 0)
})

const totalHighRiskItems = computed(() => {
  return termsClausesAuditSummaries.value.reduce((sum, a) => sum + a.high_risk_items, 0)
})

const averageTermsComplianceScore = computed(() => {
  if (termsClausesAuditSummaries.value.length === 0) return 0
  return Math.round(termsClausesAuditSummaries.value.reduce((sum, a) => sum + a.overall_compliance_score, 0) / termsClausesAuditSummaries.value.length)
})

const highComplianceContractsCount = computed(() => {
  return termsClausesAuditSummaries.value.filter(a => a.overall_compliance_score >= 90).length
})

const totalAuditedItems = computed(() => {
  return termsClausesAuditSummaries.value.reduce((sum, a) => sum + a.terms_audited + a.clauses_audited, 0)
})

const totalRecommendations = computed(() => {
  return termsClausesAuditSummaries.value.reduce((sum, a) => sum + a.recommendations_count, 0)
})

const selectedTemplateQuestions = computed(() => {
  const template = questionnaireTemplates.value.find(t => t.id === selectedTemplate.value)
  return template ? template.questions : []
})

const allQuestions = computed(() => {
  return [...selectedTemplateQuestions.value, ...customQuestions.value]
})

// Methods
const handleStatusFilterChange = (event) => {
  filterStatus.value = event.target.value
}

const handleFrequencyFilterChange = (event) => {
  filterFrequency.value = event.target.value
}

const addCustomQuestion = () => {
  if (newQuestion.value.trim()) {
    customQuestions.value.push(newQuestion.value.trim())
    newQuestion.value = ''
  }
}

const removeCustomQuestion = (index) => {
  customQuestions.value.splice(index, 1)
}

const handleCancel = () => {
  showCreateAudit.value = false
  selectedTemplate.value = ''
  customQuestions.value = []
  newQuestion.value = ''
}

const handleScheduleAudit = () => {
  if (allQuestions.value.length === 0) {
    PopupService.warning('Please select a template or add custom questions before scheduling the audit.', 'No Questions')
    return
  }
  showCreateAudit.value = false
  selectedTemplate.value = ''
  customQuestions.value = []
  newQuestion.value = ''
  PopupService.success(`New audit has been scheduled successfully with ${allQuestions.value.length} questions.`, 'Audit Scheduled')
}

const getStatusBadgeClass = (status) => {
  const statusConfig = {
    scheduled: 'px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full',
    in_progress: 'px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full',
    completed: 'px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full',
    overdue: 'px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full',
    draft: 'px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full',
    approved: 'px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full'
  }
  return statusConfig[status] || statusConfig.draft
}

const getStatusText = (status) => {
  return status.replace('_', ' ').toUpperCase()
}

const getRiskBadgeClass = (risk) => {
  const riskConfig = {
    low: 'px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full',
    medium: 'px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full',
    high: 'px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full',
    critical: 'px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full'
  }
  return riskConfig[risk] || riskConfig.low
}

const getComplianceScoreColor = (score) => {
  if (score >= 90) return 'text-green-600'
  if (score >= 75) return 'text-yellow-600'
  if (score >= 60) return 'text-orange-600'
  return 'text-red-600'
}

// View audit details
const viewAuditDetails = (audit) => {
  selectedAudit.value = audit
  showAuditDetails.value = true
}

// View terms & clauses details
const viewTermsClausesDetails = (auditSummary) => {
  selectedTermsClausesAudit.value = auditSummary
  showTermsClausesDetails.value = true
}

// Close dialog when clicking outside
const closeDialog = (event) => {
  if (event.target === event.currentTarget) {
    showCreateAudit.value = false
  }
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Audit Trail')
})
</script>
