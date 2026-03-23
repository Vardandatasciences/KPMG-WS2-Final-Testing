<template>
  <div class="questionnaire-assignment">
    <!-- Header -->
    <div class="assignment-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">Questionnaire Assignment</h1>
          <p class="page-subtitle">Assign questionnaires to vendors for completion</p>
        </div>
        <div class="header-actions">
          <button @click="openQSchedModal" class="btn-schedule-assignment">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
            Schedule Assignment
          </button>
          <button @click="openAssignmentModal" class="btn-primary">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            New Assignment
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="assignment-content">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <span class="stat-label">Total Assignments</span>
          </div>
          <div class="stat-value">{{ Array.isArray(assignments) ? assignments.length : 0 }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon pending" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <span class="stat-label">Pending</span>
          </div>
          <div class="stat-value">{{ getStatusCount('ASSIGNED') }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon progress" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <span class="stat-label">In Progress</span>
          </div>
          <div class="stat-value">{{ getStatusCount('IN_PROGRESS') }}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon completed" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <span class="stat-label">Completed</span>
          </div>
          <div class="stat-value">{{ getStatusCount('SUBMITTED') + getStatusCount('RESPONDED') + getStatusCount('COMPLETED') }}</div>
        </div>
      </div>

      <!-- Filters -->
      <div class="filters-row">
        <div class="filter-group">
          <label class="filter-label">Status</label>
          <select v-model="filters.status" class="filter-select">
            <option value="">All Statuses</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="SUBMITTED">Responded</option>
            <option value="RESPONDED">Responded</option>
            <option value="COMPLETED">Completed</option>
            <option value="OVERDUE">Overdue</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label class="filter-label">Questionnaire</label>
          <select v-model="filters.questionnaire" class="filter-select">
            <option value="">All Questionnaires</option>
            <option v-for="q in questionnaires" :key="q.questionnaire_id" :value="q.questionnaire_id">
              {{ q.questionnaire_name }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label class="filter-label">Search</label>
          <input 
            v-model="filters.search" 
            type="text" 
            placeholder="Search vendors..." 
            class="filter-input"
          />
        </div>
      </div>

      <!-- Assignments Table -->
      <div class="assignments-table-section">
        <div class="table-container">
          <table class="assignments-table">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Questionnaire</th>
                <th>Status</th>
                <th>Assigned Date</th>
                <th>Due Date</th>
                <th>Progress</th>
                <th class="actions-header">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="assignment in filteredAssignments" :key="assignment.assignment_id" class="assignment-row">
                <td>
                  <div class="vendor-info">
                    <div class="vendor-name">{{ assignment.vendor_name }}</div>
                  </div>
                </td>
                <td>
                  <div class="questionnaire-info">
                    <div class="questionnaire-name">{{ assignment.questionnaire_name }}</div>
                  </div>
                </td>
                <td>
                  <span :class="['status-badge', assignment.status.toLowerCase()]">
                    {{ formatStatus(assignment.status) }}
                  </span>
                </td>
                <td>{{ formatDate(assignment.assigned_date) }}</td>
                <td>{{ formatDate(assignment.due_date) || 'No due date' }}</td>
                <td>
                  <div class="progress-cell">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: `${getProgressPercentage(assignment)}%` }"></div>
                    </div>
                  </div>
                </td>
                <td class="assignment-actions-cell">
                  <button
                    class="btn-secondary"
                    type="button"
                    @click="viewResponses(assignment)"
                  >
                    View Responses
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="filteredAssignments.length === 0" class="empty-state">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <h3>No assignments found</h3>
            <p>No questionnaire assignments match your current filters.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Modal -->
    <div v-if="showAssignmentModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <!-- Close Button in Corner -->
        <button @click="closeModal" class="btn-close-corner">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
        
        <div class="modal-header">
          <h2>Create New Assignment</h2>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="createAssignment" class="form-grid">
            <div class="form-group form-group-full-width">
              <label class="form-label">Select Questionnaire</label>
              <select v-model="newAssignment.questionnaire_id" class="form-select" required>
                <option value="">Choose a questionnaire...</option>
                <option v-for="q in questionnaires" :key="q.questionnaire_id" :value="q.questionnaire_id">
                  {{ q.questionnaire_name }} ({{ q.question_count }} questions)
                </option>
              </select>
            </div>
            
            <div class="form-group form-group-full-width">
              <label class="form-label">Select Vendor</label>
              <select v-model="newAssignment.vendor_id" class="form-select" required>
                <option value="">Choose a vendor...</option>
                <option v-for="vendor in vendors" :key="vendor.id" :value="vendor.id">
                  {{ vendor.company_name }} ({{ vendor.vendor_category || 'No category' }})
                </option>
              </select>
            </div>
            
            <div class="form-group compact">
              <label class="form-label">Due Date (Optional)</label>
              <div class="date-input">
                <input 
                  v-model="newAssignment.due_date" 
                  type="date" 
                  class="form-input date-input-field"
                />
                <CalendarIcon class="date-input-icon" />
              </div>
            </div>
            
            <div class="form-group span-2">
              <label class="form-label">Notes (Optional)</label>
              <textarea 
                v-model="newAssignment.notes" 
                class="form-textarea" 
                rows="3"
                placeholder="Add any additional notes for this assignment..."
              ></textarea>
            </div>

            <!-- Schedule assignment (like AI Audit) -->
            <div class="form-group span-2 schedule-toggle-row">
              <button
                type="button"
                class="schedule-toggle-btn"
                @click="showScheduleSection = !showScheduleSection"
              >
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
                {{ showScheduleSection ? 'Hide Schedule' : 'Schedule Assignment' }}
              </button>
            </div>

            <div v-if="showScheduleSection" class="schedule-section">
              <h4 class="schedule-heading">Schedule questionnaire assignment</h4>
              <p class="schedule-hint">Assignments and emails will be sent at the chosen time. Recurring schedules create a new assignment each run.</p>

              <div class="schedule-block schedule-block-main">
                <div class="schedule-row">
                  <div class="schedule-field schedule-field-freq">
                    <label class="schedule-label">Frequency</label>
                    <select v-model="scheduleSimpleFreq" class="schedule-input" @change="applySimpleCron">
                      <option value="daily">Daily</option>
                      <option value="weekdays">Weekdays</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="quarterly">Quarterly</option>
                      <option value="yearly">Yearly</option>
                      <option value="does_not_repeat">One-time</option>
                    </select>
                  </div>
                  <template v-if="scheduleSimpleFreq === 'does_not_repeat'">
                    <div class="schedule-field">
                      <label class="schedule-label">Date</label>
                      <input type="date" v-model="scheduleDoesNotRepeatDate" class="schedule-input" :min="scheduleStartDateMin" />
                    </div>
                    <div class="schedule-field">
                      <label class="schedule-label">Time</label>
                      <input type="time" v-model="scheduleDoesNotRepeatTime" class="schedule-input" />
                    </div>
                  </template>
                  <template v-else>
                    <div class="schedule-field">
                      <label class="schedule-label">Time</label>
                      <input type="time" v-model="scheduleSimpleTime" class="schedule-input" @change="applySimpleCron" />
                    </div>
                  </template>
                </div>
                <div class="schedule-row schedule-row-start">
                  <div class="schedule-field schedule-field-start">
                    <label class="schedule-label">Start date <span class="schedule-optional">(optional)</span></label>
                    <input type="date" v-model="scheduleStartDate" class="schedule-input" :min="scheduleStartDateMin" title="First run on or after this date" />
                    <span class="schedule-hint-inline">Leave empty to start immediately.</span>
                  </div>
                </div>
              </div>

              <div v-if="scheduleSimpleFreq === 'weekly' || ['monthly','quarterly','yearly'].includes(scheduleSimpleFreq)" class="schedule-block schedule-block-extra">
                <span class="schedule-subheading">Recurrence options</span>
                <div class="schedule-row schedule-row-extra">
                  <div v-if="scheduleSimpleFreq === 'weekly'" class="schedule-field">
                    <label class="schedule-label">Day of week</label>
                    <select v-model="scheduleSimpleDayOfWeek" class="schedule-input" @change="applySimpleCron">
                      <option :value="0">Monday</option>
                      <option :value="1">Tuesday</option>
                      <option :value="2">Wednesday</option>
                      <option :value="3">Thursday</option>
                      <option :value="4">Friday</option>
                      <option :value="5">Saturday</option>
                      <option :value="6">Sunday</option>
                    </select>
                  </div>
                  <div v-if="['monthly','quarterly','yearly'].includes(scheduleSimpleFreq)" class="schedule-field">
                    <label class="schedule-label">Day of month (1–28)</label>
                    <input type="number" v-model.number="scheduleSimpleDayOfMonth" min="1" max="28" class="schedule-input schedule-day-input" @change="applySimpleCron" />
                  </div>
                  <div v-if="scheduleSimpleFreq === 'yearly'" class="schedule-field">
                    <label class="schedule-label">Month</label>
                    <select v-model="scheduleSimpleMonth" class="schedule-input" @change="applySimpleCron">
                      <option :value="1">January</option>
                      <option :value="2">February</option>
                      <option :value="3">March</option>
                      <option :value="4">April</option>
                      <option :value="5">May</option>
                      <option :value="6">June</option>
                      <option :value="7">July</option>
                      <option :value="8">August</option>
                      <option :value="9">September</option>
                      <option :value="10">October</option>
                      <option :value="11">November</option>
                      <option :value="12">December</option>
                    </select>
                  </div>
                </div>
              </div>

              <details class="schedule-advanced">
                <summary>Advanced: custom cron expression</summary>
                <input type="text" v-model="scheduleCronExpression" class="schedule-input schedule-cron-input" placeholder="e.g. 0 9 * * 1-5 (minute hour day month weekday)" />
              </details>
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="btn-secondary">Cancel</button>
          <button @click="createAssignment" class="btn-primary" :disabled="!canCreateAssignment">
            Create Assignment
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Schedule Assignment Modal (standalone, like External Screening) -->
  <div v-if="showQSchedModal" class="qsched-modal-overlay" @click.self="closeQSchedModal">
    <div class="qsched-modal-content">
      <button type="button" class="qsched-modal-close" @click="closeQSchedModal" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
      <div class="qsched-modal-header">
        <svg class="qsched-header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        </svg>
        <h2>Schedule Questionnaire Assignment</h2>
      </div>
      <div class="qsched-modal-body">
        <p class="qsched-modal-hint">Assign a questionnaire to a vendor at the chosen time. Recurring schedules create a new assignment each run and automatically send the vendor email.</p>

        <!-- Vendor -->
        <div class="qsched-form-group qsched-form-group-full">
          <label class="qsched-form-label">Select Vendor</label>
          <select v-model="qSchedForm.vendor_id" class="qsched-form-select" required @change="onQSchedVendorChange">
            <option value="">Choose a vendor...</option>
            <option v-for="v in vendors" :key="v.id" :value="v.id">
              {{ v.company_name }} ({{ v.vendor_code || 'No Code' }})
            </option>
          </select>
        </div>

        <!-- Questionnaire -->
        <div class="qsched-form-group qsched-form-group-full">
          <label class="qsched-form-label">Select Questionnaire</label>
          <select v-model="qSchedForm.questionnaire_id" class="qsched-form-select" required @change="loadQSavedSchedules">
            <option value="">Choose a questionnaire...</option>
            <option v-for="q in questionnaires" :key="q.questionnaire_id" :value="q.questionnaire_id">
              {{ q.questionnaire_name }} ({{ q.question_count }} questions)
            </option>
          </select>
        </div>

        <!-- Frequency + Time -->
        <div class="qsched-form-row">
          <div class="qsched-form-field qsched-field-freq">
            <label class="qsched-form-label">Frequency</label>
            <select v-model="qSchedForm.frequency" class="qsched-form-select" @change="applyQSchedCron">
              <option value="daily">Daily</option>
              <option value="weekdays">Weekdays</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="yearly">Yearly</option>
              <option value="does_not_repeat">One-time</option>
            </select>
          </div>
          <template v-if="qSchedForm.frequency === 'does_not_repeat'">
            <div class="qsched-form-field">
              <label class="qsched-form-label">Date</label>
              <input type="date" v-model="qSchedForm.oneTimeDate" class="qsched-form-input" :min="qSchedStartDateMin" />
            </div>
            <div class="qsched-form-field">
              <label class="qsched-form-label">Time</label>
              <input type="time" v-model="qSchedForm.oneTimeTime" class="qsched-form-input" />
            </div>
          </template>
          <template v-else>
            <div class="qsched-form-field">
              <label class="qsched-form-label">Time</label>
              <input type="time" v-model="qSchedForm.time" class="qsched-form-input" @change="applyQSchedCron" />
            </div>
          </template>
        </div>

        <!-- Due date + Start date -->
        <div class="qsched-form-row qsched-form-row-dates">
          <div class="qsched-form-field">
            <label class="qsched-form-label">Due Date <span class="qsched-optional">(optional)</span></label>
            <input type="date" v-model="qSchedForm.dueDate" class="qsched-form-input" />
          </div>
          <div class="qsched-form-field">
            <label class="qsched-form-label">Start date <span class="qsched-optional">(optional)</span></label>
            <input type="date" v-model="qSchedForm.startDate" class="qsched-form-input" :min="qSchedStartDateMin" />
            <span class="qsched-hint-inline">Leave empty to start immediately.</span>
          </div>
        </div>

        <!-- Recurrence options -->
        <div v-if="qSchedForm.frequency === 'weekly' || ['monthly','quarterly','yearly'].includes(qSchedForm.frequency)" class="qsched-form-block-extra">
          <span class="qsched-subheading">Recurrence options</span>
          <div class="qsched-form-row qsched-form-row-extra">
            <div v-if="qSchedForm.frequency === 'weekly'" class="qsched-form-field">
              <label class="qsched-form-label">Day of week</label>
              <select v-model="qSchedForm.dayOfWeek" class="qsched-form-select" @change="applyQSchedCron">
                <option :value="0">Monday</option>
                <option :value="1">Tuesday</option>
                <option :value="2">Wednesday</option>
                <option :value="3">Thursday</option>
                <option :value="4">Friday</option>
                <option :value="5">Saturday</option>
                <option :value="6">Sunday</option>
              </select>
            </div>
            <div v-if="['monthly','quarterly','yearly'].includes(qSchedForm.frequency)" class="qsched-form-field">
              <label class="qsched-form-label">Day of month (1–28)</label>
              <input type="number" v-model.number="qSchedForm.dayOfMonth" min="1" max="28" class="qsched-form-input qsched-day-input" @change="applyQSchedCron" />
            </div>
            <div v-if="qSchedForm.frequency === 'yearly'" class="qsched-form-field">
              <label class="qsched-form-label">Month</label>
              <select v-model="qSchedForm.month" class="qsched-form-select" @change="applyQSchedCron">
                <option :value="1">January</option><option :value="2">February</option>
                <option :value="3">March</option><option :value="4">April</option>
                <option :value="5">May</option><option :value="6">June</option>
                <option :value="7">July</option><option :value="8">August</option>
                <option :value="9">September</option><option :value="10">October</option>
                <option :value="11">November</option><option :value="12">December</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="qsched-form-group qsched-form-group-full">
          <label class="qsched-form-label">Notes <span class="qsched-optional">(optional)</span></label>
          <textarea v-model="qSchedForm.notes" class="qsched-form-textarea" rows="2" placeholder="Add any notes for this schedule..."></textarea>
        </div>

        <!-- Advanced cron -->
        <details class="qsched-advanced">
          <summary>Advanced: custom cron expression</summary>
          <input type="text" v-model="qSchedForm.cronExpression" class="qsched-form-input qsched-cron-input" placeholder="e.g. 0 9 * * 1-5" />
        </details>

        <!-- Saved Schedules list -->
        <div class="qsched-saved-section">
          <div class="qsched-saved-header-row">
            <h3 class="qsched-saved-heading">Saved Schedules</h3>
            <span v-if="qSavedSchedules.length" class="qsched-saved-count">{{ qSavedSchedules.length }} schedule{{ qSavedSchedules.length > 1 ? 's' : '' }}</span>
          </div>
          <div v-if="qSchedLoading" class="qsched-saved-empty">
            <span class="qsched-spinner"></span> Loading schedules...
          </div>
          <div v-else-if="!qSchedForm.vendor_id || !qSchedForm.questionnaire_id" class="qsched-saved-empty">
            Select a vendor and questionnaire above to see saved schedules.
          </div>
          <div v-else-if="qSavedSchedules.length === 0" class="qsched-saved-empty">
            No schedules saved yet for this vendor / questionnaire.
          </div>
          <div v-else class="qsched-saved-cards">
            <div v-for="s in qSavedSchedules" :key="s.id" class="qsched-card">
              <div class="qsched-card-header">
                <div class="qsched-card-title-row">
                  <span class="qsched-freq-badge">{{ qSchedFreqLabel(s.cron_expression) }}</span>
                  <span v-if="s.next_run_at" class="qsched-time-label">Next: {{ qSchedFormatDate(s.next_run_at) }}</span>
                </div>
                <button type="button" class="qsched-btn-delete" @click="deleteQSchedule(s.id)" title="Remove schedule">✕</button>
              </div>
              <div class="qsched-card-body">
                <div class="qsched-info-row">
                  <span class="qsched-info-label">Questionnaire</span>
                  <span class="qsched-info-value">{{ s.questionnaire_name }}</span>
                </div>
                <div class="qsched-info-row">
                  <span class="qsched-info-label">Vendor</span>
                  <span class="qsched-info-value">{{ s.vendor_name }}</span>
                </div>
                <div v-if="s.cron_expression" class="qsched-info-row">
                  <span class="qsched-info-label">Cron</span>
                  <code class="qsched-cron-code">{{ s.cron_expression }}</code>
                </div>
                <div v-if="s.scheduled_at" class="qsched-info-row">
                  <span class="qsched-info-label">Scheduled at</span>
                  <span class="qsched-info-value">{{ qSchedFormatDate(s.scheduled_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="qsched-modal-footer">
        <button type="button" class="qsched-btn-cancel" @click="closeQSchedModal">Cancel</button>
        <button
          type="button"
          class="qsched-btn-submit"
          @click="submitQSchedule"
          :disabled="!qSchedForm.vendor_id || !qSchedForm.questionnaire_id || qSchedSubmitting"
        >
          {{ qSchedSubmitting ? 'Scheduling...' : 'Schedule Assignment' }}
        </button>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Calendar as CalendarIcon } from 'lucide-vue-next'
import { apiCall } from '@/utils/api'
import './QuestionnaireAssignment.css'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

// Router
const router = useRouter()

// Reactive data
const assignments = ref([])
const vendors = ref([])
const questionnaires = ref([])
const showAssignmentModal = ref(false)
const loading = ref(false)

// Filters
const filters = ref({
  status: '',
  questionnaire: '',
  search: ''
})

// New assignment form
const newAssignment = ref({
  questionnaire_id: '',
  vendor_id: '',
  due_date: '',
  notes: ''
})

// Schedule section (like AI Audit)
const showScheduleSection = ref(false)
const scheduleSimpleFreq = ref('daily')
const scheduleStartDate = ref('')
const scheduleDoesNotRepeatDate = ref('')
const scheduleDoesNotRepeatTime = ref('09:00')
const scheduleSimpleTime = ref('09:00')
const scheduleSimpleDayOfWeek = ref(1)
const scheduleSimpleDayOfMonth = ref(1)
const scheduleSimpleMonth = ref(1)
const scheduleCronExpression = ref('')

// Computed properties
const filteredAssignments = computed(() => {
  if (!Array.isArray(assignments.value)) {
    return []
  }

  let filtered = assignments.value

  if (filters.value.status) {
    filtered = filtered.filter(a => a.status === filters.value.status)
  }

  if (filters.value.questionnaire) {
    filtered = filtered.filter(a => a.questionnaire.toString() === filters.value.questionnaire.toString())
  }

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    filtered = filtered.filter(a => 
      a.vendor_name.toLowerCase().includes(search) ||
      a.questionnaire_name.toLowerCase().includes(search)
    )
  }

  return filtered
})

const canCreateAssignment = computed(() => {
  return newAssignment.value.questionnaire_id && newAssignment.value.vendor_id
})

const scheduleStartDateMin = computed(() => new Date().toISOString().slice(0, 10))

// Methods
const getStatusCount = (status) => {
  return Array.isArray(assignments.value) ? assignments.value.filter(a => a.status === status).length : 0
}

const formatStatus = (status) => {
  const statusMap = {
    'ASSIGNED': 'Assigned',
    'IN_PROGRESS': 'In Progress', 
    'SUBMITTED': 'Responded',
    'RESPONDED': 'Responded',
    'COMPLETED': 'Completed',
    'OVERDUE': 'Overdue'
  }
  return statusMap[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

const getProgressPercentage = (assignment) => {
  // This would need to be calculated based on actual responses
  // For now, return a simple calculation based on status
  switch (assignment.status) {
    case 'ASSIGNED': return 0
    case 'IN_PROGRESS': return 50
    case 'SUBMITTED': return 100
    case 'RESPONDED': return 100
    case 'COMPLETED': return 100
    default: return 0
  }
}

function applySimpleCron() {
  const f = scheduleSimpleFreq.value
  const [h, m] = (scheduleSimpleTime.value || '09:00').split(':').map(x => parseInt(x, 10) || 0)
  const minute = m
  const hour = h
  if (f === 'does_not_repeat') {
    scheduleCronExpression.value = ''
    return
  }
  if (f === 'daily') {
    scheduleCronExpression.value = `${minute} ${hour} * * *`
    return
  }
  if (f === 'weekdays') {
    scheduleCronExpression.value = `${minute} ${hour} * * 1-5`
    return
  }
  if (f === 'weekly') {
    const dow = scheduleSimpleDayOfWeek.value
    const cronDow = dow === 6 ? 0 : dow + 1
    scheduleCronExpression.value = `${minute} ${hour} * * ${cronDow}`
    return
  }
  if (f === 'monthly') {
    const dom = Math.max(1, Math.min(28, scheduleSimpleDayOfMonth.value || 1))
    scheduleCronExpression.value = `${minute} ${hour} ${dom} * *`
    return
  }
  if (f === 'quarterly') {
    const dom = Math.max(1, Math.min(28, scheduleSimpleDayOfMonth.value || 1))
    scheduleCronExpression.value = `${minute} ${hour} ${dom} 1,4,7,10 *`
    return
  }
  if (f === 'yearly') {
    const dom = Math.max(1, Math.min(28, scheduleSimpleDayOfMonth.value || 1))
    const month = Math.max(1, Math.min(12, scheduleSimpleMonth.value || 1))
    scheduleCronExpression.value = `${minute} ${hour} ${dom} ${month} *`
    return
  }
}

const viewResponses = (assignment) => {
  if (!assignment || !assignment.assignment_id) {
    console.warn('viewResponses called without a valid assignment:', assignment)
    return
  }

  router.push({
    path: '/vendor-questionnaire-review',
    query: {
      assignment_id: assignment.assignment_id
    }
  }).catch((err) => {
    // Ignore NavigationDuplicated and similar non-critical errors
    if (err && err.name !== 'NavigationDuplicated') {
      console.error('Error navigating to vendor questionnaire response page:', err)
    }
  })
}

const loadAssignments = async () => {
  try {
    loading.value = true
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/')
    // Ensure we always set an array, handle both paginated and direct array responses
    assignments.value = Array.isArray(response.data) ? response.data : (response.data.results || [])
  } catch (error) {
    console.error('Error loading assignments:', error)
    assignments.value = [] // Set empty array on error
  } finally {
    loading.value = false
  }
}

const loadVendors = async () => {
  try {
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/get_vendors/')
    vendors.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('Error loading vendors:', error)
    vendors.value = []
  }
}

const loadQuestionnaires = async () => {
  try {
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/get_active_questionnaires/')
    questionnaires.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('Error loading questionnaires:', error)
    // Fallback to load all questionnaires if no active ones
    try {
      const fallbackResponse = await apiCall('/api/v1/vendor-questionnaire/questionnaires/')
      const results = fallbackResponse.data.results || []
      questionnaires.value = results.map(q => ({
        questionnaire_id: q.questionnaire_id,
        questionnaire_name: q.questionnaire_name,
        questionnaire_type: q.questionnaire_type,
        description: q.description,
        question_count: q.question_count || 0
      }))
    } catch (fallbackError) {
      console.error('Error loading fallback questionnaires:', fallbackError)
      questionnaires.value = []
    }
  }
}

const refreshData = async () => {
  await Promise.all([
    loadAssignments(),
    loadVendors(),
    loadQuestionnaires()
  ])
}

const createAssignment = async () => {
  try {
    loading.value = true
    const isScheduled = showScheduleSection.value
    const assignmentData = {
      ...newAssignment.value,
      vendor_ids: [newAssignment.value.vendor_id]
    }
    delete assignmentData.vendor_id

    if (isScheduled) {
      applySimpleCron()
      const oneTime = scheduleSimpleFreq.value === 'does_not_repeat' && scheduleDoesNotRepeatDate.value && scheduleDoesNotRepeatTime.value
      const recurring = ['daily', 'weekdays', 'weekly', 'monthly', 'quarterly', 'yearly'].includes(scheduleSimpleFreq.value) && scheduleSimpleTime.value
      const cron = (scheduleCronExpression.value || '').trim()
      if (!oneTime && !recurring && !cron) {
        PopupService.warning('Please set schedule date/time or frequency and time.', 'Schedule required')
        loading.value = false
        return
      }
      let scheduled_at = null
      if (oneTime) {
        const datePart = scheduleDoesNotRepeatDate.value.slice(0, 10)
        const timePart = (scheduleDoesNotRepeatTime.value || '09:00').trim()
        const timeNorm = timePart.length === 5 ? timePart + ':00' : timePart.slice(0, 8)
        scheduled_at = `${datePart}T${timeNorm}`
      }
      assignmentData.schedule = {
        cron_expression: cron || null,
        start_date: scheduleStartDate.value || null,
        scheduled_at
      }
    }
    
    const response = await apiCall('/api/v1/vendor-questionnaire/assignments/assign_questionnaire/', {
      method: 'POST',
      data: assignmentData
    })
    
    if (response.data.scheduled_count > 0) {
      PopupService.success(
        `Schedule created. ${response.data.scheduled_count} assignment(s) will be created at the scheduled time.`,
        'Scheduled'
      )
    } else {
      let emailWarnings = []
      if (response.data.assignments) {
        response.data.assignments.forEach(assignment => {
          if (assignment.email_status && !assignment.email_status.success) {
            const vendorName = assignment.temp_vendor_name || 'Unknown Vendor'
            const errorMsg = assignment.email_status.error || 'Unknown error'
            emailWarnings.push(`${vendorName}: ${errorMsg}`)
          }
        })
      }
      if (response.data.errors && response.data.errors.length > 0) {
        PopupService.warning('Some assignments could not be created:\n' + response.data.errors.join('\n'), 'Partial Success')
      } else {
        let message = `Successfully created ${response.data.created_count} assignment(s)`
        if (emailWarnings.length > 0) {
          message += '\n\nEmail notifications could not be sent:\n' + emailWarnings.join('\n')
          PopupService.warning(message, 'Assignment Created (Email Issues)')
        } else {
          message += '\n\nEmail notifications sent successfully.'
          PopupService.success(message, 'Success')
        }
      }
    }
    
    closeModal()
    await loadAssignments()
  } catch (error) {
    console.error('Error creating assignment:', error)
    PopupService.error('Error creating assignment. Please try again.', 'Assignment Failed')
  } finally {
    loading.value = false
  }
}

const openAssignmentModal = () => {
  console.log('Opening assignment modal...')
  console.log('Questionnaires available:', questionnaires.value)
  console.log('Vendors available:', vendors.value)
  showAssignmentModal.value = true
}

const closeModal = () => {
  showAssignmentModal.value = false
  showScheduleSection.value = false
  newAssignment.value = {
    questionnaire_id: '',
    vendor_id: '',
    due_date: '',
    notes: ''
  }
  scheduleSimpleFreq.value = 'daily'
  scheduleStartDate.value = ''
  scheduleDoesNotRepeatDate.value = ''
  scheduleDoesNotRepeatTime.value = '09:00'
  scheduleSimpleTime.value = '09:00'
  scheduleSimpleDayOfWeek.value = 1
  scheduleSimpleDayOfMonth.value = 1
  scheduleSimpleMonth.value = 1
  scheduleCronExpression.value = ''
}

// ─── Schedule Assignment Modal (standalone) ───────────────────────────────
const showQSchedModal = ref(false)
const qSchedSubmitting = ref(false)
const qSchedLoading = ref(false)
const qSavedSchedules = ref([])

const qSchedForm = ref({
  vendor_id: '',
  questionnaire_id: '',
  frequency: 'daily',
  time: '09:00',
  oneTimeDate: '',
  oneTimeTime: '09:00',
  startDate: '',
  dueDate: '',
  dayOfWeek: 1,
  dayOfMonth: 1,
  month: 1,
  cronExpression: '',
  notes: '',
})

const qSchedStartDateMin = computed(() => new Date().toISOString().slice(0, 10))

const openQSchedModal = () => {
  showQSchedModal.value = true
  qSavedSchedules.value = []
}

const closeQSchedModal = () => {
  showQSchedModal.value = false
  qSavedSchedules.value = []
  qSchedForm.value = {
    vendor_id: '', questionnaire_id: '', frequency: 'daily',
    time: '09:00', oneTimeDate: '', oneTimeTime: '09:00',
    startDate: '', dueDate: '', dayOfWeek: 1, dayOfMonth: 1,
    month: 1, cronExpression: '', notes: '',
  }
}

const onQSchedVendorChange = () => {
  if (qSchedForm.value.vendor_id && qSchedForm.value.questionnaire_id) {
    loadQSavedSchedules()
  }
}

const applyQSchedCron = () => {
  const f = qSchedForm.value.frequency
  if (f === 'does_not_repeat') { qSchedForm.value.cronExpression = ''; return }
  const [h, m] = (qSchedForm.value.time || '09:00').split(':').map(x => parseInt(x, 10) || 0)
  if (f === 'daily')    { qSchedForm.value.cronExpression = `${m} ${h} * * *`;          return }
  if (f === 'weekdays') { qSchedForm.value.cronExpression = `${m} ${h} * * 1-5`;        return }
  if (f === 'weekly') {
    const dow = qSchedForm.value.dayOfWeek
    const cronDow = dow === 6 ? 0 : dow + 1
    qSchedForm.value.cronExpression = `${m} ${h} * * ${cronDow}`; return
  }
  if (f === 'monthly') {
    const dom = Math.max(1, Math.min(28, qSchedForm.value.dayOfMonth || 1))
    qSchedForm.value.cronExpression = `${m} ${h} ${dom} * *`; return
  }
  if (f === 'quarterly') {
    const dom = Math.max(1, Math.min(28, qSchedForm.value.dayOfMonth || 1))
    qSchedForm.value.cronExpression = `${m} ${h} ${dom} 1,4,7,10 *`; return
  }
  if (f === 'yearly') {
    const dom = Math.max(1, Math.min(28, qSchedForm.value.dayOfMonth || 1))
    const mo = Math.max(1, Math.min(12, qSchedForm.value.month || 1))
    qSchedForm.value.cronExpression = `${m} ${h} ${dom} ${mo} *`; return
  }
}

const loadQSavedSchedules = async () => {
  if (!qSchedForm.value.vendor_id || !qSchedForm.value.questionnaire_id) return
  qSchedLoading.value = true
  try {
    const resp = await apiCall(
      `/api/v1/vendor-questionnaire/assignments/list_schedules/?vendor_id=${qSchedForm.value.vendor_id}&questionnaire_id=${qSchedForm.value.questionnaire_id}`
    )
    qSavedSchedules.value = resp.data.schedules || []
  } catch (err) {
    console.warn('Could not load saved schedules:', err)
    qSavedSchedules.value = []
  } finally {
    qSchedLoading.value = false
  }
}

const deleteQSchedule = async (scheduleId) => {
  try {
    await apiCall(`/api/v1/vendor-questionnaire/assignments/delete_schedule/?id=${scheduleId}`, { method: 'DELETE' })
    qSavedSchedules.value = qSavedSchedules.value.filter(s => s.id !== scheduleId)
    PopupService.success('Schedule removed.', 'Schedule Assignment')
  } catch (err) {
    console.error('Delete schedule error:', err)
    PopupService.error('Failed to delete schedule.', 'Schedule Assignment')
  }
}

const submitQSchedule = async () => {
  if (!qSchedForm.value.vendor_id || !qSchedForm.value.questionnaire_id) {
    PopupService.warning('Please select both a vendor and a questionnaire.', 'Schedule Assignment')
    return
  }
  const freq = qSchedForm.value.frequency
  const oneTime = freq === 'does_not_repeat'
  if (oneTime && (!qSchedForm.value.oneTimeDate || !qSchedForm.value.oneTimeTime)) {
    PopupService.warning('Please set both date and time for a one-time schedule.', 'Schedule Assignment')
    return
  }
  if (!oneTime && !qSchedForm.value.time) {
    PopupService.warning('Please set a time for the recurring schedule.', 'Schedule Assignment')
    return
  }
  qSchedSubmitting.value = true
  try {
    applyQSchedCron()
    let scheduled_at = null
    if (oneTime) {
      scheduled_at = `${qSchedForm.value.oneTimeDate}T${qSchedForm.value.oneTimeTime}:00`
    }
    const payload = {
      questionnaire_id: qSchedForm.value.questionnaire_id,
      vendor_ids: [qSchedForm.value.vendor_id],
      due_date: qSchedForm.value.dueDate || null,
      notes: qSchedForm.value.notes || '',
      schedule: {
        cron_expression: oneTime ? null : (qSchedForm.value.cronExpression || null),
        start_date: qSchedForm.value.startDate || null,
        scheduled_at,
      },
    }
    const resp = await apiCall('/api/v1/vendor-questionnaire/assignments/assign_questionnaire/', {
      method: 'POST',
      data: payload,
    })
    if (resp.data.scheduled_count > 0) {
      const vendor = vendors.value.find(v => String(v.id) === String(qSchedForm.value.vendor_id))
      const q = questionnaires.value.find(q => String(q.questionnaire_id) === String(qSchedForm.value.questionnaire_id))
      PopupService.success(
        `Schedule saved for ${vendor?.company_name || 'vendor'} — ${q?.questionnaire_name || 'questionnaire'}.`,
        'Schedule Assignment'
      )
      // Reload saved list & reset form fields (keep vendor/questionnaire selected)
      await loadQSavedSchedules()
      qSchedForm.value.oneTimeDate = ''
      qSchedForm.value.oneTimeTime = '09:00'
      qSchedForm.value.startDate = ''
      qSchedForm.value.cronExpression = ''
      qSchedForm.value.notes = ''
    } else {
      PopupService.warning(resp.data?.errors?.[0] || 'Failed to save schedule.', 'Schedule Assignment')
    }
  } catch (err) {
    console.error('Schedule assignment error:', err)
    const msg = err.response?.data?.error || err.message || 'Failed to save schedule.'
    PopupService.error(msg, 'Schedule Assignment')
  } finally {
    qSchedSubmitting.value = false
  }
}

const qSchedFormatDate = (isoStr) => {
  if (!isoStr) return '—'
  try { return new Date(isoStr).toLocaleString() } catch { return isoStr }
}

const qSchedFreqLabel = (cronExpr) => {
  if (!cronExpr) return 'One-time'
  if (/\* \* 1-5$/.test(cronExpr)) return 'Weekdays'
  const parts = cronExpr.trim().split(/\s+/)
  if (parts.length === 5) {
    if (parts[2] === '*' && parts[3] === '*' && parts[4] === '*') return 'Daily'
    if (parts[2] === '*' && parts[3] === '*') return 'Weekly'
    if (parts[3] === '*') return 'Monthly'
    if (parts[3].includes(',')) return 'Quarterly'
    return 'Yearly'
  }
  return 'Custom'
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Vendor', 'Questionnaire Assignment')
  await refreshData()
})
</script>

<style scoped>
/* Main Container */
.questionnaire-assignment {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

/* Header Section */
.assignment-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 0;
}

.header-content {
  width: 100% !important;
  padding: 0 1rem;
  display: flex !important;
  justify-content: space-between !important;
  align-items: flex-start;
  position: relative;
}

.header-info {
  flex: 0 0 auto;
  text-align: left;
}

.header-info h1.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem 0;
  text-align: left;
}

.page-subtitle {
  color: #64748b;
  font-size: 1rem;
  margin: 0;
  text-align: left;
}

.header-actions {
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center;
  margin-left: auto;
  align-self: flex-start;
  padding-top: 0;
}

/* Buttons */
.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  height: 2.5rem;
  min-width: 140px;
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.6;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  height: 2.5rem;
  min-width: 100px;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-1px);
}

.btn-action {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-view {
  color: #3b82f6;
}

.btn-view:hover {
  background: #eff6ff;
}

.btn-edit {
  color: #059669;
}

.btn-edit:hover {
  background: #ecfdf5;
}

/* Icons */
.icon {
  width: 1rem;
  height: 1rem;
}

/* Content Layout */
.assignment-content {
  flex: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #3b82f6;
}

.stat-icon.pending {
  color: #f59e0b;
}

.stat-icon.progress {
  color: #8b5cf6;
}

.stat-icon.completed {
  color: #10b981;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
}

/* Filters */
.filters-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.filter-select,
.filter-input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background: white;
  transition: border-color 0.15s ease;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Table */
.assignments-table-section {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.assignments-table {
  width: 100%;
  border-collapse: collapse;
}

.assignments-table th {
  background: #f8fafc;
  padding: 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e2e8f0;
}

.assignments-table td {
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
}

.assignment-row:hover {
  background: #f8fafc;
}

.vendor-info,
.questionnaire-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.vendor-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.8rem;
}

.questionnaire-name {
  font-weight: 600;
  color: #1e293b;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.assigned {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.in_progress {
  background: #e0e7ff;
  color: #3730a3;
}

.status-badge.submitted {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.responded {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.overdue {
  background: #fee2e2;
  color: #991b1b;
}

/* Progress */
.progress-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-bar {
  flex: 1;
  height: 0.5rem;
  background: #e2e8f0;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
  border-radius: 9999px;
}

.progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  white-space: nowrap;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.5rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.empty-icon {
  width: 3rem;
  height: 3rem;
  margin: 0 auto 1rem;
  color: #d1d5db;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.empty-state p {
  margin: 0;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 1rem;
  width: 90%;
  max-width: 480px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  position: relative;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Close Button in Top-Right Corner */
.btn-close-corner {
  position: absolute;
  top: 0.875rem;
  right: 0.875rem;
  background: #f3f4f6;
  border: none;
  padding: 0.4rem;
  border-radius: 0.5rem;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close-corner:hover {
  background: #e5e7eb;
  color: #374151;
  transform: rotate(90deg);
}

.btn-close-corner .icon {
  width: 1.125rem;
  height: 1.125rem;
}

.modal-header {
  padding: 1.25rem 1.25rem 0.75rem 1.25rem;
  border-bottom: none;
}

.modal-header h2 {
  font-size: 1.375rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  padding-right: 2.5rem;
}

.modal-body {
  padding: 0.75rem 1.25rem 1.25rem 1.25rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem 1.25rem 1.25rem;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
  border-radius: 0 0 1rem 1rem;
}

/* Form Elements */
.form-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1.35fr) minmax(220px, 1fr);
  gap: 1.25rem 1.5rem;
  align-items: start;
}

.form-group {
  margin-bottom: 0.875rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group.span-2 {
  grid-column: span 2;
}

.form-group.form-group-full-width {
  grid-column: 1 / -1;
}

.form-group.compact {
  max-width: 240px;
}

.form-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.35rem;
  letter-spacing: 0.01em;
}

.form-select,
.form-input,
.form-textarea {
  width: 100%;
  padding: 0.5rem 0.65rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  background: white;
  transition: all 0.2s ease;
  color: #1e293b;
}

.form-select {
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.125em 1.125em;
  padding-right: 2rem;
  appearance: none;
  height: 2.25rem;
}

.form-select:hover {
  border-color: #9ca3af;
}

.form-input {
  height: 2.25rem;
}

.form-select:focus,
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: #fafbfc;
}

.form-textarea {
  resize: vertical;
  min-height: 3.5rem;
  font-family: inherit;
  line-height: 1.5;
}

.form-select option {
  padding: 0.5rem;
  color: #1e293b;
}

.date-input {
  position: relative;
  display: flex;
  align-items: center;
}

.date-input-field {
  padding-right: 2.5rem;
}

.date-input-icon {
  position: absolute;
  right: 0.65rem;
  color: #6b7280;
  width: 1rem;
  height: 1rem;
  pointer-events: none;
}

.date-input-field::-webkit-calendar-picker-indicator {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  color: transparent;
  background: none;
  opacity: 0;
}

/* Vendor selection is now handled by standard form-select styles */

/* Responsive Design */
@media (max-width: 1024px) {
  .header-content {
    padding: 0 1rem;
  }
  
  .assignment-content {
    padding: 1.5rem 1rem;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }

  .form-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem 1rem;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: row;
    gap: 1rem;
    align-items: center;
  }
  
  .header-actions {
    justify-content: flex-end;
  }
  
  .filters-row {
    flex-direction: column;
  }
  
  .filter-group {
    min-width: 100%;
  }
  
  .assignments-table th,
  .assignments-table td {
    padding: 0.75rem 0.5rem;
  }
  
  .modal-content {
    width: 95%;
    max-width: 95%;
    margin: 1rem;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-group.span-2,
  .form-group.compact {
    grid-column: span 1;
    max-width: 100%;
  }
  
  .modal-header h2 {
    font-size: 1.25rem;
  }
  
  .btn-close-corner {
    top: 0.75rem;
    right: 0.75rem;
    padding: 0.4rem;
  }
  
  .btn-close-corner .icon {
    width: 1rem;
    height: 1rem;
  }
  
  .modal-body {
    padding: 0.75rem 1rem 1rem 1rem;
  }
  
  .modal-footer {
    padding: 1rem;
    flex-wrap: wrap;
  }
  
  .btn-primary,
  .btn-secondary {
    min-width: auto;
    flex: 1;
  }
  
  .form-label {
    font-size: 0.8rem;
  }
  
  .form-select,
  .form-input,
  .form-textarea {
    font-size: 0.8125rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>
