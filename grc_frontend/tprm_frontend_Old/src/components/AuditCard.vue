<template>
  <Card 
    class="shadow-card hover:shadow-hover transition-all cursor-pointer group"
    @click="$emit('click')"
  >
    <CardHeader class="pb-3 border-l-4 border-l-primary/20 group-hover:border-l-primary transition-colors">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <CardTitle class="text-lg leading-tight group-hover:text-primary transition-colors">
            {{ audit.title }}
          </CardTitle>
          <CardDescription class="mt-1 text-sm">
            <span class="font-medium">SLA:</span> {{ audit.sla_name || 'Unknown SLA' }}
          </CardDescription>
          <Badge v-if="audit.business_unit" variant="outline" class="mt-2 text-xs">
            {{ audit.business_unit }}
          </Badge>
        </div>
        <div class="flex flex-col items-end space-y-2">
          <StatusBadge :status="audit.status" />
          <Badge v-if="isOverdue" variant="destructive" class="text-xs">
            <AlertTriangle class="w-3 h-3 mr-1" />
            Overdue
          </Badge>
        </div>
      </div>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div class="space-y-3">
          <div class="flex items-center text-muted-foreground">
            <User class="w-4 h-4 mr-2 text-primary" />
            <span><strong>Auditor:</strong> {{ audit.auditor_name || 'Unknown Auditor' }}</span>
          </div>
          <div class="flex items-center text-muted-foreground">
            <Eye class="w-4 h-4 mr-2 text-primary" />
            <span><strong>Reviewer:</strong> {{ audit.reviewer_name || 'Unknown Reviewer' }}</span>
          </div>
        </div>
        <div class="space-y-3">
          <div class="flex items-center text-muted-foreground">
            <Calendar class="w-4 h-4 mr-2 text-primary" />
            <span><strong>Due:</strong> {{ formatDate(audit.due_date) }}</span>
          </div>
          <div class="flex items-center text-muted-foreground">
            <Clock class="w-4 h-4 mr-2 text-primary" />
            <span><strong>Updated:</strong> {{ formatDate(audit.updated_at) }}</span>
          </div>
        </div>
      </div>
      
      <div v-if="audit.scope" class="text-sm text-muted-foreground bg-muted/40 p-3 rounded-md border-l-2 border-primary/30">
        <strong class="text-foreground">Scope:</strong> {{ audit.scope }}
      </div>
      
      <div v-if="audit.metrics_count > 0" class="text-sm text-muted-foreground bg-blue-50 p-3 rounded-md border-l-2 border-blue-300">
        <div class="flex items-center mb-2">
          <Target class="w-4 h-4 mr-2 text-blue-600" />
          <strong class="text-foreground">Metrics ({{ audit.metrics_count }}):</strong>
        </div>
        <div class="text-xs">
          {{ audit.metrics_names }}
        </div>
      </div>

      <div v-if="audit.evidence_docs_count !== undefined" class="text-sm text-muted-foreground bg-purple-50 p-3 rounded-md border-l-2 border-purple-300">
        <div class="flex items-center">
          <Paperclip class="w-4 h-4 mr-2 text-purple-600" />
          <div>
            <div><strong class="text-foreground">Evidence Docs:</strong> {{ audit.evidence_docs_count }}</div>
            <div v-if="audit.evidence_docs_last_updated" class="text-xs">
              Updated {{ formatDate(audit.evidence_docs_last_updated) }}
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between pt-3 border-t border-border/50">
        <div class="flex items-center space-x-3 text-xs">
          <Badge variant="secondary" class="text-xs">
            {{ audit.audit_type }}
          </Badge>
          <Badge variant="outline" class="text-xs">
            {{ audit.frequency }}
          </Badge>
          <Badge v-if="audit.role" variant="outline" class="text-xs">
            {{ audit.role }}
          </Badge>
        </div>
        <div class="flex space-x-2">
          <Button 
            v-if="audit.status === 'created'"
            variant="default"
            size="sm"
            class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover"
            @click.stop="handleStartAudit"
          >
            Start Audit
          </Button>
          <Button 
            v-else-if="isMyAudit && (audit.status === 'in_progress' || audit.status === 'rejected')"
            variant="default"
            size="sm"
            class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover"
            @click.stop="handleContinueAudit"
          >
            Continue Audit
          </Button>
          <Button 
            v-else-if="isMyReview && audit.status === 'under_review'"
            variant="default"
            size="sm"
            class="bg-gradient-to-r from-green-600 to-green-700 hover:shadow-hover"
            @click.stop="handleReviewAudit"
          >
            Review Audit
          </Button>
          <Button 
            v-else
            variant="outline"
            size="sm"
            @click.stop="handleViewDetails"
          >
            View Details
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  User,
  Calendar,
  Clock,
  Eye,
  AlertTriangle,
  Target,
  Paperclip
} from 'lucide-vue-next'
import apiService from '@/services/api.js'
import Card from '@/components/ui/card.vue'
import CardHeader from '@/components/ui/card-header.vue'
import CardTitle from '@/components/ui/card-title.vue'
import CardDescription from '@/components/ui/card-description.vue'
import CardContent from '@/components/ui/card-content.vue'
import Button from '@/components/ui/button.vue'
import Badge from '@/components/ui/badge.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const props = defineProps(['audit', 'currentUserId'])
const emit = defineEmits(['click'])

const router = useRouter()

const isOverdue = computed(() => 
  new Date(props.audit.due_date) < new Date() && props.audit.status !== 'completed'
)

const isMyAudit = computed(() => props.audit.auditor_id === props.currentUserId)
const isMyReview = computed(() => props.audit.reviewer_id === props.currentUserId)

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const handleStartAudit = async () => {
  try {
    // Update audit status to in_progress
    await apiService.updateAudit(props.audit.audit_id, { status: 'in_progress' })
    router.push(`/audit/${props.audit.audit_id}`)
  } catch (error) {
    console.error('Error starting audit:', error)
    alert('Error starting audit. Please try again.')
  }
}

const handleContinueAudit = () => {
  router.push(`/audit/${props.audit.audit_id}`)
}

const handleReviewAudit = () => {
  router.push(`/audit/${props.audit.audit_id}/review`)
}

const handleViewDetails = () => {
  router.push(`/audit/${props.audit.audit_id}`)
}
</script>
