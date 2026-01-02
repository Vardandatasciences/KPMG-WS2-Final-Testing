<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">SLA Performance Dashboard</h1>
        <p class="text-muted-foreground">
          Real-time SLA compliance tracking based on audit data vs. contractual metrics
        </p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-muted-foreground">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else>
      <!-- Filters Section -->
      <Card class="mb-6">
        <CardContent class="p-4">
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label class="text-sm font-medium mb-2 block">Filter by SLA</label>
              <select 
                v-model="filters.sla_id" 
                @change="loadDashboardData"
                class="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All SLAs</option>
                <option v-for="sla in availableSLAs" :key="sla.sla_id" :value="sla.sla_id">
                  {{ sla.sla_name }}
                </option>
              </select>
            </div>
            <div>
              <label class="text-sm font-medium mb-2 block">Filter by Vendor</label>
              <select 
                v-model="filters.vendor_id" 
                @change="loadDashboardData"
                class="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Vendors</option>
                <option v-for="vendor in availableVendors" :key="vendor.vendor_id" :value="vendor.vendor_id">
                  {{ vendor.company_name }}
                </option>
              </select>
            </div>
            <div>
              <label class="text-sm font-medium mb-2 block">Filter by Contract</label>
              <select 
                v-model="filters.contract_id" 
                @change="loadDashboardData"
                class="w-full px-3 py-2 border rounded-md"
              >
                <option value="">All Contracts</option>
                <option v-for="contract in availableContracts" :key="contract.contract_id" :value="contract.contract_id">
                  {{ contract.contract_name }}
                </option>
              </select>
            </div>
            <div>
              <label class="text-sm font-medium mb-2 block">Period</label>
              <select 
                v-model="selectedPeriod" 
                class="w-full px-3 py-2 border rounded-md"
              >
                <option v-for="period in auditPeriods" :key="period.value" :value="period.value">
                  {{ period.label }}
                </option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Audit Period Info -->
      <div class="flex items-center gap-4 p-4 bg-gray-50 rounded-lg mb-6">
        <span class="text-sm font-medium">Viewing: {{ selectedPeriod.toUpperCase() }} Data</span>
      <div class="ml-auto text-sm text-muted-foreground">
        Last Audit: {{ lastAuditDate }}
      </div>
    </div>

    <!-- KPI Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">SLA Compliance Rate</p>
              <p class="text-2xl font-bold" :class="getComplianceColor(overallCompliance)">
                {{ overallCompliance }}%
              </p>
              <p class="text-xs" :class="getTrendColor(complianceTrend)">
                {{ complianceTrend > 0 ? '↗' : '↘' }} {{ Math.abs(complianceTrend) }}% vs last {{ selectedPeriod }}
              </p>
            </div>
            <CheckCircle class="h-8 w-8" :class="getComplianceColor(overallCompliance)" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Metrics in Breach</p>
              <p class="text-2xl font-bold text-red-600">{{ metricsInBreach }}</p>
              <p class="text-xs text-red-600">Out of {{ totalMetrics }} total metrics</p>
            </div>
            <AlertTriangle class="h-8 w-8 text-red-600" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Avg Performance Gap</p>
              <p class="text-2xl font-bold text-orange-600">{{ avgPerformanceGap }}%</p>
              <p class="text-xs text-orange-600">Below SLA targets</p>
            </div>
            <TrendingDown class="h-8 w-8 text-orange-600" />
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Vendors at Risk</p>
              <p class="text-2xl font-bold text-yellow-600">{{ vendorsAtRisk }}</p>
              <p class="text-xs text-yellow-600">Require attention</p>
            </div>
            <Users class="h-8 w-8 text-yellow-600" />
          </div>
        </CardContent>
      </Card>
    </div>

    <div class="space-y-6">
      <!-- SLA Analytics Tab Navigation -->
      <div class="grid w-full grid-cols-3 border-b">
        <button 
          @click="activeTab = 'overview'"
          :class="activeTab === 'overview' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'"
          class="px-4 py-2 text-sm font-medium"
        >
          SLA Overview
        </button>
        <button 
          @click="activeTab = 'metrics'"
          :class="activeTab === 'metrics' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'"
          class="px-4 py-2 text-sm font-medium"
        >
          Metrics Analysis
        </button>
        <button 
          @click="activeTab = 'breaches'"
          :class="activeTab === 'breaches' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'"
          class="px-4 py-2 text-sm font-medium"
        >
          SLA Breaches
        </button>
      </div>

      <div v-if="activeTab === 'overview'" class="space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>SLA Compliance Trends ({{ selectedPeriod }})</CardTitle>
            </CardHeader>
            <CardContent>
              <!-- Trend Summary -->
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div class="p-3 rounded-lg bg-gray-50">
                  <p class="text-xs text-muted-foreground">Current</p>
                  <p class="text-xl font-bold" :class="getComplianceColor(trendStats.current)">{{ trendStats.current }}%</p>
                </div>
                <div class="p-3 rounded-lg bg-gray-50">
                  <p class="text-xs text-muted-foreground">Change vs previous</p>
                  <p class="text-xl font-bold" :class="trendStats.delta >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ trendStats.delta >= 0 ? '↗' : '↘' }} {{ Math.abs(trendStats.delta) }}%
                  </p>
                </div>
                <div class="p-3 rounded-lg bg-gray-50">
                  <p class="text-xs text-muted-foreground">Average</p>
                  <p class="text-xl font-bold" :class="getComplianceColor(trendStats.average)">{{ trendStats.average }}%</p>
                </div>
                
              </div>

              <!-- SLA Compliance Bar Chart -->
              <div class="h-[320px] relative px-4 py-6">
                <!-- Target Line (95%) -->
                <div class="absolute left-4 right-4 border-t-2 border-dashed border-blue-400" :style="{ top: `${chartY(95)}px` }"></div>
                <div class="absolute right-2 text-xs font-semibold text-blue-600" :style="{ top: `${chartY(95) - 10}px` }">Target 95%</div>

                <div class="h-full flex items-end justify-between">
                  <div v-if="auditHistory.length === 0" class="flex items-center justify-center w-full">
                    <p class="text-muted-foreground">No audit history available</p>
                  </div>
                  <div v-for="(audit, index) in auditHistory" :key="index" class="flex flex-col items-center justify-end h-full">
                    <!-- Compliance Bar with value label -->
                    <div class="flex flex-col justify-end w-12 h-64 mb-2 relative group">
                      <div 
                        class="w-full rounded-t-sm transition-all" 
                        :class="getComplianceBarColor(audit.compliance_rate)"
                        :style="{ height: `${(audit.compliance_rate / 100) * 200}px` }"
                        :title="`Compliance: ${audit.compliance_rate}% (Target: 95%) on ${audit.audit_date}`"
                      ></div>
                      <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-semibold" :class="getComplianceColor(audit.compliance_rate)">{{ Math.round(audit.compliance_rate) }}%</div>
                  </div>
                  <!-- Period Label -->
                  <span class="text-xs text-muted-foreground font-medium">{{ audit.period }}</span>
                  </div>
                </div>
              </div>
              <!-- Legend -->
              <div class="flex justify-center space-x-6 mt-4 pt-4 border-t">
                <div class="flex items-center">
                  <div class="w-3 h-3 bg-green-500 rounded-sm mr-2"></div>
                  <span class="text-sm text-muted-foreground">Compliant (≥95%)</span>
                </div>
                <div class="flex items-center">
                  <div class="w-3 h-3 bg-yellow-500 rounded-sm mr-2"></div>
                  <span class="text-sm text-muted-foreground">At Risk (90-94%)</span>
                </div>
                <div class="flex items-center">
                  <div class="w-3 h-3 bg-red-500 rounded-sm mr-2"></div>
                  <span class="text-sm text-muted-foreground">Breach (<90%)</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Metrics Performance Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <!-- Metrics Performance Chart (data-driven conic gradient) -->
              <div class="h-[300px] flex items-center justify-center">
                <div class="relative w-48 h-48">
                  <div 
                    class="absolute inset-0 rounded-full"
                    :style="donutStyle"
                  ></div>
                  <div class="absolute inset-4 bg-white rounded-full flex flex-col items-center justify-center">
                    <span class="text-lg font-bold">{{ totalMetricsDisplay }}</span>
                    <span class="text-xs text-muted-foreground">metrics</span>
                  </div>
                </div>
              </div>
              <div class="flex justify-center mt-4 space-x-6">
                <div class="flex items-center" v-for="leg in metricsLegend" :key="leg.name">
                  <span class="w-3 h-3 rounded-full mr-2" :style="{ backgroundColor: leg.color }"></span>
                  <span class="text-sm">
                    {{ leg.name }}: {{ leg.value }} ({{ leg.percent }}%)
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Metrics Performance Comparison -->
        <Card v-if="slaMetrics.length > 0">
          <CardHeader>
            <CardTitle>All Metrics Target vs Actual Comparison</CardTitle>
            <p class="text-sm text-muted-foreground">Quick comparison of all metrics performance</p>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div v-for="(metric, index) in slaMetrics.slice(0, 6)" :key="index" class="border rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                  <div class="flex-1">
                    <h4 class="font-semibold text-sm">{{ metric.name }}</h4>
                    <p class="text-xs text-muted-foreground">{{ metric.vendor }}</p>
                  </div>
                  <Badge :class="getMetricStatusBadgeClass(metric.status)" class="text-xs">
                    {{ metric.status }}
                  </Badge>
                </div>
                
                <div class="space-y-2">
                  <!-- Target Bar -->
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-medium text-blue-600 w-16">Target:</span>
                    <div class="flex-1 h-6 bg-blue-100 rounded-lg relative overflow-hidden">
                      <div class="absolute inset-0 bg-blue-500 flex items-center px-2">
                        <span class="text-xs font-bold text-white">{{ metric.sla_target }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Actual Bar -->
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-medium w-16" :class="getPerformanceTextColor(metric.status)">Actual:</span>
                    <div class="flex-1 h-6 bg-gray-200 rounded-lg relative overflow-hidden">
                      <div 
                        class="absolute inset-y-0 left-0 flex items-center px-2 transition-all duration-500"
                        :class="getPerformanceBarClass(metric.status)"
                        :style="{ width: `${Math.min(metric.performance_percentage, 100)}%` }"
                      >
                        <span class="text-xs font-bold text-white">{{ metric.actual_value }}</span>
                      </div>
                    </div>
                    <span class="text-xs font-bold w-12 text-right" :class="getComplianceColor(metric.performance_percentage)">
                      {{ Math.round(metric.performance_percentage) }}%
                    </span>
                  </div>
                </div>
              </div>
              
              <div v-if="slaMetrics.length > 6" class="text-center">
                <button 
                  @click="activeTab = 'metrics'"
                  class="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  View all {{ slaMetrics.length }} metrics →
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- SLA Documents Summary -->
        <Card>
          <CardHeader>
            <CardTitle>Active SLA Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div v-if="activeSLAs.length === 0" class="text-center py-8">
              <p class="text-muted-foreground">No active SLAs found</p>
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div v-for="sla in activeSLAs" :key="sla.id" class="border-2 rounded-lg p-4 hover:shadow-md transition-shadow" :class="getSLABorderClass(sla.status)">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="font-semibold text-lg">{{ sla.vendor }}</h3>
                  <Badge :class="getSLAStatusBadgeClass(sla.status)" class="text-xs px-2 py-1">
                    {{ sla.status }}
                  </Badge>
                </div>
                <p class="text-sm text-muted-foreground mb-3 font-medium">{{ sla.service_type }}</p>
                
                <!-- Compliance Score Visualization -->
                <div class="mb-3 p-3 bg-gray-50 rounded-lg">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-xs text-muted-foreground">Compliance Score</span>
                    <span class="text-lg font-bold" :class="getComplianceColor(sla.compliance_rate)">
                      {{ sla.compliance_rate }}%
                    </span>
                  </div>
                  <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      class="h-full rounded-full transition-all duration-500"
                      :class="getProgressBarColor(sla.compliance_rate)"
                      :style="{ width: `${sla.compliance_rate}%` }"
                    ></div>
                  </div>
                </div>
                
                <div class="space-y-2">
                  <div class="flex justify-between text-sm">
                    <span class="text-muted-foreground">Metrics:</span>
                    <span class="font-semibold">{{ sla.metrics_count }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-muted-foreground">Next Audit:</span>
                    <span class="font-semibold">{{ sla.next_audit }}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div v-if="activeTab === 'metrics'" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>SLA Metrics Performance Analysis</CardTitle>
            <p class="text-sm text-muted-foreground">Detailed breakdown of each SLA metric vs. audit results with target comparison</p>
          </CardHeader>
          <CardContent>
            <div v-if="slaMetrics.length === 0" class="text-center py-8">
              <p class="text-muted-foreground">No metrics data available</p>
            </div>
            <div v-else class="space-y-6">
              <div v-for="metric in slaMetrics" :key="metric.id" class="border-2 rounded-lg p-6 hover:shadow-lg transition-shadow" :class="getMetricBorderClass(metric.status)">
                <!-- Header Section -->
                <div class="flex items-center justify-between mb-4">
                  <div class="flex-1">
                    <div class="flex items-center gap-3">
                      <h3 class="text-xl font-bold">{{ metric.name }}</h3>
                      <Badge :class="getMetricStatusBadgeClass(metric.status)" class="text-sm px-3 py-1">
                        {{ metric.status }}
                      </Badge>
                    </div>
                    <p class="text-sm text-muted-foreground mt-1">{{ metric.description }}</p>
                    <div class="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span>Vendor: <span class="font-semibold text-gray-700">{{ metric.vendor }}</span></span>
                      <span>|</span>
                      <span>SLA: <span class="font-semibold text-gray-700">{{ metric.sla_name }}</span></span>
                      <span>|</span>
                      <span>Checked: <span class="font-semibold text-gray-700">{{ metric.check_date }}</span></span>
                    </div>
                  </div>
                  <div class="text-center px-6 py-3 bg-gray-50 rounded-lg">
                    <p class="text-xs text-muted-foreground">Compliance Score</p>
                    <p class="text-3xl font-bold" :class="getComplianceColor(metric.performance_percentage)">
                      {{ Math.round(metric.performance_percentage) }}%
                    </p>
                  </div>
                </div>

                <!-- Target vs Actual Bar Graph -->
                <div class="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 class="text-sm font-semibold mb-4">Target vs Actual Performance</h4>
                  <div class="space-y-3">
                    <!-- Target Bar -->
                    <div>
                      <div class="flex justify-between text-sm mb-1">
                        <span class="font-medium text-blue-700">SLA Target</span>
                        <span class="font-bold text-blue-700">{{ metric.sla_target }}</span>
                      </div>
                      <div class="relative h-8 bg-blue-100 rounded-lg overflow-hidden">
                        <div class="absolute inset-0 bg-blue-500 rounded-lg flex items-center justify-center">
                          <span class="text-xs font-bold text-white">TARGET: {{ metric.sla_target }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Actual Bar -->
                    <div>
                      <div class="flex justify-between text-sm mb-1">
                        <span class="font-medium" :class="getPerformanceTextColor(metric.status)">Actual Performance</span>
                        <span class="font-bold" :class="getPerformanceTextColor(metric.status)">{{ metric.actual_value }}</span>
                      </div>
                      <div class="relative h-8 bg-gray-200 rounded-lg overflow-hidden">
                        <div 
                          class="absolute inset-y-0 left-0 rounded-lg flex items-center justify-center transition-all duration-500"
                          :class="getPerformanceBarClass(metric.status)"
                          :style="{ width: `${Math.min(metric.performance_percentage, 100)}%` }"
                        >
                          <span class="text-xs font-bold text-white whitespace-nowrap">ACTUAL: {{ metric.actual_value }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Detailed Metrics Grid -->
                <div class="grid grid-cols-4 gap-4 mt-6">
                  <div class="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p class="text-xs text-blue-600 font-medium mb-1">SLA Target</p>
                    <p class="text-lg font-bold text-blue-700">{{ metric.sla_target }}</p>
                    <p class="text-xs text-blue-500 mt-1">Required</p>
                  </div>
                  
                  <div class="text-center p-3 rounded-lg border" :class="getMetricCardClass(metric.status)">
                    <p class="text-xs font-medium mb-1">Actual Value</p>
                    <p class="text-lg font-bold">{{ metric.actual_value }}</p>
                    <p class="text-xs mt-1">Achieved</p>
                  </div>
                  
                  <div class="text-center p-3 rounded-lg border" :class="getGapCardClass(metric.gap)">
                    <p class="text-xs font-medium mb-1">Gap/Variance</p>
                    <p class="text-lg font-bold">
                      {{ metric.gap > 0 ? '+' : '' }}{{ metric.gap }}{{ metric.unit }}
                    </p>
                    <p class="text-xs mt-1">{{ metric.gap <= 0 ? 'Within Target' : 'Exceeds Target' }}</p>
                  </div>
                  
                  <div class="text-center p-3 rounded-lg border" :class="getComplianceCardClass(metric.performance_percentage)">
                    <p class="text-xs font-medium mb-1">Compliance</p>
                    <p class="text-lg font-bold">{{ Math.round(metric.performance_percentage) }}%</p>
                    <p class="text-xs mt-1">{{ getComplianceLabel(metric.performance_percentage) }}</p>
                  </div>
                </div>

                <!-- Performance Indicator -->
                <div class="mt-4">
                  <div class="flex justify-between items-center text-sm mb-2">
                    <span class="font-medium">Overall Performance Score</span>
                    <span class="font-bold" :class="getComplianceColor(metric.performance_percentage)">
                      {{ Math.round(metric.performance_percentage) }}% of Target
                    </span>
                  </div>
                  <div class="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                    <!-- Target line at 100% -->
                    <div class="absolute left-full transform -translate-x-full h-full w-1 bg-blue-600 z-10" style="left: 100%">
                      <div class="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-bold text-blue-600 whitespace-nowrap">
                        Target
                      </div>
                    </div>
                    <!-- Actual performance bar -->
                    <div 
                      class="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-700" 
                      :class="getProgressBarColor(metric.performance_percentage)"
                      :style="{ width: `${Math.min(metric.performance_percentage, 100)}%` }"
                    >
                      <span class="text-xs font-bold text-white">{{ Math.round(metric.performance_percentage) }}%</span>
                    </div>
                  </div>
                  <div class="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>0%</span>
                    <span>50%</span>
                    <span class="font-bold text-blue-600">100% (Target)</span>
                  </div>
                </div>

                <!-- Status Message -->
                <div class="mt-4 p-3 rounded-lg" :class="getStatusMessageClass(metric.status)">
                  <p class="text-sm font-medium">
                    <span v-if="metric.status === 'Compliant'">✓ Excellent! This metric is meeting SLA requirements.</span>
                    <span v-else-if="metric.status === 'At Risk'">⚠ Warning: This metric is close to breaching SLA thresholds.</span>
                    <span v-else>✗ Alert: This metric is in breach of SLA requirements and requires immediate attention.</span>
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>


      <div v-if="activeTab === 'breaches'" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>SLA Breaches & Violations</CardTitle>
            <p class="text-sm text-muted-foreground">Current and historical SLA breaches requiring attention</p>
          </CardHeader>
          <CardContent>
            <div v-if="slaBreaches.length === 0" class="text-center py-8">
              <p class="text-muted-foreground">No breaches found</p>
            </div>
            <div v-else class="space-y-4">
              <div v-for="breach in slaBreaches" :key="breach.id" class="border rounded-lg p-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-4">
                    <div>
                      <h3 class="font-medium">{{ breach.vendor }} - {{ breach.metric }}</h3>
                      <p class="text-sm text-muted-foreground">
                        SLA Target: {{ breach.sla_target }} | Actual: {{ breach.actual_value }} | Gap: {{ breach.gap }}
                      </p>
                      <p class="text-xs text-muted-foreground">
                        Breach Duration: {{ breach.duration }} | Detected: {{ breach.detected_at }}
                      </p>
                      <p class="text-xs text-muted-foreground" v-if="breach.impact">
                        Business Impact: {{ breach.impact }}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <Badge :class="getBreachSeverityBadgeClass(breach.severity)">
                      {{ breach.severity }}
                    </Badge>
                    <Badge :class="getBreachStatusBadgeClass(breach.status)">
                      {{ breach.status }}
                    </Badge>
                  </div>
                </div>
                <div v-if="breach.remediation" class="mt-3 p-3 bg-yellow-50 rounded-lg">
                  <p class="text-sm font-medium text-yellow-800">Remediation Plan:</p>
                  <p class="text-sm text-yellow-700">{{ breach.remediation }}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Breach Statistics -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-muted-foreground">Active Breaches</p>
                  <p class="text-2xl font-bold text-red-600">{{ activeBreaches }}</p>
                </div>
                <AlertTriangle class="h-8 w-8 text-red-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-muted-foreground">Resolved This Month</p>
                  <p class="text-2xl font-bold text-green-600">{{ resolvedBreaches }}</p>
                </div>
                <CheckCircle class="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-medium text-muted-foreground">Avg Resolution Time</p>
                  <p class="text-2xl font-bold text-blue-600">{{ avgResolutionTime }}</p>
                </div>
                <Clock class="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
        </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Activity,
  TrendingDown,
  Users
} from 'lucide-vue-next'
import apiService from '@/services/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const router = useRouter()
const activeTab = ref('overview')
const selectedPeriod = ref('monthly')
const loading = ref(false)
const dashboardData = ref(null)

// Filter state
const filters = ref({
  sla_id: '',
  vendor_id: '',
  contract_id: ''
})

// Filter options
const availableSLAs = ref([])
const availableVendors = ref([])
const availableContracts = ref([])

// Audit periods configuration
const auditPeriods = ref([
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Quarterly', value: 'quarterly' },
  { label: 'Yearly', value: 'yearly' }
])

// Load filter options
const loadFilterOptions = async () => {
  try {
    // Load available SLAs
    const slasResponse = await apiService.getSLAs()
    availableSLAs.value = slasResponse.results || slasResponse || []
    
    // Load available vendors
    const vendorsResponse = await apiService.getVendors()
    availableVendors.value = vendorsResponse.results || vendorsResponse || []
    
    // Load available contracts
    const contractsResponse = await apiService.getContracts()
    availableContracts.value = contractsResponse.results || contractsResponse || []
  } catch (error) {
    console.error('Error loading filter options:', error)
    PopupService.error('Error loading filter options. Some filters may not be available.', 'Loading Error')
  }
}

// Load dashboard data from backend
const loadDashboardData = async () => {
  loading.value = true
  try {
    const params = { 
      period: selectedPeriod.value,
      ...(filters.value.sla_id && { sla_id: filters.value.sla_id }),
      ...(filters.value.vendor_id && { vendor_id: filters.value.vendor_id }),
      ...(filters.value.contract_id && { contract_id: filters.value.contract_id })
    }
    const data = await apiService.getPerformanceDashboard(params)
    dashboardData.value = data
    console.log('Dashboard data loaded:', data)
  } catch (error) {
    console.error('Error loading dashboard data:', error)
    PopupService.error('Error loading dashboard data. Please try again later.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

// Watch for period changes
watch(selectedPeriod, () => {
  loadDashboardData()
})

// Load data on mount
onMounted(async () => {
  await loggingService.logPerformanceView()
  await loadFilterOptions()
  await loadDashboardData()
})

// Computed values for KPI cards - use backend data or defaults
const overallCompliance = computed(() => dashboardData.value?.overview?.overall_compliance || 0)
const complianceTrend = computed(() => dashboardData.value?.overview?.compliance_trend || 0)
const metricsInBreach = computed(() => dashboardData.value?.overview?.metrics_in_breach || 0)
const totalMetrics = computed(() => dashboardData.value?.overview?.total_metrics || 0)
const avgPerformanceGap = computed(() => dashboardData.value?.overview?.avg_performance_gap || 0)
const vendorsAtRisk = computed(() => dashboardData.value?.overview?.vendors_at_risk || 0)
const lastAuditDate = computed(() => dashboardData.value?.overview?.last_audit_date || 'N/A')

// Computed values from backend data
const auditHistory = computed(() => dashboardData.value?.audit_history || [])

// Trend stats for the chart header
const trendStats = computed(() => {
  const points = auditHistory.value || []
  if (!points.length) return { current: 0, delta: 0, average: 0, best: { value: 0 }, worst: { value: 0 } }
  const nums = points.map(p => Number(p.compliance_rate || 0))
  const current = Math.round(nums[0] || 0)
  const prev = Math.round(nums[1] || 0)
  const avg = Math.round(nums.reduce((s, n) => s + (isNaN(n) ? 0 : n), 0) / nums.length)
  const bestVal = Math.max(...nums)
  const worstVal = Math.min(...nums)
  return {
    current,
    delta: current - (prev || 0),
    average: avg,
    best: { value: Math.round(bestVal) },
    worst: { value: Math.round(worstVal) }
  }
})

// Y-axis position helper for 0..100 range area (64px bar height mapped to 200px area)
const chartY = (percent) => {
  // Chart area starts at top padding; bars are 200px max height inside a 64px col container. We map 0..100 to 200px inside container.
  const h = 200
  const topOffset = 24 // slight icon text offset
  const clamped = Math.max(0, Math.min(100, percent))
  return topOffset + (h - (clamped / 100) * h)
}

const metricsDistribution = computed(() => {
  const dist = dashboardData.value?.metrics_distribution
  if (!dist) return []
  
  return [
    { name: "Compliant", value: dist.compliant || 0, color: "#22c55e" },
    { name: "At Risk", value: dist.at_risk || 0, color: "#f59e0b" },
    { name: "Breach", value: dist.breach || 0, color: "#ef4444" }
  ]
})

// Donut chart helpers
const totalMetricsDisplay = computed(() => {
  return metricsDistribution.value.reduce((s, i) => s + (i.value || 0), 0)
})

const metricsLegend = computed(() => {
  const total = totalMetricsDisplay.value || 1
  return metricsDistribution.value.map(i => ({
    ...i,
    percent: Math.round(((i.value || 0) / total) * 100)
  }))
})

const donutStyle = computed(() => {
  const items = metricsDistribution.value
  const total = totalMetricsDisplay.value || 1
  // Build conic-gradient stops based on percentages
  let current = 0
  const stops = items.map(i => {
    const pct = ((i.value || 0) / total) * 100
    const start = current
    const end = current + pct
    current = end
    return `${i.color} ${start}% ${end}%`
  })
  // Fallback when no data
  const gradient = stops.length ? `conic-gradient(${stops.join(', ')})` : 'conic-gradient(#e5e7eb 0% 100%)'
  return { background: gradient }
})

const activeSLAs = computed(() => {
  return dashboardData.value?.active_slas || []
})

const slaMetrics = computed(() => {
  return dashboardData.value?.metrics_analysis || []
})

const slaBreaches = computed(() => {
  return dashboardData.value?.breaches || []
})

// Breach statistics
const activeBreaches = computed(() => dashboardData.value?.breach_stats?.active_breaches || 0)
const resolvedBreaches = computed(() => dashboardData.value?.breach_stats?.resolved_breaches || 0)
const avgResolutionTime = computed(() => dashboardData.value?.breach_stats?.avg_resolution_time || 'N/A')


const navigateTo = (path) => {
  router.push(path)
}


// Color helper functions
const getComplianceColor = (compliance) => {
  if (compliance >= 95) return 'text-green-600'
  if (compliance >= 90) return 'text-yellow-600'
  return 'text-red-600'
}

const getTrendColor = (trend) => {
  return trend > 0 ? 'text-green-600' : 'text-red-600'
}

const getComplianceBarColor = (compliance) => {
  if (compliance >= 95) return 'bg-green-500'
  if (compliance >= 90) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getProgressBarColor = (percentage) => {
  if (percentage >= 100) return 'bg-green-500'
  if (percentage >= 90) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getPerformanceColor = (actual, target) => {
  // Simple comparison - in real app, you'd parse the values properly
  const actualNum = parseFloat(actual)
  const targetNum = parseFloat(target)
  if (actualNum <= targetNum) return 'text-green-600'
  if (actualNum <= targetNum * 1.1) return 'text-yellow-600'
  return 'text-red-600'
}

const getGapColor = (gap) => {
  if (gap <= 0) return 'text-green-600'
  if (gap <= 5) return 'text-yellow-600'
  return 'text-red-600'
}

// Badge helper functions
const getSLAStatusBadgeClass = (status) => {
  switch (status) {
    case "Active":
      return "bg-green-100 text-green-800"
    case "At Risk":
      return "bg-yellow-100 text-yellow-800"
    case "Breach":
      return "bg-red-100 text-red-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}

const getSLABorderClass = (status) => {
  switch (status) {
    case "Active":
      return "border-green-300"
    case "At Risk":
      return "border-yellow-300"
    case "Breach":
      return "border-red-300"
    default:
      return "border-gray-300"
  }
}

const getMetricStatusBadgeClass = (status) => {
  switch (status) {
    case "Compliant":
      return "bg-green-100 text-green-800"
    case "At Risk":
      return "bg-yellow-100 text-yellow-800"
    case "Breach":
      return "bg-red-100 text-red-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}


const getBreachSeverityBadgeClass = (severity) => {
  switch (severity) {
    case "High":
      return "bg-red-100 text-red-800"
    case "Medium":
      return "bg-yellow-100 text-yellow-800"
    case "Low":
      return "bg-blue-100 text-blue-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}

const getBreachStatusBadgeClass = (status) => {
  return status === "Active" 
    ? "bg-red-100 text-red-800"
    : "bg-green-100 text-green-800"
}

// Enhanced helper functions for metrics visualization
const getMetricBorderClass = (status) => {
  switch (status) {
    case "Compliant":
      return "border-green-300"
    case "At Risk":
      return "border-yellow-300"
    case "Breach":
      return "border-red-300"
    default:
      return "border-gray-300"
  }
}

const getPerformanceTextColor = (status) => {
  switch (status) {
    case "Compliant":
      return "text-green-700"
    case "At Risk":
      return "text-yellow-700"
    case "Breach":
      return "text-red-700"
    default:
      return "text-gray-700"
  }
}

const getPerformanceBarClass = (status) => {
  switch (status) {
    case "Compliant":
      return "bg-green-500"
    case "At Risk":
      return "bg-yellow-500"
    case "Breach":
      return "bg-red-500"
    default:
      return "bg-gray-500"
  }
}

const getMetricCardClass = (status) => {
  switch (status) {
    case "Compliant":
      return "bg-green-50 border-green-200 text-green-700"
    case "At Risk":
      return "bg-yellow-50 border-yellow-200 text-yellow-700"
    case "Breach":
      return "bg-red-50 border-red-200 text-red-700"
    default:
      return "bg-gray-50 border-gray-200 text-gray-700"
  }
}

const getGapCardClass = (gap) => {
  if (gap <= 0) return "bg-green-50 border-green-200 text-green-700"
  if (gap <= 5) return "bg-yellow-50 border-yellow-200 text-yellow-700"
  return "bg-red-50 border-red-200 text-red-700"
}

const getComplianceCardClass = (percentage) => {
  if (percentage >= 100) return "bg-green-50 border-green-200 text-green-700"
  if (percentage >= 95) return "bg-yellow-50 border-yellow-200 text-yellow-700"
  return "bg-red-50 border-red-200 text-red-700"
}

const getComplianceLabel = (percentage) => {
  if (percentage >= 100) return "Excellent"
  if (percentage >= 95) return "Good"
  if (percentage >= 90) return "At Risk"
  return "Breach"
}

const getStatusMessageClass = (status) => {
  switch (status) {
    case "Compliant":
      return "bg-green-50 border border-green-200 text-green-800"
    case "At Risk":
      return "bg-yellow-50 border border-yellow-200 text-yellow-800"
    case "Breach":
      return "bg-red-50 border border-red-200 text-red-800"
    default:
      return "bg-gray-50 border border-gray-200 text-gray-800"
  }
}
</script>
