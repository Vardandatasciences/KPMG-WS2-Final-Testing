<template>
  <div class="risk-view-container">
    <PopupModal />
    
    <div class="risk-view-header">
      <button
        class="back-icon-btn"
        @click="goBack"
        aria-label="Back to Audit Findings"
      >
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="risk-view-title">Audit Finding Details</h2>
    </div>

    <div
      v-if="showDetailSkeleton"
      class="grc-skeleton-dashboard audit-finding-detail-skeleton"
      aria-busy="true"
      aria-label="Loading audit finding details"
    >
      <div class="grc-skeleton-kpi-row" style="max-width: 640px;">
        <div v-for="n in 3" :key="'afd-'+n" class="grc-skeleton-kpi-card grc-skeleton-pulse" />
      </div>
      <div class="grc-skeleton-table-wrap" style="margin-top: 16px; max-width: 800px;">
        <div v-for="n in 6" :key="'afd-r-'+n" class="grc-skeleton-row grc-skeleton-pulse" />
      </div>
    </div>

    <div v-else-if="error" class="risk-view-no-data">
      {{ error }}
    </div>

    <div class="risk-view-details-card" v-else-if="auditFinding && !showDetailSkeleton">
      <div class="risk-view-details-top">
        <div class="risk-view-id-section">
          <span class="risk-view-id-label">Audit Finding ID:</span>
          <span class="risk-view-id-value">{{ auditFinding.IncidentId }}</span>
        </div>
        <div class="risk-view-meta">
          <div class="risk-view-category">{{ auditFinding.RiskCategory || 'N/A' }}</div>
          <div class="risk-view-criticality" :class="getCriticalityClass(auditFinding.Criticality)">{{ auditFinding.Criticality || 'N/A' }}</div>
        </div>
      </div>

      <div class="risk-view-title-section">
        <h3>{{ auditFinding.IncidentTitle }}</h3>
        <div class="risk-view-compliance-section">
          <span class="risk-view-compliance-label">Compliance ID:</span>
          <span class="risk-view-compliance-value">{{ auditFinding.ComplianceId || 'N/A' }}</span>
        </div>
      </div>

      <div class="risk-view-content">
        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Description:</h4>
            <div class="risk-view-section-content">{{ auditFinding.Description || 'N/A' }}</div>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Business Impact:</h4>
            <div class="risk-view-section-content">{{ auditFinding.InitialImpactAssessment || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Possible Damage:</h4>
            <div class="risk-view-section-content">{{ auditFinding.PossibleDamage || 'N/A' }}</div>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Status:</h4>
            <div class="risk-view-section-content">{{ auditFinding.Status || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Systems/Assets Involved:</h4>
            <div class="risk-view-section-content">{{ auditFinding.SystemsAssetsInvolved || 'N/A' }}</div>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Geographic Location:</h4>
            <div class="risk-view-section-content">{{ auditFinding.GeographicLocation || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Mitigation Plan:</h4>
            <div class="risk-view-section-content">{{ auditFinding.Mitigation || 'N/A' }}</div>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Comments:</h4>
            <div class="risk-view-section-content">{{ auditFinding.Comments || 'N/A' }}</div>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Created At:</h4>
            <div class="risk-view-section-content">{{ formatDate(auditFinding.Date) }}</div>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Time:</h4>
            <div class="risk-view-section-content">{{ auditFinding.Time || 'N/A' }}</div>
          </div>
        </div>

        <!-- Assignment Information (shown only if assigned) -->
        <div v-if="auditFinding.AssignerId || auditFinding.ReviewerId" class="risk-view-content-row assignment-info-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Assigner:</h4>
            <div class="risk-view-section-content">{{ auditFinding.assigner_name || 'N/A' }}</div>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Reviewer:</h4>
            <div class="risk-view-section-content">{{ auditFinding.reviewer_name || 'N/A' }}</div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      
    </div>
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import apiService from '@/services/apiService.js'
import { API_ENDPOINTS } from '../../config/api.js'
import { useIncidentStore } from '@/stores/incident'
import '../Risk/ViewRisk.css';
import { PopupService, PopupModal } from '@/modules/popup';

export default {
  name: 'AuditFindingDetails',
  components: {
    PopupModal
  },
  data() {
    return {
      auditFinding: null,
      loading: true,
      error: null,
    }
  },
  computed: {
    ...mapStores(useIncidentStore),
    showDetailSkeleton() {
      return this.loading && !this.auditFinding
    },
  },
  async created() {
    await this.fetchAuditFindingDetails();
  },
  methods: {
    async fetchAuditFindingDetails() {
      const incidentId = this.$route.params.id
      this.error = null
      this.incidentStore.hydrateAuditFindingsFromService()
      const warm = this.incidentStore.findAuditFindingInCaches(incidentId)
      if (warm) {
        this.auditFinding = { ...warm }
        this.loading = false
        this.incidentStore
          .fetchAuditFindingDetail(incidentId, { force: true, background: true })
          .then(({ data }) => {
            if (data) this.auditFinding = data
          })
          .catch(() => {})
        return
      }
      try {
        this.loading = true
        const { data } = await this.incidentStore.fetchAuditFindingDetail(incidentId, {
          force: false,
          background: false,
        })
        this.auditFinding = data
      } catch (error) {
        console.error('Failed to fetch audit finding details:', error)
        this.error = 'Failed to load audit finding details. Please try again.'
      } finally {
        this.loading = false
      }
    },
    getCriticalityClass(criticality) {
      if (!criticality) return '';
      criticality = criticality.toLowerCase();
      if (criticality === 'critical') return 'risk-view-priority-critical';
      if (criticality === 'high') return 'risk-view-priority-high';
      if (criticality === 'medium') return 'risk-view-priority-medium';
      if (criticality === 'low') return 'risk-view-priority-low';
      return '';
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const [year, month, day] = dateString.split('-');
      return `${month}/${day}/${year}`;
    },
    goBack() {
      this.$router.push('/incident/audit-findings');
    },
    openSolveModal() {
      PopupService.confirm(
        'This audit finding will be forwarded to the Risk module. Do you want to proceed?',
        'Forward to Risk',
        () => this.confirmSolve(),
        () => {}
      );
    },
    openRejectModal() {
      PopupService.confirm(
        'Are you sure you want to close this audit finding?',
        'Close Audit Finding',
        () => this.confirmReject(),
        () => {}
      );
    },
    async sendPushNotification(notificationData) {
      try {
        await apiService.post(API_ENDPOINTS.PUSH_NOTIFICATION, notificationData);
        console.log('Push notification sent successfully');
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    confirmSolve() {
      apiService.put(API_ENDPOINTS.INCIDENT_STATUS(this.auditFinding.IncidentId), {
        status: 'Scheduled'
      })
      .then((body) => {
        console.log('Incident escalated to risk - API response:', body);
        
        // Check if the response indicates success
        if (body.success) {
          this.auditFinding.Status = 'Scheduled';
          PopupService.success(`Incident ${this.auditFinding.IncidentId} escalated to Risk successfully!`);
          // Send push notification for successful escalation
          this.sendPushNotification({
            title: 'Audit Finding Escalated to Risk',
            message: `Audit finding "${this.auditFinding.IncidentTitle || 'Untitled Finding'}" (ID: ${this.auditFinding.IncidentId}) has been successfully escalated to the Risk module.`,
            category: 'audit_finding',
            priority: 'high'
          });
          setTimeout(() => {
            this.$router.push('/incident/incident');
          }, 2000);
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', body);
          PopupService.error(body.message || 'Failed to escalate audit finding. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error updating audit finding status:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        PopupService.error('Failed to escalate audit finding. Please try again.');
        this.sendPushNotification({
          title: 'Audit Finding Escalation Failed',
          message: `Failed to escalate audit finding "${this.auditFinding.IncidentTitle || 'Untitled Finding'}" (ID: ${this.auditFinding.IncidentId}) to Risk module.`,
          category: 'audit_finding',
          priority: 'high'
        });
      });
    },
    confirmReject() {
      apiService.put(API_ENDPOINTS.INCIDENT_STATUS(this.auditFinding.IncidentId), {
        status: 'Rejected'
      })
      .then((body) => {
        console.log('Incident rejected - API response:', body);
        
        // Check if the response indicates success
        if (body.success) {
          this.auditFinding.Status = 'Rejected';
          PopupService.success(`Incident ${this.auditFinding.IncidentId} rejected successfully!`);
          this.sendPushNotification({
            title: 'Audit Finding Rejected',
            message: `Audit finding "${this.auditFinding.IncidentTitle || 'Untitled Finding'}" (ID: ${this.auditFinding.IncidentId}) has been rejected successfully.`,
            category: 'audit_finding',
            priority: 'medium'
          });
          setTimeout(() => {
            this.$router.push('/incident/incident');
          }, 2000);
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', body);
          PopupService.error(body.message || 'Failed to reject audit finding. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error updating audit finding status:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        PopupService.error('Failed to reject audit finding. Please try again.');
        this.sendPushNotification({
          title: 'Audit Finding Rejection Failed',
          message: `Failed to reject audit finding "${this.auditFinding.IncidentTitle || 'Untitled Finding'}" (ID: ${this.auditFinding.IncidentId}).`,
          category: 'audit_finding',
          priority: 'high'
        });
      });
    }
  }
}
</script>

<style scoped>
.risk-view-container {
  background-color: white;
  min-height: 100vh;
  margin-left: 280px;
  margin-top: 20px;
  margin-right: -50px;
  margin-bottom: -20px;
  width: calc(100% - 280px);
  padding: 20px;
}

.risk-view-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.risk-view-header .back-icon-btn {
  text-decoration: none;
}

.risk-view-header .back-icon-btn:hover {
  text-decoration: none;
}

.risk-view-title {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 600;
}
.risk-view-details-card {
  font-size: 0.85rem;
}

.risk-view-details-card h3 {
  font-size: 1.1rem;
}

.risk-view-details-card h4 {
  font-size: 0.9rem;
}

.risk-view-details-card span {
  font-size: 0.85rem;
}

.risk-view-details-card div {
  font-size: 0.85rem;
}

.risk-view-actions {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--risk-gray-200);
}

.risk-view-action-button {
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.risk-view-escalate {
  background-color: var(--risk-primary);
  color: white;
}

.risk-view-escalate:hover {
  background-color: var(--risk-primary-dark);
}

.risk-view-reject {
  background-color: var(--risk-danger);
  color: white;
}

.risk-view-reject:hover {
  background-color: #d32f2f;
}

/* Assignment information styling */
.assignment-info-row {
  background-color: rgba(52, 152, 219, 0.05);
  border-left: 4px solid #3498db;
  padding-left: 16px;
  margin-left: -16px;
  border-radius: 4px;
  margin-top: 8px;
  margin-bottom: 8px;
}
</style> 