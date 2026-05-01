<template>
  <div class="system-risk-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="system-risk-header">
      <div class="system-risk-header-left">
        <h2>Event-Driven Risk Monitoring</h2>
        <p>Real-time AI risks identified from the Event Module, filtered by departmental risk thresholds.</p>
      </div>

      <div class="system-risk-header-actions">
        <button
          type="button"
          class="btn btn-refresh"
          @click="loadRisks"
          :disabled="loading"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          {{ loading ? 'Updating...' : 'Refresh List' }}
        </button>
      </div>
    </div>

    <!-- Threshold Info Banner -->
    <div class="threshold-info-banner">
      <div class="info-icon">
        <i class="fas fa-shield-alt"></i>
      </div>
      <div class="info-text">
        <strong>Event-Driven Thresholds:</strong> This view monitors real-time events. Risks are only displayed when the <strong>Residual Risk Score</strong> meets or exceeds the <strong>Departmental Threshold</strong>.
      </div>
    </div>

    <!-- Admin Threshold Management Section -->
    <div v-if="isAdmin" class="admin-threshold-section">
      <div class="admin-section-header">
        <div class="title-group">
          <h3><i class="fas fa-user-shield"></i> Admin: Department Threshold Management</h3>
          <p>Adjust the Residual Risk Score requirement for each department. Updates will notify department heads via email.</p>
        </div>
        <button class="btn-refresh-small" @click="loadDepartmentThresholds" :disabled="adminLoading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': adminLoading }"></i>
        </button>
      </div>

      <div v-if="updateSuccess" class="alert alert-success">
        <i class="fas fa-check-circle"></i> {{ updateSuccess }}
      </div>
      <div v-if="updateError" class="alert alert-danger">
        <i class="fas fa-exclamation-circle"></i> {{ updateError }}
      </div>

      <!-- Polished Admin Controls -->
      <div class="admin-controls-card">
        <div class="admin-layout-split">
          <!-- Left: Department Selection -->
          <div class="admin-side-panel">
            <div class="admin-input-group">
              <label class="admin-field-label">Target Department</label>
              <div class="admin-select-container">
                <i class="fas fa-building admin-icon-muted"></i>
                <select v-model="selectedAdminDeptId" class="admin-modern-select">
                  <option value="">-- Choose Department --</option>
                  <option v-for="dept in departmentThresholds" :key="dept.DepartmentId" :value="dept.DepartmentId">
                    {{ dept.DepartmentName }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Right: Threshold Adjustment (Only if selected) -->
          <div class="admin-main-panel" :class="{ 'is-placeholder': !selectedDeptData }">
            <div v-if="selectedDeptData" class="adjustment-workflow">
              <div class="slider-block">
                <div class="slider-meta">
                  <label class="admin-field-label">Min Residual Risk Score</label>
                  <span class="score-indicator">{{ selectedDeptData.threshold_limit }}</span>
                </div>
                <div class="slider-wrapper">
                  <input 
                    type="range" 
                    v-model="selectedDeptData.threshold_limit" 
                    min="0" 
                    max="100" 
                    step="1"
                    class="premium-slider"
                  >
                  <div class="slider-track-labels">
                    <span>Relaxed</span>
                    <span>Strict</span>
                  </div>
                </div>
              </div>

              <button 
                class="admin-action-btn" 
                @click="updateThreshold(selectedDeptData)"
                :disabled="updatingThresholdId === selectedDeptData.DepartmentId"
              >
                <i v-if="updatingThresholdId === selectedDeptData.DepartmentId" class="fas fa-circle-notch fa-spin"></i>
                <i v-else class="fas fa-cloud-upload-alt"></i>
                {{ updatingThresholdId === selectedDeptData.DepartmentId ? 'Saving' : 'Update' }}
              </button>
            </div>

            <div v-else class="empty-action-hint">
              <i class="fas fa-mouse-pointer"></i>
              <p>Select a department to begin adjustment</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <i class="fas fa-circle-notch fa-spin"></i>
      <p>Analyzing departmental thresholds...</p>
    </div>

    <div v-else-if="groupedRisks.length > 0" class="department-accordion">
      <div v-for="group in groupedRisks" :key="group.department" class="dept-group">
        <div 
          class="dept-header" 
          :class="{ 'is-expanded': expandedDepts.includes(group.department) }"
          @click="toggleDept(group.department)"
        >
          <div class="dept-info">
            <span class="dept-name"><i class="fas fa-building"></i> {{ group.department }}</span>
            <span class="dept-threshold-tag">Threshold: {{ group.threshold }}</span>
          </div>
          <div class="dept-stats">
            <span class="risk-count">{{ group.risks.length }} Risk{{ group.risks.length > 1 ? 's' : '' }} Identified</span>
            <i class="fas" :class="expandedDepts.includes(group.department) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
          </div>
        </div>

        <div v-show="expandedDepts.includes(group.department)" class="dept-content">
          <div class="risk-list">
            <article v-for="risk in group.risks" :key="risk.id" class="risk-card">
              <div class="risk-card-header">
                <div class="risk-type-group">
                  <span class="risk-category-tag" :class="risk.category.toLowerCase().replace(' ', '-')">{{ risk.category }}</span>
                  <span class="risk-type-label">{{ risk.type }}</span>
                </div>
                <div class="ai-confidence-indicator">
                  <div class="confidence-tag" :class="getConfidenceClass(risk.confidence)">
                    <i class="fas fa-chart-line"></i>
                    <span>{{ risk.confidence }} Residual Score</span>
                  </div>
                </div>
              </div>

              <h3 class="risk-title">{{ risk.title }}</h3>
              
              <div class="risk-metadata">
                <span class="meta-criticality" :class="risk.criticality.toLowerCase()">{{ risk.criticality }}</span>
                <span class="meta-divider">•</span>
                <span class="meta-item">Source: {{ risk.source }}</span>
              </div>

              <p class="risk-summary-text">{{ risk.description }}</p>

              <!-- Scores Grid -->
              <div class="risk-scores-grid">
                <div class="score-stat">
                  <span class="stat-label">Likelihood</span>
                  <span class="stat-value">{{ risk.likelihood }}</span>
                </div>
                <div class="score-stat">
                  <span class="stat-label">Impact</span>
                  <span class="stat-value">{{ risk.impact }}</span>
                </div>
                <div class="score-stat exposure">
                  <span class="stat-label">Exposure</span>
                  <span class="stat-value"><strong>{{ risk.exposure }}</strong></span>
                </div>
                <div class="score-stat threshold-check">
                  <span class="stat-label">Status</span>
                  <span class="stat-value status-exceeds"><i class="fas fa-check-circle"></i> Exceeds {{ group.threshold }}% Limit</span>
                </div>
              </div>

              <!-- AI Reasoning -->
              <div class="ai-reasoning-footer">
                <strong>Analysis Context:</strong> {{ risk.aiReasoning || 'Identified based on source correlations and historical risk patterns.' }}
              </div>
            </article>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-risk-state">
      <i class="fas fa-shield-virus"></i>
      <p>No risks currently exceed departmental thresholds.</p>
    </div>
  </div>
</template>

<script>
import apiService from '@/services/apiService';

export default {
  name: 'RiskThreshold',
  data() {
    return {
      loading: false,
      isSidebarCollapsed: false,
      risks: [],
      expandedDepts: [],
      // Admin Threshold Management
      isAdmin: false,
      adminLoading: false,
      departmentThresholds: [],
      selectedAdminDeptId: '',
      updatingThresholdId: null,
      updateSuccess: null,
      updateError: null
    };
  },
  computed: {
    groupedRisks() {
      const groups = {};
      this.risks.forEach(risk => {
        const dept = risk.functionalArea || 'General';
        if (!groups[dept]) {
          groups[dept] = {
            department: dept,
            threshold: risk.threshold,
            risks: []
          };
        }
        groups[dept].risks.push(risk);
      });
      return Object.values(groups).sort((a, b) => b.risks.length - a.risks.length);
    },
    selectedDeptData() {
      if (!this.selectedAdminDeptId) return null;
      return this.departmentThresholds.find(d => d.DepartmentId === this.selectedAdminDeptId);
    }
  },
  mounted() {
    this.checkAdminStatus();
    this.loadRisks();
    this.checkSidebarState();
    document.addEventListener('click', this.checkSidebarState);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.checkSidebarState);
  },
  methods: {
    checkSidebarState() {
      const sidebar = document.querySelector('.sidebar');
      this.isSidebarCollapsed = !!sidebar && sidebar.classList.contains('collapsed');
    },
    checkAdminStatus() {
      // Check both localStorage and sessionStorage for role and ID
      let role = localStorage.getItem('role') || localStorage.getItem('user_role') || sessionStorage.getItem('role');
      let userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id');
      let isAdminFlag = false;
      
      const checkStorageObject = (str) => {
        try {
          if (str) {
            const parsed = JSON.parse(str);
            // Handle different API response structures (wrapped in 'data', 'user', or direct)
            const user = parsed.data || parsed.user || parsed;
            
            role = role || user.role || user.Role || (user.rbac && user.rbac.role);
            userId = userId || user.UserId || user.user_id || user.id || user.userid;
            isAdminFlag = isAdminFlag || user.is_admin || user.IsAdmin || (user.rbac && user.rbac.is_admin);
            
            // Case-insensitive check for GRC Administrator
            if (String(user.role).toLowerCase() === 'grc administrator' || 
                String(user.user_role).toLowerCase() === 'grc administrator') {
              isAdminFlag = true;
            }
          }
        } catch (e) {
          // Ignore JSON parse errors
        }
      };

      // Scan all possible storage locations
      checkStorageObject(localStorage.getItem('user'));
      checkStorageObject(localStorage.getItem('current_user'));
      checkStorageObject(sessionStorage.getItem('user'));
      checkStorageObject(sessionStorage.getItem('current_user'));

      const normalizedRole = (role || '').trim().toLowerCase();
      const adminRoles = ['grc administrator', 'system_admin', 'admin', 'system admin', 'grc_administrator'];
      
      // Final decision logic
      this.isAdmin = isAdminFlag || 
                     adminRoles.includes(normalizedRole) || 
                     String(userId) === '2' || 
                     String(userId) === '1'; // User 1 is often superuser
      
      console.log('[RISK-THRESHOLD] Robust Admin Check:', { 
        isAdmin: this.isAdmin, 
        role: role, 
        userId: userId,
        isAdminFlag: isAdminFlag 
      });
      
      if (this.isAdmin) {
        this.loadDepartmentThresholds();
      }
    },
    async loadDepartmentThresholds() {
      this.adminLoading = true;
      try {
        const response = await apiService.get('/api/system-risks/thresholds/');
        // Backend returns { status: 'success', data: [...] }
        if (response && response.status === 'success' && response.data) {
          this.departmentThresholds = response.data;
        } else if (response && Array.isArray(response)) {
          // Fallback if direct array returned
          this.departmentThresholds = response;
        }
      } catch (error) {
        console.error('Error loading department thresholds:', error);
      } finally {
        this.adminLoading = false;
      }
    },
    async updateThreshold(dept) {
      this.updatingThresholdId = dept.DepartmentId;
      this.updateSuccess = null;
      this.updateError = null;
      
      try {
        const response = await apiService.put('/api/system-risks/thresholds/update/', {
          department_id: dept.DepartmentId,
          threshold_limit: dept.threshold_limit
        });
        
        if (response && response.status === 'success') {
          this.updateSuccess = `Threshold for ${dept.DepartmentName} updated successfully. Email sent to ${dept.DepartmentHeadName}.`;
          // Refresh risks list to reflect new thresholds
          this.loadRisks();
          setTimeout(() => { this.updateSuccess = null; }, 5000);
        } else {
          this.updateError = response.message || 'Failed to update threshold.';
        }
      } catch (error) {
        console.error('Error updating threshold:', error);
        this.updateError = 'An error occurred while updating the threshold.';
      } finally {
        this.updatingThresholdId = null;
      }
    },
    async loadRisks() {
      this.loading = true;
      try {
        const response = await apiService.get('/api/system-risks/threshold-exceeded/');
        if (response && response.data) {
          this.risks = response.data.map(item => ({
            id: item.id,
            title: item.risk_title,
            description: item.risk_description || item.risk_title,
            category: item.category || 'Unknown',
            type: item.risk_type || 'Current',
            criticality: item.criticality || 'Medium',
            confidence: item.residual_score, // Now mapped to residual_score
            threshold: item.threshold_limit,
            functionalArea: item.functional_area || 'General',
            source: item.source_title || item.source_ref,
            likelihood: item.likelihood || 5,
            impact: item.impact || 5,
            exposure: item.exposure_rating || 0,
            aiReasoning: item.ai_reasoning || ''
          }));
          
          // Expand the first department by default if not already expanded
          if (this.groupedRisks.length > 0 && this.expandedDepts.length === 0) {
            this.expandedDepts = [this.groupedRisks[0].department];
          }
        }
      } catch (error) {
        console.error('Error loading threshold risks:', error);
      } finally {
        this.loading = false;
      }
    },
    toggleDept(dept) {
      const idx = this.expandedDepts.indexOf(dept);
      if (idx > -1) {
        this.expandedDepts.splice(idx, 1);
      } else {
        this.expandedDepts.push(dept);
      }
    },
    getConfidenceClass(score) {
      if (score >= 80) return 'high-confidence';
      if (score >= 60) return 'medium-confidence';
      return 'low-confidence';
    }
  }
};
</script>

<style scoped>
.system-risk-container {
  padding: 24px;
  background: #f8fafc;
  min-height: calc(100vh - 80px);
  margin-left: 236px;
  transition: all 0.3s ease;
  width: auto;
}

.system-risk-container.sidebar-collapsed {
  margin-left: 40px;
}

.system-risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.system-risk-header h2 {
  font-size: 26px;
  color: #1e293b;
  margin: 0;
  font-weight: 800;
}

.system-risk-header p {
  color: #64748b;
  margin: 4px 0 0 0;
  font-size: 15px;
}

.threshold-info-banner {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 4px solid #0ea5e9;
  padding: 16px 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  color: #0369a1;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.department-accordion {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dept-group {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.dept-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: #ffffff;
  transition: all 0.2s;
  user-select: none;
}

.dept-header:hover {
  background: #f8fafc;
}

.dept-header.is-expanded {
  border-bottom: 1px solid #f1f5f9;
  background: #f1f5f9;
}

.dept-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dept-name {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dept-name i {
  color: #6366f1;
}

.dept-threshold-tag {
  background: #4f46e5;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.dept-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  color: #64748b;
  font-weight: 600;
  font-size: 14px;
}

.dept-content {
  padding: 24px;
  background: #fcfcfd;
}

.risk-list {
  display: grid;
  gap: 24px;
}

.risk-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  position: relative;
}

.risk-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.risk-category-tag {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.risk-category-tag.it-security { background: #fee2e2; color: #991b1b; }
.risk-category-tag.operational { background: #fef3c7; color: #92400e; }
.risk-category-tag.compliance { background: #dcfce7; color: #166534; }

.confidence-tag {
  padding: 6px 14px;
  border-radius: 30px;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence-tag.high-confidence { background: #ecfdf5; color: #059669; border: 1px solid #10b981; }
.confidence-tag.medium-confidence { background: #fffbeb; color: #d97706; border: 1px solid #fbbf24; }
.confidence-tag.low-confidence { background: #fef2f2; color: #dc2626; border: 1px solid #f87171; }

.risk-title {
  font-size: 20px;
  color: #1e293b;
  margin: 0 0 12px 0;
  font-weight: 700;
}

.risk-metadata {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 14px;
  color: #64748b;
  margin-bottom: 16px;
}

.meta-criticality {
  font-weight: 800;
  text-transform: uppercase;
  font-size: 12px;
}

.meta-criticality.critical { color: #dc2626; }
.meta-criticality.high { color: #ea580c; }
.meta-criticality.medium { color: #d97706; }

.risk-summary-text {
  font-size: 15px;
  line-height: 1.6;
  color: #475569;
  margin-bottom: 20px;
}

.risk-scores-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 20px;
}

.score-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: #94a3b8;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 16px;
  color: #1e293b;
  font-weight: 700;
}

.status-exceeds {
  color: #059669;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.ai-reasoning-footer {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  padding: 12px 16px;
  background: #f1f5f9;
  border-radius: 8px;
  border-left: 3px solid #6366f1;
}

.loading-state {
  text-align: center;
  padding: 80px;
  color: #64748b;
}

.loading-state i {
  font-size: 40px;
  margin-bottom: 16px;
  color: #6366f1;
}

.empty-risk-state {
  text-align: center;
  padding: 100px;
  background: white;
  border-radius: 16px;
  border: 1px dashed #cbd5e1;
}

.empty-risk-state i {
  font-size: 64px;
  color: #cbd5e1;
  margin-bottom: 20px;
}

.empty-risk-state p {
  font-size: 18px;
  color: #64748b;
}

.btn-refresh {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

/* Admin Threshold Section Styles */
.admin-threshold-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
}

.admin-section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.title-group h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-group h3 i {
  color: #6366f1;
}

.title-group p {
  margin: 4px 0 0 0;
  color: #64748b;
  font-size: 14px;
}

.btn-refresh-small {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh-small:hover {
  background: #e2e8f0;
  color: #1e293b;
}

/* Premium Admin Management UI */
.admin-controls-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.admin-layout-split {
  display: flex;
  min-height: 100px;
}

.admin-side-panel {
  padding: 24px;
  background: #fcfcfd;
  border-right: 1px solid #f1f5f9;
  width: 320px;
  display: flex;
  align-items: center;
}

.admin-main-panel {
  flex: 1;
  padding: 24px 32px;
  display: flex;
  align-items: center;
  position: relative;
  background: white;
}

.admin-main-panel.is-placeholder {
  background: #fafafa;
  justify-content: center;
}

.admin-input-group {
  width: 100%;
}

.admin-field-label {
  display: block;
  font-size: 11px;
  font-weight: 800;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.admin-select-container {
  position: relative;
}

.admin-icon-muted {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #cbd5e1;
}

.admin-modern-select {
  width: 100%;
  padding: 12px 16px 12px 42px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  appearance: none;
}

.admin-modern-select:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.08);
}

.adjustment-workflow {
  display: flex;
  width: 100%;
  gap: 32px;
  align-items: flex-end;
}

.slider-block {
  flex: 1;
}

.slider-meta {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

.score-indicator {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 30px;
  font-weight: 800;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
}

.slider-wrapper {
  padding: 4px 0;
}

.premium-slider {
  width: 100%;
  height: 10px;
  background: #cbd5e1;
  border-radius: 5px;
  outline: none;
  -webkit-appearance: none;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
  margin: 10px 0;
}

.premium-slider::-webkit-slider-runnable-track {
  width: 100%;
  height: 10px;
  cursor: pointer;
  border-radius: 5px;
}

.premium-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  background: white;
  border: 4px solid #6366f1;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  margin-top: -7px; /* Centers the thumb on the track */
  transition: all 0.2s;
}

.premium-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 10px -1px rgba(99, 102, 241, 0.2);
}

.slider-track-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 10px;
  font-weight: 700;
  color: #cbd5e1;
  text-transform: uppercase;
}

.admin-action-btn {
  height: 48px;
  padding: 0 28px;
  background: #1e293b;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.2s;
}

.admin-action-btn:hover:not(:disabled) {
  background: #334155;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(30, 41, 59, 0.15);
}

.admin-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.empty-action-hint {
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-action-hint i {
  font-size: 20px;
  opacity: 0.5;
}

.empty-action-hint p {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.alert {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-success {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.alert-danger {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
</style>
