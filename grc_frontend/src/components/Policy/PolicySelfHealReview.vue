<template>
  <div class="renewal-review-page">
    <div class="renewal-review-card global-form-box">
      <header class="renewal-review-header">
        <button
          type="button"
          class="back-btn"
          aria-label="Back"
          @click="$router.back()"
        >
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="renewal-review-header-text">
          <h1 class="global-form-title">Policy renewal review</h1>
          <p class="renewal-review-subtitle">
            Review the policy details below, then approve the current version or start an update in tailoring.
          </p>
        </div>
      </header>

      <div v-if="loading" class="renewal-review-loading">
        <i class="fas fa-spinner fa-spin"></i>
        <span>Loading policy details…</span>
      </div>

      <p v-else-if="error" class="global-form-error-message renewal-review-error">{{ error }}</p>

      <template v-else-if="policy">
        <div
          v-if="isAssignedCustodian"
          class="renewal-custodian-banner"
        >
          <i class="fas fa-user-shield"></i>
          <span>
            You were assigned as the renewal custodian because the original creator is no longer active.
          </span>
        </div>

        <div v-if="decisionComplete" class="renewal-success-banner">
          <i class="fas fa-check-circle"></i>
          <span>{{ message }}</span>
        </div>

        <section class="renewal-policy-hero">
          <h2>{{ policy.PolicyName }}</h2>
          <div class="renewal-status-pills">
            <span class="status-pill" :class="statusClass(policy.Status)">{{ policy.Status || '—' }}</span>
            <span class="status-pill status-pill-muted">{{ policy.ActiveInactive || '—' }}</span>
            <span v-if="policy.CurrentVersion" class="status-pill status-pill-version">
              v{{ policy.CurrentVersion }}
            </span>
          </div>
        </section>

        <section class="renewal-details-section">
          <h3 class="section-title">Policy details</h3>
          <div class="renewal-details-grid">
            <div
              v-for="field in detailFields"
              :key="field.label"
              class="detail-cell"
            >
              <span class="detail-label">{{ field.label }}</span>
              <span class="detail-value">
                <a
                  v-if="field.isLink && field.value"
                  :href="field.value"
                  target="_blank"
                  rel="noopener noreferrer"
                >View document</a>
                <template v-else>{{ field.value }}</template>
              </span>
            </div>
          </div>
        </section>

        <section v-if="policy.PolicyDescription" class="renewal-text-section">
          <h3 class="section-title">Description</h3>
          <p class="renewal-text-block">{{ policy.PolicyDescription }}</p>
        </section>

        <section v-if="policy.Scope" class="renewal-text-section">
          <h3 class="section-title">Scope</h3>
          <p class="renewal-text-block">{{ policy.Scope }}</p>
        </section>

        <section v-if="policy.Objective" class="renewal-text-section">
          <h3 class="section-title">Objective</h3>
          <p class="renewal-text-block">{{ policy.Objective }}</p>
        </section>

        <section v-if="subpolicies.length" class="renewal-subpolicies-section">
          <h3 class="section-title">Subpolicies ({{ subpolicies.length }})</h3>
          <div class="subpolicy-list">
            <div
              v-for="(sp, spIndex) in subpolicies"
              :key="sp.SubPolicyId || spIndex"
              class="subpolicy-card"
            >
              <div class="subpolicy-card-header">
                <span class="subpolicy-name">{{ sp.SubPolicyName }}</span>
                <span class="subpolicy-status">{{ sp.Status || '—' }}</span>
              </div>
              <div v-if="sp.Identifier" class="subpolicy-meta">
                <strong>Identifier:</strong> {{ sp.Identifier }}
              </div>
              <div v-if="sp.Description" class="subpolicy-meta subpolicy-desc">
                {{ sp.Description }}
              </div>
            </div>
          </div>
        </section>

        <footer v-if="!decisionComplete" class="renewal-actions">
          <button
            type="button"
            class="btn-renewal btn-renewal-approve"
            :disabled="acting"
            @click="submit('approve')"
          >
            <i v-if="acting && pendingAction === 'approve'" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-check"></i>
            Approved
          </button>
          <button
            type="button"
            class="btn-renewal btn-renewal-update"
            :disabled="acting"
            @click="submit('update')"
          >
            <i v-if="acting && pendingAction === 'update'" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-edit"></i>
            Update
          </button>
        </footer>

        <p v-if="actionHint && !decisionComplete" class="renewal-action-hint">
          {{ actionHint }}
        </p>
      </template>
    </div>
  </div>
</template>

<script>
import apiService from '@/services/apiService'
import { API_ENDPOINTS } from '@/config/api'
import { PopupService } from '@/modules/popus/popupService'

export default {
  name: 'PolicySelfHealReview',
  data() {
    return {
      loading: true,
      error: null,
      policy: null,
      acting: false,
      pendingAction: null,
      message: '',
      decisionComplete: false,
      isAssignedCustodian: false
    }
  },
  computed: {
    subpolicies() {
      return (this.policy && this.policy.subpolicies) || []
    },
    detailFields() {
      if (!this.policy) return []
      const p = this.policy
      const rows = [
        { label: 'Identifier', value: p.Identifier },
        { label: 'Framework', value: p.FrameworkName },
        { label: 'Department', value: p.Department },
        { label: 'Policy type', value: p.PolicyType },
        { label: 'Category', value: p.PolicyCategory },
        { label: 'Subcategory', value: p.PolicySubCategory },
        { label: 'Start date', value: this.formatDate(p.StartDate) },
        { label: 'End date', value: this.formatDate(p.EndDate) },
        { label: 'Created by', value: p.CreatedByName },
        { label: 'Created date', value: this.formatDate(p.CreatedByDate) },
        { label: 'Reviewer', value: p.Reviewer },
        { label: 'Applicability', value: p.Applicability },
        { label: 'Permanent / temporary', value: p.PermanentTemporary },
        { label: 'Entities', value: p.Entities },
        {
          label: 'Reminder rules',
          value: (p.reminder_rules && p.reminder_rules.length)
            ? p.reminder_rules.map(r => `${r.start_value} ${r.start_unit} before, ${r.frequency_unit}`).join('; ')
            : 'None configured'
        },
        { label: 'Document', value: p.DocURL, isLink: true }
      ]
      return rows.filter((r) => r.value != null && String(r.value).trim() !== '')
    },
    actionHint() {
      return 'Approved confirms the current policy period with no changes. Update opens tailoring to submit a new version for review.'
    }
  },
  async created() {
    const id = this.$route.query.policyId
    if (!id) {
      this.error = 'Missing policyId in URL.'
      this.loading = false
      return
    }
    this.isAssignedCustodian = this.$route.query.assigned === '1'
    try {
      const [details, meta] = await Promise.all([
        apiService.get(API_ENDPOINTS.POLICY_DETAILS(id), {}, { skipCache: true }),
        apiService.get(API_ENDPOINTS.POLICY(id), {}, { skipCache: true }).catch(() => ({}))
      ])
      this.policy = {
        ...meta,
        ...details,
        subpolicies: details.subpolicies || meta.subpolicies || []
      }
    } catch (e) {
      this.error =
        (e.response && e.response.data && e.response.data.error) ||
        e.message ||
        'Failed to load policy'
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatDate(val) {
      if (!val) return null
      const d = new Date(val)
      if (Number.isNaN(d.getTime())) return String(val)
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    },
    statusClass(status) {
      const s = (status || '').toLowerCase()
      if (s === 'approved') return 'status-pill-approved'
      if (s === 'under review') return 'status-pill-review'
      return 'status-pill-default'
    },
    async submit(action) {
      const id = this.$route.query.policyId
      if (!id || this.acting) return
      this.acting = true
      this.pendingAction = action
      this.message = ''
      this.error = null
      try {
        const res = await apiService.post(API_ENDPOINTS.POLICY_SELF_HEAL_DECISION(id), { action })
        if (res.redirect_path) {
          this.$router.push(res.redirect_path)
          return
        }
        this.decisionComplete = true
        this.message = res.message || 'Policy renewal approved.'
        PopupService.success(this.message, 'Renewal approved')
        if (res.StartDate) {
          this.policy = { ...this.policy, StartDate: res.StartDate, EndDate: res.EndDate }
        }
      } catch (e) {
        this.error =
          (e.response &&
            e.response.data &&
            (e.response.data.error || e.response.data.detail)) ||
          e.message ||
          'Request failed'
        PopupService.error(this.error, 'Error')
      } finally {
        this.acting = false
        this.pendingAction = null
      }
    }
  }
}
</script>

<style scoped>
.renewal-review-page {
  max-width: 920px;
  margin: 1.5rem auto 2.5rem;
  padding: 0 1rem;
  animation: renewal-fade-in 0.35s ease-out;
}

@keyframes renewal-fade-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.renewal-review-card {
  padding: 1.75rem 2rem 2rem;
}

.renewal-review-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 1.5rem;
}

.back-btn {
  border: none;
  background: #f0f2f8;
  color: #4f6cff;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  cursor: pointer;
  flex-shrink: 0;
  margin-top: 4px;
}

.back-btn:hover {
  background: #e4e8f5;
}

.renewal-review-header .global-form-title {
  margin: 0 0 0.35rem;
}

.renewal-review-subtitle {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
  line-height: 1.45;
}

.renewal-review-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #666;
  padding: 2rem 0;
}

.renewal-review-error {
  margin: 1rem 0;
}

.renewal-custodian-banner,
.renewal-success-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 0.9rem;
  line-height: 1.45;
  margin-bottom: 1.25rem;
  animation: renewal-fade-in 0.3s ease-out;
}

.renewal-custodian-banner {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
}

.renewal-success-banner {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.renewal-policy-hero {
  margin-bottom: 1.5rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #eee;
}

.renewal-policy-hero h2 {
  margin: 0 0 0.75rem;
  font-size: 1.35rem;
  color: #1a1a2e;
}

.renewal-status-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-pill {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
}

.status-pill-approved {
  background: #e8f7ee;
  color: #1b8a3e;
}

.status-pill-review {
  background: #fff8e1;
  color: #f57c00;
}

.status-pill-default,
.status-pill-muted {
  background: #f0f2f8;
  color: #555;
}

.status-pill-version {
  background: #ede7f6;
  color: #5e35b1;
}

.section-title {
  margin: 0 0 0.85rem;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.renewal-details-section {
  margin-bottom: 1.5rem;
}

.renewal-details-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 24px;
}

@media (max-width: 640px) {
  .renewal-details-grid {
    grid-template-columns: 1fr;
  }
}

.detail-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #888;
}

.detail-value {
  font-size: 0.95rem;
  color: #222;
  word-break: break-word;
}

.detail-value a {
  color: #4f6cff;
  font-weight: 500;
}

.renewal-text-section {
  margin-bottom: 1.25rem;
}

.renewal-text-block {
  margin: 0;
  padding: 12px 14px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  font-size: 0.92rem;
  line-height: 1.55;
  color: #333;
  white-space: pre-wrap;
}

.renewal-subpolicies-section {
  margin-bottom: 1.5rem;
}

.subpolicy-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.subpolicy-card {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fff;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.subpolicy-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
}

.subpolicy-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.subpolicy-name {
  font-weight: 600;
  color: #4f6cff;
}

.subpolicy-status {
  font-size: 0.8rem;
  padding: 3px 10px;
  border-radius: 12px;
  background: #f0f2f8;
  color: #555;
  flex-shrink: 0;
}

.subpolicy-meta {
  font-size: 0.88rem;
  color: #555;
  margin-top: 4px;
}

.subpolicy-desc {
  color: #666;
  line-height: 1.45;
}

.renewal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 1.75rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
}

.btn-renewal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 140px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, box-shadow 0.2s, transform 0.15s ease;
}

.btn-renewal:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-renewal:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-renewal-approve {
  background: #2e7d32;
  color: #fff;
}

.btn-renewal-approve:hover:not(:disabled) {
  background: #256b29;
  box-shadow: 0 4px 12px rgba(46, 125, 50, 0.35);
}

.btn-renewal-update {
  background: #4f6cff;
  color: #fff;
}

.btn-renewal-update:hover:not(:disabled) {
  background: #3d56d9;
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.35);
}

.renewal-action-hint {
  margin: 1rem 0 0;
  font-size: 0.85rem;
  color: #777;
  line-height: 1.45;
}
</style>
