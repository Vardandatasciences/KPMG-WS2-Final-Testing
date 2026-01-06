<template>
  <div class="external-screening-container">
    <!-- Screening Results Sidebar -->
    <div class="screening-results-panel">
      <div class="panel-header">
        <h2 class="panel-title">Screening Results</h2>
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
                <span class="match-type-badge" :class="match.type.toLowerCase()">
                  {{ match.type }}
                </span>
                <span class="match-score">Score: {{ match.score }}</span>
                <span 
                  class="match-status-badge"
                  :class="match.reviewStatus.toLowerCase().replace(' ', '-')"
                >
                  {{ match.reviewStatus }}
                </span>
              </div>
            </div>

            <div class="match-details">
              <h4 class="match-title">{{ match.title }}</h4>
              
              <!-- Resolution note input/display -->
              <div class="match-section">
                <h5 class="section-title">Resolution Note</h5>
                <textarea
                  v-if="match.reviewStatus === 'Under Review'"
                  class="resolution-note-input"
                  v-model="resolutionNotes[match.id]"
                  placeholder="Add resolution note..."
                  rows="2"
                ></textarea>
                <div 
                  v-else
                  class="resolution-note-display"
                >
                  {{ match.reviewerNotes || 'No resolution note provided' }}
                </div>
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
                  :disabled="loading || match.reviewStatus !== 'Under Review'"
                >
                  <i class="icon-check"></i>
                  {{ selectedResolutionStatus[match.id] === 'CLEARED' ? '✓ Dismiss Risk' : 'Dismiss Risk' }}
                </button>
                <button 
                  class="btn-action escalate"
                  :class="{ selected: selectedResolutionStatus[match.id] === 'ESCALATED' }"
                  @click="setResolutionStatus(match.id, 'ESCALATED')"
                  :disabled="loading || match.reviewStatus !== 'Under Review'"
                >
                  <i class="icon-alert"></i>
                  {{ selectedResolutionStatus[match.id] === 'ESCALATED' ? '⚠ Mark as Risk' : 'Mark as Risk' }}
                </button>
              </div>
              <button 
                class="btn-action submit"
                @click="submitResolution(match.id)"
                :disabled="loading || !pendingChanges[match.id]"
                v-if="match.reviewStatus === 'Under Review'"
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

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import apiClient from '@/config/axios.js';
import PopupModal from '@/popup/PopupModal.vue';
import { PopupService } from '@/popup/popupService';
import notificationService from '@/services/notificationService';
import loggingService from '@/services/loggingService';

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
      selectedResolutionStatus: {}
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
    }
  },
  methods: {
    async fetchVendors(searchQuery = '') {
      this.loading = true;
      this.error = null;
      try {
        let url = 'https://grc-tprm.vardaands.com/api/tprm/vendor-core/temp-vendors/';
        
        // Add search parameter if provided
        if (searchQuery.trim()) {
          url += `?search=${encodeURIComponent(searchQuery.trim())}`;
        }
        
        console.log('Fetching vendors from:', url);
        const response = await apiClient.get(url);
        
        console.log('Raw API response:', response.data);
        
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
          console.error('Unexpected API response format:', response.data);
          this.error = 'Unexpected response format from server';
          return;
        }
        
        // Filter out vendors without essential data
        this.vendors = vendorData.filter(vendor => 
          vendor && (vendor.company_name || vendor.legal_name || vendor.vendor_code)
        );
        
        console.log(`✅ Successfully loaded ${this.vendors.length} vendors`);
        console.log('Sample vendors:', this.vendors.slice(0, 3));
        
        if (this.vendors.length === 0) {
          console.warn('⚠️ No vendors found in database');
          if (!searchQuery) {
            this.error = 'No vendors found in the database. Please add some vendors first.';
          }
        }
        
      } catch (error) {
        console.error('❌ Error fetching vendors:', error);
        console.error('Error details:', error.response?.data);
        this.error = `Failed to load vendors: ${error.message}`;
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
        const response = await apiClient.get(`https://grc-tprm.vardaands.com/api/tprm/vendor-core/screening-results/vendor_screening_results/?vendor_id=${this.selectedVendorId}`);
        
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
          `https://grc-tprm.vardaands.com/api/tprm/vendor-core/screening-results/${this.selectedScreening.screening_id}/update_match_status/`,
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
          `https://grc-tprm.vardaands.com/api/tprm/vendor-core/screening-results/${this.selectedScreening.screening_id}/mark_as_cleared/`
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
            `https://grc-tprm.vardaands.com/api/tprm/vendor-core/screening-results/${this.selectedScreening.screening_id}/add_note/`,
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
