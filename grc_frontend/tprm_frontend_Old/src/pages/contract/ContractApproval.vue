<template>
  <div class="container mx-auto p-6 space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Contract Approvals</h1>
        <p class="text-muted-foreground">Manage contract approval workflows</p>
      </div>
    </div>

    <div class="flex gap-4 mb-6">
      <Select v-model="filterStatus" class="w-48">
        <SelectTrigger>
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
          <SelectItem value="approved">Approved</SelectItem>
          <SelectItem value="rejected">Rejected</SelectItem>
          <SelectItem value="delegated">Delegated</SelectItem>
        </SelectContent>
      </Select>

      <Select v-model="filterType" class="w-48">
        <SelectTrigger>
          <SelectValue placeholder="Filter by type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          <SelectItem value="creation">Creation</SelectItem>
          <SelectItem value="amendment">Amendment</SelectItem>
          <SelectItem value="renewal">Renewal</SelectItem>
          <SelectItem value="termination">Termination</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>Approval Queue</CardTitle>
            <CardDescription>
              Pending and recent approval requests
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contract</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Level</TableHead>
                  <TableHead>Submitter</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="approval in filteredApprovals" :key="approval.approval_id">
                  <TableCell>
                    <div>
                      <div class="font-medium">{{ approval.contract_title }}</div>
                      <div class="text-sm text-muted-foreground">#{{ approval.contract_id }}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" class="capitalize">
                      {{ approval.approval_type }}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div class="flex items-center gap-2">
                      <component :is="getStatusIcon(approval.approval_status)" class="h-4 w-4" :class="getStatusIconClass(approval.approval_status)" />
                      <Badge :variant="getStatusVariant(approval.approval_status)" class="capitalize">
                        {{ approval.approval_status }}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">Level {{ approval.approval_level }}</Badge>
                  </TableCell>
                  <TableCell>{{ approval.submitter_name }}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      @click="setSelectedApproval(approval)"
                    >
                      <Eye class="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <div>
        <Card v-if="selectedApproval">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <MessageSquare class="h-5 w-5" />
              Approval Details
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <Tabs v-model="activeTab" class="w-full">
              <TabsList class="grid w-full grid-cols-3">
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="history">History</TabsTrigger>
                <TabsTrigger value="actions">Actions</TabsTrigger>
              </TabsList>
              
              <TabsContent value="details" class="space-y-4">
                <div>
                  <Label class="text-sm font-medium">Contract Title</Label>
                  <p class="text-sm text-muted-foreground">{{ selectedApproval.contract_title }}</p>
                </div>
                
                <div>
                  <Label class="text-sm font-medium">Approval Type</Label>
                  <Badge variant="outline" class="capitalize">
                    {{ selectedApproval.approval_type }}
                  </Badge>
                </div>
                
                <div>
                  <Label class="text-sm font-medium">Status</Label>
                  <div class="flex items-center gap-2">
                    <component :is="getStatusIcon(selectedApproval.approval_status)" class="h-4 w-4" :class="getStatusIconClass(selectedApproval.approval_status)" />
                    <Badge :variant="getStatusVariant(selectedApproval.approval_status)" class="capitalize">
                      {{ selectedApproval.approval_status }}
                    </Badge>
                  </div>
                </div>
                
                <div>
                  <Label class="text-sm font-medium">Comments</Label>
                  <p class="text-sm text-muted-foreground">{{ selectedApproval.comments }}</p>
                </div>
                
                <div v-if="selectedApproval.modified_fields">
                  <Label class="text-sm font-medium">Modified Fields</Label>
                  <pre class="text-xs bg-muted p-2 rounded mt-1">
                    {{ JSON.stringify(selectedApproval.modified_fields, null, 2) }}
                  </pre>
                </div>
              </TabsContent>
              
              <TabsContent value="history" class="space-y-2">
                <div v-for="(entry, index) in selectedApproval.approval_history" :key="index" class="border-l-2 border-muted pl-4 pb-2">
                  <div class="text-sm font-medium capitalize">{{ entry.action }}</div>
                  <div class="text-xs text-muted-foreground">
                    by {{ entry.user }} - Level {{ entry.level }}
                  </div>
                  <div class="text-xs text-muted-foreground">{{ entry.date }}</div>
                </div>
              </TabsContent>
              
              <TabsContent value="actions" class="space-y-4">
                <div v-if="selectedApproval.approval_status === 'pending'" class="space-y-3">
                  <Button 
                    class="w-full" 
                    @click="handleApprovalAction(selectedApproval.approval_id, 'approve')"
                  >
                    <CheckCircle class="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  
                  <Button 
                    variant="destructive" 
                    class="w-full"
                    @click="handleApprovalAction(selectedApproval.approval_id, 'reject')"
                  >
                    <XCircle class="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                  
                  <div class="space-y-2">
                    <Label for="action-comments">Comments</Label>
                    <Textarea 
                      id="action-comments"
                      placeholder="Add your comments..."
                      class="min-h-[80px]"
                      v-model="actionComments"
                    />
                  </div>
                </div>
                
                <div v-if="selectedApproval.approval_status === 'approved'" class="space-y-3">
                  <Button 
                    class="w-full" 
                    @click="generatePDF(selectedApproval)"
                  >
                    <FileText class="h-4 w-4 mr-2" />
                    Generate PDF
                  </Button>
                  
                  <div class="text-sm text-muted-foreground text-center">
                    Generate PDF from extracted contract data
                  </div>
                </div>
                
                <div v-if="selectedApproval.approval_status !== 'pending' && selectedApproval.approval_status !== 'approved'" class="text-center text-muted-foreground">
                  This approval has been {{ selectedApproval.approval_status }}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        
        <Card v-else>
          <CardContent class="flex items-center justify-center h-64">
            <p class="text-muted-foreground">Select an approval to view details</p>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Input, Label, Textarea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Tabs, TabsContent, TabsList, TabsTrigger, Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui_contract'
import { 
  CheckCircle, XCircle, Clock, ArrowRight, Eye, MessageSquare, FileText, Download 
} from 'lucide-vue-next'

// State
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const selectedApproval = ref(null)
const activeTab = ref('details')
const filterStatus = ref('all')
const filterType = ref('all')
const actionComments = ref('')

// Mock data
const mockApprovals = ref([
  {
    approval_id: 1,
    contract_id: 1001,
    approval_type: 'creation',
    approver_id: 101,
    approval_status: 'pending',
    approval_level: 1,
    submitted_data: { contract_value: 150000, vendor: "Tech Solutions Inc" },
    modified_fields: { payment_terms: "Net 30", delivery_date: "2024-03-15" },
    approval_history: [
      { date: "2024-01-15", action: "submitted", user: "John Doe", level: 1 }
    ],
    comments: "Please review the payment terms and vendor qualifications",
    approved_at: null,
    rejection_reason: "",
    delegated_to: null,
    escalation_date: "2024-01-20",
    contract_title: "Software Development Agreement",
    submitter_name: "John Doe",
    extracted_data: {
      contract_number: "CTR-2024-001",
      vendor_name: "Tech Solutions Inc",
      contract_value: 150000,
      start_date: "2024-01-15",
      end_date: "2024-12-31",
      payment_terms: "Net 30",
      delivery_terms: "FOB Destination",
      contract_type: "Service Agreement",
      description: "Software development services for enterprise application",
      key_terms: ["Agile methodology", "Monthly milestones", "Quality assurance"],
      obligations: ["Deliver source code", "Provide documentation", "Support for 6 months"],
      extracted_at: "2024-01-15T10:00:00Z",
      extraction_confidence: 0.95
    }
  },
  {
    approval_id: 2,
    contract_id: 1002,
    approval_type: 'amendment',
    approver_id: 102,
    approval_status: 'approved',
    approval_level: 2,
    submitted_data: { amendment_type: "value_increase", new_value: 200000 },
    modified_fields: { contract_value: 200000, end_date: "2024-12-31" },
    approval_history: [
      { date: "2024-01-10", action: "submitted", user: "Jane Smith", level: 1 },
      { date: "2024-01-12", action: "approved", user: "Mike Johnson", level: 2 }
    ],
    comments: "Approved with condition to add quarterly reviews",
    approved_at: "2024-01-12T10:30:00Z",
    rejection_reason: "",
    delegated_to: null,
    escalation_date: null,
    contract_title: "Marketing Services Contract",
    submitter_name: "Jane Smith",
    extracted_data: {
      contract_number: "CTR-2024-002",
      vendor_name: "Creative Marketing Group",
      contract_value: 200000,
      start_date: "2024-01-01",
      end_date: "2024-12-31",
      payment_terms: "Net 45",
      delivery_terms: "As per schedule",
      contract_type: "Marketing Services",
      description: "Comprehensive marketing and advertising services",
      key_terms: ["Quarterly reviews", "Performance metrics", "Brand guidelines"],
      obligations: ["Monthly reports", "Campaign execution", "ROI tracking"],
      extracted_at: "2024-01-10T14:30:00Z",
      extraction_confidence: 0.92
    }
  }
])

// Computed
const filteredApprovals = computed(() => {
  return mockApprovals.value.filter(approval => {
    if (filterStatus.value !== "all" && approval.approval_status !== filterStatus.value) return false
    if (filterType.value !== "all" && approval.approval_type !== filterType.value) return false
    return true
  })
})

// Methods
const getStatusIcon = (status) => {
  switch (status) {
    case 'approved': return CheckCircle
    case 'rejected': return XCircle
    case 'delegated': return ArrowRight
    default: return Clock
  }
}

const getStatusIconClass = (status) => {
  switch (status) {
    case 'approved': return 'text-green-500'
    case 'rejected': return 'text-red-500'
    case 'delegated': return 'text-blue-500'
    default: return 'text-yellow-500'
  }
}

const getStatusVariant = (status) => {
  switch (status) {
    case 'approved': return 'default'
    case 'rejected': return 'destructive'
    case 'delegated': return 'secondary'
    default: return 'outline'
  }
}

const setSelectedApproval = (approval) => {
  selectedApproval.value = approval
  activeTab.value = 'details'
}

const handleApprovalAction = async (approvalId, action, data = {}) => {
  try {
    mockApprovals.value = mockApprovals.value.map(approval => 
      approval.approval_id === approvalId 
        ? { 
            ...approval, 
            approval_status: action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'delegated',
            approved_at: action === 'approve' ? new Date().toISOString() : null,
            rejection_reason: data?.reason || '',
            delegated_to: data?.delegateTo || null,
            comments: data?.comments || approval.comments
          }
        : approval
    )
    
    // Update selected approval
    if (selectedApproval.value?.approval_id === approvalId) {
      selectedApproval.value = mockApprovals.value.find(a => a.approval_id === approvalId)
    }
    
    // Show success notification
    const actionText = action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'delegated'
    await showSuccess('Approval Updated', `Contract approval has been ${actionText} successfully.`, {
      action: 'approval_updated',
      approval_id: approvalId,
      new_status: actionText,
      contract_name: selectedApproval.value?.contract_name
    })
  } catch (error) {
    await showError('Action Failed', 'Failed to update approval. Please try again.', {
      action: 'approval_update_failed',
      approval_id: approvalId,
      error_message: error.message
    })
  }
}

const generatePDF = (approval) => {
  if (!approval.extracted_data) {
    PopupService.warning("No extracted data available for this contract", "No Data Available")
    return
  }

  // Create PDF content based on extracted data
  const pdfContent = createPDFContent(approval)
  
  // Generate and download PDF
  downloadPDF(pdfContent, `contract-${approval.contract_id}.pdf`)
}

const createPDFContent = (approval) => {
  const data = approval.extracted_data
  
  // Create a structured document with extracted data
  const content = `
CONTRACT DOCUMENT
Generated from Extracted Data

IMPORTANT NOTE: This document contains information extracted from the original contract using automated processing. 
Please verify all details against the original source document for accuracy and completeness.

Contract Information:
====================
Contract Number: ${data.contract_number}
Contract Title: ${approval.contract_title}
Contract Type: ${data.contract_type}
Vendor: ${data.vendor_name}

Financial Details:
=================
Contract Value: $${data.contract_value.toLocaleString()}
Payment Terms: ${data.payment_terms}

Timeline:
=========
Start Date: ${data.start_date}
End Date: ${data.end_date}
Delivery Terms: ${data.delivery_terms}

Description:
===========
${data.description}

Key Terms:
==========
${data.key_terms.map(term => `• ${term}`).join('\n')}

Obligations:
============
${data.obligations.map(obligation => `• ${obligation}`).join('\n')}

Extraction Information:
======================
Extracted At: ${new Date(data.extracted_at).toLocaleString()}
Confidence Level: ${(data.extraction_confidence * 100).toFixed(1)}%

Approval Details:
=================
Approval ID: ${approval.approval_id}
Approval Type: ${approval.approval_type}
Approval Status: ${approval.approval_status}
Approval Level: ${approval.approval_level}
Approved At: ${approval.approved_at ? new Date(approval.approved_at).toLocaleString() : 'N/A'}
Submitter: ${approval.submitter_name}

Generated on: ${new Date().toLocaleString()}
  `
  
  return content
}

const downloadPDF = (content, filename) => {
  // Create a blob with the content
  const blob = new Blob([content], { type: 'text/plain' })
  
  // Create download link
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  
  // Trigger download
  document.body.appendChild(link)
  link.click()
  
  // Cleanup
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Approval')
})
</script>
