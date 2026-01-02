<template>
  <div class="space-y-6">
    <!-- Header -->
      <div>
      <h1 class="text-3xl font-bold text-foreground">OCR Contract Processing</h1>
      <p class="text-muted-foreground">
        Upload scanned contracts and extract data automatically
      </p>
    </div>

    <!-- Upload Step -->
    <Card v-if="uploadStep === 'upload'">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <UploadIcon class="w-5 h-5" />
          Upload Contract Document
        </CardTitle>
        <CardDescription>
          Upload PDF, PNG, JPG, or TIFF files for automatic data extraction
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div class="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
          <FileTextIcon class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">Upload Contract Document</h3>
          <p class="text-muted-foreground mb-4">
            Supports PDF, PNG, JPG, TIFF files up to 10MB
          </p>
          <div class="relative">
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.tiff"
              @change="handleFileUpload"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <Button class="gap-2">
              <UploadIcon class="w-4 h-4" />
            Choose File
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Processing Step -->
    <Card v-if="uploadStep === 'processing'">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <FileTextIcon class="w-5 h-5" />
          Processing Document
        </CardTitle>
        <CardDescription>
          Extracting data from: {{ selectedFile?.name }}
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <div class="flex justify-between text-sm">
            <span>Upload Progress</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="w-full bg-muted rounded-full h-2">
            <div 
              class="bg-primary h-2 rounded-full transition-all duration-300" 
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
        </div>
        
        <div class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p class="text-muted-foreground">
            Analyzing document and extracting contract data...
          </p>
        </div>
      </CardContent>
    </Card>

    <!-- Review Step -->
    <div v-if="uploadStep === 'review'" class="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <EyeIcon class="w-5 h-5" />
            Review Extracted Data
          </CardTitle>
          <CardDescription>
            Verify and correct the extracted information before saving
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4">
            <div v-for="(result, index) in ocrResults" :key="index" class="flex items-center justify-between p-4 border rounded-lg">
              <div class="flex-1 space-y-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{{ result.field }}</span>
                  <AlertTriangleIcon v-if="result.needsReview" class="w-4 h-4 text-warning" />
                  <CheckCircleIcon v-else class="w-4 h-4 text-success" />
                </div>
                
                <!-- Contract Value or Liability Cap -->
                <input
                  v-if="result.field === 'contract_value' || result.field === 'liability_cap'"
                  type="number"
                  :value="result.value"
                  @input="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter amount (e.g., 150000)"
                />
                
                <!-- Date fields -->
                <input
                  v-else-if="result.field === 'start_date' || result.field === 'end_date'"
                  type="date"
                  :value="result.value"
                  @input="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                />
                
                <!-- Notice Period -->
                <input
                  v-else-if="result.field === 'notice_period_days'"
                  type="number"
                  :value="result.value"
                  @input="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter number of days"
                />
                
                <!-- Auto Renewal -->
                <select
                  v-else-if="result.field === 'auto_renewal'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
                
                <!-- Priority -->
                <select
                  v-else-if="result.field === 'priority'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
                
                <!-- Contract Type -->
                <select
                  v-else-if="result.field === 'contract_type'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="MASTER_AGREEMENT">Master Agreement</option>
                  <option value="SOW">Statement of Work (SOW)</option>
                  <option value="PURCHASE_ORDER">Purchase Order</option>
                  <option value="SERVICE_AGREEMENT">Service Agreement</option>
                  <option value="LICENSE">License</option>
                  <option value="NDA">Non-Disclosure Agreement (NDA)</option>
                </select>
                
                <!-- Contract Category -->
                <select
                  v-else-if="result.field === 'contract_category'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="goods">Goods</option>
                  <option value="services">Services</option>
                  <option value="technology">Technology</option>
                  <option value="consulting">Consulting</option>
                  <option value="others">Others</option>
                </select>
                
                <!-- Dispute Resolution -->
                <select
                  v-else-if="result.field === 'dispute_resolution_method'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="negotiation">Negotiation</option>
                  <option value="mediation">Mediation</option>
                  <option value="arbitration">Arbitration</option>
                  <option value="litigation">Litigation</option>
                </select>
                
                <!-- Termination Clause -->
                <select
                  v-else-if="result.field === 'termination_clause_type'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="convenience">Convenience</option>
                  <option value="cause">Cause</option>
                  <option value="both">Both</option>
                  <option value="none">None</option>
                </select>
                
                <!-- Compliance Status -->
                <select
                  v-else-if="result.field === 'compliance_status'"
                  :value="result.value"
                  @change="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="compliant">Compliant</option>
                  <option value="non_compliant">Non-Compliant</option>
                  <option value="under_review">Under Review</option>
                  <option value="exempt">Exempt</option>
                </select>
                
                <!-- Contract Risk Score -->
                <input
                  v-else-if="result.field === 'contract_risk_score'"
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  :value="result.value"
                  @input="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter risk score (0-10)"
                />
                
                <!-- Terms, Clauses, Renewal, Termination, Insurance, Data Protection -->
                <textarea
                  v-else-if="result.field.startsWith('term_') || result.field.startsWith('clause_') || result.field.startsWith('renewal_') || result.field.startsWith('termination_') || result.field.startsWith('insurance_') || result.field.startsWith('data_protection_') || result.field === 'renewal_terms'"
                  :value="result.value"
                  @input="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                  rows="3"
                  placeholder="Enter detailed text..."
                ></textarea>
                
                <!-- Default text input -->
                <input
                  v-else
                  type="text"
                  :value="result.value"
                  @input="handleValueChange(result.field, $event.target.value)"
                  class="w-full px-3 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div class="ml-4">
                <Badge :class="getConfidenceBadgeClass(result.confidence)">
                  {{ getConfidenceText(result.confidence) }} ({{ result.confidence }}%)
                </Badge>
            </div>
            </div>
            </div>

          <div class="border-t my-6"></div>

          <div class="flex justify-between items-center">
            <div class="text-sm text-muted-foreground">
              {{ ocrResults.filter(r => r.needsReview).length }} fields need review
            </div>
            <div class="flex gap-2">
              <Button variant="outline" @click="setUploadStep('upload')">
                Upload New File
              </Button>
              <Button @click="handleSaveContract" class="gap-2">
                <SaveIcon class="w-4 h-4" />
                Save as Contract
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Preview -->
      <Card>
        <CardHeader>
          <CardTitle>Document Preview</CardTitle>
          <CardDescription>Original uploaded document</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="bg-muted rounded-lg h-64 flex items-center justify-center">
            <div class="text-center">
              <FileTextIcon class="mx-auto h-12 w-12 text-muted-foreground mb-2" />
              <p class="text-muted-foreground">Document preview</p>
              <p class="text-sm text-muted-foreground">{{ selectedFile?.name }}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Tips Card -->
    <Card>
      <CardHeader>
        <CardTitle>OCR Tips</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
            <h4 class="font-medium mb-2">For Best Results:</h4>
            <ul class="space-y-1 text-muted-foreground">
              <li>• Use high-resolution scans (300 DPI or higher)</li>
              <li>• Ensure text is clearly readable</li>
              <li>• Avoid skewed or rotated documents</li>
              <li>• Use good lighting for photos</li>
            </ul>
          </div>
          <div>
            <h4 class="font-medium mb-2">Supported Formats:</h4>
            <ul class="space-y-1 text-muted-foreground">
              <li>• PDF documents</li>
              <li>• PNG, JPG, JPEG images</li>
              <li>• TIFF files</li>
              <li>• Maximum file size: 10MB</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import loggingService from '@/services/loggingService'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle, Button, Badge
} from '@/components/ui_contract'
import { 
  Upload as UploadIcon,
  FileText as FileTextIcon,
  CheckCircle as CheckCircleIcon,
  AlertTriangle as AlertTriangleIcon,
  Eye as EyeIcon,
  Save as SaveIcon
} from 'lucide-vue-next'

interface OCRResult {
  field: string
  value: string
  confidence: number
  needsReview: boolean
}

const router = useRouter()
const fileInput = ref<HTMLInputElement>()

// Upload state management
const uploadStep = ref<'upload' | 'processing' | 'review' | 'complete'>('upload')
const uploadProgress = ref(0)
const selectedFile = ref<File | null>(null)

// Mock OCR results with comprehensive contract fields mapping to database schema
const ocrResults = ref<OCRResult[]>([
  // Basic Contract Information (vendor_contracts table)
  {
    field: "contract_title",
    value: "Software License Agreement",
    confidence: 95,
    needsReview: false
  },
  {
    field: "contract_number",
    value: "CNT-2024-001",
    confidence: 98,
    needsReview: false
  },
  {
    field: "contract_type",
    value: "SERVICE_AGREEMENT",
    confidence: 88,
    needsReview: false
  },
  {
    field: "contract_kind",
    value: "MAIN",
    confidence: 95,
    needsReview: false
  },
  {
    field: "contract_category",
    value: "technology",
    confidence: 92,
    needsReview: false
  },
  
  // Vendor Information
  {
    field: "vendor_id",
    value: "1",
    confidence: 85,
    needsReview: true
  },
  {
    field: "vendor_name",
    value: "TechSoft Solutions Inc.",
    confidence: 98,
    needsReview: false
  },
  
  // Financial Information
  {
    field: "contract_value",
    value: "150000",
    confidence: 85,
    needsReview: true
  },
  {
    field: "currency",
    value: "USD",
    confidence: 98,
    needsReview: false
  },
  {
    field: "liability_cap",
    value: "1000000",
    confidence: 78,
    needsReview: true
  },
  
  // Dates and Terms
  {
    field: "start_date",
    value: "2024-01-15",
    confidence: 92,
    needsReview: false
  },
  {
    field: "end_date",
    value: "2025-01-14",
    confidence: 90,
    needsReview: false
  },
  {
    field: "notice_period_days",
    value: "30",
    confidence: 87,
    needsReview: false
  },
  {
    field: "auto_renewal",
    value: "false",
    confidence: 85,
    needsReview: true
  },
  {
    field: "renewal_terms",
    value: "Renewal for 12 months with 30 days notice",
    confidence: 82,
    needsReview: true
  },
  
  // Contract Status and Workflow
  {
    field: "status",
    value: "PENDING_ASSIGNMENT",
    confidence: 95,
    needsReview: false
  },
  {
    field: "workflow_stage",
    value: "pending_assignment",
    confidence: 95,
    needsReview: false
  },
  {
    field: "priority",
    value: "medium",
    confidence: 85,
    needsReview: true
  },
  {
    field: "compliance_status",
    value: "under_review",
    confidence: 90,
    needsReview: false
  },
  
  // Legal and Risk Information
  {
    field: "dispute_resolution_method",
    value: "arbitration",
    confidence: 80,
    needsReview: true
  },
  {
    field: "governing_law",
    value: "California, USA",
    confidence: 88,
    needsReview: false
  },
  {
    field: "termination_clause_type",
    value: "convenience",
    confidence: 85,
    needsReview: true
  },
  {
    field: "contract_risk_score",
    value: "6.5",
    confidence: 75,
    needsReview: true
  },
  
  // Assignment and Ownership
  {
    field: "contract_owner",
    value: "1",
    confidence: 90,
    needsReview: false
  },
  {
    field: "legal_reviewer",
    value: "2",
    confidence: 88,
    needsReview: false
  },
  {
    field: "assigned_to",
    value: "1",
    confidence: 85,
    needsReview: true
  },
  
  // Compliance
  {
    field: "compliance_framework",
    value: "SOC2",
    confidence: 82,
    needsReview: true
  },
  
  // Contract Terms (contract_terms table)
  {
    field: "term_Payment_Schedule",
    value: "Payment due within 30 days of invoice receipt",
    confidence: 92,
    needsReview: false
  },
  {
    field: "term_Delivery_Requirements",
    value: "All deliverables must meet acceptance criteria as defined in the statement of work",
    confidence: 88,
    needsReview: false
  },
  {
    field: "term_Quality_Standards",
    value: "All work must meet industry best practices and quality standards",
    confidence: 90,
    needsReview: false
  },
  {
    field: "term_Intellectual_Property",
    value: "Client retains ownership of all deliverables and intellectual property",
    confidence: 85,
    needsReview: true
  },
  {
    field: "term_Confidentiality",
    value: "All confidential information shall be protected and not disclosed to third parties",
    confidence: 94,
    needsReview: false
  },
  {
    field: "term_Performance_Standards",
    value: "Vendor shall maintain 99.9% uptime and respond to issues within 4 hours",
    confidence: 87,
    needsReview: false
  },
  
  // Contract Clauses (contract_clauses table)
  {
    field: "clause_Limitation_of_Liability",
    value: "Vendor's liability shall be limited to the contract value and shall not exceed $1,000,000",
    confidence: 92,
    needsReview: false
  },
  {
    field: "clause_Confidentiality",
    value: "Both parties agree to maintain confidentiality of all proprietary information",
    confidence: 94,
    needsReview: false
  },
  {
    field: "clause_Force_Majeure",
    value: "Neither party shall be liable for delays or failures due to circumstances beyond their control",
    confidence: 87,
    needsReview: false
  },
  {
    field: "clause_Indemnification",
    value: "Vendor shall indemnify and hold harmless client against all claims arising from vendor's negligence",
    confidence: 89,
    needsReview: true
  },
  {
    field: "clause_Data_Protection",
    value: "Vendor shall comply with all applicable data protection laws and regulations",
    confidence: 91,
    needsReview: false
  },
  {
    field: "clause_Service_Level_Agreement",
    value: "Vendor shall meet service level targets as defined in the SLA appendix",
    confidence: 86,
    needsReview: false
  },
  
  // Renewal Clauses (contract_clauses with clause_type='renewal')
  {
    field: "renewal_Notice_Period",
    value: "Either party may terminate this agreement with 30 days written notice prior to expiration",
    confidence: 88,
    needsReview: false
  },
  {
    field: "renewal_Term_Length",
    value: "Contract may be renewed for additional 12-month periods with same terms and conditions",
    confidence: 85,
    needsReview: true
  },
  {
    field: "renewal_Pricing_Adjustment",
    value: "Pricing may be adjusted annually based on market rates and inflation index",
    confidence: 82,
    needsReview: true
  },
  {
    field: "renewal_Auto_Extension",
    value: "Contract shall automatically extend for one year unless terminated with proper notice",
    confidence: 90,
    needsReview: false
  },
  
  // Termination Clauses (contract_clauses with clause_type='termination')
  {
    field: "termination_Notice_Period",
    value: "Either party may terminate this agreement with 60 days written notice for convenience",
    confidence: 92,
    needsReview: false
  },
  {
    field: "termination_For_Cause",
    value: "Either party may terminate immediately for material breach of contract terms",
    confidence: 88,
    needsReview: false
  },
  {
    field: "termination_Early_Fee",
    value: "Early termination fee shall be 25% of remaining contract value",
    confidence: 85,
    needsReview: true
  },
  {
    field: "termination_Transition_Support",
    value: "Vendor shall provide 30 days transition support and knowledge transfer upon termination",
    confidence: 87,
    needsReview: false
  },
  
  // Insurance Requirements (JSON field)
  {
    field: "insurance_General_Liability",
    value: "General liability insurance of at least $2,000,000 per occurrence",
    confidence: 89,
    needsReview: false
  },
  {
    field: "insurance_Professional_Liability",
    value: "Professional liability insurance of at least $1,000,000 per claim",
    confidence: 87,
    needsReview: false
  },
  {
    field: "insurance_Cyber_Liability",
    value: "Cyber liability insurance covering data breaches and security incidents",
    confidence: 85,
    needsReview: true
  },
  
  // Data Protection Clauses (JSON field)
  {
    field: "data_protection_GDPR_Compliance",
    value: "Vendor shall comply with GDPR requirements for EU data processing",
    confidence: 88,
    needsReview: false
  },
  {
    field: "data_protection_Data_Retention",
    value: "Personal data shall be retained only as long as necessary for contract performance",
    confidence: 86,
    needsReview: false
  },
  {
    field: "data_protection_Right_to_Erasure",
    value: "Vendor shall honor data subject requests for data erasure within 30 days",
    confidence: 84,
    needsReview: true
  }
])

const handleFileUpload = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    selectedFile.value = file
    setUploadStep('processing')
    
    // Simulate upload progress
    let progress = 0
    const interval = setInterval(() => {
      progress += 10
      uploadProgress.value = progress
      
      if (progress >= 100) {
        clearInterval(interval)
        setTimeout(() => {
          setUploadStep('review')
        }, 500)
      }
    }, 200)
  }
}

const setUploadStep = (step: 'upload' | 'processing' | 'review' | 'complete') => {
  uploadStep.value = step
}

const handleValueChange = (field: string, newValue: string) => {
  ocrResults.value = ocrResults.value.map(result => 
    result.field === field 
      ? { ...result, value: newValue, needsReview: false }
      : result
  )
}

const handleSaveContract = () => {
  // Convert OCR results to contract data structure mapping to database schema
  const getFieldValue = (fieldName: string) => {
    return ocrResults.value.find(r => r.field === fieldName)?.value || ""
  }

  const getBooleanFieldValue = (fieldName: string) => {
    const value = getFieldValue(fieldName)
    return value === "true" || value === "1"
  }

  const getNumberFieldValue = (fieldName: string) => {
    const value = getFieldValue(fieldName)
    return value ? parseFloat(value) : null
  }

  const getIntegerFieldValue = (fieldName: string) => {
    const value = getFieldValue(fieldName)
    return value ? parseInt(value) : null
  }

  // Build insurance requirements JSON object
  const insuranceRequirements = {}
  ocrResults.value
    .filter(r => r.field.startsWith('insurance_'))
    .forEach(insurance => {
      const key = insurance.field.replace('insurance_', '').toLowerCase()
      insuranceRequirements[key] = insurance.value
    })

  // Build data protection clauses JSON object
  const dataProtectionClauses = {}
  ocrResults.value
    .filter(r => r.field.startsWith('data_protection_'))
    .forEach(clause => {
      const key = clause.field.replace('data_protection_', '').toLowerCase()
      dataProtectionClauses[key] = clause.value
    })

  const contractData = {
    // Basic Contract Information (vendor_contracts table)
    contract_title: getFieldValue("contract_title"),
    contract_number: getFieldValue("contract_number"),
    contract_type: getFieldValue("contract_type"),
    contract_kind: getFieldValue("contract_kind"),
    contract_category: getFieldValue("contract_category"),
    
    // Vendor Information
    vendor_id: getIntegerFieldValue("vendor_id"),
    vendor_name: getFieldValue("vendor_name"),
    
    // Financial Information
    contract_value: getNumberFieldValue("contract_value"),
    currency: getFieldValue("currency") || "USD",
    liability_cap: getNumberFieldValue("liability_cap"),
    
    // Dates and Terms
    start_date: getFieldValue("start_date"),
    end_date: getFieldValue("end_date"),
    notice_period_days: getIntegerFieldValue("notice_period_days") || 30,
    auto_renewal: getBooleanFieldValue("auto_renewal"),
    renewal_terms: getFieldValue("renewal_terms"),
    
    // Contract Status and Workflow
    status: getFieldValue("status") || "PENDING_ASSIGNMENT",
    workflow_stage: getFieldValue("workflow_stage") || "pending_assignment",
    priority: getFieldValue("priority") || "medium",
    compliance_status: getFieldValue("compliance_status") || "under_review",
    
    // Legal and Risk Information
    dispute_resolution_method: getFieldValue("dispute_resolution_method"),
    governing_law: getFieldValue("governing_law"),
    termination_clause_type: getFieldValue("termination_clause_type"),
    contract_risk_score: getNumberFieldValue("contract_risk_score"),
    
    // Assignment and Ownership
    contract_owner: getIntegerFieldValue("contract_owner"),
    legal_reviewer: getIntegerFieldValue("legal_reviewer"),
    assigned_to: getIntegerFieldValue("assigned_to"),
    
    // Compliance
    compliance_framework: getFieldValue("compliance_framework"),
    
    // JSON Fields
    insurance_requirements: insuranceRequirements,
    data_protection_clauses: dataProtectionClauses,
    custom_fields: {},
    
    // Contract Terms (contract_terms table)
    contractTerms: ocrResults.value
      .filter(r => r.field.startsWith("term_"))
      .map((term, index) => ({
        term_id: `term_${Date.now()}_${index}`,
        term_category: term.field.replace("term_", "").replace(/_/g, " "),
        term_title: term.field.replace("term_", "").replace(/_/g, " "),
        term_text: term.value,
        risk_level: "Low",
        compliance_status: "Pending",
        is_standard: false,
        approval_status: "Pending",
        approved_by: null,
        approved_at: null,
        version_number: "1.0",
        parent_term_id: "",
        created_by: getIntegerFieldValue("contract_owner")
      })),
    
    // Contract Clauses (contract_clauses table)
    contractClauses: [
      // Standard clauses
      ...ocrResults.value
        .filter(r => r.field.startsWith("clause_"))
      .map((clause, index) => ({
        clause_id: `clause_${Date.now()}_${index}`,
          clause_name: clause.field.replace("clause_", "").replace(/_/g, " "),
        clause_type: "standard",
        clause_text: clause.value,
          risk_level: "low",
        legal_category: "Contract Terms",
        version_number: "1.0",
        is_standard: false,
          created_by: getIntegerFieldValue("contract_owner")
        })),
      
      // Renewal clauses
      ...ocrResults.value
        .filter(r => r.field.startsWith("renewal_"))
      .map((clause, index) => ({
        clause_id: `renewal_${Date.now()}_${index}`,
          clause_name: clause.field.replace("renewal_", "").replace(/_/g, " "),
        clause_type: "renewal",
        clause_text: clause.value,
        risk_level: "low",
        legal_category: "Contract Renewal",
        version_number: "1.0",
        is_standard: false,
          created_by: getIntegerFieldValue("contract_owner"),
          notice_period_days: clause.field.includes("notice") ? 30 : null,
          auto_renew: clause.field.includes("auto") ? true : false,
        renewal_terms: clause.value
      })),
      
      // Termination clauses
      ...ocrResults.value
        .filter(r => r.field.startsWith("termination_"))
      .map((clause, index) => ({
        clause_id: `termination_${Date.now()}_${index}`,
          clause_name: clause.field.replace("termination_", "").replace(/_/g, " "),
        clause_type: "termination",
        clause_text: clause.value,
        risk_level: "medium",
        legal_category: "Contract Termination",
        version_number: "1.0",
        is_standard: false,
          created_by: getIntegerFieldValue("contract_owner"),
          termination_notice_period: clause.field.includes("notice") ? 60 : null,
          early_termination_fee: clause.field.includes("fee") ? 25 : null,
        termination_conditions: clause.value
      }))
    ]
  }

  // Store in localStorage for the CreateContract page to use
  localStorage.setItem('ocrContractData', JSON.stringify(contractData))
  
  // Navigate to CreateContract page with the extracted data
  router.push('/create-contract')
}

const getConfidenceBadgeClass = (confidence: number) => {
  if (confidence >= 90) {
    return "bg-success text-success-foreground"
  } else if (confidence >= 70) {
    return "bg-warning text-warning-foreground"
  } else {
    return "bg-destructive text-destructive-foreground"
  }
}

const getConfidenceText = (confidence: number) => {
  if (confidence >= 90) {
    return "High"
  } else if (confidence >= 70) {
    return "Medium"
  } else {
    return "Low"
  }
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'OCR Upload')
})
</script>
