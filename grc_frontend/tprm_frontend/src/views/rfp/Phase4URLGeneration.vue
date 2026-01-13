<template>
  <div class="phase-container">
    <!-- Back Button -->
    <div class="back-button-container">
      <a @click.prevent="router.push('/rfp-vendor-selection')" class="back-button" style="cursor: pointer;">
        <ArrowLeft class="back-icon" />
        <span class="back-text">Back to Vendor Selection</span>
      </a>
    </div>

    <!-- Header -->
    <div class="header-section">
      <div class="header-content">
        <div class="header-text">
          <h1 class="page-title">
            <span class="title-icon">📧</span>
            Vendor Invitations
          </h1>
          <p class="page-description">
            Generate unique invitation URLs and send personalized invitations to selected vendors.
          </p>
        </div>
      </div>
    </div>

    <!-- Invitation Summary -->
    <div class="metrics-grid">
      <div class="metric-card metric-primary">
        <div class="metric-icon-wrapper metric-blue">
          <Users class="metric-icon" />
          </div>
        <div class="metric-content">
          <p class="metric-label">Selected Vendors</p>
          <p class="metric-value">{{ selectedVendorsCount }}</p>
          </div>
        <div class="metric-decoration"></div>
        </div>
        
      <div class="metric-card metric-primary">
        <div class="metric-icon-wrapper metric-green">
          <Send class="metric-icon" />
          </div>
        <div class="metric-content">
          <p class="metric-label">Invitations Sent</p>
          <p class="metric-value">{{ sentCount }}</p>
          </div>
        <div class="metric-decoration"></div>
        </div>
        
      <div class="metric-card metric-primary">
        <div class="metric-icon-wrapper metric-yellow">
          <CheckCircle2 class="metric-icon" />
          </div>
        <div class="metric-content">
          <p class="metric-label">Acknowledged</p>
          <p class="metric-value">{{ acknowledgedCount }}</p>
          </div>
        <div class="metric-decoration"></div>
        </div>
        
      <div class="metric-card metric-primary">
        <div class="metric-icon-wrapper metric-purple">
          <Clock class="metric-icon" />
          </div>
        <div class="metric-content">
          <p class="metric-label">Pending</p>
          <p class="metric-value">{{ pendingCount }}</p>
          </div>
        <div class="metric-decoration"></div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-section">
      <div class="tabs-container">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'tab-button',
            activeTab === tab.id ? 'tab-active' : 'tab-inactive'
          ]"
        >
          <span class="tab-indicator" v-if="activeTab === tab.id"></span>
          {{ tab.name }}
        </button>
      </div>

      <!-- URL Configuration Tab -->
      <div v-if="activeTab === 'configuration'" class="tab-content">
        <!-- Invitation URL Configuration -->
        <div class="content-card">
          <div class="card-header">
            <div class="card-header-content">
              <div class="card-icon-wrapper card-icon-blue">
                <Link2 class="card-icon" />
              </div>
              <div>
                <h3 class="card-title">Invitation URL Configuration</h3>
                <p class="card-subtitle">Configure and send vendor invitations</p>
              </div>
            </div>
          </div>
          <div class="card-body">
            <!-- Invitation System -->
            <div class="info-section">
              <div class="info-header">
                <div class="info-icon-wrapper">
                  <Shield class="info-icon" />
                </div>
                <h4 class="info-title">Vendor Invitation System</h4>
              </div>
              <div class="info-box">
                <div class="info-content">
                  <span class="info-label">System Overview:</span>
                  <ul class="info-list">
                    <li><span class="list-bullet">✓</span> Each vendor receives a unique invitation email with acknowledge/reject buttons</li>
                    <li><span class="list-bullet">✓</span> Unique URLs are generated in the backend and sent via email</li>
                    <li><span class="list-bullet">✓</span> Vendors can acknowledge or decline the invitation directly from the email</li>
                    <li><span class="list-bullet">✓</span> Acknowledged vendors are redirected to the external vendor portal</li>
                  </ul>
                </div>
                <div class="info-footer">
                  <p class="info-note">
                    <span class="note-icon">ℹ️</span>
                  The system automatically generates unique tokens and URLs in the backend. No manual URL management required.
                </p>
                </div>
              </div>
            </div>

            <!-- Email Configuration -->
            <div class="info-section">
              <div class="info-header">
                <div class="info-icon-wrapper">
                  <Mail class="info-icon" />
                </div>
                <h4 class="info-title">Email Invitation Settings</h4>
              </div>
              <div class="info-box">
                <div class="form-group">
                  <label class="form-label">
                    <span class="label-text">Custom Message (Optional)</span>
                    <span class="label-hint">Add a personalized message for your vendors</span>
                  </label>
                    <textarea 
                      v-model="customMessage"
                      placeholder="Add a custom message to include in the invitation emails..."
                    class="form-textarea"
                      rows="3"
                    ></textarea>
                  </div>
                <div class="checkbox-group">
                  <label class="checkbox-label">
                  <input
                    type="checkbox"
                      id="includeDeadline"
                      v-model="includeDeadline"
                      class="checkbox-input"
                  />
                    <span class="checkbox-custom"></span>
                    <span class="checkbox-text">Include RFP deadline in invitation email</span>
                </label>
                  </div>
                </div>
            </div>

            <!-- Generate Invitations Action -->
            <div class="action-card action-primary">
              <div class="action-content">
                <div class="action-text">
                  <div class="action-icon-wrapper">
                    <Send class="action-icon" />
                  </div>
                <div>
                    <h4 class="action-title">Ready to Send Invitations?</h4>
                    <p class="action-description">
                    Generate unique URLs and send personalized invitations to all selected vendors.
                  </p>
                    <div class="action-status">
                      <p v-if="selectedVendorsCount === 0" class="status-message status-error">
                        <span class="status-icon">⚠️</span>
                    No vendors selected. Please go back to Phase 3 to select vendors, or use test data for debugging.
                  </p>
                      <p v-else-if="isTestDataDetected" class="status-message status-warning">
                        <span class="status-icon">⚠️</span>
                        Test data detected! Please go back to Phase 3 to select real vendors for proper invitation generation.
                  </p>
                      <p v-else class="status-message status-success">
                        <span class="status-icon">✓</span>
                    {{ selectedVendorsCount }} vendor(s) ready for invitation.
                  </p>
                </div>
                  </div>
                </div>
                <div class="action-buttons">
                  <rfp-button
                    v-if="selectedVendorsCount === 0"
                    @click="createTestVendorData"
                    variant="outline"
                    size="sm"
                    class="btn-secondary"
                  >
                    <span class="btn-icon">🧪</span>
                    Create Test Data
                  </rfp-button>
                  <rfp-button
                    v-if="isTestDataDetected"
                    @click="clearTestDataAndGoToPhase3"
                    variant="outline"
                    size="sm"
                    class="btn-secondary"
                  >
                    <span class="btn-icon">↩️</span>
                    Go to Phase 3
                  </rfp-button>
                  <rfp-button
                    @click="fetchPrimaryContacts"
                    :disabled="loading || contactsLoading"
                    class="btn-primary"
                  >
                    <Send class="btn-icon" />
                    {{ contactsLoading ? 'Loading Contacts...' : (invitedVendors.length > 0 ? 'Send Additional Invitations' : 'Review & Send Invitations') }}
                  </rfp-button>
                </div>
              </div>
            </div>

            <!-- Open RFP Invitation Section -->
            <div class="action-card action-success">
              <div class="action-content">
                <div class="action-text">
                  <div class="action-icon-wrapper">
                    <Globe class="action-icon" />
                  </div>
                <div>
                    <h4 class="action-title">Open RFP Invitation</h4>
                    <p class="action-description">
                    Generate a public invitation URL that allows any vendor to submit proposals for this RFP.
                  </p>
                    <p class="action-hint">
                      <span class="hint-icon">💡</span>
                    This creates a public link that can be shared on websites, social media, or distributed broadly.
                  </p>
                </div>
                </div>
                <div class="action-buttons">
                  <rfp-button
                    @click="generateOpenRfpInvitation"
                    :disabled="loading || openInvitationLoading"
                    variant="outline"
                    class="btn-success"
                  >
                    <Globe class="btn-icon" />
                    {{ openInvitationLoading ? 'Generating...' : 'Generate Open RFP URL' }}
                  </rfp-button>
                </div>
              </div>
              
              <!-- Display Open RFP URL if generated -->
              <div v-if="openRfpUrl" class="url-display">
                <div class="url-header">
                  <p class="url-label">Open RFP Invitation URL:</p>
                </div>
                <div class="url-content">
                  <code class="url-text">{{ openRfpUrl }}</code>
                      <rfp-button
                        @click="copyToClipboard(openRfpUrl)"
                        variant="outline"
                        size="sm"
                    class="btn-copy"
                      >
                    <Copy class="copy-icon" />
                      </rfp-button>
                    </div>
                <div class="url-badges">
                  <span class="url-badge url-badge-active">Public Access</span>
                  <span class="url-badge url-badge-info">No Vendor Limit</span>
                  </div>
                </div>
                </div>
              </div>
            </div>

      </div>

      <!-- Distribution Status Tab -->
      <div v-if="activeTab === 'distribution'" class="tab-content">
        <!-- Vendor Invitation Management -->
        <div class="content-card">
          <div class="card-header">
            <div class="card-header-content">
              <div class="card-icon-wrapper card-icon-purple">
                <Users class="card-icon" />
              </div>
              <div>
                <h3 class="card-title">Vendor Invitation Management</h3>
                <p class="card-subtitle">Track and manage vendor invitations with unique URLs</p>
              </div>
            </div>
          </div>
          <div class="card-body">
            <div v-if="loading" class="loading-state">
              <div class="loading-spinner">
                <Loader2 class="spinner-icon" />
              </div>
              <p class="loading-text">Loading invitations...</p>
            </div>
            
            <div v-else-if="invitedVendors.length === 0" class="empty-state">
              <div class="empty-state-content">
                <div class="empty-icon-wrapper">
                  <Send class="empty-icon" />
                </div>
                <div class="empty-text">
                  <h3 class="empty-title">No invitations sent yet</h3>
                  <p class="empty-description">Generate and send unique invitation URLs to selected vendors.</p>
                </div>
                <rfp-button @click="handleGenerateAndSend" :disabled="loading" class="empty-action-button">
                  <Send class="button-icon" />
                  Generate & Send Invitations
              </rfp-button>
              </div>
            </div>
            
            <div v-else class="distribution-content">
              <!-- Bulk Actions -->
              <div class="bulk-actions-bar">
                <div class="bulk-actions-left">
                  <span class="bulk-actions-label">Bulk Actions:</span>
                  <rfp-button variant="outline" size="sm" @click="resendAllInvitations" :disabled="loading" class="bulk-action-button">
                    <Send class="action-button-icon" />
                    Resend All
                  </rfp-button>
                  <rfp-button variant="outline" size="sm" @click="exportInvitations" :disabled="loading" class="bulk-action-button">
                    <Download class="action-button-icon" />
                    Export List
                  </rfp-button>
                </div>
                <div class="bulk-actions-count">
                  <span class="count-badge">{{ invitedVendors.length }} invitation(s) total</span>
                  <span v-if="openInvitationsCount > 0" class="count-badge count-badge-success">
                    ({{ openInvitationsCount }} open)
                  </span>
                </div>
              </div>

              <!-- Invitations Table -->
              <div class="invitations-table-wrapper">
                <table class="invitations-table">
                  <thead class="table-header-sticky">
                    <tr class="table-header-row">
                        <th class="table-header-cell table-col-vendor">
                          <div class="header-content">
                            <span class="header-label">Vendor Details</span>
                          </div>
                        </th>
                        <th class="table-header-cell table-col-url">
                          <div class="header-content">
                            <span class="header-label">Unique URL</span>
                          </div>
                        </th>
                        <th class="table-header-cell table-col-status">
                          <div class="header-content">
                            <span class="header-label">Status</span>
                          </div>
                        </th>
                        <th class="table-header-cell table-col-timeline">
                          <div class="header-content">
                            <span class="header-label">Timeline</span>
                          </div>
                        </th>
                        <th class="table-header-cell table-col-actions">
                          <div class="header-content">
                            <span class="header-label">Actions</span>
                          </div>
                        </th>
                  </tr>
                </thead>
                  <tbody class="table-body">
                    <tr v-for="vendor in invitedVendors" :key="vendor.invitation_id" class="table-row">
                      <td class="table-cell table-col-vendor">
                        <div class="vendor-cell">
                          <div class="vendor-cell-header">
                            <p class="vendor-name">{{ vendor.vendor_name || 'Open RFP' }}</p>
                            <rfp-badge v-if="vendor.submission_source === 'open'" class="vendor-badge vendor-badge-public">
                              <Globe class="badge-icon" />
                            Public
                          </rfp-badge>
                        </div>
                          <p class="vendor-company">{{ vendor.company_name || 'Any Vendor' }}</p>
                          <p class="vendor-email">{{ vendor.vendor_email || 'Public Access' }}</p>
                      </div>
                    </td>
                      <td class="table-cell table-col-url">
                        <div class="url-cell">
                          <div class="url-cell-header">
                            <code class="url-token">{{ vendor.unique_token ? vendor.unique_token.substring(0, 8) + '...' : 'Not Generated' }}</code>
                            <rfp-badge 
                              :class="vendor.invitation_url ? 'url-badge url-badge-generated' : 'url-badge url-badge-pending'"
                            >
                              {{ vendor.invitation_url ? 'Generated' : 'Pending' }}
                            </rfp-badge>
                          </div>
                          <p class="url-note">
                            {{ vendor.invitation_url ? 'Email sent with unique URL' : 'URL will be generated when invitation is sent' }}
                          </p>
                      </div>
                    </td>
                      <td class="table-cell table-col-status">
                        <rfp-badge :class="getStatusColor(vendor.invitation_status)" class="status-badge-cell">
                          <component :is="getStatusIcon(vendor.invitation_status)" class="badge-icon" />
                        {{ vendor.invitation_status }}
                      </rfp-badge>
                    </td>
                      <td class="table-cell table-col-timeline">
                        <div class="timeline-cell">
                          <div v-if="vendor.invited_date" class="timeline-item timeline-sent">
                            <Clock class="timeline-icon" />
                            Sent: {{ new Date(vendor.invited_date).toLocaleDateString() }}
                          </div>
                          <div v-if="vendor.acknowledged_date" class="timeline-item timeline-acknowledged">
                            <CheckCircle2 class="timeline-icon" />
                            Acknowledged: {{ new Date(vendor.acknowledged_date).toLocaleDateString() }}
                          </div>
                          <div v-if="vendor.declined_reason" class="timeline-item timeline-declined">
                            <XCircle class="timeline-icon" />
                            Declined: {{ vendor.declined_reason }}
                          </div>
                        </div>
                    </td>
                      <td class="table-cell table-col-actions">
                        <div class="action-cell">
                        <rfp-button 
                          v-if="vendor.submission_source !== 'open'"
                          variant="outline" 
                          size="sm"
                            @click="resendInvitation(vendor.invitation_id)"
                          :disabled="loading"
                            title="Resend invitation"
                            class="action-icon-button"
                        >
                            <Send class="action-icon" />
                        </rfp-button>
                        <rfp-button 
                          v-if="vendor.submission_source === 'open'"
                          variant="outline" 
                          size="sm"
                            @click="copyToClipboard(vendor.invitation_url)"
                            title="Copy public URL"
                            class="action-icon-button"
                        >
                            <Copy class="action-icon" />
                        </rfp-button>
                        <rfp-button 
                          variant="outline" 
                          size="sm"
                            @click="viewInvitationDetails(vendor)"
                            title="View details"
                            class="action-icon-button"
                        >
                            <Eye class="action-icon" />
                        </rfp-button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tracking Tab -->
      <div v-if="activeTab === 'tracking'" class="tab-content">
        <!-- Invitation Analytics -->
        <div class="content-card">
          <div class="card-header">
            <div class="card-header-content">
              <div class="card-icon-wrapper card-icon-green">
                <BarChart3 class="card-icon" />
                  </div>
                    <div>
                <h3 class="card-title">Invitation Analytics & Tracking</h3>
                <p class="card-subtitle">Monitor invitation performance and vendor engagement</p>
                  </div>
                  </div>
                </div>
          <div class="card-body">
            <div v-if="loading" class="loading-state">
              <div class="loading-spinner">
                <Loader2 class="spinner-icon" />
                    </div>
              <p class="loading-text">Loading analytics...</p>
                    </div>
            
            <div v-else class="analytics-content">
              <!-- Key Metrics -->
              <div class="analytics-metrics-grid">
                <div class="analytics-metric-card metric-total">
                  <div class="metric-icon-container">
                    <Send class="metric-icon-large" />
                  </div>
                  <div class="metric-info">
                    <p class="metric-label">Total Sent</p>
                    <p class="metric-number">{{ invitationStats.total }}</p>
                  </div>
                  <div class="metric-decoration"></div>
                </div>
                
                <div class="analytics-metric-card metric-open">
                  <div class="metric-icon-container">
                    <Globe class="metric-icon-large" />
                    </div>
                  <div class="metric-info">
                    <p class="metric-label">Open RFP</p>
                    <p class="metric-number">{{ openInvitationsCount }}</p>
                    </div>
                  <div class="metric-decoration"></div>
                </div>
                
                <div class="analytics-metric-card metric-acknowledged">
                  <div class="metric-icon-container">
                    <CheckCircle2 class="metric-icon-large" />
                    </div>
                  <div class="metric-info">
                    <p class="metric-label">Acknowledged</p>
                    <p class="metric-number">{{ invitationStats.acknowledged }}</p>
                    </div>
                  <div class="metric-decoration"></div>
                  </div>
                
                <div class="analytics-metric-card metric-pending">
                  <div class="metric-icon-container">
                    <Clock class="metric-icon-large" />
                  </div>
                  <div class="metric-info">
                    <p class="metric-label">Pending</p>
                    <p class="metric-number">{{ invitationStats.pending }}</p>
                  </div>
                  <div class="metric-decoration"></div>
                </div>
                
                <div class="analytics-metric-card metric-rate">
                  <div class="metric-icon-container">
                    <TrendingUp class="metric-icon-large" />
                    </div>
                  <div class="metric-info">
                    <p class="metric-label">Response Rate</p>
                    <p class="metric-number">
                      {{ invitationStats.total > 0 ? Math.round((invitationStats.acknowledged / invitationStats.total) * 100) : 0 }}%
                      </p>
                    </div>
                  <div class="metric-decoration"></div>
                </div>
              </div>
              
              <!-- Detailed Analytics -->
              <div class="analytics-details-grid">
                <div class="analytics-detail-card">
                  <div class="detail-card-header">
                    <div class="detail-card-icon">
                      <BarChart3 class="detail-icon" />
                      </div>
                    <h3 class="detail-card-title">Status Breakdown</h3>
                    </div>
                  <div class="detail-card-body">
                    <div v-for="status in invitationStats.breakdown" :key="status.invitation_status" class="status-breakdown-item">
                      <div class="status-breakdown-left">
                        <div class="status-dot" :class="getStatusDotColor(status.invitation_status)"></div>
                        <span class="status-name">{{ status.invitation_status }}</span>
                      </div>
                      <span class="status-count">{{ status.count }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="analytics-detail-card">
                  <div class="detail-card-header">
                    <div class="detail-card-icon">
                      <Activity class="detail-icon" />
                    </div>
                    <h3 class="detail-card-title">Recent Activity</h3>
                        </div>
                  <div class="detail-card-body">
                    <div v-if="recentActivity.length === 0" class="activity-empty">
                      <p class="activity-empty-text">No recent activity</p>
                    </div>
                    <div v-else class="activity-list">
                      <div v-for="activity in recentActivity.slice(0, 5)" :key="activity.id" class="activity-item">
                        <div class="activity-dot"></div>
                        <div class="activity-content">
                          <p class="activity-description">{{ activity.description }}</p>
                          <p class="activity-time">{{ formatActivityTime(activity.timestamp) }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- URL Performance -->
              <div class="analytics-detail-card analytics-url-performance">
                <div class="detail-card-header">
                  <div class="detail-card-icon">
                    <Link2 class="detail-icon" />
                    </div>
                  <h3 class="detail-card-title">URL Performance</h3>
                    </div>
                <div class="url-performance-grid">
                  <div class="url-performance-item">
                    <p class="url-performance-number">{{ urlStats.totalClicks || 0 }}</p>
                    <p class="url-performance-label">Total Clicks</p>
                    </div>
                  <div class="url-performance-item">
                    <p class="url-performance-number">{{ urlStats.uniqueClicks || 0 }}</p>
                    <p class="url-performance-label">Unique Clicks</p>
                  </div>
                  <div class="url-performance-item">
                    <p class="url-performance-number">{{ urlStats.conversionRate || 0 }}%</p>
                    <p class="url-performance-label">Conversion Rate</p>
                </div>
              </div>
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Invitation Success Popup -->
  <div v-if="showSuccessPopup" class="modal-overlay" @click.self="closeSuccessPopup">
    <div class="success-modal-container">
      <div class="success-modal-content">
        <!-- Success Animation -->
        <div class="success-animation">
          <div class="success-checkmark">
            <div class="check-icon">
              <svg viewBox="0 0 52 52">
                <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Success Content -->
        <div class="success-content">
          <h2 class="success-title">Invitations Sent Successfully! 🎉</h2>
          <p class="success-subtitle">Your vendor invitations have been distributed</p>

          <!-- Stats Grid -->
          <div class="success-stats">
            <div class="stat-card stat-success">
              <div class="stat-icon-wrapper">
                <Send class="stat-icon" />
              </div>
              <div class="stat-content">
                <p class="stat-value">{{ successPopupData.totalSent }}</p>
                <p class="stat-label">Sent Successfully</p>
              </div>
            </div>
            
            <div v-if="successPopupData.totalFailed > 0" class="stat-card stat-warning">
              <div class="stat-icon-wrapper">
                <AlertCircle class="stat-icon" />
              </div>
              <div class="stat-content">
                <p class="stat-value">{{ successPopupData.totalFailed }}</p>
                <p class="stat-label">Failed</p>
              </div>
            </div>
          </div>

          <!-- Vendor List -->
          <div class="success-vendors">
            <h3 class="vendors-title">Invited Vendors</h3>
            <div class="vendors-list">
              <div v-for="invitation in successPopupData.invitations" :key="invitation.invitation_id" class="vendor-item">
                <div class="vendor-avatar-small">
                  <span class="vendor-initial">{{ invitation.vendor_name?.charAt(0) || 'V' }}</span>
                </div>
                <div class="vendor-details">
                  <p class="vendor-name">{{ invitation.vendor_name }}</p>
                  <p class="vendor-email">{{ invitation.vendor_email }}</p>
                </div>
                <div class="vendor-status success">
                  <CheckCircle2 class="status-icon" />
                  <span>Sent</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Failed Emails (if any) -->
          <div v-if="successPopupData.totalFailed > 0" class="failed-emails-section">
            <h3 class="failed-title">⚠️ Failed Invitations</h3>
            <div class="failed-list">
              <div v-for="failed in successPopupData.failedEmails" :key="failed.vendor_email" class="failed-item">
                <div class="failed-icon-wrapper">
                  <XCircle class="failed-icon" />
                </div>
                <div class="failed-details">
                  <p class="failed-email">{{ failed.vendor_email }}</p>
                  <p class="failed-reason">{{ failed.error }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="success-actions">
            <rfp-button
              @click="closeSuccessPopup"
              variant="outline"
              class="success-button success-button-secondary"
            >
              <span class="button-icon">✕</span>
              Close
            </rfp-button>
            <rfp-button
              @click="viewInvitations"
              class="success-button success-button-secondary"
            >
              <Eye class="button-icon" />
              View Invitations
            </rfp-button>
            <rfp-button
              @click="navigateAfterSuccess"
              class="success-button success-button-primary"
            >
              <CheckCircle2 class="button-icon" />
              Continue
            </rfp-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Contact Confirmation Dialog -->
  <div v-if="showContactConfirmation" class="modal-overlay">
    <div class="modal-container">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-header-content">
            <div class="modal-icon-wrapper">
              <Users class="modal-icon" />
            </div>
            <div>
              <h2 class="modal-title">Confirm Primary Contact Details</h2>
              <p class="modal-subtitle">Review and verify vendor contact information</p>
            </div>
          </div>
          <button @click="showContactConfirmation = false" class="modal-close-button">
            <X class="modal-close-icon" />
          </button>
        </div>
        
        <div class="modal-description">
          <div class="description-icon">📧</div>
          <p class="description-text">
            Please review the primary contact details for each selected vendor. These contacts will receive the invitation emails.
          </p>
        </div>

        <div class="modal-body">
          <div v-for="contact in primaryContacts" :key="contact.vendor_id" class="contact-card">
            <div v-if="contact.error" class="contact-error-card">
              <div class="error-content">
                <div class="error-icon-wrapper">
                  <AlertCircle class="error-icon" />
                </div>
                <div class="error-text">
                  <h3 class="error-title">Vendor ID: {{ contact.vendor_id }}</h3>
                  <p class="error-message">{{ contact.error }}</p>
                </div>
              </div>
            </div>
            
            <div v-else class="contact-success-card">
              <div class="contact-header">
                <div class="contact-avatar">
                  <span class="avatar-text">{{ contact.full_name.charAt(0) }}</span>
                </div>
                <div class="contact-info">
                  <h3 class="contact-name">{{ contact.full_name }}</h3>
                  <span class="contact-badge">
                    <span class="badge-dot"></span>
                    Primary Contact
                  </span>
                </div>
              </div>
              
              <div class="contact-details-grid">
                <div class="detail-item">
                  <div class="detail-icon-wrapper detail-email">
                    <Mail class="detail-icon" />
                  </div>
                  <div class="detail-content">
                    <label class="detail-label">Email Address</label>
                    <p class="detail-value detail-email-value">{{ contact.email }}</p>
                  </div>
                </div>
                
                <div class="detail-item">
                  <div class="detail-icon-wrapper detail-phone">
                    <Phone class="detail-icon" />
                  </div>
                  <div class="detail-content">
                    <label class="detail-label">Phone Number</label>
                    <p class="detail-value">{{ contact.phone || contact.mobile || 'Not provided' }}</p>
                  </div>
                </div>
                
                <div class="detail-item">
                  <div class="detail-icon-wrapper detail-designation">
                    <Briefcase class="detail-icon" />
                  </div>
                  <div class="detail-content">
                    <label class="detail-label">Designation</label>
                    <p class="detail-value">{{ contact.designation || 'Not specified' }}</p>
                  </div>
                </div>
                
                <div class="detail-item">
                  <div class="detail-icon-wrapper detail-department">
                    <Building class="detail-icon" />
                  </div>
                  <div class="detail-content">
                    <label class="detail-label">Department</label>
                    <p class="detail-value">{{ contact.department || 'Not specified' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <rfp-button
            @click="showContactConfirmation = false"
            variant="outline"
            class="modal-button modal-button-secondary"
          >
            <span class="button-icon">✕</span>
            Cancel
          </rfp-button>
          <rfp-button
            @click="confirmAndSendInvitations"
            :disabled="loading"
            class="modal-button modal-button-primary"
          >
            <Send class="button-icon" />
            {{ loading ? 'Sending...' : 'Confirm & Send Invitations' }}
          </rfp-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import { 
  Link2, 
  Send, 
  Copy, 
  CheckCircle2,
  Clock,
  XCircle,
  Eye,
  ArrowRight,
  Users,
  Globe,
  Shield,
  Loader2,
  Mail,
  Download,
  TrendingUp,
  BarChart3,
  Activity,
  X,
  AlertCircle,
  Phone,
  Briefcase,
  Building,
  ArrowLeft
} from 'lucide-vue-next'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRfpApi } from '@/composables/useRfpApi.js'
import rfpBadge from '@/components_rfp/rfpBadge.vue'
import rfpButton from '@/components_rfp/rfpButton.vue'
import rfpCard from '@/components_rfp/rfpCard.vue'
import rfpCardHeader from '@/components_rfp/rfpCardHeader.vue'
import rfpCardContent from '@/components_rfp/rfpCardContent.vue'
import rfpCardTitle from '@/components_rfp/rfpCardTitle.vue'
import newInvitationService from '@/services/newInvitationService.js'
import vendorInvitationService from '@/services/vendorInvitationService.js'
import { useRouter } from 'vue-router'

const { success: showToast, error: showErrorToast } = rfpUseToast()

// Router
const router = useRouter()

// Authentication
const { getAuthHeaders } = useRfpApi()

const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const activeTab = ref('configuration')
const loading = ref(false)
const invitedVendors = ref([])
const customMessage = ref('')
const includeDeadline = ref(true)
const primaryContacts = ref([])
const contactsLoading = ref(false)
const showContactConfirmation = ref(false)
const openRfpUrl = ref('')
const openInvitationLoading = ref(false)
const invitationStats = ref({
  total: 0,
  acknowledged: 0,
  pending: 0,
  breakdown: []
})
const recentActivity = ref([])
const urlStats = ref({
  totalClicks: 0,
  uniqueClicks: 0,
  conversionRate: 0
})
const showSuccessPopup = ref(false)
const successPopupData = ref({
  totalSent: 0,
  totalFailed: 0,
  failedEmails: [],
  invitations: []
})

const tabs = [
  { id: 'configuration', name: 'URL Configuration' },
  { id: 'distribution', name: 'Distribution Status' },
  { id: 'tracking', name: 'Tracking & Analytics' }
]

// Get RFP ID from route params or store
const rfpId = ref(null) // Will be set from localStorage

const sentCount = computed(() => invitedVendors.value.filter(v => v.invitation_status === "SENT" || v.invitation_status === "ACKNOWLEDGED").length)
const acknowledgedCount = computed(() => invitedVendors.value.filter(v => v.invitation_status === "ACKNOWLEDGED").length)
const pendingCount = computed(() => invitedVendors.value.filter(v => v.invitation_status === "SENT").length)
const openInvitationsCount = computed(() => invitedVendors.value.filter(v => v.submission_source === "open").length)

// Computed property for selected vendors count from localStorage
const selectedVendorsCount = computed(() => {
  try {
    const selectedVendorsData = localStorage.getItem('selectedVendors')
    if (selectedVendorsData) {
      const allVendors = JSON.parse(selectedVendorsData)
      return allVendors.total || 0
    }
    return 0
  } catch (error) {
    console.error('❌ [DEBUG] Error getting selected vendors count:', error)
    return 0
  }
})

// Computed property to detect if test data is being used
const isTestDataDetected = computed(() => {
  try {
    const selectedVendorsData = localStorage.getItem('selectedVendors')
    if (selectedVendorsData) {
      const allVendors = JSON.parse(selectedVendorsData)
      const isTestData = allVendors.existing?.some(v => v.company_name === "Test Company 1") || 
                        allVendors.manual?.some(v => v.company_name === "Manual Test Company")
      return isTestData
    }
    return false
  } catch (error) {
    console.error('❌ [DEBUG] Error detecting test data:', error)
    return false
  }
})

const getStatusColor = (status) => {
  switch (status) {
    case "SENT": return "status-badge active"
    case "ACKNOWLEDGED": return "status-badge evaluation"
    case "DECLINED": return "status-badge danger"
    case "RESPONDED": return "status-badge awarded"
    default: return "status-badge draft"
  }
}

const getStatusIcon = (status) => {
  switch (status) {
    case "SENT": return Send
    case "ACKNOWLEDGED": return CheckCircle2
    case "DECLINED": return XCircle
    case "RESPONDED": return Eye
    default: return Clock
  }
}

const getStatusDotColor = (status) => {
  switch (status) {
    case "SENT": return "bg-blue-500"
    case "ACKNOWLEDGED": return "bg-green-500"
    case "DECLINED": return "bg-red-500"
    case "RESPONDED": return "bg-purple-500"
    default: return "bg-gray-500"
  }
}

const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
  showToast("Copied to clipboard")
}

const loadInvitations = async () => {
  try {
    loading.value = true
    const response = await newInvitationService.getInvitationsByRfp(rfpId.value)
    invitedVendors.value = response.invitations || []
  } catch (error) {
    console.error('Error loading invitations:', error)
    showErrorToast("Failed to load invitations")
  } finally {
    loading.value = false
  }
}

const loadInvitationStats = async () => {
  try {
    const response = await vendorInvitationService.getInvitationStats(rfpId.value)
    invitationStats.value = response.stats
  } catch (error) {
    console.error('Error loading invitation stats:', error)
  }
}

const sendInvitation = async (invitationId) => {
  try {
    loading.value = true
    
    // Get RFP data from localStorage
    const selectedRFPData = localStorage.getItem('selectedRFP')
    let rfpData = {
      rfp_title: "Sample RFP Title",
      rfp_number: "RFP-2024-001",
      deadline: "2025-02-15"
    }
    
    if (selectedRFPData) {
      try {
        const parsedRfpData = JSON.parse(selectedRFPData)
        rfpData = {
          rfp_title: parsedRfpData.rfp_title || rfpData.rfp_title,
          rfp_number: parsedRfpData.rfp_number || rfpData.rfp_number,
          deadline: parsedRfpData.deadline || rfpData.deadline
        }
      } catch (error) {
        console.error('❌ [DEBUG] Error parsing RFP data:', error)
      }
    }
    
    // For individual invitation sending, we need to get the full invitation object
    // For now, create a minimal invitation object with the ID
    const invitationObj = {
      invitation_id: invitationId,
      vendor_email: "contact@example.com", // This should be populated from the invitation data
      vendor_name: "Vendor Contact",
      invitation_url: "https://rfp.company.com/invitation/" + invitationId,
      company_name: "Vendor Company"
    }
    const response = await vendorInvitationService.sendInvitations(rfpId.value, [invitationObj], rfpData)
    
    if (response.results && response.results[0] && response.results[0].success) {
      showToast("Invitation Sent", "Vendor invitation has been sent successfully.")
      await loadInvitations()
    } else {
      showErrorToast("Failed to send invitation")
    }
  } catch (error) {
    console.error('Error sending invitation:', error)
    showErrorToast("Failed to send invitation")
  } finally {
    loading.value = false
  }
}

const resendInvitation = async (invitationId) => {
  try {
    loading.value = true
    const rfpData = {
      title: "Sample RFP Title", // This should come from the current RFP context
      deadline: "2025-02-15"
    }
    
    await vendorInvitationService.resendInvitation(invitationId, rfpData)
    showToast("Invitation Resent", "Vendor invitation has been resent.")
    await loadInvitations()
  } catch (error) {
    console.error('Error resending invitation:', error)
    showErrorToast("Failed to resend invitation")
  } finally {
    loading.value = false
  }
}

// Handle generate and send - fetch contacts first if needed
const handleGenerateAndSend = async () => {
  try {
    // If contacts are not loaded, fetch them first (will show confirmation dialog)
    if (!primaryContacts.value || primaryContacts.value.length === 0) {
      await fetchPrimaryContacts()
    } else {
      // Contacts already loaded, proceed directly
      await generateAndSendInvitations()
    }
  } catch (error) {
    console.error('❌ [DEBUG] Error in handleGenerateAndSend:', error)
    showErrorToast("Failed to prepare invitations", "An error occurred while preparing vendor contacts.")
  }
}

// Fetch primary contacts for selected vendors
const fetchPrimaryContacts = async () => {
  try {
    console.log('👥 [DEBUG] Fetching primary contacts...')
    contactsLoading.value = true
    
    // Get selected vendors from localStorage (set by Phase 3)
    const selectedVendorsData = localStorage.getItem('selectedVendors')
    const selectedRFPData = localStorage.getItem('selectedRFP')
    
    console.log('📋 [DEBUG] Raw localStorage data:', {
      selectedVendorsData,
      selectedRFPData
    })
    
    if (!selectedVendorsData || !selectedRFPData) {
      console.error('❌ [DEBUG] Missing vendor or RFP data in localStorage')
      showErrorToast("No vendor selection found", "Please go back to Phase 3 and select vendors first.")
      return
    }
    
    const allVendors = JSON.parse(selectedVendorsData)
    const rfpData = JSON.parse(selectedRFPData)
    
    console.log('📋 [DEBUG] Parsed vendors:', allVendors)
    console.log('📋 [DEBUG] Parsed RFP:', rfpData)
    
    const allContacts = []
    
    // Handle existing vendors - use contact info already fetched in Phase 3
    if (allVendors.existing && allVendors.existing.length > 0) {
      console.log('🏢 [DEBUG] Processing existing vendors:', allVendors.existing.length)
      
      for (const vendor of allVendors.existing) {
        console.log(`📋 [DEBUG] Processing vendor:`, vendor)
        
        // Check if contact_info is already present (from Phase 3)
        if (vendor.contact_info && vendor.contact_info.email) {
          console.log(`✅ [DEBUG] Using contact info from Phase 3 for vendor ${vendor.vendor_id}`)
          
          allContacts.push({
            vendor_id: vendor.vendor_id,
            vendor_type: 'existing',
            company_name: vendor.company_name,
            contact_id: vendor.contact_info.contact_id,
            first_name: vendor.contact_info.first_name,
            last_name: vendor.contact_info.last_name,
            full_name: `${vendor.contact_info.first_name} ${vendor.contact_info.last_name}`.trim(),
            email: vendor.contact_info.email,
            phone: vendor.contact_info.phone || vendor.contact_info.mobile || vendor.contact_phone,
            mobile: vendor.contact_info.mobile,
            designation: vendor.contact_info.designation || vendor.contact_designation,
            department: vendor.contact_info.department || vendor.contact_department || 'Vendor Relations',
            contact_type: vendor.contact_info.contact_type || 'PRIMARY'
          })
        } else if (vendor.contact_email) {
          // Fallback: use quick access fields from Phase 3
          console.log(`⚠️ [DEBUG] Using quick access fields for vendor ${vendor.vendor_id}`)
          
          allContacts.push({
            vendor_id: vendor.vendor_id,
            vendor_type: 'existing',
            company_name: vendor.company_name,
            contact_id: null,
            first_name: vendor.contact_name?.split(' ')[0] || 'Unknown',
            last_name: vendor.contact_name?.split(' ').slice(1).join(' ') || 'Contact',
            full_name: vendor.contact_name || 'Unknown Contact',
            email: vendor.contact_email,
            phone: vendor.contact_phone,
            mobile: vendor.contact_phone,
            designation: vendor.contact_designation || 'Primary Contact',
            department: vendor.contact_department || 'Vendor Relations',
            contact_type: 'PRIMARY'
          })
        } else {
          // No contact information available
          console.error(`❌ [DEBUG] No contact information for vendor ${vendor.vendor_id}`)
          allContacts.push({
            vendor_id: vendor.vendor_id,
            vendor_type: 'existing',
            company_name: vendor.company_name,
            error: 'No primary contact information available. Please ensure vendors have primary contacts in Phase 3.'
          })
        }
      }
    }
    
    // Handle unmatched vendors (manual + bulk) - use contact details from rfp_unmatched_vendors table
    if (allVendors.manual && allVendors.manual.length > 0) {
      console.log('📝 [DEBUG] Manual vendors:', allVendors.manual)
      allVendors.manual.forEach(vendor => {
        allContacts.push({
          vendor_id: vendor.id || vendor.unmatched_id,
          vendor_type: 'manual',
          company_name: vendor.company_name,
          contact_id: null,
          first_name: vendor.vendor_name?.split(' ')[0] || 'Unknown',
          last_name: vendor.vendor_name?.split(' ').slice(1).join(' ') || 'Contact',
          full_name: vendor.vendor_name || 'Unknown Contact',
          email: vendor.vendor_email,
          phone: vendor.vendor_phone,
          mobile: vendor.vendor_phone,
          designation: 'Primary Contact',
          department: 'Vendor Relations',
          contact_type: 'PRIMARY'
        })
      })
    }
    
    if (allVendors.bulk && allVendors.bulk.length > 0) {
      console.log('📦 [DEBUG] Bulk vendors:', allVendors.bulk)
      allVendors.bulk.forEach(vendor => {
        allContacts.push({
          vendor_id: vendor.unmatched_id,
          vendor_type: 'bulk',
          company_name: vendor.company_name,
          contact_id: null,
          first_name: vendor.vendor_name?.split(' ')[0] || 'Unknown',
          last_name: vendor.vendor_name?.split(' ').slice(1).join(' ') || 'Contact',
          full_name: vendor.vendor_name || 'Unknown Contact',
          email: vendor.vendor_email,
          phone: vendor.vendor_phone,
          mobile: vendor.vendor_phone,
          designation: 'Primary Contact',
          department: 'Vendor Relations',
          contact_type: 'PRIMARY'
        })
      })
    }
    
    console.log('✅ [DEBUG] All contacts prepared:', allContacts)
    
    if (allContacts.length > 0) {
      primaryContacts.value = allContacts
      showContactConfirmation.value = true
    } else {
      showErrorToast("No vendors selected", "Please select vendors in Phase 3 first.")
    }
    
  } catch (error) {
    console.error('❌ [DEBUG] Error fetching primary contacts:', error)
    showErrorToast("Failed to fetch contact details", "Please try again or contact support.")
  } finally {
    contactsLoading.value = false
  }
}

// Confirm and send invitations after reviewing contacts
const confirmAndSendInvitations = async () => {
  try {
    showContactConfirmation.value = false
    await generateAndSendInvitations()
  } catch (error) {
    console.error('❌ [DEBUG] Error in confirmAndSendInvitations:', error)
  }
}

const generateAndSendInvitations = async () => {
  loading.value = true
  
  try {
    console.log('🔍 [DEBUG] Starting NEW URI invitation generation process...')
    
    // Get selected vendors from localStorage (set by Phase 3)
    const selectedVendorsData = localStorage.getItem('selectedVendors')
    const selectedRFPData = localStorage.getItem('selectedRFP')
    
    console.log('📋 [DEBUG] Raw localStorage data:', {
      selectedVendorsData,
      selectedRFPData
    })
    
    if (!selectedVendorsData || !selectedRFPData) {
      console.error('❌ [DEBUG] Missing vendor or RFP data in localStorage')
      showErrorToast("No vendor selection found", "Please go back to Phase 3 and select vendors first.")
      loading.value = false
      return
    }
    
    const allVendors = JSON.parse(selectedVendorsData)
    const rfpData = JSON.parse(selectedRFPData)
    
    console.log('📊 [DEBUG] Parsed data:', {
      allVendors,
      rfpData
    })
    
    // Update RFP ID from the stored data
    rfpId.value = rfpData.rfp_id
    
    // If primaryContacts are not loaded, fetch them first
    if (!primaryContacts.value || primaryContacts.value.length === 0) {
      console.log('📧 [DEBUG] Primary contacts not loaded, fetching them first...')
      await fetchPrimaryContacts()
      // Wait for user to confirm contacts in the dialog
      // The confirmAndSendInvitations will be called after confirmation
      loading.value = false
      return
    }
    
    // Prepare vendor data for NEW URI method
    const selectedVendors = []
    
    if (primaryContacts.value && primaryContacts.value.length > 0) {
      console.log('👥 [DEBUG] Using confirmed contact details:', primaryContacts.value)
      
      primaryContacts.value.forEach(contact => {
        if (contact.error) {
          console.warn('⚠️ [DEBUG] Skipping contact with error:', contact.error)
          return
        }
        
        console.log('👤 [DEBUG] Processing contact:', contact)
        
        // For existing vendors, use vendor_id and contact info
        if (contact.vendor_type === 'existing') {
          selectedVendors.push({
            vendor_id: contact.vendor_id, // Use vendor_id from contact (already extracted from Phase 3 data)
            vendor_name: contact.full_name,
            email: contact.email,
            phone: contact.phone || contact.mobile,
            company_name: contact.company_name,
            is_matched_vendor: true,
            vendor_type: 'existing',
            contact_id: contact.contact_id,
            contact_info: {
              first_name: contact.first_name,
              last_name: contact.last_name,
              designation: contact.designation,
              department: contact.department,
              contact_type: contact.contact_type
            }
          })
        } else {
          // For unmatched vendors (manual/bulk), don't include vendor_id
          selectedVendors.push({
            vendor_id: null,
            vendor_name: contact.full_name,
            email: contact.email,
            phone: contact.phone || contact.mobile,
            company_name: contact.company_name,
            is_matched_vendor: false,
            vendor_type: contact.vendor_type
          })
        }
      })
    } else {
      showErrorToast("No contact information", "Please confirm vendor contacts before sending invitations.")
      loading.value = false
      return
    }
    
    if (selectedVendors.length === 0) {
      showErrorToast("No vendors to invite", "Please select vendors in Phase 3 first.")
      loading.value = false
      return
    }
    
    console.log('📤 [DEBUG] Final selectedVendors array:', selectedVendors)
    console.log('📤 [DEBUG] About to create invitations using NEW URI method for vendors:', selectedVendors)
    
    try {
      // Use NEW URI method to create invitations
      const response = await newInvitationService.generateInvitations(
        rfpId.value,
        selectedVendors,
        customMessage.value || "Please review our RFP and submit your proposal."
      )
      
      console.log('✅ [DEBUG] NEW URI Invitation creation response:', response)
      
      if (response.success && response.invitations) {
        console.log('📧 [DEBUG] Generated invitations with NEW URI method:', response.invitations)
        
        // Send email invitations using the new service
        const emailResponse = await newInvitationService.sendInvitationEmails(response.invitations, rfpData)
        console.log('✅ [DEBUG] Email sending response:', emailResponse)
        console.log('✅ [DEBUG] Email response structure:', {
          success: emailResponse.success,
          sent_emails: emailResponse.sent_emails,
          failed_emails: emailResponse.failed_emails,
          sentCount: emailResponse.sent_emails?.length,
          failedCount: emailResponse.failed_emails?.length
        })
        
        if (emailResponse && emailResponse.success !== false) {
          const sentCount = emailResponse.sent_emails?.length || 0
          const failedCount = emailResponse.failed_emails?.length || 0
          
          if (sentCount > 0) {
            // Show comprehensive success popup (no toast notification)
            showInvitationSuccessPopup({
              totalSent: sentCount,
              totalFailed: failedCount,
              failedEmails: emailResponse.failed_emails || [],
              invitations: response.invitations
            })
          } else {
            // Only show error if no emails were sent at all
            showErrorToast(
              "No invitations sent", 
              "Failed to send any invitations. Please check your configuration."
            )
          }
          
          if (failedCount > 0) {
            console.log('❌ [DEBUG] Failed emails details:', emailResponse.failed_emails)
            
            // Display detailed error information
            emailResponse.failed_emails.forEach(failed => {
              console.log(`❌ Failed Email Details:`)
              console.log(`  Vendor: ${failed.vendor_email}`)
              console.log(`  Error: ${failed.error}`)
              console.log(`  Error Type: ${failed.error_type || 'Unknown'}`)
            })
          }
          
          // Display the generated URLs for manual sending if any failed
          if (failedCount > 0) {
            console.log('📧 [DEBUG] MANUAL EMAIL SENDING REQUIRED:')
            response.invitations.forEach(invitation => {
              console.log(`\n📧 Manual Email for ${invitation.vendor_name} (${invitation.vendor_email}):`)
              console.log(`🔗 NEW URI URL: ${invitation.invitation_url}`)
              console.log(`📝 Content: ${newInvitationService.generateEmailBody(invitation, rfpData)}`)
            })
          }
        } else {
          console.error('❌ [DEBUG] Email sending completely failed:', emailResponse)
          showErrorToast(
            "Email sending failed", 
            "Invitations were generated but emails could not be sent. Check console for manual sending instructions."
          )
          
          // Display all generated URLs for manual sending
          console.log('📧 [DEBUG] ALL EMAILS REQUIRE MANUAL SENDING:')
          response.invitations.forEach(invitation => {
            console.log(`\n📧 Manual Email for ${invitation.vendor_name} (${invitation.vendor_email}):`)
            console.log(`🔗 NEW URI URL: ${invitation.invitation_url}`)
            console.log(`📝 Content: ${newInvitationService.generateEmailBody(invitation, rfpData)}`)
          })
        }
        
        await loadInvitations()
        await loadInvitationStats()
        await loadRecentActivity()
      } else {
        console.error('❌ [DEBUG] Invitation generation failed:', response)
        showErrorToast("Failed to generate invitations", response.error || "Please check console for details.")
      }
    } catch (error) {
      console.error('❌ [DEBUG] Error creating invitations:', error)
      console.error('❌ [DEBUG] Error details:', error.response?.data || error.message)
      showErrorToast("Failed to create invitations", error.response?.data?.error || error.message || "Please check console for details.")
    }
  } catch (error) {
    console.error('❌ [DEBUG] Error in invitation process:', error)
    console.error('❌ [DEBUG] Error details:', error.response?.data || error.message)
    showErrorToast("Failed to process invitations", error.response?.data?.error || error.message || "Please check console for details.")
  } finally {
    loading.value = false
  }
}

// Generate Open RFP Invitation URL
const generateOpenRfpInvitation = async () => {
  try {
    openInvitationLoading.value = true
    console.log('🌐 [DEBUG] Generating open RFP invitation...')
    
    // Get RFP data from localStorage
    const selectedRFPData = localStorage.getItem('selectedRFP')
    if (!selectedRFPData) {
      showErrorToast("No RFP data found", "Please select an RFP first.")
      return
    }
    
    const rfpData = JSON.parse(selectedRFPData)
    const currentRfpId = rfpData.rfp_id || rfpId.value
    
    console.log('📋 [DEBUG] Generating open invitation for RFP ID:', currentRfpId)
    
    // Use the newInvitationService to generate open RFP invitation
    const response = await newInvitationService.generateOpenRfpInvitation(currentRfpId)
    
    console.log('✅ [DEBUG] Open RFP invitation response:', response)
    
    if (response.success && response.invitation) {
      openRfpUrl.value = response.invitation.invitation_url
      showToast("Open RFP URL Generated", "Public invitation URL has been created successfully.")
      
      // Refresh invitations list to include the open invitation
      await loadInvitations()
      await loadInvitationStats()
    } else {
      showErrorToast("Failed to generate open RFP URL", response.error || "Unknown error occurred.")
    }
    
  } catch (error) {
    console.error('❌ [DEBUG] Error generating open RFP invitation:', error)
    showErrorToast("Failed to generate open RFP URL", error.message || "Please try again.")
  } finally {
    openInvitationLoading.value = false
  }
}

const resendAllInvitations = async () => {
  try {
    loading.value = true
    const pendingInvitations = invitedVendors.value.filter(v => v.invitation_status === 'SENT')
    
    if (pendingInvitations.length === 0) {
      showToast("No pending invitations to resend")
      return
    }
    
    const invitationIds = pendingInvitations.map(v => v.invitation_id)
    
    // Get RFP data from localStorage
    const selectedRFPData = localStorage.getItem('selectedRFP')
    let rfpData = {
      rfp_title: "Sample RFP Title",
      rfp_number: "RFP-2024-001",
      deadline: "2025-02-15"
    }
    
    if (selectedRFPData) {
      try {
        const parsedRfpData = JSON.parse(selectedRFPData)
        rfpData = {
          rfp_title: parsedRfpData.rfp_title || rfpData.rfp_title,
          rfp_number: parsedRfpData.rfp_number || rfpData.rfp_number,
          deadline: parsedRfpData.deadline || rfpData.deadline
        }
      } catch (error) {
        console.error('❌ [DEBUG] Error parsing RFP data:', error)
      }
    }
    
    // Convert invitation IDs to invitation objects for resending
    const invitationObjects = pendingInvitations.map(inv => ({
      invitation_id: inv.invitation_id,
      vendor_email: inv.vendor_email || "contact@example.com",
      vendor_name: inv.vendor_name || "Vendor Contact", 
      invitation_url: inv.invitation_url || `https://rfp.company.com/invitation/${inv.invitation_id}`,
      company_name: inv.company_name || "Vendor Company"
    }))
    
    await vendorInvitationService.sendInvitations(rfpId.value, invitationObjects, rfpData)
    showToast("Invitations Resent", `Resent ${invitationIds.length} invitation(s).`)
    await loadInvitations()
  } catch (error) {
    console.error('Error resending invitations:', error)
    showErrorToast("Failed to resend invitations")
  } finally {
    loading.value = false
  }
}

const exportInvitations = async () => {
  try {
    const csvContent = generateInvitationsCSV(invitedVendors.value)
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rfp-invitations-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    showToast("Export Complete", "Invitation list exported successfully.")
  } catch (error) {
    console.error('Error exporting invitations:', error)
    showErrorToast("Failed to export invitations")
  }
}

const viewInvitationDetails = (vendor) => {
  // This would open a modal or navigate to a details page
  console.log('View invitation details for:', vendor)
  showToast("Feature Coming Soon", "Invitation details view will be available soon.")
}

// Success popup functions
const showInvitationSuccessPopup = (data) => {
  successPopupData.value = {
    totalSent: data.totalSent,
    totalFailed: data.totalFailed,
    failedEmails: data.failedEmails,
    invitations: data.invitations
  }
  showSuccessPopup.value = true
}

// Navigate to next step after successful invitation sending
const navigateAfterSuccess = () => {
  closeSuccessPopup()
  // Navigate to RFP details or dashboard
  // You can customize this route based on your application flow
  const selectedRFPData = localStorage.getItem('selectedRFP')
  if (selectedRFPData) {
    const rfpData = JSON.parse(selectedRFPData)
    router.push(`/rfps/${rfpData.rfp_id}`)
  } else {
    router.push('/rfps')
  }
}

const closeSuccessPopup = () => {
  showSuccessPopup.value = false
  // Reset data after closing
  setTimeout(() => {
    successPopupData.value = {
      totalSent: 0,
      totalFailed: 0,
      failedEmails: [],
      invitations: []
    }
  }, 300)
}

const viewInvitations = () => {
  closeSuccessPopup()
  // Switch to distribution tab to view invitations
  activeTab.value = 'distribution'
  showToast("Viewing Invitations", "Switched to Distribution Status tab")
}

const generateInvitationsCSV = (invitations) => {
  const headers = ['Vendor Name', 'Company', 'Email', 'Status', 'Unique Token', 'Invitation URL', 'Sent Date', 'Acknowledged Date']
  const rows = invitations.map(inv => [
    inv.vendor_name,
    inv.company_name,
    inv.vendor_email,
    inv.invitation_status,
    inv.unique_token,
    inv.invitation_url,
    inv.invited_date ? new Date(inv.invited_date).toLocaleDateString() : '',
    inv.acknowledged_date ? new Date(inv.acknowledged_date).toLocaleDateString() : ''
  ])
  
  return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
}

const loadRecentActivity = async () => {
  try {
    // This would load recent activity from the API
    // For now, we'll simulate some activity
    recentActivity.value = [
      {
        id: 1,
        description: "Invitation sent to ABC Corp",
        timestamp: new Date(Date.now() - 1000 * 60 * 30) // 30 minutes ago
      },
      {
        id: 2,
        description: "XYZ Ltd acknowledged invitation",
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2 hours ago
      }
    ]
  } catch (error) {
    console.error('Error loading recent activity:', error)
  }
}

const formatActivityTime = (timestamp) => {
  const now = new Date()
  const diff = now - new Date(timestamp)
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  return 'Just now'
}

// Function to create test data for debugging
const createTestVendorData = () => {
  const testData = {
    selectedVendors: {
      existing: [
        {
          vendor_id: 1,
          company_name: "Test Company 1",
          name: "John Doe",
          email: "john@testcompany1.com",
          phone: "+1-555-0001",
          vendor_type: "existing",
          is_matched_vendor: true
        }
      ],
      manual: [
        {
          id: "manual_1",
          company_name: "Manual Test Company",
          vendor_name: "Jane Smith",
          vendor_email: "jane@manualtest.com",
          vendor_phone: "+1-555-0002",
          vendor_type: "manual",
          is_matched_vendor: false
        }
      ],
      bulk: [],
      total: 2
    },
    selectedRFP: {
      rfp_id: 37,
      rfp_title: "Test RFP",
      rfp_number: "RFP-2024-TEST",
      deadline: "2025-02-15"
    }
  }
  
  localStorage.setItem('selectedVendors', JSON.stringify(testData.selectedVendors))
  localStorage.setItem('selectedRFP', JSON.stringify(testData.selectedRFP))
  
  console.log('🧪 [DEBUG] Created test vendor data:', testData)
  return testData
}

// Function to clear test data and navigate to Phase 3
const clearTestDataAndGoToPhase3 = () => {
  console.log('🧹 [DEBUG] Clearing test data and navigating to Phase 3...')
  
  // Clear the test data from localStorage
  localStorage.removeItem('selectedVendors')
  
  // Keep the RFP data as it's real
  const selectedRFPData = localStorage.getItem('selectedRFP')
  if (selectedRFPData) {
    const rfpData = JSON.parse(selectedRFPData)
    // Check if it's test RFP data
    if (rfpData.rfp_title === "Test RFP") {
      localStorage.removeItem('selectedRFP')
      console.log('🧹 [DEBUG] Also cleared test RFP data')
    }
  }
  
  showToast("Test Data Cleared", "Test data has been cleared. Please select real vendors in Phase 3.")
  
  // Navigate to Phase 3
  setTimeout(() => {
    router.push('/rfp-vendor-selection')
  }, 1000)
}


// Function to display selected vendors summary for debugging
const displaySelectedVendorsSummary = () => {
  try {
    const selectedVendorsData = localStorage.getItem('selectedVendors')
    const selectedRFPData = localStorage.getItem('selectedRFP')
    
    if (selectedVendorsData && selectedRFPData) {
      const allVendors = JSON.parse(selectedVendorsData)
      const rfpData = JSON.parse(selectedRFPData)
      
      console.log('📊 [DEBUG] Phase 4 - Selected Vendors Summary:')
      console.log('📋 [DEBUG] RFP Data:', rfpData)
      console.log('🏢 [DEBUG] Existing Vendors:', allVendors.existing?.length || 0, allVendors.existing)
      console.log('📝 [DEBUG] Manual Vendors:', allVendors.manual?.length || 0, allVendors.manual)
      console.log('📦 [DEBUG] Bulk Vendors:', allVendors.bulk?.length || 0, allVendors.bulk)
      console.log('📊 [DEBUG] Total Vendors:', allVendors.total || 0)
      
      // Check if this is test data by looking for test company names
      const isTestData = allVendors.existing?.some(v => v.company_name === "Test Company 1") || 
                        allVendors.manual?.some(v => v.company_name === "Manual Test Company")
      
      if (isTestData) {
        console.warn('⚠️ [DEBUG] WARNING: Test data detected! This should be replaced with real vendor selection data.')
        console.log('🔧 [DEBUG] To fix: Go back to Phase 3, select real vendors, and click "Generate URLs & Send Invitations"')
      } else {
        console.log('✅ [DEBUG] Real vendor data detected - proceeding with actual selections')
      }
      
      return {
        rfpData,
        allVendors,
        total: allVendors.total || 0,
        isTestData
      }
    } else {
      console.warn('⚠️ [DEBUG] No vendor or RFP data found in localStorage')
      console.log('🔧 [DEBUG] To fix: Go to Phase 3, select vendors, and click "Generate URLs & Send Invitations"')
      return null
    }
  } catch (error) {
    console.error('❌ [DEBUG] Error displaying vendor summary:', error)
    return null
  }
}

onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 4 - URL Generation')
  console.log('🚀 [DEBUG] Phase 4 component mounted, checking localStorage...')
  
  // Check all localStorage keys for debugging
  console.log('🔍 [DEBUG] All localStorage keys:', Object.keys(localStorage))
  
  // Set RFP ID from localStorage - check multiple possible keys
  const selectedRFPData = localStorage.getItem('selectedRFP') || 
                         localStorage.getItem('rfp_for_approval_workflow') ||
                         localStorage.getItem('rfp-app-rfp')
  const selectedVendorsData = localStorage.getItem('selectedVendors') ||
                             localStorage.getItem('rfp-app-vendor')
  
  console.log('📋 [DEBUG] Raw localStorage data on mount:')
  console.log('  - selectedRFP:', selectedRFPData)
  console.log('  - selectedVendors:', selectedVendorsData)
  
  if (selectedRFPData) {
    try {
      const rfpData = JSON.parse(selectedRFPData)
      rfpId.value = rfpData.rfp_id || rfpData.id || 37
      console.log('📋 [DEBUG] Set RFP ID from localStorage:', rfpId.value)
    } catch (error) {
      console.error('❌ [DEBUG] Error parsing RFP data:', error)
      rfpId.value = 37 // Fallback to test RFP ID
    }
  } else {
    console.warn('⚠️ [DEBUG] No RFP data in localStorage, using fallback')
    rfpId.value = 37 // Fallback to test RFP ID
  }
  
  // Display vendor summary for debugging
  displaySelectedVendorsSummary()
  
  loadInvitations()
  loadInvitationStats()
  loadRecentActivity()
})
</script>

<style scoped>
/* Container */
.phase-container {
  @apply space-y-6;
}

/* Back Button */
.back-button-container {
  @apply mb-4;
}

.back-button {
  @apply inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 border border-gray-200 hover:border-gray-300 shadow-sm hover:shadow-md;
}

.back-icon {
  @apply h-4 w-4;
}

.back-text {
  @apply font-medium;
}

/* Header Section */
.header-section {
  @apply bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl p-6 border border-blue-100;
}

.header-content {
  @apply flex items-center justify-between;
}

.header-text {
  @apply flex-1;
}

.page-title {
  @apply text-4xl font-bold tracking-tight text-gray-900 mb-2;
}

.title-icon {
  @apply mr-3 text-4xl;
}

.page-description {
  @apply text-gray-600 text-lg;
}

.phase-badge {
  @apply flex flex-col items-center justify-center bg-white rounded-xl px-6 py-4 shadow-lg border-2 border-blue-200;
}

.badge-number {
  @apply text-4xl font-bold text-blue-600;
}

.badge-text {
  @apply text-sm text-gray-500 font-medium;
}

/* Metrics Grid */
.metrics-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4;
}

.metric-card {
  @apply bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 p-6 relative overflow-hidden border border-gray-100;
}

.metric-card:hover {
  @apply transform -translate-y-1;
}

.metric-icon-wrapper {
  @apply w-12 h-12 rounded-xl flex items-center justify-center mb-4;
}

.metric-blue {
  @apply bg-gradient-to-br from-blue-500 to-blue-600;
}

.metric-green {
  @apply bg-gradient-to-br from-green-500 to-green-600;
}

.metric-yellow {
  @apply bg-gradient-to-br from-yellow-500 to-yellow-600;
}

.metric-purple {
  @apply bg-gradient-to-br from-purple-500 to-purple-600;
}

.metric-icon {
  @apply h-6 w-6 text-white;
}

.metric-content {
  @apply relative z-10;
}

.metric-label {
  @apply text-xs font-medium text-gray-500 uppercase tracking-wider mb-1;
}

.metric-value {
  @apply text-3xl font-bold text-gray-900;
}

.metric-decoration {
  @apply absolute -bottom-4 -right-4 w-24 h-24 rounded-full opacity-10;
}

/* Tabs Section */
.tabs-section {
  @apply space-y-6;
}

.tabs-container {
  @apply flex gap-2 border-b-2 border-gray-200;
}

.tab-button {
  @apply relative px-6 py-4 font-medium text-sm transition-all duration-200;
}

.tab-active {
  @apply text-blue-600 border-b-4 border-blue-600;
}

.tab-inactive {
  @apply text-gray-500 hover:text-gray-700 hover:border-gray-300;
}

.tab-indicator {
  @apply absolute bottom-0 left-0 right-0 h-1 bg-blue-600 rounded-t-full;
}

/* Content Card */
.content-card {
  @apply bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden;
}

.card-header {
  @apply bg-gradient-to-r from-gray-50 to-white px-6 py-5 border-b border-gray-200;
}

.card-header-content {
  @apply flex items-center gap-4;
}

.card-icon-wrapper {
  @apply w-12 h-12 rounded-xl flex items-center justify-center;
}

.card-icon-blue {
  @apply bg-gradient-to-br from-blue-500 to-blue-600;
}

.card-icon {
  @apply h-6 w-6 text-white;
}

.card-title {
  @apply text-xl font-bold text-gray-900;
}

.card-subtitle {
  @apply text-sm text-gray-500 mt-1;
}

.card-body {
  @apply p-6 space-y-6;
}

/* Info Section */
.info-section {
  @apply space-y-4;
}

.info-header {
  @apply flex items-center gap-3;
}

.info-icon-wrapper {
  @apply w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center;
}

.info-icon {
  @apply h-5 w-5 text-blue-600;
}

.info-title {
  @apply text-lg font-semibold text-gray-900;
}

.info-box {
  @apply bg-gradient-to-br from-gray-50 to-white p-5 rounded-xl border border-gray-200 space-y-4;
}

.info-content {
  @apply space-y-3;
}

.info-label {
  @apply text-sm font-semibold text-gray-700 block;
}

.info-list {
  @apply space-y-2 ml-4;
}

.info-list li {
  @apply text-sm text-gray-700 flex items-start gap-2;
}

.list-bullet {
  @apply text-green-600 font-bold;
}

.info-footer {
  @apply pt-3 border-t border-gray-200;
}

.info-note {
  @apply text-xs text-gray-600 flex items-start gap-2;
}

.note-icon {
  @apply text-blue-500;
}

/* Form Elements */
.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block;
}

.label-text {
  @apply text-sm font-semibold text-gray-700 block;
}

.label-hint {
  @apply text-xs text-gray-500 block mt-1;
}

.form-textarea {
  @apply w-full px-4 py-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all;
}

.checkbox-group {
  @apply pt-2;
}

.checkbox-label {
  @apply flex items-center gap-3 cursor-pointer;
}

.checkbox-input {
  @apply sr-only;
}

.checkbox-custom {
  @apply w-5 h-5 border-2 border-gray-300 rounded-md flex items-center justify-center transition-all;
}

.checkbox-input:checked + .checkbox-custom {
  @apply bg-blue-600 border-blue-600;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  @apply text-white text-xs font-bold;
}

.checkbox-text {
  @apply text-sm text-gray-700;
}

/* Action Cards */
.action-card {
  @apply rounded-2xl p-6 shadow-lg border-2;
}

.action-primary {
  @apply bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200;
}

.action-success {
  @apply bg-gradient-to-br from-green-50 to-emerald-50 border-green-200;
}

.action-content {
  @apply flex items-start justify-between gap-6;
}

.action-text {
  @apply flex items-start gap-4 flex-1;
}

.action-icon-wrapper {
  @apply w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0;
}

.action-primary .action-icon-wrapper {
  @apply bg-gradient-to-br from-blue-500 to-blue-600;
}

.action-success .action-icon-wrapper {
  @apply bg-gradient-to-br from-green-500 to-green-600;
}

.action-icon {
  @apply h-6 w-6 text-white;
}

.action-title {
  @apply text-lg font-bold text-gray-900 mb-2;
}

.action-description {
  @apply text-sm text-gray-600 mb-3;
}

.action-hint {
  @apply text-xs text-gray-500 flex items-center gap-2;
}

.hint-icon {
  @apply text-green-600;
}

.action-status {
  @apply mt-3;
}

.status-message {
  @apply text-sm flex items-center gap-2;
}

.status-error {
  @apply text-red-600;
}

.status-warning {
  @apply text-orange-600;
}

.status-success {
  @apply text-green-600;
}

.status-icon {
  @apply text-lg;
}

.action-buttons {
  @apply flex gap-2 flex-shrink-0;
}

/* Buttons */
.btn-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg hover:shadow-xl transition-all;
}

.btn-secondary {
  @apply bg-white border-2 border-gray-300 text-gray-700 hover:bg-gray-50 transition-all;
}

.btn-success {
  @apply bg-white border-2 border-green-300 text-green-700 hover:bg-green-50 transition-all;
}

.btn-icon {
  @apply h-4 w-4 mr-2;
}

/* URL Display */
.url-display {
  @apply mt-6 p-5 bg-white rounded-xl border-2 border-green-200;
}

.url-header {
  @apply mb-3;
}

.url-label {
  @apply text-sm font-semibold text-gray-700;
}

.url-content {
  @apply flex items-center gap-3 mb-3;
}

.url-text {
  @apply flex-1 px-4 py-3 bg-gray-50 rounded-lg text-xs font-mono break-all border border-gray-200;
}

.btn-copy {
  @apply bg-green-50 border-green-300 text-green-700 hover:bg-green-100 transition-all;
}

.copy-icon {
  @apply h-4 w-4;
}

.url-badges {
  @apply flex gap-2;
}

.url-badge {
  @apply px-3 py-1 rounded-full text-xs font-medium;
}

.url-badge-active {
  @apply bg-green-100 text-green-800;
}

.url-badge-info {
  @apply bg-blue-100 text-blue-800;
}

/* Navigation Section */
.navigation-section {
  @apply flex justify-between items-center pt-8 pb-4;
}

.nav-button {
  @apply flex items-center gap-4 px-6 py-4 rounded-xl font-medium transition-all shadow-md hover:shadow-xl;
}

.nav-button-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white;
}

.nav-button-secondary {
  @apply bg-white border-2 border-gray-300 text-gray-700 hover:bg-gray-50;
}

.nav-icon {
  @apply text-2xl;
}

.nav-text {
  @apply flex flex-col;
}

.nav-label {
  @apply text-sm text-gray-500;
}

.nav-desc {
  @apply text-base font-semibold;
}

/* Status Badges */
.status-badge.active {
  @apply bg-green-100 text-green-800 border-green-200 px-3 py-1 rounded-full text-sm font-medium;
}

.status-badge.evaluation {
  @apply bg-yellow-100 text-yellow-800 border-yellow-200;
}

.status-badge.draft {
  @apply bg-gray-100 text-gray-800 border-gray-200;
}

.status-badge.danger {
  @apply bg-red-100 text-red-800 border-red-200;
}

.status-badge.awarded {
  @apply bg-green-100 text-green-800 border-green-200;
}

/* Modal Dialog Styles */
.modal-overlay {
  @apply fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 p-4;
}

.modal-container {
  @apply bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col;
}

.modal-content {
  @apply flex flex-col h-full;
}

.modal-header {
  @apply bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-8 py-6 border-b border-blue-100 flex items-center justify-between;
}

.modal-header-content {
  @apply flex items-center gap-4 flex-1;
}

.modal-icon-wrapper {
  @apply w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg;
}

.modal-icon {
  @apply h-7 w-7 text-white;
}

.modal-title {
  @apply text-2xl font-bold text-gray-900 mb-1;
}

.modal-subtitle {
  @apply text-sm text-gray-600;
}

.modal-close-button {
  @apply w-10 h-10 rounded-lg bg-white border-2 border-gray-200 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50 transition-all shadow-sm;
}

.modal-close-icon {
  @apply h-5 w-5;
}

.modal-description {
  @apply px-8 py-4 bg-blue-50 border-b border-blue-100 flex items-start gap-3;
}

.description-icon {
  @apply text-2xl;
}

.description-text {
  @apply text-sm text-gray-700 leading-relaxed;
}

.modal-body {
  @apply flex-1 overflow-y-auto px-8 py-6 space-y-4;
}

/* Contact Cards */
.contact-card {
  @apply rounded-xl overflow-hidden border border-gray-200 shadow-sm hover:shadow-md transition-all;
}

.contact-error-card {
  @apply bg-gradient-to-br from-red-50 to-pink-50 border-2 border-red-200 p-5;
}

.error-content {
  @apply flex items-start gap-4;
}

.error-icon-wrapper {
  @apply w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center flex-shrink-0;
}

.error-icon {
  @apply h-6 w-6 text-white;
}

.error-text {
  @apply flex-1;
}

.error-title {
  @apply text-base font-semibold text-red-900 mb-1;
}

.error-message {
  @apply text-sm text-red-700;
}

.contact-success-card {
  @apply bg-white p-6;
}

.contact-header {
  @apply flex items-center gap-4 mb-6 pb-6 border-b border-gray-200;
}

.contact-avatar {
  @apply w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg;
}

.avatar-text {
  @apply text-2xl font-bold text-white;
}

.contact-info {
  @apply flex-1;
}

.contact-name {
  @apply text-xl font-bold text-gray-900 mb-2;
}

.contact-badge {
  @apply inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-100 text-green-800 text-xs font-semibold;
}

.badge-dot {
  @apply w-2 h-2 rounded-full bg-green-600;
}

.contact-details-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.detail-item {
  @apply flex items-start gap-4 p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-all border border-gray-100;
}

.detail-icon-wrapper {
  @apply w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0;
}

.detail-email {
  @apply bg-gradient-to-br from-blue-500 to-blue-600;
}

.detail-phone {
  @apply bg-gradient-to-br from-green-500 to-green-600;
}

.detail-designation {
  @apply bg-gradient-to-br from-purple-500 to-purple-600;
}

.detail-department {
  @apply bg-gradient-to-br from-orange-500 to-orange-600;
}

.detail-icon {
  @apply h-5 w-5 text-white;
}

.detail-content {
  @apply flex-1 min-w-0;
}

.detail-label {
  @apply block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1;
}

.detail-value {
  @apply text-sm text-gray-900 font-medium break-words;
}

.detail-email-value {
  @apply font-mono text-blue-700;
}

.modal-footer {
  @apply px-8 py-6 bg-gray-50 border-t border-gray-200 flex items-center justify-end gap-3;
}

.modal-button {
  @apply px-6 py-3 rounded-lg font-semibold transition-all shadow-sm hover:shadow-md;
}

.modal-button-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white;
}

.modal-button-secondary {
  @apply bg-white border-2 border-gray-300 text-gray-700 hover:bg-gray-50;
}

.button-icon {
  @apply h-4 w-4 inline-block mr-2;
}

/* Success Popup Styles */
.success-modal-container {
  @apply bg-white rounded-3xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-scale-in;
}

.success-modal-content {
  @apply flex flex-col h-full;
}

.success-animation {
  @apply flex justify-center pt-8 pb-4;
}

.success-checkmark {
  @apply relative w-24 h-24;
}

.check-icon {
  @apply w-full h-full;
}

.checkmark-circle {
  @apply stroke-green-500;
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  fill: none;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark-check {
  @apply stroke-green-500;
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
}

@keyframes stroke {
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes scale-in {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.animate-scale-in {
  animation: scale-in 0.3s ease-out;
}

.success-content {
  @apply px-8 pb-8 flex-1 overflow-y-auto;
}

.success-title {
  @apply text-3xl font-bold text-center text-gray-900 mb-2;
}

.success-subtitle {
  @apply text-center text-gray-600 mb-6;
}

.success-stats {
  @apply grid grid-cols-2 gap-4 mb-6;
}

.stat-card {
  @apply p-4 rounded-xl border-2 flex items-center gap-4;
}

.stat-success {
  @apply bg-green-50 border-green-200;
}

.stat-warning {
  @apply bg-orange-50 border-orange-200;
}

.stat-icon-wrapper {
  @apply w-12 h-12 rounded-lg flex items-center justify-center;
}

.stat-success .stat-icon-wrapper {
  @apply bg-green-500;
}

.stat-warning .stat-icon-wrapper {
  @apply bg-orange-500;
}

.stat-icon {
  @apply h-6 w-6 text-white;
}

.stat-content {
  @apply flex-1;
}

.stat-value {
  @apply text-2xl font-bold text-gray-900;
}

.stat-label {
  @apply text-xs text-gray-600 uppercase tracking-wider;
}

.success-vendors {
  @apply mb-6;
}

.vendors-title {
  @apply text-lg font-semibold text-gray-900 mb-3;
}

.vendors-list {
  @apply space-y-2 max-h-64 overflow-y-auto;
}

.vendor-item {
  @apply flex items-center gap-3 p-3 rounded-lg bg-gray-50 border border-gray-200;
}

.vendor-avatar-small {
  @apply w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0;
}

.vendor-initial {
  @apply text-white font-bold text-sm;
}

.vendor-details {
  @apply flex-1 min-w-0;
}

.vendor-name {
  @apply text-sm font-semibold text-gray-900 truncate;
}

.vendor-email {
  @apply text-xs text-gray-600 truncate;
}

.vendor-status {
  @apply flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold;
}

.vendor-status.success {
  @apply bg-green-100 text-green-800;
}

.status-icon {
  @apply h-3 w-3;
}

.failed-emails-section {
  @apply mb-6 p-4 rounded-xl bg-red-50 border border-red-200;
}

.failed-title {
  @apply text-base font-semibold text-red-900 mb-3;
}

.failed-list {
  @apply space-y-2;
}

.failed-item {
  @apply flex items-start gap-3 p-3 rounded-lg bg-white border border-red-200;
}

.failed-icon-wrapper {
  @apply w-8 h-8 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0;
}

.failed-icon {
  @apply h-4 w-4 text-white;
}

.failed-details {
  @apply flex-1 min-w-0;
}

.failed-email {
  @apply text-sm font-semibold text-gray-900;
}

.failed-reason {
  @apply text-xs text-red-700;
}

.success-actions {
  @apply flex gap-3 pt-4 border-t border-gray-200;
}

.success-button {
  @apply flex-1 px-6 py-3 rounded-lg font-semibold transition-all shadow-sm hover:shadow-md;
}

.success-button-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white;
}

.success-button-secondary {
  @apply bg-white border-2 border-gray-300 text-gray-700 hover:bg-gray-50;
}

/* Loading & Empty States */
.loading-state {
  @apply flex flex-col items-center justify-center py-12;
}

.loading-spinner {
  @apply mb-4;
}

.spinner-icon {
  @apply h-10 w-10 animate-spin text-blue-600;
}

.loading-text {
  @apply text-gray-600 font-medium;
}

.empty-state {
  @apply py-12;
}

.empty-state-content {
  @apply flex flex-col items-center space-y-6;
}

.empty-icon-wrapper {
  @apply w-20 h-20 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center;
}

.empty-icon {
  @apply h-10 w-10 text-blue-600;
}

.empty-text {
  @apply text-center space-y-2;
}

.empty-title {
  @apply text-xl font-semibold text-gray-900;
}

.empty-description {
  @apply text-gray-600;
}

.empty-action-button {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg hover:shadow-xl transition-all;
}

/* Distribution Content */
.distribution-content {
  @apply space-y-4;
}

/* Bulk Actions Bar */
.bulk-actions-bar {
  @apply flex items-center justify-between bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 p-5 rounded-xl border-2 border-blue-200 shadow-md;
}

.bulk-actions-left {
  @apply flex items-center gap-4;
}

.bulk-actions-label {
  @apply text-sm font-bold text-gray-800 uppercase tracking-wide;
}

.bulk-action-button {
  @apply bg-white border-2 border-gray-600 text-gray-900 hover:bg-gradient-to-r hover:from-blue-600 hover:to-blue-700 hover:border-blue-700 hover:text-white transition-all duration-200 shadow-lg hover:shadow-2xl;
  @apply font-bold px-6 py-2.5;
  @apply flex items-center gap-2;
}

.bulk-action-button:hover {
  transform: translateY(-1px);
}

.action-button-icon {
  @apply h-5 w-5;
}

.bulk-actions-count {
  @apply flex items-center gap-3;
}

.count-badge {
  @apply px-4 py-2 rounded-full text-sm font-bold bg-white text-gray-800 border-2 border-gray-300 shadow-sm;
}

.count-badge-success {
  @apply bg-gradient-to-r from-green-100 to-green-200 text-green-900 border-green-400;
}

/* Invitations Table */
.invitations-table-wrapper {
  @apply overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm;
  max-height: 600px;
}

.invitations-table {
  @apply w-full;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

.table-header-sticky {
  position: sticky;
  top: 0;
  z-index: 10;
}

.table-header-row {
  @apply bg-gradient-to-r from-gray-800 to-gray-900;
}

.table-header-cell {
  @apply py-5 px-5 text-xs font-extrabold text-white uppercase tracking-widest;
  text-align: left !important;
  vertical-align: middle;
  @apply shadow-sm border-r border-gray-700;
  position: relative;
}

.table-header-cell:last-child {
  border-right: none;
}

.header-content {
  @apply flex items-center justify-start;
}

.header-label {
  @apply block;
}

.table-body {
  @apply bg-white;
}

.table-row {
  @apply border-b border-gray-200 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200;
  @apply hover:shadow-sm;
}

.table-cell {
  @apply py-5 px-5;
  text-align: left !important;
  vertical-align: top;
  border-right: 1px solid #e5e7eb;
}

.table-cell:last-child {
  border-right: none;
}

/* Column Widths - Fixed widths for consistent alignment */
.table-col-vendor {
  width: 28%;
  min-width: 250px;
}

.table-col-url {
  width: 22%;
  min-width: 200px;
}

.table-col-status {
  width: 15%;
  min-width: 140px;
}

.table-col-timeline {
  width: 20%;
  min-width: 180px;
}

.table-col-actions {
  width: 15%;
  min-width: 140px;
}

/* Ensure all content is left-aligned */
.table-col-vendor,
.table-col-url,
.table-col-status,
.table-col-timeline,
.table-col-actions {
  text-align: left !important;
}

/* Prevent content overflow */
.table-cell {
  overflow: hidden;
  word-wrap: break-word;
}

/* Vendor Cell */
.vendor-cell {
  @apply space-y-2;
}

.vendor-cell-header {
  @apply flex items-center gap-2 flex-wrap;
}

.vendor-name {
  @apply font-bold text-gray-900 text-sm leading-tight;
}

.vendor-badge {
  @apply text-xs inline-flex items-center gap-1.5 flex-shrink-0;
}

.vendor-badge-public {
  @apply bg-gradient-to-br from-blue-100 to-blue-200 text-blue-900 border-2 border-blue-400 px-3 py-1.5 rounded-full shadow-md font-bold;
}

.vendor-company {
  @apply text-sm text-gray-700 font-semibold leading-tight;
}

.vendor-email {
  @apply text-xs text-gray-600 break-all leading-tight font-medium;
}

.badge-icon {
  @apply h-3.5 w-3.5 flex-shrink-0;
}

/* URL Cell */
.url-cell {
  @apply space-y-2;
}

.url-cell-header {
  @apply flex items-center gap-2 flex-wrap;
}

.url-token {
  @apply text-xs bg-gradient-to-br from-gray-50 to-gray-100 px-3 py-2 rounded-lg font-mono break-all border-2 border-gray-300 shadow-sm;
  @apply font-semibold text-gray-800;
}

.url-badge {
  @apply text-xs px-3 py-1.5 rounded-full font-semibold inline-flex items-center flex-shrink-0 shadow-md;
  border: 1px solid;
}

.url-badge-generated {
  @apply bg-green-100 text-green-800 border-green-400;
}

.url-badge-pending {
  @apply bg-yellow-100 text-yellow-800 border-yellow-400;
}

.url-note {
  @apply text-xs text-gray-600 leading-tight font-medium;
}

/* Status Badge Cell */
.status-badge-cell {
  @apply inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full font-semibold text-xs shadow-md;
  white-space: nowrap;
  display: inline-flex;
  text-align: left;
  border: 1px solid;
  justify-content: flex-start;
}

/* Timeline Cell */
.timeline-cell {
  @apply space-y-2;
}

.timeline-item {
  @apply flex items-start gap-2.5 text-xs;
  line-height: 1.5;
  @apply px-2 py-1 rounded-md;
}

.timeline-sent {
  @apply text-gray-800 font-semibold bg-gray-50;
}

.timeline-acknowledged {
  @apply text-green-800 font-bold bg-green-50;
}

.timeline-declined {
  @apply text-red-800 font-bold bg-red-50;
}

.timeline-icon {
  @apply h-4 w-4 flex-shrink-0 mt-0.5;
}

/* Action Cell */
.action-cell {
  @apply flex items-center gap-2;
  text-align: left;
  justify-content: flex-start;
}

.action-icon-button {
  @apply bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-500 text-blue-700 hover:from-blue-600 hover:to-blue-700 hover:border-blue-700 hover:text-white transition-all duration-200 shadow-lg hover:shadow-2xl;
  @apply flex items-center justify-center;
  @apply rounded-lg;
  width: 42px;
  height: 42px;
  padding: 0;
  min-width: 42px;
  flex-shrink: 0;
}

.action-icon-button:disabled {
  @apply opacity-40 cursor-not-allowed hover:from-blue-50 hover:to-blue-100 hover:border-blue-500 hover:text-blue-700;
}

.action-icon {
  @apply h-5 w-5;
  display: inline-block;
}

/* Analytics Content */
.analytics-content {
  @apply space-y-6;
}

/* Analytics Metrics Grid */
.analytics-metrics-grid {
  @apply grid grid-cols-1 md:grid-cols-5 gap-4;
}

.analytics-metric-card {
  @apply p-5 rounded-xl border-2 relative overflow-hidden hover:shadow-lg transition-all;
}

.metric-total {
  @apply bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200;
}

.metric-open {
  @apply bg-gradient-to-br from-green-50 to-green-100 border-green-200;
}

.metric-acknowledged {
  @apply bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200;
}

.metric-pending {
  @apply bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200;
}

.metric-rate {
  @apply bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200;
}

.metric-icon-container {
  @apply w-12 h-12 rounded-xl flex items-center justify-center mb-3;
}

.metric-total .metric-icon-container {
  @apply bg-gradient-to-br from-blue-500 to-blue-600;
}

.metric-open .metric-icon-container {
  @apply bg-gradient-to-br from-green-500 to-green-600;
}

.metric-acknowledged .metric-icon-container {
  @apply bg-gradient-to-br from-emerald-500 to-emerald-600;
}

.metric-pending .metric-icon-container {
  @apply bg-gradient-to-br from-yellow-500 to-yellow-600;
}

.metric-rate .metric-icon-container {
  @apply bg-gradient-to-br from-purple-500 to-purple-600;
}

.metric-icon-large {
  @apply h-6 w-6 text-white;
}

.metric-info {
  @apply relative z-10;
}

.metric-label {
  @apply text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1;
}

.metric-number {
  @apply text-2xl font-bold text-gray-900;
}

.metric-decoration {
  @apply absolute -bottom-4 -right-4 w-20 h-20 rounded-full opacity-10;
}

/* Analytics Details Grid */
.analytics-details-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-6;
}

.analytics-detail-card {
  @apply bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden;
}

.detail-card-header {
  @apply flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-200;
}

.detail-card-icon {
  @apply w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center;
}

.detail-icon {
  @apply h-5 w-5 text-blue-600;
}

.detail-card-title {
  @apply text-base font-semibold text-gray-900;
}

.detail-card-body {
  @apply p-6;
}

/* Status Breakdown */
.status-breakdown-item {
  @apply flex justify-between items-center py-3 border-b border-gray-100 last:border-0;
}

.status-breakdown-left {
  @apply flex items-center gap-3;
}

.status-dot {
  @apply w-3 h-3 rounded-full;
}

.status-name {
  @apply text-sm text-gray-700;
}

.status-count {
  @apply font-semibold text-gray-900;
}

/* Activity List */
.activity-empty {
  @apply text-center py-8;
}

.activity-empty-text {
  @apply text-sm text-gray-500;
}

.activity-list {
  @apply space-y-3;
}

.activity-item {
  @apply flex items-start gap-3;
}

.activity-dot {
  @apply w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0;
}

.activity-content {
  @apply flex-1;
}

.activity-description {
  @apply text-sm text-gray-900;
}

.activity-time {
  @apply text-xs text-gray-500 mt-1;
}

/* URL Performance */
.analytics-url-performance {
  @apply col-span-full;
}

.url-performance-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-6 p-6;
}

.url-performance-item {
  @apply text-center p-6 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200;
}

.url-performance-number {
  @apply text-4xl font-bold text-gray-900 mb-2;
}

.url-performance-label {
  @apply text-sm text-gray-600 font-medium;
}

/* Card Icon Colors */
.card-icon-purple {
  @apply bg-gradient-to-br from-purple-500 to-purple-600;
}

.card-icon-green {
  @apply bg-gradient-to-br from-green-500 to-green-600;
}

/* Ensure proper card spacing and alignment */
.space-y-6 > * + * {
  margin-top: 1.5rem;
}

/* Prevent overlapping issues */
.phase-card {
  position: relative;
  z-index: 1;
}

/* Ensure proper spacing between cards */
.space-y-6 {
  position: relative;
}

/* Card content spacing */
.rfp-card-content {
  @apply p-4;
}

/* Ensure consistent input field styling */
code {
  @apply font-mono text-sm;
}

/* Fix input field layout to prevent overlapping */
input[type="text"] {
  min-width: 0;
  flex: 1;
}

/* Ensure proper flex layout */
.flex {
  display: flex;
}

.flex-1 {
  flex: 1 1 0%;
}

/* Prevent button overlapping */
.rfp-button {
  flex-shrink: 0;
}

/* Ensure proper spacing in grid layouts */
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .md\\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.gap-6 {
  gap: 1.5rem;
}

/* Ensure proper spacing between sections */
.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-y-3 > * + * {
  margin-top: 0.75rem;
}

.space-y-2 > * + * {
  margin-top: 0.5rem;
}

/* Reset any potential margin/padding conflicts */
* {
  box-sizing: border-box;
}

/* Ensure proper container spacing */
.max-w-7xl {
  max-width: 80rem;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.py-6 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

@media (min-width: 640px) {
  .sm\\:px-6 {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
}

@media (min-width: 1024px) {
  .lg\\:px-8 {
    padding-left: 2rem;
    padding-right: 2rem;
  }
}
</style>
