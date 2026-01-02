<template>
  <div class="kpi-dashboard">
    <!-- Error Message -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="filters-section">
      <div class="filters-container">
        <div class="filters-label">
          <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46 22,3"></polygon>
          </svg>
          Filters:
        </div>
        
        <div class="filter-group">
          <div class="filter-item">
            <svg class="calendar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            <select class="filter-select">
              <option>Last 12 Months</option>
              <option>Last 6 Months</option>
              <option>Last 3 Months</option>
            </select>
          </div>
          
          <div class="filter-item">
            <select class="filter-select">
              <option>All Vendors</option>
              <option>Vendor A</option>
              <option>Vendor B</option>
            </select>
          </div>
          
          <div class="filter-item">
            <select class="filter-select">
              <option>All Plans</option>
              <option>Plan A</option>
              <option>Plan B</option>
            </select>
          </div>
          
          <div class="filter-item">
            <select class="filter-select">
              <option>All Strategies</option>
              <option>Strategy A</option>
              <option>Strategy B</option>
            </select>
          </div>
          
          <div class="filter-item">
            <select class="filter-select">
              <option>All Roles</option>
              <option>Role A</option>
              <option>Role B</option>
            </select>
          </div>
          
          <div class="filter-item">
            <select class="filter-select">
              <option>All Status</option>
              <option>Active</option>
              <option>Inactive</option>
            </select>
          </div>
        </div>
        
        <button class="reset-filters-btn">Reset Filters</button>
      </div>
    </div>

    <div class="kpi-grid">
      <!-- Loading Overlay -->
      <div v-if="loading" class="loading-overlay">
        <div style="text-align: center;">
          <div style="width: 40px; height: 40px; border: 4px solid #e5e7eb; border-top: 4px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 16px;"></div>
          <div style="color: #6b7280; font-size: 14px;">Loading KPI data...</div>
        </div>
      </div>

      <!-- Row 1 -->

      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22,4 12,14.01 9,11.01"></polyline>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Plan Approval Rate</h3>
            <div class="kpi-change negative">-3.2%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatPercentage(kpis.planApprovalRate) }}</div>
        <div class="kpi-chart">
          <div class="circular-progress">
            <svg class="progress-ring" width="140" height="140">
              <circle
                class="progress-ring-bg"
                cx="60"
                cy="60"
                r="50"
                fill="transparent"
                stroke="#e5e7eb"
                stroke-width="8"
              />
              <circle
                class="progress-ring-fill"
                cx="60"
                cy="60"
                r="50"
                fill="transparent"
                stroke="#10b981"
                stroke-width="8"
                stroke-dasharray="314"
                stroke-dashoffset="114"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="progress-text">
              <div class="progress-value">63.6%</div>
              <div class="progress-target">Target: 75%</div>
            </div>
          </div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12,6 12,12 16,14"></polyline>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Avg OCR Time</h3>
            <div class="kpi-change positive">+8.1%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatTime(kpis.avgOcrTime, 'hrs') }}</div>
        <div class="kpi-chart">
          <div class="bar-chart">
            <div class="bar" style="height: 60%"></div>
            <div class="bar" style="height: 80%"></div>
            <div class="bar" style="height: 70%"></div>
            <div class="bar" style="height: 90%"></div>
          </div>
          <div class="chart-labels">
            <span>A</span>
            <span>B</span>
            <span>C</span>
            <span>D</span>
          </div>
        </div>
      </div>

      <!-- Row 2 -->


      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Test Approval Rate</h3>
            <div class="kpi-change positive">+4.7%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatPercentage(kpis.testApprovalRate) }}</div>
        <div class="kpi-chart">
          <div class="circular-progress">
            <svg class="progress-ring" width="140" height="140">
              <circle
                class="progress-ring-bg"
                cx="60"
                cy="60"
                r="50"
                fill="transparent"
                stroke="#e5e7eb"
                stroke-width="8"
              />
              <circle
                class="progress-ring-fill"
                cx="60"
                cy="60"
                r="50"
                fill="transparent"
                stroke="#10b981"
                stroke-width="8"
                stroke-dasharray="314"
                stroke-dashoffset="119"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="progress-text">
              <div class="progress-value">62%</div>
              <div class="progress-target">Target: 75%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 3 - New Cards -->

      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12,6 12,12 16,14"></polyline>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Avg Answer Time</h3>
            <div class="kpi-change positive">+7.8%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatTime(kpis.avgAnswerTime, 'hrs') }}</div>
        <div class="kpi-chart">
          <svg class="area-chart" viewBox="0 0 300 80">
            <defs>
              <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:0.8"/>
                <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:0.1"/>
              </linearGradient>
            </defs>
            <path 
              d="M10,60 L35,55 L60,50 L85,52 L110,45 L135,40 L160,43 L185,38 L210,35 L235,32 L260,30 L285,28 L285,75 L10,75 Z"
              fill="url(#areaGradient)" 
              stroke="#8b5cf6" 
              stroke-width="2"
            />
          </svg>
          <div class="chart-months">
            <span>Feb</span>
            <span>Mar</span>
            <span>Apr</span>
            <span>May</span>
            <span>Jun</span>
            <span>Jul</span>
            <span>Aug</span>
            <span>Sep</span>
            <span>Oct</span>
            <span>Nov</span>
            <span>Dec</span>
          </div>
        </div>
        
        <!-- Additional Answer Time Metrics -->
        <div class="answer-time-breakdown">
          <div class="breakdown-item">
            <span class="breakdown-label">Fastest:</span>
            <span class="breakdown-value">{{ formatTime(kpis.avgAnswerTime * 0.6, 'hrs') }}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">Slowest:</span>
            <span class="breakdown-value">{{ formatTime(kpis.avgAnswerTime * 1.8, 'hrs') }}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">Target:</span>
            <span class="breakdown-value">{{ formatTime(1.5, 'hrs') }}</span>
          </div>
        </div>
      </div>


      <!-- Row 4 - New Cards -->
      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon orange">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Evaluation Time</h3>
            <div class="kpi-change positive">+12.1%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatTime(kpis.evaluationTime, 'days') }}</div>
        <div class="kpi-chart">
          <div class="circular-progress">
            <svg class="progress-ring" width="140" height="140">
              <circle
                class="progress-ring-bg"
                cx="60"
                cy="60"
                r="50"
                fill="transparent"
                stroke="#e5e7eb"
                stroke-width="8"
              />
              <circle
                class="progress-ring-fill"
                cx="60"
                cy="60"
                r="50"
                fill="transparent"
                stroke="#f59e0b"
                stroke-width="8"
                stroke-dasharray="314"
                stroke-dashoffset="125"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="progress-text">
              <div class="progress-value">3.1d</div>
              <div class="progress-target">Max: 5d</div>
            </div>
          </div>
        </div>
        
        <!-- Evaluation Time Breakdown -->
        <div class="evaluation-breakdown">
          <div class="breakdown-item">
            <span class="breakdown-label">Avg Review:</span>
            <span class="breakdown-value">{{ formatTime(kpis.evaluationTime * 0.4, 'days') }}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">Avg Approval:</span>
            <span class="breakdown-value">{{ formatTime(kpis.evaluationTime * 0.6, 'days') }}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">On Time:</span>
            <span class="breakdown-value">{{ Math.round(85) }}%</span>
          </div>
        </div>
      </div>



      <!-- Row 5 - Average Evaluation Scores Card -->
      <div class="kpi-card evaluation-scores-card">
        <div class="kpi-header">
          <div class="kpi-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3v18h18"></path>
              <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
              <circle cx="18" cy="8" r="2"></circle>
              <circle cx="13" cy="13" r="2"></circle>
              <circle cx="10" cy="10" r="2"></circle>
              <circle cx="7" cy="14" r="2"></circle>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Average Evaluation Scores</h3>
            <div class="kpi-change positive">+2.4%</div>
          </div>
        </div>
        
        <!-- Main Score Display -->
        <div class="main-score-display">
          <div class="primary-score">{{ formatScore(evaluationScores.avg_overall_score) }}</div>
          <div class="score-label">Overall Score</div>
        </div>
        
        <!-- Compact Scores Display -->
        <div class="compact-scores-display">
          <div class="score-row">
            <div class="score-item-compact">
              <span class="score-name-compact">Quality:</span>
              <span class="score-value-compact">{{ formatScore(evaluationScores.avg_quality_score) }}</span>
            </div>
            <div class="score-item-compact">
              <span class="score-name-compact">Coverage:</span>
              <span class="score-value-compact">{{ formatScore(evaluationScores.avg_coverage_score) }}</span>
            </div>
          </div>
          <div class="score-row">
            <div class="score-item-compact">
              <span class="score-name-compact">Recovery:</span>
              <span class="score-value-compact">{{ formatScore(evaluationScores.avg_recovery_score) }}</span>
            </div>
            <div class="score-item-compact">
              <span class="score-name-compact">Compliance:</span>
              <span class="score-value-compact">{{ formatScore(evaluationScores.avg_compliance_score) }}</span>
            </div>
          </div>
        </div>
        
        <!-- Compact Summary -->
        <div class="compact-summary">
          <span class="summary-text">Total: {{ formatNumber(evaluationScores.total_evaluations) }} | Submitted: {{ formatNumber(evaluationScores.submitted_evaluations) }}</span>
        </div>
      </div>

      <!-- Row 6 - Risk and User Activity Cards -->
      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon red">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"></path>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Total Risks</h3>
            <div class="kpi-change positive">+5.2%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatNumber(kpis.totalRisks) }}</div>
        <div class="kpi-chart">
          <!-- Risk Distribution Donut Chart -->
          <div class="risk-donut-chart">
            <svg class="donut-svg" width="140" height="140" viewBox="0 0 140 140">
              <!-- Background circle -->
              <circle
                cx="70"
                cy="70"
                r="55"
                fill="transparent"
                stroke="#e5e7eb"
                stroke-width="8"
              />
              
              <!-- Critical Risks (Red) -->
              <circle
                cx="70"
                cy="70"
                r="55"
                fill="transparent"
                stroke="#ef4444"
                stroke-width="8"
                stroke-dasharray="86"
                stroke-dashoffset="0"
                transform="rotate(-90 70 70)"
                class="donut-segment critical"
              />
              
              <!-- High Risks (Orange) -->
              <circle
                cx="70"
                cy="70"
                r="55"
                fill="transparent"
                stroke="#f59e0b"
                stroke-width="8"
                stroke-dasharray="86"
                stroke-dashoffset="-{{ getRiskSegmentOffset('critical') }}"
                transform="rotate(-90 70 70)"
                class="donut-segment high"
              />
              
              <!-- Medium Risks (Yellow) -->
              <circle
                cx="70"
                cy="70"
                r="55"
                fill="transparent"
                stroke="#eab308"
                stroke-width="8"
                stroke-dasharray="86"
                stroke-dashoffset="-{{ getRiskSegmentOffset('critical') + getRiskSegmentOffset('high') }}"
                transform="rotate(-90 70 70)"
                class="donut-segment medium"
              />
              
              <!-- Low Risks (Green) -->
              <circle
                cx="70"
                cy="70"
                r="55"
                fill="transparent"
                stroke="#10b981"
                stroke-width="8"
                stroke-dasharray="86"
                stroke-dashoffset="-{{ getRiskSegmentOffset('critical') + getRiskSegmentOffset('high') + getRiskSegmentOffset('medium') }}"
                transform="rotate(-90 70 70)"
                class="donut-segment low"
              />
            </svg>
            
            <!-- Center content -->
            <div class="donut-center">
              <div class="center-value">{{ formatNumber(kpis.totalRisks) }}</div>
              <div class="center-label">TOTAL RISKS</div>
            </div>
          </div>
        </div>
        
        <!-- Risk Legend - Moved below the chart -->
        <div class="risk-legend-below">
          <div class="legend-item">
            <div class="legend-color critical"></div>
            <span class="legend-label">Critical</span>
            <span class="legend-value">{{ kpis.criticalRisks }}</span>
          </div>
          <div class="legend-item">
            <div class="legend-color high"></div>
            <span class="legend-label">High</span>
            <span class="legend-value">{{ Math.round(kpis.totalRisks * 0.3) }}</span>
          </div>
          <div class="legend-item">
            <div class="legend-color medium"></div>
            <span class="legend-label">Medium</span>
            <span class="legend-value">{{ Math.round(kpis.totalRisks * 0.4) }}</span>
          </div>
          <div class="legend-item">
            <div class="legend-color low"></div>
            <span class="legend-label">Low</span>
            <span class="legend-value">{{ Math.round(kpis.totalRisks * 0.3) }}</span>
          </div>
        </div>
      </div>


      <div class="kpi-card">
        <div class="kpi-header">
          <div class="kpi-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Active Users</h3>
            <div class="kpi-change positive">+12.3%</div>
          </div>
        </div>
        <div class="kpi-value">{{ formatNumber(kpis.activeUsers) }}</div>
        <div class="kpi-chart">
          <div class="user-activity">
            <div class="activity-item">
              <span class="activity-label">Recent Activity</span>
              <span class="activity-count">{{ kpis.recentActivity }}</span>
            </div>
            <div class="activity-item">
              <span class="activity-label">Overdue Approvals</span>
              <span class="activity-count">{{ kpis.overdueApprovals }}</span>
            </div>
            <div class="activity-item">
              <span class="activity-label">Overdue Assignments</span>
              <span class="activity-count">{{ kpis.overdueAssignments }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 7 - Compliance Metrics Card -->
      <div class="kpi-card compliance-card">
        <div class="kpi-header">
          <div class="kpi-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4"></path>
              <circle cx="12" cy="12" r="10"></circle>
            </svg>
          </div>
          <div class="kpi-info">
            <h3 class="kpi-title">Compliance Metrics</h3>
            <div class="kpi-change positive">+2.1%</div>
          </div>
        </div>
        
        <!-- Main Compliance Score Display -->
        <div class="main-compliance-display">
          <div class="primary-compliance-score">{{ formatScore(complianceMetrics.average_compliance_score) }}</div>
          <div class="compliance-label">Average Compliance Score</div>
        </div>
        
        <!-- Compliance Distribution Bar Chart -->
        <div class="compliance-distribution">
          <div class="compliance-bar-chart">
            <div class="bar-chart-container">
              <!-- Excellent (90-100) -->
              <div class="bar-item">
                <div class="bar-label">Excellent<br>(90-100)</div>
                <div class="bar-wrapper">
                  <div 
                    class="bar excellent" 
                    :style="{ height: getBarHeight(complianceMetrics.compliance_score_distribution.excellent_90_100) }"
                  ></div>
                </div>
                <div class="bar-value">{{ complianceMetrics.compliance_score_distribution.excellent_90_100 }}</div>
              </div>

              <!-- Good (80-89) -->
              <div class="bar-item">
                <div class="bar-label">Good<br>(80-89)</div>
                <div class="bar-wrapper">
                  <div 
                    class="bar good" 
                    :style="{ height: getBarHeight(complianceMetrics.compliance_score_distribution.good_80_89) }"
                  ></div>
                </div>
                <div class="bar-value">{{ complianceMetrics.compliance_score_distribution.good_80_89 }}</div>
              </div>

              <!-- Fair (70-79) -->
              <div class="bar-item">
                <div class="bar-label">Fair<br>(70-79)</div>
                <div class="bar-wrapper">
                  <div 
                    class="bar fair" 
                    :style="{ height: getBarHeight(complianceMetrics.compliance_score_distribution.fair_70_79) }"
                  ></div>
                </div>
                <div class="bar-value">{{ complianceMetrics.compliance_score_distribution.fair_70_79 }}</div>
              </div>

              <!-- Poor (Below 70) -->
              <div class="bar-item">
                <div class="bar-label">Poor<br>(<70)</div>
                <div class="bar-wrapper">
                  <div 
                    class="bar poor" 
                    :style="{ height: getBarHeight(complianceMetrics.compliance_score_distribution.poor_below_70) }"
                  ></div>
                </div>
                <div class="bar-value">{{ complianceMetrics.compliance_score_distribution.poor_below_70 }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Compliance Summary -->
        <div class="compliance-summary">
          <div class="summary-item">
            <span class="summary-label">Plans Meeting Threshold:</span>
            <span class="summary-value">{{ formatNumber(complianceMetrics.plans_meeting_threshold) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Compliance Rate:</span>
            <span class="summary-value">{{ formatPercentage(complianceMetrics.compliance_rate) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

export default {
  name: 'KPIDashboard',
  data() {
    return {
      loading: true,
      error: null,
      kpis: {
        planApprovalRate: 0,
        avgOcrTime: 0,
        testApprovalRate: 0,
        avgAnswerTime: 0,
        evaluationTime: 0,
        totalRisks: 0,
        criticalRisks: 0,
        activeUsers: 0,
        recentActivity: 0,
        overdueApprovals: 0,
        overdueAssignments: 0
      },
      complianceMetrics: {
        average_compliance_score: 0,
        compliance_score_distribution: {
          excellent_90_100: 0,
          good_80_89: 0,
          fair_70_79: 0,
          poor_below_70: 0,
          no_score: 0
        },
        plans_meeting_threshold: 0,
        total_plans_with_scores: 0,
        compliance_rate: 0
      },
      evaluationScores: {
        avg_overall_score: 0,
        avg_quality_score: 0,
        avg_coverage_score: 0,
        avg_recovery_score: 0,
        avg_compliance_score: 0,
        total_evaluations: 0,
        submitted_evaluations: 0,
        score_distribution: {},
        score_breakdown: {
          distribution: {},
          averages: {}
        },
        weighted_distribution: {
          counts: {},
          percentages: {}
        },
        status_distribution: {},
        evaluator_performance: {}
      },
      // Chart data for visualizations
      chartData: {
        monthlyTrends: [],
        scoreDistribution: {},
        answerTypeDistribution: {},
        completionRates: {}
      }
    }
  },
  async mounted() {
    await loggingService.logPageView('BCP', 'KPI Dashboard')
    await Promise.all([
      this.fetchKPIData(),
      this.fetchEvaluationScoresData()
    ])
    // Set up auto-refresh every 5 minutes
    this.refreshInterval = setInterval(async () => {
      await Promise.all([
        this.fetchKPIData(),
        this.fetchEvaluationScoresData()
      ])
    }, 5 * 60 * 1000)
  },
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  methods: {
    async fetchKPIData() {
      try {
        this.loading = true
        this.error = null
        
        console.log('Fetching KPI data from backend...')
        const response = await api.dashboard.kpi()
        
        if (response.data) {
          this.updateKPIs(response.data)
          console.log('KPI data updated successfully:', response.data)
          
          // Show success notification
          await this.showSuccess('KPI Data Loaded', 'KPI dashboard data loaded successfully.', {
            action: 'kpi_data_loaded',
            data_source: 'api'
          })
          
          // Show success popup
          PopupService.success('KPI dashboard data loaded successfully.', 'KPI Data Loaded')
        } else {
          throw new Error('No data received from API')
        }
      } catch (error) {
        console.error('Error fetching KPI data:', error)
        this.error = `Failed to load KPI data: ${error.message}`
        
        // Show error notification
        await this.showError('Loading Failed', 'Failed to load KPI data. Using fallback data.', {
          action: 'kpi_data_loading_failed',
          error_message: error.message,
          fallback_used: true
        })
        
        // Show error popup
        PopupService.error('Failed to load KPI data. Using fallback data.', 'Loading Failed')
        
        // Fallback to static data if API fails
        this.loadFallbackData()
      } finally {
        this.loading = false
      }
    },
    
    // Notification methods
    async showSuccess(title, message, data = {}) {
      const { showSuccess } = useNotifications()
      return await showSuccess(title, message, data)
    },
    
    async showError(title, message, data = {}) {
      const { showError } = useNotifications()
      return await showError(title, message, data)
    },
    
    async showWarning(title, message, data = {}) {
      const { showWarning } = useNotifications()
      return await showWarning(title, message, data)
    },
    
    async showInfo(title, message, data = {}) {
      const { showInfo } = useNotifications()
      return await showInfo(title, message, data)
    },
    
    updateKPIs(data) {
      // Update KPI values with real data
      this.kpis = {
        planApprovalRate: data.plan_approval_rate || 0,
        avgOcrTime: data.avg_ocr_time || 0,
        testApprovalRate: data.test_approval_rate || 0,
        avgAnswerTime: data.avg_answer_time || 0,
        evaluationTime: data.evaluation_time || 0,
        totalRisks: data.total_risks || 0,
        criticalRisks: data.critical_risks || 0,
        activeUsers: data.active_users || 0,
        recentActivity: data.recent_activity || 0,
        overdueApprovals: data.overdue_approvals || 0,
        overdueAssignments: data.overdue_assignments || 0
      }
      
      // Update compliance metrics
      if (data.compliance_metrics) {
        this.complianceMetrics = {
          average_compliance_score: data.compliance_metrics.average_compliance_score || 0,
          compliance_score_distribution: data.compliance_metrics.compliance_score_distribution || {
            excellent_90_100: 0,
            good_80_89: 0,
            fair_70_79: 0,
            poor_below_70: 0,
            no_score: 0
          },
          plans_meeting_threshold: data.compliance_metrics.plans_meeting_threshold || 0,
          total_plans_with_scores: data.compliance_metrics.total_plans_with_scores || 0,
          compliance_rate: data.compliance_metrics.compliance_rate || 0
        }
      }
      
      // Update chart data
      this.chartData = {
        monthlyTrends: data.monthly_trends || {},
        scoreDistribution: data.completion_rates || {},
        completionRates: data.completion_rates || {}
      }
    },
    
    
    loadFallbackData() {
      // Fallback to static data if API fails
      this.kpis = {
        planApprovalRate: 63.6,
        avgOcrTime: 2.4,
        testApprovalRate: 62,
        avgAnswerTime: 100.8,
        evaluationTime: 3.1,
        totalRisks: 45,
        criticalRisks: 8,
        activeUsers: 25,
        recentActivity: 18,
        overdueApprovals: 3,
        overdueAssignments: 5
      }
      
      this.complianceMetrics = {
        average_compliance_score: 85.3,
        compliance_score_distribution: {
          excellent_90_100: 45,
          good_80_89: 67,
          fair_70_79: 28,
          poor_below_70: 12,
          no_score: 4
        },
        plans_meeting_threshold: 112,
        total_plans_with_scores: 152,
        compliance_rate: 73.7
      }
      
      this.evaluationScores = {
        avg_overall_score: 82.5,
        avg_quality_score: 85.2,
        avg_coverage_score: 78.9,
        avg_recovery_score: 81.3,
        avg_compliance_score: 84.7,
        total_evaluations: 156,
        submitted_evaluations: 142,
        score_distribution: {
          excellent: 45,
          good: 67,
          fair: 28,
          poor: 12
        },
        score_breakdown: {
          distribution: {
            excellent_90_100: 45,
            good_80_89: 67,
            fair_70_79: 28,
            poor_below_70: 12
          },
          averages: {
            quality: 85.2,
            coverage: 78.9,
            recovery: 81.3,
            compliance: 84.7,
            overall: 82.5
          }
        }
      }
    },
    
    async fetchEvaluationScoresData() {
      try {
        console.log('Fetching evaluation scores data from backend...')
        const response = await api.dashboard.evaluationScores()
        
        if (response.data) {
          this.updateEvaluationScores(response.data)
          console.log('Evaluation scores data updated successfully:', response.data)
        } else {
          throw new Error('No evaluation scores data received from API')
        }
      } catch (error) {
        console.error('Error fetching evaluation scores data:', error)
        // Use fallback data for evaluation scores
        this.evaluationScores = {
          avg_overall_score: 82.5,
          avg_quality_score: 85.2,
          avg_coverage_score: 78.9,
          avg_recovery_score: 81.3,
          avg_compliance_score: 84.7,
          total_evaluations: 156,
          submitted_evaluations: 142,
          score_distribution: {},
          score_breakdown: {
            distribution: {
              excellent_90_100: 45,
              good_80_89: 67,
              fair_70_79: 28,
              poor_below_70: 12
            },
            averages: {}
          },
          weighted_distribution: {
            counts: {},
            percentages: {}
          },
          status_distribution: {},
          evaluator_performance: {}
        }
      }
    },
    
    updateEvaluationScores(data) {
      this.evaluationScores = {
        avg_overall_score: data.avg_overall_score || 0,
        avg_quality_score: data.avg_quality_score || 0,
        avg_coverage_score: data.avg_coverage_score || 0,
        avg_recovery_score: data.avg_recovery_score || 0,
        avg_compliance_score: data.avg_compliance_score || 0,
        total_evaluations: data.total_evaluations || 0,
        submitted_evaluations: data.submitted_evaluations || 0,
        score_distribution: data.score_distribution || {},
        score_breakdown: data.score_breakdown || {
          distribution: {},
          averages: {}
        },
        weighted_distribution: data.weighted_distribution || {
          counts: {},
          percentages: {}
        },
        status_distribution: data.status_distribution || {},
        evaluator_performance: data.evaluator_performance || {}
      }
    },
    
    formatPercentage(value) {
      return `${value.toFixed(1)}%`
    },
    
    formatTime(value, unit = 'hrs') {
      if (unit === 'hrs') {
        return `${value.toFixed(1)} hrs`
      } else if (unit === 'days') {
        return `${value.toFixed(1)} d`
      }
      return value.toString()
    },
    
    formatNumber(value) {
      return value.toLocaleString()
    },
    
    formatScore(value) {
      if (value === null || value === undefined) return '0.0'
      return value.toFixed(1)
    },
    
    getChangeIndicator(current, previous = 0) {
      if (previous === 0) return 'positive'
      const change = ((current - previous) / previous) * 100
      return change >= 0 ? 'positive' : 'negative'
    },
    
    getChangeValue(current, previous = 0) {
      if (previous === 0) return '+0.0%'
      const change = ((current - previous) / previous) * 100
      const sign = change >= 0 ? '+' : ''
      return `${sign}${change.toFixed(1)}%`
    },
    
    getBarHeight(value) {
      // Calculate the maximum value for scaling
      const distribution = this.complianceMetrics.compliance_score_distribution
      const maxValue = Math.max(
        distribution.excellent_90_100,
        distribution.good_80_89,
        distribution.fair_70_79,
        distribution.poor_below_70
      )
      
      // If max value is 0, return 16px minimum height for visibility
      if (maxValue === 0) return '16px'
      
      // If current value is 0, return minimum height
      if (value === 0) return '16px'
      
      // Calculate percentage height with better scaling
      // Maximum bar height is 100px, minimum is 16px
      // Add some base height to make bars more visible
      const percentage = (value / maxValue) * 100
      const baseHeight = 16 // Minimum height for visibility
      const variableHeight = (percentage / 100) * 84 // Remaining height for scaling
      const totalHeight = baseHeight + variableHeight
      
      return `${totalHeight}px`
    },
    
    getRiskSegmentOffset(riskType) {
      const totalRisks = this.kpis.totalRisks
      if (totalRisks === 0) return 0
      
      let segmentValue = 0
      const circumference = 346 // 2 * PI * 55
      
      switch (riskType) {
        case 'critical':
          segmentValue = this.kpis.criticalRisks
          break
        case 'high':
          segmentValue = Math.round(totalRisks * 0.3)
          break
        case 'medium':
          segmentValue = Math.round(totalRisks * 0.4)
          break
        case 'low':
          segmentValue = Math.round(totalRisks * 0.3)
          break
        default:
          return 0
      }
      
      return (segmentValue / totalRisks) * circumference
    }
  }
}
</script>

<style scoped>
@import './KPIDashboard.css';
</style>
