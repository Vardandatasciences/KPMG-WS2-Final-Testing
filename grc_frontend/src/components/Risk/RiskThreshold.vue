<template>
  <div class="system-risk-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="system-risk-header">
      <div class="system-risk-header-left">
        <h2>Event-Driven Risk Monitoring</h2>
        <p>Real-time AI risks identified from the Event Module, filtered by departmental confidence thresholds.</p>
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
        <strong>Event-Driven Thresholds:</strong> This view monitors real-time events. Risks are only displayed when the <strong>AI Confidence Score</strong> meets or exceeds the <strong>Departmental Threshold</strong>.
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
            <span class="dept-threshold-tag">Threshold: {{ group.threshold }}%</span>
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
                    <i class="fas fa-robot"></i>
                    <span>{{ risk.confidence }}% AI Confidence</span>
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
                <strong>AI Rationale:</strong> {{ risk.aiReasoning || 'Identified based on source correlations and historical risk patterns.' }}
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
      expandedDepts: []
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
    }
  },
  mounted() {
    this.loadRisks();
    this.checkSidebarState();
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
            confidence: item.confidence_score,
            threshold: item.threshold_limit,
            functionalArea: item.functional_area || 'General',
            source: item.source_title || item.source_ref,
            likelihood: item.likelihood || 5,
            impact: item.impact || 5,
            exposure: item.exposure_rating || 0,
            aiReasoning: item.ai_reasoning || ''
          }));
          
          // Expand the first department by default
          if (this.groupedRisks.length > 0) {
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
</style>
