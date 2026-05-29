<template>
  <div v-if="visible" class="audit-reassign-overlay" @click.self="close">
    <div class="audit-reassign-modal" role="dialog" aria-labelledby="audit-reassign-title">
      <div class="audit-reassign-header">
        <h3 id="audit-reassign-title">Reassign overdue audit</h3>
        <button type="button" class="close-btn" aria-label="Close" @click="close">&times;</button>
      </div>
      <p v-if="auditId" class="audit-reassign-meta">Audit ID: {{ auditId }}</p>
      <p class="audit-reassign-desc">
        Select a new auditor. They will receive a notification and the audit will return to &quot;Yet to Start&quot;.
      </p>
      <label class="audit-reassign-label">New auditor</label>
      <select v-model="selectedAuditorId" class="audit-reassign-select" :disabled="loadingUsers || submitting">
        <option value="">Select auditor</option>
        <option v-for="u in auditors" :key="u.UserId" :value="String(u.UserId)">
          {{ u.UserName }}
        </option>
      </select>
      <p v-if="error" class="audit-reassign-error">{{ error }}</p>
      <div class="audit-reassign-actions">
        <button type="button" class="btn btn-cancel" :disabled="submitting" @click="close">Cancel</button>
        <button
          type="button"
          class="btn btn-submit"
          :disabled="!selectedAuditorId || submitting"
          @click="submitReassign"
        >
          {{ submitting ? 'Reassigning…' : 'Reassign audit' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';
import { API_ENDPOINTS } from '@/config/api';

export default {
  name: 'AuditReassignModal',
  props: {
    visible: { type: Boolean, default: false },
    auditId: { type: [Number, String], default: null },
  },
  emits: ['close', 'reassigned'],
  data() {
    return {
      auditors: [],
      selectedAuditorId: '',
      loadingUsers: false,
      submitting: false,
      error: null,
    };
  },
  watch: {
    visible(val) {
      if (val) {
        this.error = null;
        this.selectedAuditorId = '';
        this.loadAuditors();
      }
    },
  },
  methods: {
    close() {
      if (!this.submitting) {
        this.$emit('close');
      }
    },
    async loadAuditors() {
      this.loadingUsers = true;
      try {
        const currentUserId =
          sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || '';
        const list = await api.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION, {
          params: {
            module: 'audit',
            permission_type: 'auditor',
            current_user_id: currentUserId,
          },
        });
        this.auditors = Array.isArray(list) ? list : (list?.data || []);
      } catch (e) {
        console.error('Failed to load auditors', e);
        this.error = 'Could not load auditor list.';
        this.auditors = [];
      } finally {
        this.loadingUsers = false;
      }
    },
    async submitReassign() {
      if (!this.auditId || !this.selectedAuditorId) return;
      this.submitting = true;
      this.error = null;
      try {
        const res = await api.post(API_ENDPOINTS.AUDIT_REASSIGN(this.auditId), {
          new_auditor_id: Number(this.selectedAuditorId),
        });
        const data = res?.data || res;
        if (data.success === false) {
          throw new Error(data.message || data.error || 'Reassign failed');
        }
        this.$emit('reassigned', { auditId: this.auditId, auditorId: this.selectedAuditorId });
        this.$emit('close');
      } catch (e) {
        this.error =
          e.response?.data?.error ||
          e.response?.data?.message ||
          e.message ||
          'Failed to reassign audit';
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script>

<style scoped>
.audit-reassign-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10050;
}
.audit-reassign-modal {
  background: #fff;
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  width: min(420px, 92vw);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
}
.audit-reassign-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.audit-reassign-header h3 {
  margin: 0;
  font-size: 1.15rem;
}
.close-btn {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
  line-height: 1;
}
.audit-reassign-meta {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0 0 0.5rem;
}
.audit-reassign-desc {
  font-size: 0.9rem;
  color: #475569;
  margin: 0 0 1rem;
}
.audit-reassign-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
}
.audit-reassign-select {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.audit-reassign-error {
  color: #b91c1c;
  font-size: 0.85rem;
  margin: 0 0 0.75rem;
}
.audit-reassign-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
.btn-cancel {
  padding: 0.45rem 0.9rem;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  border-radius: 6px;
  cursor: pointer;
}
.btn-submit {
  padding: 0.45rem 0.9rem;
  background: #1e3a8a;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.btn-submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
