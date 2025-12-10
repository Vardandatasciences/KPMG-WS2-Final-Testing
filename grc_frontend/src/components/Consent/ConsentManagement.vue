<template>
  <div class="consent-management">
    <div class="header">
      <h1><i class="fas fa-shield-alt"></i> My Consents</h1>
      <p>View and manage your consent preferences. You can withdraw your consent at any time.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="loading-content">
        <div class="spinner-large"></div>
        <p>Loading your consents...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i> {{ error }}
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="success-message">
      <i class="fas fa-check-circle"></i> {{ successMessage }}
    </div>

    <!-- Consent Status Section -->
    <div v-if="!loading && !error" class="consent-status-section">
      <div class="section-header">
        <h2>Active Consents</h2>
        <button 
          v-if="activeConsents.length > 0" 
          @click="showWithdrawAllModal = true" 
          class="btn-withdraw-all"
        >
          <i class="fas fa-ban"></i> Withdraw All Consents
        </button>
      </div>

      <!-- Active Consents List -->
      <div v-if="activeConsents.length > 0" class="consents-list">
        <div 
          v-for="consent in activeConsents" 
          :key="`${consent.action_type}-${consent.framework}`"
          class="consent-card active"
        >
          <div class="consent-card-header">
            <div class="consent-info">
              <i class="fas fa-check-circle consent-icon"></i>
              <div>
                <h3>{{ getActionLabel(consent.action_type) }}</h3>
                <p class="consent-meta">
                  <span class="meta-item">
                    <i class="fas fa-layer-group"></i>
                    {{ getFrameworkName(consent.framework) }}
                  </span>
                  <span v-if="consent.last_accepted" class="meta-item">
                    <i class="fas fa-calendar-check"></i>
                    {{ formatDate(consent.last_accepted.accepted_at) }}
                  </span>
                </p>
              </div>
            </div>
            <button 
              @click="showWithdrawModal(consent)" 
              class="btn-withdraw"
            >
              <i class="fas fa-times"></i> Withdraw
            </button>
          </div>
        </div>
      </div>

      <!-- No Active Consents -->
      <div v-else class="no-consents">
        <i class="fas fa-info-circle"></i>
        <p>You don't have any active consents at the moment.</p>
      </div>
    </div>

    <!-- Withdrawal History Section -->
    <div v-if="!loading && !error && withdrawals.length > 0" class="withdrawal-history-section">
      <div class="section-header">
        <h2>Withdrawal History</h2>
      </div>
      <div class="withdrawals-list">
        <div 
          v-for="withdrawal in withdrawals" 
          :key="withdrawal.withdrawal_id"
          class="consent-card withdrawn"
        >
          <div class="consent-card-header">
            <div class="consent-info">
              <i class="fas fa-ban consent-icon"></i>
              <div>
                <h3>{{ getActionLabel(withdrawal.action_type) }}</h3>
                <p class="consent-meta">
                  <span class="meta-item">
                    <i class="fas fa-layer-group"></i>
                    {{ getFrameworkName(withdrawal.framework) }}
                  </span>
                  <span class="meta-item">
                    <i class="fas fa-calendar-times"></i>
                    {{ formatDate(withdrawal.withdrawn_at) }}
                  </span>
                  <span v-if="withdrawal.reason" class="meta-item">
                    <i class="fas fa-comment-alt"></i>
                    {{ withdrawal.reason }}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Withdraw Single Consent Modal -->
    <div v-if="showWithdrawSingleModal" class="modal-overlay" @click.self="closeWithdrawModal">
      <div class="modal-container withdraw-modal">
        <div class="modal-header">
          <div class="modal-title-section">
            <div class="modal-icon-wrapper">
              <i class="fas fa-shield-alt modal-title-icon"></i>
            </div>
            <h2>Withdraw Consent</h2>
          </div>
          <button @click="closeWithdrawModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="warning-box">
            <div class="warning-icon-wrapper">
              <i class="fas fa-exclamation-triangle warning-icon"></i>
            </div>
            <div class="warning-content">
              <h3 class="warning-title">Confirm Withdrawal</h3>
              <p class="warning-message">
                Are you sure you want to withdraw your consent for
                <span class="action-name">{{ selectedConsent ? getActionLabel(selectedConsent.action_type) : '' }}</span>?
              </p>
            </div>
          </div>
          
          <div class="info-box">
            <i class="fas fa-info-circle info-icon"></i>
            <p class="info-text">
              Once withdrawn, you will need to provide consent again before performing this action. 
              Your withdrawal will be recorded for compliance purposes.
            </p>
          </div>
          
          <div class="form-group">
            <label for="withdraw-reason" class="form-label">
              <i class="fas fa-comment-alt label-icon"></i>
              Reason for Withdrawal <span class="optional-badge">(Optional)</span>
            </label>
            <textarea 
              id="withdraw-reason"
              v-model="withdrawReason" 
              placeholder="Please provide a reason for withdrawing consent (e.g., privacy concerns, no longer needed, etc.)..."
              rows="4"
              class="form-textarea"
            ></textarea>
            <div class="char-count" v-if="withdrawReason">
              {{ withdrawReason.length }} characters
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeWithdrawModal" class="btn-cancel">
            <i class="fas fa-times"></i>
            Cancel
          </button>
          <button @click="confirmWithdraw" class="btn-confirm" :disabled="withdrawing">
            <i v-if="withdrawing" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-ban"></i>
            {{ withdrawing ? 'Withdrawing...' : 'Withdraw Consent' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Withdraw All Consents Modal -->
    <div v-if="showWithdrawAllModal" class="modal-overlay" @click.self="showWithdrawAllModal = false">
      <div class="modal-container withdraw-modal">
        <div class="modal-header">
          <div class="modal-title-section">
            <div class="modal-icon-wrapper">
              <i class="fas fa-shield-alt modal-title-icon"></i>
            </div>
            <h2>Withdraw All Consents</h2>
          </div>
          <button @click="showWithdrawAllModal = false" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="warning-box critical">
            <div class="warning-icon-wrapper">
              <i class="fas fa-exclamation-triangle warning-icon"></i>
            </div>
            <div class="warning-content">
              <h3 class="warning-title">Confirm Withdrawal of All Consents</h3>
              <p class="warning-message">
                Are you sure you want to withdraw <strong>all {{ activeConsents.length }}</strong> of your active consents?
              </p>
            </div>
          </div>
          
          <div class="info-box">
            <i class="fas fa-info-circle info-icon"></i>
            <p class="info-text">
              This action will withdraw all {{ activeConsents.length }} active consent(s). 
              You will need to provide consent again before performing any actions that require it. 
              All withdrawals will be recorded for compliance purposes.
            </p>
          </div>
          
          <div class="form-group">
            <label for="withdraw-all-reason" class="form-label">
              <i class="fas fa-comment-alt label-icon"></i>
              Reason for Withdrawal <span class="optional-badge">(Optional)</span>
            </label>
            <textarea 
              id="withdraw-all-reason"
              v-model="withdrawAllReason" 
              placeholder="Please provide a reason for withdrawing all consents (e.g., privacy concerns, account closure, etc.)..."
              rows="4"
              class="form-textarea"
            ></textarea>
            <div class="char-count" v-if="withdrawAllReason">
              {{ withdrawAllReason.length }} characters
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showWithdrawAllModal = false" class="btn-cancel">
            <i class="fas fa-times"></i>
            Cancel
          </button>
          <button @click="confirmWithdrawAll" class="btn-confirm" :disabled="withdrawing">
            <i v-if="withdrawing" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-ban"></i>
            {{ withdrawing ? 'Withdrawing...' : 'Withdraw All Consents' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  checkConsentStatus, 
  withdrawConsent, 
  withdrawAllConsents, 
  getUserConsentWithdrawals,
  getActionLabel 
} from '@/utils/consentManager.js';
import api from '@/services/api.js';

export default {
  name: 'ConsentManagement',
  data() {
    return {
      loading: false,
      error: null,
      successMessage: null,
      consentStatus: [],
      withdrawals: [],
      frameworks: {},
      showWithdrawSingleModal: false,
      showWithdrawAllModal: false,
      selectedConsent: null,
      withdrawReason: '',
      withdrawAllReason: '',
      withdrawing: false
    };
  },
  computed: {
    activeConsents() {
      return this.consentStatus.filter(c => c.has_active_consent);
    },
    userId() {
      return localStorage.getItem('user_id');
    },
    frameworkId() {
      return localStorage.getItem('framework_id') || '1';
    }
  },
  mounted() {
    this.loadConsentData();
    this.loadFrameworks();
  },
  methods: {
    async loadConsentData() {
      this.loading = true;
      this.error = null;
      
      try {
        // Load consent status
        const statusResponse = await checkConsentStatus(
          this.userId, 
          this.frameworkId
        );
        
        if (statusResponse.status === 'success') {
          this.consentStatus = Array.isArray(statusResponse.data) 
            ? statusResponse.data 
            : [statusResponse];
        }
        
        // Load withdrawal history
        const withdrawalsResponse = await getUserConsentWithdrawals(
          this.userId,
          this.frameworkId
        );
        
        if (withdrawalsResponse.status === 'success') {
          this.withdrawals = withdrawalsResponse.data || [];
        }
      } catch (error) {
        console.error('Error loading consent data:', error);
        this.error = error.response?.data?.message || 'Failed to load consent data. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    
    async loadFrameworks() {
      try {
        const response = await api.get('/api/frameworks/');
        if (response.data && Array.isArray(response.data)) {
          response.data.forEach(fw => {
            this.frameworks[fw.FrameworkId] = fw.FrameworkName;
          });
        }
      } catch (error) {
        console.error('Error loading frameworks:', error);
      }
    },
    
    getFrameworkName(frameworkId) {
      if (!frameworkId) return 'N/A';
      
      // If it's an object with FrameworkName
      if (typeof frameworkId === 'object' && frameworkId.FrameworkName) {
        return frameworkId.FrameworkName;
      }
      
      // If it's a number or string ID, look it up
      const id = typeof frameworkId === 'object' ? frameworkId.FrameworkId : frameworkId;
      return this.frameworks[id] || (id ? `Framework ${id}` : 'Default Framework');
    },
    
    getActionLabel(actionType) {
      return getActionLabel(actionType);
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    showWithdrawModal(consent) {
      this.selectedConsent = consent;
      this.withdrawReason = '';
      this.showWithdrawSingleModal = true;
    },
    
    closeWithdrawModal() {
      this.showWithdrawSingleModal = false;
      this.selectedConsent = null;
      this.withdrawReason = '';
    },
    
    async confirmWithdraw() {
      if (!this.selectedConsent) return;
      
      this.withdrawing = true;
      this.error = null;
      this.successMessage = null;
      
      try {
        const response = await withdrawConsent(
          this.userId,
          this.selectedConsent.action_type,
          this.withdrawReason || null
        );
        
        if (response.status === 'success') {
          this.successMessage = `Consent for ${this.getActionLabel(this.selectedConsent.action_type)} has been withdrawn successfully.`;
          this.closeWithdrawModal();
          await this.loadConsentData();
          
          // Clear success message after 5 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 5000);
        } else {
          this.error = response.message || 'Failed to withdraw consent.';
        }
      } catch (error) {
        console.error('Error withdrawing consent:', error);
        this.error = error.response?.data?.message || 'Failed to withdraw consent. Please try again.';
      } finally {
        this.withdrawing = false;
      }
    },
    
    async confirmWithdrawAll() {
      this.withdrawing = true;
      this.error = null;
      this.successMessage = null;
      
      try {
        const response = await withdrawAllConsents(
          this.userId,
          this.frameworkId,
          this.withdrawAllReason || null
        );
        
        if (response.status === 'success') {
          this.successMessage = `All consents have been withdrawn successfully.`;
          this.showWithdrawAllModal = false;
          this.withdrawAllReason = '';
          await this.loadConsentData();
          
          // Clear success message after 5 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 5000);
        } else {
          this.error = response.message || 'Failed to withdraw all consents.';
        }
      } catch (error) {
        console.error('Error withdrawing all consents:', error);
        this.error = error.response?.data?.message || 'Failed to withdraw all consents. Please try again.';
      } finally {
        this.withdrawing = false;
      }
    }
  }
};
</script>

<style scoped>
.consent-management {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.header {
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #f1f5f9;
}

.header h1 {
  font-size: 2.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 1rem;
  letter-spacing: -0.02em;
}

.header h1 i {
  color: #6366f1;
  font-size: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header p {
  color: #64748b;
  font-size: 1.0625rem;
  line-height: 1.6;
  margin: 0;
}

.loading, .error-message, .success-message {
  padding: 1.25rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid;
}

.loading {
  background: transparent;
  border: none;
  padding: 3rem 0;
  margin: 2rem 0;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  color: #64748b;
}

.loading-content p {
  font-size: 1.0625rem;
  font-weight: 500;
  margin: 0;
}

.spinner-large {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #991b1b;
  border-left-color: #ef4444;
}

.success-message {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  color: #166534;
  border-left-color: #22c55e;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.75rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.01em;
}

.btn-withdraw-all {
  padding: 0.875rem 1.75rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.2), 0 2px 4px -1px rgba(239, 68, 68, 0.1);
}

.btn-withdraw-all:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3), 0 4px 6px -2px rgba(239, 68, 68, 0.2);
}

.btn-withdraw-all:active {
  transform: translateY(0);
}

.consents-list, .withdrawals-list {
  display: grid;
  gap: 1.25rem;
}

.consent-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.75rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.consent-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  transition: width 0.3s ease;
}

.consent-card.active {
  border-color: #22c55e;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.15);
  background: linear-gradient(to right, #f0fdf4 0%, #ffffff 4%);
}

.consent-card.active::before {
  background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%);
  width: 4px;
}

.consent-card.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.2);
}

.consent-card.withdrawn {
  border-color: #fca5a5;
  opacity: 0.85;
  background: linear-gradient(to right, #fef2f2 0%, #ffffff 4%);
}

.consent-card.withdrawn::before {
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
  width: 4px;
}

.consent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.consent-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.consent-icon {
  font-size: 2rem;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.consent-card.active .consent-icon {
  color: #16a34a;
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
}

.consent-card.withdrawn .consent-icon {
  color: #dc2626;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}

.consent-info h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.consent-meta {
  margin: 0;
  color: #64748b;
  font-size: 0.9375rem;
  display: flex;
  gap: 1.25rem;
  flex-wrap: wrap;
  line-height: 1.6;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
}

.meta-item i {
  font-size: 0.875rem;
  color: #94a3b8;
  width: 16px;
  text-align: center;
}

.btn-withdraw {
  padding: 0.625rem 1.25rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
}

.btn-withdraw:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(239, 68, 68, 0.3);
}

.btn-withdraw:active {
  transform: translateY(0);
}

.no-consents {
  text-align: center;
  padding: 4rem 2rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  color: #64748b;
  border: 2px dashed #cbd5e1;
}

.no-consents i {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  color: #cbd5e1;
  opacity: 0.7;
}

.no-consents p {
  font-size: 1.125rem;
  font-weight: 500;
  color: #94a3b8;
  margin: 0;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: overlayFadeIn 0.2s ease;
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-container {
  background: white;
  border-radius: 24px;
  max-width: 560px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(0, 0, 0, 0.05);
  animation: modalSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  flex-direction: column;
}

.modal-container.withdraw-modal {
  max-width: 600px;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 2.5rem 1.75rem;
  border-bottom: 2px solid #f1f5f9;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  position: relative;
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.modal-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.modal-title-icon {
  color: white;
  font-size: 1.5rem;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.02em;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  font-size: 1.125rem;
  color: #64748b;
  cursor: pointer;
  padding: 0.625rem;
  border-radius: 10px;
  transition: all 0.2s ease;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
  transform: rotate(90deg);
}

.modal-body {
  padding: 2rem 2.5rem;
  overflow-y: auto;
  flex: 1;
}

.warning-box {
  display: flex;
  gap: 1.25rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-radius: 16px;
  border: 2px solid #fecaca;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}

.warning-box::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
}

.warning-box.critical {
  background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
  border-color: #fecdd3;
}

.warning-icon-wrapper {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.warning-icon {
  color: white;
  font-size: 1.5rem;
}

.warning-content {
  flex: 1;
}

.warning-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: #991b1b;
  letter-spacing: -0.01em;
}

.warning-message {
  margin: 0;
  font-size: 1rem;
  color: #7f1d1d;
  line-height: 1.6;
}

.action-name {
  font-weight: 700;
  color: #dc2626;
  background: rgba(255, 255, 255, 0.6);
  padding: 0.125rem 0.5rem;
  border-radius: 6px;
  display: inline-block;
}

.info-box {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  border: 1px solid #bae6fd;
  margin-bottom: 1.75rem;
}

.info-icon {
  color: #0369a1;
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.info-text {
  margin: 0;
  color: #0c4a6e;
  line-height: 1.7;
  font-size: 0.9375rem;
  flex: 1;
}

.form-group {
  margin-bottom: 0;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  margin-bottom: 0.75rem;
  color: #1e293b;
  font-weight: 600;
  font-size: 0.9375rem;
}

.label-icon {
  color: #6366f1;
  font-size: 0.875rem;
}

.optional-badge {
  font-weight: 500;
  color: #64748b;
  font-size: 0.875rem;
}

.form-textarea {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-family: inherit;
  font-size: 0.9375rem;
  resize: vertical;
  transition: all 0.2s ease;
  background: #ffffff;
  color: #1e293b;
  line-height: 1.6;
  min-height: 100px;
}

.form-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1), 0 2px 4px rgba(0, 0, 0, 0.05);
  background: #fafbfc;
}

.form-textarea::placeholder {
  color: #94a3b8;
  font-style: italic;
}

.char-count {
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: #64748b;
  text-align: right;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.75rem 2.5rem 2rem;
  border-top: 2px solid #f1f5f9;
  background: linear-gradient(135deg, #fafbfc 0%, #ffffff 100%);
}

.btn-cancel, .btn-confirm {
  padding: 0.9375rem 2rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9375rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 140px;
  justify-content: center;
}

.btn-cancel {
  background: #ffffff;
  color: #475569;
  border: 2px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-cancel:hover {
  background: #f8fafc;
  color: #334155;
  border-color: #cbd5e1;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-confirm {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3), 0 2px 4px rgba(239, 68, 68, 0.2);
}

.btn-confirm:hover:not(:disabled) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(239, 68, 68, 0.4), 0 4px 8px rgba(239, 68, 68, 0.3);
}

.btn-confirm:active:not(:disabled) {
  transform: translateY(0);
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.withdrawal-history-section {
  margin-top: 3.5rem;
  padding-top: 2.5rem;
  border-top: 2px solid #f1f5f9;
}

/* Responsive */
@media (max-width: 768px) {
  .consent-management {
    padding: 1rem;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .consent-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .btn-withdraw {
    width: 100%;
    justify-content: center;
  }
}
</style>

