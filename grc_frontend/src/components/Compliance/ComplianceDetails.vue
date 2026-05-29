<template>
  <div class="compliance_details_page">
    <!-- Header with Navigation -->
    <div class="compliance_header">
      <div class="compliance_header_left">
        <!-- Use global back-icon-btn styles from main.css -->
        <button class="back-icon-btn" @click="goBack" aria-label="Back">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h1 class="compliance_title">
          Details: {{ getComplianceId(selectedApproval) }}
          <span class="version-text" v-if="selectedApproval">(Version: {{ selectedApproval.version || selectedApproval.Version || 'u1' }})</span>
        </h1>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="compliance_loading_container">
      <div class="compliance_loading_spinner"></div>
      <p>Loading compliance details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="compliance_error_container">
      <div class="compliance_error_message">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Compliance</h3>
        <p>{{ error }}</p>
        <button class="compliance_retry_btn" @click="fetchComplianceDetails">Try Again</button>
      </div>
    </div>

    <!-- Compliance Details Content -->
    <div v-else-if="selectedApproval" class="compliance_details_container">
      <!-- Compliance Approval Section -->
      <div class="compliance_approval_section">
        <h4>Compliance Approval</h4>
        
        <!-- Compliance status indicator -->
        <div class="compliance_status_indicator">
          <span class="status-label">Status:</span>
          <span class="status-value" :class="{
            'status-approved': correctComplianceStatus === 'Approved',
            'status-rejected': correctComplianceStatus === 'Rejected',
            'status-pending': correctComplianceStatus === 'Under Review'
          }">
            {{ correctComplianceStatus }}
          </span>
          <span v-if="selectedApproval.ApprovedDate" class="approval-date">
            (Approved on: {{ formatDate(selectedApproval.ApprovedDate) }})
          </span>
          <span v-if="!canSubmitReviewComputed && canPerformReviewActionsComputed" class="status-note">
            <i class="fas fa-info-circle"></i>
            Review already submitted
          </span>
        </div>

        <div class="compliance_actions">
          <!-- Final Compliance Approval Button -->
          <!-- Show resubmission indicator for resubmitted items -->
          <div v-if="isResubmittedCompliance" class="resubmission-indicator">
            <i class="fas fa-redo-alt"></i>
            <span><strong>Resubmitted for Review:</strong> This compliance was previously rejected and has been resubmitted with modifications.</span>
          </div>
          
          <!-- Approval Buttons Container -->
          <div class="approval-buttons-container">
            <button 
              class="btn-approve" 
              @click="approveCompliance()" 
              v-if="canPerformReviewActionsComputed && (selectedApproval.ApprovedNot === null || isResubmittedCompliance || hasRejectionRemarks) && correctComplianceStatus !== 'Rejected'"
            >
              Final Approval
            </button>
            
            <button 
              class="btn-reject" 
              @click="rejectCompliance()"
              v-if="canPerformReviewActionsComputed && (selectedApproval.ApprovedNot === null || isResubmittedCompliance || hasRejectionRemarks) && correctComplianceStatus !== 'Rejected'"
            >
              Reject
            </button>
            
          </div>
          
          <!-- Show message when compliance is already processed -->
          <div v-if="canPerformReviewActionsComputed && !canSubmitReviewComputed" class="processed-compliance-message">
            <i class="fas fa-check-circle" v-if="correctComplianceStatus === 'Approved'"></i>
            <i class="fas fa-times-circle" v-if="correctComplianceStatus === 'Rejected'"></i>
            <span v-if="correctComplianceStatus === 'Approved'">This compliance has already been approved and cannot be submitted for review again.</span>
            <span v-if="correctComplianceStatus === 'Rejected'">This compliance has already been rejected and cannot be submitted for review again.</span>
          </div>
          
          <!-- Show message for compliance creators -->
          <div v-if="isCurrentUserCreatorComputed && selectedApproval.ApprovedNot === null && correctComplianceStatus !== 'Rejected'" class="creator-message">
            <i class="fas fa-info-circle"></i>
            <span>This compliance is under review. You cannot approve or reject your own compliance.</span>
          </div>
          
          <!-- Show message for administrators who are not assigned as reviewers -->
          <div v-if="isGRCAdministrator && !canPerformReviewActionsComputed && selectedApproval.ApprovedNot === null && correctComplianceStatus !== 'Rejected'" class="admin-message">
            <i class="fas fa-eye"></i>
            <span>Viewing compliance. You are not assigned as the reviewer for this compliance.</span>
          </div>
        </div>
      </div>

      <!-- Display compliance details -->
      <div v-if="selectedApproval" class="compliance_info_section">
        <h4>Compliance Information</h4>
        <div v-for="row in displayDetailRows" :key="row.key" class="compliance_detail_row">
          <strong>{{ row.label }}:</strong>
          <span v-if="row.key === 'Status'">
            {{ correctComplianceStatus }}
          </span>
          <ul v-else-if="row.isList" class="mitigation-points">
            <li v-for="(item, idx) in row.items" :key="`${row.key}-${idx}`">{{ item }}</li>
          </ul>
          <span v-else>{{ row.value }}</span>
        </div>
      </div>

      <!-- Show edited fields for resubmitted reviewer items -->
      <div v-if="changedFieldsForDisplay.length" class="compliance_info_section">
        <h4>Edited Changes (Previous vs Current)</h4>
        <div
          v-for="change in changedFieldsForDisplay"
          :key="change.field"
          class="compliance_detail_row"
        >
          <strong>{{ formatFieldName(change.field) }}:</strong>
          <span>
            <span style="color:#b91c1c;">{{ sanitizeValue(change.old_value ?? 'N/A') }}</span>
            <span> -> </span>
            <span style="color:#166534;">{{ sanitizeValue(change.new_value ?? 'N/A') }}</span>
          </span>
        </div>
      </div>
      
      <!-- Add a message for rejected compliances -->
      <div v-if="selectedApproval.ApprovedNot === false" class="rejected-compliance-message">
        <div class="rejection-note">
          <i class="fas fa-exclamation-triangle"></i>
          This compliance has been rejected.
        </div>
      </div>
    </div>

    <!-- Rejection Modal -->
    <div v-if="showRejectModal" class="compliance_reject_modal">
      <div class="compliance_reject_modal_content">
        <h4>Rejection Reason</h4>
        <p>Please provide a reason for rejecting this compliance</p>
        <textarea 
          v-model="rejectionComment" 
          class="compliance_rejection_comment" 
          placeholder="Enter your comments here..."></textarea>
        <div class="compliance_reject_modal_actions">
          <button class="compliance_cancel_btn" @click="cancelRejection" :disabled="isSubmittingRejection">Cancel</button>
          <button class="compliance_confirm_btn" @click="confirmRejection" :disabled="isSubmittingRejection">
            {{ isSubmittingRejection ? 'Submitting...' : 'Confirm Rejection' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import { useComplianceStore } from '@/stores/compliance'
import { usePermissionStore } from '@/stores/permission'

export default {
  name: 'ComplianceDetails',
  components: {
    PopupModal
  },
  setup() {
    const complianceStore = useComplianceStore()
    const permissionStore = usePermissionStore()
    return { complianceStore, permissionStore }
  },
  props: {
    complianceId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      selectedApproval: null,
      loading: true,
      error: null,
      showRejectModal: false,
      rejectionComment: '',
      isSubmittingRejection: false,
      // User management
      currentUserId: null,
      currentUserName: '',
      isGRCAdministrator: false,
      userInitialized: false,
      frameworkNameById: {},
      policyNameById: {},
      subPolicyNameById: {}
    }
  },
  async mounted() {
    await Promise.all([this.initializeUser(), this.fetchComplianceDetails()]);
  },
  methods: {
    async initializeUser() {
      try {
        console.log('Initializing user and checking role...');
        
        // Get current user role
        const responseData = await this.complianceStore.fetchUserRole({ background: true });
        console.log('User role API response:', responseData);
        
        if (responseData.success) {
          this.permissionStore.setFromUserRoleResponse(responseData)
          this.currentUserId = responseData.user_id;
          this.currentUserName = responseData.username || responseData.user_name || '';
          
          // Store username in localStorage for fallback
          if (this.currentUserName) {
            localStorage.setItem('user_name', this.currentUserName);
          }
          
          // Check specifically for "GRC Administrator" role
          const userRole = responseData.role;
          console.log('User role received:', userRole);
          
          // Use permissionStore gate instead of hard-coded role strings.
          this.isGRCAdministrator =
            this.permissionStore.can('compliance.details.adminReview') ||
            this.permissionStore.can('compliance.review.manageAll');
          
          console.log('Is GRC Administrator:', this.isGRCAdministrator);
          
          this.userInitialized = true;
        } else {
          console.error('User role API did not return success:', responseData);
          // Fallback for development/testing
          console.log('Using fallback user role for testing...');
          this.currentUserId = 2; // Default user ID
          this.isGRCAdministrator = false; // Default to non-administrator
          this.userInitialized = true;
        }
      } catch (error) {
        console.error('Error initializing user:', error);
        // Fallback for development/testing
        console.log('Using fallback user role due to error...');
        this.currentUserId = 2; // Default user ID
        this.isGRCAdministrator = false; // Default to non-administrator  
        this.userInitialized = true;
      }
    },

    async fetchComplianceDetails() {
      try {
        this.loading = true;
        this.error = null;

        console.log('Fetching compliance details for ID:', this.complianceId);

        // Step 1: Collect approval workflow metadata from sessionStorage (ApprovedNot, ReviewerId, etc.)
        let approvalMeta = {};
        const storedComplianceData = sessionStorage.getItem('complianceData');
        if (storedComplianceData) {
          try {
            const parsed = JSON.parse(storedComplianceData);
            const storedId = this.getComplianceId(parsed);
            if (storedId == this.complianceId) {
              approvalMeta = parsed;
              console.log('Loaded approval metadata from sessionStorage');
            }
          } catch (e) {
            console.warn('Failed to parse sessionStorage compliance data:', e);
          }
          sessionStorage.removeItem('complianceData');
        }

        // Step 2: Always fetch full compliance record directly from the API
        const compResp = await this.complianceStore.getComplianceById(this.complianceId);
        const compData = compResp?.data?.data || compResp?.data || null;

        if (!compData || (!compData.ComplianceId && !compData.compliance_id)) {
          // Fallback: if API returned nothing, use sessionStorage data if available
          if (Object.keys(approvalMeta).length > 0) {
            this.selectedApproval = approvalMeta;
            await this.enrichRelatedNames();
          } else {
            this.error = 'Could not load compliance details. Please try again.';
          }
          return;
        }

        // Step 3: Merge — keep DB data for content fields, but preserve approval-task
        // workflow metadata from session (ApprovedNot, ApprovalId, ReviewerId, etc.)
        // so pending deactivation items still show Final Approval / Reject correctly.
        this.selectedApproval = {
          ...compData,
          ...approvalMeta,
          ComplianceId: compData.ComplianceId || compData.compliance_id || this.complianceId,
          ExtractedData: {
            ...compData,
            // Keep latest review/resubmission edits from approval payload authoritative.
            ...(approvalMeta.ExtractedData || {}),
          }
        };

        console.log('Compliance details loaded from API:', this.selectedApproval);

        // Step 4: Enrich framework/policy/subpolicy names (FrameworkName already in compData if available)
        await this.enrichRelatedNames();

      } catch (error) {
        console.error('Error fetching compliance details:', error);
        this.error = this.handleError(error, 'loading compliance details');
      } finally {
        this.loading = false;
      }
    },

    goBack() {
      this.$router.push({ name: 'ComplianceApprover' });
    },

    getComplianceId(compliance) {
      if (!compliance) {
        return this.complianceId;
      }
      const extracted = compliance.ExtractedData || {};
      const candidate =
        extracted.compliance_id ??
        extracted.ComplianceId ??
        compliance.ComplianceId ??
        null;
      if (candidate != null && candidate !== '') {
        return typeof candidate === 'object'
          ? (candidate.ComplianceId ?? candidate.compliance_id ?? this.complianceId)
          : candidate;
      }
      return this.complianceId;
    },
    getApprovalId(compliance) {
      if (!compliance) return null;
      return compliance.ApprovalId || compliance.approval_id || null;
    },

    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return ''; // Invalid date
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },

    formatFieldName(field) {
      // Convert camelCase or PascalCase to display format
      return field
        // Insert space before all uppercase letters
        .replace(/([A-Z])/g, ' $1')
        // Replace first char with uppercase
        .replace(/^./, str => str.toUpperCase())
        .trim();
    },

    sanitizeValue(value) {
      if (value === null || value === undefined) return '';
      
      // If value is a string, clean it up
      if (typeof value === 'string') {
        // Remove HTML tags
        let cleanValue = value.replace(/<[^>]*>/g, '');
        
        // Remove API endpoint patterns
        cleanValue = cleanValue.replace(/api\/[^\s]*/g, '');
        
        // Remove code block patterns
        cleanValue = cleanValue.replace(/\[name='[^']*'\]/g, '');
        
        // Clean up extra whitespace
        cleanValue = cleanValue.replace(/\s+/g, ' ').trim();
        
        return cleanValue;
      }

      if (Array.isArray(value)) {
        return value.map(item => this.sanitizeValue(item)).filter(Boolean).join(', ');
      }

      if (typeof value === 'object') {
        try {
          return JSON.stringify(value);
        } catch (e) {
          return String(value);
        }
      }
      
      return String(value);
    },

    getFieldValue(key) {
      const extracted = this.selectedApproval?.ExtractedData || {};
      const topLevel = this.selectedApproval || {};

      // Deactivation records may store an internal request identifier at top-level.
      // For UI display, always prefer the canonical compliance identifier.
      if (String(key) === 'Identifier' && extracted?.type === 'compliance_deactivation') {
        const explicitComplianceIdentifier =
          extracted.compliance_identifier ||
          extracted.ComplianceIdentifier ||
          null;
        if (explicitComplianceIdentifier) return explicitComplianceIdentifier;

        const candidate =
          extracted.Identifier ||
          extracted.identifier ||
          topLevel.Identifier ||
          null;
        if (typeof candidate === 'string' && candidate.startsWith('COMP-DEACTIVATE-')) {
          const withoutPrefix = candidate.replace(/^COMP-DEACTIVATE-/, '');
          // Newer request IDs may append "-<ComplianceId>" at the end.
          return withoutPrefix.replace(/-\d+$/, '');
        }
        if (candidate != null) return candidate;
      }

      if (extracted[key] !== undefined) return extracted[key];
      if (topLevel[key] !== undefined) return topLevel[key];

      const lower = String(key).toLowerCase();
      const extractedMatch = Object.keys(extracted).find(k => k.toLowerCase() === lower);
      if (extractedMatch) return extracted[extractedMatch];

      const topLevelMatch = Object.keys(topLevel).find(k => k.toLowerCase() === lower);
      if (topLevelMatch) return topLevel[topLevelMatch];

      return undefined;
    },

    async enrichRelatedNames() {
      try {
        const frameworkId = this.getFieldValue('FrameworkId');
        const policyId = this.getFieldValue('PolicyId');
        const subPolicyId = this.getFieldValue('SubPolicy');

        const fwName = this.getFieldValue('FrameworkName');
        const polName = this.getFieldValue('PolicyName');
        const subName = this.getFieldValue('SubPolicyName');

        if (frameworkId && fwName) this.frameworkNameById[frameworkId] = fwName;
        if (policyId && polName) this.policyNameById[policyId] = polName;
        if (subPolicyId && subName) this.subPolicyNameById[subPolicyId] = subName;

        // API get_compliance_details already returns FrameworkName, PolicyName, SubPolicyName — skip heavy list/public calls.
        if (fwName && polName && subName) {
          return;
        }

        const routeCid = String(this.complianceId);
        const rawCid =
          this.selectedApproval?.ExtractedData?.ComplianceId ?? this.selectedApproval?.ComplianceId;
        const actualComplianceId =
          rawCid != null && typeof rawCid === 'object' ? rawCid.ComplianceId : rawCid;
        const actualIdStr = actualComplianceId != null ? String(actualComplianceId) : '';

        const hasTitle = !!(this.getFieldValue('ComplianceTitle') || '').trim();
        if (!hasTitle && actualIdStr && actualIdStr !== routeCid) {
          try {
            const compResp = await this.complianceStore.getComplianceById(actualIdStr);
            const compData = compResp?.data?.data ?? compResp?.data;
            const title = compData?.ComplianceTitle || compData?.compliance_title || null;
            if (title) {
              this.selectedApproval = {
                ...this.selectedApproval,
                ExtractedData: {
                  ...this.selectedApproval.ExtractedData,
                  ComplianceTitle: title,
                },
              };
            }
          } catch (e) {
            console.warn('Could not fetch ComplianceTitle from DB:', e);
          }
        }

        if (frameworkId && !fwName && !this.frameworkNameById[frameworkId]) {
          const frameworksResp = await this.complianceStore.getComplianceFrameworks();
          const frameworks = Array.isArray(frameworksResp?.data)
            ? frameworksResp.data
            : frameworksResp?.data?.frameworks || frameworksResp?.data?.data || [];
          frameworks.forEach((fw) => {
            const id = fw.FrameworkId || fw.id;
            const name = fw.FrameworkName || fw.name || fw.framework_name;
            if (id && name) this.frameworkNameById[id] = name;
          });
        }

        if (frameworkId && !polName) {
          const policiesResp = await this.complianceStore.getCompliancePolicies(frameworkId);
          const policiesArr = Array.isArray(policiesResp?.data)
            ? policiesResp.data
            : policiesResp?.data?.policies || [];
          policiesArr.forEach((pol) => {
            const id = pol.PolicyId || pol.id;
            const name = pol.PolicyName || pol.name;
            if (id && name) this.policyNameById[id] = name;
          });
        }

        if (policyId && !subName) {
          const subPoliciesResp = await this.complianceStore.getComplianceSubPolicies(policyId);
          const subPoliciesArr = Array.isArray(subPoliciesResp?.data)
            ? subPoliciesResp.data
            : subPoliciesResp?.data?.subpolicies || subPoliciesResp?.data?.data || [];
          subPoliciesArr.forEach((sp) => {
            const id = sp.SubPolicyId || sp.id;
            const name = sp.SubPolicyName || sp.name;
            if (id && name) this.subPolicyNameById[id] = name;
          });
        }
      } catch (error) {
        console.warn('Could not resolve framework/policy/subpolicy names:', error);
      }
    },

    parseMitigationPoints(rawMitigation) {
      if (!rawMitigation) return [];

      let parsed = rawMitigation;
      if (typeof rawMitigation === 'string') {
        const trimmed = rawMitigation.trim();
        if (!trimmed) return [];
        try {
          parsed = JSON.parse(trimmed);
        } catch (e) {
          // Not JSON; split by line breaks/bullets as fallback
          return trimmed
            .split(/\r?\n|•|- /)
            .map(s => s.trim())
            .filter(Boolean);
        }
      }

      if (Array.isArray(parsed)) {
        return parsed.map(item => this.sanitizeValue(item)).filter(Boolean);
      }

      if (parsed && typeof parsed === 'object') {
        return Object.keys(parsed)
          .sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true }))
          .map(key => this.sanitizeValue(parsed[key]))
          .filter(Boolean);
      }

      return [this.sanitizeValue(parsed)].filter(Boolean);
    },

    // Check if current user is the reviewer for this compliance (kept for backward compatibility)
    isCurrentUserReviewer(compliance) {
      if (!compliance || !this.currentUserId) return false;
      
      // For GRC Administrators, they can only review compliances specifically assigned to them
      if (this.isGRCAdministrator) {
        const reviewerId = compliance.ReviewerId || compliance.ExtractedData?.Reviewer;
        const reviewerName = compliance.ExtractedData?.Reviewer;
        
        // Check by ID first
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          return true;
        }
        
        // Check by username
        if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
          return true;
        }
        
        return false;
      }
      
      // Check if current user is the reviewer for this compliance
      const reviewerId = compliance.ReviewerId || compliance.ExtractedData?.Reviewer;
      const reviewerName = compliance.ExtractedData?.Reviewer;
      
      // Check by ID first
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by username (fallback for when reviewer is stored as username)
      if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
        return true;
      }
      
      // Check if the compliance was created by the current user (they shouldn't review their own compliances)
      if (this.isCurrentUserCreator(compliance)) {
        return false;
      }
      
      return false;
    },

    // Check if current user can perform review actions (approve/reject)
    canPerformReviewActions(compliance) {
      if (!compliance || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the compliance
      return this.isCurrentUserReviewer(compliance) && !this.isCurrentUserCreator(compliance);
    },

    // Check if current user is the creator of this compliance (kept for backward compatibility)
    isCurrentUserCreator(compliance) {
      if (!compliance || !this.currentUserId) return false;
      
      const createdBy = compliance.ExtractedData?.CreatedByName || compliance.CreatedByName;
      const createdById = compliance.ExtractedData?.CreatedBy || compliance.CreatedBy;
      const userId = compliance.ExtractedData?.UserID || compliance.UserID;
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by name (fallback)
      if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
        return true;
      }
      
      return false;
    },

    // Helper method to get current user name
    getCurrentUserName() {
      // For current user, use stored username or fallback to localStorage
      return this.currentUserName || localStorage.getItem('user_name') || '';
    },

    // Helper method to check if review can be submitted
    canSubmitReview(compliance) {
      if (!compliance || !compliance.ExtractedData) return false;
      
      // Can only submit review if compliance is under review and not already processed
      return this.correctComplianceStatus === 'Under Review' && 
             compliance.ApprovedNot === null;
    },

    // Helper method to get tooltip for submit button
    getSubmitButtonTooltip(compliance) {
      if (!compliance || !compliance.ExtractedData) return 'Cannot submit review';
      
      if (this.correctComplianceStatus === 'Approved') {
        return 'Compliance is already approved';
      } else if (this.correctComplianceStatus === 'Rejected') {
        return 'Compliance is already rejected';
      } else if (compliance.ApprovedNot !== null) {
        return 'Review decision already made';
      } else {
        return 'Submit your review decision';
      }
    },

    // Compliance Actions
    approveCompliance() {
      console.log('=== APPROVE COMPLIANCE CALLED ===');
      console.log('Selected approval:', this.selectedApproval);
      
      if (!this.selectedApproval || !this.getApprovalId(this.selectedApproval)) {
        console.error('No compliance selected for approval');
        PopupService.warning('Approval context missing. Open this item from Compliance Approver list and try again.', 'Missing Approval');
        return;
      }

      PopupService.confirm(
        'Are you sure you want to approve this compliance?',
        'Confirm Approval',
        () => {
          console.log('User confirmed approval, calling proceedWithComplianceApproval');
          this.proceedWithComplianceApproval();
        }
      );
    },

    proceedWithComplianceApproval() {
      console.log('=== PROCEED WITH COMPLIANCE APPROVAL ===');
      const approvalId = this.getApprovalId(this.selectedApproval);
      console.log('Approval ID:', approvalId);
      
      // Use the same approach as ComplianceApprover - submit compliance review with approval
      const reviewData = {
        ExtractedData: this.selectedApproval.ExtractedData || {},
        approved: true,
        remarks: '',
        UserId: this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy,
        ReviewerId: this.currentUserId,
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      // Clear resubmission flag when approving
      if (reviewData.ExtractedData.compliance_approval) {
        reviewData.ExtractedData.compliance_approval.inResubmission = false;
        reviewData.ExtractedData.compliance_approval.approved = true;
        reviewData.ExtractedData.compliance_approval.remarks = '';
      }
      
      // Set compliance ActiveInactive to Active when approved
      reviewData.ExtractedData.ActiveInactive = 'Active';
      reviewData.ExtractedData.Status = 'Approved';
      
      console.log('Review data for approval:', reviewData);
      
      // Submit compliance review using the compliance service
      this.complianceStore.submitComplianceReviewCompat(approvalId, reviewData)
        .then(response => {
          console.log('Compliance approved successfully:', response.data);
          
          // Update compliance status and store approval date
          this.selectedApproval.ExtractedData.Status = 'Approved';
          this.selectedApproval.ApprovedNot = true;
          
          // Store the approval date from the response
          if (response.data.ApprovedDate) {
            this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
          }
          
          PopupService.success('Compliance approved successfully!', 'Compliance Approved');
          
          // Navigate back to ComplianceApprover after a short delay to ensure backend processing
          setTimeout(() => {
            this.$router.push({ name: 'ComplianceApprover' });
          }, 1500);
        })
        .catch(error => {
          this.handleError(error, 'approving compliance');
        });
    },

    rejectCompliance() {
      this.showRejectModal = true;
    },

    submitReview() {
      console.log('submitReview called with approval:', this.selectedApproval);
      
      // Prevent submission if compliance is already processed (approved or rejected)
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Compliance is already rejected, preventing duplicate submission');
        PopupService.warning('Compliance has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Compliance is already approved, preventing duplicate submission');
        PopupService.warning('Compliance has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ApprovedNot !== null) {
        console.log('Delegating to submitComplianceReview with approval status:', this.selectedApproval.ApprovedNot);
        this.submitComplianceReview(this.selectedApproval.ApprovedNot);
      } else {
        console.error('Cannot submit review - no approval or approval status set');
      }
    },

    // Helper method to submit compliance review
    submitComplianceReview(approved, remarks = '') {
      if (!this.selectedApproval || !this.getApprovalId(this.selectedApproval)) {
        console.error('No compliance selected for review submission');
        PopupService.warning('Approval context missing. Open this item from Compliance Approver list and try again.', 'Missing Approval');
        return;
      }
      
      const approvalId = this.getApprovalId(this.selectedApproval);
      console.log(`Submitting compliance review for approval ${approvalId}`, {
        approved: approved,
        remarks: remarks
      });
      
      // Preserve the original UserId (compliance creator) and set ReviewerId to current user
      const originalUserId = this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy;
      
      // Create the compliance review data
      const reviewData = {
        ExtractedData: this.selectedApproval.ExtractedData || {},
        ApprovedNot: approved,
        remarks: remarks,
        UserId: originalUserId, // Preserve original compliance creator's ID
        ReviewerId: this.currentUserId, // Set reviewer ID to current user
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      console.log('Review data being sent:', reviewData);

      // Set compliance ActiveInactive to Active when approved
      if (approved === true) {
        reviewData.ExtractedData.ActiveInactive = 'Active';
      }
      
      // If rejecting, ensure compliance_approval contains rejection remarks and clear resubmission flag
      if (approved === false && remarks) {
        if (!reviewData.ExtractedData.compliance_approval) {
          reviewData.ExtractedData.compliance_approval = {};
        }
        reviewData.ExtractedData.compliance_approval.remarks = remarks;
        reviewData.ExtractedData.compliance_approval.approved = false;
        reviewData.ExtractedData.compliance_approval.inResubmission = false; // Clear resubmission flag
      }
      
      // If approving, clear resubmission flag and set approval status
      if (approved === true) {
        if (!reviewData.ExtractedData.compliance_approval) {
          reviewData.ExtractedData.compliance_approval = {};
        }
        reviewData.ExtractedData.compliance_approval.approved = true;
        reviewData.ExtractedData.compliance_approval.remarks = '';
        reviewData.ExtractedData.compliance_approval.inResubmission = false; // Clear resubmission flag
      }
      
      // Submit compliance review using the compliance service
      this.complianceStore.submitComplianceReviewCompat(approvalId, reviewData)
        .then(response => {
          console.log('Compliance review submitted successfully:', response.data);
          
          // Reset loading state
          this.isSubmittingRejection = false;
          
          // Update the approval data with the response
          this.selectedApproval.ApprovedNot = approved;
          this.selectedApproval.Version = response.data.Version;
          
          if (approved) {
            this.selectedApproval.ExtractedData.Status = 'Approved';
            
            // Store the approval date from the response
            if (response.data.ApprovedDate) {
              this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
            }
            
            PopupService.success('Compliance approved successfully!', 'Compliance Approved');
            
            // Navigate back to ComplianceApprover after a short delay to ensure backend processing
            setTimeout(() => {
              this.$router.push({ name: 'ComplianceApprover' });
            }, 1500);
          } else {
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            console.log('Compliance rejected - updating UI state');
            PopupService.success('Compliance rejected and sent back to user for revision!', 'Compliance Rejected');
          }
        })
        .catch(error => {
          this.handleError(error, 'submitting compliance review');
          // Reset loading state on error
          this.isSubmittingRejection = false;
        });
    },

    cancelRejection() {
      this.showRejectModal = false;
      this.rejectionComment = '';
      this.isSubmittingRejection = false; // Reset loading state
    },

    confirmRejection() {
      console.log('=== CONFIRM REJECTION CALLED ===');
      console.log('Rejection comment:', this.rejectionComment);
      console.log('Selected approval:', this.selectedApproval);
      
      if (!this.rejectionComment.trim()) {
        PopupService.warning('Please provide a rejection reason', 'Missing Reason');
        return;
      }

      // Prevent double submission
      if (this.isSubmittingRejection) {
        console.log('Rejection already in progress, preventing duplicate submission');
        return;
      }

      this.isSubmittingRejection = true;
      console.log('Setting isSubmittingRejection to true');
      
      // For direct compliance rejection, use submitComplianceReview with rejection reason
      if (!this.selectedApproval || !this.getApprovalId(this.selectedApproval)) {
        console.error('No compliance selected for rejection');
        PopupService.warning('Approval context missing. Open this item from Compliance Approver list and try again.', 'Missing Approval');
        this.cancelRejection();
        return;
      }
      
      // Initialize ExtractedData if it doesn't exist or is empty
      if (!this.selectedApproval.ExtractedData || Object.keys(this.selectedApproval.ExtractedData).length === 0) {
        this.selectedApproval.ExtractedData = {};
      }
      
      // Initialize compliance approval if doesn't exist
      if (!this.selectedApproval.ExtractedData.compliance_approval) {
        this.selectedApproval.ExtractedData.compliance_approval = {};
      }
      
      // Update the compliance status and approval state in the UI
      this.selectedApproval.ExtractedData.compliance_approval.approved = false;
      this.selectedApproval.ExtractedData.compliance_approval.remarks = this.rejectionComment;
      this.selectedApproval.ExtractedData.Status = 'Rejected';
      this.selectedApproval.ApprovedNot = false;
      
      console.log('Updated selectedApproval:', this.selectedApproval);
      
      // Submit the review with rejection data directly
      console.log('Calling submitComplianceReview with false and comment:', this.rejectionComment);
      this.submitComplianceReview(false, this.rejectionComment);
      
      // Close the modal after submission starts
      this.showRejectModal = false;
      this.rejectionComment = '';
    },

    // Helper method to handle and display errors
    handleError(error, context) {
      console.error(`Error ${context}:`, error);
      let errorMessage = 'An unexpected error occurred';

      if (error.response) {
        const data = error.response.data;
        // Prefer specific backend messages and avoid rendering booleans like "true".
        if (data && typeof data === 'object') {
          errorMessage = data.error || data.detail || data.message || `Server error: ${error.response.status}`;
        } else if (typeof data === 'string') {
          errorMessage = data;
        } else {
          errorMessage = `Server error: ${error.response.status}`;
        }
      } else if (error.request) {
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        errorMessage = error.message || errorMessage;
      }

      if (error.response?.status === 409 && /no pending user submission/i.test(String(errorMessage))) {
        errorMessage = 'This item is already processed or no longer pending review.';
      }

      PopupService.error(`Error ${context}: ${errorMessage}`, 'Error');
      return errorMessage;
    }
  },
  computed: {
    displayDetailRows() {
      if (!this.selectedApproval) return [];

      // All columns from the Compliance DB table, in a logical display order
      const complianceColumns = [
        // Identification
        { key: 'ComplianceTitle',           label: 'Compliance Title' },
        { key: 'Identifier',                label: 'Identifier' },
        { key: 'ComplianceVersion',         label: 'Compliance Version' },
        { key: 'Status',                    label: 'Status' },

        // Structure
        { key: '_framework',                label: 'Framework' },
        { key: '_policy',                   label: 'Policy' },
        { key: '_subpolicy',                label: 'Sub Policy' },

        // Content
        { key: 'ComplianceItemDescription', label: 'Compliance Item Description' },
        { key: 'ComplianceType',            label: 'Compliance Type' },
        { key: 'Scope',                     label: 'Scope' },
        { key: 'Objective',                 label: 'Objective' },
        { key: 'Applicability',             label: 'Applicability' },
        { key: 'BusinessUnitsCovered',      label: 'Business Units Covered' },

        // Classification
        { key: 'Criticality',               label: 'Criticality' },
        { key: 'MandatoryOptional',         label: 'Mandatory / Optional' },
        { key: 'ManualAutomatic',           label: 'Manual / Automatic' },
        { key: 'PermanentTemporary',        label: 'Permanent / Temporary' },
        { key: 'MaturityLevel',             label: 'Maturity Level' },
        { key: 'ActiveInactive',            label: 'Active / Inactive' },

        // Risk
        { key: 'IsRisk',                    label: 'Is Risk' },
        { key: 'Impact',                    label: 'Impact' },
        { key: 'Probability',               label: 'Probability' },
        { key: 'RiskType',                  label: 'Risk Type' },
        { key: 'RiskCategory',              label: 'Risk Category' },
        { key: 'RiskBusinessImpact',        label: 'Risk Business Impact' },
        { key: 'PotentialRiskScenarios',    label: 'Potential Risk Scenarios' },
        { key: 'PossibleDamage',            label: 'Possible Damage' },
        { key: 'mitigation',                label: 'Mitigation', isList: true },

        // Audit
        { key: 'CreatedByName',             label: 'Created By' },
        { key: 'CreatedByDate',             label: 'Created Date' },
        { key: 'Reviewer',                  label: 'Reviewer' },
      ];

      return complianceColumns.map(col => {
        const { key, label } = col;

        // ── Virtual / resolved keys ──────────────────────────────────────
        if (key === '_framework') {
          const name = this.getFieldValue('FrameworkName')
            || this.frameworkNameById[this.getFieldValue('FrameworkId')]
            || null;
          return { key, label, isList: false, items: [], value: name || 'N/A' };
        }
        if (key === '_policy') {
          const name = this.getFieldValue('PolicyName')
            || this.policyNameById[this.getFieldValue('PolicyId')]
            || null;
          return { key, label, isList: false, items: [], value: name || 'N/A' };
        }
        if (key === '_subpolicy') {
          const subId = this.getFieldValue('SubPolicy');
          const name = this.getFieldValue('SubPolicyName')
            || this.subPolicyNameById[subId]
            || null;
          return { key, label, isList: false, items: [], value: name || 'N/A' };
        }

        // ── Mitigation bullet list ────────────────────────────────────────
        if (col.isList) {
          const rawValue = this.getFieldValue(key);
          const points = this.parseMitigationPoints(rawValue);
          return { key, label, isList: true, items: points.length ? points : ['N/A'], value: '' };
        }

        // ── Status uses computed correctComplianceStatus ──────────────────
        if (key === 'Status') {
          return { key, label, isList: false, items: [], value: this.correctComplianceStatus };
        }

        // ── Boolean display ───────────────────────────────────────────────
        const rawValue = this.getFieldValue(key);
        if (typeof rawValue === 'boolean') {
          return { key, label, isList: false, items: [], value: rawValue ? 'Yes' : 'No' };
        }

        return {
          key,
          label,
          isList: false,
          items: [],
          value: (rawValue !== undefined && rawValue !== null && rawValue !== '')
            ? this.sanitizeValue(rawValue)
            : 'N/A'
        };
      });
    },

    changedFieldsForDisplay() {
      if (!this.selectedApproval) return [];

      // Prefer backend-computed diff when available.
      const serverChanges = this.selectedApproval.ChangedFields;
      if (Array.isArray(serverChanges) && serverChanges.length) {
        return serverChanges;
      }

      // Fallback: compute diff client-side from previous/current extracted payload.
      const current = this.selectedApproval.ExtractedData || {};
      const previous = this.selectedApproval.PreviousExtractedData || {};
      if (!Object.keys(previous).length) return [];

      const normalize = (value) => {
        if (value === null || value === undefined) return null;
        if (typeof value === 'string') return value.trim();
        if (Array.isArray(value) || typeof value === 'object') {
          try {
            return JSON.stringify(value);
          } catch (_e) {
            return String(value);
          }
        }
        return value;
      };

      const ignoredKeys = new Set(['compliance_approval', 'inResubmission']);
      const keys = new Set([...Object.keys(current), ...Object.keys(previous)]);
      const changes = [];

      keys.forEach((key) => {
        if (ignoredKeys.has(key)) return;
        if (normalize(current[key]) !== normalize(previous[key])) {
          changes.push({
            field: key,
            old_value: previous[key],
            new_value: current[key]
          });
        }
      });

      return changes;
    },

    // Computed property to get the correct compliance status
    correctComplianceStatus() {
      if (!this.selectedApproval) return 'Unknown';

      const isResubmitted =
        this.selectedApproval.ExtractedData?.compliance_approval?.inResubmission === true;
      if (isResubmitted) {
        return 'Under Review';
      }
      // Compliance table Status wins over stale ApprovedNot from an old approval row in sessionStorage.
      const tableStatus = this.selectedApproval.Status;
      const version = String(
        this.selectedApproval.Version || this.selectedApproval.version || ''
      );
      if (
        tableStatus === 'Under Review' &&
        (version.startsWith('u') || !version) &&
        this.selectedApproval.ApprovedNot === true
      ) {
        return 'Under Review';
      }
      if (this.selectedApproval.ApprovedNot === true) {
        return 'Approved';
      }
      if (this.selectedApproval.ApprovedNot === false) {
        return 'Rejected';
      }
      if (this.selectedApproval.ApprovedNot === null) {
        const hasRejectionRemarks = this.selectedApproval.ExtractedData?.compliance_approval?.remarks;
        if (hasRejectionRemarks) {
          return 'Under Review';
        }
      }
      return this.selectedApproval.ExtractedData?.Status || 'Under Review';
    },

    // Computed property to check if current user is the reviewer
    isCurrentUserReviewerComputed() {
      if (!this.selectedApproval || !this.currentUserId) return false;
      
      // For GRC Administrators, they can only review compliances specifically assigned to them
      if (this.isGRCAdministrator) {
        const reviewerId = this.selectedApproval.ReviewerId || this.selectedApproval.ExtractedData?.Reviewer;
        const reviewerName = this.selectedApproval.ExtractedData?.Reviewer;
        
        // Check by ID first
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          return true;
        }
        
        // Check by username
        if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
          return true;
        }
        
        return false;
      }
      
      // Check if current user is the reviewer for this compliance
      const reviewerId = this.selectedApproval.ReviewerId || this.selectedApproval.ExtractedData?.Reviewer;
      const reviewerName = this.selectedApproval.ExtractedData?.Reviewer;
      
      // Check by ID first
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by username (fallback for when reviewer is stored as username)
      if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
        return true;
      }
      
      // Check if the compliance was created by the current user (they shouldn't review their own compliances)
      if (this.isCurrentUserCreatorComputed) {
        return false;
      }
      
      return false;
    },

    // Computed property to check if current user is the creator
    isCurrentUserCreatorComputed() {
      if (!this.selectedApproval || !this.currentUserId) return false;
      
      const createdBy = this.selectedApproval.ExtractedData?.CreatedByName || this.selectedApproval.CreatedByName;
      const createdById = this.selectedApproval.ExtractedData?.CreatedBy || this.selectedApproval.CreatedBy;
      const userId = this.selectedApproval.ExtractedData?.UserID || this.selectedApproval.UserID;
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by name (fallback)
      if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
        return true;
      }
      
      return false;
    },

    // Computed property to check if current user can perform review actions
    canPerformReviewActionsComputed() {
      if (!this.selectedApproval || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the compliance
      return this.isCurrentUserReviewerComputed && !this.isCurrentUserCreatorComputed;
    },

    // Computed property to check if this is a resubmitted compliance
    isResubmittedCompliance() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;

      if (this.selectedApproval.ExtractedData?.compliance_approval?.inResubmission === true) {
        return true;
      }
      if (this.selectedApproval.ApprovedNot === null) {
        const hasRejectionRemarks = this.selectedApproval.ExtractedData?.compliance_approval?.remarks;
        if (hasRejectionRemarks && hasRejectionRemarks.trim().length > 0) {
          return true;
        }
      }
      return false;
    },

    // Computed property to check if compliance has rejection remarks
    hasRejectionRemarks() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;

      const remarks = this.selectedApproval.ExtractedData?.compliance_approval?.remarks;
      return !!(remarks && remarks.trim().length > 0);
    },

    // Computed property to check if review can be submitted
    canSubmitReviewComputed() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      
      // For resubmitted compliances, ApprovedNot is null and inResubmission is true
      const isResubmitted = this.selectedApproval.ExtractedData?.compliance_approval?.inResubmission === true;
      
      // Can submit review if:
      // 1. ApprovedNot is null (pending state) OR it's a resubmitted compliance AND
      // 2. Either status is "Under Review" OR it's a resubmitted compliance
      return (this.selectedApproval.ApprovedNot === null || this.isResubmittedCompliance) && 
             (this.correctComplianceStatus === 'Under Review' || isResubmitted);
    }
  }
}
</script>

<style scoped>
@import './ComplianceDetails.css';
</style>
