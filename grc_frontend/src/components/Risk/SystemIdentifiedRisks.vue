<template>
  <div class="system-risk-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="system-risk-header">
      <h2>System Identified Risks</h2>
      <p>AI-detected risks pending your review. Accept and complete details to add to the Risk Register.</p>
    </div>

    <div class="system-risk-stats">
      <div class="stat-card">
        <p class="stat-value">{{ pendingCount }}</p>
        <p class="stat-label">Pending Review</p>
      </div>
      <div class="stat-card">
        <p class="stat-value accepted">{{ acceptedCount }}</p>
        <p class="stat-label">Accepted Today</p>
      </div>
      <div class="stat-card">
        <p class="stat-value rejected">{{ rejectedCount }}</p>
        <p class="stat-label">Rejected</p>
      </div>
      <div class="stat-card">
        <p class="stat-value">{{ sourcesActive }}/6</p>
        <p class="stat-label">Sources Active</p>
      </div>
    </div>

    <div class="source-chips">
      <button
        v-for="source in sourceFilters"
        :key="source"
        type="button"
        class="chip"
      >
        {{ source }}
      </button>
    </div>

    <div class="risk-list">
      <article v-for="risk in risks" :key="risk.id" class="risk-card">
        <div class="risk-card-top">
          <span class="risk-tag">{{ risk.category }}</span>
          <span class="confidence">AI Confidence: {{ risk.confidence }}%</span>
        </div>
        <h3>{{ risk.title }}</h3>
        <p class="risk-desc">{{ risk.description }}</p>

        <div class="risk-meta">
          <span>Type: {{ risk.type }}</span>
          <span>Criticality: {{ risk.criticality }}</span>
          <span>Source: {{ risk.source }}</span>
          <span>Detected: {{ risk.detected }}</span>
        </div>

        <div class="risk-score-row">
          <span>Likelihood: {{ risk.likelihood }}/10</span>
          <span>Impact: {{ risk.impact }}/10</span>
          <span>Exposure: {{ risk.exposure }}</span>
        </div>

        <p class="mitigation">Mitigation: {{ risk.mitigation }}</p>

        <div class="risk-actions">
          <button type="button" class="btn primary" @click="openReview(risk)">Review &amp; Accept</button>
          <button type="button" class="btn ghost" @click="rejectFromList(risk.id)">Reject</button>
        </div>
      </article>
    </div>

    <div v-if="selectedRisk" class="modal-backdrop" @click.self="closeReview">
      <div class="review-modal">
        <div class="review-header">
          <h3>Review AI-Identified Risk</h3>
          <button type="button" class="close-btn" @click="closeReview">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="review-body">
          <section class="draft-side">
            <h4>AI Draft (Read-only)</h4>
            <p><strong>Risk Title:</strong> {{ selectedRisk.title }}</p>
            <p><strong>Risk Type:</strong> {{ selectedRisk.type }}</p>
            <p><strong>Category:</strong> {{ selectedRisk.category }}</p>
            <p><strong>Criticality:</strong> {{ selectedRisk.criticality }}</p>
            <p><strong>Risk Description:</strong> {{ selectedRisk.description }}</p>
            <p><strong>Possible Damage:</strong> {{ selectedRisk.possibleDamage }}</p>
            <p><strong>Business Impact:</strong> {{ selectedRisk.businessImpact.join(', ') }}</p>
            <p><strong>Likelihood:</strong> {{ selectedRisk.likelihood }}/10</p>
            <p><strong>Impact:</strong> {{ selectedRisk.impact }}/10</p>
            <p><strong>Exposure Rating:</strong> {{ selectedRisk.exposure }}</p>
            <p><strong>Priority:</strong> {{ selectedRisk.priority }}</p>
            <p><strong>Mitigation Steps:</strong></p>
            <ol>
              <li v-for="(step, index) in selectedRisk.mitigationSteps" :key="`${selectedRisk.id}-step-${index}`">
                {{ step }}
              </li>
            </ol>
          </section>

          <section class="edit-side">
            <h4>Your Review (Editable)</h4>

            <label>Risk Title</label>
            <input v-model="reviewForm.title" type="text" />

            <label>Risk Type</label>
            <select v-model="reviewForm.type">
              <option>Current</option>
              <option>Emerging</option>
            </select>

            <label>Category</label>
            <input v-model="reviewForm.category" type="text" />

            <label>Criticality</label>
            <select v-model="reviewForm.criticality">
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
              <option>Critical</option>
            </select>

            <label>Risk Description</label>
            <textarea v-model="reviewForm.description" rows="3"></textarea>

            <label>Possible Damage</label>
            <textarea v-model="reviewForm.possibleDamage" rows="2"></textarea>

            <label>Business Impact</label>
            <div class="impact-tags">
              <button
                v-for="impact in impactOptions"
                :key="impact"
                type="button"
                class="impact-tag"
                :class="{ active: reviewForm.businessImpact.includes(impact) }"
                @click="toggleImpact(impact)"
              >
                {{ impact }}
              </button>
            </div>

            <label>Likelihood: {{ reviewForm.likelihood }}/10</label>
            <input v-model.number="reviewForm.likelihood" type="range" min="1" max="10" />

            <label>Impact: {{ reviewForm.impact }}/10</label>
            <input v-model.number="reviewForm.impact" type="range" min="1" max="10" />

            <label>Exposure Rating (auto-calculated)</label>
            <input :value="reviewForm.likelihood * reviewForm.impact" type="number" readonly />

            <label>Priority</label>
            <select v-model="reviewForm.priority">
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
              <option>Critical</option>
            </select>
          </section>
        </div>

        <div class="review-footer">
          <button type="button" class="btn primary" @click="acceptRisk">Accept &amp; Send for Approval</button>
          <button type="button" class="btn ghost" @click="saveDraft">Save as Draft</button>
          <button type="button" class="btn danger" @click="rejectCurrent">Reject</button>
          <button type="button" class="btn ghost" @click="closeReview">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'SystemIdentifiedRisks',
  data() {
    return {
      isSidebarCollapsed: false,
      loading: false,
      sourceFilters: [
        'Audit Findings',
        'Incidents',
        'Compliance Controls',
        'TPRM / Vendor Data',
        'External Integrations',
        'Manual / Events'
      ],
      impactOptions: ['Revenue Loss', 'Reputation', 'Regulatory', 'Operational', 'Strategic'],
      stats: {
        pendingCount: 0,
        acceptedToday: 0,
        rejectedCount: 0,
        sourcesActive: 0
      },
      pagination: {
        page: 1,
        pageSize: 10,
        totalCount: 0,
        totalPages: 0
      },
      filters: {
        source: '',
        status: '',
        category: ''
      },
      selectedRisk: null,
      reviewForm: {
        title: '',
        type: 'Current',
        category: '',
        criticality: 'Medium',
        description: '',
        possibleDamage: '',
        businessImpact: [],
        likelihood: 5,
        impact: 5,
        priority: 'Medium'
      },
      risks: []
    };
  },
  computed: {
    pendingCount() {
      return this.stats.pendingCount || 0;
    },
    acceptedCount() {
      return this.stats.acceptedToday || 0;
    },
    rejectedCount() {
      return this.stats.rejectedCount || 0;
    },
    sourcesActive() {
      return this.stats.sourcesActive || 0;
    }
  },
  methods: {
    async loadStats() {
      try {
        const response = await axios.get(API_ENDPOINTS.SYSTEM_RISKS_STATS, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          this.stats = response.data.stats;
        }
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    },

    async loadRisks() {
      this.loading = true;
      try {
        const params = new URLSearchParams({
          page: this.pagination.page,
          page_size: this.pagination.pageSize,
          ...this.filters
        });
        
        const response = await axios.get(`${API_ENDPOINTS.SYSTEM_RISKS_LIST}?${params}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          // Transform API data to match component expectations
          this.risks = response.data.data.map(item => ({
            id: item.id,
            category: item.category || 'Unknown',
            confidence: item.confidence_score || 0,
            title: item.risk_title || '',
            description: item.risk_description || '',
            type: item.risk_type || 'Current',
            criticality: item.criticality || 'Medium',
            source: item.source_ref || '',
            detected: this.formatDate(item.created_at),
            likelihood: item.likelihood || 5,
            impact: item.impact || 5,
            exposure: item.exposure_rating || 0,
            priority: item.priority || 'Medium',
            businessImpact: item.business_impact || [],
            possibleDamage: item.possible_damage || '',
            mitigation: item.mitigation_steps && item.mitigation_steps.length > 0 
              ? item.mitigation_steps[0] 
              : 'No mitigation defined',
            mitigationSteps: item.mitigation_steps || [],
            status: item.status
          }));
          this.pagination = response.data.pagination;
        }
      } catch (error) {
        console.error('Error loading risks:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to load system identified risks.'
        });
      } finally {
        this.loading = false;
      }
    },

    async runIncidentScan() {
      this.loading = true;
      try {
        const response = await axios.post(API_ENDPOINTS.SYSTEM_RISKS_RUN_SCAN_INCIDENT, {
          limit: 50
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          this.$notify?.({
            type: 'success',
            title: 'Scan Complete',
            text: response.data.message
          });
          
          // Reload data
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error running scan:', error);
        this.$notify?.({
          type: 'error',
          title: 'Scan Failed',
          text: 'Failed to run incident risk scan.'
        });
      } finally {
        this.loading = false;
      }
    },

    async openReview(risk) {
      try {
        const response = await axios.get(API_ENDPOINTS.SYSTEM_RISKS_DETAIL(risk.id), {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          const data = response.data.data;
          this.selectedRisk = {
            ...risk,
            // Add additional details from API
            possibleDamage: data.possible_damage || risk.possibleDamage,
            businessImpact: data.business_impact || risk.businessImpact,
            mitigationSteps: data.mitigation_steps || risk.mitigationSteps,
            aiReasoning: data.ai_reasoning || ''
          };
          
          this.reviewForm = {
            title: data.risk_title || '',
            type: data.risk_type || 'Current',
            category: data.category || 'Operational',
            criticality: data.criticality || 'Medium',
            description: data.risk_description || '',
            possibleDamage: data.possible_damage || '',
            businessImpact: [...(data.business_impact || [])],
            likelihood: data.likelihood || 5,
            impact: data.impact || 5,
            priority: data.priority || 'Medium'
          };
        }
      } catch (error) {
        console.error('Error loading risk details:', error);
        // Fallback to basic risk data
        this.selectedRisk = risk;
        this.reviewForm = {
          title: risk.title,
          type: risk.type,
          category: risk.category,
          criticality: risk.criticality,
          description: risk.description,
          possibleDamage: risk.possibleDamage,
          businessImpact: [...risk.businessImpact],
          likelihood: risk.likelihood,
          impact: risk.impact,
          priority: risk.priority
        };
      }
    },

    async acceptRisk() {
      if (!this.selectedRisk) return;
      
      try {
        const response = await axios.post(API_ENDPOINTS.SYSTEM_RISKS_ACCEPT(this.selectedRisk.id), {}, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          this.$notify?.({
            type: 'success',
            title: 'Accepted',
            text: response.data.message
          });
          
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error accepting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to accept risk.'
        });
      }
    },

    async saveDraft() {
      if (!this.selectedRisk) return;
      
      try {
        const response = await axios.put(API_ENDPOINTS.SYSTEM_RISKS_REVIEW(this.selectedRisk.id), {
          risk_title: this.reviewForm.title,
          risk_type: this.reviewForm.type,
          category: this.reviewForm.category,
          criticality: this.reviewForm.criticality,
          risk_description: this.reviewForm.description,
          possible_damage: this.reviewForm.possibleDamage,
          business_impact: this.reviewForm.businessImpact,
          likelihood: this.reviewForm.likelihood,
          impact: this.reviewForm.impact,
          priority: this.reviewForm.priority
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          this.$notify?.({
            type: 'info',
            title: 'Draft Saved',
            text: response.data.message
          });
          this.closeReview();
          await this.loadRisks(); // Reload to show updated status
        }
      } catch (error) {
        console.error('Error saving draft:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to save draft.'
        });
      }
    },

    async rejectCurrent() {
      const reason = prompt('Please provide a reason for rejection:');
      if (!reason || !this.selectedRisk) return;
      
      try {
        const response = await axios.post(API_ENDPOINTS.SYSTEM_RISKS_REJECT(this.selectedRisk.id), {
          reason: reason
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          this.$notify?.({
            type: 'info',
            title: 'Rejected',
            text: response.data.message
          });
          
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error rejecting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to reject risk.'
        });
      }
    },

    async rejectFromList(id) {
      const reason = prompt('Please provide a reason for rejection:');
      if (!reason) return;
      
      try {
        const response = await axios.post(API_ENDPOINTS.SYSTEM_RISKS_REJECT(id), {
          reason: reason
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        if (response.data.status === 'success') {
          this.$notify?.({
            type: 'info',
            title: 'Rejected',
            text: 'Risk rejected successfully.'
          });
          
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error rejecting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to reject risk.'
        });
      }
    },

    checkSidebarState() {
      const sidebar = document.querySelector('.sidebar');
      this.isSidebarCollapsed = !!sidebar && sidebar.classList.contains('collapsed');
    },

    closeReview() {
      this.selectedRisk = null;
    },

    toggleImpact(impact) {
      if (this.reviewForm.businessImpact.includes(impact)) {
        this.reviewForm.businessImpact = this.reviewForm.businessImpact.filter((item) => item !== impact);
      } else {
        this.reviewForm.businessImpact.push(impact);
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'Unknown';
      
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffHours < 1) {
        return 'Just now';
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else if (diffDays < 7) {
        return `${diffDays}d ago`;
      } else {
        return date.toLocaleDateString();
      }
    }
  },
  async mounted() {
    this.checkSidebarState();
    document.addEventListener('click', this.checkSidebarState);
    
    // Load initial data
    await this.loadStats();
    await this.loadRisks();
  },
  beforeUnmount() {
    document.removeEventListener('click', this.checkSidebarState);
  }
};
</script>

<style src="./SystemIdentifiedRisks.css" scoped></style>
