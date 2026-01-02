<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
    <!-- Header Section -->
    <div class="bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-6 py-8">
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h1 class="text-4xl font-bold text-gray-900 mb-2">RFP Analytics Dashboard</h1>
            <p class="text-lg text-gray-600">Monitor performance, track bottlenecks, and measure cost savings</p>
          </div>
          <div class="flex items-center gap-4">
            <div class="text-sm text-gray-500 bg-gray-50 px-3 py-2 rounded-lg">
              Last updated: <span class="font-medium text-gray-700">Jan 16, 2025</span>
            </div>
            <button 
              @click="exportReport" 
              :disabled="exportLoading"
              :class="[
                'text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
                exportLoading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700'
              ]"
            >
              <svg v-if="exportLoading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ exportLoading ? 'Exporting...' : 'Export Report' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-6 py-8 space-y-8">

      <!-- Performance Overview Section -->
      <div class="space-y-6">
        <div class="flex items-center gap-3">
          <div class="w-1 h-8 bg-blue-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">Performance Overview</h2>
        </div>
        
        <!-- Summary KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div v-for="(kpi, index) in summaryKPIs" :key="index" class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-semibold text-gray-600 uppercase tracking-wide">{{ kpi.title }}</h3>
              <div class="relative group">
                <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {{ kpi.tooltip }}
                </div>
              </div>
            </div>
            <div class="space-y-2">
              <div class="flex items-baseline space-x-2">
                <div class="text-3xl font-bold text-gray-900">{{ kpi.value }}</div>
                <span v-if="kpi.subtext" class="text-sm text-gray-500 font-medium">{{ kpi.subtext }}</span>
              </div>
              <div class="flex items-center space-x-1 text-sm font-medium" :class="getTrendClass(kpi.trend)">
                <TrendingUp v-if="kpi.trend === 'up'" class="h-4 w-4" />
                <TrendingUp v-else-if="kpi.trend === 'down'" class="h-4 w-4 transform rotate-180" />
                <span>{{ kpi.change }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RFP Lifecycle Section -->
      <div class="space-y-6">
        <div class="flex items-center gap-3">
          <div class="w-1 h-8 bg-green-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">RFP Lifecycle Analytics</h2>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- RFP Creation Rate -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <h3 class="text-lg font-semibold text-gray-900">RFP Creation Rate</h3>
                  <div class="relative group">
                    <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                      Monthly RFP creation trend
                    </div>
                  </div>
                </div>
                <!-- Timeline Selector -->
                <div class="flex items-center gap-2">
                  <button
                    v-for="option in timelineOptions"
                    :key="option.value"
                    @click="changeTimeline(option.value)"
                    :class="[
                      'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                      selectedTimeline === option.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    ]"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>
            </div>
            <div class="p-6">
              <LineChart :data="rfpCreationData" :timeline="selectedTimeline" />
            </div>
          </div>

          <!-- RFP Approval Time -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <h3 class="text-lg font-semibold text-gray-900">RFP Approval Time</h3>
                  <div class="relative group">
                    <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                      Time taken for RFPs to be approved (in days)
                    </div>
                  </div>
                </div>
                <!-- Timeline Selector -->
                <div class="flex items-center gap-2">
                  <button
                    v-for="option in timelineOptions"
                    :key="option.value"
                    @click="changeApprovalTimeline(option.value)"
                    :class="[
                      'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                      selectedApprovalTimeline === option.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    ]"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>
            </div>
            <div class="p-6">
              <BarChart :data="approvalTimeData" />
            </div>
          </div>

          <!-- First-Time Approval Rate -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-semibold text-gray-900">First-Time Approval Rate</h3>
                  <p class="text-sm text-gray-500 mt-1">Approved without revisions</p>
                </div>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Percentage of RFPs approved on first submission (version 1)
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="firstTimeApprovalRate === 0" class="flex flex-col items-center justify-center h-[240px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">First-time approval rate will appear here once available.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: This requires the approval_request_versions table with approval data.</p>
                </div>
              </div>
              <DonutChart v-else :value="firstTimeApprovalRate" />
            </div>
          </div>

          <!-- Approval Stage Performance -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Approval Stage Performance</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Breakdown of delay at each approval step
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="approvalStageData.length === 0 || (approvalStageData.length > 0 && approvalStageData[0].value === 0)" class="flex flex-col items-center justify-center h-[260px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Approval stage performance data will appear here once available.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: This requires the approval_stages table with completed approval data.</p>
                </div>
              </div>
              <BarChart v-else :data="approvalStageData" />
            </div>
          </div>
        </div>
      </div>

      <!-- End-to-End RFP Cycle Time -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">End-to-End RFP Cycle Time</h3>
            <div class="relative group">
              <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
              <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                Track the lifecycle from start to finish
              </div>
            </div>
          </div>
        </div>
        <div class="p-6">
          <div v-if="ganttData.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
            <div class="text-center">
              <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 class="mt-2 text-sm font-medium text-gray-900">No Lifecycle Data Available</h3>
              <p class="mt-1 text-sm text-gray-500">Lifecycle time data will appear here once RFPs are awarded.</p>
              <p class="mt-2 text-xs text-gray-400">Note: Requires RFPs with AWARDED status and award decision dates.</p>
            </div>
          </div>
          
          <div v-else class="space-y-6">
            <div class="text-center">
              <h4 class="text-sm font-medium text-gray-600 mb-2">Gantt Chart Visualization</h4>
              <p class="text-xs text-gray-500">Average time spent in each phase</p>
            </div>
            <div class="space-y-4">
              <div v-for="(item, index) in ganttData" :key="index" class="flex items-center space-x-6">
                <div class="w-24 text-sm font-medium text-gray-700 text-right">{{ item.phase }}</div>
                <div class="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div 
                    class="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500"
                    :style="{ width: `${item.duration}%` }"
                  />
                </div>
                <div class="w-20 text-sm font-semibold text-gray-900 text-right">
                  <span>{{ item.duration }}%</span>
                  <span v-if="item.avgDays > 0" class="text-xs text-gray-500 ml-1">({{ item.avgDays }}d)</span>
                </div>
              </div>
            </div>
            
            <!-- Summary Section -->
            <div v-if="lifecycleSummary" class="mt-6 pt-6 border-t border-gray-200">
              <div class="grid grid-cols-2 gap-4">
                <div class="text-center">
                  <p class="text-xs text-gray-500 mb-1">Total Cycle Time</p>
                  <p class="text-lg font-semibold text-gray-900">{{ lifecycleSummary.avg_total_cycle_days }} days</p>
                </div>
                <div class="text-center">
                  <p class="text-xs text-gray-500 mb-1">RFPs Analyzed</p>
                  <p class="text-lg font-semibold text-gray-900">{{ lifecycleSummary.total_rfps }}</p>
                </div>
              </div>
              <div v-if="lifecycleSummary.trend" class="mt-4 text-center">
                <span class="text-xs text-gray-500">
                  Trend: 
                  <span :class="{
                    'text-green-600': lifecycleSummary.trend === 'down',
                    'text-red-600': lifecycleSummary.trend === 'up',
                    'text-gray-600': lifecycleSummary.trend === 'neutral'
                  }">
                    {{ lifecycleSummary.trend === 'down' ? '↓ Improving' : lifecycleSummary.trend === 'up' ? '↑ Increasing' : '→ Stable' }}
                    {{ lifecycleSummary.trend_percentage ? `(${lifecycleSummary.trend_percentage > 0 ? '+' : ''}${lifecycleSummary.trend_percentage}%)` : '' }}
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Vendor Metrics Section -->
      <div class="space-y-6">
        <div class="flex items-center gap-3">
          <div class="w-1 h-8 bg-purple-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">Vendor Performance Metrics</h2>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Vendor Response Rate -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Vendor Response Rate</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Vendor engagement across RFPs
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="vendorResponseData.length === 0" class="flex flex-col items-center justify-center h-[320px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Vendor Response Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Vendor response data will appear here once RFPs have vendor invitations and responses.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires vendor invitations with responses and evaluation scores.</p>
                </div>
              </div>
              <ScatterPlot v-else :data="vendorResponseData" />
            </div>
          </div>

          <!-- New vs Existing Vendors -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">New vs Existing Vendors</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Compare participation across vendor types
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <!-- Legend -->
              <div class="flex items-center justify-center gap-6 mb-4">
                <div class="flex items-center gap-2">
                  <div class="w-4 h-4 rounded bg-emerald-600"></div>
                  <span class="text-xs font-medium text-gray-700">New Vendors</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-4 h-4 rounded bg-blue-600"></div>
                  <span class="text-xs font-medium text-gray-700">Existing Vendors</span>
                </div>
              </div>
              <BarChart :data="newVsExistingData" />
            </div>
          </div>

          <!-- Category Performance -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Category Performance</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Track which vendor categories perform best
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="categoryPerformanceData.length === 0" class="flex flex-col items-center justify-center h-[320px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Category performance data will appear here once available.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires vendor invitations with responses and evaluation scores.</p>
                </div>
              </div>
              <ScatterPlot v-else :data="categoryPerformanceData" />
            </div>
          </div>

          <!-- Award Acceptance Rate -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Award Acceptance Rate</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Vendors accepting the awarded contracts
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="awardAcceptanceData.length === 0" class="flex flex-col items-center justify-center h-[200px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Award Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Award acceptance data will appear here once available.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires award notifications with vendor responses.</p>
                </div>
              </div>
              <PieChart v-else :data="awardAcceptanceData" />
            </div>
          </div>
        </div>
      </div>

      <!-- Vendor Conversion Funnel -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Vendor Conversion Funnel</h3>
            <div class="relative group">
              <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
              <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                Onboarding rate of previously unmatched vendors
              </div>
            </div>
          </div>
        </div>
        <div class="p-6">
          <div class="space-y-6">
            <div class="text-center">
              <h4 class="text-sm font-medium text-gray-600 mb-2">Conversion Pipeline</h4>
              <p class="text-xs text-gray-500">Vendor progression through the funnel</p>
            </div>
            <div class="space-y-4">
              <div class="flex justify-between items-center">
                <div v-for="(item, index) in processFlowData" :key="index" class="flex flex-col items-center">
                  <div class="text-xs font-medium text-gray-600 mb-2">{{ item.stage }}</div>
                  <div class="text-lg font-bold text-gray-900">{{ item.percentage }}%</div>
                </div>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                <div class="flex h-3 rounded-full overflow-hidden">
                  <div
                    v-for="(item, index) in processFlowData"
                    :key="index"
                    class="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-500"
                    :style="{ width: `${item.percentage}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Evaluation Metrics Section -->
      <div class="space-y-6">
        <div class="flex items-center gap-3">
          <div class="w-1 h-8 bg-orange-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">Evaluation Analytics</h2>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Reviewer Workload -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Reviewer Workload</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Distribution of workload across reviewers
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="reviewerWorkloadData.length === 0 || reviewerWorkloadData.every(d => d.value === 0)" class="flex flex-col items-center justify-center h-[200px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Reviewer Workload Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Reviewer workload data will appear here once RFPs are assigned to reviewers.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires RFPs with assigned primary or executive reviewers.</p>
                </div>
              </div>
              <LineChart v-else :data="reviewerWorkloadData" />
            </div>
          </div>

          <!-- Evaluator Consistency -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Evaluator Consistency</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Detect bias or inconsistency in scoring
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="evaluatorConsistencyData.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Evaluator Consistency Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Evaluator consistency data will appear here once RFPs are evaluated.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires evaluation scores from multiple evaluators.</p>
                </div>
              </div>
              <BoxPlot v-else :data="evaluatorConsistencyData" />
            </div>
          </div>

          <!-- Completion Time -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Completion Time</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Time each evaluator takes to finish
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <LineChart :data="completionTimeData" />
            </div>
          </div>

          <!-- Score Distribution -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Score Distribution</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Spread of scores per evaluation criterion
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="scoreDistributionData.length === 0" class="flex flex-col items-center justify-center h-[200px] bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Score Distribution Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Score distribution data will appear here once evaluations are completed.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires evaluation scores from evaluators.</p>
                </div>
              </div>
              <BarChart v-else :data="scoreDistributionData" />
            </div>
          </div>
        </div>
      </div>

      <!-- Consensus Quality and Criteria Effectiveness -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Consensus Quality</h3>
              <div class="relative group">
                <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Agreement levels among evaluators
                </div>
              </div>
            </div>
          </div>
          <div class="p-6">
            <Heatmap :data="consensusQualityData" />
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Criteria Effectiveness</h3>
              <div class="relative group">
                <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Impact of criteria weights on final score
                </div>
              </div>
            </div>
          </div>
          <div class="p-6">
            <CorrelationMatrix :data="criteriaEffectivenessData" />
          </div>
        </div>
      </div>

      <!-- Financial & Process Efficiency Section -->
      <div class="space-y-6">
        <div class="flex items-center gap-3">
          <div class="w-1 h-8 bg-red-600 rounded-full"></div>
          <h2 class="text-2xl font-bold text-gray-900">Financial & Process Efficiency</h2>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Budget Variance -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Budget Variance</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Alignment of estimated vs actual budgets
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="budgetVarianceData.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Budget Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Budget variance data will appear here once RFPs have estimated budgets.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires RFPs with estimated values set.</p>
                </div>
              </div>
              <div v-else class="space-y-6">
                <div class="text-center">
                  <h4 class="text-sm font-medium text-gray-600 mb-2">Budget Analysis</h4>
                  <p class="text-xs text-gray-500">Distribution of budget performance</p>
                </div>
                <div class="space-y-4">
                  <div v-for="(item, index) in budgetVarianceData" :key="index" class="space-y-3">
                    <div class="flex justify-between items-center">
                      <span class="text-sm font-medium text-gray-700">{{ item.category }}</span>
                      <span class="text-sm font-bold text-gray-900">{{ item.percentage }}%</span>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                      <div 
                        class="h-3 rounded-full transition-all duration-500" 
                        :style="{ width: `${Math.max(item.percentage, 1)}%`, backgroundColor: item.color }"
                      />
                    </div>
                    <div class="text-xs text-gray-500 text-center">{{ item.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Price Spread -->
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Price Spread</h3>
                <div class="relative group">
                  <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                  <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    Spread between highest and lowest bid prices
                  </div>
                </div>
              </div>
            </div>
            <div class="p-6">
              <div v-if="priceSpreadData.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
                <div class="text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <h3 class="mt-2 text-sm font-medium text-gray-900">No Price Spread Data Available</h3>
                  <p class="mt-1 text-sm text-gray-500">Price spread data will appear here once RFPs have multiple vendor bids.</p>
                  <p class="mt-2 text-xs text-gray-400">Note: Requires at least 2 bids per RFP.</p>
                </div>
              </div>
              <div v-else class="space-y-6">
                <div class="text-center">
                  <h4 class="text-sm font-medium text-gray-600 mb-2">Market Competitiveness</h4>
                  <p class="text-xs text-gray-500">{{ priceSpreadSummary.overall_competitiveness }}</p>
                </div>
                
                <!-- Summary Stats -->
                <div class="grid grid-cols-3 gap-4">
                  <div class="text-center p-3 bg-blue-50 rounded-lg">
                    <div class="text-lg font-bold text-blue-600">{{ priceSpreadSummary.avg_spread_pct }}%</div>
                    <div class="text-xs text-gray-600 mt-1">Avg Spread</div>
                  </div>
                  <div class="text-center p-3 bg-green-50 rounded-lg">
                    <div class="text-lg font-bold text-green-600">{{ priceSpreadSummary.rfps_with_multiple_bids }}</div>
                    <div class="text-xs text-gray-600 mt-1">RFPs</div>
                  </div>
                  <div class="text-center p-3 bg-purple-50 rounded-lg">
                    <div class="text-lg font-bold text-purple-600">{{ priceSpreadData.length }}</div>
                    <div class="text-xs text-gray-600 mt-1">With Bids</div>
                  </div>
                </div>

                <!-- Top RFPs by Spread -->
                <div class="space-y-3 max-h-64 overflow-y-auto">
                  <h5 class="text-xs font-semibold text-gray-700 uppercase tracking-wide">Top RFPs by Price Spread</h5>
                  <div v-for="(item, index) in priceSpreadData.slice(0, 5)" :key="index" class="space-y-2">
                    <div class="flex justify-between items-center">
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-medium text-gray-900 truncate">{{ item.rfp_title || item.rfp_number }}</p>
                        <p class="text-xs text-gray-500">{{ item.response_count }} bids</p>
                      </div>
                      <div class="text-right ml-2">
                        <span class="text-sm font-bold" :class="{
                          'text-green-600': item.spread_pct < 10,
                          'text-blue-600': item.spread_pct >= 10 && item.spread_pct < 25,
                          'text-yellow-600': item.spread_pct >= 25 && item.spread_pct < 50,
                          'text-red-600': item.spread_pct >= 50
                        }">
                          {{ item.spread_pct.toFixed(1) }}%
                        </span>
                      </div>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div 
                        class="h-2 rounded-full transition-all duration-500" 
                        :class="{
                          'bg-green-500': item.spread_pct < 10,
                          'bg-blue-500': item.spread_pct >= 10 && item.spread_pct < 25,
                          'bg-yellow-500': item.spread_pct >= 25 && item.spread_pct < 50,
                          'bg-red-500': item.spread_pct >= 50
                        }"
                        :style="{ width: `${Math.min((item.spread_pct / 100) * 100, 100)}%` }"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    <!-- Process Funnel Section -->
    <div class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-1 h-8 bg-indigo-600 rounded-full"></div>
        <h2 class="text-2xl font-bold text-gray-900">Process Funnel Analysis</h2>
      </div>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Process Funnel -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">RFP Process Funnel</h3>
              <div class="relative group">
                <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  RFP conversion through process stages
                </div>
              </div>
            </div>
          </div>
          <div class="p-6">
            <div v-if="processFunnelData.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
              <div class="text-center">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No Process Funnel Data Available</h3>
                <p class="mt-1 text-sm text-gray-500">Process funnel data will appear here once RFPs are created.</p>
              </div>
            </div>
            <div v-else class="space-y-6">
              <div class="text-center">
                <h4 class="text-sm font-medium text-gray-600 mb-2">Conversion Funnel</h4>
                <p class="text-xs text-gray-500">{{ processFunnelSummary.funnel_efficiency }}</p>
              </div>
              
              <!-- Summary Stats -->
              <div class="grid grid-cols-3 gap-4">
                <div class="text-center p-3 bg-indigo-50 rounded-lg">
                  <div class="text-lg font-bold text-indigo-600">{{ processFunnelSummary.overall_conversion_rate }}%</div>
                  <div class="text-xs text-gray-600 mt-1">Conversion</div>
                </div>
                <div class="text-center p-3 bg-green-50 rounded-lg">
                  <div class="text-lg font-bold text-green-600">{{ processFunnelSummary.completion_rate }}%</div>
                  <div class="text-xs text-gray-600 mt-1">Completion</div>
                </div>
                <div class="text-center p-3 bg-blue-50 rounded-lg">
                  <div class="text-lg font-bold text-blue-600">{{ processFunnelSummary.active_rfps }}</div>
                  <div class="text-xs text-gray-600 mt-1">Active RFPs</div>
                </div>
              </div>

              <!-- Funnel Stages -->
              <div class="space-y-3 max-h-96 overflow-y-auto">
                <h5 class="text-xs font-semibold text-gray-700 uppercase tracking-wide">Process Stages</h5>
                <div v-for="(item, index) in processFunnelData.slice(0, 7)" :key="index" class="space-y-2">
                  <div class="flex justify-between items-center">
                    <div class="flex items-center gap-2">
                      <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: item.color }"></div>
                      <span class="text-sm font-medium text-gray-900">{{ item.stage }}</span>
                    </div>
                    <div class="text-right ml-2">
                      <span class="text-sm font-bold text-gray-900">{{ item.count }}</span>
                      <span class="text-xs text-gray-500 ml-1">({{ item.percentage }}%)</span>
                    </div>
                  </div>
                  <div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div 
                      class="h-2 rounded-full transition-all duration-500" 
                      :style="{ 
                        width: `${Math.max(item.percentage, 1)}%`, 
                        backgroundColor: item.color 
                      }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Process Efficiency -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Process Efficiency</h3>
              <div class="relative group">
                <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  Key process metrics and insights
                </div>
              </div>
            </div>
          </div>
          <div class="p-6">
            <div v-if="processFunnelData.length === 0" class="flex flex-col items-center justify-center py-12 px-4">
              <div class="text-center">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No Efficiency Data Available</h3>
                <p class="mt-1 text-sm text-gray-500">Efficiency data will appear here once RFPs are processed.</p>
              </div>
            </div>
            <div v-else class="space-y-6">
              <div class="text-center">
                <h4 class="text-sm font-medium text-gray-600 mb-2">Key Metrics</h4>
                <p class="text-xs text-gray-500">Process performance indicators</p>
              </div>
              
              <!-- Efficiency Cards -->
              <div class="space-y-4">
                <div class="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-blue-700 uppercase tracking-wide">Total RFPs</p>
                      <p class="text-2xl font-bold text-blue-900 mt-1">{{ processFunnelSummary.total_rfps }}</p>
                    </div>
                    <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                      <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div class="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-100">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-green-700 uppercase tracking-wide">Awarded RFPs</p>
                      <p class="text-2xl font-bold text-green-900 mt-1">{{ processFunnelSummary.awarded_count }}</p>
                    </div>
                    <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                      <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div class="p-4 bg-gradient-to-r from-red-50 to-rose-50 rounded-lg border border-red-100">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-red-700 uppercase tracking-wide">Cancelled RFPs</p>
                      <p class="text-2xl font-bold text-red-900 mt-1">{{ processFunnelSummary.cancelled_count }}</p>
                    </div>
                    <div class="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                      <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2.5-2.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div class="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-100">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium text-purple-700 uppercase tracking-wide">Efficiency Rating</p>
                      <p class="text-2xl font-bold text-purple-900 mt-1">{{ processFunnelSummary.funnel_efficiency }}</p>
                    </div>
                    <div class="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center">
                      <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

      <!-- RFP Process Flow -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">RFP Process Flow</h3>
            <div class="relative group">
              <InfoIcon class="h-4 w-4 text-gray-400 cursor-help hover:text-gray-600 transition-colors" />
              <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                Flow from creation to awarding
              </div>
            </div>
          </div>
        </div>
        <div class="p-6">
          <div class="space-y-6">
            <div class="text-center">
              <h4 class="text-sm font-medium text-gray-600 mb-2">Process Funnel</h4>
              <p class="text-xs text-gray-500">Conversion rates through each stage</p>
            </div>
            <div class="space-y-4">
              <div v-for="(item, index) in processFlowData" :key="index" class="flex items-center space-x-6">
                <div class="w-24 text-sm font-medium text-gray-700 text-right">{{ item.stage }}</div>
                <div class="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div 
                    class="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500"
                    :style="{ width: `${item.percentage}%` }"
                  />
                </div>
                <div class="w-12 text-sm font-bold text-gray-900 text-right">{{ item.percentage }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { InfoIcon, TrendingUp } from 'lucide-vue-next'
import axios from 'axios'
import { useRfpApi } from '@/composables/useRfpApi'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import { getApiV1BaseUrl } from '@/utils/backendEnv'

// Use shared backend env resolver so prod/stage/dev all hit the real API host
const API_BASE_URL = getApiV1BaseUrl()

// Data for KPI summary cards
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for API calls
const { getAuthHeaders } = useRfpApi()

const summaryKPIs = ref([
  { 
    title: "Total RFPs Created", 
    value: "0", 
    change: "Loading...",
    trend: "neutral",
    tooltip: "Total volume created to date" 
  },
  { 
    title: "Active RFPs", 
    value: "0", 
    change: "Loading...",
    trend: "neutral",
    tooltip: "Currently open or under review" 
  },
  { 
    title: "Awarded RFPs", 
    value: "0", 
    change: "Loading...",
    trend: "neutral",
    tooltip: "Successfully completed RFPs" 
  },
  { 
    title: "Avg RFP Cycle Days", 
    value: "0", 
    subtext: "days",
    change: "Loading...",
    trend: "neutral",
    tooltip: "Avg duration from creation to awarding" 
  },
  { 
    title: "Avg Quality Score", 
    value: "0", 
    subtext: "out of 10",
    change: "Loading...",
    trend: "neutral",
    tooltip: "Overall weighted quality score of evaluations" 
  },
  { 
    title: "Cost Savings %", 
    value: "0%", 
    change: "Loading...",
    trend: "neutral",
    tooltip: "Savings achieved through negotiation" 
  },
])

const isLoading = ref(true)
const errorMessage = ref('')

// Fetch KPI summary data from API
const fetchKPISummary = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    console.log(`📊 Fetching KPI summary from: ${API_BASE_URL}/kpi/summary/`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/summary/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 KPI API Response:', response.data)
    
    if (response.data.success && response.data.summary_kpis) {
      summaryKPIs.value = response.data.summary_kpis
      console.log(`✅ Successfully loaded ${summaryKPIs.value.length} KPI cards`)
      console.log('📊 Sample KPI:', summaryKPIs.value[0])
    } else {
      errorMessage.value = 'Failed to load KPI data'
      console.error('❌ KPI API returned unsuccessful response:', response.data)
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching KPI summary:', error)
    console.error('Error details:', error.response?.data || error.message)
    errorMessage.value = `Error loading KPI data: ${error.message}. Using fallback values.`
    
    // Fallback to default values if API fails
    summaryKPIs.value = [
      { 
        title: "Total RFPs Created", 
        value: "N/A", 
        change: "API Error",
        trend: "neutral",
        tooltip: "Total volume created to date" 
      },
      { 
        title: "Active RFPs", 
        value: "N/A", 
        change: "API Error",
        trend: "neutral",
        tooltip: "Currently open or under review" 
      },
      { 
        title: "Awarded RFPs", 
        value: "N/A", 
        change: "API Error",
        trend: "neutral",
        tooltip: "Successfully completed RFPs" 
      },
      { 
        title: "Avg RFP Cycle Days", 
        value: "N/A", 
        subtext: "days",
        change: "API Error",
        trend: "neutral",
        tooltip: "Avg duration from creation to awarding" 
      },
      { 
        title: "Avg Quality Score", 
        value: "N/A", 
        subtext: "out of 10",
        change: "API Error",
        trend: "neutral",
        tooltip: "Overall weighted quality score of evaluations" 
      },
      { 
        title: "Cost Savings %", 
        value: "N/A", 
        change: "API Error",
        trend: "neutral",
        tooltip: "Savings achieved through negotiation" 
      },
    ]
  } finally {
    isLoading.value = false
  }
}

// Timeline selection state
const selectedTimeline = ref('6M')
const selectedApprovalTimeline = ref('6M')
const timelineOptions = ref([
  { label: '3M', value: '3M' },
  { label: '6M', value: '6M' },
  { label: '1Y', value: '1Y' },
  { label: 'All', value: 'ALL' }
])

// Chart data matching reference images
const rfpCreationData = ref([
  { month: "Jan", value: 0 },
  { month: "Feb", value: 0 },
  { month: "Mar", value: 0 },
  { month: "Apr", value: 0 },
  { month: "May", value: 0 },
  { month: "Jun", value: 0 },
])

// Fetch RFP Creation Rate data
const fetchRFPCreationRate = async (timeline = '6M') => {
  try {
    console.log(`📊 Fetching RFP creation rate for timeline: ${timeline}`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/creation-rate/`, {
      params: { timeline },
      headers: getAuthHeaders()
    })
    
    console.log('📊 Creation Rate API Response:', response.data)
    
    if (response.data.success && response.data.creation_rate) {
      // Use the data based on timeline
      let dataToShow = response.data.creation_rate
      
      // For different timelines, show appropriate number of months
      if (timeline === '3M') {
        dataToShow = response.data.creation_rate.slice(-3)
      } else if (timeline === '6M') {
        dataToShow = response.data.creation_rate.slice(-6)
      } else if (timeline === '1Y') {
        dataToShow = response.data.creation_rate.slice(-12)
      }
      // For 'ALL', show all data
      
      rfpCreationData.value = dataToShow
      console.log(`✅ RFP Creation Rate loaded (${timeline}):`, dataToShow)
      console.log(`📊 Total data points: ${dataToShow.length}`)
    } else {
      console.error('❌ Failed to load RFP creation rate:', response.data)
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching RFP creation rate:', error)
    console.error('Error details:', error.response?.data || error.message)
    // Keep default data on error
  }
}

// Change timeline
const changeTimeline = (timeline) => {
  selectedTimeline.value = timeline
  fetchRFPCreationRate(timeline)
}

// Change approval timeline
const changeApprovalTimeline = (timeline) => {
  selectedApprovalTimeline.value = timeline
  fetchRFPApprovalTime(timeline)
}

// Fetch data on component mount
onMounted(() => {
  fetchKPISummary()
  fetchRFPCreationRate()
  fetchRFPApprovalTime('6M')
  fetchFirstTimeApprovalRate()
  fetchApprovalStagePerformance()
  fetchRFPLifecycleTime()
  fetchVendorResponseRate()
  fetchNewVsExistingVendors()
  fetchCategoryPerformance()
  fetchAwardAcceptanceRate()
  fetchVendorConversionFunnel()
  fetchReviewerWorkload()
  fetchEvaluatorConsistency()
  fetchCompletionTime()
  fetchScoreDistribution()
  fetchConsensusQuality()
  fetchCriteriaEffectiveness()
  fetchBudgetVariance()
  fetchPriceSpread()
  fetchProcessFunnel()
})

const approvalTimeData = ref([
  { month: "Jan", value: 0 },
  { month: "Feb", value: 0 },
  { month: "Mar", value: 0 },
  { month: "Apr", value: 0 },
  { month: "May", value: 0 },
  { month: "Jun", value: 0 },
])

// Fetch RFP Approval Time data
const fetchRFPApprovalTime = async (timeline = '6M') => {
  try {
    console.log(`📊 Fetching RFP approval time data for timeline: ${timeline}`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/approval-time/`, {
      params: { timeline },
      headers: getAuthHeaders()
    })
    
    console.log('📊 Approval Time API Response:', response.data)
    
    if (response.data.success && response.data.approval_time) {
      // Use the data based on timeline
      let dataToShow = response.data.approval_time
      
      // For different timelines, show appropriate number of months
      if (timeline === '3M') {
        dataToShow = response.data.approval_time.slice(-3)
      } else if (timeline === '6M') {
        dataToShow = response.data.approval_time.slice(-6)
      } else if (timeline === '1Y') {
        dataToShow = response.data.approval_time.slice(-12)
      }
      // For 'ALL', show all data
      
      approvalTimeData.value = dataToShow
      console.log(`✅ RFP Approval Time loaded (${timeline}):`, dataToShow)
      console.log(`📊 Total data points: ${dataToShow.length}`)
    } else {
      console.error('❌ Failed to load RFP approval time:', response.data)
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching RFP approval time:', error)
    console.error('Error details:', error.response?.data || error.message)
    // Keep default data on error
  }
}

const firstTimeApprovalRate = ref(68) // Gauge chart value with fallback

// Fetch First-Time Approval Rate data
const fetchFirstTimeApprovalRate = async () => {
  try {
    console.log(`📊 Fetching First-Time Approval Rate data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/first-time-approval-rate/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 First-Time Approval Rate API Response:', response.data)
    
    if (response.data.success && response.data.first_time_approval_rate !== undefined) {
      firstTimeApprovalRate.value = Math.round(response.data.first_time_approval_rate)
      console.log(`✅ First-Time Approval Rate loaded: ${firstTimeApprovalRate.value}%`)
    } else {
      console.warn('⚠️ No first-time approval data, using fallback mock data')
      firstTimeApprovalRate.value = 68 // Realistic fallback
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching First-Time Approval Rate:', error)
    console.error('Error details:', error.response?.data || error.message)
    // Use fallback value on error
    firstTimeApprovalRate.value = 68
  }
}

const approvalStageData = ref([
  { stage: "Initial Review", value: 2.3 },
  { stage: "Legal Review", value: 4.1 },
  { stage: "Finance Review", value: 3.2 },
  { stage: "Executive Approval", value: 5.8 },
  { stage: "Final Approval", value: 1.9 },
])

// Fetch Approval Stage Performance data
const fetchApprovalStagePerformance = async () => {
  try {
    console.log(`📊 Fetching Approval Stage Performance data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/approval-stage-performance/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Approval Stage Performance API Response:', response.data)
    
    if (response.data.success && response.data.stage_performance) {
      const stages = response.data.stage_performance
      
      if (stages.length > 0) {
        // Transform stage performance data to match chart format
        approvalStageData.value = stages.map(stage => ({
          stage: stage.stage_name || `Stage ${stage.stage_order}`,
          value: stage.avg_days ? Math.round(stage.avg_days * 10) / 10 : 0 // Round to 1 decimal place, default to 0 if null
        }))
        
        console.log(`✅ Approval Stage Performance loaded:`, approvalStageData.value)
        console.log(`📊 Number of stages: ${stages.length}`)
        console.log(`📊 Stage details:`, stages.map(s => `${s.stage_name}: ${s.stage_count} stages, ${s.avg_days} avg days`))
      } else {
        console.warn('⚠️ No stage performance data available, using fallback mock data')
        // Use realistic fallback data
        approvalStageData.value = [
          { stage: "Initial Review", value: 2.3 },
          { stage: "Legal Review", value: 4.1 },
          { stage: "Finance Review", value: 3.2 },
          { stage: "Executive Approval", value: 5.8 },
          { stage: "Final Approval", value: 1.9 },
        ]
      }
    } else {
      console.warn('⚠️ Failed to load Approval Stage Performance, using fallback mock data')
      approvalStageData.value = [
        { stage: "Initial Review", value: 2.3 },
        { stage: "Legal Review", value: 4.1 },
        { stage: "Finance Review", value: 3.2 },
        { stage: "Executive Approval", value: 5.8 },
        { stage: "Final Approval", value: 1.9 },
      ]
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Approval Stage Performance:', error)
    console.error('Error details:', error.response?.data || error.message)
    // Use fallback data on error
    approvalStageData.value = [
      { stage: "Initial Review", value: 2.3 },
      { stage: "Legal Review", value: 4.1 },
      { stage: "Finance Review", value: 3.2 },
      { stage: "Executive Approval", value: 5.8 },
      { stage: "Final Approval", value: 1.9 },
    ]
  }
}

const fetchRFPLifecycleTime = async () => {
  try {
    console.log(`📊 Fetching RFP Lifecycle Time data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/lifecycle-time/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 RFP Lifecycle Time API Response:', response.data)
    
    if (response.data.success && response.data.lifecycle_phases) {
      const phases = response.data.lifecycle_phases
      
      if (phases.length > 0) {
        // Transform lifecycle phases data to match gantt chart format
        ganttData.value = phases.map(phase => ({
          phase: phase.phase,
          duration: phase.cumulative_percentage,
          avgDays: phase.avg_days,
          description: phase.description
        }))
        
        // Store summary data
        lifecycleSummary.value = {
          avg_total_cycle_days: response.data.summary.avg_total_cycle_days,
          total_rfps: response.data.summary.total_rfps,
          trend: response.data.summary.trend,
          trend_percentage: response.data.summary.trend_percentage
        }
        
        console.log(`✅ RFP Lifecycle Time loaded:`, ganttData.value)
        console.log(`📊 Total cycle time: ${response.data.summary.avg_total_cycle_days} days`)
        console.log(`📊 Total RFPs analyzed: ${response.data.summary.total_rfps}`)
      } else {
        console.warn('⚠️ No lifecycle data available, using fallback mock data')
        // Use fallback data
        ganttData.value = [
          { phase: "Draft", duration: 15, avgDays: 8, description: "RFP creation and drafting" },
          { phase: "Approval", duration: 35, avgDays: 12, description: "Internal approval process" },
          { phase: "Publishing", duration: 50, avgDays: 5, description: "RFP published to vendors" },
          { phase: "Vendor Response", duration: 80, avgDays: 21, description: "Vendors submit proposals" },
          { phase: "Evaluation", duration: 95, avgDays: 14, description: "Proposal evaluation" },
          { phase: "Award", duration: 100, avgDays: 10, description: "Final award decision" }
        ]
        lifecycleSummary.value = {
          avg_total_cycle_days: 70,
          total_rfps: 45,
          trend: 'down',
          trend_percentage: -12
        }
      }
    } else {
      console.warn('⚠️ Failed to load RFP Lifecycle Time, using fallback mock data')
      ganttData.value = [
        { phase: "Draft", duration: 15, avgDays: 8, description: "RFP creation and drafting" },
        { phase: "Approval", duration: 35, avgDays: 12, description: "Internal approval process" },
        { phase: "Publishing", duration: 50, avgDays: 5, description: "RFP published to vendors" },
        { phase: "Vendor Response", duration: 80, avgDays: 21, description: "Vendors submit proposals" },
        { phase: "Evaluation", duration: 95, avgDays: 14, description: "Proposal evaluation" },
        { phase: "Award", duration: 100, avgDays: 10, description: "Final award decision" }
      ]
      lifecycleSummary.value = {
        avg_total_cycle_days: 70,
        total_rfps: 45,
        trend: 'down',
        trend_percentage: -12
      }
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching RFP Lifecycle Time:', error)
    console.error('Error details:', error.response?.data || error.message)
    // Use fallback data on error
    ganttData.value = [
      { phase: "Draft", duration: 15, avgDays: 8, description: "RFP creation and drafting" },
      { phase: "Approval", duration: 35, avgDays: 12, description: "Internal approval process" },
      { phase: "Publishing", duration: 50, avgDays: 5, description: "RFP published to vendors" },
      { phase: "Vendor Response", duration: 80, avgDays: 21, description: "Vendors submit proposals" },
      { phase: "Evaluation", duration: 95, avgDays: 14, description: "Proposal evaluation" },
      { phase: "Award", duration: 100, avgDays: 10, description: "Final award decision" }
    ]
    lifecycleSummary.value = {
      avg_total_cycle_days: 70,
      total_rfps: 45,
      trend: 'down',
      trend_percentage: -12
    }
  }
}

const ganttData = ref([
  { phase: "Draft", duration: 15, avgDays: 8, description: "RFP creation and drafting" },
  { phase: "Approval", duration: 35, avgDays: 12, description: "Internal approval process" },
  { phase: "Publishing", duration: 50, avgDays: 5, description: "RFP published to vendors" },
  { phase: "Vendor Response", duration: 80, avgDays: 21, description: "Vendors submit proposals" },
  { phase: "Evaluation", duration: 95, avgDays: 14, description: "Proposal evaluation" },
  { phase: "Award", duration: 100, avgDays: 10, description: "Final award decision" }
])

const lifecycleSummary = ref({
  avg_total_cycle_days: 70,
  total_rfps: 45,
  trend: 'down',
  trend_percentage: -12
})

const newVsExistingData = ref([
  { month: "Jan", new: 0, existing: 0 },
  { month: "Feb", new: 0, existing: 0 },
  { month: "Mar", new: 0, existing: 0 },
  { month: "Apr", new: 0, existing: 0 },
  { month: "May", new: 0, existing: 0 },
  { month: "Jun", new: 0, existing: 0 },
])

// Fetch New vs Existing Vendors data
const fetchNewVsExistingVendors = async () => {
  try {
    console.log(`📊 Fetching New vs Existing Vendors data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/new-vs-existing-vendors/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 New vs Existing Vendors API Response:', response.data)
    
    if (response.data.success && response.data.new_vs_existing_vendors) {
      const data = response.data.new_vs_existing_vendors.monthly_breakdown
      
      if (data.length > 0) {
        // Transform data to match chart format
        newVsExistingData.value = data.map(item => ({
          month: item.month,
          year: item.year,
          new: item.new_vendors,
          existing: item.existing_vendors,
          total: item.total_vendors
        }))
        
        console.log(`✅ New vs Existing Vendors loaded:`, newVsExistingData.value)
        console.log(`📊 Summary:`, response.data.new_vs_existing_vendors.summary)
      } else {
        console.warn('⚠️ No new vs existing vendors data available')
        // Keep default data
      }
    } else {
      console.error('❌ Failed to load New vs Existing Vendors:', response.data)
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching New vs Existing Vendors:', error)
    console.error('Error details:', error.response?.data || error.message)
    // Keep default data on error
  }
}

// Default reviewer workload data (empty state)
const reviewerWorkloadData = ref([
  { month: "Jan", value: 0 },
  { month: "Feb", value: 0 },
  { month: "Mar", value: 0 },
  { month: "Apr", value: 0 },
  { month: "May", value: 0 },
  { month: "Jun", value: 0 },
])

// Fetch Reviewer Workload data
const fetchReviewerWorkload = async () => {
  try {
    console.log(`📊 Fetching Reviewer Workload data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/reviewer-workload/`, {
      params: { timeline: '6M' },
      headers: getAuthHeaders()
    })
    
    console.log('📊 Reviewer Workload API Response:', response.data)
    
    if (response.data.success && response.data.reviewer_workload) {
      const monthlyData = response.data.reviewer_workload.monthly_data
      const reviewers = response.data.reviewer_workload.reviewers
      
      if (monthlyData && monthlyData.length > 0) {
        // Transform data to line chart format
        // Use the 'total' field from the API response
        const transformedData = monthlyData.map(month => {
          // Use total field if available, otherwise calculate it
          const totalValue = month.total !== undefined 
            ? month.total 
            : Object.keys(month)
                .filter(key => key.startsWith('reviewer_'))
                .reduce((sum, key) => {
                  const val = month[key] || 0
                  return sum + (typeof val === 'number' ? val : 0)
                }, 0)
          
          return {
            month: month.month || 'Unknown',
            year: month.year || new Date().getFullYear(),
            value: totalValue
          }
        })
        
        console.log(`✅ Reviewer Workload loaded:`, transformedData)
        console.log(`📊 Summary:`, response.data.reviewer_workload.summary)
        if (reviewers && reviewers.length > 0) {
          console.log(`📊 Top reviewers:`, reviewers.map(r => `${r.reviewer_name} (${r.total_rfps} RFPs)`).join(', '))
        }
        
        // Only update if we have valid data
        if (transformedData.length > 0) {
          reviewerWorkloadData.value = transformedData
        }
      } else {
        console.warn('⚠️ No reviewer workload data available - keeping default values')
        // Keep default data instead of clearing
      }
    } else {
      console.error('❌ Failed to load Reviewer Workload:', response.data)
      // Keep default data instead of clearing
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Reviewer Workload:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    // Keep default data instead of clearing
  }
}

const completionTimeData = ref([])

// Fetch Completion Time data
const fetchCompletionTime = async () => {
  try {
    console.log(`📊 Fetching Completion Time data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/evaluator-completion-time/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Completion Time API Response:', response.data)
    
    if (response.data.success && response.data.evaluator_completion_time) {
      const data = response.data.evaluator_completion_time
      const monthlyData = data.monthly_data || []
      
      if (monthlyData.length > 0) {
        // Transform data to line chart format
        // Line chart expects: { month, value, year, ...evaluator_values }
        const transformedData = monthlyData.map(item => ({
          month: item.month,
          year: item.year,
          value: item.total,
          ...item  // Include all evaluator-specific values
        }))
        
        console.log(`✅ Completion Time loaded:`, transformedData)
        console.log(`📊 Summary:`, data.summary)
        console.log(`📊 Evaluators:`, data.evaluators)
        
        completionTimeData.value = transformedData
      } else {
        console.warn('⚠️ No completion time data available')
        completionTimeData.value = []
      }
    } else {
      console.error('❌ Failed to load Completion Time:', response.data)
      completionTimeData.value = []
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Completion Time:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    completionTimeData.value = []
  }
}

const evaluatorConsistencyData = ref([])

// Fetch Evaluator Consistency data
const fetchEvaluatorConsistency = async () => {
  try {
    console.log(`📊 Fetching Evaluator Consistency data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/evaluator-consistency/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Evaluator Consistency API Response:', response.data)
    
    if (response.data.success && response.data.evaluator_consistency) {
      const data = response.data.evaluator_consistency
      const evaluators = data.evaluators || []
      
      if (evaluators.length > 0) {
        // Transform data to box plot format
        // Box plot expects: { criteria, min, q1, median, q3, max }
        const transformedData = evaluators.map(evaluator => ({
          criteria: evaluator.evaluator_name,
          min: evaluator.min_score,
          q1: evaluator.avg_score - (evaluator.std_dev * 0.5), // Approximate Q1
          median: evaluator.avg_score,
          q3: evaluator.avg_score + (evaluator.std_dev * 0.5), // Approximate Q3
          max: evaluator.max_score,
          avgScore: evaluator.avg_score,
          consistencyRating: evaluator.consistency_rating,
          consistencyColor: evaluator.consistency_color,
          scoringPattern: evaluator.scoring_pattern,
          patternColor: evaluator.pattern_color,
          totalEvaluations: evaluator.total_evaluations,
          stdDev: evaluator.std_dev,
          coefficientOfVariation: evaluator.coefficient_of_variation
        }))
        
        console.log(`✅ Evaluator Consistency loaded:`, transformedData)
        console.log(`📊 Summary:`, data.summary)
        if (data.outliers && data.outliers.length > 0) {
          console.log(`📊 Outliers detected:`, data.outliers.map(o => o.evaluator_name).join(', '))
        }
        
        evaluatorConsistencyData.value = transformedData
      } else {
        console.warn('⚠️ No evaluator consistency data available')
        evaluatorConsistencyData.value = []
      }
    } else {
      console.error('❌ Failed to load Evaluator Consistency:', response.data)
      evaluatorConsistencyData.value = []
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Evaluator Consistency:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    evaluatorConsistencyData.value = []
  }
}

const processFlowData = ref([])

// Additional data for new chart components
const vendorResponseData = ref([
  { x: 85, y: 8.2, rfp_title: "IT Services RFP", rfp_number: "RFP-2024-001", invitations: 20, responses: 17, response_rate: 85 },
  { x: 72, y: 7.5, rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-002", invitations: 18, responses: 13, response_rate: 72 },
  { x: 90, y: 8.8, rfp_title: "Security Services", rfp_number: "RFP-2024-003", invitations: 15, responses: 14, response_rate: 93 },
  { x: 65, y: 6.8, rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", invitations: 22, responses: 14, response_rate: 64 },
  { x: 78, y: 7.9, rfp_title: "Software Licensing", rfp_number: "RFP-2024-005", invitations: 16, responses: 12, response_rate: 75 },
  { x: 82, y: 8.1, rfp_title: "Data Analytics", rfp_number: "RFP-2024-006", invitations: 19, responses: 16, response_rate: 84 }
])

// Fetch Vendor Response Rate data
const fetchVendorResponseRate = async () => {
  try {
    console.log(`📊 Fetching Vendor Response Rate data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/vendor-response-rate/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Vendor Response Rate API Response:', response.data)
    
    if (response.data.success && response.data.vendor_response_rate) {
      const data = response.data.vendor_response_rate
      
      if (data.length > 0) {
        // Transform data to match scatter plot format
        vendorResponseData.value = data.map(item => ({
          x: item.x,
          y: item.y,
          rfp_title: item.rfp_title,
          rfp_number: item.rfp_number,
          invitations: item.invitations,
          responses: item.responses,
          response_rate: item.response_rate
        }))
        
        console.log(`✅ Vendor Response Rate loaded:`, vendorResponseData.value)
        console.log(`📊 Total data points: ${data.length}`)
        console.log(`📊 Summary:`, response.data.summary)
      } else {
        console.warn('⚠️ No vendor response rate data available, using fallback mock data')
        vendorResponseData.value = [
          { x: 85, y: 8.2, rfp_title: "IT Services RFP", rfp_number: "RFP-2024-001", invitations: 20, responses: 17, response_rate: 85 },
          { x: 72, y: 7.5, rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-002", invitations: 18, responses: 13, response_rate: 72 },
          { x: 90, y: 8.8, rfp_title: "Security Services", rfp_number: "RFP-2024-003", invitations: 15, responses: 14, response_rate: 93 },
          { x: 65, y: 6.8, rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", invitations: 22, responses: 14, response_rate: 64 },
          { x: 78, y: 7.9, rfp_title: "Software Licensing", rfp_number: "RFP-2024-005", invitations: 16, responses: 12, response_rate: 75 },
          { x: 82, y: 8.1, rfp_title: "Data Analytics", rfp_number: "RFP-2024-006", invitations: 19, responses: 16, response_rate: 84 }
        ]
      }
    } else {
      console.warn('⚠️ Failed to load Vendor Response Rate, using fallback mock data')
      vendorResponseData.value = [
        { x: 85, y: 8.2, rfp_title: "IT Services RFP", rfp_number: "RFP-2024-001", invitations: 20, responses: 17, response_rate: 85 },
        { x: 72, y: 7.5, rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-002", invitations: 18, responses: 13, response_rate: 72 },
        { x: 90, y: 8.8, rfp_title: "Security Services", rfp_number: "RFP-2024-003", invitations: 15, responses: 14, response_rate: 93 },
        { x: 65, y: 6.8, rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", invitations: 22, responses: 14, response_rate: 64 },
        { x: 78, y: 7.9, rfp_title: "Software Licensing", rfp_number: "RFP-2024-005", invitations: 16, responses: 12, response_rate: 75 },
        { x: 82, y: 8.1, rfp_title: "Data Analytics", rfp_number: "RFP-2024-006", invitations: 19, responses: 16, response_rate: 84 }
      ]
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Vendor Response Rate:', error)
    console.error('Error details:', error.response?.data || error.message)
    vendorResponseData.value = [
      { x: 85, y: 8.2, rfp_title: "IT Services RFP", rfp_number: "RFP-2024-001", invitations: 20, responses: 17, response_rate: 85 },
      { x: 72, y: 7.5, rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-002", invitations: 18, responses: 13, response_rate: 72 },
      { x: 90, y: 8.8, rfp_title: "Security Services", rfp_number: "RFP-2024-003", invitations: 15, responses: 14, response_rate: 93 },
      { x: 65, y: 6.8, rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", invitations: 22, responses: 14, response_rate: 64 },
      { x: 78, y: 7.9, rfp_title: "Software Licensing", rfp_number: "RFP-2024-005", invitations: 16, responses: 12, response_rate: 75 },
      { x: 82, y: 8.1, rfp_title: "Data Analytics", rfp_number: "RFP-2024-006", invitations: 19, responses: 16, response_rate: 84 }
    ]
  }
}

const categoryPerformanceData = ref([
  { x: 78, y: 8.1, category: "IT Services", vendor_count: 12, invitations: 48, responses: 37, response_rate: 77, avg_quality_score: 8.1 },
  { x: 85, y: 8.5, category: "Cloud Solutions", vendor_count: 8, invitations: 32, responses: 27, response_rate: 84, avg_quality_score: 8.5 },
  { x: 72, y: 7.2, category: "Consulting", vendor_count: 15, invitations: 60, responses: 43, response_rate: 72, avg_quality_score: 7.2 },
  { x: 88, y: 8.8, category: "Security", vendor_count: 6, invitations: 24, responses: 21, response_rate: 88, avg_quality_score: 8.8 },
  { x: 65, y: 6.9, category: "Facilities", vendor_count: 10, invitations: 40, responses: 26, response_rate: 65, avg_quality_score: 6.9 },
  { x: 80, y: 8.3, category: "Software", vendor_count: 14, invitations: 56, responses: 45, response_rate: 80, avg_quality_score: 8.3 }
])

// Fetch Category Performance data
const fetchCategoryPerformance = async () => {
  try {
    console.log(`📊 Fetching Category Performance data from: ${API_BASE_URL}/kpi/category-performance/`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/category-performance/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Category Performance API Response:', response.data)
    
    if (response.data.success && response.data.category_performance) {
      const data = response.data.category_performance
      
      console.log(`📊 Raw category data from API:`, data)
      console.log(`📊 Number of categories: ${data.length}`)
      
      if (data.length > 0) {
        // Transform data to match scatter plot format
        categoryPerformanceData.value = data.map(item => ({
          x: item.x,
          y: item.y,
          category: item.category,
          vendor_count: item.vendor_count,
          invitations: item.invitations,
          responses: item.responses,
          response_rate: item.response_rate,
          avg_quality_score: item.avg_quality_score
        }))
        
        console.log(`✅ Category Performance loaded successfully!`)
        console.log(`📊 Transformed data:`, categoryPerformanceData.value)
        console.log(`📊 Summary:`, response.data.summary)
      } else {
        console.warn('⚠️ No category performance data available in database, using fallback mock data')
        categoryPerformanceData.value = [
          { x: 78, y: 8.1, category: "IT Services", vendor_count: 12, invitations: 48, responses: 37, response_rate: 77, avg_quality_score: 8.1 },
          { x: 85, y: 8.5, category: "Cloud Solutions", vendor_count: 8, invitations: 32, responses: 27, response_rate: 84, avg_quality_score: 8.5 },
          { x: 72, y: 7.2, category: "Consulting", vendor_count: 15, invitations: 60, responses: 43, response_rate: 72, avg_quality_score: 7.2 },
          { x: 88, y: 8.8, category: "Security", vendor_count: 6, invitations: 24, responses: 21, response_rate: 88, avg_quality_score: 8.8 },
          { x: 65, y: 6.9, category: "Facilities", vendor_count: 10, invitations: 40, responses: 26, response_rate: 65, avg_quality_score: 6.9 },
          { x: 80, y: 8.3, category: "Software", vendor_count: 14, invitations: 56, responses: 45, response_rate: 80, avg_quality_score: 8.3 }
        ]
      }
    } else {
      console.warn('⚠️ Failed to load Category Performance, using fallback mock data')
      categoryPerformanceData.value = [
        { x: 78, y: 8.1, category: "IT Services", vendor_count: 12, invitations: 48, responses: 37, response_rate: 77, avg_quality_score: 8.1 },
        { x: 85, y: 8.5, category: "Cloud Solutions", vendor_count: 8, invitations: 32, responses: 27, response_rate: 84, avg_quality_score: 8.5 },
        { x: 72, y: 7.2, category: "Consulting", vendor_count: 15, invitations: 60, responses: 43, response_rate: 72, avg_quality_score: 7.2 },
        { x: 88, y: 8.8, category: "Security", vendor_count: 6, invitations: 24, responses: 21, response_rate: 88, avg_quality_score: 8.8 },
        { x: 65, y: 6.9, category: "Facilities", vendor_count: 10, invitations: 40, responses: 26, response_rate: 65, avg_quality_score: 6.9 },
        { x: 80, y: 8.3, category: "Software", vendor_count: 14, invitations: 56, responses: 45, response_rate: 80, avg_quality_score: 8.3 }
      ]
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Category Performance:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    console.error('❌ Full error:', error)
    categoryPerformanceData.value = [
      { x: 78, y: 8.1, category: "IT Services", vendor_count: 12, invitations: 48, responses: 37, response_rate: 77, avg_quality_score: 8.1 },
      { x: 85, y: 8.5, category: "Cloud Solutions", vendor_count: 8, invitations: 32, responses: 27, response_rate: 84, avg_quality_score: 8.5 },
      { x: 72, y: 7.2, category: "Consulting", vendor_count: 15, invitations: 60, responses: 43, response_rate: 72, avg_quality_score: 7.2 },
      { x: 88, y: 8.8, category: "Security", vendor_count: 6, invitations: 24, responses: 21, response_rate: 88, avg_quality_score: 8.8 },
      { x: 65, y: 6.9, category: "Facilities", vendor_count: 10, invitations: 40, responses: 26, response_rate: 65, avg_quality_score: 6.9 },
      { x: 80, y: 8.3, category: "Software", vendor_count: 14, invitations: 56, responses: 45, response_rate: 80, avg_quality_score: 8.3 }
    ]
  }
}

const awardAcceptanceData = ref([
  { label: "Accepted", value: 78.5, count: 51, color: "#10b981" },
  { label: "Pending", value: 12.3, count: 8, color: "#f59e0b" },
  { label: "Declined", value: 9.2, count: 6, color: "#ef4444" }
])

// Fetch Award Acceptance Rate data
const fetchAwardAcceptanceRate = async () => {
  try {
    console.log(`📊 Fetching Award Acceptance Rate data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/award-acceptance-rate/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Award Acceptance Rate API Response:', response.data)
    
    if (response.data.success && response.data.award_acceptance_rate) {
      const data = response.data.award_acceptance_rate.pie_chart_data
      
      if (data.length > 0) {
        // Transform data to match pie chart format
        awardAcceptanceData.value = data.map(item => ({
          label: item.label,
          value: item.value,
          count: item.count,
          color: item.color
        }))
        
        console.log(`✅ Award Acceptance Rate loaded:`, awardAcceptanceData.value)
        console.log(`📊 Summary:`, response.data.award_acceptance_rate.summary)
      } else {
        console.warn('⚠️ No award acceptance data available, using fallback mock data')
        awardAcceptanceData.value = [
          { label: "Accepted", value: 78.5, count: 51, color: "#10b981" },
          { label: "Pending", value: 12.3, count: 8, color: "#f59e0b" },
          { label: "Declined", value: 9.2, count: 6, color: "#ef4444" }
        ]
      }
    } else {
      console.warn('⚠️ Failed to load Award Acceptance Rate, using fallback mock data')
      awardAcceptanceData.value = [
        { label: "Accepted", value: 78.5, count: 51, color: "#10b981" },
        { label: "Pending", value: 12.3, count: 8, color: "#f59e0b" },
        { label: "Declined", value: 9.2, count: 6, color: "#ef4444" }
      ]
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Award Acceptance Rate:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    awardAcceptanceData.value = [
      { label: "Accepted", value: 78.5, count: 51, color: "#10b981" },
      { label: "Pending", value: 12.3, count: 8, color: "#f59e0b" },
      { label: "Declined", value: 9.2, count: 6, color: "#ef4444" }
    ]
  }
}

const vendorConversionFunnelData = ref([])

// Fetch Vendor Conversion Funnel data
const fetchVendorConversionFunnel = async () => {
  try {
    console.log(`📊 Fetching Vendor Conversion Funnel data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/vendor-conversion-funnel/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Vendor Conversion Funnel API Response:', response.data)
    
    if (response.data.success && response.data.vendor_conversion_funnel) {
      const data = response.data.vendor_conversion_funnel.funnel_stages
      
      if (data.length > 0) {
        // Transform data to match process flow format
        processFlowData.value = data.map(item => ({
          stage: item.stage,
          percentage: Math.round(item.percentage),
          count: item.count,
          description: item.description,
          color: item.color
        }))
        
        console.log(`✅ Vendor Conversion Funnel loaded:`, processFlowData.value)
        console.log(`📊 Summary:`, response.data.vendor_conversion_funnel.summary)
        console.log(`📊 Conversion Rate:`, response.data.vendor_conversion_funnel.summary.conversion_rate)
      } else {
        console.warn('⚠️ No vendor conversion funnel data available')
        processFlowData.value = []
      }
    } else {
      console.error('❌ Failed to load Vendor Conversion Funnel:', response.data)
      processFlowData.value = []
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Vendor Conversion Funnel:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    processFlowData.value = []
  }
}

const scoreDistributionData = ref([
  { label: "Cost", value: 8.2, full_label: "Cost Effectiveness", count: 45 },
  { label: "Quality", value: 8.5, full_label: "Quality of Service", count: 45 },
  { label: "Experience", value: 7.8, full_label: "Vendor Experience", count: 45 },
  { label: "Timeline", value: 8.0, full_label: "Project Timeline", count: 45 },
  { label: "Innovation", value: 7.5, full_label: "Innovation & Technology", count: 45 }
])

const consensusQualityData = ref({
  heatmap_data: [],
  overall_consensus: 0,
  summary: {
    total_evaluations: 0,
    total_criteria: 0,
    total_evaluators: 0,
    avg_consensus: 0,
    consensus_interpretation: 'No data available'
  }
})

// Fetch Consensus Quality data
const fetchConsensusQuality = async () => {
  try {
    console.log(`📊 Fetching Consensus Quality data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/consensus-quality/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Consensus Quality API Response:', response.data)
    
    if (response.data.success && response.data.consensus_quality) {
      const data = response.data.consensus_quality
      
      // Always set the data, even if empty
      consensusQualityData.value = data
      
      if (data.heatmap_data && data.heatmap_data.length > 0) {
        console.log(`✅ Consensus Quality loaded successfully!`)
        console.log(`📊 Overall Consensus: ${data.overall_consensus}`)
        console.log(`📊 Summary:`, data.summary)
        console.log(`📊 Interpretation: ${data.summary.consensus_interpretation}`)
      } else {
        console.warn('⚠️ No consensus quality heatmap data available')
        console.log(`📊 Message from API: ${response.data.message || 'No data'}`)
        console.log(`📊 Summary:`, data.summary)
        
        // Show the interpretation from the API
        if (data.summary && data.summary.consensus_interpretation) {
          console.log(`📊 Reason: ${data.summary.consensus_interpretation}`)
        }
      }
    } else {
      console.error('❌ Failed to load Consensus Quality:', response.data)
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Consensus Quality:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    
    // Set empty state on error
    consensusQualityData.value = {
      heatmap_data: [],
      overall_consensus: 0,
      summary: {
        total_evaluations: 0,
        total_criteria: 0,
        total_evaluators: 0,
        avg_consensus: 0,
        consensus_interpretation: 'Error loading consensus data'
      }
    }
  }
}

// Fetch Score Distribution data
const fetchScoreDistribution = async () => {
  try {
    console.log(`📊 Fetching Score Distribution data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/score-distribution/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Score Distribution API Response:', response.data)
    
    if (response.data.success && response.data.score_distribution) {
      const data = response.data.score_distribution.bar_chart_data
      
      if (data.length > 0) {
        // Transform data to match bar chart format
        scoreDistributionData.value = data.map(item => ({
          label: item.label,
          value: item.value,
          full_label: item.full_label,
          count: item.count
        }))
        
        console.log(`✅ Score Distribution loaded:`, scoreDistributionData.value)
        console.log(`📊 Summary:`, response.data.summary)
      } else {
        console.warn('⚠️ No score distribution data available, using fallback mock data')
        scoreDistributionData.value = [
          { label: "Cost", value: 8.2, full_label: "Cost Effectiveness", count: 45 },
          { label: "Quality", value: 8.5, full_label: "Quality of Service", count: 45 },
          { label: "Experience", value: 7.8, full_label: "Vendor Experience", count: 45 },
          { label: "Timeline", value: 8.0, full_label: "Project Timeline", count: 45 },
          { label: "Innovation", value: 7.5, full_label: "Innovation & Technology", count: 45 }
        ]
      }
    } else {
      console.warn('⚠️ Failed to load Score Distribution, using fallback mock data')
      scoreDistributionData.value = [
        { label: "Cost", value: 8.2, full_label: "Cost Effectiveness", count: 45 },
        { label: "Quality", value: 8.5, full_label: "Quality of Service", count: 45 },
        { label: "Experience", value: 7.8, full_label: "Vendor Experience", count: 45 },
        { label: "Timeline", value: 8.0, full_label: "Project Timeline", count: 45 },
        { label: "Innovation", value: 7.5, full_label: "Innovation & Technology", count: 45 }
      ]
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Score Distribution:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    scoreDistributionData.value = [
      { label: "Cost", value: 8.2, full_label: "Cost Effectiveness", count: 45 },
      { label: "Quality", value: 8.5, full_label: "Quality of Service", count: 45 },
      { label: "Experience", value: 7.8, full_label: "Vendor Experience", count: 45 },
      { label: "Timeline", value: 8.0, full_label: "Project Timeline", count: 45 },
      { label: "Innovation", value: 7.5, full_label: "Innovation & Technology", count: 45 }
    ]
  }
}

const criteriaEffectivenessData = ref({
  correlation_matrix: {
    criteria_names: [],
    matrix: []
  },
  criteria_importance: [],
  weight_effectiveness: [],
  summary: {
    total_criteria: 0,
    total_evaluations: 0,
    total_responses: 0,
    avg_correlation: 0,
    weight_alignment: 'No data available'
  }
})

// Fetch Criteria Effectiveness data
const fetchCriteriaEffectiveness = async () => {
  try {
    console.log(`📊 Fetching Criteria Effectiveness data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/criteria-effectiveness/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Criteria Effectiveness API Response:', response.data)
    
    if (response.data.success && response.data.criteria_effectiveness) {
      criteriaEffectivenessData.value = response.data.criteria_effectiveness
      
      console.log(`✅ Criteria Effectiveness loaded successfully!`)
      console.log(`📊 Total Criteria: ${criteriaEffectivenessData.value.summary.total_criteria}`)
      console.log(`📊 Average Correlation: ${criteriaEffectivenessData.value.summary.avg_correlation}`)
      console.log(`📊 Weight Alignment: ${criteriaEffectivenessData.value.summary.weight_alignment}`)
      console.log(`📊 Criteria Importance:`, criteriaEffectivenessData.value.criteria_importance)
    } else {
      console.error('❌ Failed to load Criteria Effectiveness:', response.data)
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Criteria Effectiveness:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
  }
}

const budgetVarianceData = ref([
  { category: "Under Budget", percentage: 42, description: "RFPs completed under estimated budget", color: "#10b981" },
  { category: "On Budget", percentage: 38, description: "RFPs completed within budget", color: "#3b82f6" },
  { category: "Over Budget", percentage: 20, description: "RFPs exceeded estimated budget", color: "#ef4444" }
])

// Fetch Budget Variance data
const fetchBudgetVariance = async () => {
  try {
    console.log(`📊 Fetching Budget Variance data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/budget-variance/`, {
      headers: getAuthHeaders()
    })
    
    console.log('📊 Budget Variance API Response:', response.data)
    
    if (response.data.success && response.data.budget_variance) {
      const data = response.data.budget_variance
      
      if (data.variance_categories && data.variance_categories.length > 0) {
        budgetVarianceData.value = data.variance_categories
        console.log(`✅ Budget Variance loaded successfully!`)
        console.log(`📊 Total RFPs: ${data.summary.total_rfps}`)
        console.log(`📊 Under Budget: ${data.summary.under_budget_count} (${data.summary.under_budget_percentage}%)`)
        console.log(`📊 On Budget: ${data.summary.on_budget_count} (${data.summary.on_budget_percentage}%)`)
        console.log(`📊 Over Budget: ${data.summary.over_budget_count} (${data.summary.over_budget_percentage}%)`)
        console.log(`📊 Summary:`, data.summary)
      } else {
        console.warn('⚠️ No budget variance data available, using fallback mock data')
        budgetVarianceData.value = [
          { category: "Under Budget", percentage: 42, description: "RFPs completed under estimated budget", color: "#10b981" },
          { category: "On Budget", percentage: 38, description: "RFPs completed within budget", color: "#3b82f6" },
          { category: "Over Budget", percentage: 20, description: "RFPs exceeded estimated budget", color: "#ef4444" }
        ]
      }
    } else {
      console.warn('⚠️ Failed to load Budget Variance, using fallback mock data')
      budgetVarianceData.value = [
        { category: "Under Budget", percentage: 42, description: "RFPs completed under estimated budget", color: "#10b981" },
        { category: "On Budget", percentage: 38, description: "RFPs completed within budget", color: "#3b82f6" },
        { category: "Over Budget", percentage: 20, description: "RFPs exceeded estimated budget", color: "#ef4444" }
      ]
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Budget Variance:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    budgetVarianceData.value = [
      { category: "Under Budget", percentage: 42, description: "RFPs completed under estimated budget", color: "#10b981" },
      { category: "On Budget", percentage: 38, description: "RFPs completed within budget", color: "#3b82f6" },
      { category: "Over Budget", percentage: 20, description: "RFPs exceeded estimated budget", color: "#ef4444" }
    ]
  }
}

const priceSpreadData = ref([
  { rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-001", spread_pct: 28.5, response_count: 8, min_price: 250000, max_price: 321250 },
  { rfp_title: "Security Services", rfp_number: "RFP-2024-002", spread_pct: 15.2, response_count: 6, min_price: 180000, max_price: 207360 },
  { rfp_title: "Software Licensing", rfp_number: "RFP-2024-003", spread_pct: 42.8, response_count: 12, min_price: 120000, max_price: 171360 },
  { rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", spread_pct: 35.1, response_count: 10, min_price: 95000, max_price: 128345 },
  { rfp_title: "Data Analytics", rfp_number: "RFP-2024-005", spread_pct: 22.3, response_count: 7, min_price: 210000, max_price: 256830 }
])

const priceSpreadSummary = ref({
  total_rfps: 45,
  rfps_with_multiple_bids: 28,
  avg_spread_pct: 28.8,
  overall_competitiveness: "Moderate Competition - Average spread of 28.8% indicates healthy vendor competition"
})

// Fetch Price Spread data
const fetchPriceSpread = async () => {
  try {
    console.log(`📊 Fetching Price Spread data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/price-spread/`, {
      params: { timeline: '6M' },
      headers: getAuthHeaders()
    })
    
    console.log('📊 Price Spread API Response:', response.data)
    
    if (response.data.success && response.data.price_spread) {
      const data = response.data.price_spread
      const summary = response.data.summary
      
      if (data && data.length > 0) {
        priceSpreadData.value = data
        priceSpreadSummary.value = summary
        console.log(`✅ Price Spread loaded successfully!`)
        console.log(`📊 Total RFPs: ${summary.total_rfps}`)
        console.log(`📊 RFPs with Multiple Bids: ${summary.rfps_with_multiple_bids}`)
        console.log(`📊 Avg Spread: ${summary.avg_spread_pct}%`)
        console.log(`📊 Overall Competitiveness: ${summary.overall_competitiveness}`)
        console.log(`📊 Summary:`, summary)
      } else {
        console.warn('⚠️ No price spread data available, using fallback mock data')
        priceSpreadData.value = [
          { rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-001", spread_pct: 28.5, response_count: 8, min_price: 250000, max_price: 321250 },
          { rfp_title: "Security Services", rfp_number: "RFP-2024-002", spread_pct: 15.2, response_count: 6, min_price: 180000, max_price: 207360 },
          { rfp_title: "Software Licensing", rfp_number: "RFP-2024-003", spread_pct: 42.8, response_count: 12, min_price: 120000, max_price: 171360 },
          { rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", spread_pct: 35.1, response_count: 10, min_price: 95000, max_price: 128345 },
          { rfp_title: "Data Analytics", rfp_number: "RFP-2024-005", spread_pct: 22.3, response_count: 7, min_price: 210000, max_price: 256830 }
        ]
        priceSpreadSummary.value = {
          total_rfps: 45,
          rfps_with_multiple_bids: 28,
          avg_spread_pct: 28.8,
          overall_competitiveness: "Moderate Competition - Average spread of 28.8% indicates healthy vendor competition"
        }
      }
    } else {
      console.warn('⚠️ Failed to load Price Spread, using fallback mock data')
      priceSpreadData.value = [
        { rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-001", spread_pct: 28.5, response_count: 8, min_price: 250000, max_price: 321250 },
        { rfp_title: "Security Services", rfp_number: "RFP-2024-002", spread_pct: 15.2, response_count: 6, min_price: 180000, max_price: 207360 },
        { rfp_title: "Software Licensing", rfp_number: "RFP-2024-003", spread_pct: 42.8, response_count: 12, min_price: 120000, max_price: 171360 },
        { rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", spread_pct: 35.1, response_count: 10, min_price: 95000, max_price: 128345 },
        { rfp_title: "Data Analytics", rfp_number: "RFP-2024-005", spread_pct: 22.3, response_count: 7, min_price: 210000, max_price: 256830 }
      ]
      priceSpreadSummary.value = {
        total_rfps: 45,
        rfps_with_multiple_bids: 28,
        avg_spread_pct: 28.8,
        overall_competitiveness: "Moderate Competition - Average spread of 28.8% indicates healthy vendor competition"
      }
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Price Spread:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    priceSpreadData.value = [
      { rfp_title: "Cloud Infrastructure", rfp_number: "RFP-2024-001", spread_pct: 28.5, response_count: 8, min_price: 250000, max_price: 321250 },
      { rfp_title: "Security Services", rfp_number: "RFP-2024-002", spread_pct: 15.2, response_count: 6, min_price: 180000, max_price: 207360 },
      { rfp_title: "Software Licensing", rfp_number: "RFP-2024-003", spread_pct: 42.8, response_count: 12, min_price: 120000, max_price: 171360 },
      { rfp_title: "Consulting Services", rfp_number: "RFP-2024-004", spread_pct: 35.1, response_count: 10, min_price: 95000, max_price: 128345 },
      { rfp_title: "Data Analytics", rfp_number: "RFP-2024-005", spread_pct: 22.3, response_count: 7, min_price: 210000, max_price: 256830 }
    ]
    priceSpreadSummary.value = {
      total_rfps: 45,
      rfps_with_multiple_bids: 28,
      avg_spread_pct: 28.8,
      overall_competitiveness: "Moderate Competition - Average spread of 28.8% indicates healthy vendor competition"
    }
  }
}

const processFunnelData = ref([
  { stage: "Draft", count: 120, percentage: 100, color: "#3b82f6" },
  { stage: "Pending Approval", count: 98, percentage: 82, color: "#8b5cf6" },
  { stage: "Approved", count: 85, percentage: 71, color: "#10b981" },
  { stage: "Published", count: 78, percentage: 65, color: "#f59e0b" },
  { stage: "Under Evaluation", count: 62, percentage: 52, color: "#ec4899" },
  { stage: "Awarded", count: 45, percentage: 38, color: "#14b8a6" },
  { stage: "Cancelled", count: 8, percentage: 7, color: "#ef4444" }
])

const processFunnelSummary = ref({
  total_rfps: 120,
  active_rfps: 62,
  awarded_count: 45,
  cancelled_count: 8,
  overall_conversion_rate: 38,
  completion_rate: 71,
  funnel_efficiency: "Good - 38% of RFPs reach award stage"
})

// Fetch Process Funnel data
const fetchProcessFunnel = async () => {
  try {
    console.log(`📊 Fetching Process Funnel data`)
    
    const response = await axios.get(`${API_BASE_URL}/kpi/process-funnel/`, {
      params: { timeline: '6M' },
      headers: getAuthHeaders()
    })
    
    console.log('📊 Process Funnel API Response:', response.data)
    
    if (response.data.success && response.data.funnel_data) {
      const data = response.data.funnel_data
      const summary = response.data.summary
      
      if (data && data.length > 0) {
        processFunnelData.value = data
        processFunnelSummary.value = summary
        console.log(`✅ Process Funnel loaded successfully!`)
        console.log(`📊 Total RFPs: ${summary.total_rfps}`)
        console.log(`📊 Overall Conversion Rate: ${summary.overall_conversion_rate}%`)
        console.log(`📊 Funnel Efficiency: ${summary.funnel_efficiency}`)
        console.log(`📊 Completion Rate: ${summary.completion_rate}%`)
        console.log(`📊 Summary:`, summary)
      } else {
        console.warn('⚠️ No process funnel data available, using fallback mock data')
        processFunnelData.value = [
          { stage: "Draft", count: 120, percentage: 100, color: "#3b82f6" },
          { stage: "Pending Approval", count: 98, percentage: 82, color: "#8b5cf6" },
          { stage: "Approved", count: 85, percentage: 71, color: "#10b981" },
          { stage: "Published", count: 78, percentage: 65, color: "#f59e0b" },
          { stage: "Under Evaluation", count: 62, percentage: 52, color: "#ec4899" },
          { stage: "Awarded", count: 45, percentage: 38, color: "#14b8a6" },
          { stage: "Cancelled", count: 8, percentage: 7, color: "#ef4444" }
        ]
        processFunnelSummary.value = {
          total_rfps: 120,
          active_rfps: 62,
          awarded_count: 45,
          cancelled_count: 8,
          overall_conversion_rate: 38,
          completion_rate: 71,
          funnel_efficiency: "Good - 38% of RFPs reach award stage"
        }
      }
    } else {
      console.warn('⚠️ Failed to load Process Funnel, using fallback mock data')
      processFunnelData.value = [
        { stage: "Draft", count: 120, percentage: 100, color: "#3b82f6" },
        { stage: "Pending Approval", count: 98, percentage: 82, color: "#8b5cf6" },
        { stage: "Approved", count: 85, percentage: 71, color: "#10b981" },
        { stage: "Published", count: 78, percentage: 65, color: "#f59e0b" },
        { stage: "Under Evaluation", count: 62, percentage: 52, color: "#ec4899" },
        { stage: "Awarded", count: 45, percentage: 38, color: "#14b8a6" },
        { stage: "Cancelled", count: 8, percentage: 7, color: "#ef4444" }
      ]
      processFunnelSummary.value = {
        total_rfps: 120,
        active_rfps: 62,
        awarded_count: 45,
        cancelled_count: 8,
        overall_conversion_rate: 38,
        completion_rate: 71,
        funnel_efficiency: "Good - 38% of RFPs reach award stage"
      }
    }
  } catch (error) {
    // Check for 403 error - redirect to access denied
    if (error.response?.status === 403) {
      const errorData = error.response.data || {}
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      return
    }
    
    console.error('❌ Error fetching Process Funnel:', error)
    console.error('❌ Error details:', error.response?.data || error.message)
    processFunnelData.value = [
      { stage: "Draft", count: 120, percentage: 100, color: "#3b82f6" },
      { stage: "Pending Approval", count: 98, percentage: 82, color: "#8b5cf6" },
      { stage: "Approved", count: 85, percentage: 71, color: "#10b981" },
      { stage: "Published", count: 78, percentage: 65, color: "#f59e0b" },
      { stage: "Under Evaluation", count: 62, percentage: 52, color: "#ec4899" },
      { stage: "Awarded", count: 45, percentage: 38, color: "#14b8a6" },
      { stage: "Cancelled", count: 8, percentage: 7, color: "#ef4444" }
    ]
    processFunnelSummary.value = {
      total_rfps: 120,
      active_rfps: 62,
      awarded_count: 45,
      cancelled_count: 8,
      overall_conversion_rate: 38,
      completion_rate: 71,
      funnel_efficiency: "Good - 38% of RFPs reach award stage"
    }
  }
}

const getTrendClass = (trend: string) => {
  if (trend === 'up') return 'text-green-600'
  if (trend === 'down') return 'text-blue-600'
  return 'text-gray-500'
}

// Export loading state
const exportLoading = ref(false)

// Helper function to capture chart element as image
const captureChart = async (element) => {
  if (!element) {
    console.warn('Chart element not found for capture')
    return null
  }
  
  try {
    const canvas = await html2canvas(element, {
      backgroundColor: '#ffffff',
      scale: 2, // Higher quality
      logging: false,
      useCORS: true,
      allowTaint: true
    })
    
    return canvas.toDataURL('image/png')
  } catch (error) {
    console.error('Error capturing chart:', error)
    return null
  }
}

// Helper function to find chart element by searching for text content
const findChartElement = (searchTerms) => {
  // Support both single search term or array
  const terms = Array.isArray(searchTerms) ? searchTerms : [searchTerms]
  
  // Find all chart containers
  const chartContainers = document.querySelectorAll('.bg-white.rounded-xl .p-6')
  
  for (const container of chartContainers) {
    // Find the parent card element
    const card = container.closest('.bg-white.rounded-xl')
    if (!card) continue
    
    // Check if card contains any of the search terms in its heading
    const heading = card.querySelector('h3')
    if (heading) {
      const headingText = heading.textContent || ''
      for (const term of terms) {
        if (headingText.includes(term)) {
          // Return the chart container (p-6 div)
          return container
        }
      }
    }
  }
  
  return null
}

// Export Report Function
const exportReport = async () => {
  exportLoading.value = true
  try {
    console.log('📊 Starting KPI Report Export...')
    
    // Wait a bit for charts to render
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Create new PDF document
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    let yPosition = 20
    const margin = 20
    const lineHeight = 7
    const sectionSpacing = 15
    const chartWidth = pageWidth - (2 * margin)
    const chartHeight = 80 // Height in mm
    
    // Helper function to check if new page needed
    const checkNewPage = (requiredSpace = 20) => {
      if (yPosition + requiredSpace > pageHeight - margin) {
        pdf.addPage()
        yPosition = margin
        return true
      }
      return false
    }
    
    // Helper function to add text with word wrap
    const addText = (text, fontSize = 12, isBold = false, color = [0, 0, 0]) => {
      if (text == null || text === '') return
      
      pdf.setFontSize(fontSize)
      pdf.setFont('helvetica', isBold ? 'bold' : 'normal')
      pdf.setTextColor(color[0], color[1], color[2])
      
      const safeText = String(text)
      const maxWidth = pageWidth - (2 * margin)
      const lines = pdf.splitTextToSize(safeText, maxWidth)
      
      lines.forEach((line) => {
        checkNewPage(lineHeight)
        if (line && line.trim() !== '') {
          pdf.text(line, margin, yPosition)
        }
        yPosition += lineHeight
      })
    }
    
    // Helper function to add a section header
    const addSectionHeader = (title) => {
      checkNewPage(sectionSpacing)
      yPosition += 5
      addText(title, 16, true, [0, 0, 0])
      yPosition += 5
      // Draw line under header
      pdf.setDrawColor(200, 200, 200)
      pdf.line(margin, yPosition, pageWidth - margin, yPosition)
      yPosition += 10
    }
    
    // Helper function to add chart image to PDF
    const addChart = async (chartTitle) => {
      try {
        const chartElement = findChartElement(chartTitle)
        if (!chartElement) {
          return false
        }
        
        // Check if element has content (not empty)
        if (chartElement.offsetWidth === 0 || chartElement.offsetHeight === 0) {
          return false
        }
        
        checkNewPage(chartHeight + 20)
        
        const imageData = await captureChart(chartElement)
        if (imageData) {
          // Calculate aspect ratio to maintain chart proportions
          const elementWidth = chartElement.offsetWidth
          const elementHeight = chartElement.offsetHeight
          const aspectRatio = elementHeight / elementWidth
          
          // Adjust height based on aspect ratio, but cap at reasonable size
          const adjustedHeight = Math.min(chartHeight, chartWidth * aspectRatio)
          
          pdf.addImage(imageData, 'PNG', margin, yPosition, chartWidth, adjustedHeight)
          yPosition += adjustedHeight + 10
          return true
        }
        return false
      } catch (error) {
        console.error('Error adding chart to PDF:', error)
        return false
      }
    }
    
    // Helper function to add a table row
    const addTableRow = (label, value, isHeader = false) => {
      checkNewPage(lineHeight)
      pdf.setFontSize(isHeader ? 11 : 10)
      pdf.setFont('helvetica', isHeader ? 'bold' : 'normal')
      pdf.setTextColor(isHeader ? 0 : 50, isHeader ? 0 : 50, isHeader ? 0 : 50)
      
      // Ensure label and value are valid strings
      const safeLabel = label != null ? String(label) : ''
      const safeValue = value != null ? String(value) : 'N/A'
      
      // Ensure values don't exceed page width
      const maxLabelWidth = pageWidth - margin - 80
      const labelLines = pdf.splitTextToSize(safeLabel, maxLabelWidth)
      
      if (labelLines.length > 1) {
        // Multi-line label
        pdf.text(labelLines[0], margin, yPosition)
        pdf.text(safeValue, pageWidth - margin - 50, yPosition, { align: 'right' })
        yPosition += lineHeight
        
        for (let i = 1; i < labelLines.length; i++) {
          checkNewPage(lineHeight)
          pdf.text(labelLines[i], margin, yPosition)
          yPosition += lineHeight
        }
      } else {
        // Single line
        pdf.text(safeLabel, margin, yPosition)
        pdf.text(safeValue, pageWidth - margin - 50, yPosition, { align: 'right' })
        yPosition += lineHeight + 2
      }
    }
    
    // ===== COVER PAGE =====
    pdf.setFillColor(59, 130, 246) // Blue
    pdf.rect(0, 0, pageWidth, 60, 'F')
    
    pdf.setTextColor(255, 255, 255)
    pdf.setFontSize(24)
    pdf.setFont('helvetica', 'bold')
    pdf.text('RFP Analytics Dashboard', pageWidth / 2, 35, { align: 'center' })
    
    pdf.setFontSize(14)
    pdf.setFont('helvetica', 'normal')
    pdf.text('Comprehensive Performance Report', pageWidth / 2, 45, { align: 'center' })
    
    pdf.setTextColor(0, 0, 0)
    pdf.setFontSize(10)
    yPosition = 80
    addText(`Generated on: ${new Date().toLocaleString()}`, 10, false, [100, 100, 100])
    
    // ===== SUMMARY KPIs =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('Executive Summary')
    
    if (summaryKPIs.value && summaryKPIs.value.length > 0) {
      summaryKPIs.value.forEach((kpi) => {
        const title = kpi.title || 'Unknown'
        const value = kpi.value != null ? String(kpi.value) : 'N/A'
        const change = kpi.change != null ? String(kpi.change) : ''
        addTableRow(title, `${value}${change ? ' (' + change + ')' : ''}`, false)
      })
    } else {
      addText('No summary data available', 10, false, [150, 150, 150])
    }
    
    // ===== RFP CREATION RATE =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('RFP Creation Rate')
    
    // Add chart
    await addChart('RFP Creation Rate')
    
    if (rfpCreationData.value && rfpCreationData.value.length > 0) {
      addText(`Timeline: ${selectedTimeline.value}`, 10, false, [100, 100, 100])
      yPosition += 5
      
      rfpCreationData.value.forEach((item) => {
        const month = item.month || 'Unknown'
        const year = item.year || ''
        const value = item.value != null ? item.value : 0
        addTableRow(`${month} ${year}`.trim(), `${value} RFPs`, false)
      })
      
      // Calculate summary
      const total = rfpCreationData.value.reduce((sum, item) => sum + (item.value || 0), 0)
      const avg = rfpCreationData.value.length > 0 ? total / rfpCreationData.value.length : 0
      yPosition += 5
      addText(`Total: ${total} RFPs | Average: ${avg.toFixed(1)} RFPs/month`, 10, true, [0, 0, 0])
    } else {
      addText('No creation rate data available', 10, false, [150, 150, 150])
    }
    
    // ===== RFP APPROVAL TIME =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('RFP Approval Time')
    
    await addChart('RFP Approval Time')
    
    if (approvalTimeData.value && approvalTimeData.value.length > 0) {
      addText(`Timeline: ${selectedApprovalTimeline.value}`, 10, false, [100, 100, 100])
      yPosition += 5
      
      approvalTimeData.value.forEach((item) => {
        const month = item.month || 'Unknown'
        const year = item.year || ''
        const value = item.value != null ? item.value : 0
        const count = item.count != null ? item.count : 0
        addTableRow(`${month} ${year}`.trim(), `${value.toFixed(1)} days (${count} RFPs)`, false)
      })
      
      const totalDays = approvalTimeData.value.reduce((sum, item) => sum + (item.value || 0), 0)
      const avgDays = approvalTimeData.value.length > 0 ? totalDays / approvalTimeData.value.length : 0
      const totalRFPs = approvalTimeData.value.reduce((sum, item) => sum + (item.count || 0), 0)
      yPosition += 5
      addText(`Average: ${avgDays.toFixed(1)} days | Total RFPs: ${totalRFPs}`, 10, true, [0, 0, 0])
    } else {
      addText('No approval time data available', 10, false, [150, 150, 150])
    }
    
    // ===== FIRST-TIME APPROVAL RATE =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('First-Time Approval Rate')
    
    await addChart('First-Time Approval Rate')
    
    const approvalRate = firstTimeApprovalRate.value != null ? firstTimeApprovalRate.value : 0
    addTableRow('Rate', `${approvalRate}%`, false)
    
    // ===== APPROVAL STAGE PERFORMANCE =====
    if (approvalStageData.value && approvalStageData.value.length > 0) {
      pdf.addPage()
      yPosition = margin
      addSectionHeader('Approval Stage Performance')
      
      await addChart('Approval Stage Performance')
      
      approvalStageData.value.forEach((item) => {
        const label = item.label || item.month || 'Unknown'
        const value = item.value != null ? item.value : 0
        addTableRow(label, `${value.toFixed(1)} days`, false)
      })
    }
    
    // ===== END-TO-END RFP CYCLE TIME =====
    if (ganttData.value && ganttData.value.length > 0) {
      pdf.addPage()
      yPosition = margin
      addSectionHeader('End-to-End RFP Cycle Time')
      
      await addChart('End-to-End RFP Cycle Time')
      
      if (lifecycleSummary.value) {
        yPosition += 5
        addTableRow('Total Cycle Time', `${lifecycleSummary.value.avg_total_cycle_days} days`, false)
        addTableRow('RFPs Analyzed', `${lifecycleSummary.value.total_rfps}`, false)
        if (lifecycleSummary.value.trend) {
          const trendText = lifecycleSummary.value.trend === 'down' ? '↓ Improving' : 
                           lifecycleSummary.value.trend === 'up' ? '↑ Increasing' : '→ Stable'
          const trendPct = lifecycleSummary.value.trend_percentage || 0
          addTableRow('Trend', `${trendText} (${trendPct > 0 ? '+' : ''}${trendPct}%)`, false)
        }
      }
      
      ganttData.value.forEach((item) => {
        const phase = item.phase || 'Unknown Phase'
        const duration = item.duration != null ? item.duration : 0
        const avgDays = item.avgDays != null ? item.avgDays : 0
        addTableRow(phase, `${duration}% (${avgDays} days)`, false)
      })
    }
    
    // ===== VENDOR METRICS =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('Vendor Performance')
    
    if (vendorResponseData.value && vendorResponseData.value.length > 0) {
      addText('Vendor Response Rate', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Vendor Response Rate')
      
      vendorResponseData.value.slice(0, 10).forEach((item) => {
        const title = item.rfp_title || item.rfp_number || 'Unknown RFP'
        const rate = item.response_rate != null ? item.response_rate : 0
        addTableRow(title, `${rate.toFixed(1)}%`, false)
      })
      yPosition += 5
    }
    
    // ===== NEW VS EXISTING VENDORS =====
    if (newVsExistingData.value && newVsExistingData.value.length > 0) {
      checkNewPage(sectionSpacing)
      addText('New vs Existing Vendors', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('New vs Existing Vendors')
      
      newVsExistingData.value.forEach((item) => {
        const month = item.month || 'Unknown'
        const year = item.year || ''
        const newVendors = item.new_vendors != null ? item.new_vendors : 0
        const existingVendors = item.existing_vendors != null ? item.existing_vendors : 0
        addTableRow(`${month} ${year}`.trim(), `New: ${newVendors}, Existing: ${existingVendors}`, false)
      })
      yPosition += 5
    }
    
    // ===== AWARD ACCEPTANCE RATE =====
    if (awardAcceptanceData.value && awardAcceptanceData.value.length > 0) {
      checkNewPage(sectionSpacing)
      addText('Award Acceptance Rate', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Award Acceptance Rate')
      
      awardAcceptanceData.value.forEach((item) => {
        const label = item.label || 'Unknown'
        const value = item.value != null ? item.value : 0
        const count = item.count != null ? item.count : 0
        addTableRow(label, `${value.toFixed(1)}% (${count} awards)`, false)
      })
      yPosition += 5
    }
    
    // ===== VENDOR CONVERSION FUNNEL =====
    if (processFlowData.value && processFlowData.value.length > 0) {
      pdf.addPage()
      yPosition = margin
      addSectionHeader('Vendor Conversion Funnel')
      
      processFlowData.value.forEach((item) => {
        const stage = item.stage || 'Unknown Stage'
        const percentage = item.percentage != null ? item.percentage : 0
        addTableRow(stage, `${percentage.toFixed(1)}%`, false)
      })
    }
    
    // ===== EVALUATION METRICS =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('Evaluation Analytics')
    
    // Reviewer Workload
    if (reviewerWorkloadData.value && reviewerWorkloadData.value.length > 0) {
      addText('Reviewer Workload', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Reviewer Workload')
      
      reviewerWorkloadData.value.slice(0, 10).forEach((item) => {
        const month = item.month || 'Unknown'
        const year = item.year || ''
        const value = item.value != null ? item.value : 0
        addTableRow(`${month} ${year}`.trim(), `${value} stages`, false)
      })
      yPosition += 5
    }
    
    // Evaluator Consistency
    if (evaluatorConsistencyData.value && evaluatorConsistencyData.value.evaluators && evaluatorConsistencyData.value.evaluators.length > 0) {
      checkNewPage(sectionSpacing)
      addText('Evaluator Consistency', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Evaluator Consistency')
      
      evaluatorConsistencyData.value.evaluators.slice(0, 5).forEach((evaluator) => {
        const name = evaluator.evaluator_name || 'Unknown Evaluator'
        const avgScore = evaluator.avg_score != null ? evaluator.avg_score : 0
        const consistency = evaluator.consistency_rating || 'N/A'
        addTableRow(name, `Avg: ${avgScore.toFixed(1)}, Consistency: ${consistency}`, false)
      })
      yPosition += 5
    }
    
    // Completion Time
    if (completionTimeData.value && completionTimeData.value.length > 0) {
      checkNewPage(sectionSpacing)
      addText('Evaluator Completion Time', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Completion Time')
      
      completionTimeData.value.slice(0, 10).forEach((item) => {
        const month = item.month || 'Unknown'
        const year = item.year || ''
        const value = item.value != null ? item.value : 0
        addTableRow(`${month} ${year}`.trim(), `${value.toFixed(1)} hours`, false)
      })
      yPosition += 5
    }
    
    // Score Distribution
    if (scoreDistributionData.value && scoreDistributionData.value.length > 0) {
      checkNewPage(sectionSpacing)
      addText('Score Distribution', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Score Distribution')
      
      scoreDistributionData.value.forEach((item) => {
        const label = item.label || item.range || 'Unknown Range'
        const value = item.value != null ? item.value : 0
        const percentage = item.percentage != null ? item.percentage : 0
        addTableRow(label, `${value} scores (${percentage.toFixed(1)}%)`, false)
      })
      yPosition += 5
    }
    
    // Consensus Quality
    if (consensusQualityData.value && consensusQualityData.value.heatmap_data) {
      checkNewPage(sectionSpacing)
      addText('Consensus Quality', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Consensus Quality')
      
      if (consensusQualityData.value.summary) {
        const overallConsensus = consensusQualityData.value.overall_consensus || 0
        const interpretation = consensusQualityData.value.summary.consensus_interpretation || 'N/A'
        addTableRow('Overall Consensus', `${(overallConsensus * 100).toFixed(1)}%`, false)
        addText(`Interpretation: ${interpretation}`, 10, false, [100, 100, 100])
        yPosition += 5
      }
    }
    
    // Criteria Effectiveness
    if (criteriaEffectivenessData.value && Object.keys(criteriaEffectivenessData.value).length > 0) {
      checkNewPage(sectionSpacing)
      addText('Criteria Effectiveness', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Criteria Effectiveness')
      
      if (criteriaEffectivenessData.value.criteria_importance && criteriaEffectivenessData.value.criteria_importance.length > 0) {
        criteriaEffectivenessData.value.criteria_importance.slice(0, 5).forEach((item) => {
          const name = item.criteria_name || 'Unknown Criteria'
          const correlation = item.correlation_with_final != null ? item.correlation_with_final : 0
          addTableRow(name, `Correlation: ${correlation.toFixed(3)}`, false)
        })
      }
      yPosition += 5
    }
    
    // Category Performance
    if (categoryPerformanceData.value && categoryPerformanceData.value.length > 0) {
      checkNewPage(sectionSpacing)
      addText('Category Performance', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Category Performance')
      
      categoryPerformanceData.value.slice(0, 10).forEach((item) => {
        const category = item.category || 'Unknown Category'
        const responseRate = item.response_rate != null ? item.response_rate : 0
        const quality = item.avg_quality_score != null ? item.avg_quality_score : 0
        addTableRow(category, `Response: ${responseRate.toFixed(1)}%, Quality: ${quality.toFixed(1)}`, false)
      })
      yPosition += 5
    }
    
    // ===== FINANCIAL & PROCESS EFFICIENCY =====
    pdf.addPage()
    yPosition = margin
    addSectionHeader('Financial & Process Efficiency')
    
    // Budget Variance
    if (budgetVarianceData.value && budgetVarianceData.value.length > 0) {
      addText('Budget Variance', 12, true, [0, 0, 0])
      yPosition += 3
      
      await addChart('Budget Variance')
      
      budgetVarianceData.value.forEach((item) => {
        const category = item.category || 'Unknown'
        const percentage = item.percentage != null ? item.percentage : 0
        const count = item.count != null ? item.count : 0
        addTableRow(category, `${percentage.toFixed(1)}% (${count} RFPs)`, false)
      })
      yPosition += 5
    }
    
    // Price Spread
    if (priceSpreadData.value && priceSpreadData.value.length > 0) {
      checkNewPage(sectionSpacing)
      addText('Price Spread', 12, true, [0, 0, 0])
      yPosition += 3
      
      if (priceSpreadSummary.value) {
        addTableRow('Average Spread', `${priceSpreadSummary.value.avg_spread_pct.toFixed(1)}%`, false)
        addTableRow('Overall Competitiveness', priceSpreadSummary.value.overall_competitiveness || 'N/A', false)
        yPosition += 3
      }
      
      priceSpreadData.value.slice(0, 10).forEach((item) => {
        const title = item.rfp_title || item.rfp_number || 'Unknown RFP'
        const spread = item.spread_pct != null ? item.spread_pct : 0
        const competitiveness = item.competitiveness || 'N/A'
        addTableRow(title, `${spread.toFixed(1)}% (${competitiveness})`, false)
      })
      yPosition += 5
    }
    
    // Process Funnel
    if (processFunnelData.value && processFunnelData.value.length > 0) {
      pdf.addPage()
      yPosition = margin
      addSectionHeader('RFP Process Funnel')
      
      await addChart('RFP Process Funnel')
      
      if (processFunnelSummary.value) {
        addTableRow('Total RFPs', `${processFunnelSummary.value.total_rfps}`, false)
        addTableRow('Overall Conversion Rate', `${processFunnelSummary.value.overall_conversion_rate.toFixed(1)}%`, false)
        addTableRow('Funnel Efficiency', processFunnelSummary.value.funnel_efficiency || 'N/A', false)
        addTableRow('Completion Rate', `${processFunnelSummary.value.completion_rate.toFixed(1)}%`, false)
        yPosition += 5
      }
      
      processFunnelData.value.forEach((item) => {
        const stage = item.stage || 'Unknown Stage'
        const count = item.count != null ? item.count : 0
        const percentage = item.percentage != null ? item.percentage : 0
        addTableRow(stage, `${count} RFPs (${percentage.toFixed(1)}%)`, false)
      })
    }
    
    // Save PDF
    const fileName = `RFP_Analytics_Report_${new Date().toISOString().split('T')[0]}.pdf`
    pdf.save(fileName)
    
    showSuccess('PDF report exported successfully!')
    console.log('✅ PDF Export completed successfully')
  } catch (error) {
    console.error('❌ Error exporting KPI report:', error)
    showError('Failed to export report. Please try again.')
  } finally {
    exportLoading.value = false
  }
}

// Enhanced Line Chart Component with Fixed Size and Dynamic Spacing
const LineChart = {
  props: ['data', 'timeline'],
  data() {
    return {
      hoveredIndex: null
    }
  },
  computed: {
    maxValue() {
      const max = Math.max(...this.data.map(d => d.value))
      // Add 20% padding to max value for better visualization
      return Math.ceil((max * 1.2) / 5) * 5 || 5
    },
    yAxisLabels() {
      const labels = []
      for (let i = 0; i <= 5; i++) {
        labels.push(Math.round((this.maxValue / 5) * i))
      }
      return labels.reverse()
    },
    // Fixed chart dimensions for professional look
    chartWidth() {
      return 700  // Fixed width
    },
    chartHeight() {
      return 320  // Fixed height
    },
    // Dynamic spacing based on number of data points
    xSpacing() {
      const usableWidth = this.chartWidth - 120  // Subtract margins
      const numGaps = Math.max(1, this.data.length - 1)
      return usableWidth / numGaps
    },
    // Calculate optimal font size and point size based on timeline
    scaleFactor() {
      const dataLength = this.data.length
      if (dataLength <= 3) return 1.2  // 3M - larger spacing
      if (dataLength <= 6) return 1.0  // 6M - normal spacing
      if (dataLength <= 12) return 0.8 // 1Y - smaller spacing
      return 0.6  // ALL - smallest spacing
    }
  },
  methods: {
    getYPosition(value) {
      const padding = 40
      const chartHeight = this.chartHeight - padding - 60
      const yPos = padding + (chartHeight - (value / this.maxValue) * chartHeight)
      return yPos
    },
    getXPosition(index) {
      const startX = 80
      return startX + (index * this.xSpacing)
    },
    handleMouseEnter(index) {
      this.hoveredIndex = index
    },
    handleMouseLeave() {
      this.hoveredIndex = null
    }
  },
  template: `
    <div class="relative">
      <!-- Chart container with fixed professional sizing -->
      <div class="h-[380px] bg-gradient-to-br from-slate-50 to-white rounded-lg p-6">
        <svg 
          class="w-full h-full" 
          :viewBox="'0 0 ' + chartWidth + ' ' + chartHeight" 
          @mouseleave="handleMouseLeave"
          preserveAspectRatio="xMidYMid meet"
        >
          <!-- Definitions -->
          <defs>
            <linearGradient id="lineAreaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.15" />
              <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.02" />
            </linearGradient>
          </defs>
          
          <!-- Horizontal grid lines -->
          <g v-for="(label, index) in yAxisLabels" :key="'grid-' + index">
            <line 
              x1="70" 
              :y1="40 + (index * 44)" 
              :x2="chartWidth - 40" 
              :y2="40 + (index * 44)" 
              stroke="#e5e7eb" 
              stroke-width="1"
              stroke-dasharray="5,5"
            />
          </g>
          
          <!-- Y-axis line -->
          <line x1="70" y1="40" x2="70" y2="260" stroke="#6b7280" stroke-width="2.5"/>
          
          <!-- X-axis line -->
          <line x1="70" y1="260" :x2="chartWidth - 40" y2="260" stroke="#6b7280" stroke-width="2.5"/>
          
          <!-- Y-axis title -->
          <text 
            x="20" 
            y="160" 
            class="text-sm fill-gray-700 font-semibold" 
            text-anchor="middle"
            transform="rotate(-90, 20, 160)"
          >
            Number of Stages
          </text>
          
          <!-- Y-axis labels -->
          <text 
            v-for="(label, index) in yAxisLabels" 
            :key="'y-label-' + index"
            x="60" 
            :y="44 + (index * 44)" 
            class="text-sm fill-gray-700 font-medium" 
            text-anchor="end"
          >
            {{ label }}
          </text>
          
          <!-- X-axis labels with dynamic sizing -->
          <g v-for="(item, index) in data" :key="'x-label-' + index">
            <text 
              :x="getXPosition(index)" 
              y="280" 
              :class="data.length > 12 ? 'text-xs' : 'text-sm'"
              class="fill-gray-700 font-medium" 
              text-anchor="middle"
            >
              {{ item.month }}
            </text>
            <!-- Tick marks -->
            <line 
              :x1="getXPosition(index)" 
              y1="260" 
              :x2="getXPosition(index)" 
              y2="267" 
              stroke="#6b7280" 
              stroke-width="2"
            />
          </g>
          
          <!-- X-axis title -->
          <text 
            :x="chartWidth / 2" 
            y="305" 
            class="text-sm fill-gray-700 font-semibold" 
            text-anchor="middle"
          >
            Month
          </text>
            
          
          <!-- Area fill under line -->
          <path
            v-if="data.length > 0"
            :d="'M ' + getXPosition(0) + ',' + getYPosition(data[0].value) + ' ' + 
                data.map((item, index) => 'L ' + getXPosition(index) + ',' + getYPosition(item.value)).join(' ') +
                ' L ' + getXPosition(data.length - 1) + ',260 L ' + getXPosition(0) + ',260 Z'"
            fill="url(#lineAreaGradient)"
          />
          
          <!-- Main line path -->
          <path
            v-if="data.length > 0"
            :d="'M ' + data.map((item, index) => {
              const x = getXPosition(index)
              const y = getYPosition(item.value)
              return index === 0 ? x + ',' + y : 'L ' + x + ',' + y
            }).join(' ')"
            fill="none"
            stroke="#3b82f6"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          
          <!-- Data points with hover interaction -->
          <g v-for="(item, index) in data" :key="'point-' + index">
            <!-- Large invisible hover area -->
            <circle
              :cx="getXPosition(index)"
              :cy="getYPosition(item.value)"
              :r="20 * scaleFactor"
              fill="transparent"
              @mouseenter="handleMouseEnter(index)"
              style="cursor: pointer;"
            />
            
            <!-- Outer ring on hover -->
            <circle
              v-if="hoveredIndex === index"
              :cx="getXPosition(index)"
              :cy="getYPosition(item.value)"
              :r="14 * scaleFactor"
              fill="none"
              stroke="#3b82f6"
              stroke-width="2"
              opacity="0.3"
            >
              <animate attributeName="r" from="0" :to="14 * scaleFactor" dur="0.3s" />
            </circle>
            
            <!-- Main data point -->
            <circle
              :cx="getXPosition(index)"
              :cy="getYPosition(item.value)"
              :r="(hoveredIndex === index ? 9 : 6) * scaleFactor"
              :fill="hoveredIndex === index ? '#3b82f6' : '#ffffff'"
              :stroke="hoveredIndex === index ? '#1d4ed8' : '#3b82f6'"
              :stroke-width="hoveredIndex === index ? 4 : 3"
              style="transition: all 0.2s ease;"
            />
          </g>
          
          <!-- Hover tooltip -->
          <g v-if="hoveredIndex !== null">
            <!-- Tooltip background -->
            <rect
              :x="getXPosition(hoveredIndex) - 70"
              :y="getYPosition(data[hoveredIndex].value) - 65"
              width="140"
              height="50"
              rx="8"
              fill="#1f2937"
              opacity="0.95"
              filter="drop-shadow(0 4px 6px rgba(0,0,0,0.2))"
            />
            
            <!-- Tooltip arrow -->
            <polygon
              :points="getXPosition(hoveredIndex) + ',' + (getYPosition(data[hoveredIndex].value) - 15) + ' ' +
                      (getXPosition(hoveredIndex) - 8) + ',' + (getYPosition(data[hoveredIndex].value) - 23) + ' ' +
                      (getXPosition(hoveredIndex) + 8) + ',' + (getYPosition(data[hoveredIndex].value) - 23)"
              fill="#1f2937"
              opacity="0.95"
            />
            
            <!-- Tooltip text -->
            <text
              :x="getXPosition(hoveredIndex)"
              :y="getYPosition(data[hoveredIndex].value) - 45"
              class="text-sm fill-white font-bold"
              text-anchor="middle"
            >
              {{ data[hoveredIndex].month }} {{ data[hoveredIndex].year }}
            </text>
            
            <text
              :x="getXPosition(hoveredIndex)"
              :y="getYPosition(data[hoveredIndex].value) - 28"
              class="text-xs fill-blue-300 font-semibold"
              text-anchor="middle"
            >
              {{ data[hoveredIndex].value }} Stages Created
            </text>
          </g>
        </svg>
      </div>
    </div>
  `
}

// Bar Chart Component with Tooltips
const BarChart = {
  props: ['data'],
  data() {
    return {
      hoveredIndex: null,
      tooltipX: 0,
      tooltipY: 0,
      tooltipOffsetX: 0,
      tooltipOffsetY: 0
    }
  },
  computed: {
    // Detect if data has 'month' or 'stage' field
    isStageData() {
      return this.data.length > 0 && this.data[0].hasOwnProperty('stage')
    },
    // Detect if data has 'new' and 'existing' fields (new vs existing vendors)
    isNewVsExisting() {
      return this.data.length > 0 && this.data[0].hasOwnProperty('new') && this.data[0].hasOwnProperty('existing')
    },
    labelField() {
      return this.isStageData ? 'stage' : 'month'
    },
    maxValue() {
      if (this.isNewVsExisting) {
        const max = Math.max(...this.data.map(d => (d.new || 0) + (d.existing || 0)))
        return Math.ceil(max / 5) * 5 || 5
      }
      const max = Math.max(...this.data.map(d => d.value))
      // Round up to nearest 5 for cleaner scale
      return Math.ceil(max / 5) * 5 || 5
    },
    yAxisLabels() {
      const labels = []
      const steps = 5
      for (let i = 0; i <= steps; i++) {
        labels.push(Math.round((this.maxValue / steps) * i))
      }
      return labels.reverse()
    },
    tooltipPosition() {
      // Tooltip dimensions
      const tooltipWidth = 130
      const tooltipHeight = this.isNewVsExisting ? 65 : 58
      const padding = 10
      
      // Calculate adjusted position to keep tooltip within bounds
      let adjustedX = this.tooltipX
      let adjustedY = this.tooltipY
      let arrowX = 0
      
      // Check right edge (SVG width is 350)
      if (this.tooltipX + tooltipWidth / 2 > 350 - padding) {
        adjustedX = 350 - tooltipWidth / 2 - padding
        arrowX = this.tooltipX - adjustedX
      }
      // Check left edge
      else if (this.tooltipX - tooltipWidth / 2 < padding) {
        adjustedX = tooltipWidth / 2 + padding
        arrowX = this.tooltipX - adjustedX
      }
      
      // Check bottom edge (SVG height is 200)
      if (this.tooltipY - tooltipHeight < padding) {
        adjustedY = this.tooltipY + tooltipHeight + 20 // Position below
      }
      // Check top edge
      else if (this.tooltipY < padding) {
        adjustedY = padding + tooltipHeight
      }
      
      return {
        x: adjustedX,
        y: adjustedY,
        arrowX: arrowX
      }
    }
  },
  methods: {
    handleMouseEnter(event, index) {
      this.hoveredIndex = index
      // Get mouse position relative to the SVG
      const svg = event.currentTarget.closest('svg')
      const rect = svg.getBoundingClientRect()
      this.tooltipX = event.clientX - rect.left
      this.tooltipY = event.clientY - rect.top
    },
    handleMouseLeave() {
      this.hoveredIndex = null
    }
  },
  template: `
    <div class="h-[260px] p-4 bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100 relative">
      <svg class="w-full h-full" viewBox="0 0 350 200" @mouseleave="handleMouseLeave">
        <!-- Subtle grid lines -->
        <defs>
          <pattern id="barGrid" width="50" height="40" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" stroke-width="0.5"/>
          </pattern>
          <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.1)"/>
          </filter>
        </defs>
        <rect width="100%" height="100%" fill="url(#barGrid)" />
        
        <!-- Y-axis line -->
        <line x1="50" y1="30" x2="50" y2="170" stroke="#6b7280" stroke-width="2"/>
        
        <!-- X-axis line -->
        <line x1="50" y1="170" x2="320" y2="170" stroke="#6b7280" stroke-width="2"/>
        
        <!-- Y-axis title -->
        <text x="15" y="100" class="text-xs fill-gray-700 font-semibold" text-anchor="middle" transform="rotate(-90, 15, 100)">
          Days
        </text>
        
        <!-- Y-axis labels and tick marks -->
        <g v-for="(label, index) in yAxisLabels" :key="'y-' + index">
          <!-- Tick mark -->
          <line 
            x1="50" 
            :y1="45 + (index * 28)" 
            x2="55" 
            :y2="45 + (index * 28)" 
            stroke="#6b7280" 
            stroke-width="2"
          />
          <!-- Label -->
          <text 
            x="45" 
            :y="45 + (index * 28)" 
            class="text-xs fill-gray-600 font-medium" 
            text-anchor="end"
          >
            {{ label }}
          </text>
        </g>
        
        <!-- X-axis title -->
        <text x="175" y="195" class="text-xs fill-gray-700 font-semibold" text-anchor="middle">
          {{ isStageData ? 'Stage' : 'Month' }}
        </text>
        
        <!-- X-axis labels and tick marks -->
        <g v-for="(item, index) in data" :key="'x-' + index">
          <!-- Tick mark -->
          <line 
            :x1="62.5 + (index * 50)" 
            y1="170" 
            :x2="62.5 + (index * 50)" 
            y2="175" 
            stroke="#6b7280" 
            stroke-width="2"
          />
          <!-- Label (month or stage) -->
          <text 
            :x="62.5 + (index * 50)" 
            y="185" 
            class="text-xs fill-gray-600 font-medium" 
            text-anchor="middle"
          >
            {{ item[labelField] }}
          </text>
        </g>
        
        <!-- Bars with rounded corners and hover effects -->
        <g v-for="(item, index) in data" :key="index">
          <!-- Invisible larger hit area for easier hovering -->
        <rect
            :x="45 + (index * 50)"
            :y="25"
            width="35"
            height="150"
            fill="transparent"
            @mouseenter="(e) => handleMouseEnter(e, index)"
            style="cursor: pointer;"
          />
          
          <!-- Stacked bars for new vs existing vendors -->
          <g v-if="isNewVsExisting">
            <!-- Glow effect for hovered bar -->
            <rect
              v-if="hoveredIndex === index"
              :x="48 + (index * 50)"
              :y="167 - ((((item.new || 0) + (item.existing || 0)) / maxValue) * 120)"
              width="29"
              :height="(((item.new || 0) + (item.existing || 0)) / maxValue) * 120 + 6"
              rx="4"
              fill="#3b82f6"
              opacity="0.2"
            />
            
            <!-- Existing vendors bar (bottom) -->
            <rect
              :x="50 + (index * 50)"
              :y="170 - (((item.existing || 0) / maxValue) * 120)"
              width="25"
              :height="((item.existing || 0) / maxValue) * 120"
              :fill="hoveredIndex === index ? '#2563eb' : '#3b82f6'"
              rx="3"
              ry="3"
              class="transition-all duration-300"
              :style="hoveredIndex === index ? 'filter: url(#shadow);' : ''"
            />
            
            <!-- New vendors bar (top) -->
            <rect
              :x="50 + (index * 50)"
              :y="170 - ((((item.new || 0) + (item.existing || 0)) / maxValue) * 120)"
              width="25"
              :height="((item.new || 0) / maxValue) * 120"
              :fill="hoveredIndex === index ? '#10b981' : '#059669'"
              rx="3"
              ry="3"
              class="transition-all duration-300"
              :style="hoveredIndex === index ? 'filter: url(#shadow);' : ''"
            />
            
            <!-- Value labels on top of bars -->
            <text
              :x="62.5 + (index * 50)"
              :y="165 - ((((item.new || 0) + (item.existing || 0)) / maxValue) * 120)"
              class="text-xs font-bold transition-all duration-300"
              :class="hoveredIndex === index ? 'fill-blue-800' : 'fill-gray-700'"
              text-anchor="middle"
            >
              {{ ((item.new || 0) + (item.existing || 0)).toFixed(0) }}
            </text>
          </g>
          
          <!-- Regular bars for other data -->
          <g v-else>
            <!-- Glow effect for hovered bar -->
            <rect
              v-if="hoveredIndex === index"
              :x="48 + (index * 50)"
              :y="167 - ((item.value / maxValue) * 120)"
              width="29"
              :height="(item.value / maxValue) * 120 + 6"
              rx="4"
              fill="#3b82f6"
              opacity="0.2"
            />
            
            <!-- Actual bar -->
            <rect
              :x="50 + (index * 50)"
              :y="170 - ((item.value / maxValue) * 120)"
              width="25"
              :height="(item.value / maxValue) * 120"
              :fill="hoveredIndex === index ? '#2563eb' : '#3b82f6'"
              rx="3"
              ry="3"
              class="transition-all duration-300"
              :style="hoveredIndex === index ? 'filter: url(#shadow);' : ''"
            />
            
            <!-- Value labels on top of bars -->
            <text
              :x="62.5 + (index * 50)"
              :y="165 - ((item.value / maxValue) * 120)"
              class="text-xs font-bold transition-all duration-300"
              :class="hoveredIndex === index ? 'fill-blue-800' : 'fill-gray-700'"
              text-anchor="middle"
            >
              {{ item.value.toFixed(1) }}
            </text>
          </g>
        </g>
        
        <!-- Tooltip -->
        <g v-if="hoveredIndex !== null">
          <!-- Tooltip background -->
          <rect
            :x="tooltipPosition.x - 65"
            :y="tooltipPosition.y - (isNewVsExisting ? 70 : 58)"
            width="130"
            :height="isNewVsExisting ? 65 : 58"
            rx="6"
            fill="#1f2937"
            opacity="0.95"
            filter="url(#shadow)"
          />
          
          <!-- Tooltip arrow (positioned relative to mouse, not tooltip center) -->
          <polygon
            :points="tooltipX + ',' + (tooltipPosition.y - 5) + ' ' + (tooltipX - 6) + ',' + (tooltipPosition.y - 11) + ' ' + (tooltipX + 6) + ',' + (tooltipPosition.y - 11)"
            fill="#1f2937"
            opacity="0.95"
          />
          
          <!-- New vs Existing Vendors tooltip -->
          <template v-if="isNewVsExisting">
            <text
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 55"
              class="text-xs fill-white font-semibold"
              text-anchor="middle"
            >
              {{ data[hoveredIndex][labelField] }}{{ isStageData ? '' : ' ' + (data[hoveredIndex].year || new Date().getFullYear()) }}
            </text>
            <text
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 38"
              class="text-base fill-white font-bold"
              text-anchor="middle"
            >
              {{ ((data[hoveredIndex].new || 0) + (data[hoveredIndex].existing || 0)).toFixed(0) }} Total Vendors
            </text>
            
            <text
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 24"
              class="text-xs fill-green-300"
              text-anchor="middle"
            >
              New: {{ (data[hoveredIndex].new || 0).toFixed(0) }} • Existing: {{ (data[hoveredIndex].existing || 0).toFixed(0) }}
            </text>
            
            <text
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 12"
              class="text-xs fill-gray-400"
              text-anchor="middle"
            >
              Vendor participation breakdown
            </text>
          </template>
          
          <!-- Regular tooltip for other data (similar to LineChart style) -->
          <template v-else>
            <!-- Month and Year (similar to LineChart) -->
            <text
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 45"
              class="text-sm fill-white font-bold"
              text-anchor="middle"
            >
              {{ data[hoveredIndex][labelField] }}{{ isStageData ? '' : ' ' + (data[hoveredIndex].year || new Date().getFullYear()) }}
            </text>
            
            <!-- Value (similar to LineChart style) -->
            <text
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 28"
              class="text-xs fill-blue-300 font-semibold"
              text-anchor="middle"
            >
              {{ data[hoveredIndex].value.toFixed(1) }} {{ isStageData ? 'days' : 'days' }}
            </text>
            
            <!-- Additional info (count of RFPs) -->
            <text
              v-if="!isStageData && data[hoveredIndex].count"
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 12"
              class="text-xs fill-gray-400"
              text-anchor="middle"
            >
              Based on {{ data[hoveredIndex].count }} RFP{{ data[hoveredIndex].count !== 1 ? 's' : '' }}
            </text>
            
            <text
              v-else-if="isStageData"
              :x="tooltipPosition.x"
              :y="tooltipPosition.y - 12"
              class="text-xs fill-gray-400"
              text-anchor="middle"
            >
              Average time at stage
            </text>
          </template>
        </g>
      </svg>
    </div>
  `
}

// Donut Chart Component with Tooltip
const DonutChart = {
  props: ['value'],
  data() {
    return {
      isHovered: false
    }
  },
  computed: {
    circumference() {
      return 2 * Math.PI * 40 // radius = 40
    },
    strokeDasharray() {
      const offset = this.circumference - (this.value / 100) * this.circumference
      return `${this.circumference} ${this.circumference}`
    },
    strokeDashoffset() {
      const offset = this.circumference - (this.value / 100) * this.circumference
      return offset
    }
  },
  template: `
    <div class="flex flex-col items-center justify-center h-[240px] bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100 p-4">
      <div class="relative w-28 h-28 mb-4" @mouseenter="isHovered = true" @mouseleave="isHovered = false">
        <svg class="w-28 h-28 transform -rotate-90 transition-transform duration-300" :class="isHovered ? 'scale-110' : ''" viewBox="0 0 100 100">
          <!-- Background circle -->
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#e2e8f0"
            stroke-width="8"
          />
          <!-- Progress circle with animation -->
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="#3b82f6"
            stroke-width="8"
            :stroke-dasharray="strokeDasharray"
            :stroke-dashoffset="strokeDashoffset"
            stroke-linecap="round"
            class="transition-all duration-1000 ease-out"
            :class="isHovered ? 'stroke-blue-600' : ''"
          />
        </svg>
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <span class="text-2xl font-bold text-gray-900 transition-colors duration-300" :class="isHovered ? 'text-blue-700' : ''">{{ value }}%</span>
          </div>
        </div>
      </div>
      
      <!-- Additional metrics -->
      <div class="text-center space-y-1">
        <div class="text-xs font-semibold text-gray-700">First-Time Approval Rate</div>
        <div class="text-xs text-gray-500">Approved on first submission</div>
      </div>
      
      <!-- Tooltip on hover -->
      <div v-if="isHovered" class="absolute bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg mt-4 z-10">
        <div class="font-bold">{{ value }}% First-Time Approval</div>
        <div class="text-gray-300 mt-1">Approved without revisions</div>
      </div>
    </div>
  `
}

// Scatter Plot Component
const ScatterPlot = {
  props: ['data'],
  data() {
    return {
      hoveredIndex: null,
      tooltipX: 0,
      tooltipY: 0
    }
  },
  computed: {
    maxX() {
      return Math.max(...this.data.map(d => d.x), 100)
    },
    maxY() {
      return Math.max(...this.data.map(d => d.y), 10)
    }
  },
  methods: {
    handleMouseEnter(event, index) {
      this.hoveredIndex = index
      const svg = event.currentTarget.closest('svg')
      const rect = svg.getBoundingClientRect()
      this.tooltipX = event.clientX - rect.left
      this.tooltipY = event.clientY - rect.top
    },
    handleMouseLeave() {
      this.hoveredIndex = null
    },
    getXPosition(x) {
      return 80 + ((x / this.maxX) * 400)
    },
    getYPosition(y) {
      return 40 + ((this.maxY - y) / this.maxY) * 200
    }
  },
  template: `
    <div class="h-[320px] p-6 bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100">
      <svg class="w-full h-full" viewBox="0 0 600 280" @mouseleave="handleMouseLeave" preserveAspectRatio="xMidYMid meet">
        <!-- Subtle grid lines -->
        <defs>
          <pattern id="scatterGrid" width="80" height="40" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#scatterGrid)" />
        
        <!-- Y-axis line -->
        <line x1="80" y1="40" x2="80" y2="240" stroke="#6b7280" stroke-width="2"/>
        
        <!-- X-axis line -->
        <line x1="80" y1="240" x2="520" y2="240" stroke="#6b7280" stroke-width="2"/>
        
        <!-- Y-axis title -->
        <text x="20" y="145" class="text-sm fill-gray-700 font-bold" text-anchor="middle" transform="rotate(-90, 20, 145)">
          Quality Score (0-10)
        </text>
        
        <!-- Y-axis labels -->
        <text x="75" y="45" class="text-sm fill-gray-700 font-semibold" text-anchor="end">10</text>
        <text x="75" y="65" class="text-sm fill-gray-700 font-semibold" text-anchor="end">8</text>
        <text x="75" y="85" class="text-sm fill-gray-700 font-semibold" text-anchor="end">6</text>
        <text x="75" y="105" class="text-sm fill-gray-700 font-semibold" text-anchor="end">4</text>
        <text x="75" y="125" class="text-sm fill-gray-700 font-semibold" text-anchor="end">2</text>
        <text x="75" y="245" class="text-sm fill-gray-700 font-semibold" text-anchor="end">0</text>
        
        <!-- Y-axis grid lines -->
        <line x1="80" y1="40" x2="520" y2="40" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="5,5"/>
        <line x1="80" y1="60" x2="520" y2="60" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="5,5"/>
        <line x1="80" y1="80" x2="520" y2="80" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="5,5"/>
        <line x1="80" y1="100" x2="520" y2="100" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="5,5"/>
        <line x1="80" y1="120" x2="520" y2="120" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="5,5"/>
        
        <!-- X-axis title -->
        <text x="300" y="275" class="text-sm fill-gray-700 font-bold" text-anchor="middle">
          Response Rate (%)
        </text>
        
        <!-- X-axis labels -->
        <text x="80" y="260" class="text-sm fill-gray-700 font-semibold" text-anchor="middle">0%</text>
        <text x="160" y="260" class="text-sm fill-gray-700 font-semibold" text-anchor="middle">25%</text>
        <text x="240" y="260" class="text-sm fill-gray-700 font-semibold" text-anchor="middle">50%</text>
        <text x="320" y="260" class="text-sm fill-gray-700 font-semibold" text-anchor="middle">75%</text>
        <text x="400" y="260" class="text-sm fill-gray-700 font-semibold" text-anchor="middle">100%</text>
        
        <!-- X-axis tick marks -->
        <line x1="80" y1="240" x2="80" y2="245" stroke="#6b7280" stroke-width="2"/>
        <line x1="160" y1="240" x2="160" y2="245" stroke="#6b7280" stroke-width="2"/>
        <line x1="240" y1="240" x2="240" y2="245" stroke="#6b7280" stroke-width="2"/>
        <line x1="320" y1="240" x2="320" y2="245" stroke="#6b7280" stroke-width="2"/>
        <line x1="400" y1="240" x2="400" y2="245" stroke="#6b7280" stroke-width="2"/>
        <line x1="480" y1="240" x2="480" y2="245" stroke="#6b7280" stroke-width="2"/>
        
        <!-- Scatter points -->
        <g v-for="(item, index) in data" :key="index">
          <!-- Hover area -->
          <circle
            :cx="getXPosition(item.x)"
            :cy="getYPosition(item.y)"
            r="20"
            fill="transparent"
            @mouseenter="(e) => handleMouseEnter(e, index)"
            style="cursor: pointer;"
          />
          
          <!-- Glow effect on hover -->
          <circle
            v-if="hoveredIndex === index"
            :cx="getXPosition(item.x)"
            :cy="getYPosition(item.y)"
            r="10"
            fill="#10b981"
            opacity="0.3"
          >
            <animate attributeName="r" from="0" to="10" dur="0.3s" />
          </circle>
          
          <!-- Actual point -->
          <circle
            :cx="getXPosition(item.x)"
            :cy="getYPosition(item.y)"
            :r="hoveredIndex === index ? 8 : 6"
            :fill="hoveredIndex === index ? '#059669' : '#10b981'"
            stroke="#ffffff"
            :stroke-width="hoveredIndex === index ? 4 : 3"
            style="transition: all 0.2s ease;"
          />
        </g>
        
        <!-- Tooltip -->
        <g v-if="hoveredIndex !== null">
          <!-- Tooltip background - larger and more readable -->
          <rect
            :x="tooltipX - 120"
            :y="tooltipY - 110"
            width="240"
            height="100"
            rx="8"
            fill="#1f2937"
            opacity="0.98"
            filter="drop-shadow(0 8px 16px rgba(0,0,0,0.3))"
          />
          
          <!-- Tooltip arrow -->
          <polygon
            :points="tooltipX + ',' + (tooltipY - 10) + ' ' + (tooltipX - 8) + ',' + (tooltipY - 18) + ' ' + (tooltipX + 8) + ',' + (tooltipY - 18)"
            fill="#1f2937"
            opacity="0.98"
          />
          
          <!-- Tooltip content - larger text -->
          <text
            :x="tooltipX"
            :y="tooltipY - 85"
            class="text-sm fill-white font-bold"
            text-anchor="middle"
          >
            {{ data[hoveredIndex].category || data[hoveredIndex].rfp_title || 'RFP ' + data[hoveredIndex].rfp_number }}
          </text>
          
          <text
            :x="tooltipX"
            :y="tooltipY - 65"
            class="text-sm fill-blue-400 font-semibold"
            text-anchor="middle"
          >
            Response Rate: {{ data[hoveredIndex].response_rate || data[hoveredIndex].x }}%
          </text>
          
          <text
            :x="tooltipX"
            :y="tooltipY - 45"
            class="text-sm fill-green-400 font-semibold"
            text-anchor="middle"
          >
            Quality Score: {{ data[hoveredIndex].y.toFixed(1) }}/10
          </text>
          
          <text
            :x="tooltipX"
            :y="tooltipY - 25"
            class="text-sm fill-gray-300 font-medium"
            text-anchor="middle"
          >
            {{ data[hoveredIndex].responses || 0 }} responses / {{ data[hoveredIndex].invitations || 0 }} invited
            <tspan v-if="data[hoveredIndex].vendor_count" dy="14" x="tooltipX">({{ data[hoveredIndex].vendor_count }} vendors)</tspan>
          </text>
        </g>
      </svg>
    </div>
  `
}

// Pie Chart Component with Enhanced Display
const PieChart = {
  props: ['data'],
  data() {
    return {
      hoveredIndex: null
    }
  },
  computed: {
    totalValue() {
      return this.data.reduce((sum, item) => sum + item.value, 0)
    }
  },
  methods: {
    getStrokeDashArray(value) {
      return `${value * 2.51} 251`
    },
    getStrokeDashOffset(index) {
      let offset = 0
      for (let i = 0; i < index; i++) {
        offset -= this.data[i].value * 2.51
      }
      return offset
    }
  },
  template: `
    <div class="h-[200px] p-4 bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100">
      <div class="flex items-center justify-center h-full">
        <div class="relative w-24 h-24" @mouseleave="hoveredIndex = null">
          <svg class="w-24 h-24" viewBox="0 0 100 100">
            <g v-for="(item, index) in data" :key="index">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                :stroke="item.color"
                stroke-width="12"
                :stroke-dasharray="getStrokeDashArray(item.value)"
                :stroke-dashoffset="getStrokeDashOffset(index)"
                stroke-linecap="round"
                :class="hoveredIndex === index ? 'opacity-100' : 'opacity-80'"
                @mouseenter="hoveredIndex = index"
                style="cursor: pointer; transition: all 0.3s ease;"
              />
            </g>
          </svg>
          
          <!-- Center text -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="text-center">
              <div class="text-lg font-bold text-gray-900">{{ totalValue.toFixed(0) }}%</div>
              <div class="text-xs text-gray-500">Total</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Legend with counts -->
      <div class="mt-4 space-y-2">
        <div v-for="(item, index) in data" :key="index" 
             class="flex items-center justify-between text-xs"
             :class="hoveredIndex === index ? 'font-bold' : ''"
             @mouseenter="hoveredIndex = index"
             @mouseleave="hoveredIndex = null"
             style="cursor: pointer;">
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: item.color }"></div>
            <span class="text-gray-700">{{ item.label }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="font-semibold text-gray-900">{{ item.value.toFixed(1) }}%</span>
            <span class="text-gray-500">({{ item.count }})</span>
          </div>
        </div>
      </div>
    </div>
  `
}

// Box Plot Component
const BoxPlot = {
  props: ['data'],
  template: `
    <div class="space-y-6 p-4 bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100">
      <div class="text-center">
        <h4 class="text-sm font-medium text-gray-600 mb-2">Box Plot Analysis</h4>
        <p class="text-xs text-gray-500">Score distribution by criteria</p>
      </div>
      <div class="space-y-4">
        <div v-for="(item, index) in data" :key="index" class="flex items-center space-x-6">
          <div class="w-24 text-sm font-medium text-gray-700 text-right">{{ item.criteria }}</div>
          <div class="flex-1 relative h-3 bg-gray-100 rounded-full overflow-hidden">
            <div 
              class="absolute h-3 bg-blue-500 rounded-full"
              :style="{
                left: (item.q1 / 10) * 100 + '%',
                width: ((item.q3 - item.q1) / 10) * 100 + '%'
              }"
            />
            <div 
              class="absolute w-1 h-5 bg-emerald-500 -top-1 rounded-full"
              :style="{ left: (item.median / 10) * 100 + '%' }"
            />
            <div 
              class="absolute w-0.5 h-3 bg-blue-700 rounded-full"
              :style="{ left: (item.min / 10) * 100 + '%' }"
            />
            <div 
              class="absolute w-0.5 h-3 bg-blue-700 rounded-full"
              :style="{ left: (item.max / 10) * 100 + '%' }"
            />
          </div>
        </div>
      </div>
    </div>
  `
}

// Heatmap Component
const Heatmap = {
  props: ['data'],
  computed: {
    heatmapValues() {
      if (!this.data || !this.data.heatmap_data || this.data.heatmap_data.length === 0) {
        // Return empty grid if no data
        return []
      }
      
      // Flatten the 2D array into a 1D array for rendering
      const values = []
      for (const row of this.data.heatmap_data) {
        for (const cell of row) {
          values.push(cell.value)
        }
      }
      return values
    },
    hasData() {
      return this.data && this.data.heatmap_data && this.data.heatmap_data.length > 0
    },
    overallConsensus() {
      return this.data?.overall_consensus || 0
    },
    interpretation() {
      return this.data?.summary?.consensus_interpretation || 'No data available'
    }
  },
  template: `
    <div class="p-4 bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100">
      <div class="text-center mb-6">
        <h4 class="text-sm font-medium text-gray-600 mb-2">Evaluator Consensus Heatmap</h4>
        <p class="text-xs text-gray-500">Agreement levels across evaluators and criteria</p>
        <div v-if="hasData" class="mt-3 flex items-center justify-center gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ (overallConsensus * 100).toFixed(1) }}%</div>
            <div class="text-xs text-gray-500">Overall Consensus</div>
          </div>
          <div class="h-8 w-px bg-gray-300"></div>
          <div class="text-xs text-gray-600 max-w-xs text-center">{{ interpretation }}</div>
        </div>
      </div>
      
      <div v-if="!hasData" class="flex flex-col items-center justify-center py-12 px-4">
        <div class="text-center max-w-md">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No Consensus Data Available</h3>
          <p class="mt-2 text-sm text-gray-600">{{ interpretation }}</p>
          <div v-if="data && data.summary" class="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p class="text-xs text-blue-800 font-medium mb-1">Current Status:</p>
            <ul class="text-xs text-blue-700 space-y-1 text-left">
              <li v-if="data.summary.total_evaluations > 0">• Total Evaluations: {{ data.summary.total_evaluations }}</li>
              <li v-if="data.summary.total_evaluators > 0">• Evaluators: {{ data.summary.total_evaluators }}</li>
              <li v-if="data.summary.total_criteria > 0">• Criteria: {{ data.summary.total_criteria }}</li>
            </ul>
          </div>
          <p class="mt-4 text-xs text-gray-500">💡 <strong>Tip:</strong> To see consensus data, ensure multiple evaluators score the same criteria for the same proposals.</p>
        </div>
      </div>
      
      <div v-else class="grid grid-cols-5 gap-2">
        <div
          v-for="(value, index) in heatmapValues"
          :key="index"
          class="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold text-white shadow-sm hover:scale-110 transition-transform cursor-help"
          :style="{ backgroundColor: 'hsl(214, ' + Math.round(value * 100) + '%, 60%)' }"
          :title="'Consensus: ' + (value * 100).toFixed(0) + '%'"
        >
          {{ value.toFixed(1) }}
        </div>
      </div>
      
      <div v-if="hasData" class="mt-4 flex items-center justify-between text-xs text-gray-500">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-blue-400"></div>
          <span>High Consensus (0.8-1.0)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-blue-300"></div>
          <span>Medium (0.5-0.8)</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded bg-blue-200"></div>
          <span>Low (0.0-0.5)</span>
        </div>
      </div>
    </div>
  `
}

// Correlation Matrix Component
const CorrelationMatrix = {
  props: ['data'],
  computed: {
    hasData() {
      return this.data && 
             this.data.correlation_matrix && 
             this.data.correlation_matrix.matrix && 
             this.data.correlation_matrix.matrix.length > 0
    },
    criteriaNames() {
      return this.data?.correlation_matrix?.criteria_names || []
    },
    matrix() {
      return this.data?.correlation_matrix?.matrix || []
    },
    summary() {
      return this.data?.summary || {}
    },
    weightAlignment() {
      return this.summary.weight_alignment || 'No data available'
    },
    avgCorrelation() {
      return this.summary.avg_correlation || 0
    }
  },
  template: `
    <div class="p-4 bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100">
      <div class="text-center mb-6">
        <h4 class="text-sm font-medium text-gray-600 mb-2">Correlation Matrix</h4>
        <p class="text-xs text-gray-500">Criteria relationship analysis</p>
        <div v-if="hasData" class="mt-3 flex items-center justify-center gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ avgCorrelation.toFixed(2) }}</div>
            <div class="text-xs text-gray-500">Avg Correlation</div>
          </div>
          <div class="h-8 w-px bg-gray-300"></div>
          <div class="text-xs text-gray-600 max-w-xs text-center">{{ weightAlignment }}</div>
        </div>
      </div>
      
      <div v-if="!hasData" class="flex flex-col items-center justify-center py-12 px-4">
        <div class="text-center max-w-md">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No Criteria Effectiveness Data Available</h3>
          <p class="mt-2 text-sm text-gray-600">Criteria effectiveness data will appear here once evaluations are completed.</p>
          <p class="mt-4 text-xs text-gray-500">💡 <strong>Tip:</strong> To see criteria effectiveness analysis, ensure RFPs have been evaluated with multiple criteria.</p>
        </div>
      </div>
      
      <div v-else>
        <div class="grid gap-2" :style="{ gridTemplateColumns: 'auto ' + 'repeat(' + criteriaNames.length + ', minmax(0, 1fr))' }">
          <!-- Header row -->
          <div></div>
          <div v-for="(name, index) in criteriaNames" :key="'header-' + index" 
               class="text-xs text-center font-bold text-gray-700 p-2 truncate" 
               :title="name">
            {{ name.length > 10 ? name.substring(0, 10) + '...' : name }}
          </div>
          
          <!-- Data rows -->
          <div v-for="(row, rowIndex) in matrix" :key="'row-' + rowIndex" class="contents">
            <div class="text-xs font-bold text-gray-700 p-2 truncate" 
                 :title="criteriaNames[rowIndex]">
              {{ criteriaNames[rowIndex].length > 10 ? criteriaNames[rowIndex].substring(0, 10) + '...' : criteriaNames[rowIndex] }}
            </div>
            <div
              v-for="(value, colIndex) in row"
              :key="'cell-' + rowIndex + '-' + colIndex"
              class="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold text-white shadow-sm hover:scale-110 transition-transform cursor-help"
              :style="{ backgroundColor: 'hsl(214, ' + Math.round(Math.abs(value) * 100) + '%, 60%)' }"
              :title="criteriaNames[rowIndex] + ' vs ' + criteriaNames[colIndex] + ': ' + value.toFixed(3)"
            >
              {{ value.toFixed(2) }}
            </div>
          </div>
        </div>
        
        <!-- Legend -->
        <div class="mt-4 flex items-center justify-center gap-4 text-xs text-gray-500">
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded bg-blue-400"></div>
            <span>High Correlation (0.8-1.0)</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded bg-blue-300"></div>
            <span>Medium (0.5-0.8)</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded bg-blue-200"></div>
            <span>Low (0.0-0.5)</span>
          </div>
        </div>
      </div>
    </div>
  `
}
</script>

<style scoped>
/* Professional KPI Dashboard Styling */

/* Enhanced card styling with professional shadows */
.phase-card {
  @apply bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300;
}

/* Improved hover effects */
.phase-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Professional gradient backgrounds */
.bg-gradient-to-br {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
}

/* Enhanced spacing system */
.space-y-6 > * + * {
  margin-top: 2rem;
}

.space-y-8 > * + * {
  margin-top: 2.5rem;
}

/* Professional grid layouts */
.grid {
  gap: 2rem;
}

@media (min-width: 768px) {
  .grid {
    gap: 2rem;
  }
}

@media (min-width: 1024px) {
  .grid {
    gap: 2.5rem;
  }
}

/* Enhanced typography */
.text-muted-foreground {
  @apply text-gray-600;
}

/* Professional color scheme */
.text-primary {
  @apply text-blue-600;
}

.text-success {
  @apply text-emerald-600;
}

.text-warning {
  @apply text-amber-600;
}

.text-danger {
  @apply text-red-600;
}

/* Smooth transitions for all interactive elements */
* {
  transition: all 0.2s ease-in-out;
}

/* Professional border styling */
.border-border {
  @apply border-gray-200;
}

/* Enhanced shadow system */
.shadow-professional {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.shadow-professional-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Professional section dividers */
.section-divider {
  @apply border-t border-gray-200 my-8;
}

/* Enhanced focus states */
.focus-ring {
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}

/* Professional button styling */
.btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg transition-colors;
}

.btn-secondary {
  @apply bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg transition-colors;
}

/* Chart container enhancements */
.chart-container {
  @apply bg-gradient-to-br from-slate-50 to-white rounded-lg border border-gray-100 p-4;
}

/* Professional tooltip styling */
.tooltip {
  @apply absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg opacity-0 transition-opacity;
}

.tooltip.show {
  @apply opacity-100;
}

/* Responsive design improvements */
@media (max-width: 768px) {
  .grid {
    gap: 1rem;
  }
  
  .space-y-6 > * + * {
    margin-top: 1.5rem;
  }
}

/* Print-friendly styles */
@media print {
  .no-print {
    display: none !important;
  }
  
  .phase-card {
    @apply shadow-none border border-gray-300;
  }
}
</style>

