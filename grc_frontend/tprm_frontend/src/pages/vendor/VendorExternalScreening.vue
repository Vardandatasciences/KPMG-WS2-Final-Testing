<template>
  <div class="external-screening-container">
    <!-- Screening Results Sidebar -->
    <div class="screening-results-panel">
      <div class="panel-header screening-panel-header">
        <h2 class="panel-title">Screening Results</h2>
        <div class="panel-header-actions">
          <button
            type="button"
            class="btn-run-screening"
            :disabled="!selectedVendor || !selectedVendor.vendor_code || runScreeningInProgress"
            @click="runScreeningNow"
            title="Run external screening now for the selected vendor"
          >
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': runScreeningInProgress }"></i>
            {{ runScreeningInProgress ? 'Running...' : 'Run screening now' }}
          </button>
          <button type="button" class="btn-schedule-screening" @click="openScheduleModal">
            <i class="fas fa-calendar-alt"></i>
            Schedule Screening
          </button>
        </div>
      </div>
      
      <div class="vendor-dropdown-container">
        <!-- Custom Dropdown with integrated search -->
        <div class="custom-dropdown">
          <div 
            class="dropdown-trigger"
            @click="toggleDropdown"
            :class="{ active: isDropdownOpen }"
          >
            <span class="dropdown-text">
              {{ selectedVendor ? `${selectedVendor.company_name} (${selectedVendor.vendor_code || 'No Code'})` : 'Search vendors by name or code...' }}
            </span>
            <span class="dropdown-arrow" :class="{ rotated: isDropdownOpen }">▼</span>
          </div>
          
          <div v-if="isDropdownOpen" class="dropdown-menu">
            <!-- Search Input inside dropdown -->
            <div class="dropdown-search">
              <input 
                v-model="searchQuery"
                @input="onSearchInput"
                type="text"
                placeholder="Search vendors..."
                class="dropdown-search-input"
                @click.stop
              />
              <div v-if="searchQuery" class="search-clear" @click="clearSearch">
                <span class="clear-icon">×</span>
              </div>
            </div>
            
            <!-- Vendor Options -->
            <div class="dropdown-options">
              <div 
                v-if="filteredVendors.length === 0 && searchQuery"
                class="no-results-option"
              >
                No vendors found matching "{{ searchQuery }}"
              </div>
              <div 
                v-else-if="filteredVendors.length === 0"
                class="no-results-option"
              >
                No vendors available
              </div>
              <div 
                v-for="vendor in filteredVendors" 
                :key="vendor.id"
                class="dropdown-option"
                :class="{ selected: selectedVendorId == vendor.id }"
                @click="selectVendor(vendor)"
              >
                <span class="vendor-name">{{ vendor.company_name }}</span>
                <span class="vendor-code">({{ vendor.vendor_code || 'No Code' }})</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Search results info -->
        <div v-if="searchQuery && filteredVendors.length > 0" class="search-results-info">
          Found {{ filteredVendors.length }} vendor(s)
        </div>
      </div>
      
      <div class="results-list">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading screening results...</p>
        </div>
        
        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <div class="error-icon">⚠</div>
          <p>{{ error }}</p>
          <button @click="onVendorChange()" class="retry-button">Retry</button>
        </div>
        
        <!-- Vendor Screening Results -->
        <div v-else-if="selectedVendor && vendorScreeningResults.length > 0">
          <template v-for="screening in vendorScreeningResults" :key="screening.screening_id">
            <div 
              class="result-item"
              :class="{ active: selectedScreening?.screening_id === screening.screening_id }"
              @click="selectScreening(screening)"
            >
            <div class="result-header">
              <h3 class="result-company">{{ screening.screening_type }}</h3>
              <div class="result-icons">
                <span v-if="screening.status === 'CLEAR'" class="status-icon cleared">✓</span>
                <span v-else-if="screening.status === 'POTENTIAL_MATCH'" class="status-icon warning">⚠</span>
                <span v-else-if="screening.status === 'CONFIRMED_MATCH'" class="status-icon blocked">✗</span>
                <span v-else class="status-icon pending">⏳</span>
              </div>
            </div>
            
            <div class="result-meta">
              <span class="result-source">{{ screening.screening_type }}</span>
              <span
                v-if="isSimulatedType(screening.screening_type)"
                class="result-source-simulated"
              >
                (simulated – no external API)
              </span>
              <span class="result-date">{{ formatDate(screening.screening_date) }}</span>
            </div>
            
            <div class="result-status">
              <span 
                class="status-badge" 
                :class="screening.status.toLowerCase()"
              >
                {{ getStatusText(screening.status) }}
              </span>
              <span class="match-count">{{ screening.total_matches }} matches</span>
            </div>
            
            <!-- Risk Level Indicator -->
            <div v-if="screening.high_risk_matches > 0" class="risk-indicator">
              <span class="risk-badge high-risk">{{ screening.high_risk_matches }} High Risk</span>
            </div>
            </div>
          </template>
        </div>
        
        <!-- No Results State -->
        <div v-else-if="selectedVendor && vendorScreeningResults.length === 0" class="no-results-state">
          <div class="no-results-icon">📋</div>
          <h3>No Screening Results</h3>
          <p>This vendor has not been screened yet.</p>
          <div class="no-results-help">
            <p><strong>Possible reasons:</strong></p>
            <ul>
              <li>Vendor was just registered - screening may still be in progress</li>
              <li>Vendor was created manually without triggering automatic screening</li>
              <li>Screening failed during the registration process</li>
            </ul>
            <p><strong>What to do:</strong></p>
            <ul>
              <li>Wait a few minutes and refresh this page</li>
              <li>Check browser console for any error messages</li>
              <li>Contact support if the issue persists</li>
            </ul>
          </div>
        </div>
        
        <!-- Default State -->
        <div v-else class="default-state">
          <div class="default-icon">🔍</div>
          <h3>Select a Vendor</h3>
          <p>Choose a vendor from the dropdown to view their screening results.</p>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="match-review-panel">
      <div class="panel-header">
        <h2 class="panel-title">
          {{ selectedScreening ? `${selectedVendor?.company_name} - ${selectedScreening.screening_type}` : selectedVendor ? `${selectedVendor.company_name} - Select Screening` : 'Select a vendor' }}
        </h2>
        
        <!-- Horizontal Tabs -->
        <div v-if="selectedVendor && selectedScreening" class="horizontal-tabs">
          <template v-for="tab in tabs" :key="tab.id">
            <button 
              class="horizontal-tab"
              :class="{ active: activeTab === tab.id }"
              @click="activeTab = tab.id"
            >
              {{ tab.label }}
              <span v-if="tab.id === 'matches' && selectedScreening?.total_matches" class="tab-count">
                ({{ selectedScreening.total_matches }})
              </span>
            </button>
          </template>
        </div>
        
        <div class="header-actions" v-if="selectedScreening">
          <button class="btn-primary" @click="markAsCleared" v-if="selectedScreening.status !== 'CLEAR'">
            <i class="icon-clear"></i>
            Clear All
          </button>
        </div>
      </div>

      <div v-if="selectedVendor && selectedScreening" class="match-content">

        <!-- Matches Content -->
        <div v-if="activeTab === 'matches'" class="matches-content">
          <!-- Zero Matches State -->
          <div v-if="matches.length === 0" class="zero-matches-state">
            <div class="zero-matches-icon">🎉</div>
            <h3 class="zero-matches-title">No Matches Found</h3>
            <p class="zero-matches-description">
              Great news! No potential matches were found during the screening process for this vendor.
            </p>
            <div class="zero-matches-details">
              <div class="detail-item">
                <span class="detail-label">Screening Status:</span>
                <span class="detail-value status-clear">CLEARED</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Risk Level:</span>
                <span class="detail-value risk-low">LOW</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Last Updated:</span>
                <span class="detail-value">{{ formatDate(selectedResult?.last_updated) }}</span>
              </div>
            </div>
          </div>

          <!-- Matches List -->
          <div v-else>
            <template v-for="match in matches" :key="match.id">
              <div 
                class="match-card"
                :class="{ frozen: match.reviewStatus !== 'Under Review' }"
              >
            <div class="match-header">
              <div class="match-type">
                <span class="match-type-badge" :class="(match.type || '').toLowerCase()">
                  {{ match.type }}
                </span>
                <span class="match-score">Score: {{ match.score }}</span>
                <span 
                  class="match-status-badge"
                  :class="(match.reviewStatus || '').toLowerCase().replace(' ', '-')"
                >
                  {{ match.reviewStatus }}
                </span>
              </div>
            </div>

            <div class="match-details">
              <h4 class="match-title">{{ match.title }}</h4>
              
              <!-- Resolution note input (always editable) -->
              <div class="match-section">
                <h5 class="section-title">Resolution Note</h5>
                <textarea
                  class="resolution-note-input"
                  v-model="resolutionNotes[match.id]"
                  :placeholder="match.reviewerNotes || 'Add resolution note...'"
                  rows="2"
                ></textarea>
              </div>

              <div class="match-section">
                <h5 class="section-title">Details</h5>
                <p class="section-content">{{ match.details }}</p>
              </div>
            </div>

            <div class="match-actions">
              <div class="resolution-buttons">
                <button 
                  class="btn-action clear"
                  :class="{ selected: selectedResolutionStatus[match.id] === 'CLEARED' }"
                  @click="setResolutionStatus(match.id, 'CLEARED')"
                  :disabled="loading"
                >
                  <i class="icon-check"></i>
                  {{ selectedResolutionStatus[match.id] === 'CLEARED' ? '✓ Dismiss Risk' : 'Dismiss Risk' }}
                </button>
                <button 
                  class="btn-action escalate"
                  :class="{ selected: selectedResolutionStatus[match.id] === 'ESCALATED' }"
                  @click="setResolutionStatus(match.id, 'ESCALATED')"
                  :disabled="loading"
                >
                  <i class="icon-alert"></i>
                  {{ selectedResolutionStatus[match.id] === 'ESCALATED' ? '⚠ Mark as Risk' : 'Mark as Risk' }}
                </button>
              </div>
              <button 
                class="btn-action submit"
                @click="submitResolution(match.id)"
                :disabled="loading || !pendingChanges[match.id] || !selectedResolutionStatus[match.id]"
              >
                <i class="icon-save"></i>
                Submit
              </button>
            </div>
          </div>
            </template>
          </div>
        </div>

        <!-- Summary Content -->
        <div v-else-if="activeTab === 'summary'" class="summary-content">
          <div class="summary-header">
            <h3 class="summary-title">Screening Overview</h3>
            <p class="summary-subtitle">Complete analysis results for {{ selectedVendor?.company_name }}</p>
          </div>
          
          <div class="summary-grid">
            <div class="summary-card primary">
              <div class="card-icon">
                <span class="icon">📊</span>
              </div>
              <div class="card-content">
                <h4 class="card-label">Total Matches</h4>
                <div class="summary-value primary">{{ selectedScreening?.total_matches || 0 }}</div>
                <div class="card-description">Potential matches found</div>
              </div>
            </div>
            
            <div class="summary-card danger">
              <div class="card-icon">
                <span class="icon">⚠️</span>
              </div>
              <div class="card-content">
                <h4 class="card-label">High Risk</h4>
                <div class="summary-value danger">{{ selectedScreening?.high_risk_matches || 0 }}</div>
                <div class="card-description">Critical matches identified</div>
              </div>
            </div>
            
            <div class="summary-card" :class="getStatusCardClass(selectedScreening?.status)">
              <div class="card-icon">
                <span class="icon">{{ getStatusIcon(selectedScreening?.status) }}</span>
              </div>
              <div class="card-content">
                <h4 class="card-label">Status</h4>
                <div class="summary-value" :class="getStatusClass(selectedScreening?.status)">
                  {{ getStatusText(selectedScreening?.status) }}
                </div>
                <div class="card-description">Current screening status</div>
              </div>
            </div>
            
            <div class="summary-card info">
              <div class="card-icon">
                <span class="icon">🔍</span>
              </div>
              <div class="card-content">
                <h4 class="card-label">Screening Type</h4>
                <div class="summary-value info">{{ selectedScreening?.screening_type || 'N/A' }}</div>
                <div class="card-description">Type of screening performed</div>
              </div>
            </div>
          </div>
          
          <!-- Additional Details Section -->
          <div class="summary-details">
            <div class="details-header">
              <h4>Additional Information</h4>
            </div>
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">Vendor Code:</span>
                <span class="detail-value">{{ selectedVendor?.vendor_code || 'Not assigned' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Screening Date:</span>
                <span class="detail-value">{{ formatDate(selectedScreening?.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Last Updated:</span>
                <span class="detail-value">{{ formatDate(selectedScreening?.updated_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Risk Level:</span>
                <span class="detail-value" :class="getRiskLevelClass()">
                  {{ getRiskLevel() }}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Empty State -->
      <div v-else-if="selectedVendor && !selectedScreening" class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>Select a Screening Type</h3>
        <p>Choose a screening result from the left panel to view match details</p>
      </div>
      
      <!-- No Vendor Selected State -->
      <div v-else class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>No vendor selected</h3>
        <p>Select a vendor from the dropdown to view their screening results</p>
      </div>
    </div>
  </div>

  <!-- Schedule Screening Modal -->
  <div v-if="showScheduleModal" class="schedule-modal-overlay" @click.self="closeScheduleModal">
    <div class="schedule-modal-content">
      <button type="button" class="schedule-modal-close" @click="closeScheduleModal" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
      <div class="schedule-modal-header">
        <h2>Schedule External Screening</h2>
      </div>
      <div class="schedule-modal-body">
        <p class="schedule-modal-hint">Run external screening for a vendor at the chosen time. Select vendor, frequency, and time.</p>

        <div class="schedule-form-group schedule-form-group-full">
          <label class="schedule-form-label">Select Vendor</label>
          <select v-model="scheduleForm.vendor_id" class="schedule-form-select" required @change="onModalVendorChange">
            <option value="">Choose a vendor...</option>
            <option v-for="v in uniqueVendors" :key="v.id" :value="v.id">
              {{ v.company_name }} ({{ v.vendor_code || 'No Code' }})
            </option>
          </select>
        </div>

        <div class="schedule-form-row">
          <div class="schedule-form-field schedule-field-freq">
            <label class="schedule-form-label">Frequency</label>
            <select v-model="scheduleForm.frequency" class="schedule-form-select" @change="applyScheduleCron">
              <option value="daily">Daily</option>
              <option value="weekdays">Weekdays</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="yearly">Yearly</option>
              <option value="does_not_repeat">One-time</option>
            </select>
          </div>
          <template v-if="scheduleForm.frequency === 'does_not_repeat'">
            <div class="schedule-form-field">
              <label class="schedule-form-label">Date</label>
              <input type="date" v-model="scheduleForm.oneTimeDate" class="schedule-form-input" :min="scheduleStartDateMin" />
            </div>
            <div class="schedule-form-field">
              <label class="schedule-form-label">Time</label>
              <input type="time" v-model="scheduleForm.oneTimeTime" class="schedule-form-input" />
            </div>
          </template>
          <template v-else>
            <div class="schedule-form-field">
              <label class="schedule-form-label">Time</label>
              <input type="time" v-model="scheduleForm.time" class="schedule-form-input" @change="applyScheduleCron" />
            </div>
          </template>
        </div>

        <div class="schedule-form-row schedule-form-row-start">
          <div class="schedule-form-field schedule-field-start">
            <label class="schedule-form-label">Start date <span class="schedule-optional">(optional)</span></label>
            <input type="date" v-model="scheduleForm.startDate" class="schedule-form-input" :min="scheduleStartDateMin" />
            <span class="schedule-hint-inline">Leave empty to start immediately.</span>
          </div>
        </div>

        <div v-if="scheduleForm.frequency === 'weekly' || ['monthly','quarterly','yearly'].includes(scheduleForm.frequency)" class="schedule-form-block-extra">
          <span class="schedule-subheading">Recurrence options</span>
          <div class="schedule-form-row schedule-form-row-extra">
            <div v-if="scheduleForm.frequency === 'weekly'" class="schedule-form-field">
              <label class="schedule-form-label">Day of week</label>
              <select v-model="scheduleForm.dayOfWeek" class="schedule-form-select" @change="applyScheduleCron">
                <option :value="0">Monday</option>
                <option :value="1">Tuesday</option>
                <option :value="2">Wednesday</option>
                <option :value="3">Thursday</option>
                <option :value="4">Friday</option>
                <option :value="5">Saturday</option>
                <option :value="6">Sunday</option>
              </select>
            </div>
            <div v-if="['monthly','quarterly','yearly'].includes(scheduleForm.frequency)" class="schedule-form-field">
              <label class="schedule-form-label">Day of month (1–28)</label>
              <input type="number" v-model.number="scheduleForm.dayOfMonth" min="1" max="28" class="schedule-form-input schedule-day-input" @change="applyScheduleCron" />
            </div>
            <div v-if="scheduleForm.frequency === 'yearly'" class="schedule-form-field">
              <label class="schedule-form-label">Month</label>
              <select v-model="scheduleForm.month" class="schedule-form-select" @change="applyScheduleCron">
                <option :value="1">January</option>
                <option :value="2">February</option>
                <option :value="3">March</option>
                <option :value="4">April</option>
                <option :value="5">May</option>
                <option :value="6">June</option>
                <option :value="7">July</option>
                <option :value="8">August</option>
                <option :value="9">September</option>
                <option :value="10">October</option>
                <option :value="11">November</option>
                <option :value="12">December</option>
              </select>
            </div>
          </div>
        </div>

        <details class="schedule-advanced">
          <summary>Advanced: custom cron expression</summary>
          <input type="text" v-model="scheduleForm.cronExpression" class="schedule-form-input schedule-cron-input" placeholder="e.g. 0 9 * * 1-5" />
        </details>

        <!-- Saved Schedules list -->
        <div class="saved-schedules-section">
          <div class="saved-schedules-header-row">
            <h3 class="saved-schedules-heading">Saved Schedules</h3>
            <span v-if="schedules.length" class="saved-schedules-count">{{ schedules.length }} schedule{{ schedules.length > 1 ? 's' : '' }}</span>
          </div>

          <div v-if="schedulesLoading" class="saved-schedules-loading">
            <span class="ss-spinner"></span> Loading schedules…
          </div>
          <div v-else-if="!scheduleForm.vendor_id" class="saved-schedules-empty">
            Select a vendor above to see its schedules.
          </div>
          <div v-else-if="schedules.length === 0" class="saved-schedules-empty">
            No schedules saved yet for this vendor.
          </div>

          <div v-else class="saved-schedules-cards">
            <div v-for="s in schedules" :key="s.id" class="ss-card">
              <!-- Card header -->
              <div class="ss-card-header">
                <div class="ss-card-title-row">
                  <span class="ss-freq-badge">{{ scheduleFrequencyLabel(s.frequency) }}</span>
                  <span v-if="scheduleTimeFromCron(s.cron_expression)" class="ss-time-label">
                    @ {{ scheduleTimeFromCron(s.cron_expression) }}
                  </span>
                  <span v-else-if="s.scheduled_at" class="ss-time-label">
                    @ {{ formatScheduleNextRun(s.scheduled_at) }}
                  </span>
                </div>
                <div class="ss-card-actions">
                  <span :class="['schedule-status-badge', s.status]">{{ s.status }}</span>
                  <button type="button" class="btn-delete-schedule" @click="deleteSchedule(s.id)" title="Remove schedule">✕</button>
                </div>
              </div>

              <!-- Card body: run info -->
              <div class="ss-card-body">
                <div class="ss-info-row">
                  <span class="ss-info-label">Next run</span>
                  <span class="ss-info-value" :class="{ 'ss-overdue': isScheduleOverdue(s) }">
                    {{ s.next_run_at ? formatScheduleNextRun(s.next_run_at) : '—' }}
                    <span v-if="isScheduleOverdue(s)" class="ss-overdue-tag">Pending</span>
                  </span>
                </div>
                <div class="ss-info-row">
                  <span class="ss-info-label">Last run</span>
                  <span class="ss-info-value">{{ s.last_run_at ? formatScheduleNextRun(s.last_run_at) : 'Not yet run' }}</span>
                </div>
                <div v-if="s.cron_expression" class="ss-info-row">
                  <span class="ss-info-label">Cron</span>
                  <code class="ss-cron-code">{{ s.cron_expression }}</code>
                </div>
              </div>

              <!-- Last run results -->
              <div v-if="s.last_run_results && s.last_run_results.length" class="ss-results">
                <span class="ss-results-label">Last run results</span>
                <div class="ss-results-grid">
                  <div v-for="r in s.last_run_results" :key="r.screening_type" class="ss-result-chip" :class="r.status.toLowerCase()">
                    <span class="ss-result-type">{{ r.screening_type }}</span>
                    <span class="ss-result-status-icon">
                      <template v-if="r.status === 'CLEAR'">✓</template>
                      <template v-else-if="r.status === 'POTENTIAL_MATCH'">⚠</template>
                      <template v-else-if="r.status === 'CONFIRMED_MATCH'">✗</template>
                      <template v-else>⏳</template>
                    </span>
                    <span class="ss-result-matches">{{ r.total_matches }} match{{ r.total_matches !== 1 ? 'es' : '' }}</span>
                    <span v-if="r.high_risk_matches > 0" class="ss-result-high-risk">{{ r.high_risk_matches }} high risk</span>
                  </div>
                </div>
              </div>
              <div v-else-if="s.last_run_at" class="ss-results-empty">
                No results recorded for last run.
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="schedule-modal-footer">
        <button type="button" class="btn-schedule-cancel" @click="closeScheduleModal">Cancel</button>
        <button type="button" class="btn-schedule-submit" @click="submitSchedule" :disabled="!scheduleForm.vendor_id || scheduleSubmitting">
          {{ scheduleSubmitting ? 'Scheduling...' : 'Schedule Screening' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import apiClient from '@/config/axios.js';
import PopupModal from '@/popup/PopupModal.vue';
import { PopupService } from '@/popup/popupService';
import notificationService from '@/services/notificationService';
import loggingService from '@/services/loggingService';
import { getTprmApiV1BaseUrl, getTprmApiUrl, getApiV1Url } from '@/utils/backendEnv';

export default {
  name: 'VendorExternalScreening',
  components: {
    PopupModal
  },
  data() {
    return {
      selectedVendor: null,
      selectedScreening: null,
      selectedVendorId: '',
      activeTab: 'matches',
      loading: false,
      error: null,
      vendors: [],
      vendorScreeningResults: [],
      searchQuery: '',
      searchTimeout: null,
      isDropdownOpen: false,
      tabs: [
        { id: 'matches', label: 'Matches' },
        { id: 'summary', label: 'Summary' }
      ],
      matches: [],
      resolutionNotes: {},
      pendingChanges: {},
      selectedResolutionStatus: {},
      showScheduleModal: false,
      scheduleSubmitting: false,
      schedulesLoading: false,
      schedules: [],
      runScreeningInProgress: false,
      scheduleForm: {
        vendor_id: '',
        frequency: 'daily',
        time: '09:00',
        oneTimeDate: '',
        oneTimeTime: '09:00',
        startDate: '',
        dayOfWeek: 1,
        dayOfMonth: 1,
        month: 1,
        cronExpression: ''
      }
    }
  },
  computed: {
    uniqueVendors() {
      // Remove duplicates based on vendor ID
      const uniqueVendors = [];
      const seenIds = new Set();
      
      this.vendors.forEach(vendor => {
        if (!seenIds.has(vendor.id)) {
          seenIds.add(vendor.id);
          uniqueVendors.push(vendor);
        }
      });
      
      return uniqueVendors;
    },
    
    filteredVendors() {
      if (!this.searchQuery.trim()) {
        return this.uniqueVendors;
      }
      
      const query = this.searchQuery.toLowerCase().trim();
      return this.uniqueVendors.filter(vendor => {
        const companyName = (vendor.company_name || '').toLowerCase();
        const vendorCode = (vendor.vendor_code || '').toLowerCase();
        const legalName = (vendor.legal_name || '').toLowerCase();
        
        return companyName.includes(query) || 
               vendorCode.includes(query) || 
               legalName.includes(query);
      });
    },
    scheduleStartDateMin() {
      return new Date().toISOString().slice(0, 10);
    }
  },
  methods: {
    isSimulatedType(type) {
      const t = (type || '').toUpperCase()
      return false
    },
    async fetchVendors(searchQuery = '') {
      this.loading = true;
      this.error = null;
      try {
        // Use getApiV1Url since backend is at /api/v1/vendor-core/ not /api/tprm/v1/vendor-core/
        let url = getApiV1Url('vendor-core/temp-vendors/');
        
        // Add search parameter if provided
        if (searchQuery.trim()) {
          url += `?search=${encodeURIComponent(searchQuery.trim())}`;
        }
        
        console.log('🔍 Fetching vendors from:', url);
        const response = await apiClient.get(url);
        
        console.log('📡 Raw API response:', response.data);
        
        // Handle different response formats
        let vendorData = [];
        if (response.data && Array.isArray(response.data)) {
          // Direct array response
          vendorData = response.data;
        } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
          // Paginated response
          vendorData = response.data.results;
        } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
          // Custom wrapper response
          vendorData = response.data.data;
        } else {
          console.error('❌ Unexpected API response format:', response.data);
          this.error = 'Unexpected response format from server';
          return;
        }
        
        // Filter out vendors without essential data
        this.vendors = vendorData.filter(vendor => 
          vendor && (vendor.company_name || vendor.legal_name || vendor.vendor_code)
        );
        
        console.log(`✅ Successfully loaded ${this.vendors.length} vendors`);
        if (response.data.tenant_id) {
          console.log(`🏢 Tenant ID: ${response.data.tenant_id}`);
        } else {
          console.warn('⚠️ No tenant_id in response');
        }
        console.log('📋 Sample vendors:', this.vendors.slice(0, 3));
        
        if (this.vendors.length === 0) {
          console.warn('⚠️ No vendors found in database');
          const helpMessage = response.data.help || 'No vendors found in the database. Please add some vendors first.';
          if (!searchQuery) {
            this.error = helpMessage;
          }
          console.log('💡 Help:', helpMessage);
        }
        
      } catch (error) {
        console.error('❌ Error fetching vendors:', error);
        console.error('🔍 Error details:', error.response?.data);
        
        let errorMessage = 'Failed to load vendors';
        
        if (error.response) {
          // Server responded with error
          if (error.response.status === 403) {
            errorMessage = 'Access denied. Please check your permissions.';
          } else if (error.response.status === 401) {
            errorMessage = 'Authentication required. Please log in.';
          } else if (error.response.status === 404) {
            errorMessage = 'Vendors endpoint not found. Please contact support.';
          } else if (error.response.data?.message) {
            errorMessage = error.response.data.message;
          } else if (error.response.data?.error) {
            errorMessage = error.response.data.error;
          } else {
            errorMessage = `Failed to load vendors: ${error.message}`;
          }
        } else if (error.request) {
          // Request made but no response
          errorMessage = 'No response from server. Please check your connection.';
        } else {
          // Other error
          errorMessage = `Failed to load vendors: ${error.message}`;
        }
        
        this.error = errorMessage;
        this.vendors = [];
      } finally {
        this.loading = false;
      }
    },
    
    onSearchInput() {
      // Clear existing timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }
      
      // Set new timeout for debounced search
      this.searchTimeout = setTimeout(() => {
        console.log('Search query:', this.searchQuery);
        
        // Reset selected vendor when search changes
        if (this.searchQuery && this.selectedVendorId) {
          const stillVisible = this.filteredVendors.some(v => v.id == this.selectedVendorId);
          if (!stillVisible) {
            this.selectedVendorId = '';
            this.selectedVendor = null;
            this.selectedScreening = null;
            this.vendorScreeningResults = [];
            this.matches = [];
          }
        }
        
        // Optional: Implement server-side search for large datasets
        // this.fetchVendors(this.searchQuery);
      }, 300);
    },
    
    clearSearch() {
      this.searchQuery = '';
      this.selectedVendorId = '';
      this.selectedVendor = null;
      this.selectedScreening = null;
      this.vendorScreeningResults = [];
      this.matches = [];
      this.isDropdownOpen = false;
    },
    
    getDropdownPlaceholder() {
      if (this.searchQuery && this.filteredVendors.length === 0) {
        return 'No vendors match your search';
      }
      if (this.vendors.length === 0) {
        return 'No vendors available';
      }
      return 'Select vendors';
    },
    
    toggleDropdown() {
      this.isDropdownOpen = !this.isDropdownOpen;
      if (this.isDropdownOpen && !this.searchQuery) {
        this.searchQuery = '';
      }
    },

    openScheduleModal() {
      this.showScheduleModal = true;
      this.scheduleForm.vendor_id = this.selectedVendorId || '';
      this.schedules = [];
      const vc = this._modalVendorCode();
      if (vc) this.loadSchedules(vc);
    },

    // Returns the vendor_code for whichever vendor is currently chosen in the modal
    _modalVendorCode() {
      const v = this.uniqueVendors.find(v => String(v.id) === String(this.scheduleForm.vendor_id));
      return v ? v.vendor_code : null;
    },

    // Called when the vendor dropdown inside the modal changes
    onModalVendorChange() {
      this.schedules = [];
      const vc = this._modalVendorCode();
      if (vc) this.loadSchedules(vc);
    },

    async loadSchedules(vendorCode) {
      if (!vendorCode) return;
      this.schedulesLoading = true;
      try {
        const url = getApiV1Url(`management/vendors/${encodeURIComponent(vendorCode)}/screening-schedules/`);
        const response = await apiClient.get(url);
        if (response.data && response.data.success) {
          this.schedules = response.data.schedules || [];
        }
      } catch (err) {
        console.error('Failed to load schedules:', err);
      } finally {
        this.schedulesLoading = false;
      }
    },

    async deleteSchedule(scheduleId) {
      const vc = this._modalVendorCode();
      if (!vc) return;
      try {
        const url = getApiV1Url(
          `management/vendors/${encodeURIComponent(vc)}/screening-schedules/${scheduleId}/`
        );
        await apiClient.delete(url);
        this.schedules = this.schedules.filter(s => s.id !== scheduleId);
        PopupService.success('Schedule removed.', 'Schedule Screening');
      } catch (err) {
        console.error('Delete schedule error:', err);
        PopupService.error('Failed to delete schedule.', 'Schedule Screening');
      }
    },

    formatScheduleNextRun(isoStr) {
      if (!isoStr) return 'Not set';
      try {
        return new Date(isoStr).toLocaleString();
      } catch {
        return isoStr;
      }
    },

    scheduleFrequencyLabel(freq) {
      const labels = {
        does_not_repeat: 'One-time',
        daily: 'Daily',
        weekdays: 'Weekdays',
        weekly: 'Weekly',
        monthly: 'Monthly',
        quarterly: 'Quarterly',
        yearly: 'Yearly',
      };
      return labels[freq] || freq;
    },

    // Extracts HH:MM from a cron expression like "0 9 * * *"
    scheduleTimeFromCron(cronExpr) {
      if (!cronExpr) return '';
      const parts = cronExpr.trim().split(/\s+/);
      if (parts.length >= 2) {
        const m = String(parts[0]).padStart(2, '0');
        const h = String(parts[1]).padStart(2, '0');
        if (!isNaN(parseInt(h)) && !isNaN(parseInt(m))) {
          return `${h}:${m}`;
        }
      }
      return '';
    },

    // Returns true if next_run_at is in the past and schedule is active
    isScheduleOverdue(s) {
      if (!s.next_run_at || !s.is_active) return false;
      return new Date(s.next_run_at) < new Date();
    },

    async runScreeningNow() {
      if (!this.selectedVendor || !this.selectedVendor.vendor_code) {
        PopupService.warning('Select a vendor with a vendor code to run screening.', 'Run Screening');
        return;
      }
      this.runScreeningInProgress = true;
      try {
        const url = getApiV1Url(`management/vendors/${encodeURIComponent(this.selectedVendor.vendor_code)}/external-screening/`);
        const response = await apiClient.post(url);
        if (response.data && response.data.success) {
          PopupService.success(
            `Screening completed. ${(response.data.screening_results || []).length} type(s) run. Refresh results to see updates.`,
            'Run Screening'
          );
          await this.onVendorChange();
        } else {
          PopupService.warning(response.data?.error || 'Screening request completed with no results.', 'Run Screening');
        }
      } catch (err) {
        console.error('Run screening error:', err);
        const msg = err.response?.data?.error || err.response?.data?.message || err.message || 'Failed to run screening.';
        PopupService.error(msg, 'Run Screening');
      } finally {
        this.runScreeningInProgress = false;
      }
    },

    closeScheduleModal() {
      this.showScheduleModal = false;
      this.scheduleForm = {
        vendor_id: '',
        frequency: 'daily',
        time: '09:00',
        oneTimeDate: '',
        oneTimeTime: '09:00',
        startDate: '',
        dayOfWeek: 1,
        dayOfMonth: 1,
        month: 1,
        cronExpression: ''
      };
    },

    applyScheduleCron() {
      const f = this.scheduleForm.frequency;
      const [h, m] = (this.scheduleForm.time || '09:00').split(':').map(x => parseInt(x, 10) || 0);
      const minute = m;
      const hour = h;
      if (f === 'does_not_repeat') {
        this.scheduleForm.cronExpression = '';
        return;
      }
      if (f === 'daily') {
        this.scheduleForm.cronExpression = `${minute} ${hour} * * *`;
        return;
      }
      if (f === 'weekdays') {
        this.scheduleForm.cronExpression = `${minute} ${hour} * * 1-5`;
        return;
      }
      if (f === 'weekly') {
        const dow = this.scheduleForm.dayOfWeek;
        const cronDow = dow === 6 ? 0 : dow + 1;
        this.scheduleForm.cronExpression = `${minute} ${hour} * * ${cronDow}`;
        return;
      }
      if (f === 'monthly') {
        const dom = Math.max(1, Math.min(28, this.scheduleForm.dayOfMonth || 1));
        this.scheduleForm.cronExpression = `${minute} ${hour} ${dom} * *`;
        return;
      }
      if (f === 'quarterly') {
        const dom = Math.max(1, Math.min(28, this.scheduleForm.dayOfMonth || 1));
        this.scheduleForm.cronExpression = `${minute} ${hour} ${dom} 1,4,7,10 *`;
        return;
      }
      if (f === 'yearly') {
        const dom = Math.max(1, Math.min(28, this.scheduleForm.dayOfMonth || 1));
        const month = Math.max(1, Math.min(12, this.scheduleForm.month || 1));
        this.scheduleForm.cronExpression = `${minute} ${hour} ${dom} ${month} *`;
        return;
      }
    },

    async submitSchedule() {
      if (!this.scheduleForm.vendor_id) {
        PopupService.warning('Please select a vendor.', 'Schedule Screening');
        return;
      }
      const freq = this.scheduleForm.frequency;
      const oneTime = freq === 'does_not_repeat';
      if (oneTime && (!this.scheduleForm.oneTimeDate || !this.scheduleForm.oneTimeTime)) {
        PopupService.warning('Please set both date and time for a one-time schedule.', 'Schedule Screening');
        return;
      }
      if (!oneTime && !this.scheduleForm.time) {
        PopupService.warning('Please set a time for the recurring schedule.', 'Schedule Screening');
        return;
      }

      this.scheduleSubmitting = true;
      try {
        this.applyScheduleCron();

        const vendor = this.uniqueVendors.find(v => v.id == this.scheduleForm.vendor_id);
        if (!vendor || !vendor.vendor_code) {
          PopupService.warning('Selected vendor has no vendor code.', 'Schedule Screening');
          return;
        }

        // Build payload
        const payload = {
          frequency: freq,
          cron_expression: this.scheduleForm.cronExpression || null,
          start_date: this.scheduleForm.startDate || null,
          notes: '',
        };

        if (oneTime) {
          // Combine date + time into ISO string
          payload.scheduled_at = `${this.scheduleForm.oneTimeDate}T${this.scheduleForm.oneTimeTime}:00`;
          payload.cron_expression = null;
        }

        const url = getApiV1Url(
          `management/vendors/${encodeURIComponent(vendor.vendor_code)}/screening-schedules/`
        );
        const response = await apiClient.post(url, payload);

        if (response.data && response.data.success) {
          const schedule = response.data.schedule;
          PopupService.success(
            `Schedule saved for ${vendor.company_name}. ` +
            `Next run: ${this.formatScheduleNextRun(schedule.next_run_at)}.`,
            'Schedule Screening'
          );
          // Refresh list in modal
          this.schedules = [...this.schedules, schedule];
          // Reset form but keep modal open so user can see the new entry
          this.scheduleForm.oneTimeDate = '';
          this.scheduleForm.oneTimeTime = '09:00';
          this.scheduleForm.startDate = '';
          this.scheduleForm.cronExpression = '';
        } else {
          PopupService.warning(response.data?.error || 'Failed to save schedule.', 'Schedule Screening');
        }
      } catch (err) {
        console.error('Schedule screening error:', err);
        const msg = err.response?.data?.error || err.message || 'Failed to save schedule.';
        PopupService.error(msg, 'Schedule Screening');
      } finally {
        this.scheduleSubmitting = false;
      }
    },
    
    selectVendor(vendor) {
      this.selectedVendorId = vendor.id;
      this.selectedVendor = vendor;
      this.isDropdownOpen = false;
      this.searchQuery = '';
      this.onVendorChange();
    },
    
    handleClickOutside(event) {
      if (!event.target.closest('.custom-dropdown')) {
        this.isDropdownOpen = false;
      }
    },
    

    async onVendorChange() {
      if (!this.selectedVendorId) {
        this.selectedVendor = null;
        this.selectedScreening = null;
        this.vendorScreeningResults = [];
        this.matches = [];
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        console.log(`🔍 Fetching screening results for vendor ID: ${this.selectedVendorId}`);
        // Use getApiV1Url since backend is at /api/v1/vendor-core/ not /api/tprm/v1/vendor-core/
        const response = await apiClient.get(getApiV1Url(`vendor-core/screening-results/vendor_screening_results/?vendor_id=${this.selectedVendorId}`));
        
        console.log('📡 API Response:', response.data);
        
        if (response.data.status === 'success') {
          const results = response.data.data;
          console.log(`🎯 Found ${results.length} screening results:`, results);
          
          // Get vendor info from filtered vendors first, then fall back to all vendors
          const vendor = this.filteredVendors.find(v => v.id == this.selectedVendorId) || 
                        this.uniqueVendors.find(v => v.id == this.selectedVendorId);
          console.log('👤 Found vendor:', vendor);
          
          this.selectedVendor = vendor;
          this.vendorScreeningResults = results;
          this.selectedScreening = null; // Reset selected screening
          this.matches = [];
          
          console.log('✅ Selected vendor:', this.selectedVendor);
          console.log('📊 Vendor screening results:', this.vendorScreeningResults);
          
          // Show success message if screening results found
          if (results.length > 0) {
            console.log(`🎉 SUCCESS: ${results.length} screening results loaded for ${vendor?.company_name}`);
            
            // Log each screening result for debugging
            results.forEach(result => {
              console.log(`   📋 ${result.screening_type}: ${result.status} (${result.total_matches} matches)`);
            });
          } else {
            console.log(`⚠️ No screening results found for vendor ${vendor?.company_name} (ID: ${this.selectedVendorId})`);
            console.log('💡 This might be because:');
            console.log('   1. Vendor was just registered and screening is still in progress');
            console.log('   2. Screening failed during registration');
            console.log('   3. Vendor was created without triggering screening');
          }
        } else {
          console.error('❌ API returned error status:', response.data);
          this.error = 'Failed to fetch screening results for vendor';
        }
      } catch (error) {
        console.error('🚨 Error fetching vendor screening results:', error);
        console.error('🔍 Error details:', error.response?.data);
        this.error = `Network error: ${error.message}`;
        
        // Additional debugging info
        if (error.response?.status === 404) {
          console.log('💡 404 Error - This usually means the vendor has no screening results yet');
        } else if (error.response?.status === 500) {
          console.log('💡 500 Error - This indicates a server-side issue');
        }
      } finally {
        this.loading = false;
      }
    },

    getOverallStatus(results) {
      if (results.some(r => r.status === 'CONFIRMED_MATCH')) return 'confirmed_match';
      if (results.some(r => r.status === 'POTENTIAL_MATCH')) return 'potential_match';
      if (results.some(r => r.status === 'UNDER_REVIEW')) return 'under_review';
      return 'clear';
    },

    selectScreening(screening) {
      console.log('Selecting screening:', screening);
      this.selectedScreening = screening;
      this.activeTab = 'matches';
      
      // Set matches from the selected screening
      if (screening && screening.matches && Array.isArray(screening.matches)) {
        console.log('Processing matches:', screening.matches);
        this.matches = screening.matches.map(match => ({
          id: match.match_id,
          type: match.match_type,
          score: match.match_score,
          reviewStatus: this.mapResolutionStatus(match.resolution_status),
          title: this.getMatchTitle(match),
          reviewerNotes: match.resolution_notes || 'No notes available',
          details: this.getMatchDetails(match),
          rawMatch: match
        }));
        // Initialize local resolution notes with existing reviewer notes (if any)
        this.matches.forEach(m => {
          if (m.reviewerNotes && m.reviewerNotes !== 'No notes available') {
            this.resolutionNotes[m.id] = m.reviewerNotes;
          } else if (this.resolutionNotes[m.id] == null) {
            this.resolutionNotes[m.id] = '';
          }
        });
        console.log('Processed matches:', this.matches);
      } else {
        console.log('No matches found for this screening');
        this.matches = [];
      }
    },


    mapResolutionStatus(status) {
      const statusMap = {
        'PENDING': 'Under Review',
        'CLEARED': 'False Positive',
        'ESCALATED': 'Escalated',
        'BLOCKED': 'Confirmed Match'
      };
      return statusMap[status] || status;
    },

    getMatchTitle(match) {
      const details = match.match_details || {};
      return details.name || match.match_type || 'Unknown Match';
    },

    getMatchDetails(match) {
      const details = match.match_details || {};
      return details.remarks || details.programs?.join(', ') || 'No additional details available';
    },

    getStatusText(status) {
      const statusMap = {
        'CLEAR': 'Cleared',
        'UNDER_REVIEW': 'Under Review',
        'POTENTIAL_MATCH': 'Potential Match',
        'CONFIRMED_MATCH': 'Confirmed Match',
        'clear': 'Cleared',
        'under_review': 'Under Review',
        'potential_match': 'Potential Match',
        'confirmed_match': 'Confirmed Match'
      };
      return statusMap[status] || status;
    },

    getStatusClass(status) {
      if (!status) return '';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('clear')) return 'success';
      if (statusLower.includes('potential') || statusLower.includes('warning')) return 'warning';
      if (statusLower.includes('confirmed') || statusLower.includes('blocked')) return 'risk';
      return '';
    },
    
    getStatusIcon(status) {
      if (!status) return '❓';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('clear')) return '✅';
      if (statusLower.includes('under_review')) return '⏳';
      if (statusLower.includes('potential') || statusLower.includes('warning')) return '⚠️';
      if (statusLower.includes('confirmed') || statusLower.includes('blocked')) return '🚫';
      return '❓';
    },
    
    getStatusCardClass(status) {
      if (!status) return 'info';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('clear')) return 'success';
      if (statusLower.includes('under_review')) return 'warning';
      if (statusLower.includes('potential') || statusLower.includes('warning')) return 'warning';
      if (statusLower.includes('confirmed') || statusLower.includes('blocked')) return 'danger';
      return 'info';
    },
    
    formatDate(dateString) {
      if (!dateString) return 'Not available';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    getRiskLevel() {
      const highRisk = this.selectedScreening?.high_risk_matches || 0;
      const total = this.selectedScreening?.total_matches || 0;
      
      if (highRisk > 0) return 'HIGH';
      if (total > 0) return 'MEDIUM';
      return 'LOW';
    },
    
    getRiskLevelClass() {
      const level = this.getRiskLevel();
      switch (level) {
        case 'HIGH': return 'risk-high';
        case 'MEDIUM': return 'risk-medium';
        case 'LOW': return 'risk-low';
        default: return 'risk-low';
      }
    },

    getHighRiskCount() {
      return this.matches.filter(m => {
        const rawMatch = m.rawMatch;
        return rawMatch && rawMatch.match_details && rawMatch.match_details.risk_level === 'HIGH';
      }).length;
    },

    getUnderReviewCount() {
      return this.matches.filter(m => m.reviewStatus === 'Under Review').length;
    },

    getClearedCount() {
      return this.matches.filter(m => m.reviewStatus === 'False Positive').length;
    },

    async updateMatchStatus(matchId, status, notes = '') {
      if (!this.selectedScreening) return;
      
      try {
        const response = await apiClient.post(
          getApiV1Url(`vendor-core/screening-results/${this.selectedScreening.screening_id}/update_match_status/`),
          {
            match_id: matchId,
            status: status,
            notes: notes
          }
        );
        
        if (response.data.message) {
          // Refresh the data for the current vendor
          await this.onVendorChange();
          
          // Re-select the current screening to update the matches
          const updatedScreening = this.vendorScreeningResults.find(s => s.screening_id === this.selectedScreening.screening_id);
          if (updatedScreening) {
            this.selectScreening(updatedScreening);
          }
        }
      } catch (error) {
        console.error('Error updating match status:', error);
        this.error = 'Failed to update match status';
      }
    },

    setResolutionStatus(matchId, status) {
      this.selectedResolutionStatus[matchId] = status;
      this.pendingChanges[matchId] = true;
    },

    async submitResolution(matchId) {
      if (!this.selectedResolutionStatus[matchId]) {
        PopupService.warning('Please select a resolution status first', 'Missing Resolution Status');
        return;
      }

      const status = this.selectedResolutionStatus[matchId];
      const note = this.resolutionNotes[matchId] || '';
      
      try {
        await this.updateMatchStatus(matchId, status, note);
        
        // Clear pending changes
        this.pendingChanges[matchId] = false;
        this.selectedResolutionStatus[matchId] = null;
        this.resolutionNotes[matchId] = '';
        
        // Refresh the data
        await this.onVendorChange();
        
        // Re-select the current screening
        const updatedScreening = this.vendorScreeningResults.find(s => s.screening_id === this.selectedScreening.screening_id);
        if (updatedScreening) {
          this.selectScreening(updatedScreening);
        }
      } catch (error) {
        console.error('Error submitting resolution:', error);
        this.error = 'Failed to submit resolution';
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },

    async markAsCleared() {
      if (!this.selectedScreening) return;
      
      try {
        // Update the selected screening to CLEAR status
        const response = await apiClient.post(
          getApiV1Url(`vendor-core/screening-results/${this.selectedScreening.screening_id}/mark_as_cleared/`)
        );
        
        if (response.data.message) {
          // Refresh the data
          await this.onVendorChange();
          
          // Re-select the current screening
          const updatedScreening = this.vendorScreeningResults.find(s => s.screening_id === this.selectedScreening.screening_id);
          if (updatedScreening) {
            this.selectScreening(updatedScreening);
          }
        }
      } catch (error) {
        console.error('Error marking as cleared:', error);
        this.error = 'Failed to mark as cleared';
      }
    },

    async addNote() {
      PopupService.comment(
        'Add a note for this screening:',
        'Add Note',
        async (note) => {
          if (note && this.selectedScreening) {
            try {
              const response = await apiClient.post(
            getApiV1Url(`vendor-core/screening-results/${this.selectedScreening.screening_id}/add_note/`),
            { note: note }
          );
          
          if (response.data.message) {
            // Refresh the data
            await this.onVendorChange();
            
            // Re-select the current screening
            const updatedScreening = this.vendorScreeningResults.find(s => s.screening_id === this.selectedScreening.screening_id);
            if (updatedScreening) {
              this.selectScreening(updatedScreening);
            }
          }
        } catch (error) {
          console.error('Error adding note:', error);
          this.error = 'Failed to add note';
          PopupService.error('Failed to add note', 'Note Error');
        }
      }
        }
      );
    }
  },

  async mounted() {
    await loggingService.logPageView('Vendor', 'Vendor External Screening');
    console.log('Component mounted, fetching vendors...');
    await this.fetchVendors();
    console.log('Vendors loaded:', this.vendors.length);
    console.log('Unique vendors:', this.uniqueVendors.length);
    // Don't auto-fetch screening results, let user select vendor first
    
    // Add click outside listener to close dropdown
    document.addEventListener('click', this.handleClickOutside);
  },
  
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  },
}
</script>

<style scoped src="./VendorExternalScreening.css"></style>
