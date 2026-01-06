<template>
  <div class="approval-workflow-creator max-w-6xl mx-auto p-6">
    <!-- RFP Request Information -->
    <div v-if="rfpRequestData" class="bg-blue-50 rounded-lg shadow-sm border border-blue-200 mb-6">
      <div class="px-6 py-4 border-b border-blue-200">
        <h2 class="text-xl font-bold text-blue-900">
          {{ isProposalEvaluation ? 'Proposal Evaluation Information' : 
             isRfpCreation ? 'RFP Creation Approval Information' : 
             isCommitteeEvaluation ? 'Committee Evaluation Information' : 
             'RFP Request Information' }}
        </h2>
        <p class="mt-1 text-sm text-blue-700">
          {{ isProposalEvaluation ? 'Review the proposal details before creating the evaluation workflow' : 
             isRfpCreation ? 'Review the RFP creation request before creating the approval workflow' :
             isCommitteeEvaluation ? 'Review the shortlisted proposals before creating the committee evaluation workflow' :
             'Review the RFP details before creating the approval workflow' }}
        </p>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Basic Information -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-blue-900 uppercase tracking-wide">Basic Information</h3>
            <div>
              <label class="text-xs font-medium text-blue-700">RFP Title</label>
              <p class="text-sm text-gray-900 font-medium">{{ rfpRequestData.title || rfpRequestData.rfp_title || 'Not specified' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-blue-700">RFP Type</label>
              <p class="text-sm text-gray-900">{{ rfpRequestData.type || rfpRequestData.rfp_type || 'Not specified' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-blue-700">Category</label>
              <p class="text-sm text-gray-900">{{ rfpRequestData.category || 'Not specified' }}</p>
            </div>
          </div>

          <!-- Budget & Timeline -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-blue-900 uppercase tracking-wide">Budget & Timeline</h3>
            <div>
              <label class="text-xs font-medium text-blue-700">Budget Range</label>
              <p class="text-sm text-gray-900">
                <span v-if="(rfpRequestData.budgetMin || rfpRequestData.budget_range_min) && (rfpRequestData.budgetMax || rfpRequestData.budget_range_max)">
                  ${{ Number(rfpRequestData.budgetMin || rfpRequestData.budget_range_min).toLocaleString() }} - ${{ Number(rfpRequestData.budgetMax || rfpRequestData.budget_range_max).toLocaleString() }}
                </span>
                <span v-else class="text-gray-500">Not specified</span>
              </p>
            </div>
            <div>
              <label class="text-xs font-medium text-blue-700">Project Timeline</label>
              <p class="text-sm text-gray-900">{{ rfpRequestData.timeline || 'Not specified' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-blue-700">Submission Deadline</label>
              <p class="text-sm text-gray-900">
                {{ (rfpRequestData.deadline || rfpRequestData.submission_deadline) ? new Date(rfpRequestData.deadline || rfpRequestData.submission_deadline).toLocaleDateString() : 'Not specified' }}
              </p>
            </div>
          </div>

          <!-- Evaluation Criteria -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-blue-900 uppercase tracking-wide">Evaluation Criteria</h3>
            <div>
              <label class="text-xs font-medium text-blue-700">Total Criteria</label>
              <p class="text-sm text-gray-900">{{ rfpRequestData.criteria?.length || 0 }} criteria defined</p>
            </div>
            <div v-if="rfpRequestData.criteria && rfpRequestData.criteria.length > 0">
              <label class="text-xs font-medium text-blue-700">Criteria List</label>
              <div class="space-y-1 max-h-32 overflow-y-auto">
                <div v-for="criterion in rfpRequestData.criteria.slice(0, 3)" :key="criterion.id" class="text-xs text-gray-700">
                  • {{ criterion.name }} ({{ criterion.weight }}%)
                </div>
                <div v-if="rfpRequestData.criteria.length > 3" class="text-xs text-gray-500">
                  +{{ rfpRequestData.criteria.length - 3 }} more...
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="mt-6">
          <label class="text-xs font-medium text-blue-700">Description</label>
          <p class="text-sm text-gray-900 mt-1">{{ rfpRequestData.description }}</p>
        </div>
      </div>
    </div>

    <!-- Proposal Information (for proposal evaluation workflows) -->
    <div v-if="isProposalEvaluation && proposalData" class="bg-green-50 rounded-lg shadow-sm border border-green-200 mb-6">
      <div class="px-6 py-4 border-b border-green-200">
        <h2 class="text-xl font-bold text-green-900">Proposal Information</h2>
        <p class="mt-1 text-sm text-green-700">Review the proposal details for evaluation workflow</p>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Vendor Information -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-green-900 uppercase tracking-wide">Vendor Information</h3>
            <div>
              <label class="text-xs font-medium text-green-700">Vendor Name</label>
              <p class="text-sm text-gray-900 font-medium">{{ proposalData.vendor_name || 'Not specified' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-green-700">Organization</label>
              <p class="text-sm text-gray-900">{{ proposalData.org || 'Not specified' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-green-700">Contact Email</label>
              <p class="text-sm text-gray-900">{{ proposalData.contact_email || 'Not specified' }}</p>
            </div>
          </div>

          <!-- Proposal Details -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-green-900 uppercase tracking-wide">Proposal Details</h3>
            <div>
              <label class="text-xs font-medium text-green-700">Proposed Value</label>
              <p class="text-sm text-gray-900 font-semibold text-green-600">
                ${{ proposalData.proposed_value ? Number(proposalData.proposed_value).toLocaleString() : 'Not specified' }}
              </p>
            </div>
            <div>
              <label class="text-xs font-medium text-green-700">Submission Date</label>
              <p class="text-sm text-gray-900">
                {{ proposalData.submitted_at ? new Date(proposalData.submitted_at).toLocaleDateString() : 'Not specified' }}
              </p>
            </div>
            <div>
              <label class="text-xs font-medium text-green-700">Status</label>
              <p class="text-sm text-gray-900">{{ proposalData.evaluation_status || 'Not specified' }}</p>
            </div>
          </div>

          <!-- Evaluation Status -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-green-900 uppercase tracking-wide">Evaluation Status</h3>
            <div>
              <label class="text-xs font-medium text-green-700">Current Status</label>
              <p class="text-sm text-gray-900">{{ proposalData.evaluation_status || 'SUBMITTED' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-green-700">Technical Score</label>
              <p class="text-sm text-gray-900">{{ proposalData.technical_score || 'Not evaluated' }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-green-700">Commercial Score</label>
              <p class="text-sm text-gray-900">{{ proposalData.commercial_score || 'Not evaluated' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Proposal Evaluation Information -->
    <div v-if="isBulkProposalEvaluation && rfpRequestData?.selected_proposals" class="bg-purple-50 rounded-lg shadow-sm border border-purple-200 mb-6">
      <div class="px-6 py-4 border-b border-purple-200">
        <h2 class="text-xl font-bold text-purple-900">Bulk Proposal Evaluation</h2>
        <p class="mt-1 text-sm text-purple-700">
          Creating evaluation workflow for {{ rfpRequestData.proposal_count }} selected proposals
        </p>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Selected Proposals Summary -->
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-purple-900 uppercase tracking-wide">Selected Proposals</h3>
            <div>
              <label class="text-xs font-medium text-purple-700">Total Proposals</label>
              <p class="text-sm text-gray-900 font-medium">{{ rfpRequestData.proposal_count }} proposals</p>
            </div>
            <div>
              <label class="text-xs font-medium text-purple-700">RFP</label>
              <p class="text-sm text-gray-900">{{ rfpRequestData.rfp_title || rfpRequestData.rfp_number }}</p>
            </div>
          </div>

          <!-- Proposal List -->
          <div class="space-y-3 md:col-span-2">
            <h3 class="text-sm font-semibold text-purple-900 uppercase tracking-wide">Proposal Details</h3>
            <div class="max-h-32 overflow-y-auto space-y-2">
              <div 
                v-for="proposal in rfpRequestData.selected_proposals" 
                :key="proposal.response_id"
                class="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-100"
              >
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ proposal.vendor_name }}</p>
                  <p class="text-xs text-gray-500">{{ proposal.org || 'No organization specified' }}</p>
                </div>
                <div class="text-right">
                  <p class="text-xs text-gray-500">ID: {{ proposal.response_id }}</p>
                  <p v-if="proposal.proposed_value" class="text-xs text-purple-600 font-medium">
                    ${{ Number(proposal.proposed_value).toLocaleString() }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Workflow Creation Form -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-900">Create Approval Workflow</h2>
        <p class="mt-1 text-sm text-gray-600">Define workflow template with stages and assigned roles</p>
      </div>

      <form @submit.prevent="submitWorkflow" class="p-6 space-y-6">
        <!-- Workflow Basic Information -->
        <div class="border-b border-gray-200 pb-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Workflow Information</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Workflow Name</label>
              <input
                v-model="workflowForm.workflow_name"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Standard Policy Approval"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Workflow Type</label>
              <select
                v-model="workflowForm.workflow_type"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="MULTI_LEVEL">Multi Level (Sequential)</option>
                <option value="MULTI_PERSON">Multi Person (Parallel)</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Business Object Type</label>
              <!-- Show readonly input field with "RFP" value -->
              <input
                v-model="workflowForm.business_object_type"
                type="text"
                readonly
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 cursor-not-allowed"
              />
              <p class="mt-1 text-xs text-gray-500">
                Business Object Type is automatically set to "RFP" for all RFP workflows (including committee evaluation).
              </p>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Created By</label>
              <input
                v-model="workflowForm.created_by"
                type="text"
                readonly
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50"
                placeholder="User ID"
              />
            </div>
          </div>

          <div class="mt-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              v-model="workflowForm.description"
              required
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe the workflow purpose and rules..."
            />
          </div>
        </div>

        <!-- Stages Configuration -->
        <div class="border-b border-gray-200 pb-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium text-gray-900">Workflow Stages</h3>
            <button
              type="button"
              @click="addStage"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Add Stage
            </button>
          </div>

          <div v-if="stages.length === 0" class="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No stages configured</h3>
            <p class="mt-1 text-sm text-gray-500">Get started by creating your first workflow stage.</p>
            <div class="mt-6">
              <button
                type="button"
                @click="addStage"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Add First Stage
              </button>
            </div>
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="(stage, index) in stages"
              :key="index"
              class="bg-gray-50 rounded-lg p-6 border border-gray-200"
            >
              <div class="flex justify-between items-center mb-4">
                <h4 class="text-md font-medium text-gray-900">Stage {{ index + 1 }}</h4>
                <div class="flex space-x-2">
                  <button
                    v-if="index > 0"
                    type="button"
                    @click="moveStage(index, 'up')"
                    class="text-gray-400 hover:text-gray-600"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                  <button
                    v-if="index < stages.length - 1"
                    type="button"
                    @click="moveStage(index, 'down')"
                    class="text-gray-400 hover:text-gray-600"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    @click="removeStage(index)"
                    class="text-red-400 hover:text-red-600"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Stage Name</label>
                  <input
                    v-model="stage.stage_name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Manager Review"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Stage Order</label>
                  <input
                    v-model.number="stage.stage_order"
                    type="number"
                    min="1"
                    :max="stages.length"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Assigned User
                    <span class="text-xs text-gray-500 font-normal ml-1">(Management & Executive only)</span>
                  </label>
                  <select
                    v-model="stage.assigned_user_id"
                    required
                    @change="(event) => handleUserSelection(stage, event.target.value)"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select user</option>
                    <option
                      v-for="user in users"
                      :key="user.id"
                      :value="user.id"
                    >
                      {{ getUserDisplayName(user) }}
                    </option>
                  </select>
                  <p v-if="users.length === 0" class="mt-1 text-xs text-red-600">
                    No users with Management or Executive role available
                  </p>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">User Role</label>
                  <input
                    v-model="stage.assigned_user_role"
                    type="text"
                    readonly
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50"
                    placeholder="Auto-populated from user"
                  />
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Department</label>
                  <input
                    v-model="stage.department"
                    type="text"
                    readonly
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50"
                    placeholder="Auto-populated from user"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Assigned User Name</label>
                  <input
                    v-model="stage.assigned_user_name"
                    type="text"
                    readonly
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50"
                    placeholder="Auto-populated from user"
                  />
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Stage Type</label>
                  <select
                    v-model="stage.stage_type"
                    disabled
                    :class="'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 cursor-not-allowed'"
                  >
                    <option value="SEQUENTIAL">Sequential</option>
                    <option value="PARALLEL">Parallel</option>
                  </select>
                  <p class="mt-1 text-xs text-gray-500">
                    Stage Type matches Workflow Type
                  </p>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Deadline Date</label>
                  <input
                    v-model="stage.deadline_date"
                    type="date"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div class="mt-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">Stage Description</label>
                <textarea
                  v-model="stage.stage_description"
                  rows="2"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Describe what this stage involves..."
                />
              </div>

              <div class="mt-4">
                <label class="flex items-center">
                  <input
                    v-model="stage.is_mandatory"
                    type="checkbox"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span class="ml-2 text-sm text-gray-700">This stage is mandatory</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="flex justify-end space-x-4 pt-6">
          <button
            type="button"
            @click="resetForm"
            class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Reset
          </button>
          <button
            type="submit"
            :disabled="submitting"
            class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {{ submitting ? 'Creating...' : 'Create Workflow' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Success Modal -->
    <div
      v-if="successDialogVisible"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
    >
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 class="text-lg leading-6 font-medium text-gray-900 mt-4">Workflow Created!</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500">Your approval workflow has been created successfully.</p>
            
            <!-- Bulk Proposal Evaluation Summary -->
            <div v-if="isBulkProposalEvaluation && rfpRequestData?.selected_proposals" class="mt-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
              <p class="text-sm font-medium text-purple-900">Bulk Proposal Evaluation Created:</p>
              <p class="text-sm text-purple-700">
                {{ rfpRequestData.proposal_count }} proposals assigned to {{ stages.length }} evaluators
              </p>
              <p class="text-xs text-purple-600 mt-1">
                Total evaluation tasks: {{ rfpRequestData.proposal_count * stages.length }} ({{ stages.length }} evaluators × {{ rfpRequestData.proposal_count }} proposals)
              </p>
            </div>
            
            <p v-if="rfpRequestData" class="text-sm text-gray-500 mt-2">
              This workflow is now ready to be used for the RFP: <strong>{{ rfpRequestData.rfp_title || rfpRequestData.title || 'Untitled RFP' }}</strong>
            </p>
            <div class="mt-4 text-left bg-gray-50 p-4 rounded-md">
              <p class="text-sm"><strong>Workflow ID:</strong> {{ createdWorkflowId }}</p>
              <p class="text-sm"><strong>Name:</strong> {{ workflowForm.workflow_name }}</p>
              <p class="text-sm"><strong>Type:</strong> {{ getWorkflowTypeLabel(workflowForm.workflow_type) }}</p>
              <p class="text-sm"><strong>Stages:</strong> {{ stages.length }}</p>
              <div v-if="createdApprovalId" class="mt-3 pt-3 border-t border-gray-200">
                <p class="text-sm font-medium text-blue-900">Approval Request(s) Created:</p>
                <p class="text-sm"><strong>Approval ID(s):</strong> {{ createdApprovalId }}</p>
                <p class="text-sm"><strong>Status:</strong> DRAFT</p>
                <p class="text-sm"><strong>Priority:</strong> {{ rfpRequestData?.criticality_level || rfpRequestData?.criticalityLevel || 'Medium' }}</p>
                <div class="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                  <p class="text-xs font-medium text-blue-900">Version Tracking Enabled</p>
                  <p class="text-xs text-blue-700">
                    All stage status changes will be automatically logged with version numbers. 
                    Each approval request will maintain a complete audit trail.
                  </p>
                </div>
                <div v-if="isBulkProposalEvaluation && rfpRequestData?.selected_proposals" class="mt-2">
                  <p class="text-xs text-gray-600">
                    Each evaluator will receive {{ rfpRequestData.proposal_count }} evaluation tasks (one per proposal). 
                    Total: {{ stages.length }} evaluators × {{ rfpRequestData.proposal_count }} proposals = {{ rfpRequestData.proposal_count * stages.length }} evaluation tasks.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="items-center px-4 py-3">
            <button
              @click="closeSuccessDialog"
              class="px-4 py-2 bg-blue-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '@/utils/api_rfp'
import axios from 'axios'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiUrl, getApiOrigin } from '@/utils/backendEnv'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// Form data
const workflowForm = reactive({
  workflow_name: '',
  workflow_type: 'MULTI_LEVEL',
  description: '',
  business_object_type: 'RFP', // Default to RFP
  is_active: true,
  created_by: '1', // Default user ID
})

// Stages data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

const stages = ref([])

// Users data - fetched from backend
const users = ref([])
const loadingUsers = ref(false)

// State
const submitting = ref(false)
const successDialogVisible = ref(false)
const createdWorkflowId = ref('')
const createdApprovalId = ref('')
const rfpRequestData = ref(null)
const proposalData = ref(null)

// Computed
const isProposalEvaluation = computed(() => {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('type') === 'proposal_evaluation'
})

const isRfpCreation = computed(() => {
  const urlParams = new URLSearchParams(window.location.search)
  const workflowType = urlParams.get('type')
  return workflowType === 'rfp_creation' || 
         workflowType === 'proposal_evaluation' || 
         workflowType === 'bulk_proposal_evaluation' || 
         workflowType === 'committee_evaluation'
})

const isCommitteeEvaluation = computed(() => {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('type') === 'committee_evaluation'
})

const isBulkProposalEvaluation = computed(() => {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('type') === 'bulk_proposal_evaluation'
})

// Methods
const addStage = () => {
  // Determine stage type based on workflow type
  let stageType = 'SEQUENTIAL' // Default
  if (workflowForm.workflow_type === 'MULTI_PERSON') {
    stageType = 'PARALLEL'
  } else if (workflowForm.workflow_type === 'MULTI_LEVEL') {
    stageType = 'SEQUENTIAL'
  }
  
  const newStage = {
    stage_order: stages.value.length + 1,
    stage_name: '',
    stage_description: '',
    assigned_user_id: '',
    assigned_user_name: '',
    assigned_user_role: '',
    department: '',
    stage_type: stageType,
    deadline_date: null,
    is_mandatory: true
  }
  stages.value.push(newStage)
}

const addDefaultStages = () => {
  // Get first two users from the fetched users list
  const user1 = users.value[0] || { id: '1', first_name: 'User', last_name: 'One', role: 'Manager', department: 'General' }
  const user2 = users.value[1] || { id: '2', first_name: 'User', last_name: 'Two', role: 'Director', department: 'General' }
  
  // Add Manager Review stage
  const managerStage = {
    stage_order: 1,
    stage_name: 'Manager Review',
    stage_description: 'Initial review by department manager',
    assigned_user_id: user1.id,
    assigned_user_name: `${user1.first_name} ${user1.last_name}`,
    assigned_user_role: user1.role || 'Manager',
    department: user1.department || 'General',
    stage_type: 'SEQUENTIAL',
    deadline_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
    is_mandatory: true
  }
  
  // Add Director Approval stage
  const directorStage = {
    stage_order: 2,
    stage_name: 'Director Approval',
    stage_description: 'Final approval by department director',
    assigned_user_id: user2.id,
    assigned_user_name: `${user2.first_name} ${user2.last_name}`,
    assigned_user_role: user2.role || 'Director',
    department: user2.department || 'General',
    stage_type: 'SEQUENTIAL',
    deadline_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 14 days from now
    is_mandatory: true
  }
  
  stages.value.push(managerStage, directorStage)
  console.log('Added default stages for RFP creation:', stages.value)
}

const addProposalEvaluationStages = () => {
  // Get first two users from the fetched users list
  const user1 = users.value[0] || { id: '1', first_name: 'User', last_name: 'One', role: 'Technical Manager', department: 'IT' }
  const user2 = users.value[1] || { id: '2', first_name: 'User', last_name: 'Two', role: 'Finance Director', department: 'Finance' }
  
  // Add Technical Evaluation stage
  const technicalStage = {
    stage_order: 1,
    stage_name: 'Technical Evaluation',
    stage_description: 'Technical review of the proposal by technical experts using detailed evaluation criteria',
    assigned_user_id: user1.id,
    assigned_user_name: `${user1.first_name} ${user1.last_name}`,
    assigned_user_role: user1.role || 'Technical Manager',
    department: user1.department || 'IT',
    stage_type: 'PARALLEL',
    deadline_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days from now
    is_mandatory: true
  }
  
  // Add Commercial Evaluation stage
  const commercialStage = {
    stage_order: 2,
    stage_name: 'Commercial Evaluation',
    stage_description: 'Commercial and financial review of the proposal including pricing and terms',
    assigned_user_id: user2.id,
    assigned_user_name: `${user2.first_name} ${user2.last_name}`,
    assigned_user_role: user2.role || 'Finance Director',
    department: user2.department || 'Finance',
    stage_type: 'PARALLEL',
    deadline_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days from now (same as technical)
    is_mandatory: true
  }
  
  stages.value.push(technicalStage, commercialStage)
  console.log('Added proposal evaluation stages:', stages.value)
}

const addCommitteeEvaluationStages = async () => {
  try {
    // Get RFP ID from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id') || localStorage.getItem('current_rfp_id')
    
    if (!rfpId) {
      console.error('No RFP ID found for committee evaluation')
      return
    }
    
    // Fetch committee members from backend
    const response = await fetch(`https://grc-tprm.vardaands.com/api/tprm/rfp/rfp/${rfpId}/committee/get/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      console.error('Failed to fetch committee members')
      return
    }
    
    const committeeData = await response.json()
    if (!committeeData.success || !committeeData.committee_members) {
      console.error('No committee members found')
      return
    }
    
    // Clear existing stages
    stages.value = []
    
    // Create one stage per committee member (parallel execution)
    committeeData.committee_members.forEach((member, index) => {
      const stage = {
        stage_order: 0, // All stages run in parallel (order = 0)
        stage_name: `Committee Evaluation - Member ${member.member_id}`,
        stage_description: `Final committee evaluation by committee member (${member.member_role})`,
        assigned_user_id: member.member_id,
        assigned_user_name: `Committee Member ${member.member_id}`,
        assigned_user_role: member.member_role || 'Committee Member',
        department: 'Committee',
        stage_type: 'PARALLEL',
        deadline_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 14 days from now
        is_mandatory: true
      }
      stages.value.push(stage)
    })
    
    console.log(`Added ${stages.value.length} committee evaluation stages (one per member):`, stages.value)
    
  } catch (error) {
    console.error('Error adding committee evaluation stages:', error)
    // Fallback to default stages if API fails
    addDefaultCommitteeStages()
  }
}

const addDefaultCommitteeStages = () => {
  // Get users from the fetched users list
  const user1 = users.value[0] || { id: '1', first_name: 'User', last_name: 'One', role: 'Committee Member', department: 'IT' }
  const user2 = users.value[2] || { id: '3', first_name: 'User', last_name: 'Three', role: 'Committee Chair', department: 'Operations' }
  
  // Fallback: Add default committee stages if API fails
  const committeeChairStage = {
    stage_order: 1,
    stage_name: 'Committee Chair Evaluation',
    stage_description: 'Committee chair conducts detailed evaluation and ranking of shortlisted proposals',
    assigned_user_id: user2.id,
    assigned_user_name: `${user2.first_name} ${user2.last_name}`,
    assigned_user_role: user2.role || 'Committee Chair',
    department: user2.department || 'Operations',
    stage_type: 'SEQUENTIAL',
    deadline_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days from now
    is_mandatory: true
  }
  
  const committeeMemberStage = {
    stage_order: 2,
    stage_name: 'Committee Member Evaluation',
    stage_description: 'Committee members provide individual evaluations and rankings',
    assigned_user_id: user1.id,
    assigned_user_name: `${user1.first_name} ${user1.last_name}`,
    assigned_user_role: user1.role || 'Committee Member',
    department: user1.department || 'IT',
    stage_type: 'PARALLEL',
    deadline_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days from now (same as chair)
    is_mandatory: true
  }
  
  const finalConsensusStage = {
    stage_order: 3,
    stage_name: 'Final Consensus & Award',
    stage_description: 'Final consensus building and award declaration',
    assigned_user_id: user2.id,
    assigned_user_name: `${user2.first_name} ${user2.last_name}`,
    assigned_user_role: user2.role || 'Committee Chair',
    department: user2.department || 'Operations',
    stage_type: 'SEQUENTIAL',
    deadline_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
    is_mandatory: true
  }
  
  stages.value.push(committeeChairStage, committeeMemberStage, finalConsensusStage)
  console.log('Added default committee evaluation stages:', stages.value)
}

const addBulkProposalEvaluationStages = () => {
  // Get users from the fetched users list
  const user1 = users.value[0] || { id: '1', first_name: 'User', last_name: 'One', role: 'Technical Manager', department: 'IT' }
  const user2 = users.value[1] || { id: '2', first_name: 'User', last_name: 'Two', role: 'Finance Director', department: 'Finance' }
  const user3 = users.value[2] || { id: '3', first_name: 'User', last_name: 'Three', role: 'VP Operations', department: 'Operations' }
  const user4 = users.value[3] || { id: '4', first_name: 'User', last_name: 'Four', role: 'QA Manager', department: 'HR' }
  
  // Add Technical Evaluation stage for bulk proposals
  const technicalStage = {
    stage_order: 1,
    stage_name: 'Technical Evaluation',
    stage_description: 'Technical review of selected proposals by technical experts using detailed evaluation criteria',
    assigned_user_id: user1.id,
    assigned_user_name: `${user1.first_name} ${user1.last_name}`,
    assigned_user_role: user1.role || 'Technical Manager',
    department: user1.department || 'IT',
    stage_type: 'PARALLEL',
    deadline_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
    is_mandatory: true
  }
  
  // Add Commercial Evaluation stage for bulk proposals
  const commercialStage = {
    stage_order: 2,
    stage_name: 'Commercial Evaluation',
    stage_description: 'Commercial and financial review of selected proposals including pricing and terms',
    assigned_user_id: user2.id,
    assigned_user_name: `${user2.first_name} ${user2.last_name}`,
    assigned_user_role: user2.role || 'Finance Director',
    department: user2.department || 'Finance',
    stage_type: 'PARALLEL',
    deadline_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
    is_mandatory: true
  }
  
  // Add Quality Assurance Review stage
  const qualityReviewStage = {
    stage_order: 3,
    stage_name: 'Quality Assurance Review',
    stage_description: 'Quality assurance review to ensure evaluation consistency and completeness',
    assigned_user_id: user4.id,
    assigned_user_name: `${user4.first_name} ${user4.last_name}`,
    assigned_user_role: user4.role || 'QA Manager',
    department: user4.department || 'HR',
    stage_type: 'SEQUENTIAL',
    deadline_date: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 10 days from now
    is_mandatory: true
  }
  
  // Add Senior Management Approval stage
  const seniorApprovalStage = {
    stage_order: 4,
    stage_name: 'Senior Management Approval',
    stage_description: 'Final approval by senior management for bulk proposal evaluation results',
    assigned_user_id: user3.id,
    assigned_user_name: `${user3.first_name} ${user3.last_name}`,
    assigned_user_role: user3.role || 'VP Operations',
    department: user3.department || 'Operations',
    stage_type: 'SEQUENTIAL',
    deadline_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 14 days from now
    is_mandatory: true
  }
  
  stages.value.push(technicalStage, commercialStage, qualityReviewStage, seniorApprovalStage)
  console.log('Added bulk proposal evaluation stages:', stages.value)
}

const removeStage = (index: number) => {
  PopupService.confirm(
    'Are you sure you want to remove this stage?',
    'Confirm Removal',
    () => {
      stages.value.splice(index, 1)
      // Reorder remaining stages
      stages.value.forEach((stage, idx) => {
        stage.stage_order = idx + 1
      })
    }
  )
}

const moveStage = (index: number, direction: string) => {
  if (direction === 'up' && index > 0) {
    const temp = stages.value[index]
    stages.value[index] = stages.value[index - 1]
    stages.value[index - 1] = temp
    // Update stage orders
    stages.value.forEach((stage, idx) => {
      stage.stage_order = idx + 1
    })
  } else if (direction === 'down' && index < stages.value.length - 1) {
    const temp = stages.value[index]
    stages.value[index] = stages.value[index + 1]
    stages.value[index + 1] = temp
    // Update stage orders
    stages.value.forEach((stage, idx) => {
      stage.stage_order = idx + 1
    })
  }
}

const validateStages = () => {
  if (stages.value.length < 2) {
    PopupService.warning('At least two stages are required for a workflow', 'Insufficient Stages')
    return false
  }
  
  for (let i = 0; i < stages.value.length; i++) {
    const stage = stages.value[i]
    if (!stage.stage_name || !stage.assigned_user_id || !stage.assigned_user_name || !stage.deadline_date) {
      PopupService.warning(`Stage ${i + 1} is missing required information (name, user, or deadline)`, 'Missing Information')
      return false
    }
  }

  return true
}

const submitWorkflow = async () => {
  if (!validateStages()) {
    return
  }

  // Prevent duplicate submissions
  if (submitting.value) {
    console.log('Workflow submission already in progress')
    return
  }

  try {
    submitting.value = true

    // Prepare stages data with proper date formatting and type conversion
    const formattedStages = stages.value.map(stage => {
      let userId = null
      if (stage.assigned_user_id) {
        // Convert 'U001' to 1, 'U002' to 2, etc.
        const numericPart = stage.assigned_user_id.replace(/^U/, '')
        userId = parseInt(numericPart)
        if (isNaN(userId)) {
          console.error('Invalid user ID format:', stage.assigned_user_id)
          userId = null
        }
      }
      
      return {
        ...stage,
        assigned_user_id: userId,
        deadline_date: stage.deadline_date ? new Date(stage.deadline_date).toISOString() : null
      }
    })

    const submitData = {
      ...workflowForm,
      created_by: parseInt(workflowForm.created_by),
      stages_config: formattedStages,
      // Include RFP data to create approval request
      rfp_data: rfpRequestData.value
    }
    
    console.log('Submitting workflow data:', submitData)
    console.log('RFP Data being sent:', submitData.rfp_data)
    console.log('Workflow Type Hint:', submitData.rfp_data?.workflow_type_hint)
    console.log('Stages being sent:', submitData.stages_config)
    
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    const response = await axios.post(`${apiOrigin}/api/tprm/rfp-approval/workflows/`, submitData, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })
    
    console.log('Workflow creation response:', response.data)
    console.log('Workflow ID:', response.data.workflow_id)
    console.log('Approval ID(s):', response.data.approval_id || response.data.approval_ids)
    console.log('Approval Count:', response.data.approval_count)
    
    createdWorkflowId.value = response.data.workflow_id
    createdApprovalId.value = response.data.approval_id || (response.data.approval_ids ? response.data.approval_ids.join(', ') : null)
    successDialogVisible.value = true
    
  } catch (error) {
    console.error('Error creating workflow:', error)
    console.error('Error response:', error.response)
    console.error('Error data:', error.response?.data)
    console.error('Error status:', error.response?.status)
    PopupService.error('Failed to create workflow: ' + (error.response?.data?.error || error.message || 'Unknown error'), 'Workflow Creation Failed')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  workflowForm.workflow_name = ''
  workflowForm.workflow_type = 'MULTI_LEVEL'
  workflowForm.description = ''
  workflowForm.business_object_type = ''
  workflowForm.is_active = true
  stages.value = []
}

const closeSuccessDialog = () => {
  successDialogVisible.value = false
  // Clear RFP data since workflow has been created
  localStorage.removeItem('rfp_for_approval_workflow')
  rfpRequestData.value = null
  createdApprovalId.value = ''
  // Navigate back or reset as needed
  resetForm()
}

const getWorkflowTypeLabel = (type: string) => {
  return type === 'MULTI_LEVEL' ? 'Multi Level (Sequential)' : 'Multi Person (Parallel)'
}

const handleUserSelection = (stage: any, userId: string) => {
  const selectedUser = users.value.find(user => user.id === userId)
  if (selectedUser) {
    stage.assigned_user_id = selectedUser.id
    stage.assigned_user_name = `${selectedUser.first_name} ${selectedUser.last_name}`
    stage.assigned_user_role = selectedUser.role
    stage.department = selectedUser.department
  }
}

const getUserDisplayName = (user: any) => {
  const firstName = user.first_name || 'Unknown'
  const lastName = user.last_name || 'User'
  const role = user.role || 'User'
  const department = user.department || 'General'
  return `${firstName} ${lastName} (${role} - ${department})`
}

const fetchUsers = async () => {
  try {
    loadingUsers.value = true
    
    // Get workflow type from URL or workflow form
    const urlParams = new URLSearchParams(window.location.search)
    let workflowType = urlParams.get('type')
    
    // If no workflow type in URL, check the workflow form
    if (!workflowType) {
      // Try to infer from business_object_type or workflow_name
      if (workflowForm.workflow_name?.toLowerCase().includes('rfp creation')) {
        workflowType = 'rfp_creation'
      }
    }
    
    // Build URL with workflow_type parameter
    // Try multiple URL paths in case one doesn't work
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    let baseUrls = [
      `${apiOrigin}/api/tprm/rfp-approval/users/`,
      'https://grc-tprm.vardaands.com/api/tprm/rfp-approval/users/',
      `${apiOrigin}/api/tprm/approval/users/`
    ]
    
    let url = baseUrls[0] // Start with the most likely working path
    if (workflowType) {
      url += `?workflow_type=${workflowType}`
    }
    
    console.log('📡 Fetching users for workflow type:', workflowType)
    console.log('📡 API URL:', url)
    
    let response
    let lastError
    
    // Try each URL path until one works
    for (const baseUrl of baseUrls) {
      try {
        const testUrl = workflowType ? `${baseUrl}?workflow_type=${workflowType}` : baseUrl
        console.log(`🔄 Trying URL: ${testUrl}`)
        response = await axios.get(testUrl, {
          headers: getAuthHeaders()
        })
        console.log(`✅ Success with URL: ${testUrl}`)
        break // Success, exit loop
      } catch (error) {
        console.log(`❌ Failed with URL: ${baseUrl}`, error.response?.status)
        lastError = error
        // Continue to next URL
      }
    }
    
    // If all URLs failed, throw the last error
    if (!response) {
      throw lastError || new Error('All URL paths failed')
    }
    
    console.log('📊 Users API response:', response.data)
    
    // Check if response has error field (backend returns error in response body)
    if (response.data && response.data.error) {
      console.error('❌ Backend returned error:', response.data.error)
      console.error('   Allowed roles:', response.data.allowed_roles)
      console.error('   Total users in DB:', response.data.total_users_in_db)
      users.value = []
      // Show error notification
      showError('No Users Available', response.data.error)
    } else if (Array.isArray(response.data)) {
      // Normal response - array of users
      users.value = response.data
      console.log(`✅ Fetched ${users.value.length} users from backend:`, users.value)
      
      if (users.value.length === 0) {
        showWarning('No Users Found', `No users found with the required roles for ${workflowType || 'this workflow type'}. Please ensure users have the correct roles assigned in the rbac_tprm table.`)
      }
    } else if (response.data && response.data.users) {
      // Response wrapped in object
      users.value = response.data.users
      console.log(`✅ Fetched ${users.value.length} users from backend:`, users.value)
    } else {
      console.warn('⚠️ Unexpected response format:', response.data)
      users.value = []
    }
  } catch (error) {
    console.error('❌ Error fetching users:', error)
    console.error('   Error response:', error.response?.data)
    console.error('   Error status:', error.response?.status)
    
    users.value = []
    
    // Show user-friendly error message
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        'Failed to fetch users from the server'
    showError('Error Loading Users', errorMessage)
  } finally {
    loadingUsers.value = false
  }
}

const fetchRFPFromDatabase = async (rfpId: string) => {
  try {
    console.log('Fetching RFP data from database for ID:', rfpId)
    const response = await axios.get(`https://grc-tprm.vardaands.com/api/tprm/rfp/rfps/${rfpId}/`, {
      headers: getAuthHeaders()
    })
    console.log('Fetched RFP data from database:', response.data)
    
    if (response.data) {
      // Update rfpRequestData with fresh data from database
      rfpRequestData.value = {
        ...rfpRequestData.value,
        rfp_id: response.data.rfp_id,
        rfp_number: response.data.rfp_number,
        rfp_title: response.data.rfp_title,
        title: response.data.rfp_title, // Add frontend field name
        description: response.data.description,
        rfp_type: response.data.rfp_type,
        type: response.data.rfp_type, // Add frontend field name
        category: response.data.category,
        estimated_value: response.data.estimated_value,
        estimatedValue: response.data.estimated_value, // Add frontend field name
        currency: response.data.currency,
        budget_range_min: response.data.budget_range_min,
        budgetMin: response.data.budget_range_min, // Add frontend field name
        budget_range_max: response.data.budget_range_max,
        budgetMax: response.data.budget_range_max, // Add frontend field name
        issue_date: response.data.issue_date,
        issueDate: response.data.issue_date, // Add frontend field name
        submission_deadline: response.data.submission_deadline,
        deadline: response.data.submission_deadline, // Add frontend field name
        evaluation_period_end: response.data.evaluation_period_end,
        evaluationPeriodEnd: response.data.evaluation_period_end, // Add frontend field name
        evaluation_method: response.data.evaluation_method,
        evaluationMethod: response.data.evaluation_method, // Add frontend field name
        criticality_level: response.data.criticality_level,
        criticalityLevel: response.data.criticality_level, // Add frontend field name
        geographical_scope: response.data.geographical_scope,
        geographicalScope: response.data.geographical_scope, // Add frontend field name
        compliance_requirements: response.data.compliance_requirements,
        complianceRequirements: response.data.compliance_requirements, // Add frontend field name
        allow_late_submissions: response.data.allow_late_submissions,
        allowLateSubmissions: response.data.allow_late_submissions, // Add frontend field name
        auto_publish: response.data.auto_publish,
        autoPublish: response.data.auto_publish, // Add frontend field name
        status: response.data.status,
        created_at: response.data.created_at,
        updated_at: response.data.updated_at
      }
      
      console.log('Updated RFP data with database values:', rfpRequestData.value)
      
      // Fetch evaluation criteria if RFP number is available
      if (response.data.rfp_number) {
        await fetchEvaluationCriteria(response.data.rfp_number)
      }
    }
  } catch (error) {
    console.error('Error fetching RFP from database:', error)
  }
}

// Fetch evaluation criteria for the RFP
const fetchEvaluationCriteria = async (rfpNumber: string) => {
  try {
    console.log('Fetching evaluation criteria for RFP:', rfpNumber)
    const response = await axios.get(`https://grc-tprm.vardaands.com/api/tprm/rfp/rfp/${rfpNumber}/evaluation-criteria/`, {
      headers: getAuthHeaders()
    })
    console.log('Fetched evaluation criteria:', response.data)
    
    if (response.data && response.data.success && response.data.criteria) {
      // Transform criteria to match template format
      const transformedCriteria = response.data.criteria.map((criterion: any) => ({
        id: criterion.criteria_id,
        name: criterion.criteria_name,
        weight: criterion.weight_percentage,
        description: criterion.criteria_description,
        type: criterion.evaluation_type,
        required: criterion.is_mandatory
      }))
      
      // Update rfpRequestData with criteria
      if (rfpRequestData.value) {
        rfpRequestData.value.criteria = transformedCriteria
        console.log('✅ Updated RFP data with evaluation criteria:', transformedCriteria.length, 'criteria')
      } else {
        console.warn('⚠️ rfpRequestData is null, cannot add criteria')
      }
    } else {
      console.log('ℹ️ No evaluation criteria found for RFP:', rfpNumber)
      // Initialize empty criteria array if none found
      if (rfpRequestData.value) {
        rfpRequestData.value.criteria = []
      }
    }
  } catch (error) {
    console.error('Error fetching evaluation criteria:', error)
    // Initialize empty criteria array on error
    if (rfpRequestData.value) {
      rfpRequestData.value.criteria = []
    }
  }
}

// Initialize
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Approval Workflow Creator')
  workflowForm.created_by = '1' // Set default user ID
  
  // Fetch users from backend first
  await fetchUsers()
  
  // Check URL parameters for workflow type
  const urlParams = new URLSearchParams(window.location.search)
  const workflowType = urlParams.get('type')
  console.log('Workflow type from URL:', workflowType)
  
  // Set workflow form based on type
  if (workflowType === 'proposal_evaluation') {
    workflowForm.business_object_type = 'RFP'
    workflowForm.workflow_name = 'Proposal Evaluation Workflow'
    workflowForm.workflow_type = 'MULTI_PERSON' // Parallel workflow for proposal evaluation
    workflowForm.description = 'Workflow for evaluating vendor proposals submitted for RFP'
  } else if (workflowType === 'bulk_proposal_evaluation') {
    workflowForm.business_object_type = 'RFP'
    workflowForm.workflow_name = 'Bulk Proposal Evaluation Workflow'
    workflowForm.workflow_type = 'MULTI_PERSON' // Parallel workflow for bulk proposal evaluation
    workflowForm.description = 'Workflow for bulk evaluation of multiple vendor proposals'
  } else if (workflowType === 'rfp_creation') {
    workflowForm.business_object_type = 'RFP'
    workflowForm.workflow_name = 'RFP Creation Approval Workflow'
    workflowForm.description = 'Workflow for approving RFP creation requests'
  } else if (workflowType === 'committee_evaluation') {
    workflowForm.business_object_type = 'RFP'
    workflowForm.workflow_name = 'Committee Evaluation Workflow'
    workflowForm.description = 'Workflow for final committee evaluation and ranking of shortlisted vendors'
    // Load committee evaluation stages asynchronously
    addCommitteeEvaluationStages()
  }
  
  // Load RFP data from the previous page
  const rfpData = localStorage.getItem('rfp_for_approval_workflow')
  const currentRfpId = localStorage.getItem('current_rfp_id')
  const proposalDataStr = localStorage.getItem('proposal_for_evaluation')
  console.log('Raw localStorage data:', rfpData)
  console.log('Current RFP ID:', currentRfpId)
  console.log('Proposal data:', proposalDataStr)
  
  // Load proposal data if available
  if (proposalDataStr) {
    try {
      proposalData.value = JSON.parse(proposalDataStr)
      console.log('Parsed proposal data:', proposalData.value)
    } catch (error) {
      console.error('Error parsing proposal data:', error)
    }
  }
  
  if (rfpData) {
    try {
      const parsedData = JSON.parse(rfpData)
      console.log('Parsed RFP data:', parsedData)
      console.log('All keys in RFP data:', Object.keys(parsedData))
      console.log('Criteria in parsed data:', parsedData.criteria)
      
      rfpRequestData.value = parsedData
      
      // Add workflow_type_hint to rfp data for backend detection
      if (workflowType) {
        rfpRequestData.value.workflow_type_hint = workflowType
        console.log('Added workflow_type_hint:', workflowType)
      }
      
      console.log('RFP Title (title):', parsedData.title)
      console.log('RFP Title (rfp_title):', parsedData.rfp_title)
      console.log('RFP Type (type):', parsedData.type)
      console.log('RFP Type (rfp_type):', parsedData.rfp_type)
      console.log('RFP Description:', parsedData.description)
      console.log('RFP ID (rfp_id):', parsedData.rfp_id)
      console.log('RFP Number:', parsedData.rfp_number)
      console.log('Criteria count:', parsedData.criteria?.length || 0)
      
      // Auto-add default stages if none exist
      if (stages.value.length === 0) {
        console.log('No stages found, adding default stages...')
        if (workflowType === 'proposal_evaluation') {
          addProposalEvaluationStages()
        } else if (workflowType === 'bulk_proposal_evaluation') {
          addBulkProposalEvaluationStages()
        } else if (workflowType === 'rfp_creation') {
          addDefaultStages() // Use default RFP creation stages
        } else if (workflowType === 'committee_evaluation') {
          addCommitteeEvaluationStages()
        } else {
          addDefaultStages() // Default fallback
        }
      }
    } catch (error) {
      console.error('Error parsing RFP data:', error)
    }
  } else {
    console.log('No RFP data found in localStorage')
  }
  
  // Fallback: Try to fetch RFP data from database if localStorage data is incomplete or missing
  const rfpIdToFetch = rfpRequestData.value?.rfp_id || currentRfpId
  if (rfpIdToFetch && (!rfpRequestData.value || !rfpRequestData.value.title && !rfpRequestData.value.rfp_title)) {
    console.log('RFP data incomplete or missing, fetching from database for ID:', rfpIdToFetch)
    // Call fetchRFPFromDatabase without await to avoid blocking onMounted
    fetchRFPFromDatabase(rfpIdToFetch).then(() => {
      console.log('RFP data fetched from database successfully')
    }).catch((error) => {
      console.error('Failed to fetch RFP data from database:', error)
    })
  } else if (rfpRequestData.value && rfpRequestData.value.rfp_number && !rfpRequestData.value.criteria) {
    // If RFP data exists but criteria are missing, fetch criteria
    console.log('RFP data exists but criteria missing, fetching criteria for RFP:', rfpRequestData.value.rfp_number)
    fetchEvaluationCriteria(rfpRequestData.value.rfp_number).then(() => {
      console.log('Evaluation criteria fetched successfully')
    }).catch((error) => {
      console.error('Failed to fetch evaluation criteria:', error)
    })
  }
})

// Watch for changes to business_object_type and ensure it stays "RFP" for RFP-related workflows
watch(() => isRfpCreation.value, (isRfpCreationWorkflow) => {
  if (isRfpCreationWorkflow) {
    // Ensure business object type is always "RFP" for RFP-related workflows (creation, evaluation, committee)
    workflowForm.business_object_type = 'RFP'
  }
}, { immediate: true })

// Watch for committee evaluation and ensure business_object_type is "RFP"
watch(() => isCommitteeEvaluation.value, (isCommitteeEval) => {
  if (isCommitteeEval) {
    // Ensure business object type is always "RFP" for committee evaluation workflows
    workflowForm.business_object_type = 'RFP'
  }
}, { immediate: true })

// Also watch the business_object_type field itself to prevent manual changes for RFP-related workflows
watch(() => workflowForm.business_object_type, (newValue) => {
  if ((isRfpCreation.value || isCommitteeEvaluation.value || isProposalEvaluation.value || isBulkProposalEvaluation.value) && newValue !== 'RFP') {
    // Revert to "RFP" if user tries to change it for an RFP-related workflow
    workflowForm.business_object_type = 'RFP'
  }
})

// Watch for workflow_type changes and sync all stages to match
watch(() => workflowForm.workflow_type, (newType) => {
  // Map workflow type to stage type
  let stageType = 'SEQUENTIAL'
  if (newType === 'MULTI_PERSON') {
    stageType = 'PARALLEL'
  } else if (newType === 'MULTI_LEVEL') {
    stageType = 'SEQUENTIAL'
  }
  
  // Update all stages to match the workflow type
  stages.value.forEach(stage => {
    stage.stage_type = stageType
  })
})
</script>

<style scoped>
/* Component-specific styles */
</style>