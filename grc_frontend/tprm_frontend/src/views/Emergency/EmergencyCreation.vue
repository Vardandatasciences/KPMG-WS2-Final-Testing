<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
    <div class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <!-- Header -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex flex-col gap-4">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-lg bg-gradient-to-br from-red-600 to-rose-600 flex items-center justify-center">
                <Icons name="exclamation-triangle" class="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-gray-900">Emergency Procurement Creation</h1>
                <div v-if="lastSaved" class="flex items-center gap-1 text-xs sm:text-sm text-gray-500 mt-1">
                  <Icons v-if="isAutoSaving" name="clock" class="h-3 w-3 animate-spin" />
                  <Icons v-else name="check-circle" class="h-3 w-3 text-green-500" />
                  <span v-if="isAutoSaving">Saving...</span>
                  <span v-else>Saved {{ formatTime(lastSaved) }}</span>
                </div>
              </div>
            </div>
        
            <!-- Action Buttons -->
            <div class="flex flex-wrap items-center gap-2">
              <button 
                v-if="hasExistingDraft" 
                @click="clearDraftAndStartFresh" 
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-orange-200 bg-orange-50 text-orange-700 hover:bg-orange-100 hover:border-orange-300 transition-all text-sm font-medium shadow-sm"
              >
                <Icons name="refresh-cw" class="h-4 w-4 mr-1.5" />
                <span>Reset</span>
              </button>
              
              <button
                @click="loadSampleData"
                :disabled="isSubmitting || isGeneratingDocument || isUploadingDocuments"
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 hover:border-indigo-300 transition-all text-sm font-medium shadow-sm"
              >
                <Icons name="wand-2" class="h-4 w-4 mr-1.5" />
                <span>Load Sample</span>
              </button>
              
              <button 
                @click="handleSaveDraft" 
                :disabled="isSubmitting"
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium shadow-sm"
              >
                <Icons v-if="isSubmitting && !isFormValid" name="loader" class="h-4 w-4 mr-1.5 animate-spin" />
                <Icons v-else name="save" class="h-4 w-4 mr-1.5" />
                <span>Save Draft</span>
              </button>
              
              <button 
                @click="handleProceedToApprovalWorkflow" 
                :disabled="isSubmitting || isUploadingDocuments || !isFormValid"
                class="inline-flex items-center px-5 h-10 rounded-lg bg-red-600 text-white hover:bg-red-700 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold shadow-md"
              >
                <Icons v-if="(isSubmitting || isUploadingDocuments) && isFormValid" name="loader" class="h-4 w-4 mr-2 animate-spin" />
                <Icons v-else name="arrow-right" class="h-4 w-4 mr-2" />
                <span v-if="isUploadingDocuments">Uploading...</span>
                <span v-else-if="isSubmitting">Processing...</span>
                <span v-else>{{ formData.autoApprove ? 'Submit & Auto-Approve' : 'Proceed to Approval' }}</span>
              </button>
            </div>
          </div>
          
          <p class="text-gray-600 text-sm mt-2">
            Create an emergency procurement request for urgent situations requiring immediate action.
          </p>
        </div>
      </div>

      <!-- Form Container -->
      <div class="space-y-6">
        <!-- Tabs Navigation -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div class="border-b border-gray-200 bg-gray-50/50">
            <nav class="flex overflow-x-auto" aria-label="Tabs">
              <div class="flex w-full px-2 tab-container">
                <button
                  v-for="(tab, index) in visibleTabs"
                  :key="tab.value"
                  type="button"
                  @click="activeTab = tab.value"
                  :class="[
                    'group relative flex items-center gap-2 px-2 sm:px-3 py-2.5 sm:py-3 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 tab-button',
                    activeTab === tab.value
                      ? 'text-red-700 border-b-2 border-red-600 bg-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-white/50 border-b-2 border-transparent'
                  ]"
                >
                  <span
                    class="flex items-center justify-center h-6 w-6 sm:h-7 sm:w-7 rounded-full text-xs font-bold transition-all duration-200 shrink-0 tab-number"
                    :class="activeTab === tab.value
                      ? 'bg-red-600 text-white shadow-md'
                      : 'bg-white border-2 border-gray-300 text-gray-600 group-hover:border-gray-400'"
                  >
                    {{ index + 1 }}
                  </span>
                  <span class="flex flex-col items-start min-w-0 flex-1 overflow-hidden tab-text">
                    <span class="font-semibold leading-tight truncate w-full text-xs sm:text-sm tab-label">{{ tab.label }}</span>
                    <span class="text-[10px] sm:text-xs font-normal text-gray-500 leading-tight truncate w-full tab-description">
                      {{ tab.description }}
                    </span>
                  </span>
                </button>
              </div>
            </nav>
          </div>
        </div>

        <!-- Basic Information -->
        <Card
          v-show="activeTab === 'basic'"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader class="bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 rounded-t-xl">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-lg bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center shadow-sm">
                <Icons name="exclamation-triangle" class="h-5 w-5 text-white" />
              </div>
              <div>
                <CardTitle class="text-lg font-semibold text-gray-900">Basic Information</CardTitle>
                <CardDescription class="text-sm text-gray-600 mt-0.5">
                  Define the core details of your emergency procurement
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="emergencyNumber">
                  <span>Emergency Procurement Number *</span>
                </Label>
                <Input
                  id="emergencyNumber"
                  placeholder="e.g., EMERGENCY-2024-001"
                  v-model="formData.emergencyNumber"
                />
              </div>
              <div class="space-y-2">
                <Label html-for="title">
                  <span>Title *</span>
                </Label>
                <Input
                  id="title"
                  placeholder="e.g., Emergency Server Replacement"
                  v-model="formData.title"
                />
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="type">
                  <span>Emergency Type *</span>
                </Label>
                <Select v-model="formData.type" :disabled="loadingEmergencyTypes">
                  <option value="" disabled>Select type</option>
                  <option v-for="emergencyType in emergencyTypes" :key="emergencyType" :value="emergencyType">
                    {{ emergencyType }}
                  </option>
                </Select>
                <p v-if="loadingEmergencyTypes" class="text-xs text-muted-foreground">Loading emergency types...</p>
              </div>
              <div class="space-y-2">
                <Label html-for="emergencyTypeCategory">
                  <span>Emergency Category *</span>
                </Label>
                <Select v-model="formData.emergencyTypeCategory">
                  <option value="" disabled>Select category</option>
                  <option value="Natural Disaster">Natural Disaster</option>
                  <option value="System Failure">System Failure</option>
                  <option value="Security Breach">Security Breach</option>
                  <option value="Supply Chain Disruption">Supply Chain Disruption</option>
                  <option value="Regulatory Compliance">Regulatory Compliance</option>
                  <option value="Other">Other</option>
                </Select>
              </div>
            </div>

            <div class="space-y-2">
              <Label html-for="description">
                <span>Description *</span>
              </Label>
              <Textarea
                id="description"
                placeholder="Provide a detailed description of the emergency procurement requirements..."
                :rows="4"
                v-model="formData.description"
              />
            </div>

            <div class="space-y-2">
              <Label html-for="emergencyJustification">
                <span>Emergency Justification *</span>
              </Label>
              <Textarea
                id="emergencyJustification"
                placeholder="Explain why this is an emergency procurement and why normal procurement processes cannot be followed..."
                :rows="3"
                v-model="formData.emergencyJustification"
              />
              <p class="text-xs text-red-600 font-medium">Required for audit and compliance purposes</p>
            </div>

            <div class="space-y-2">
              <Label html-for="impactDescription">
                <span>Impact Description *</span>
              </Label>
              <Textarea
                id="impactDescription"
                placeholder="Describe the impact if this procurement is not completed immediately..."
                :rows="3"
                v-model="formData.impactDescription"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="issueDate">
                  <span>Issue Date *</span>
                </Label>
                <Input
                  id="issueDate"
                  type="date"
                  v-model="formData.issueDate"
                />
              </div>
              <div class="space-y-2">
                <Label html-for="deadline">
                  <span>Submission Deadline *</span>
                </Label>
                <input
                  id="deadline"
                  type="datetime-local"
                  v-model="formData.deadline"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="urgencyLevel">
                  <span>Urgency Level *</span>
                </Label>
                <Select v-model="formData.urgencyLevel">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </Select>
              </div>
              <div class="space-y-2">
                <Label html-for="requiredDeliveryDate">
                  <span>Required Delivery Date *</span>
                </Label>
                <Input
                  id="requiredDeliveryDate"
                  type="date"
                  v-model="formData.requiredDeliveryDate"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Budget Section -->
        <Card
          v-show="activeTab === 'budget'"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="dollar-sign" class="h-5 w-5 text-primary" />
              <CardTitle>Budget & Financials</CardTitle>
            </div>
            <CardDescription>
              Set budget parameters for emergency procurement
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div v-if="!hiddenFields.estimatedValue" class="space-y-2">
                <Label html-for="estimatedValue">Estimated Value</Label>
                <Input
                  id="estimatedValue"
                  type="number"
                  placeholder="100,000"
                  v-model="formData.estimatedValue"
                />
              </div>
              <div v-if="!hiddenFields.currency" class="space-y-2">
                <Label html-for="currency">Currency</Label>
                <Select v-model="formData.currency">
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="INR">INR</option>
                </Select>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label html-for="budgetMin">Budget Range (Min)</Label>
                <Input
                  id="budgetMin"
                  type="number"
                  placeholder="80,000"
                  v-model="formData.budgetMin"
                />
              </div>
              <div class="space-y-2">
                <Label html-for="budgetMax">Budget Range (Max)</Label>
                <Input
                  id="budgetMax"
                  type="number"
                  placeholder="120,000"
                  v-model="formData.budgetMax"
                />
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label html-for="evaluationPeriodEnd">Evaluation Period End</Label>
                <Input
                  id="evaluationPeriodEnd"
                  type="date"
                  v-model="formData.evaluationPeriodEnd"
                />
              </div>
              <div class="space-y-2">
                <Label html-for="awardDate">Award Date</Label>
                <Input
                  id="awardDate"
                  type="date"
                  v-model="formData.awardDate"
                />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <!-- Documents Section -->
        <Card
          v-show="activeTab === 'documents'"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="upload" class="h-5 w-5 text-primary" />
              <CardTitle>Document Upload</CardTitle>
            </div>
            <CardDescription>
              Upload supporting documents for your emergency procurement
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <Label html-for="documentName">Document Name *</Label>
                  <Input
                    id="documentName"
                    placeholder="e.g., Emergency Report"
                    v-model="newDocument.name"
                  />
                </div>
                <div class="space-y-2">
                  <Label html-for="documentFile">Select File *</Label>
                  <input
                    id="documentFile"
                    type="file"
                    @change="handleFileSelect"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png"
                    class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </div>
              
              <div class="flex gap-2">
                <Button 
                  @click="addDocument" 
                  variant="outline" 
                  size="sm"
                  :disabled="!newDocument.name || !newDocument.file"
                >
                  <Icons name="plus" class="h-4 w-4 mr-2" />
                  Add Document
                </Button>
              </div>
            </div>

            <div v-if="uploadedDocuments.length > 0" class="space-y-3">
              <h4 class="text-sm font-semibold">Documents ({{ uploadedDocuments.length }})</h4>
              <div class="space-y-2">
                <div 
                  v-for="(doc, index) in uploadedDocuments" 
                  :key="`doc-${index}`"
                  class="flex items-center justify-between p-3 border border-border rounded-lg"
                >
                  <div class="flex items-center gap-3 flex-1">
                    <Icons name="file" class="h-4 w-4 text-gray-500" />
                    <div class="flex-1">
                      <p class="text-sm font-medium">{{ doc.name }}</p>
                      <p class="text-xs text-muted-foreground">{{ doc.fileName }} ({{ formatFileSize(doc.fileSize) }})</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    @click="removeDocument(index)"
                  >
                    <Icons name="trash2" class="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <!-- Evaluation Criteria -->
        <Card
          v-show="activeTab === 'criteria'"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="target" class="h-5 w-5 text-primary" />
              <CardTitle>Evaluation Criteria</CardTitle>
            </div>
            <CardDescription>
              Define how vendors will be evaluated (weights must total 100%)
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">Total Weight:</span>
                <Badge :variant="totalWeight === 100 ? 'default' : totalWeight > 100 ? 'destructive' : 'secondary'">
                  {{ totalWeight }}%
                </Badge>
                <span v-if="totalWeight !== 100" class="text-xs text-muted-foreground">
                  {{ totalWeight > 100 ? `(${totalWeight - 100}% over)` : `(${100 - totalWeight}% remaining)` }}
                </span>
              </div>
              <div class="flex gap-2">
                <Button @click="addCriterion" size="sm" variant="outline">
                  <Icons name="plus" class="h-4 w-4 mr-2" />
                  Add Criterion
                </Button>
                <Button 
                  v-if="totalWeight !== 100 && totalWeight > 0" 
                  @click="normalizeWeights" 
                  size="sm" 
                  variant="secondary"
                >
                  <Icons name="target" class="h-4 w-4 mr-2" />
                  Normalize to 100%
                </Button>
              </div>
            </div>

            <div class="space-y-3">
              <div v-for="(criterion, index) in criteria" :key="criterion.id" class="p-4 border border-border rounded-lg space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium">Criterion {{ index + 1 }}</span>
                  <Button
                    v-if="criteria.length > 1"
                    variant="ghost"
                    size="sm"
                    @click="removeCriterion(criterion.id)"
                  >
                    <Icons name="trash2" class="h-4 w-4" />
                  </Button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div class="space-y-2">
                    <Label>Name</Label>
                    <Input
                      placeholder="e.g., Response Time"
                      v-model="criterion.name"
                    />
                  </div>
                  <div class="space-y-2">
                    <Label>Weight (%)</Label>
                    <div class="relative">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        :value="criterion.weight"
                        @input="handleWeightChange(index, Number($event.target.value))"
                        :class="criterion.weight > 0 && totalWeight > 100 ? 'border-orange-300 bg-orange-50' : ''"
                      />
                    </div>
                  </div>
                </div>

                <div class="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    placeholder="Describe what this criterion evaluates..."
                    :rows="2"
                    v-model="criterion.description"
                  />
                </div>
                
                <div class="flex items-center space-x-2">
                  <Checkbox
                    :id="`veto-${criterion.id}`"
                    v-model="criterion.isVeto"
                  />
                  <Label :html-for="`veto-${criterion.id}`" class="text-sm">
                    Veto Criterion (failing this criterion eliminates the vendor)
                  </Label>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Process Settings -->
        <Card
          v-show="activeTab === 'process'"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="settings" class="h-5 w-5 text-primary" />
              <CardTitle>Process Settings</CardTitle>
            </div>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div v-if="!hiddenFields.criticalityLevel" class="space-y-2">
                <Label html-for="criticalityLevel">Criticality Level</Label>
                <Select v-model="formData.criticalityLevel">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </Select>
              </div>
              <div class="space-y-2">
                <Label html-for="evaluationMethod">Evaluation Method</Label>
                <Select v-model="formData.evaluationMethod">
                  <option value="weighted_scoring">Weighted Scoring</option>
                  <option value="lowest_price">Lowest Price</option>
                  <option value="best_value">Best Value</option>
                </Select>
              </div>
            </div>
            
            <div class="space-y-2">
              <Label html-for="geographicalScope">Geographical Scope</Label>
              <Input
                id="geographicalScope"
                placeholder="e.g., United States, Global, Europe"
                v-model="formData.geographicalScope"
              />
            </div>
            
            <div class="space-y-2">
              <Label html-for="complianceRequirements">Compliance Requirements</Label>
              <Textarea
                id="complianceRequirements"
                placeholder="Enter compliance requirements (comma-separated or one per line)..."
                :rows="3"
                v-model="formData.complianceRequirements"
              />
              <p class="text-xs text-gray-500">Enter requirements separated by commas or new lines</p>
            </div>
            
            <div class="space-y-2">
              <Label html-for="retentionExpiry">Data Retention Expiry</Label>
              <Input
                id="retentionExpiry"
                type="date"
                v-model="formData.retentionExpiry"
              />
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="flex items-center space-x-2">
                <Checkbox
                  id="allowLateSubmissions"
                  v-model="formData.allowLateSubmissions"
                />
                <Label html-for="allowLateSubmissions" class="text-sm">
                  Allow Late Submissions
                </Label>
              </div>
              <div v-if="!hiddenFields.autoApprove" class="flex items-center space-x-2">
                <Checkbox
                  id="autoApprove"
                  v-model="formData.autoApprove"
                />
                <Label html-for="autoApprove" class="text-sm">
                  Auto-approve (no approval workflow required)
                </Label>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Card from '@/components_rfp/ui/Card.vue'
import CardHeader from '@/components_rfp/ui/CardHeader.vue'
import CardTitle from '@/components_rfp/ui/CardTitle.vue'
import CardDescription from '@/components_rfp/ui/CardDescription.vue'
import CardContent from '@/components_rfp/ui/CardContent.vue'
import Button from '@/components_rfp/ui/Button.vue'
import Input from '@/components_rfp/ui/Input.vue'
import Label from '@/components_rfp/ui/Label.vue'
import Textarea from '@/components_rfp/ui/Textarea.vue'
import Select from '@/components_rfp/ui/Select.vue'
import Checkbox from '@/components_rfp/ui/Checkbox.vue'
import Badge from '@/components_rfp/ui/Badge.vue'
import Icons from '@/components_rfp/ui/Icons.vue'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'

const { success, error } = rfpUseToast()
const router = useRouter()
const { getAuthHeaders } = useRfpApi()

const API_BASE_URL = getTprmApiV1BaseUrl()

const lastSaved = ref<Date | null>(null)
const isAutoSaving = ref(false)
const isSubmitting = ref(false)
const isUploadingDocuments = ref(false)
const isGeneratingDocument = ref(false)

const formTabs = [
  { value: 'basic', label: 'Basic Setup', description: 'Core details & justification' },
  { value: 'documents', label: 'Documents', description: 'Upload files' },
  { value: 'budget', label: 'Budget & Financials', description: 'Financials' },
  { value: 'criteria', label: 'Evaluation Criteria', description: 'Weights & scoring' },
  { value: 'process', label: 'Process Settings', description: 'Configuration' }
]
const activeTab = ref(formTabs[0].value)
const hiddenTabs = ref<Set<string>>(new Set())
const visibleTabs = computed(() => formTabs.filter(tab => !hiddenTabs.value.has(tab.value)))

// Default Emergency Procurement types
const defaultEmergencyTypes = [
  'System Failure',
  'Security Breach',
  'Natural Disaster',
  'Critical Infrastructure Failure',
  'Data Loss',
  'Service Outage',
  'Equipment Failure',
  'Network Failure',
  'Power Outage',
  'Emergency Maintenance'
]

const emergencyTypes = ref<string[]>([...defaultEmergencyTypes])
const loadingEmergencyTypes = ref(false)

const hiddenFields = ref<Record<string, boolean>>({
  estimatedValue: false,
  currency: false,
  criticalityLevel: false,
  autoApprove: false
})

interface EvaluationCriteria {
  id: string
  name: string
  description: string
  weight: number
  isVeto: boolean
}

const criteria = ref<EvaluationCriteria[]>([])

const formData = ref({
  emergencyNumber: '',
  title: '',
  description: '',
  type: '',
  emergencyTypeCategory: '',
  emergencyJustification: '',
  impactDescription: '',
  urgencyLevel: 'high',
  requiredDeliveryDate: '',
  estimatedValue: '',
  currency: 'USD',
  budgetMin: '',
  budgetMax: '',
  issueDate: '',
  deadline: '',
  evaluationPeriodEnd: '',
  awardDate: '',
  criticalityLevel: 'high',
  evaluationMethod: 'weighted_scoring',
  geographicalScope: '',
  complianceRequirements: '',
  retentionExpiry: '',
  allowLateSubmissions: false,
  autoApprove: false,
  customFields: {} as Record<string, any>
})

const hasExistingDraft = computed(() => {
  const emergencyId = localStorage.getItem('current_emergency_id')
  return emergencyId && emergencyId !== 'null' && emergencyId !== ''
})

const totalWeight = computed(() => {
  return criteria.value.reduce((sum, criterion) => sum + criterion.weight, 0)
})

const addCriterion = () => {
  criteria.value.push({
    id: `criterion-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    name: '',
    description: '',
    weight: 0,
    isVeto: false
  })
}

const removeCriterion = (id: string) => {
  const index = criteria.value.findIndex(c => c.id === id)
  if (index > -1) {
    criteria.value.splice(index, 1)
  }
}

const handleWeightChange = (index: number, newWeight: number) => {
  if (newWeight < 0) newWeight = 0
  if (newWeight > 100) newWeight = 100
  criteria.value[index].weight = newWeight
}

const normalizeWeights = () => {
  if (totalWeight.value === 0) return
  const factor = 100 / totalWeight.value
  criteria.value.forEach(criterion => {
    criterion.weight = Math.round(criterion.weight * factor * 100) / 100
  })
}

const newDocument = ref({
  name: '',
  file: null,
  fileName: '',
  fileSize: 0
})

const uploadedDocuments = ref([])

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    newDocument.value.file = file
    newDocument.value.fileName = file.name
    newDocument.value.fileSize = file.size
  }
}

const addDocument = () => {
  if (!newDocument.value.name || !newDocument.value.file) {
    error('Validation Error', 'Please provide both document name and select a file.')
    return
  }
  uploadedDocuments.value.push({
    name: newDocument.value.name,
    file: newDocument.value.file,
    fileName: newDocument.value.fileName,
    fileSize: newDocument.value.fileSize,
    uploaded: false
  })
  newDocument.value = { name: '', file: null, fileName: '', fileSize: 0 }
  success('Document Added', 'Document added to upload queue.')
}

const removeDocument = (index) => {
  uploadedDocuments.value.splice(index, 1)
  success('Document Removed', 'Document removed from upload queue.')
}

const isFormValid = computed(() => {
  return !!(formData.value.title && formData.value.description && formData.value.type && formData.value.emergencyNumber && formData.value.deadline && formData.value.issueDate && formData.value.emergencyJustification && formData.value.impactDescription && formData.value.emergencyTypeCategory && formData.value.urgencyLevel && formData.value.requiredDeliveryDate)
})

const fetchEmergencyTypes = async () => {
  try {
    loadingEmergencyTypes.value = true
    const response = await axios.get(`${API_BASE_URL}/emergency-types/types/`, {
      headers: getAuthHeaders()
    })
    if (response.data && response.data.success && response.data.emergency_types && response.data.emergency_types.length > 0) {
      // Merge backend types with defaults, removing duplicates
      const backendTypes = response.data.emergency_types
      const merged = [...new Set([...defaultEmergencyTypes, ...backendTypes])]
      emergencyTypes.value = merged.sort()
    } else {
      // Use defaults if backend doesn't return types
      emergencyTypes.value = [...defaultEmergencyTypes]
    }
  } catch (err) {
    console.error('Error fetching Emergency types:', err)
    // Use defaults on error
    emergencyTypes.value = [...defaultEmergencyTypes]
  } finally {
    loadingEmergencyTypes.value = false
  }
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString()
}

const clearDraftAndStartFresh = () => {
  localStorage.removeItem('current_emergency_id')
  localStorage.removeItem('emergency_draft_current')
  resetFormData()
  success('Started Fresh', 'Starting with a clean form.')
}

const resetFormData = () => {
  formData.value = {
    emergencyNumber: '',
    title: '',
    description: '',
    type: '',
    emergencyTypeCategory: '',
    emergencyJustification: '',
    impactDescription: '',
    urgencyLevel: 'high',
    requiredDeliveryDate: '',
    estimatedValue: '',
    currency: 'USD',
    budgetMin: '',
    budgetMax: '',
    issueDate: '',
    deadline: '',
    evaluationPeriodEnd: '',
    awardDate: '',
    criticalityLevel: 'high',
    evaluationMethod: 'weighted_scoring',
    geographicalScope: '',
    complianceRequirements: '',
    retentionExpiry: '',
    allowLateSubmissions: false,
    autoApprove: false,
    customFields: {}
  }
  criteria.value = []
  uploadedDocuments.value = []
}

const loadSampleData = () => {
  const today = new Date()
  const inTwoWeeks = new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000)
  const inThreeWeeks = new Date(today.getTime() + 21 * 24 * 60 * 60 * 1000)
  const inOneMonth = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000)
  const inThreeDays = new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000)
  const inTwoDays = new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000)
  const formatDate = (d: Date) => d.toISOString().split('T')[0]
  const formatDateTimeLocal = (d: Date) => {
    const iso = d.toISOString()
    return iso.slice(0, 16)
  }
  
  // Populate all form fields
  formData.value = {
    emergencyNumber: `EMERGENCY-${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-001`,
    title: 'Emergency Server Replacement - Critical System Failure',
    description: 'Primary production server has failed, causing complete system outage. Immediate replacement required to restore operations. This emergency procurement bypasses standard procedures due to critical business impact.',
    type: emergencyTypes.value[0] || 'System Failure',
    category: 'IT Infrastructure',
    emergencyTypeCategory: 'System Failure',
    emergencyJustification: 'Critical production server failure occurred at 2:00 AM, causing complete system outage affecting all business operations. Normal procurement process would take 2-3 weeks, which is unacceptable given the business impact. Immediate replacement is required to restore services and prevent further revenue loss.',
    impactDescription: 'Complete system outage affecting 500+ users, inability to process customer transactions, potential revenue loss of $50,000+ per day, compliance violations due to inability to process required reports. Customer trust and satisfaction severely impacted.',
    urgencyLevel: 'CRITICAL',
    requiredDeliveryDate: formatDate(inThreeDays),
    estimatedValue: '150000',
    currency: 'USD',
    budgetMin: '140000',
    budgetMax: '180000',
    issueDate: formatDate(today),
    deadline: formatDateTimeLocal(inTwoDays),
    evaluationPeriodEnd: formatDate(inThreeWeeks),
    awardDate: formatDate(inOneMonth),
    criticalityLevel: 'critical',
    evaluationMethod: 'weighted_scoring',
    geographicalScope: 'Local',
    complianceRequirements: 'Hardware Certification, Warranty Requirements, Data Security Standards',
    retentionExpiry: formatDate(new Date(today.getTime() + 365 * 24 * 60 * 60 * 1000)),
    allowLateSubmissions: false,
    autoApprove: true,
    customFields: {
      'downtime_cost': '$50,000/day',
      'affected_systems': 'Primary Database'
    }
  }
  
  // Populate evaluation criteria
  criteria.value = [
    {
      id: `criterion-${Date.now()}-1`,
      name: 'Delivery Speed',
      description: 'Critical evaluation of vendor\'s ability to deliver equipment within the required timeframe',
      weight: 50,
      isVeto: true
    },
    {
      id: `criterion-${Date.now()}-2`,
      name: 'Technical Compatibility',
      description: 'Assessment of equipment compatibility with existing infrastructure and requirements',
      weight: 30,
      isVeto: false
    },
    {
      id: `criterion-${Date.now()}-3`,
      name: 'Price',
      description: 'Evaluation of pricing within emergency budget constraints',
      weight: 20,
      isVeto: false
    }
  ]
  
  // Populate sample documents
  uploadedDocuments.value = [
    {
      name: 'Incident Report',
      fileName: 'incident-report.pdf',
      fileSize: 128000,
      uploaded: false
    },
    {
      name: 'Technical Requirements',
      fileName: 'technical-requirements.docx',
      fileSize: 76800,
      uploaded: false
    }
  ]
  
  success('Sample Data Loaded', 'All fields have been populated with realistic sample data including evaluation criteria and documents.')
}

const handleSaveDraft = async () => {
  try {
    isSubmitting.value = true
    
    // Parse compliance requirements
    const complianceReqs = formData.value.complianceRequirements
      ? formData.value.complianceRequirements.split(/[,\n]/).map(r => r.trim()).filter(r => r)
      : null
    
    // Prepare documents array if any documents are uploaded
    const documentsArray = uploadedDocuments.value.length > 0
      ? uploadedDocuments.value.map(doc => ({
          name: doc.name,
          fileName: doc.fileName,
          fileSize: doc.fileSize,
          uploaded: doc.uploaded || false
        }))
      : null
    
    const emergencyData = {
      emergency_number: formData.value.emergencyNumber,
      emergency_title: formData.value.title,
      description: formData.value.description,
      emergency_type: formData.value.type || 'SYSTEM_FAILURE',
      emergency_type_category: formData.value.emergencyTypeCategory,
      emergency_justification: formData.value.emergencyJustification,
      impact_description: formData.value.impactDescription,
      urgency_level: formData.value.urgencyLevel || 'HIGH',
      required_delivery_date: formData.value.requiredDeliveryDate ? new Date(formData.value.requiredDeliveryDate).toISOString().split('T')[0] : null,
      estimated_value: formData.value.estimatedValue ? Number(formData.value.estimatedValue) : null,
      currency: formData.value.currency || 'USD',
      budget_range_min: formData.value.budgetMin ? Number(formData.value.budgetMin) : null,
      budget_range_max: formData.value.budgetMax ? Number(formData.value.budgetMax) : null,
      issue_date: formData.value.issueDate ? new Date(formData.value.issueDate).toISOString().split('T')[0] : null,
      submission_deadline: formData.value.deadline ? new Date(formData.value.deadline).toISOString() : null,
      evaluation_period_end: formData.value.evaluationPeriodEnd ? new Date(formData.value.evaluationPeriodEnd).toISOString().split('T')[0] : null,
      award_date: formData.value.awardDate ? new Date(formData.value.awardDate).toISOString().split('T')[0] : null,
      criticality_level: formData.value.criticalityLevel || 'high',
      evaluation_method: formData.value.evaluationMethod || 'weighted_scoring',
      geographical_scope: formData.value.geographicalScope || null,
      compliance_requirements: complianceReqs,
      retentionExpiry: formData.value.retentionExpiry ? new Date(formData.value.retentionExpiry).toISOString().split('T')[0] : null,
      allow_late_submissions: Boolean(formData.value.allowLateSubmissions),
      auto_approve: Boolean(formData.value.autoApprove),
      status: 'DRAFT',
      custom_fields: formData.value.customFields || null,
      documents: documentsArray
    }
    
    let existingEmergencyId = localStorage.getItem('current_emergency_id')
    const isUpdate = existingEmergencyId && existingEmergencyId !== 'null' && existingEmergencyId !== ''
    
    let response
    if (isUpdate) {
      response = await axios.patch(`${API_BASE_URL}/emergency-procurements/${existingEmergencyId}/`, emergencyData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
      })
    } else {
      response = await axios.post(`${API_BASE_URL}/emergency-procurements/`, emergencyData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
      })
    }
    
    const savedEmergencyId = response.data.emergency_id || existingEmergencyId
    localStorage.setItem('current_emergency_id', savedEmergencyId)
    
    if (response.data.emergency_number) {
      formData.value.emergencyNumber = response.data.emergency_number
    }
    
    // Save evaluation criteria if any exist
    if (criteria.value.length > 0 && savedEmergencyId) {
      try {
        // Delete existing criteria first (if updating)
        if (isUpdate) {
          await axios.delete(`${API_BASE_URL}/emergency-evaluation-criteria/`, {
            headers: getAuthHeaders(),
            params: { emergency_id: savedEmergencyId }
          }).catch(() => {}) // Ignore if no criteria exist
        }
        
        // Save new criteria
        for (const criterion of criteria.value) {
          if (criterion.name && criterion.description) {
            await axios.post(`${API_BASE_URL}/emergency-evaluation-criteria/`, {
              emergency_id: savedEmergencyId,
              criteria_name: criterion.name,
              criteria_description: criterion.description,
              weight_percentage: criterion.weight,
              is_mandatory: criterion.isVeto,
              veto_enabled: criterion.isVeto,
              evaluation_type: 'scoring',
              display_order: criteria.value.indexOf(criterion)
            }, {
              headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
            })
          }
        }
      } catch (criteriaErr) {
        console.error('Error saving evaluation criteria:', criteriaErr)
        // Don't fail the whole save if criteria save fails
      }
    }
    
    success(isUpdate ? 'Draft Updated' : 'Draft Saved', `Your Emergency Procurement has been ${isUpdate ? 'updated' : 'saved'} as a draft.`)
    lastSaved.value = new Date()
    
  } catch (err) {
    console.error('Error saving Emergency Procurement:', err)
    if (err.response && err.response.data) {
      error('Error', `Failed to save Emergency Procurement: ${JSON.stringify(err.response.data)}`)
    } else {
      error('Error', 'Failed to save Emergency Procurement. Please try again.')
    }
  } finally {
    isSubmitting.value = false
  }
}

const handleProceedToApprovalWorkflow = async () => {
  await handleSaveDraft()
  // Stay on the same screen after saving
  success('Emergency Procurement Saved', 'Your Emergency Procurement has been saved successfully. You can continue editing or proceed with the approval workflow when ready.')
}

let autoSaveInterval: any = null

onMounted(async () => {
  await fetchEmergencyTypes()
  autoSaveInterval = setInterval(() => {
    if (formData.value.title || formData.value.description) {
      isAutoSaving.value = true
      localStorage.setItem('emergency_draft_current', JSON.stringify(formData.value))
      lastSaved.value = new Date()
      setTimeout(() => isAutoSaving.value = false, 1000)
    }
  }, 30000)
})

onUnmounted(() => {
  if (autoSaveInterval) {
    clearInterval(autoSaveInterval)
  }
})
</script>

<style scoped>
.tab-container {
  width: 100%;
  gap: 0;
  min-width: 0;
}

.tab-button {
  flex: 1 1 0%;
  min-width: 0;
  min-width: clamp(120px, calc((100% - 16px) / max(var(--tab-count, 3), 1)), 220px);
  max-width: 100%;
  box-sizing: border-box;
  transition: min-width 0.2s ease;
}

.tab-text {
  min-width: 0;
  flex: 1 1 auto;
}

.tab-label,
.tab-description {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
