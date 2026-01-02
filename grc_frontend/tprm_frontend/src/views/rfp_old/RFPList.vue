<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">RFP Management</h1>
        <p class="text-muted-foreground">
          View, manage, and share all your active RFPs
        </p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" @click="refreshRFPs">
          <RefreshCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }" />
          Refresh
        </Button>
        <Button as-child class="gradient-primary">
          <a href="/rfp-creation">
            <Plus class="h-4 w-4 mr-2" />
            Create New RFP
          </a>
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <Card class="phase-card">
      <div class="p-6">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              placeholder="Search RFPs by title, number, or description..."
              class="w-full"
            />
          </div>
          <div class="flex gap-2">
            <Select v-model="statusFilter">
              <SelectTrigger class="w-40">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="in_review">In Review</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="submission_open">Submission Open</SelectItem>
                <SelectItem value="evaluation">Evaluation</SelectItem>
                <SelectItem value="awarded">Awarded</SelectItem>
              </SelectContent>
            </Select>
            <Select v-model="typeFilter">
              <SelectTrigger class="w-40">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Types</SelectItem>
                <SelectItem value="GOODS">Goods</SelectItem>
                <SelectItem value="SERVICES">Services</SelectItem>
                <SelectItem value="TECHNOLOGY">Technology</SelectItem>
                <SelectItem value="CONSULTING">Consulting</SelectItem>
                <SelectItem value="SOFTWARE">Software</SelectItem>
                <SelectItem value="INFRASTRUCTURE">Infrastructure</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </Card>

    <!-- RFP List -->
    <div class="grid gap-6">
      <Card v-for="rfp in filteredRFPs" :key="rfp.id" class="phase-card">
        <div class="p-6">
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <!-- RFP Info -->
            <div class="flex-1 space-y-3">
              <div class="flex items-center gap-3 flex-wrap">
                <h3 class="text-lg font-semibold">{{ rfp.title }}</h3>
                <Badge :class="getStatusColor(rfp.status)">
                  {{ formatStatus(rfp.status) }}
                </Badge>
                <Badge variant="outline">{{ rfp.type }}</Badge>
              </div>
              
              <div class="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                <span class="font-medium">{{ rfp.rfp_number }}</span>
                <span class="flex items-center gap-1">
                  <Calendar class="h-3 w-3" />
                  {{ formatDate(rfp.createdDate) }}
                </span>
                <span class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ formatDate(rfp.deadline) }}
                </span>
                <span v-if="rfp.budgetMin || rfp.budgetMax" class="flex items-center gap-1">
                  <DollarSign class="h-3 w-3" />
                  {{ formatBudget(rfp.budgetMin, rfp.budgetMax) }}
                </span>
              </div>
              
              <p class="text-sm text-muted-foreground line-clamp-2">
                {{ rfp.description }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex flex-col sm:flex-row gap-2">
              <Button variant="outline" size="sm" @click="downloadRFPFromList(rfp, 'pdf')" :disabled="downloadLoading">
                <Download class="h-4 w-4 mr-2" />
                PDF
              </Button>
              <Button variant="outline" size="sm" @click="downloadRFPFromList(rfp, 'word')" :disabled="downloadLoading">
                <FileText class="h-4 w-4 mr-2" />
                DOC
              </Button>
              <Button variant="outline" size="sm" @click="shareRFP(rfp)">
                <Share2 class="h-4 w-4 mr-2" />
                Share
              </Button>
              <Button variant="outline" size="sm" @click="viewRFP(rfp)">
                <Eye class="h-4 w-4 mr-2" />
                View
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                @click="goToConsensusAndAward(rfp)"
                class="bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100"
              >
                <Target class="h-4 w-4 mr-2" />
                Consensus & Award
              </Button>
              <!-- Edit button disabled - RFPEditModal component not available -->
              <!-- <Button 
                v-if="canEditRFP(rfp)" 
                variant="outline" 
                size="sm" 
                @click="editRFP(rfp)"
                class="bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100"
              >
                <Edit class="h-4 w-4 mr-2" />
                Edit
              </Button> -->
            </div>
          </div>
        </div>
      </Card>

      <!-- Empty State -->
      <Card v-if="filteredRFPs.length === 0 && !loading" class="phase-card">
        <div class="p-12 text-center">
          <FileText class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No RFPs Found</h3>
          <p class="text-muted-foreground mb-4">
            {{ searchQuery || statusFilter || typeFilter ? 'No RFPs match your current filters.' : 'You haven\'t created any RFPs yet.' }}
          </p>
          <Button as-child>
            <a href="/rfp-creation">
              <Plus class="h-4 w-4 mr-2" />
              Create Your First RFP
            </a>
          </Button>
        </div>
      </Card>

      <!-- Loading State -->
      <Card v-if="loading" class="phase-card">
        <div class="p-12 text-center">
          <RefreshCw class="h-8 w-8 mx-auto text-muted-foreground mb-4 animate-spin" />
          <p class="text-muted-foreground">Loading RFPs...</p>
        </div>
      </Card>
    </div>

    <!-- Document Viewer Modal removed - not needed for RFP payload only view -->

    <!-- Share Modal -->
    <Dialog v-model:open="showShareModal">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>Share RFP</DialogTitle>
          <DialogDescription>
            Generate an open invitation link for vendors to submit proposals for this RFP
          </DialogDescription>
        </DialogHeader>
        
        <div class="space-y-4">
          <div v-if="shareLoading" class="text-center py-4">
            <RefreshCw class="h-6 w-6 mx-auto text-muted-foreground mb-2 animate-spin" />
            <p class="text-muted-foreground">Generating open invitation link...</p>
          </div>
          
          <div v-else-if="publicLink" class="space-y-3">
            <div>
              <Label class="text-sm font-medium">Open Invitation Link</Label>
              <div class="flex gap-2 mt-1">
                <Input :value="publicLink" readonly class="flex-1" />
                <Button variant="outline" size="sm" @click="copyToClipboard(publicLink)">
                  <Copy class="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div class="text-sm text-muted-foreground">
              <p>This open invitation link allows any vendor to access the RFP portal and submit proposals without requiring a specific invitation.</p>
            </div>
          </div>
          
          <div v-else class="text-center py-4">
            <AlertCircle class="h-8 w-8 mx-auto text-destructive mb-2" />
            <p class="text-destructive">Failed to generate open invitation link</p>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" @click="showShareModal = false">Close</Button>
          <Button v-if="publicLink" @click="copyToClipboard(publicLink)">
            <Copy class="h-4 w-4 mr-2" />
            Copy Link
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- RFP Preview Modal -->
    <Dialog v-model:open="showRFPPreviewModal">
      <DialogContent class="max-w-7xl max-h-[95vh] p-0">
        <div class="flex flex-col h-full">
          <!-- Header -->
          <div class="flex-shrink-0 border-b border-gray-200 bg-gray-50 px-6 py-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">{{ selectedRFP?.title }}</h2>
                <p class="text-sm text-gray-600 mt-1">{{ selectedRFP?.rfp_number || 'RFP Details' }}</p>
              </div>
              <div class="flex items-center gap-3">
                <Badge :class="getStatusColor(selectedRFP?.status)" class="text-sm px-3 py-1">
                  {{ formatStatus(selectedRFP?.status) }}
                </Badge>
                <Button variant="outline" size="sm" @click="showRFPPreviewModal = false">
                  <X class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto">
            <div v-if="rfpPreviewLoading" class="flex items-center justify-center h-64">
              <div class="text-center">
                <RefreshCw class="h-8 w-8 mx-auto text-gray-400 mb-4 animate-spin" />
                <p class="text-gray-600">Loading RFP details...</p>
              </div>
            </div>
            
            <div v-else-if="rfpFullDetails" class="p-6 space-y-8">
              <!-- Overview Section -->
              <div class="bg-white rounded-xl border border-gray-200 p-8">
                <div class="flex items-center gap-3 mb-6">
                  <div class="p-2 bg-blue-100 rounded-lg">
                    <FileText class="h-6 w-6 text-blue-600" />
                  </div>
                  <h3 class="text-xl font-semibold text-gray-900">Overview</h3>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <!-- Basic Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Basic Information</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">RFP Number</Label>
                        <p class="text-sm font-medium text-gray-900 mt-1">{{ rfpFullDetails.rfp_number || 'Not assigned' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Type</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.rfp_type }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Category</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.category || 'Not specified' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Version</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.version_number }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Budget Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Budget Information</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Estimated Value</Label>
                        <p class="text-sm font-medium text-gray-900 mt-1">
                          {{ rfpFullDetails.estimated_value ? `$${Number(rfpFullDetails.estimated_value).toLocaleString()}` : 'Not specified' }}
                        </p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Budget Range</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatBudget(rfpFullDetails.budget_range_min, rfpFullDetails.budget_range_max) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Currency</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.currency }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Timeline Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Timeline</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Issue Date</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.issue_date) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Submission Deadline</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.submission_deadline) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Evaluation End</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.evaluation_period_end) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Award Date</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.award_date) }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Description -->
                <div class="mt-8 pt-6 border-t border-gray-100">
                  <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Description</Label>
                  <p class="text-sm text-gray-700 mt-2 leading-relaxed">{{ rfpFullDetails.description }}</p>
                </div>
              </div>

              <!-- Configuration Section -->
              <div class="bg-white rounded-xl border border-gray-200 p-8">
                <div class="flex items-center gap-3 mb-6">
                  <div class="p-2 bg-green-100 rounded-lg">
                    <Target class="h-6 w-6 text-green-600" />
                  </div>
                  <h3 class="text-xl font-semibold text-gray-900">Configuration & Workflow</h3>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Evaluation Settings</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Evaluation Method</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.evaluation_method?.replace('_', ' ').toUpperCase() || 'Not specified' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Criticality Level</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.criticality_level?.toUpperCase() || 'Not specified' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Geographical Scope</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.geographical_scope || 'Not specified' }}</p>
                      </div>
                    </div>
                  </div>

                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Workflow Settings</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Auto Publish</Label>
                        <Badge :class="rfpFullDetails.auto_publish ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="mt-1">
                          {{ rfpFullDetails.auto_publish ? 'Enabled' : 'Disabled' }}
                        </Badge>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Late Submissions</Label>
                        <Badge :class="rfpFullDetails.allow_late_submissions ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="mt-1">
                          {{ rfpFullDetails.allow_late_submissions ? 'Allowed' : 'Not Allowed' }}
                        </Badge>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Approval Workflow ID</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.approval_workflow_id || 'Not specified' }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- JSON Data Section -->
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Compliance Requirements -->
                <div v-if="rfpFullDetails.compliance_requirements" class="bg-white rounded-xl border border-gray-200 p-8">
                  <div class="flex items-center gap-3 mb-6">
                    <div class="p-2 bg-purple-100 rounded-lg">
                      <FileText class="h-6 w-6 text-purple-600" />
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900">Compliance Requirements</h3>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                    <pre class="text-xs text-gray-700 whitespace-pre-wrap">{{ JSON.stringify(rfpFullDetails.compliance_requirements, null, 2) }}</pre>
                  </div>
                </div>

                <!-- Custom Fields -->
                <div v-if="rfpFullDetails.custom_fields" class="bg-white rounded-xl border border-gray-200 p-8">
                  <div class="flex items-center gap-3 mb-6">
                    <div class="p-2 bg-orange-100 rounded-lg">
                      <FileText class="h-6 w-6 text-orange-600" />
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900">Custom Fields</h3>
                  </div>
                  <div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                    <pre class="text-xs text-gray-700 whitespace-pre-wrap">{{ JSON.stringify(rfpFullDetails.custom_fields, null, 2) }}</pre>
                  </div>
                </div>
              </div>

              <!-- Documents Section -->
              <div v-if="rfpFullDetails.documents && Array.isArray(rfpFullDetails.documents) && rfpFullDetails.documents.length > 0" class="bg-white rounded-xl border border-gray-200 p-8">
                <div class="flex items-center gap-3 mb-6">
                  <div class="p-2 bg-indigo-100 rounded-lg">
                    <FileText class="h-6 w-6 text-indigo-600" />
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900">Document References</h3>
                  <Badge variant="outline" class="ml-2">{{ rfpFullDetails.documents.length }} documents</Badge>
                </div>
                <div class="bg-gray-50 rounded-lg p-4">
                  <p class="text-sm text-gray-600 mb-3">Document IDs stored in this RFP:</p>
                  <div class="flex flex-wrap gap-2">
                    <Badge v-for="docId in rfpFullDetails.documents" :key="docId" variant="outline" class="bg-white">
                      {{ docId }}
                    </Badge>
                  </div>
                </div>
              </div>

              <!-- Award Information -->
              <div v-if="rfpFullDetails.final_evaluation_score || rfpFullDetails.award_justification" class="bg-white rounded-xl border border-gray-200 p-8">
                <div class="flex items-center gap-3 mb-6">
                  <div class="p-2 bg-yellow-100 rounded-lg">
                    <Target class="h-6 w-6 text-yellow-600" />
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900">Award Information</h3>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div class="space-y-4">
                    <div>
                      <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Final Evaluation Score</Label>
                      <p class="text-lg font-semibold text-gray-900 mt-1">{{ rfpFullDetails.final_evaluation_score || 'Not available' }}</p>
                    </div>
                    <div>
                      <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Award Decision Date</Label>
                      <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.award_decision_date) }}</p>
                    </div>
                  </div>
                  <div v-if="rfpFullDetails.award_justification" class="space-y-4">
                    <div>
                      <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Award Justification</Label>
                      <p class="text-sm text-gray-700 mt-2 leading-relaxed">{{ rfpFullDetails.award_justification }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- System Information -->
              <div class="bg-gray-50 rounded-xl border border-gray-200 p-8">
                <div class="flex items-center gap-3 mb-6">
                  <div class="p-2 bg-gray-100 rounded-lg">
                    <Clock class="h-6 w-6 text-gray-600" />
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900">System Information</h3>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-200 pb-2">Timestamps</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Created At</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.created_at) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Updated At</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfpFullDetails.updated_at) }}</p>
                      </div>
                    </div>
                  </div>

                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-200 pb-2">User Information</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Created By</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.created_by || 'Unknown' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Approved By</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.approved_by || 'Not approved' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Primary Reviewer</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.primary_reviewer_id || 'Not assigned' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Executive Reviewer</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfpFullDetails.executive_reviewer_id || 'Not assigned' }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="flex items-center justify-center h-64">
              <div class="text-center">
                <AlertCircle class="h-8 w-8 mx-auto text-red-400 mb-4" />
                <p class="text-red-600 font-medium">Failed to load RFP details</p>
                <p class="text-sm text-gray-500 mt-1">Please try again or contact support</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex-shrink-0 border-t border-gray-200 bg-gray-50 px-6 py-4">
            <div class="flex items-center justify-between">
              <div class="text-sm text-gray-500">
                RFP ID: {{ rfpFullDetails?.rfp_id || 'N/A' }}
              </div>
              <div class="flex items-center gap-3">
                <Button variant="outline" @click="showRFPPreviewModal = false">
                  Close
                </Button>
                <Button v-if="rfpFullDetails" @click="copyRFPData" class="bg-blue-600 hover:bg-blue-700">
                  <Copy class="h-4 w-4 mr-2" />
                  Copy RFP Data
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <!-- RFP Edit Modal - Component not available -->
    <!-- <RFPEditModal
      v-if="showRFPEditModal"
      :rfp-id="selectedRFPForEdit?.id"
      :change-request="changeRequestForEdit"
      @close="closeEditModal"
      @saved="handleRFPSaved"
    /> -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRFPStore } from '@/store/index_rfp'
import { rfpUseToast } from '@/composables/rfpUseToast'
import { useNotifications } from '@/composables/useNotifications'
import { useRfpApi } from '@/composables/useRfpApi'
import loggingService from '@/services/loggingService'

// Components
import Card from '@/components_rfp/Card.vue'
import Button from '@/components_rfp/Button.vue'
import Badge from '@/components_rfp/rfpBadge.vue'
import Input from '@/components_rfp/ui/Input.vue'
import Select from '@/components_rfp/ui/Select.vue'
import SelectContent from '@/components_rfp/ui/SelectContent.vue'
import SelectItem from '@/components_rfp/ui/SelectItem.vue'
import SelectTrigger from '@/components_rfp/ui/SelectTrigger.vue'
import SelectValue from '@/components_rfp/ui/SelectValue.vue'
import Dialog from '@/components_rfp/ui/Dialog.vue'
import DialogContent from '@/components_rfp/ui/DialogContent.vue'
import DialogDescription from '@/components_rfp/ui/DialogDescription.vue'
import DialogFooter from '@/components_rfp/ui/DialogFooter.vue'
import DialogHeader from '@/components_rfp/ui/DialogHeader.vue'
import DialogTitle from '@/components_rfp/ui/DialogTitle.vue'
import Label from '@/components_rfp/ui/Label.vue'
// import RFPEditModal from '@/components_rfp/RFPEditModal.vue' // Component not found

// Icons
import {
  FileText,
  Share2,
  Eye,
  Download,
  Copy,
  RefreshCw,
  Plus,
  Calendar,
  Clock,
  DollarSign,
  AlertCircle,
  Target,
  Building2,
  X,
  Edit,
  AlertTriangle
} from 'lucide-vue-next'

// Store and composables
const rfpStore = useRFPStore()
const { success, error: toastError } = rfpUseToast()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// Selected RFP for preview
const selectedRFP = ref(null)

// Share modal
const showShareModal = ref(false)
const publicLink = ref('')
const shareLoading = ref(false)

// RFP Preview modal
const showRFPPreviewModal = ref(false)
const rfpFullDetails = ref(null)
const rfpPreviewLoading = ref(false)
const downloadLoading = ref(false)

// RFP Edit modal
const showRFPEditModal = ref(false)
const selectedRFPForEdit = ref(null)
const changeRequestForEdit = ref(null)

// Computed properties
const filteredRFPs = computed(() => {
  let filtered = rfpStore.rfps

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(rfp => 
      rfp.title.toLowerCase().includes(query) ||
      rfp.rfp_number?.toLowerCase().includes(query) ||
      rfp.description?.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value) {
    filtered = filtered.filter(rfp => rfp.status === statusFilter.value)
  }

  // Filter by type
  if (typeFilter.value) {
    filtered = filtered.filter(rfp => rfp.rfp_type === typeFilter.value)
  }

  return filtered
})

// Methods
const refreshRFPs = async () => {
  loading.value = true
  try {
    await rfpStore.fetchRFPs()
    success('RFPs refreshed successfully')
    
    // Show success notification
    await showSuccess('RFPs Refreshed', 'RFP list has been refreshed successfully.', {
      action: 'rfp_list_refreshed',
      count: rfpStore.rfps.length
    })
  } catch (error) {
    console.error('Error refreshing RFPs:', error)
    toastError('Failed to refresh RFPs')
    
    // Show error notification
    await showError('Refresh Failed', 'Failed to refresh RFP list. Please try again.', {
      action: 'rfp_list_refresh_failed',
      error_message: error.message
    })
  } finally {
    loading.value = false
  }
}

// viewDocuments function removed - not needed for RFP payload only view

const shareRFP = async (rfp) => {
  selectedRFP.value = rfp
  showShareModal.value = true
  shareLoading.value = true
  publicLink.value = ''
  
  try {
    // Generate open RFP invitation link using the new format
    const baseUrl = 'http://localhost:3000' // Frontend base URL
    const openRfpUrl = `${baseUrl}/submit/open?rfpId=${rfp.id}`
    
    // Also try to generate the invitation record in the backend
    try {
      const { getAuthHeaders } = useRfpApi()
      const response = await fetch('http://localhost:8000/api/v1/generate-open-invitation/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          rfpId: rfp.id
        })
      })
      
      const data = await response.json()
      if (data.success && data.invitation) {
        // Use the backend-generated URL if available
        publicLink.value = data.invitation.invitation_url
      } else {
        // Fallback to frontend-generated URL
        publicLink.value = openRfpUrl
      }
    } catch (backendError) {
      console.warn('Backend invitation generation failed, using frontend URL:', backendError)
      // Fallback to frontend-generated URL
      publicLink.value = openRfpUrl
    }
    
  } catch (error) {
    console.error('Error generating open RFP link:', error)
    toastError('Failed to generate open RFP link')
  } finally {
    shareLoading.value = false
  }
}

const viewRFP = async (rfp) => {
  selectedRFP.value = rfp
  showRFPPreviewModal.value = true
  rfpPreviewLoading.value = true
  rfpFullDetails.value = null
  
  try {
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`http://localhost:8000/api/v1/rfps/${rfp.id}/get_full_details/`, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error Response:', errorText)
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json()
    
    if (data.success) {
      rfpFullDetails.value = data.rfp
    } else {
      toastError('Failed to load RFP details')
    }
  } catch (error) {
    console.error('Error loading RFP details:', error)
    toastError('Failed to load RFP details')
  } finally {
    rfpPreviewLoading.value = false
  }
}

// Document functions removed since we're only showing document IDs from the RFP payload

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    success('Link copied to clipboard')
  } catch (error) {
    console.error('Error copying to clipboard:', error)
    toastError('Failed to copy link')
  }
}

const copyRFPData = async () => {
  if (!rfpFullDetails.value) return
  
  try {
    const rfpDataString = JSON.stringify(rfpFullDetails.value, null, 2)
    await navigator.clipboard.writeText(rfpDataString)
    success('RFP data copied to clipboard')
  } catch (error) {
    console.error('Error copying RFP data:', error)
    toastError('Failed to copy RFP data')
  }
}

// RFP Editing Methods
const canEditRFP = (rfp) => {
  // Only allow editing if there are change requests or if RFP is in draft/review status
  const editableStatuses = ['draft', 'in_review']
  return editableStatuses.includes(rfp.status) || hasChangeRequests(rfp)
}

const hasChangeRequests = (rfp) => {
  // Check if there are any change requests for this RFP
  // This would typically come from the approval workflow system
  return rfp.has_change_requests || rfp.change_requests_count > 0
}

const editRFP = async (rfp) => {
  selectedRFPForEdit.value = rfp
  changeRequestForEdit.value = null
  
  // Check if there are specific change requests for this RFP
  try {
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`http://localhost:8000/api/v1/rfp-change-requests/${rfp.id}/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success && data.change_requests && data.change_requests.length > 0) {
        // Get the most recent change request
        changeRequestForEdit.value = data.change_requests[0]
      }
    }
  } catch (error) {
    console.log('No change requests found or error fetching them:', error)
  }
  
  showRFPEditModal.value = true
}

const closeEditModal = () => {
  showRFPEditModal.value = false
  selectedRFPForEdit.value = null
  changeRequestForEdit.value = null
}

const handleRFPSaved = (updatedRFP) => {
  // Refresh the RFP list to show updated data
  refreshRFPs()
  showRFPEditModal.value = false
  selectedRFPForEdit.value = null
  changeRequestForEdit.value = null
}

const goToConsensusAndAward = (rfp) => {
  const rfpId = rfp.id || rfp.rfp_id
  if (rfpId) {
    window.location.href = `/rfp-consensus?rfp_id=${rfpId}`
  } else {
    showError('Unable to navigate: RFP ID not found')
  }
}

const downloadRFPFromList = async (rfp, format) => {
  downloadLoading.value = true
  
  try {
    const rfpId = rfp.id
    const endpoint = format === 'pdf' 
      ? `http://localhost:8000/api/v1/rfps/${rfpId}/download/pdf/`
      : `http://localhost:8000/api/v1/rfps/${rfpId}/download/word/`
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: getAuthHeaders()
      // Remove Accept header to let backend handle content type
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`Download error response:`, errorText)
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
    }
    
    // Get the filename from Content-Disposition header or create one
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `${rfp.rfp_number || rfp.title || 'RFP'}_${new Date().toISOString().split('T')[0]}.${format === 'pdf' ? 'pdf' : 'docx'}`
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    
    // Create blob and download
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    success(`${format.toUpperCase()} document downloaded successfully`)
    
  } catch (error) {
    console.error(`Error downloading ${format.toUpperCase()}:`, error)
    toastError(`Failed to download ${format.toUpperCase()} document`)
  } finally {
    downloadLoading.value = false
  }
}

// Helper functions
const formatStatus = (status) => {
  const statusMap = {
    'draft': 'Draft',
    'in_review': 'In Review',
    'published': 'Published',
    'submission_open': 'Submission Open',
    'evaluation': 'Evaluation',
    'awarded': 'Awarded',
    'cancelled': 'Cancelled',
    'archived': 'Archived'
  }
  return statusMap[status] || status
}

const getStatusColor = (status) => {
  switch (status) {
    case 'draft': return 'bg-gray-100 text-gray-800'
    case 'in_review': return 'bg-blue-100 text-blue-800'
    case 'published': return 'bg-green-100 text-green-800'
    case 'submission_open': return 'bg-purple-100 text-purple-800'
    case 'evaluation': return 'bg-yellow-100 text-yellow-800'
    case 'awarded': return 'bg-emerald-100 text-emerald-800'
    case 'cancelled': return 'bg-red-100 text-red-800'
    case 'archived': return 'bg-gray-100 text-gray-600'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Not set'
  return new Date(dateString).toLocaleDateString()
}

const formatBudget = (min, max) => {
  if (!min && !max) return 'Not specified'
  if (min && max) return `$${Number(min).toLocaleString()} - $${Number(max).toLocaleString()}`
  if (min) return `$${Number(min).toLocaleString()}+`
  if (max) return `Up to $${Number(max).toLocaleString()}`
  return 'Not specified'
}

// formatFileSize function removed - not needed for RFP payload only view

// Test backend connectivity
const testBackendConnection = async () => {
  try {
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch('http://localhost:8000/api/v1/rfps/', {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    console.log('Backend connection test:', response.status, response.statusText)
    return response.ok
  } catch (error) {
    console.error('Backend connection failed:', error)
    return false
  }
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('RFP', 'RFP List')
  loading.value = true
  try {
    // Test backend connection first
    const isBackendAvailable = await testBackendConnection()
    if (!isBackendAvailable) {
      toastError('Backend server is not available. Please ensure the Django server is running on port 8000.')
      return
    }
    
    await rfpStore.fetchRFPs()
    
    // Check for edit parameters in URL
    const urlParams = new URLSearchParams(window.location.search)
    const editRfpId = urlParams.get('edit')
    const changeRequestParam = urlParams.get('changeRequest')
    
    if (editRfpId) {
      // Find the RFP to edit
      const rfpToEdit = rfpStore.rfps.find(rfp => rfp.id == editRfpId)
      if (rfpToEdit) {
        selectedRFPForEdit.value = rfpToEdit
        
        // Parse change request if provided
        if (changeRequestParam) {
          try {
            changeRequestForEdit.value = JSON.parse(decodeURIComponent(changeRequestParam))
          } catch (e) {
            console.error('Error parsing change request:', e)
          }
        }
        
        showRFPEditModal.value = true
        
        // Clean up URL parameters
        const newUrl = window.location.pathname
        window.history.replaceState({}, document.title, newUrl)
      }
    }
  } catch (error) {
    console.error('Error loading RFPs:', error)
    toastError('Failed to load RFPs. Please check if the backend server is running.')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.phase-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow;
}

.text-muted-foreground {
  @apply text-gray-500;
}

.text-destructive {
  @apply text-red-600;
}

.gradient-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
