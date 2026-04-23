<template>
  <div v-if="isVisible" class="modal-backdrop" @click.self="closeModal">
    <div class="workflow-modal">
      <div class="workflow-modal-header">
        <h3>Send for Approval</h3>
        <p class="workflow-modal-subtitle">Select user and reviewer to create workflow</p>
        <button type="button" class="close-btn" @click="closeModal">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="workflow-modal-body">
        <div class="workflow-form">
          <div class="form-group">
            <label for="assigned-user">Assigned User *</label>
            <select 
              id="assigned-user" 
              v-model="selectedUser" 
              class="form-control"
              :disabled="loading"
            >
              <option value="">Select User</option>
              <option 
                v-for="user in users" 
                :key="user.UserId" 
                :value="user.UserId"
              >
                {{ user.UserName }} ({{ user.department || 'No Department' }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="reviewer">Reviewer *</label>
            <select 
              id="reviewer" 
              v-model="selectedReviewer" 
              class="form-control"
              :disabled="loading"
            >
              <option value="">Select Reviewer</option>
              <option 
                v-for="reviewer in reviewers" 
                :key="reviewer.UserId" 
                :value="reviewer.UserId"
              >
                {{ reviewer.UserName }} ({{ reviewer.department || 'No Department' }})
              </option>
            </select>
          </div>

          <div v-if="riskData" class="risk-summary">
            <h4>Risk Summary</h4>
            <div class="risk-summary-content">
              <p><strong>Title:</strong> {{ riskData.title }}</p>
              <p><strong>Category:</strong> {{ riskData.category }}</p>
              <p><strong>Criticality:</strong> {{ riskData.criticality }}</p>
              <p><strong>Priority:</strong> {{ riskData.priority }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="workflow-modal-footer">
        <button 
          type="button" 
          class="btn primary" 
          @click="submitWorkflow"
          :disabled="!canSubmit || submitting"
        >
          <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
          {{ submitting ? 'Creating Workflow...' : 'Send for Approval' }}
        </button>
        <button type="button" class="btn ghost" @click="closeModal" :disabled="submitting">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js';
import apiService from '../../services/apiService.js';

export default {
  name: 'SystemRiskWorkflowModal',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    },
    riskData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      selectedUser: '',
      selectedReviewer: '',
      users: [],
      reviewers: [],
      loading: false,
      submitting: false
    };
  },
  computed: {
    canSubmit() {
      return this.selectedUser && this.selectedReviewer && this.riskData;
    }
  },
  watch: {
    isVisible(newVal) {
      if (newVal) {
        this.loadUsers();
        this.resetForm();
      }
    }
  },
  methods: {
    normalizeUsers(rawList) {
      if (!Array.isArray(rawList)) return [];
      return rawList
        .map((user) => {
          const userId = user?.UserId ?? user?.user_id ?? user?.id ?? user?.value ?? '';
          const userName = user?.UserName ?? user?.user_name ?? user?.username ?? user?.name ?? user?.label ?? '';
          const department = user?.department ?? user?.Department ?? user?.dept ?? '';

          if (!userId || !userName) return null;
          return {
            ...user,
            UserId: userId,
            UserName: userName,
            department
          };
        })
        .filter(Boolean);
    },

    resetForm() {
      this.selectedUser = this.riskData?.riskOwner || '';
      this.selectedReviewer = this.riskData?.reviewer || '';
      
      console.log('Reset form with pre-selected data:', {
        user: this.selectedUser,
        reviewer: this.selectedReviewer
      });
    },

    async loadUsers() {
      this.loading = true;
      try {
        const currentUserId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || '';
        const usersEndpoint = API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION
          || API_ENDPOINTS.USERS_FOR_DROPDOWN
          || API_ENDPOINTS.USERS;

        const response = await apiService.get(usersEndpoint, {
          module: 'risk',
          current_user_id: currentUserId
        });

        // Support multiple API response shapes:
        // 1) { status: 'success', data: [...] }
        // 2) { users: [...] }
        // 3) [ ... ]
        const payload = response?.data;
        const list = Array.isArray(payload)
          ? payload
          : (Array.isArray(payload?.data) ? payload.data : (Array.isArray(payload?.users) ? payload.users : []));

        const normalized = this.normalizeUsers(list);
        this.users = normalized;
        // For now use the same list for reviewer selection.
        this.reviewers = normalized;
      } catch (error) {
        console.error('Error loading users:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to load users list.'
        });
      } finally {
        this.loading = false;
      }
    },

    async submitWorkflow() {
      if (!this.canSubmit) return;

      this.submitting = true;
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_SEND_FOR_APPROVAL(this.riskData.id), {
          user_id: this.selectedUser,
          reviewer_id: this.selectedReviewer,
          risk_data: {
            risk_title: this.riskData.title,
            risk_type: this.riskData.type,
            category: this.riskData.category,
            criticality: this.riskData.criticality,
            risk_description: this.riskData.description,
            possible_damage: this.riskData.possibleDamage,
            business_impact: this.riskData.businessImpact,
            likelihood: this.riskData.likelihood,
            impact: this.riskData.impact,
            exposure_rating: this.riskData.exposure,
            priority: this.riskData.priority,
            mitigation_steps: this.riskData.mitigationSteps,
            compliance_id: this.riskData.complianceId,
            multiplier_x: this.riskData.multiplierX,
            multiplier_y: this.riskData.multiplierY
          }
        });

        if (response && (response.status === 'success' || response.data?.status === 'success')) {
          this.$notify?.({
            type: 'success',
            title: 'Success',
            text: 'Risk sent for approval successfully!'
          });
          
          this.$emit('workflow-created', {
            riskId: this.riskData.id,
            userId: this.selectedUser,
            reviewerId: this.selectedReviewer
          });
          
          this.closeModal();
        }
      } catch (error) {
        console.error('Error creating workflow:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: error.response?.data?.message || 'Failed to create workflow.'
        });
      } finally {
        this.submitting = false;
      }
    },

    closeModal() {
      if (!this.submitting) {
        this.$emit('close');
      }
    }
  }
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.workflow-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.workflow-modal-header {
  padding: 20px;
  border-bottom: 1px solid #e5e5e5;
  position: relative;
}

.workflow-modal-header h3 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 1.25rem;
}

.workflow-modal-subtitle {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #666;
  cursor: pointer;
  padding: 5px;
}

.close-btn:hover {
  color: #333;
}

.workflow-modal-body {
  padding: 20px;
}

.workflow-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.form-control {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-control:disabled {
  background-color: #f8f9fa;
  color: #6c757d;
}

.risk-summary {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 15px;
}

.risk-summary h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1rem;
}

.risk-summary-content p {
  margin: 5px 0;
  font-size: 0.9rem;
  color: #555;
}

.workflow-modal-footer {
  padding: 20px;
  border-top: 1px solid #e5e5e5;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s;
}

.btn.primary {
  background-color: #007bff;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn.primary:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.btn.ghost {
  background-color: transparent;
  color: #6c757d;
  border: 1px solid #ddd;
}

.btn.ghost:hover:not(:disabled) {
  background-color: #f8f9fa;
  color: #495057;
}

.btn.ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.fa-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>