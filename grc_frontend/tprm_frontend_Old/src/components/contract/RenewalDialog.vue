<template>
  <Dialog :open="open" @close="$emit('close')">
    <DialogContent class="max-w-6xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <RefreshCw class="w-5 h-5" />
          Initiate Contract Renewal
        </DialogTitle>
        <DialogDescription>
          Create a comprehensive renewal request for {{ contract?.title }}
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-6">
        <!-- Basic Contract Information -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Contract Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="space-y-2">
                <Label>Contract ID</Label>
                <Input :value="contract?.id || ''" disabled />
              </div>
              <div class="space-y-2">
                <Label>Vendor</Label>
                <Input :value="contract?.vendor_name || ''" disabled />
              </div>
              <div class="space-y-2">
                <Label>Contract Type</Label>
                <Input :value="contract?.type || ''" disabled />
              </div>
              <div class="space-y-2">
                <Label>Current Status</Label>
                <Input :value="contract?.status || ''" disabled />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Renewal Schedule -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Renewal Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label>Renewal Date *</Label>
                <Input 
                  type="date" 
                  v-model="localRenewalForm.renewal_date"
                />
              </div>
              <div class="space-y-2">
                <Label>Decision Due Date *</Label>
                <Input 
                  type="date" 
                  v-model="localRenewalForm.decision_due_date"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Financial Terms -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Financial Terms</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="space-y-2">
                <Label>Contract Value</Label>
                <Input 
                  type="number"
                  v-model="localRenewalForm.contract_value"
                  placeholder="0.00"
                />
              </div>
              <div class="space-y-2">
                <Label>Currency</Label>
                <Select v-model="localRenewalForm.currency">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                    <SelectItem value="CAD">CAD</SelectItem>
                    <SelectItem value="AUD">AUD</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label>Liability Cap</Label>
                <Input 
                  type="number"
                  v-model="localRenewalForm.liability_cap"
                  placeholder="0.00"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Contract Terms -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Contract Terms</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label>Start Date</Label>
                <Input 
                  type="date" 
                  v-model="localRenewalForm.start_date"
                />
              </div>
              <div class="space-y-2">
                <Label>End Date</Label>
                <Input 
                  type="date" 
                  v-model="localRenewalForm.end_date"
                />
              </div>
              <div class="space-y-2">
                <Label>Contract Category</Label>
                <Select v-model="localRenewalForm.contract_category">
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="goods">Goods</SelectItem>
                    <SelectItem value="services">Services</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="consulting">Consulting</SelectItem>
                    <SelectItem value="others">Others</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label>Contract Type</Label>
                <Select v-model="localRenewalForm.contract_type">
                  <SelectTrigger>
                    <SelectValue placeholder="Select contract type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MASTER_AGREEMENT">Master Agreement</SelectItem>
                    <SelectItem value="SOW">Statement of Work</SelectItem>
                    <SelectItem value="PURCHASE_ORDER">Purchase Order</SelectItem>
                    <SelectItem value="SERVICE_CONTRACT">Service Contract</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Contract Clauses -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Contract Clauses</CardTitle>
          </CardHeader>
          <CardContent class="space-y-6">
            <!-- Renewal Clauses -->
            <div class="space-y-4">
              <Label class="text-base font-medium">Renewal Clauses</Label>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label>Auto-Renewal</Label>
                  <div class="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="auto_renewal"
                      v-model="localRenewalForm.auto_renewal"
                      class="rounded border-gray-300"
                    />
                    <Label for="auto_renewal">Enable automatic renewal</Label>
                  </div>
                </div>
                <div class="space-y-2">
                  <Label>Notice Period (Days)</Label>
                  <Input 
                    type="number"
                    v-model="localRenewalForm.notice_period_days"
                    placeholder="30"
                  />
                </div>
              </div>
              <div class="space-y-2">
                <Label>Renewal Terms & Conditions</Label>
                <Textarea 
                  placeholder="Describe renewal terms and conditions..."
                  v-model="localRenewalForm.renewal_terms"
                  rows="4"
                />
              </div>
            </div>

            <!-- Termination Clauses -->
            <div class="space-y-4">
              <Label class="text-base font-medium">Termination Clauses</Label>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label>Termination Type</Label>
                  <Select v-model="localRenewalForm.termination_clause">
                    <SelectTrigger>
                      <SelectValue placeholder="Select termination type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="convenience">Convenience</SelectItem>
                      <SelectItem value="cause">Cause</SelectItem>
                      <SelectItem value="both">Both</SelectItem>
                      <SelectItem value="none">None</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div class="space-y-2">
                  <Label>Dispute Resolution</Label>
                  <Select v-model="localRenewalForm.dispute_resolution">
                    <SelectTrigger>
                      <SelectValue placeholder="Select resolution method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="negotiation">Negotiation</SelectItem>
                      <SelectItem value="mediation">Mediation</SelectItem>
                      <SelectItem value="arbitration">Arbitration</SelectItem>
                      <SelectItem value="litigation">Litigation</SelectItem>
                      <SelectItem value="hybrid">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div class="space-y-2">
                <Label>Governing Law</Label>
                <Input 
                  v-model="localRenewalForm.governing_law"
                  placeholder="e.g., California, USA"
                />
              </div>
            </div>

            <!-- Compliance Clauses -->
            <div class="space-y-4">
              <Label class="text-base font-medium">Compliance Clauses</Label>
              <div class="space-y-2">
                <Label>Insurance Requirements</Label>
                <Textarea 
                  placeholder="Specify insurance requirements and coverage amounts..."
                  v-model="localRenewalForm.insurance_requirements"
                  rows="3"
                />
              </div>
              <div class="space-y-2">
                <Label>Data Protection Clauses</Label>
                <Textarea 
                  placeholder="Specify data protection and privacy requirements..."
                  v-model="localRenewalForm.data_protection_clauses"
                  rows="3"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Risk & Compliance -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Risk & Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="space-y-2">
                <Label>Contract Risk Score</Label>
                <Input 
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  v-model="localRenewalForm.contract_risk_score"
                  placeholder="0.0"
                />
              </div>
              <div class="space-y-2">
                <Label>Priority</Label>
                <Select v-model="localRenewalForm.priority">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label>Compliance Status</Label>
                <Select v-model="localRenewalForm.compliance_status">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="compliant">Compliant</SelectItem>
                    <SelectItem value="non_compliant">Non-Compliant</SelectItem>
                    <SelectItem value="under_review">Under Review</SelectItem>
                    <SelectItem value="pending_review">Pending Review</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Additional Comments -->
        <Card>
          <CardHeader>
            <CardTitle class="text-lg">Additional Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <Label>Renewal Comments & Notes</Label>
              <Textarea 
                placeholder="Add any additional notes, special conditions, or comments about this renewal request..."
                v-model="localRenewalForm.comments"
                rows="4"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <DialogFooter class="gap-2">
        <Button variant="outline" @click="$emit('close')">
          Cancel
        </Button>
        <Button @click="handleSubmit" class="gap-2">
          <RefreshCw class="w-4 h-4" />
          Submit Renewal Request
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
  Card, CardContent, CardHeader, CardTitle,
  Button, Input, Label, Textarea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui_contract'
import { RefreshCw } from 'lucide-vue-next'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  contract: {
    type: Object,
    default: null
  },
  renewalForm: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'submit', 'update:renewal-form'])

// Local form state
const localRenewalForm = ref({ ...props.renewalForm })

// Watch for prop changes and update local state
watch(() => props.renewalForm, (newForm) => {
  localRenewalForm.value = { ...newForm }
}, { deep: true })

// Watch local form changes and emit updates
watch(localRenewalForm, (newForm) => {
  emit('update:renewal-form', { ...newForm })
}, { deep: true })

const handleSubmit = () => {
  emit('submit', localRenewalForm.value)
}
</script>
