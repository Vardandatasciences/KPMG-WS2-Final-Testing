<template>
  <span :class="badgeClasses">
    <span v-if="showIcon" :class="iconClasses">
      {{ getStatusIcon(status) }}
    </span>
    {{ getStatusText(status) }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  showIcon: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['sm', 'default', 'lg'].includes(value)
  }
})

const badgeClasses = computed(() => {
  const baseClasses = 'inline-flex items-center rounded-full font-medium'
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    default: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm'
  }
  
  const statusClasses = {
    // Contract statuses
    'DRAFT': 'bg-gray-100 text-gray-800',
    'ACTIVE': 'bg-green-100 text-green-800',
    'PENDING': 'bg-yellow-100 text-yellow-800',
    'PENDING_APPROVAL': 'bg-yellow-100 text-yellow-800',
    'APPROVED': 'bg-green-100 text-green-800',
    'REJECTED': 'bg-red-100 text-red-800',
    'EXPIRED': 'bg-red-100 text-red-800',
    'TERMINATED': 'bg-red-100 text-red-800',
    'SUSPENDED': 'bg-orange-100 text-orange-800',
    'UNDER_REVIEW': 'bg-blue-100 text-blue-800',
    'ARCHIVED': 'bg-gray-100 text-gray-800',
    
    // Audit statuses
    'IN_PROGRESS': 'bg-blue-100 text-blue-800',
    'COMPLETED': 'bg-green-100 text-green-800',
    'OVERDUE': 'bg-red-100 text-red-800',
    'NOT_STARTED': 'bg-gray-100 text-gray-800',
    'ON_HOLD': 'bg-orange-100 text-orange-800',
    
    // Default fallback
    'default': 'bg-gray-100 text-gray-800'
  }
  
  const status = props.status?.toUpperCase() || 'DEFAULT'
  
  return [
    baseClasses,
    sizeClasses[props.size],
    statusClasses[status] || statusClasses['default']
  ].join(' ')
})

const iconClasses = computed(() => {
  const baseClasses = 'mr-1'
  const sizeClasses = {
    sm: 'text-xs',
    default: 'text-xs',
    lg: 'text-sm'
  }
  
  return [baseClasses, sizeClasses[props.size]].join(' ')
})

const getStatusIcon = (status) => {
  const icons = {
    'DRAFT': '📝',
    'ACTIVE': '✅',
    'PENDING': '⏳',
    'PENDING_APPROVAL': '⏳',
    'APPROVED': '✅',
    'REJECTED': '❌',
    'EXPIRED': '⏰',
    'TERMINATED': '🚫',
    'SUSPENDED': '⏸️',
    'UNDER_REVIEW': '👀',
    'ARCHIVED': '📦',
    'IN_PROGRESS': '🔄',
    'COMPLETED': '✅',
    'OVERDUE': '⚠️',
    'NOT_STARTED': '⏸️',
    'ON_HOLD': '⏸️'
  }
  
  return icons[status?.toUpperCase()] || '❓'
}

const getStatusText = (status) => {
  const textMap = {
    'DRAFT': 'Draft',
    'ACTIVE': 'Active',
    'PENDING': 'Pending',
    'PENDING_APPROVAL': 'Pending Approval',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected',
    'EXPIRED': 'Expired',
    'TERMINATED': 'Terminated',
    'SUSPENDED': 'Suspended',
    'UNDER_REVIEW': 'Under Review',
    'ARCHIVED': 'Archived',
    'IN_PROGRESS': 'In Progress',
    'COMPLETED': 'Completed',
    'OVERDUE': 'Overdue',
    'NOT_STARTED': 'Not Started',
    'ON_HOLD': 'On Hold'
  }
  
  return textMap[status?.toUpperCase()] || status || 'Unknown'
}
</script>