<template>
  <div class="dashboard-container">
    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <div class="error-content">
        <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <span>{{ error }}</span>
        <button @click="loadDashboardData" class="retry-btn">Retry</button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !dashboardData" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">Loading dashboard data...</p>
    </div>

    <!-- Dashboard Content -->
    <div v-if="dashboardData" class="dashboard-content">
      <!-- Key Metrics Row -->
      <div class="metrics-grid">
        <!-- Plan Metrics -->
        <div class="metric-card">
          <div class="metric-header">
            <div class="metric-icon plan-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14,2 14,8 20,8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
            </div>
            <h3 class="metric-title">Plans</h3>
          </div>
          <div class="metric-content">
            <div class="metric-main">
              <div class="metric-value">{{ dashboardData.plan_metrics?.total_plans || 0 }}</div>
              <div class="metric-change positive">+8%</div>
              <!-- Debug info for development -->
              <div v-if="!dashboardData.plan_metrics?.total_plans && dataSource !== 'mock'" style="font-size: 10px; color: red; margin-top: 4px;">
                🚨 No data
              </div>
            </div>
            <div class="metric-details">
              <div class="metric-detail-item">
                <span class="detail-label">BCP:</span>
                <span class="detail-value">{{ dashboardData.plan_metrics?.bcp_plans || 0 }}</span>
              </div>
              <div class="metric-detail-item">
                <span class="detail-label">DRP:</span>
                <span class="detail-value">{{ dashboardData.plan_metrics?.drp_plans || 0 }}</span>
              </div>
              <div class="metric-detail-item">
                <span class="detail-label">Approved:</span>
                <span class="detail-value">{{ dashboardData.plan_metrics?.approved_plans || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Evaluation Metrics -->
        <div class="metric-card">
          <div class="metric-header">
            <div class="metric-icon evaluation-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11H5a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0-7H9a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0 0v3c0 1.1-.9 2-2 2h-4m0-5H9a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0 0v3c0 1.1-.9 2-2 2h-4"/>
              </svg>
            </div>
            <h3 class="metric-title">Evaluations</h3>
          </div>
          <div class="metric-content">
            <div class="metric-main">
              <div class="metric-value">{{ dashboardData.evaluation_metrics?.total_evaluations || 0 }}</div>
              <div class="metric-change positive">+5%</div>
            </div>
            <div class="metric-details">
              <div class="metric-detail-item">
                <span class="detail-label">Avg Score:</span>
                <span class="detail-value">{{ dashboardData.evaluation_metrics?.avg_overall_score || 0 }}%</span>
              </div>
              <div class="metric-detail-item">
                <span class="detail-label">Completed:</span>
                <span class="detail-value">{{ dashboardData.evaluation_metrics?.submitted_evaluations || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Testing Metrics -->
        <div class="metric-card">
          <div class="metric-header">
            <div class="metric-icon testing-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12,6 12,12 16,14"></polyline>
              </svg>
            </div>
            <h3 class="metric-title">Tests</h3>
          </div>
          <div class="metric-content">
            <div class="metric-main">
              <div class="metric-value">{{ dashboardData.testing_metrics?.total_assignments || 0 }}</div>
              <div class="metric-change positive">+12%</div>
            </div>
            <div class="metric-details">
              <div class="metric-detail-item">
                <span class="detail-label">Success Rate:</span>
                <span class="detail-value">{{ dashboardData.testing_metrics?.success_rate || 0 }}%</span>
              </div>
              <div class="metric-detail-item">
                <span class="detail-label">Overdue:</span>
                <span class="detail-value">{{ dashboardData.testing_metrics?.overdue_assignments || 0 }}</span>
              </div>
            </div>
          </div>
        </div>


        <!-- Approval Metrics -->
        <div class="metric-card">
          <div class="metric-header">
            <div class="metric-icon approval-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22,4 12,14.01 9,11.01"></polyline>
              </svg>
            </div>
            <h3 class="metric-title">Approvals</h3>
          </div>
          <div class="metric-content">
            <div class="metric-main">
              <div class="metric-value">{{ dashboardData.approval_metrics?.total_approvals || 0 }}</div>
              <div class="metric-change positive">+3%</div>
            </div>
            <div class="metric-details">
              <div class="metric-detail-item">
                <span class="detail-label">Completion:</span>
                <span class="detail-value">{{ dashboardData.approval_metrics?.completion_rate || 0 }}%</span>
              </div>
              <div class="metric-detail-item">
                <span class="detail-label">Overdue:</span>
                <span class="detail-value">{{ dashboardData.approval_metrics?.overdue_approvals || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- User Activity Metrics -->
        <div class="metric-card">
          <div class="metric-header">
            <div class="metric-icon user-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <h3 class="metric-title">Users</h3>
          </div>
          <div class="metric-content">
            <div class="metric-main">
              <div class="metric-value">{{ dashboardData.user_metrics?.active_users || 0 }}</div>
              <div class="metric-change negative">-2%</div>
            </div>
            <div class="metric-details">
              <div class="metric-detail-item">
                <span class="detail-label">Total:</span>
                <span class="detail-value">{{ dashboardData.user_metrics?.total_users || 0 }}</span>
              </div>
              <div class="metric-detail-item">
                <span class="detail-label">Active:</span>
                <span class="detail-value">{{ dashboardData.user_metrics?.recent_activity || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Section - First Row (Plan Status & Risk Priority) -->
      <div class="charts-section charts-section--two-columns">
        <!-- Plan Status Distribution -->
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">Plan Status Distribution</h3>
            <div class="chart-actions">
              <button class="btn btn--sm btn--outline" @click="exportChart('plan-status')">Export</button>
            </div>
          </div>
          <div class="chart-content">
            <!-- Debug info for plan status -->
            <div v-if="planStatusSlices.length === 0 && dashboardData" style="position: absolute; top: 10px; right: 10px; font-size: 10px; color: orange; background: rgba(255,255,255,0.8); padding: 4px; border-radius: 4px;">
              🐛 No status data: {{ JSON.stringify(dashboardData.plan_metrics?.status_distribution || 'undefined') }}
            </div>
            
            <div v-if="planStatusSlices.length > 0" class="donut-chart-container">
              <svg class="donut-chart" viewBox="0 0 500 500">
                <!-- Donut chart will be rendered here -->
                <g class="donut-chart-group">
                  <!-- Chart slices will be generated dynamically -->
                  <circle
                    v-for="(slice, index) in planStatusSlices"
                    :key="`slice-${index}`"
                    :cx="250"
                    :cy="250"
                    :r="120"
                    :stroke="slice.color"
                    :stroke-width="80"
                    :stroke-dasharray="getDonutSliceDashArray(slice)"
                    :stroke-dashoffset="getDonutSliceOffset(index)"
                    fill="none"
                    class="donut-slice"
                    @mouseenter="showSliceTooltip($event, slice)"
                    @mouseleave="hideSliceTooltip"
                  />
                  
                  <!-- Percentage labels for each slice -->
                  <text
                    v-for="(slice, index) in planStatusSlices"
                    :key="`percentage-${index}`"
                    :x="getPercentageLabelX(slice, index)"
                    :y="getPercentageLabelY(slice, index)"
                    text-anchor="middle"
                    font-size="18"
                    font-weight="700"
                    fill="white"
                    class="percentage-label"
                  >
                    {{ slice.percentage.toFixed(1) }}%
                  </text>
                  
                </g>
              </svg>
              
              <!-- Legend -->
              <div class="donut-legend">
                <div 
                  v-for="(slice, index) in planStatusSlices" 
                  :key="`legend-${index}`" 
                  class="legend-item"
                >
                  <div class="legend-dot" :style="{ backgroundColor: slice.color }"></div>
                  <span class="legend-label">{{ slice.label }}</span>
                  <span class="legend-value">{{ slice.count }}</span>
                </div>
              </div>
            </div>
            
            <!-- No data placeholder -->
            <div v-else class="chart-placeholder">
              <div class="chart-placeholder-content">
                <svg class="chart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p class="chart-placeholder-text">No plan status data available</p>
                <p class="chart-placeholder-subtext">Plans will appear here once they are submitted</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Risk Priority Distribution -->
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">Risk Priority Distribution</h3>
            <div class="chart-actions">
              <button class="btn btn--sm btn--outline" @click="exportChart('risk-priority')">Export</button>
            </div>
          </div>
          <div class="chart-content">
            <div class="risk-chart-container">
              <svg class="bar-chart" viewBox="0 0 500 250">
                <!-- Grid lines -->
                <defs>
                  <pattern id="riskGrid" width="60" height="28" patternUnits="userSpaceOnUse">
                    <path d="M 60 0 L 0 0 0 28" fill="none" stroke="#f1f5f9" stroke-width="1"/>
                  </pattern>
                </defs>
                <rect width="500" height="250" fill="url(#riskGrid)" />
                
                <!-- Y-axis -->
                <line x1="60" y1="30" x2="60" y2="220" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- X-axis -->
                <line x1="60" y1="220" x2="460" y2="220" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- Bars -->
                <!-- Critical: 3 -->
                <rect x="100" y="200" width="70" height="20" fill="#ef4444" rx="6"/>
                <!-- High: 13 -->
                <rect x="190" y="140" width="70" height="80" fill="#f59e0b" rx="6"/>
                <!-- Medium: 92 -->
                <rect x="280" y="30" width="70" height="190" fill="#3b82f6" rx="6"/>
                <!-- Low: 12 -->
                <rect x="370" y="160" width="70" height="60" fill="#10b981" rx="6"/>
                
                <!-- Bar values -->
                <text x="135" y="215" text-anchor="middle" font-size="12" font-weight="bold" fill="#1f2937">3</text>
                <text x="225" y="175" text-anchor="middle" font-size="12" font-weight="bold" fill="#1f2937">13</text>
                <text x="315" y="65" text-anchor="middle" font-size="12" font-weight="bold" fill="#1f2937">92</text>
                <text x="405" y="195" text-anchor="middle" font-size="12" font-weight="bold" fill="#1f2937">12</text>
                
                <!-- Y-axis labels -->
                <text x="55" y="45" text-anchor="end" font-size="10" fill="#64748b">100</text>
                <text x="55" y="80" text-anchor="end" font-size="10" fill="#64748b">75</text>
                <text x="55" y="115" text-anchor="end" font-size="10" fill="#64748b">50</text>
                <text x="55" y="150" text-anchor="end" font-size="10" fill="#64748b">25</text>
                <text x="55" y="225" text-anchor="end" font-size="10" fill="#64748b">0</text>
                
                <!-- X-axis labels -->
                <text x="135" y="240" text-anchor="middle" font-size="10" fill="#64748b">Critical</text>
                <text x="225" y="240" text-anchor="middle" font-size="10" fill="#64748b">High</text>
                <text x="315" y="240" text-anchor="middle" font-size="10" fill="#64748b">Medium</text>
                <text x="405" y="240" text-anchor="middle" font-size="10" fill="#64748b">Low</text>
              </svg>
              
              <!-- Risk Priority Legend -->
              <div class="risk-legend">
                <div class="legend-item">
                  <div class="legend-dot" style="background-color: #ef4444;"></div>
                  <span class="legend-label">Critical</span>
                  <span class="legend-value">3</span>
                </div>
                <div class="legend-item">
                  <div class="legend-dot" style="background-color: #f59e0b;"></div>
                  <span class="legend-label">High</span>
                  <span class="legend-value">13</span>
                </div>
                <div class="legend-item">
                  <div class="legend-dot" style="background-color: #3b82f6;"></div>
                  <span class="legend-label">Medium</span>
                  <span class="legend-value">92</span>
                </div>
                <div class="legend-item">
                  <div class="legend-dot" style="background-color: #10b981;"></div>
                  <span class="legend-label">Low</span>
                  <span class="legend-value">12</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Enhanced Monthly Trends - Full Width Row -->
      <div class="charts-section charts-section--full-width">
        <!-- Enhanced Monthly Activity Trends -->
        <div class="chart-card chart-card--full-width">
          <div class="chart-header">
            <h3 class="chart-title">Monthly Activity Trends</h3>
            <div class="chart-actions">
              <button class="btn btn--sm btn--outline" @click="exportMonthlyTrends">Export</button>
              <button class="btn btn--sm btn--outline" @click="refreshTrendsData">Refresh</button>
            </div>
          </div>

          <div class="chart-content chart-content--full-width">
            <!-- Enhanced Chart Container with Two-Column Layout -->
            <div class="enhanced-line-chart-container trends-layout-two-column">
              
              <!-- Left Side: Chart Visualization -->
              <div class="chart-visualization trends-chart-main">
                <svg class="enhanced-line-chart" :viewBox="`0 0 ${chartDimensions.width} ${chartDimensions.height}`">
                  <!-- Chart Background and Grid -->
                 <defs>
                    <pattern :id="`enhancedGrid-${chartId}`" width="40" height="30" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#f1f5f9" stroke-width="1"/>
                   </pattern>
                    <!-- Gradient definitions for area charts -->
                    <linearGradient id="plansGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.3" />
                      <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.05" />
                    </linearGradient>
                    <linearGradient id="evaluationsGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" style="stop-color:#10b981;stop-opacity:0.3" />
                      <stop offset="100%" style="stop-color:#10b981;stop-opacity:0.05" />
                    </linearGradient>
                    <linearGradient id="testsGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:0.3" />
                      <stop offset="100%" style="stop-color:#f59e0b;stop-opacity:0.05" />
                    </linearGradient>
                 </defs>
                  <rect :width="chartDimensions.width" :height="chartDimensions.height" :fill="`url(#enhancedGrid-${chartId})`" />
                 
                 <!-- Y-axis -->
                  <line x1="80" y1="40" :x2="80" :y2="chartDimensions.height - 60" stroke="#e2e8f0" stroke-width="2"/>
                 
                 <!-- X-axis -->
                  <line x1="80" :y1="chartDimensions.height - 60" :x2="chartDimensions.width - 40" :y2="chartDimensions.height - 60" stroke="#e2e8f0" stroke-width="2"/>
                  
                  <!-- Y-axis labels -->
                  <text v-for="(label, index) in trendsYAxisLabels" :key="`y-label-${index}`"
                        x="75" :y="getTrendsYAxisLabelPosition(index)" text-anchor="end" font-size="12" fill="#64748b">
                    {{ label }}
                  </text>
                  
                  <!-- X-axis labels -->
                  <text v-for="(label, index) in trendsXAxisLabels" :key="`x-label-${index}`"
                        :x="getTrendsXAxisLabelPosition(index)" :y="chartDimensions.height - 40" text-anchor="middle" font-size="12" fill="#64748b">
                    {{ label }}
                  </text>
                  
                  <!-- Area charts (if selected) -->
                  <g v-if="selectedViewMode === 'area'">
                    <path v-for="(area, index) in areaPaths" :key="`area-${index}`"
                          :d="area.path" 
                          :fill="area.gradient" 
                          opacity="0.6" 
                          class="area-path"/>
                  </g>
                  
                  <!-- Moving average lines -->
                  <g v-if="selectedMovingAverage !== 'none'">
                    <polyline v-for="(line, index) in movingAverageLines" :key="`ma-line-${index}`"
                              :points="line.points"
                   fill="none" 
                              :stroke="line.color"
                              stroke-width="2"
                              stroke-dasharray="5,5"
                              opacity="0.7"/>
                  </g>
                  
                  <!-- Main trend lines -->
                  <g v-for="(line, index) in trendLines" :key="`trend-line-${index}`">
                    <polyline :points="line.points"
                   fill="none" 
                              :stroke="line.color"
                   stroke-width="4"
                              class="trend-line"/>
                  </g>
                  
                  <!-- Interactive data points -->
                  <g v-for="(point, pointIndex) in interactiveDataPoints" :key="`point-${pointIndex}`">
                    <circle :cx="point.x" 
                            :cy="point.y" 
                            r="6" 
                            :fill="point.color" 
                            stroke="#ffffff" 
                            stroke-width="3"
                            class="data-point"
                            @mouseenter="showDataPointTooltip($event, point)"
                            @mouseleave="hideDataPointTooltip"
                            @click="drillDownToDataPoint(point)"/>
                    
                    <!-- Hover state circle -->
                    <circle :cx="point.x" 
                            :cy="point.y" 
                            r="12" 
                            fill="transparent"
                            class="data-point-hover"
                            @mouseenter="showDataPointTooltip($event, point)"
                            @mouseleave="hideDataPointTooltip"/>
                  </g>
                </svg>
               
                <!-- Interactive Tooltip -->
                <div v-if="tooltip.visible" 
                     class="chart-tooltip"
                     :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
                  <div class="tooltip-header">
                    <h4 class="tooltip-title">{{ tooltip.title }}</h4>
                    <span class="tooltip-subtitle">{{ tooltip.subtitle }}</span>
                  </div>
                  <div class="tooltip-content">
                    <div class="tooltip-metric" v-for="metric in tooltip.metrics" :key="metric.name">
                      <div class="metric-row">
                        <div class="metric-info">
                          <div class="metric-dot" :style="{ backgroundColor: metric.color }"></div>
                          <span class="metric-name">{{ metric.name }}</span>
                  </div>
                        <div class="metric-value">{{ metric.value }}</div>
                </div>
                      <div class="metric-change" v-if="metric.change" :class="metric.changeClass">
                        <span class="change-icon">{{ metric.changeIcon }}</span>
                        <span class="change-text">{{ metric.change }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="tooltip-actions">
                    <button class="tooltip-btn" @click="drillDownToDataPoint(tooltip.pointData)">Drill Down</button>
                  </div>
                </div>
              </div>

              <!-- Right Side: Activity Metrics -->
              <div class="trends-sidebar">
                <!-- Enhanced Legend with Statistics -->
                <div class="enhanced-legend">
                  <div class="legend-header">
                    <h4>Activity Metrics</h4>
                    <div class="legend-stats">
                      <span class="stat-item">Total: {{ totalActivityCount }}</span>
                      <span class="stat-item">Avg/Month: {{ averageMonthlyActivity }}</span>
                    </div>
                  </div>
                  
                  <div class="legend-items">
                    <div v-for="(item, index) in enhancedLegendItems" :key="`legend-${index}`" class="legend-item">
                      <div class="legend-main">
                        <div class="legend-line" :style="{ backgroundColor: item.color }"></div>
                        <span class="legend-label">{{ item.name }}</span>
                        <span class="legend-value">{{ item.currentValue }}</span>
                      </div>
                      <div class="legend-details">
                        <div class="detail-row">
                          <span class="detail-label">Trend:</span>
                          <span class="detail-value" :class="item.trendClass">{{ item.trendIcon }} {{ item.trendText }}</span>
                        </div>
                        <div class="detail-row">
                          <span class="detail-label">Peak:</span>
                          <span class="detail-value">{{ item.peakValue }} ({{ item.peakMonth }})</span>
                        </div>
                        <div class="detail-row">
                          <span class="detail-label">Growth:</span>
                          <span class="detail-value" :class="item.growthClass">{{ item.growthRate }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Section - Second Row (Evaluation Score & Questionnaire Status) -->
      <div class="charts-section charts-section--two-columns">

        <!-- Evaluation Score Distribution - Horizontal Bar Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">Evaluation Score Distribution</h3>
            <div class="chart-actions">
              <button class="btn btn--sm btn--outline" @click="exportChart('evaluation-scores')">Export</button>
            </div>
          </div>
          <div class="chart-content">
            <div class="horizontal-bar-chart-container">
              <svg class="horizontal-bar-chart" viewBox="0 0 600 300">
                <!-- Grid lines -->
                <defs>
                  <pattern id="evalGrid" width="60" height="30" patternUnits="userSpaceOnUse">
                    <path d="M 60 0 L 0 0 0 30" fill="none" stroke="#f1f5f9" stroke-width="1"/>
                  </pattern>
                </defs>
                <rect width="600" height="300" fill="url(#evalGrid)" />
                
                <!-- Y-axis -->
                <line x1="100" y1="40" x2="100" y2="240" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- X-axis -->
                <line x1="100" y1="240" x2="550" y2="240" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- Horizontal bars -->
                <!-- Excellent (90-100) -->
                <rect x="100" y="50" :width="getEvaluationBarWidth('excellent')" height="35" fill="#10b981" rx="4"/>
                <text x="95" y="72" text-anchor="end" font-size="12" fill="#64748b">Excellent</text>
                <text x="105" y="72" font-size="12" font-weight="bold" fill="#1f2937">{{ dashboardData.evaluation_metrics?.score_distribution?.excellent || 25 }}</text>
                
                <!-- Good (80-89) -->
                <rect x="100" y="95" :width="getEvaluationBarWidth('good')" height="35" fill="#3b82f6" rx="4"/>
                <text x="95" y="117" text-anchor="end" font-size="12" fill="#64748b">Good</text>
                <text x="105" y="117" font-size="12" font-weight="bold" fill="#1f2937">{{ dashboardData.evaluation_metrics?.score_distribution?.good || 35 }}</text>
                
                <!-- Fair (70-79) -->
                <rect x="100" y="140" :width="getEvaluationBarWidth('fair')" height="35" fill="#f59e0b" rx="4"/>
                <text x="95" y="162" text-anchor="end" font-size="12" fill="#64748b">Fair</text>
                <text x="105" y="162" font-size="12" font-weight="bold" fill="#1f2937">{{ dashboardData.evaluation_metrics?.score_distribution?.fair || 15 }}</text>
                
                <!-- Poor (Below 70) -->
                <rect x="100" y="185" :width="getEvaluationBarWidth('poor')" height="35" fill="#ef4444" rx="4"/>
                <text x="95" y="207" text-anchor="end" font-size="12" fill="#64748b">Poor</text>
                <text x="105" y="207" font-size="12" font-weight="bold" fill="#1f2937">{{ dashboardData.evaluation_metrics?.score_distribution?.poor || 5 }}</text>
                
                <!-- X-axis labels -->
                <text x="150" y="255" text-anchor="middle" font-size="11" fill="#64748b">10</text>
                <text x="250" y="255" text-anchor="middle" font-size="11" fill="#64748b">20</text>
                <text x="350" y="255" text-anchor="middle" font-size="11" fill="#64748b">30</text>
                <text x="450" y="255" text-anchor="middle" font-size="11" fill="#64748b">40</text>
                
                <!-- Chart title -->
                <text x="300" y="25" text-anchor="middle" font-size="14" font-weight="600" fill="#374151">Score Range Distribution</text>
              </svg>
            </div>
          </div>
        </div>

        <!-- Questionnaire Status Distribution - Stacked Bar Chart -->
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">Questionnaire Status Distribution</h3>
            <div class="chart-actions">
              <button class="btn btn--sm btn--outline" @click="exportChart('questionnaire-status')">Export</button>
            </div>
          </div>
          <div class="chart-content">
            <div class="stacked-bar-chart-container">
              <svg class="stacked-bar-chart" viewBox="0 0 500 320">
                <!-- Grid lines -->
                <defs>
                  <pattern id="questionnaireGrid" width="50" height="32" patternUnits="userSpaceOnUse">
                    <path d="M 50 0 L 0 0 0 32" fill="none" stroke="#f1f5f9" stroke-width="1"/>
                  </pattern>
                </defs>
                <rect width="500" height="320" fill="url(#questionnaireGrid)" />
                
                <!-- Y-axis -->
                <line x1="80" y1="40" x2="80" y2="260" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- X-axis -->
                <line x1="80" y1="260" x2="450" y2="260" stroke="#e2e8f0" stroke-width="2"/>
                
                <!-- Stacked bars for each questionnaire type -->
                <!-- BCP Questionnaires -->
                <g class="bcp-stack">
                  <rect x="120" :y="260 - getQuestionnaireBarHeight('BCP')" width="60" :height="getQuestionnaireBarHeight('BCP')" fill="#3b82f6" rx="6"/>
                  <text x="150" y="125" text-anchor="middle" font-size="11" font-weight="bold" fill="#1f2937">BCP</text>
                  <text x="150" :y="260 - getQuestionnaireBarHeight('BCP')/2 + 5" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">{{ dashboardData.testing_metrics?.questionnaire_type_dist?.BCP || 12 }}</text>
                </g>
                
                <!-- DRP Questionnaires -->
                <g class="drp-stack">
                  <rect x="220" :y="260 - getQuestionnaireBarHeight('DRP')" width="60" :height="getQuestionnaireBarHeight('DRP')" fill="#10b981" rx="6"/>
                  <text x="250" y="125" text-anchor="middle" font-size="11" font-weight="bold" fill="#1f2937">DRP</text>
                  <text x="250" :y="260 - getQuestionnaireBarHeight('DRP')/2 + 5" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">{{ dashboardData.testing_metrics?.questionnaire_type_dist?.DRP || 12 }}</text>
                </g>
                
                <!-- Y-axis labels -->
                <text x="70" y="70" text-anchor="end" font-size="11" fill="#64748b">20</text>
                <text x="70" y="120" text-anchor="end" font-size="11" fill="#64748b">15</text>
                <text x="70" y="170" text-anchor="end" font-size="11" fill="#64748b">10</text>
                <text x="70" y="220" text-anchor="end" font-size="11" fill="#64748b">5</text>
                <text x="70" y="265" text-anchor="end" font-size="11" fill="#64748b">0</text>
                
                <!-- Chart title -->
                <text x="265" y="25" text-anchor="middle" font-size="14" font-weight="600" fill="#374151">Questionnaires by Type</text>
              </svg>
              
              <!-- Status breakdown table -->
              <div class="questionnaire-status-table">
                <h4>Status Breakdown</h4>
                <div class="status-grid">
                  <div class="status-item approved">
                    <div class="status-dot"></div>
                    <span class="status-label">Approved</span>
                    <span class="status-count">{{ dashboardData.testing_metrics?.questionnaire_status_dist?.APPROVED || 16 }}</span>
                  </div>
                  <div class="status-item in-review">
                    <div class="status-dot"></div>
                    <span class="status-label">In Review</span>
                    <span class="status-count">{{ dashboardData.testing_metrics?.questionnaire_status_dist?.IN_REVIEW || 3 }}</span>
                  </div>
                  <div class="status-item draft">
                    <div class="status-dot"></div>
                    <span class="status-label">Draft</span>
                    <span class="status-count">{{ dashboardData.testing_metrics?.questionnaire_status_dist?.DRAFT || 5 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Plan Volume Metrics - Interactive Bar Chart -->
        <div class="chart-card chart-card--wide">
          <div class="chart-header">
            <h3 class="chart-title">Plan Volume Metrics Analysis</h3>
            <div class="chart-actions">
              <button class="btn btn--sm btn--outline" @click="exportChart('plan-volume')">Export</button>
            </div>
          </div>
          
          <div class="chart-content">
            <!-- Chart Controls Section -->
            <div class="controls-section">
              <div class="controls-header">
                <h4 class="controls-title">Chart Configuration</h4>
                <p class="controls-description">Select dimensions and filters to customize your analysis</p>
              </div>
              
              <div class="chart-controls">
                <div class="control-group">
                  <label class="control-label">X-Axis Dimension</label>
                  <select v-model="selectedXAxis" @change="updateChart" class="control-select">
                    <option value="plan_type">Plan Type</option>
                    <option value="criticality">Criticality</option>
                    <option value="status">Status</option>
                    <option value="vendor">Vendor</option>
                    <option value="strategy">Strategy</option>
                  </select>
                </div>
                
                <div class="control-group">
                  <label class="control-label">Y-Axis Metric</label>
                  <select v-model="selectedYAxis" @change="updateChart" class="control-select">
                    <option value="count">Count</option>
                    <option value="percentage">Percentage</option>
                    <option value="quality_rate">Quality Rate</option>
                    <option value="approval_rate">Approval Rate</option>
                  </select>
                </div>
                
                <div class="control-group">
                  <label class="control-label">Data Filter</label>
                  <select v-model="selectedFilter" @change="updateChart" class="control-select">
                    <option value="all">All Plans</option>
                    <option value="bcp">BCP Only</option>
                    <option value="drp">DRP Only</option>
                    <option value="approved">Approved Only</option>
                    <option value="submitted">Submitted Only</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Chart Visualization Section -->
            <div class="chart-visualization">
              <div class="chart-container">
                <div class="chart-header-info">
                  <h4 class="chart-subtitle">{{ chartTitle }}</h4>
                  <div class="chart-meta">
                    <span class="meta-item">{{ chartBars.length }} Categories</span>
                    <span class="meta-item">{{ maxValue }} Max Value</span>
                  </div>
                </div>
                
                <div class="chart-wrapper">
                  <svg class="interactive-bar-chart" :viewBox="`0 0 ${chartWidth} ${chartHeight}`">
                    <!-- Grid lines -->
                    <defs>
                      <pattern :id="`grid-${chartId}`" width="40" height="30" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#f1f5f9" stroke-width="1"/>
                      </pattern>
                    </defs>
                    <rect :width="chartWidth" :height="chartHeight" :fill="`url(#grid-${chartId})`" />
                    
                    <!-- Y-axis -->
                    <line x1="80" y1="40" :x2="80" :y2="chartHeight - 60" stroke="#e2e8f0" stroke-width="2"/>
                    
                    <!-- X-axis -->
                    <line x1="80" :y1="chartHeight - 60" :x2="chartWidth - 40" :y2="chartHeight - 60" stroke="#e2e8f0" stroke-width="2"/>
                    
                    <!-- Y-axis labels -->
                    <text v-for="(label, index) in yAxisLabels" :key="`y-label-${index}`"
                          x="75" :y="getTrendsYAxisLabelPosition(index)" text-anchor="end" font-size="12" fill="#64748b">
                      {{ label }}
                    </text>
                    
                    <!-- X-axis labels -->
                    <text v-for="(label, index) in xAxisLabels" :key="`x-label-${index}`"
                          :x="getTrendsXAxisLabelPosition(index)" :y="chartHeight - 40" text-anchor="middle" font-size="12" fill="#64748b">
                      {{ label }}
                    </text>
                    
                    <!-- Bars -->
                    <g v-for="(bar, index) in chartBars" :key="`bar-${index}`">
                      <rect :x="getBarXPosition(index)" 
                            :y="getBarYPosition(bar.value)" 
                            :width="getBarWidth()" 
                            :height="getBarHeight(bar.value)"
                            :fill="getBarColor(bar.category)"
                            rx="4"
                            class="chart-bar"
                            @mouseenter="showTooltip($event, bar)"
                            @mouseleave="hideTooltip"/>
                      
                      <!-- Bar value labels -->
                      <text :x="getBarXPosition(index) + getBarWidth()/2" 
                            :y="getBarYPosition(bar.value) - 5" 
                            text-anchor="middle" 
                            font-size="11" 
                            font-weight="600" 
                            fill="#1f2937">
                        {{ formatBarValue(bar.value) }}
                      </text>
                    </g>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Chart Information Section -->
            <div class="chart-information">
              <div class="info-section">
                <h5 class="info-title">Data Legend</h5>
                <div class="chart-legend">
                  <div v-for="(category, index) in chartCategories" :key="`legend-${index}`" class="legend-item">
                    <div class="legend-dot" :style="{ backgroundColor: getBarColor(category) }"></div>
                    <span class="legend-text">{{ category }}</span>
                    <span class="legend-value">{{ getCategoryValue(category) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="info-section">
                <h5 class="info-title">Summary Statistics</h5>
                <div class="chart-summary">
                  <div class="summary-item">
                    <div class="summary-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 11H5a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0-7H9a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0 0v3c0 1.1-.9 2-2 2h-4"/>
                      </svg>
                    </div>
                    <div class="summary-content">
                      <span class="summary-label">Data Points</span>
                      <span class="summary-value">{{ chartBars.length }}</span>
                    </div>
                  </div>
                  
                  <div class="summary-item">
                    <div class="summary-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 3h18v18H3zM9 9h6v6H9z"/>
                      </svg>
                    </div>
                    <div class="summary-content">
                      <span class="summary-label">Max Value</span>
                      <span class="summary-value">{{ maxValue }}</span>
                    </div>
                  </div>
                  
                  <div class="summary-item">
                    <div class="summary-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                      </svg>
                    </div>
                    <div class="summary-content">
                      <span class="summary-label">Average</span>
                      <span class="summary-value">{{ averageValue }}</span>
                    </div>
                  </div>
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
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import api from '@/services/api_bcp'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Reactive data
const dashboardData = ref(null)
const loading = ref(false)
const error = ref<string | null>(null)
const lastUpdated = ref('')
const dataSource = ref<'real' | 'mock' | null>(null)

// Interactive Chart Data
const selectedXAxis = ref('plan_type')
const selectedYAxis = ref('count')
const selectedFilter = ref('all')
const chartId = ref(Math.random().toString(36).substr(2, 9))
const chartWidth = ref(800)
const chartHeight = ref(400)
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  subtitle: '',
  metrics: [],
  pointData: null
})

// Enhanced Monthly Trends Data
const selectedTimeRange = ref('1Y')
const selectedPlanType = ref('all')
const selectedDepartment = ref('all')
const selectedViewMode = ref('line')
const selectedMovingAverage = ref('none')
const chartDimensions = ref({ width: 600, height: 400 })
const trendAnalysisSummary = ref([])
const trendLines = ref([])
const areaPaths = ref([])
const movingAverageLines = ref([])
const interactiveDataPoints = ref([])
const enhancedLegendItems = ref([])
const totalActivityCount = ref(0)
const averageMonthlyActivity = ref(0)
// Separate refs for enhanced trends chart axis labels
const trendsXAxisLabels = ref([])
const trendsYAxisLabels = ref([])

// API base URL
const API_BASE = `${getTprmApiBaseUrl()}/bcpdrp`

// Test API connection first
const testApiConnection = async () => {
  try {
    // First try the debug endpoint (no auth required)
    const debugResponse = await fetch(`${API_BASE}/dashboard/debug/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (debugResponse.ok) {
      const debugData = await debugResponse.json()
      console.log('Debug endpoint successful:', debugData)
    }
    
    // Test database connectivity
    const dbResponse = await fetch(`${API_BASE}/dashboard/db-test/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (dbResponse.ok) {
      const dbData = await dbResponse.json()
      console.log('Database test successful:', dbData)
    }
    
    // Then try the test endpoint (no auth required)
    const response = await fetch(`${API_BASE}/dashboard/test/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('API test successful:', data)
    return true
  } catch (err: any) {
    console.error('API test failed:', err)
    return false
  }
}

// Load dashboard data
const loadDashboardData = async () => {
  try {
    loading.value = true
    error.value = null
    
    console.log('🔍 DEBUG: Starting dashboard data load...')
    console.log('🔍 DEBUG: API base URL:', API_BASE)
    
    // Use the authenticated API service instead of raw fetch
    const response = await api.dashboard.overview() as any
    
    console.log('✅ DEBUG: Dashboard API response received:', response)
    console.log('🔍 DEBUG: Response type:', typeof response)
    console.log('🔍 DEBUG: Response keys:', Object.keys(response || {}))
    console.log('🔍 DEBUG: Response.data type:', typeof response.data)
    console.log('🔍 DEBUG: Response.data keys:', Object.keys(response.data || {}))
    console.log('🔍 DEBUG: Raw response.data:', response.data)
    
    // The response interceptor should have already unwrapped the envelope
    // So response.data should contain the actual dashboard data
    const responseData = response.data as any
    console.log('🔍 DEBUG: Response data extracted:', responseData)
    console.log('🔍 DEBUG: Response data keys:', Object.keys(responseData || {}))
    
    // Check if response has expected structure
    if (responseData && typeof responseData === 'object') {
      console.log('🔍 DEBUG: plan_metrics exists:', !!responseData.plan_metrics)
      console.log('🔍 DEBUG: plan_metrics keys:', Object.keys(responseData.plan_metrics || {}))
      console.log('🔍 DEBUG: evaluation_metrics exists:', !!responseData.evaluation_metrics)
      console.log('🔍 DEBUG: testing_metrics exists:', !!responseData.testing_metrics)
      
      if (responseData.plan_metrics) {
        console.log('🔍 DEBUG: total_plans:', responseData.plan_metrics.total_plans)
        console.log('🔍 DEBUG: status_distribution:', responseData.plan_metrics.status_distribution)
      }
    }
    
    dashboardData.value = responseData
    lastUpdated.value = new Date().toLocaleString()
    dataSource.value = 'real'
    error.value = null // Clear any previous errors
    
    // Debug temporal_metrics
    console.log('🔍 DEBUG: temporal_metrics exists:', !!responseData.temporal_metrics)
    console.log('🔍 DEBUG: temporal_metrics data:', responseData.temporal_metrics)
    if (responseData.temporal_metrics) {
      console.log('🔍 DEBUG: monthly_plans:', responseData.temporal_metrics.monthly_plans)
      console.log('🔍 DEBUG: monthly_evaluations:', responseData.temporal_metrics.monthly_evaluations)
      console.log('🔍 DEBUG: monthly_tests:', responseData.temporal_metrics.monthly_tests)
    }
    
    console.log('✅ DEBUG: Dashboard data successfully loaded')
    
    // Update trends chart after data is loaded
    await nextTick()
    updateTrendsChart()
    
  } catch (err: any) {
    console.error('❌ DEBUG: Dashboard API Error Details:')
    console.error('  - Error message:', err.message)
    console.error('  - Error status:', err.response?.status)
    console.error('  - Error data:', err.response?.data)
    console.error('  - Full error:', err)
    
    error.value = err.message || 'Failed to load dashboard data'
    
    // Show error notification with more details
    await showError('Dashboard Loading Failed', `API Error: ${err.message}. Status: ${err.response?.status || 'Unknown'}`, {
      action: 'dashboard_loading_failed',
      error_message: err.message,
      error_status: err.response?.status,
      fallback_used: true
    })
    
    // Load mock data as fallback
    console.log('⚠️ DEBUG: Loading mock data as fallback...')
    const mockData = getMockDashboardData()
    console.log('🔍 DEBUG: Mock data structure:', Object.keys(mockData))
    dashboardData.value = mockData
    lastUpdated.value = new Date().toLocaleString()
    dataSource.value = 'mock'
    
    // Show info notification about fallback
    await showInfo('Using Mock Data', 'Dashboard is now using mock data due to API connection issues.', {
      action: 'mock_data_fallback',
      data_source: 'mock'
    })
  } finally {
    loading.value = false
  }
}

// Refresh data
const refreshData = async () => {
  await showInfo('Refreshing Data', 'Dashboard data is being refreshed...', {
    action: 'dashboard_refresh',
    timestamp: new Date().toISOString()
  })
  loadDashboardData()
}

// Get status color for charts
const getStatusColor = (status: string) => {
  const colors = {
    'SUBMITTED': 'status-submitted',
    'APPROVED': 'status-approved',
    'REJECTED': 'status-rejected',
    'OCR_COMPLETED': 'status-ocr',
    'ASSIGNED_FOR_EVALUATION': 'status-assigned',
    'UNDER_EVALUATION': 'status-evaluation',
    'REVISION_REQUESTED': 'status-revision'
  }
  return colors[status] || 'status-default'
}

// Get priority color for charts
const getPriorityColor = (priority: string) => {
  const colors = {
    'Critical': 'priority-critical',
    'High': 'priority-high',
    'Medium': 'priority-medium',
    'Low': 'priority-low'
  }
  return colors[priority] || 'priority-default'
}

// Export chart data
const exportChart = async (chartType: string) => {
  try {
    await showInfo('Exporting Chart', `Exporting ${chartType} chart data...`, {
      action: 'chart_export',
      chart_type: chartType
    })
    console.log(`Exporting ${chartType} chart`)
    // Implement chart export functionality
  } catch (error) {
    await showError('Export Failed', `Failed to export ${chartType} chart. Please try again.`, {
      action: 'chart_export_failed',
      chart_type: chartType,
      error_message: error.message
    })
  }
}

// Get evaluation bar width for horizontal chart
const getEvaluationBarWidth = (scoreRange: string) => {
  if (!dashboardData.value?.evaluation_metrics?.score_distribution) {
    // Fallback values
    const fallbackValues = { excellent: 25, good: 35, fair: 15, poor: 5 }
    return (fallbackValues[scoreRange] || 0) * 10 // Scale factor for visualization
  }
  
  const value = dashboardData.value.evaluation_metrics.score_distribution[scoreRange] || 0
  return Math.max(value * 10, 20) // Scale factor with minimum width
}

// Get questionnaire bar height for stacked chart
const getQuestionnaireBarHeight = (type: string) => {
  if (!dashboardData.value?.testing_metrics?.questionnaire_type_dist) {
    return type === 'BCP' ? 120 : 120 // Fallback heights
  }
  
  const value = dashboardData.value.testing_metrics.questionnaire_type_dist[type] || 0
  return Math.max(value * 10, 40) // Scale factor with minimum height
}

// Plan Volume Metrics Helper Functions
const getCriticalityPercentage = (criticality: string) => {
  if (!dashboardData.value?.plan_metrics?.criticality_distribution) {
    return 0
  }
  
  const total = Object.values(dashboardData.value.plan_metrics.criticality_distribution).reduce((sum: number, count: unknown) => sum + (count as number), 0) as number
  const value = (dashboardData.value.plan_metrics.criticality_distribution[criticality] as number) || 0
  return total > 0 ? (value / total) * 100 : 0
}

const getTopVendors = (limit: number) => {
  if (!dashboardData.value?.plan_metrics?.vendor_distribution) {
    return {}
  }
  
  const vendors = dashboardData.value.plan_metrics.vendor_distribution
  const sortedVendors = Object.entries(vendors)
    .sort(([,a], [,b]) => (b as number) - (a as number))
    .slice(0, limit)
  
  return Object.fromEntries(sortedVendors)
}

const getVendorPercentage = (vendorId: string) => {
  if (!dashboardData.value?.plan_metrics?.vendor_distribution) {
    return 0
  }
  
  const total = Object.values(dashboardData.value.plan_metrics.vendor_distribution).reduce((sum: number, count: unknown) => sum + (count as number), 0) as number
  const value = (dashboardData.value.plan_metrics.vendor_distribution[vendorId] as number) || 0
  return total > 0 ? (value / total) * 100 : 0
}

const getTopStrategies = (limit: number) => {
  if (!dashboardData.value?.plan_metrics?.strategy_distribution) {
    return {}
  }
  
  const strategies = dashboardData.value.plan_metrics.strategy_distribution
  const sortedStrategies = Object.entries(strategies)
    .sort(([,a], [,b]) => (b as number) - (a as number))
    .slice(0, limit)
  
  return Object.fromEntries(sortedStrategies)
}

const getStrategyPercentage = (strategyName: string) => {
  if (!dashboardData.value?.plan_metrics?.strategy_distribution) {
    return 0
  }
  
  const total = Object.values(dashboardData.value.plan_metrics.strategy_distribution).reduce((sum: number, count: unknown) => sum + (count as number), 0) as number
  const value = (dashboardData.value.plan_metrics.strategy_distribution[strategyName] as number) || 0
  return total > 0 ? (value / total) * 100 : 0
}

// Interactive Chart Computed Properties
const chartData = computed(() => {
  console.log('🔍 DEBUG: chartData computed - checking data...')
  console.log('🔍 DEBUG: dashboardData exists:', !!dashboardData.value)
  console.log('🔍 DEBUG: plan_metrics exists:', !!dashboardData.value?.plan_metrics)
  
  if (!dashboardData.value?.plan_metrics) {
    console.log('⚠️ DEBUG: No plan_metrics data available for chart')
    return []
  }
  
  const data = dashboardData.value.plan_metrics
  console.log('🔍 DEBUG: plan_metrics data for chart:', data)
  let chartData = []
  
  switch (selectedXAxis.value) {
    case 'plan_type':
      chartData = [
        { category: 'BCP', value: data.bcp_plans || 0 },
        { category: 'DRP', value: data.drp_plans || 0 }
      ]
      break
    case 'criticality':
      chartData = Object.entries(data.criticality_distribution || {}).map(([key, value]) => ({
        category: key,
        value: value as number
      }))
      break
    case 'status':
      chartData = Object.entries(data.status_distribution || {}).map(([key, value]) => ({
        category: key,
        value: value as number
      }))
      break
    case 'vendor':
      chartData = Object.entries(data.vendor_distribution || {})
        .sort(([,a], [,b]) => (b as number) - (a as number))
        .slice(0, 8)
        .map(([key, value]) => ({
          category: `Vendor ${key}`,
          value: value as number
        }))
      break
    case 'strategy':
      chartData = Object.entries(data.strategy_distribution || {})
        .sort(([,a], [,b]) => (b as number) - (a as number))
        .slice(0, 8)
        .map(([key, value]) => ({
          category: key,
          value: value as number
        }))
      break
  }
  
  return chartData
})

const chartBars = computed(() => {
  let bars = chartData.value
  
  // Apply filter
  if (selectedFilter.value !== 'all') {
    bars = bars.filter(bar => {
      switch (selectedFilter.value) {
        case 'bcp':
          return bar.category === 'BCP'
        case 'drp':
          return bar.category === 'DRP'
        case 'approved':
          return bar.category === 'APPROVED'
        case 'submitted':
          return bar.category === 'SUBMITTED'
        default:
          return true
      }
    })
  }
  
  // Apply Y-axis transformation
  return bars.map(bar => {
    let value = bar.value
    if (selectedYAxis.value === 'percentage') {
      const total = bars.reduce((sum, b) => sum + b.value, 0)
      value = total > 0 ? (bar.value / total) * 100 : 0
    } else if (selectedYAxis.value === 'quality_rate') {
      value = dashboardData.value?.plan_metrics?.quality_rate || 0
    } else if (selectedYAxis.value === 'approval_rate') {
      value = dashboardData.value?.plan_metrics?.approval_rate || 0
    }
    
    return {
      ...bar,
      value: Math.round(value * 100) / 100
    }
  })
})

const chartCategories = computed(() => {
  return [...new Set(chartBars.value.map(bar => bar.category))]
})

const xAxisLabels = computed(() => {
  return chartBars.value.map(bar => bar.category)
})

const yAxisLabels = computed(() => {
  const maxValue = Math.max(...chartBars.value.map(bar => bar.value), 1)
  const steps = 5
  const step = maxValue / steps
  return Array.from({ length: steps + 1 }, (_, i) => Math.round(step * i))
})

const chartTitle = computed(() => {
  const xLabel = selectedXAxis.value.replace('_', ' ').toUpperCase()
  const yLabel = selectedYAxis.value.replace('_', ' ').toUpperCase()
  return `${xLabel} vs ${yLabel}`
})

const maxValue = computed(() => {
  return Math.max(...chartBars.value.map(bar => bar.value), 0)
})

const averageValue = computed(() => {
  const values = chartBars.value.map(bar => bar.value)
  return values.length > 0 ? Math.round((values.reduce((sum, val) => sum + val, 0) / values.length) * 100) / 100 : 0
})

// Chart Methods
const getBarColor = (category: string) => {
  const colors = {
    'BCP': '#3b82f6',
    'DRP': '#10b981',
    'CRITICAL': '#ef4444',
    'HIGH': '#f59e0b',
    'MEDIUM': '#3b82f6',
    'LOW': '#10b981',
    'SUBMITTED': '#6b7280',
    'APPROVED': '#10b981',
    'REJECTED': '#ef4444',
    'OCR_COMPLETED': '#8b5cf6'
  }
  
  // For vendors and strategies, use a consistent color
  if (category.startsWith('Vendor')) return '#8b5cf6'
  if (!colors[category]) return '#6366f1'
  
  return colors[category] || '#6366f1'
}

const getBarXPosition = (index: number) => {
  const barWidth = getBarWidth()
  const spacing = 20
  return 100 + (index * (barWidth + spacing))
}

const getBarYPosition = (value: number) => {
  const maxVal = maxValue.value
  const chartAreaHeight = chartHeight.value - 100
  const barHeight = (value / maxVal) * chartAreaHeight
  return chartHeight.value - 60 - barHeight
}

const getBarWidth = () => {
  const availableWidth = chartWidth.value - 140
  const barCount = chartBars.value.length
  return Math.max(30, Math.min(60, availableWidth / barCount - 10))
}

const getBarHeight = (value: number) => {
  const maxVal = maxValue.value
  const chartAreaHeight = chartHeight.value - 100
  return Math.max(2, (value / maxVal) * chartAreaHeight)
}

// These functions are now defined in the enhanced trends section

const formatBarValue = (value: number) => {
  if (selectedYAxis.value === 'percentage') {
    return `${value.toFixed(1)}%`
  }
  return value.toString()
}

const updateChart = () => {
  // Chart will automatically update due to computed properties
  console.log('Chart updated:', { selectedXAxis: selectedXAxis.value, selectedYAxis: selectedYAxis.value, selectedFilter: selectedFilter.value })
}

const showTooltip = (event: MouseEvent, bar: any) => {
  // Tooltip implementation
  console.log('Show tooltip:', bar)
}

const hideTooltip = () => {
  // Hide tooltip
  console.log('Hide tooltip')
}

const getCategoryValue = (category: string) => {
  const bar = chartBars.value.find(b => b.category === category)
  return bar ? formatBarValue(bar.value) : '0'
}

// Plan Status Donut Chart Computed Properties
const planStatusSlices = computed(() => {
  console.log('🔍 DEBUG: planStatusSlices computed - checking data...')
  console.log('🔍 DEBUG: dashboardData exists:', !!dashboardData.value)
  console.log('🔍 DEBUG: plan_metrics exists:', !!dashboardData.value?.plan_metrics)
  console.log('🔍 DEBUG: status_distribution exists:', !!dashboardData.value?.plan_metrics?.status_distribution)
  
  if (!dashboardData.value?.plan_metrics?.status_distribution) {
    console.log('⚠️ DEBUG: No status_distribution data available')
    // Return empty array if no data
    return []
  }
  
  const statusDistribution = dashboardData.value.plan_metrics.status_distribution
  console.log('🔍 DEBUG: status_distribution data:', statusDistribution)
  
  const total = Object.values(statusDistribution).reduce((sum: number, count: unknown) => sum + (count as number), 0) as number
  console.log('🔍 DEBUG: total status count:', total)
  
  if (total === 0) {
    console.log('⚠️ DEBUG: Total status count is 0')
    return []
  }
  
  // Status colors mapping based on the model choices
  const statusColors = {
    'SUBMITTED': '#6b7280',      // Gray
    'OCR_COMPLETED': '#8b5cf6',  // Purple
    'ASSIGNED_FOR_EVALUATION': '#3b82f6', // Blue
    'APPROVED': '#10b981',       // Green
    'REJECTED': '#ef4444',       // Red
    'REVISION_REQUESTED': '#f59e0b' // Orange
  }
  
  // Status labels mapping
  const statusLabels = {
    'SUBMITTED': 'Submitted',
    'OCR_COMPLETED': 'OCR Completed',
    'ASSIGNED_FOR_EVALUATION': 'Assigned for Evaluation',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected',
    'REVISION_REQUESTED': 'Revision Requested'
  }
  
  const slices = []
  let cumulativePercentage = 0
  
  // Create slices for each status that has data
  Object.entries(statusDistribution).forEach(([status, count]) => {
    const statusCount = count as number
    if (statusCount > 0) {
      const percentage = (statusCount / total) * 100
      const circumference = 2 * Math.PI * 120 // radius = 120 (updated to match new SVG dimensions)
      const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`
      
      slices.push({
        status,
        count: statusCount,
        percentage: percentage,
        color: statusColors[status] || '#6b7280',
        label: statusLabels[status] || status,
        circumference: circumference,
        strokeDasharray: strokeDasharray,
        cumulativePercentage: cumulativePercentage
      })
      
      cumulativePercentage += percentage
    }
  })
  
  return slices
})

const totalPlanStatusCount = computed(() => {
  if (!dashboardData.value?.plan_metrics?.status_distribution) {
    return 0
  }
  
  return Object.values(dashboardData.value.plan_metrics.status_distribution)
    .reduce((sum: number, count: unknown) => sum + (count as number), 0) as number
})

// Donut Chart Methods
const getDonutSliceDashArray = (slice: any) => {
  return slice.strokeDasharray
}

const getDonutSliceOffset = (index: number) => {
  let offset = 0
  for (let i = 0; i < index; i++) {
    const slice = planStatusSlices.value[i]
    if (slice) {
      offset += (slice.percentage / 100) * slice.circumference
    }
  }
  return -offset
}

const showSliceTooltip = (event: MouseEvent, slice: any) => {
  // Tooltip implementation for donut slices
  console.log('Show tooltip for:', slice)
}

const hideSliceTooltip = () => {
  // Hide tooltip
  console.log('Hide tooltip')
}

// Percentage label positioning methods
const getPercentageLabelX = (slice: any, index: number) => {
  const centerX = 250 // Updated center to match new SVG dimensions
  const radius = 120 // Position labels at the center of the donut slices (same as circle radius)
  
  // Calculate the cumulative angle based on circumference (matching SVG circle behavior)
  let cumulativeLength = 0
  for (let i = 0; i < index; i++) {
    const prevSlice = planStatusSlices.value[i]
    if (prevSlice) {
      cumulativeLength += (prevSlice.percentage / 100) * prevSlice.circumference
    }
  }
  
  // Calculate the middle position of the current slice
  const sliceLength = (slice.percentage / 100) * slice.circumference
  const middleLength = cumulativeLength + (sliceLength / 2)
  
  // Convert circumference position to angle (SVG circles start from 3 o'clock, go clockwise)
  const circumference = 2 * Math.PI * 120 // Updated radius = 120
  const angleRadians = (middleLength / circumference) * 2 * Math.PI
  
  return centerX + Math.cos(angleRadians) * radius
}

const getPercentageLabelY = (slice: any, index: number) => {
  const centerY = 250 // Updated center to match new SVG dimensions
  const radius = 120 // Position labels at the center of the donut slices (same as circle radius)
  
  // Calculate the cumulative angle based on circumference (matching SVG circle behavior)
  let cumulativeLength = 0
  for (let i = 0; i < index; i++) {
    const prevSlice = planStatusSlices.value[i]
    if (prevSlice) {
      cumulativeLength += (prevSlice.percentage / 100) * prevSlice.circumference
    }
  }
  
  // Calculate the middle position of the current slice
  const sliceLength = (slice.percentage / 100) * slice.circumference
  const middleLength = cumulativeLength + (sliceLength / 2)
  
  // Convert circumference position to angle (SVG circles start from 3 o'clock, go clockwise)
  const circumference = 2 * Math.PI * 120 // Updated radius = 120
  const angleRadians = (middleLength / circumference) * 2 * Math.PI
  
  return centerY + Math.sin(angleRadians) * radius
}

// Mock data for fallback
const getMockDashboardData = () => {
  return {
    plan_metrics: {
      total_plans: 154,
      bcp_plans: 89,
      drp_plans: 65,
      status_distribution: {
        'SUBMITTED': 12,
        'APPROVED': 89,
        'REJECTED': 8,
        'OCR_COMPLETED': 25,
        'ASSIGNED_FOR_EVALUATION': 15,
        'UNDER_EVALUATION': 5
      },
      criticality_distribution: {
        'LOW': 20,
        'MEDIUM': 45,
        'HIGH': 30,
        'CRITICAL': 15
      },
      ocr_completed: 120,
      ocr_rate: 78.5,
      approved_plans: 89,
      rejected_plans: 8,
      approval_rate: 91.8,
      vendor_distribution: {
        '1': 45,
        '2': 38,
        '3': 42,
        '4': 29
      },
      strategy_distribution: {
        'Strategy A': 25,
        'Strategy B': 30,
        'Strategy C': 35,
        'Strategy D': 28,
        'Strategy E': 36
      },
      plans_with_details: 140,
      quality_rate: 90.9
    },
    evaluation_metrics: {
      total_evaluations: 87,
      submitted_evaluations: 75,
      status_distribution: {
        'ASSIGNED': 5,
        'IN_PROGRESS': 7,
        'SUBMITTED': 75
      },
      avg_overall_score: 85.2,
      avg_quality_score: 82.5,
      avg_coverage_score: 88.1,
      avg_recovery_score: 86.3,
      avg_compliance_score: 84.7,
      score_distribution: {
        excellent: 25,
        good: 35,
        fair: 15,
        poor: 5
      },
      evaluator_performance: {
        '101': 15,
        '102': 12,
        '103': 18,
        '104': 10,
        '105': 20
      }
    },
    testing_metrics: {
      total_questionnaires: 24,
      questionnaire_status_dist: {
        'DRAFT': 5,
        'IN_REVIEW': 3,
        'APPROVED': 16
      },
      questionnaire_type_dist: {
        'BCP': 12,
        'DRP': 12
      },
      total_questions: 180,
      question_type_dist: {
        'TEXT': 45,
        'YES_NO': 90,
        'MULTIPLE_CHOICE': 45
      },
      required_questions: 150,
      optional_questions: 30,
      total_assignments: 156,
      assignment_status_dist: {
        'ASSIGNED': 12,
        'IN_PROGRESS': 8,
        'SUBMITTED': 136
      },
      owner_decision_dist: {
        'PENDING': 15,
        'APPROVED': 120,
        'REJECTED': 16,
        'REWORK_REQUESTED': 5
      },
      approved_tests: 120,
      rejected_tests: 16,
      success_rate: 88.2,
      overdue_assignments: 8
    },
    approval_metrics: {
      total_approvals: 45,
      status_distribution: {
        'ASSIGNED': 8,
        'IN_PROGRESS': 5,
        'COMMENTED': 25,
        'SKIPPED': 7
      },
      object_type_dist: {
        'PLAN EVALUATION': 30,
        'NEW QUESTIONNAIRE': 10,
        'QUESTIONNAIRE RESPONSE': 5
      },
      plan_type_dist: {
        'BCP': 25,
        'DRP': 20
      },
      workflow_dist: {
        'Plan Approval Workflow': 30,
        'Questionnaire Review Workflow': 10,
        'Test Assignment Workflow': 5
      },
      completed_approvals: 32,
      completion_rate: 71.1,
      overdue_approvals: 8,
      assignee_performance: {
        'John Smith': 12,
        'Jane Doe': 8,
        'Mike Johnson': 15,
        'Sarah Wilson': 10
      }
    },
    risk_metrics: {
      total_risks: 0,
      priority_distribution: {},
      status_distribution: {},
      type_distribution: {},
      avg_score: 0,
      avg_likelihood: 0,
      avg_impact: 0,
      avg_exposure: 0,
      critical_risks: 0,
      high_score_risks: 0,
      mitigated_risks: 0,
      open_risks: 0,
      score_distribution: {}
    },
    user_metrics: {
      total_users: 25,
      active_users: 22,
      department_dist: {
        '1': 8,
        '2': 6,
        '3': 7,
        '4': 4
      },
      recent_activity: 18,
      plan_submissions: {
        '101': 5,
        '102': 3,
        '103': 7,
        '104': 4,
        '105': 6
      },
      evaluation_completions: {
        '201': 8,
        '202': 6,
        '203': 10,
        '204': 5,
        '205': 12
      },
      test_assignments: {
        '301': 15,
        '302': 12,
        '303': 18,
        '304': 8,
        '305': 20
      }
    },
    temporal_metrics: {
      monthly_plans: [
        { month: '2024-01', count: 12 },
        { month: '2024-02', count: 15 },
        { month: '2024-03', count: 18 },
        { month: '2024-04', count: 14 },
        { month: '2024-05', count: 16 },
        { month: '2024-06', count: 20 }
      ],
      monthly_evaluations: [
        { month: '2024-01', count: 8 },
        { month: '2024-02', count: 12 },
        { month: '2024-03', count: 15 },
        { month: '2024-04', count: 10 },
        { month: '2024-05', count: 14 },
        { month: '2024-06', count: 16 }
      ],
      monthly_tests: [
        { month: '2024-01', count: 20 },
        { month: '2024-02', count: 25 },
        { month: '2024-03', count: 30 },
        { month: '2024-04', count: 22 },
        { month: '2024-05', count: 28 },
        { month: '2024-06', count: 31 }
      ],
      monthly_risks: []
    }
  }
}

// Enhanced Monthly Trends Methods
const updateTrendsChart = () => {
  console.log('🔍 DEBUG: updateTrendsChart called')
  console.log('🔍 DEBUG: Chart update with filters:', {
    timeRange: selectedTimeRange.value,
    planType: selectedPlanType.value,
    department: selectedDepartment.value,
    viewMode: selectedViewMode.value,
    movingAverage: selectedMovingAverage.value
  })
  console.log('🔍 DEBUG: dashboardData exists:', !!dashboardData.value)
  console.log('🔍 DEBUG: temporal_metrics exists:', !!dashboardData.value?.temporal_metrics)
  
  // Process the data based on current filters
  try {
    processTrendsData()
    console.log('✅ DEBUG: Trends chart updated successfully')
  } catch (error) {
    console.error('❌ DEBUG: Error updating trends chart:', error)
  }
}

const processTrendsData = () => {
  console.log('🔍 DEBUG: processTrendsData called')
  console.log('🔍 DEBUG: dashboardData.value exists:', !!dashboardData.value)
  console.log('🔍 DEBUG: temporal_metrics exists:', !!dashboardData.value?.temporal_metrics)
  
  if (!dashboardData.value?.temporal_metrics) {
    console.log('⚠️ DEBUG: No temporal_metrics, using mock data')
    // Use mock data if no real data available
    const mockData = getMockTemporalData()
    processTemporalData(mockData)
    return
  }
  
  const temporalData = dashboardData.value.temporal_metrics
  console.log('🔍 DEBUG: Processing temporal data:', temporalData)
  console.log('🔍 DEBUG: monthly_plans length:', temporalData.monthly_plans?.length || 0)
  console.log('🔍 DEBUG: monthly_evaluations length:', temporalData.monthly_evaluations?.length || 0)
  console.log('🔍 DEBUG: monthly_tests length:', temporalData.monthly_tests?.length || 0)
  
  processTemporalData(temporalData)
}

const processTemporalData = (temporalData) => {
  // Get filtered data based on selections
  const filteredData = filterTemporalData(temporalData)
  
  // Calculate trend analysis
  calculateTrendAnalysis(filteredData)
  
  // Generate chart elements
  generateChartElements(filteredData)
  
  // Update legend and summary
  updateEnhancedLegend(filteredData)
}

const filterTemporalData = (data) => {
  let filteredData = { ...data }
  
  // Filter by time range
  const monthsToShow = getMonthsForTimeRange(selectedTimeRange.value)
  filteredData.monthly_plans = filterDataByTimeRange(data.monthly_plans, monthsToShow)
  filteredData.monthly_evaluations = filterDataByTimeRange(data.monthly_evaluations, monthsToShow)
  filteredData.monthly_tests = filterDataByTimeRange(data.monthly_tests, monthsToShow)
  
  return filteredData
}

const getMonthsForTimeRange = (timeRange) => {
  const months = {
    '3M': 3,
    '6M': 6,
    '1Y': 12,
    '2Y': 24
  }
  return months[timeRange] || 12
}

const filterDataByTimeRange = (data, months) => {
  if (!data || !Array.isArray(data)) return []
  return data.slice(-months)
}

const calculateTrendAnalysis = (data) => {
  const analysis = []
  
  // Plans analysis
  const plansData = data.monthly_plans || []
  if (plansData.length > 0) {
    analysis.push({
      name: 'Plans',
      iconClass: 'plan-icon',
      iconPath: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
      currentValue: plansData[plansData.length - 1]?.count || 0,
      previousValue: plansData[plansData.length - 2]?.count || 0,
      changeClass: getChangeClass(plansData),
      trendIcon: getTrendIcon(plansData),
      changeText: getChangeText(plansData),
      momChange: calculateMoMChange(plansData),
      yoyChange: calculateYoYChange(plansData)
    })
  }
  
  // Evaluations analysis
  const evaluationsData = data.monthly_evaluations || []
  if (evaluationsData.length > 0) {
    analysis.push({
      name: 'Evaluations',
      iconClass: 'evaluation-icon',
      iconPath: 'M9 11H5a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0-7H9a2 2 0 0 0-2 2v3c0 1.1.9 2 2 2h4m0-7h4m0 0v3c0 1.1-.9 2-2 2h-4',
      currentValue: evaluationsData[evaluationsData.length - 1]?.count || 0,
      previousValue: evaluationsData[evaluationsData.length - 2]?.count || 0,
      changeClass: getChangeClass(evaluationsData),
      trendIcon: getTrendIcon(evaluationsData),
      changeText: getChangeText(evaluationsData),
      momChange: calculateMoMChange(evaluationsData),
      yoyChange: calculateYoYChange(evaluationsData)
    })
  }
  
  // Tests analysis
  const testsData = data.monthly_tests || []
  if (testsData.length > 0) {
    analysis.push({
      name: 'Tests',
      iconClass: 'testing-icon',
      iconPath: 'M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z',
      currentValue: testsData[testsData.length - 1]?.count || 0,
      previousValue: testsData[testsData.length - 2]?.count || 0,
      changeClass: getChangeClass(testsData),
      trendIcon: getTrendIcon(testsData),
      changeText: getChangeText(testsData),
      momChange: calculateMoMChange(testsData),
      yoyChange: calculateYoYChange(testsData)
    })
  }
  
  trendAnalysisSummary.value = analysis
}

const getChangeClass = (data) => {
  if (data.length < 2) return 'neutral'
  const current = data[data.length - 1]?.count || 0
  const previous = data[data.length - 2]?.count || 0
  return current > previous ? 'positive' : current < previous ? 'negative' : 'neutral'
}

const getTrendIcon = (data) => {
  if (data.length < 2) return '→'
  const current = data[data.length - 1]?.count || 0
  const previous = data[data.length - 2]?.count || 0
  return current > previous ? '↗️' : current < previous ? '↘️' : '→'
}

const getChangeText = (data) => {
  if (data.length < 2) return 'No change'
  const current = data[data.length - 1]?.count || 0
  const previous = data[data.length - 2]?.count || 0
  const change = current - previous
  return change > 0 ? `+${change}` : change < 0 ? `${change}` : 'No change'
}

const calculateMoMChange = (data) => {
  if (data.length < 2) return '0%'
  const current = data[data.length - 1]?.count || 0
  const previous = data[data.length - 2]?.count || 0
  if (previous === 0) return current > 0 ? '+100%' : '0%'
  const change = ((current - previous) / previous) * 100
  return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`
}

const calculateYoYChange = (data) => {
  if (data.length < 12) return 'N/A'
  const current = data[data.length - 1]?.count || 0
  const previous = data[data.length - 13]?.count || 0
  if (previous === 0) return current > 0 ? '+100%' : '0%'
  const change = ((current - previous) / previous) * 100
  return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`
}

const generateChartElements = (data) => {
  console.log('🔍 DEBUG: generateChartElements called with data:', data)
  
  const chartWidth = chartDimensions.value.width
  const chartHeight = chartDimensions.value.height
  const margin = { top: 40, right: 40, bottom: 60, left: 80 }
  const chartAreaWidth = chartWidth - margin.left - margin.right
  const chartAreaHeight = chartHeight - margin.top - margin.bottom
  
  // Generate all months data for consistent x-axis
  const allMonths = generateAllMonths(data)
  console.log('🔍 DEBUG: Generated months for chart:', allMonths.length)
  trendsXAxisLabels.value = allMonths.map(m => m.label)
  
  // Calculate Y-axis scale
  const maxValue = calculateMaxValue(data)
  const yScale = maxValue > 0 ? chartAreaHeight / maxValue : 1
  trendsYAxisLabels.value = generateYAxisLabels(maxValue)
  console.log('🔍 DEBUG: Chart scale - maxValue:', maxValue, 'yScale:', yScale)
  
  // Generate trend lines
  trendLines.value = generateTrendLines(data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale)
  console.log('🔍 DEBUG: Generated trend lines:', trendLines.value.length)
  
  // Generate area paths
  areaPaths.value = generateAreaPaths(data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale)
  console.log('🔍 DEBUG: Generated area paths:', areaPaths.value.length)
  
  // Generate moving average lines
  if (selectedMovingAverage.value !== 'none') {
    movingAverageLines.value = generateMovingAverageLines(data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale)
    console.log('🔍 DEBUG: Generated moving average lines:', movingAverageLines.value.length)
  } else {
    movingAverageLines.value = []
  }
  
  // Generate interactive data points
  interactiveDataPoints.value = generateInteractiveDataPoints(data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale)
  console.log('🔍 DEBUG: Generated interactive data points:', interactiveDataPoints.value.length)
}

const generateAllMonths = (data) => {
  const allMonths = []
  const plans = data.monthly_plans || []
  const evaluations = data.monthly_evaluations || []
  const tests = data.monthly_tests || []
  
  console.log('🔍 DEBUG: generateAllMonths - plans:', plans.length, 'evaluations:', evaluations.length, 'tests:', tests.length)
  
  // Get all unique months
  const monthSet = new Set()
  ;[...plans, ...evaluations, ...tests].forEach(item => {
    if (item && item.month) {
      monthSet.add(item.month)
    }
  })
  
  const sortedMonths = Array.from(monthSet).sort()
  console.log('🔍 DEBUG: Unique months found:', sortedMonths)
  
  // If no months found, generate last 12 months as fallback
  if (sortedMonths.length === 0) {
    console.log('⚠️ DEBUG: No months found in data, generating last 12 months as fallback')
    const today = new Date()
    for (let i = 11; i >= 0; i--) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1)
      const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      sortedMonths.push(monthStr)
    }
  }
  
  sortedMonths.forEach((month, index) => {
    try {
      // Handle month format (YYYY-MM)
      const dateStr = month.includes('-') ? month + '-01' : `${month}-01`
      const date = new Date(dateStr)
      if (!isNaN(date.getTime())) {
        allMonths.push({
          month,
          label: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
          index
        })
      } else {
        console.warn('⚠️ DEBUG: Invalid month format:', month)
      }
    } catch (e) {
      console.error('❌ DEBUG: Error parsing month:', month, e)
    }
  })
  
  console.log('🔍 DEBUG: Generated months:', allMonths.length)
  return allMonths
}

const calculateMaxValue = (data) => {
  const plans = data.monthly_plans || []
  const evaluations = data.monthly_evaluations || []
  const tests = data.monthly_tests || []
  
  const allValues = [...plans, ...evaluations, ...tests]
    .filter(item => item && typeof item === 'object')
    .map(item => item.count || 0)
  
  const maxValue = allValues.length > 0 ? Math.max(...allValues, 20) : 20 // Minimum scale of 20
  console.log('🔍 DEBUG: Calculated max value:', maxValue, 'from', allValues.length, 'values')
  return maxValue
}

const generateYAxisLabels = (maxValue) => {
  const steps = 5
  const step = maxValue / steps
  return Array.from({ length: steps + 1 }, (_, i) => Math.round(step * i))
}

const generateTrendLines = (data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale) => {
  const lines = []
  const colors = {
    plans: '#3b82f6',
    evaluations: '#10b981',
    tests: '#f59e0b'
  }
  
  // Guard against empty months array
  if (!allMonths || allMonths.length === 0) {
    console.warn('⚠️ DEBUG: No months available for trend lines')
    return lines
  }
  
  // Calculate step size (handle single month case)
  const stepSize = allMonths.length > 1 ? chartAreaWidth / (allMonths.length - 1) : 0
  
  // Plans line
  if (data.monthly_plans && data.monthly_plans.length > 0) {
    const points = allMonths.map((month, index) => {
      const dataPoint = data.monthly_plans.find(p => p && p.month === month.month)
      const value = dataPoint?.count || 0
      const x = margin.left + (index * stepSize)
      const y = margin.top + chartAreaHeight - (value * yScale)
      return `${x},${y}`
    }).join(' ')
    
    if (points) {
      lines.push({
        points,
        color: colors.plans
      })
    }
  }
  
  // Evaluations line
  if (data.monthly_evaluations && data.monthly_evaluations.length > 0) {
    const points = allMonths.map((month, index) => {
      const dataPoint = data.monthly_evaluations.find(p => p && p.month === month.month)
      const value = dataPoint?.count || 0
      const x = margin.left + (index * stepSize)
      const y = margin.top + chartAreaHeight - (value * yScale)
      return `${x},${y}`
    }).join(' ')
    
    if (points) {
      lines.push({
        points,
        color: colors.evaluations
      })
    }
  }
  
  // Tests line
  if (data.monthly_tests && data.monthly_tests.length > 0) {
    const points = allMonths.map((month, index) => {
      const dataPoint = data.monthly_tests.find(p => p && p.month === month.month)
      const value = dataPoint?.count || 0
      const x = margin.left + (index * stepSize)
      const y = margin.top + chartAreaHeight - (value * yScale)
      return `${x},${y}`
    }).join(' ')
    
    if (points) {
      lines.push({
        points,
        color: colors.tests
      })
    }
  }
  
  console.log('🔍 DEBUG: Generated trend lines:', lines.length)
  return lines
}

const generateAreaPaths = (data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale) => {
  const areas = []
  
  // Guard against empty months array
  if (!allMonths || allMonths.length === 0) {
    return areas
  }
  
  // Calculate step size (handle single month case)
  const stepSize = allMonths.length > 1 ? chartAreaWidth / (allMonths.length - 1) : 0
  
  // Plans area
  if (data.monthly_plans && data.monthly_plans.length > 0) {
    const pathData = allMonths.map((month, index) => {
      const dataPoint = data.monthly_plans.find(p => p && p.month === month.month)
      const value = dataPoint?.count || 0
      const x = margin.left + (index * stepSize)
      const y = margin.top + chartAreaHeight - (value * yScale)
      return index === 0 ? `M ${x} ${margin.top + chartAreaHeight} L ${x} ${y}` : `L ${x} ${y}`
    }).join(' ') + ` L ${margin.left + chartAreaWidth} ${margin.top + chartAreaHeight} Z`
    
    if (pathData) {
      areas.push({
        path: pathData,
        gradient: 'url(#plansGradient)'
      })
    }
  }
  
  return areas
}

const generateMovingAverageLines = (data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale) => {
  const lines = []
  const windowSize = selectedMovingAverage.value === '3M' ? 3 : 6
  
  // Calculate moving averages for each metric
  const metrics = ['monthly_plans', 'monthly_evaluations', 'monthly_tests']
  const colors = ['#3b82f6', '#10b981', '#f59e0b']
  
  metrics.forEach((metric, metricIndex) => {
    if (data[metric] && data[metric].length >= windowSize) {
      const movingAverages = []
      
      for (let i = windowSize - 1; i < allMonths.length; i++) {
        const windowData = []
        for (let j = 0; j < windowSize; j++) {
          const monthData = data[metric].find(p => p.month === allMonths[i - j]?.month)
          windowData.push(monthData?.count || 0)
        }
        const average = windowData.reduce((sum, val) => sum + val, 0) / windowSize
        movingAverages.push({ month: allMonths[i].month, average, index: i })
      }
      
      const points = movingAverages.map(ma => {
        const x = margin.left + (ma.index * (chartAreaWidth / (allMonths.length - 1)))
        const y = margin.top + chartAreaHeight - (ma.average * yScale)
        return `${x},${y}`
      }).join(' ')
      
      lines.push({
        points,
        color: colors[metricIndex]
      })
    }
  })
  
  return lines
}

const generateInteractiveDataPoints = (data, allMonths, chartAreaWidth, chartAreaHeight, margin, yScale) => {
  const points = []
  const colors = {
    plans: '#3b82f6',
    evaluations: '#10b981',
    tests: '#f59e0b'
  }
  
  // Guard against empty months array
  if (!allMonths || allMonths.length === 0) {
    return points
  }
  
  // Calculate step size (handle single month case)
  const stepSize = allMonths.length > 1 ? chartAreaWidth / (allMonths.length - 1) : 0
  
  // Generate points for each metric
  const metrics = [
    { key: 'monthly_plans', name: 'Plans', color: colors.plans },
    { key: 'monthly_evaluations', name: 'Evaluations', color: colors.evaluations },
    { key: 'monthly_tests', name: 'Tests', color: colors.tests }
  ]
  
  metrics.forEach(metric => {
    if (data[metric.key] && Array.isArray(data[metric.key]) && data[metric.key].length > 0) {
      data[metric.key].forEach(dataPoint => {
        if (dataPoint && dataPoint.month) {
          const monthIndex = allMonths.findIndex(m => m.month === dataPoint.month)
          if (monthIndex >= 0) {
            const x = margin.left + (monthIndex * stepSize)
            const y = margin.top + chartAreaHeight - ((dataPoint.count || 0) * yScale)
            
            points.push({
              x,
              y,
              color: metric.color,
              name: metric.name,
              value: dataPoint.count || 0,
              month: allMonths[monthIndex].label,
              fullMonth: dataPoint.month,
              metric: metric.key
            })
          }
        }
      })
    }
  })
  
  console.log('🔍 DEBUG: Generated interactive data points:', points.length)
  return points
}

const updateEnhancedLegend = (data) => {
  const legendItems = []
  const colors = {
    plans: '#3b82f6',
    evaluations: '#10b981',
    tests: '#f59e0b'
  }
  
  const metrics = [
    { key: 'monthly_plans', name: 'Plans' },
    { key: 'monthly_evaluations', name: 'Evaluations' },
    { key: 'monthly_tests', name: 'Tests' }
  ]
  
  metrics.forEach(metric => {
    const metricData = data[metric.key] || []
    if (metricData.length > 0) {
      const currentValue = metricData[metricData.length - 1]?.count || 0
      const peakData = metricData.reduce((max, item) => item.count > max.count ? item : max, metricData[0])
      const growthRate = calculateGrowthRate(metricData)
      
      legendItems.push({
        name: metric.name,
        color: colors[metric.key.replace('monthly_', '')],
        currentValue,
        trendIcon: getTrendIcon(metricData),
        trendText: getTrendText(metricData),
        trendClass: getChangeClass(metricData),
        peakValue: peakData.count,
        peakMonth: new Date(peakData.month + '-01').toLocaleDateString('en-US', { month: 'short' }),
        growthRate: growthRate.toFixed(1),
        growthClass: growthRate > 0 ? 'positive' : growthRate < 0 ? 'negative' : 'neutral'
      })
    }
  })
  
  enhancedLegendItems.value = legendItems
  
  // Calculate totals
  const allData = [...(data.monthly_plans || []), ...(data.monthly_evaluations || []), ...(data.monthly_tests || [])]
  totalActivityCount.value = allData.reduce((sum, item) => sum + (item.count || 0), 0)
  averageMonthlyActivity.value = allData.length > 0 ? Math.round(totalActivityCount.value / allData.length) : 0
}

const calculateGrowthRate = (data) => {
  if (data.length < 2) return 0
  const first = data[0].count || 0
  const last = data[data.length - 1].count || 0
  if (first === 0) return last > 0 ? 100 : 0
  return ((last - first) / first) * 100
}

const getTrendText = (data) => {
  if (data.length < 2) return 'Stable'
  const current = data[data.length - 1]?.count || 0
  const previous = data[data.length - 2]?.count || 0
  return current > previous ? 'Increasing' : current < previous ? 'Decreasing' : 'Stable'
}

// Tooltip methods
const showDataPointTooltip = (event, point) => {
  const rect = event.target.closest('svg').getBoundingClientRect()
  const x = event.clientX - rect.left + 10
  const y = event.clientY - rect.top - 10
  
  tooltip.value = {
    visible: true,
    x,
    y,
    title: point.month,
    subtitle: `${point.name} Activity`,
    pointData: point,
    metrics: [{
      name: point.name,
      value: point.value,
      color: point.color,
      change: getPointChange(point),
      changeIcon: getPointChangeIcon(point),
      changeClass: getPointChangeClass(point)
    }]
  }
}

const hideDataPointTooltip = () => {
  tooltip.value = {
    visible: false,
    x: 0,
    y: 0,
    title: '',
    subtitle: '',
    metrics: [],
    pointData: null
  }
}

const getPointChange = (point) => {
  // This would need to be implemented with historical data comparison
  return '+12%'
}

const getPointChangeIcon = (point) => {
  return '↗️'
}

const getPointChangeClass = (point) => {
  return 'positive'
}

const drillDownToDataPoint = (point) => {
  console.log('Drilling down to:', point)
  // Implement drill-down functionality
}

const getTrendsYAxisLabelPosition = (index) => {
  const chartAreaHeight = chartDimensions.value.height - 100
  const step = chartAreaHeight / (trendsYAxisLabels.value.length - 1)
  return chartDimensions.value.height - 60 - (index * step)
}

const getTrendsXAxisLabelPosition = (index) => {
  const chartAreaWidth = chartDimensions.value.width - 120
  const step = chartAreaWidth / (trendsXAxisLabels.value.length - 1)
  return 80 + (index * step)
}

// Export and refresh methods
const exportMonthlyTrends = () => {
  console.log('Exporting monthly trends data')
  // Implement export functionality
}

const refreshTrendsData = () => {
  console.log('Refreshing trends data')
  loadDashboardData()
}

// Mock data for enhanced trends
const getMockTemporalData = () => {
  return {
    monthly_plans: [
      { month: '2024-01', count: 12 },
      { month: '2024-02', count: 15 },
      { month: '2024-03', count: 18 },
      { month: '2024-04', count: 14 },
      { month: '2024-05', count: 16 },
      { month: '2024-06', count: 20 },
      { month: '2024-07', count: 22 },
      { month: '2024-08', count: 25 }
    ],
    monthly_evaluations: [
      { month: '2024-01', count: 8 },
      { month: '2024-02', count: 12 },
      { month: '2024-03', count: 15 },
      { month: '2024-04', count: 10 },
      { month: '2024-05', count: 14 },
      { month: '2024-06', count: 16 },
      { month: '2024-07', count: 18 },
      { month: '2024-08', count: 21 }
    ],
    monthly_tests: [
      { month: '2024-01', count: 20 },
      { month: '2024-02', count: 25 },
      { month: '2024-03', count: 30 },
      { month: '2024-04', count: 22 },
      { month: '2024-05', count: 28 },
      { month: '2024-06', count: 31 },
      { month: '2024-07', count: 33 },
      { month: '2024-08', count: 35 }
    ]
  }
}

// Watch for dashboardData changes and update chart
watch(() => dashboardData.value?.temporal_metrics, (newTemporalMetrics) => {
  console.log('🔍 DEBUG: temporal_metrics changed:', newTemporalMetrics)
  if (newTemporalMetrics) {
    // Use nextTick to ensure DOM is updated
    nextTick(() => {
      updateTrendsChart()
    })
  }
}, { deep: true, immediate: false })

// Load data on component mount
onMounted(async () => {
  console.log('🔍 DEBUG: Dashboard component mounted')
  
  // Test API connectivity first
  try {
    console.log('🔍 DEBUG: Testing API connectivity...')
    const connectivityTest = await testApiConnection()
    console.log('🔍 DEBUG: API connectivity test result:', connectivityTest)
  } catch (testError) {
    console.error('❌ DEBUG: API connectivity test failed:', testError)
  }
  
  await loggingService.logBCPView()
  await loadDashboardData()
  
  // Initialize trends chart after data is loaded (with delay to ensure DOM is ready)
  await nextTick()
  setTimeout(() => {
    updateTrendsChart()
  }, 500)
})
</script>

<style scoped>
@import './Dashboard.css';
</style>
