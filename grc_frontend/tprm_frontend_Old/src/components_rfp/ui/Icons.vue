<template>
  <svg
    :class="iconClasses"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <!-- Plus Icon -->
    <path v-if="name === 'plus'" d="M5 12h14m-7-7v14" />
    
    <!-- Trash2 Icon -->
    <path v-if="name === 'trash2'" d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V8m3 0V6c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    <line v-if="name === 'trash2'" x1="10" y1="11" x2="10" y2="17" />
    <line v-if="name === 'trash2'" x1="14" y1="11" x2="14" y2="17" />
    
    <!-- Save Icon -->
    <path v-if="name === 'save'" d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
    <polyline v-if="name === 'save'" points="17,21 17,13 7,13 7,21" />
    <polyline v-if="name === 'save'" points="7,3 7,8 15,8" />
    
    <!-- ArrowRight Icon -->
    <line v-if="name === 'arrow-right'" x1="5" y1="12" x2="19" y2="12" />
    <polyline v-if="name === 'arrow-right'" points="12,5 19,12 12,19" />
    
    <!-- DollarSign Icon -->
    <line v-if="name === 'dollar-sign'" x1="12" y1="1" x2="12" y2="23" />
    <path v-if="name === 'dollar-sign'" d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    
    <!-- Calendar Icon -->
    <rect v-if="name === 'calendar'" x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line v-if="name === 'calendar'" x1="16" y1="2" x2="16" y2="6" />
    <line v-if="name === 'calendar'" x1="8" y1="2" x2="8" y2="6" />
    <line v-if="name === 'calendar'" x1="3" y1="10" x2="21" y2="10" />
    
    <!-- Users Icon -->
    <path v-if="name === 'users'" d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle v-if="name === 'users'" cx="9" cy="7" r="4" />
    <path v-if="name === 'users'" d="M22 21v-2a4 4 0 0 0-3-3.87" />
    <path v-if="name === 'users'" d="M16 3.13a4 4 0 0 1 0 7.75" />
    
    <!-- Target Icon -->
    <circle v-if="name === 'target'" cx="12" cy="12" r="10" />
    <circle v-if="name === 'target'" cx="12" cy="12" r="6" />
    <circle v-if="name === 'target'" cx="12" cy="12" r="2" />
    
    <!-- Settings Icon -->
    <circle v-if="name === 'settings'" cx="12" cy="12" r="3" />
    <path v-if="name === 'settings'" d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    
    <!-- FileText Icon -->
    <path v-if="name === 'file-text'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline v-if="name === 'file-text'" points="14,2 14,8 20,8" />
    <line v-if="name === 'file-text'" x1="16" y1="13" x2="8" y2="13" />
    <line v-if="name === 'file-text'" x1="16" y1="17" x2="8" y2="17" />
    <polyline v-if="name === 'file-text'" points="10,9 9,9 8,9" />
    
    <!-- Lightbulb Icon -->
    <path v-if="name === 'lightbulb'" d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1z" />
    <path v-if="name === 'lightbulb'" d="M12 2C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z" />
    
    <!-- Clock Icon -->
    <circle v-if="name === 'clock'" cx="12" cy="12" r="10" />
    <polyline v-if="name === 'clock'" points="12,6 12,12 16,14" />
    
    <!-- CheckCircle Icon -->
    <path v-if="name === 'check-circle'" d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline v-if="name === 'check-circle'" points="22,4 12,14.01 9,11.01" />
    
    <!-- User Icon -->
    <path v-if="name === 'user'" d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle v-if="name === 'user'" cx="12" cy="7" r="4" />
    
    <!-- Mail Icon -->
    <rect v-if="name === 'mail'" x="2" y="4" width="20" height="16" rx="2" />
    <polyline v-if="name === 'mail'" points="22,7 13,13 2,7" />
    
    <!-- Camera Icon -->
    <path v-if="name === 'camera'" d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
    <circle v-if="name === 'camera'" cx="12" cy="13" r="3" />
    
    <!-- Check Icon -->
    <polyline v-if="name === 'check'" points="20,6 9,17 4,12" />
    
    <!-- FileText2 Icon (for documents) -->
    <path v-if="name === 'file-text2'" d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
    <polyline v-if="name === 'file-text2'" points="14,2 14,8 20,8" />
    <line v-if="name === 'file-text2'" x1="16" y1="13" x2="8" y2="13" />
    <line v-if="name === 'file-text2'" x1="16" y1="17" x2="8" y2="17" />
    <polyline v-if="name === 'file-text2'" points="10,9 9,9 8,9" />
    
    <!-- Calculator Icon (for budget) -->
    <rect v-if="name === 'calculator'" x="4" y="2" width="16" height="20" rx="2" />
    <rect v-if="name === 'calculator'" x="8" y="6" width="8" height="4" rx="1" />
    <rect v-if="name === 'calculator'" x="6" y="12" width="2" height="2" />
    <rect v-if="name === 'calculator'" x="10" y="12" width="2" height="2" />
    <rect v-if="name === 'calculator'" x="14" y="12" width="2" height="2" />
    <rect v-if="name === 'calculator'" x="6" y="16" width="2" height="2" />
    <rect v-if="name === 'calculator'" x="10" y="16" width="2" height="2" />
    <rect v-if="name === 'calculator'" x="14" y="16" width="2" height="2" />
    
    <!-- Award Icon (for criteria) -->
    <circle v-if="name === 'award'" cx="12" cy="8" r="6" />
    <path v-if="name === 'award'" d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11" />
    
    <!-- UserCheck Icon (for reviewers) -->
    <path v-if="name === 'user-check'" d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle v-if="name === 'user-check'" cx="9" cy="7" r="4" />
    <polyline v-if="name === 'user-check'" points="16,11 18,13 22,9" />
    
    <!-- CheckCircle2 Icon (for finalize) -->
    <circle v-if="name === 'check-circle2'" cx="12" cy="12" r="10" />
    <path v-if="name === 'check-circle2'" d="M9 12l2 2 4-4" />
    
    <!-- ChevronUp Icon (for moving items up) -->
    <polyline v-if="name === 'chevron-up'" points="18,15 12,9 6,15" />
    
    <!-- ChevronDown Icon (for moving items down) -->
    <polyline v-if="name === 'chevron-down'" points="6,9 12,15 18,9" />
    
    <!-- Upload Icon -->
    <path v-if="name === 'upload'" d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline v-if="name === 'upload'" points="17,8 12,3 7,8" />
    <line v-if="name === 'upload'" x1="12" y1="3" x2="12" y2="15" />
    
    <!-- Download Icon -->
    <path v-if="name === 'download'" d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline v-if="name === 'download'" points="7,10 12,15 17,10" />
    <line v-if="name === 'download'" x1="12" y1="15" x2="12" y2="3" />
    
    <!-- File Icon -->
    <path v-if="name === 'file'" d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
    <polyline v-if="name === 'file'" points="13,2 13,9 20,9" />
    
    <!-- X Icon (for close/remove) -->
    <line v-if="name === 'x'" x1="18" y1="6" x2="6" y2="18" />
    <line v-if="name === 'x'" x1="6" y1="6" x2="18" y2="18" />
    
    <!-- Loader Icon (spinning) -->
    <line v-if="name === 'loader'" x1="12" y1="2" x2="12" y2="6" />
    <line v-if="name === 'loader'" x1="12" y1="18" x2="12" y2="22" />
    <line v-if="name === 'loader'" x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
    <line v-if="name === 'loader'" x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
    <line v-if="name === 'loader'" x1="2" y1="12" x2="6" y2="12" />
    <line v-if="name === 'loader'" x1="18" y1="12" x2="22" y2="12" />
    <line v-if="name === 'loader'" x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
    <line v-if="name === 'loader'" x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    
    <!-- RefreshCw Icon -->
    <polyline v-if="name === 'refresh-cw'" points="23,4 23,10 17,10" />
    <polyline v-if="name === 'refresh-cw'" points="1,20 1,14 7,14" />
    <path v-if="name === 'refresh-cw'" d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    
    <!-- Info Icon -->
    <circle v-if="name === 'info'" cx="12" cy="12" r="10" />
    <line v-if="name === 'info'" x1="12" y1="16" x2="12" y2="12" />
    <line v-if="name === 'info'" x1="12" y1="8" x2="12.01" y2="8" />
    
    <!-- AlertTriangle Icon -->
    <path v-if="name === 'alert-triangle'" d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line v-if="name === 'alert-triangle'" x1="12" y1="9" x2="12" y2="13" />
    <line v-if="name === 'alert-triangle'" x1="12" y1="17" x2="12.01" y2="17" />
    
    <!-- Grip Icon (for drag handle - 6 dots) -->
    <circle v-if="name === 'grip'" cx="9" cy="5" r="1.5" />
    <circle v-if="name === 'grip'" cx="15" cy="5" r="1.5" />
    <circle v-if="name === 'grip'" cx="9" cy="12" r="1.5" />
    <circle v-if="name === 'grip'" cx="15" cy="12" r="1.5" />
    <circle v-if="name === 'grip'" cx="9" cy="19" r="1.5" />
    <circle v-if="name === 'grip'" cx="15" cy="19" r="1.5" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { rfpCn } from '@/utils/rfpUtils.js'

interface Props {
  name: 'plus' | 'trash2' | 'save' | 'arrow-right' | 'dollar-sign' | 'calendar' | 'users' | 'target' | 'settings' | 'file-text' | 'lightbulb' | 'clock' | 'check-circle' | 'user' | 'mail' | 'camera' | 'check' | 'file-text2' | 'calculator' | 'award' | 'user-check' | 'check-circle2' | 'chevron-up' | 'chevron-down' | 'upload' | 'download' | 'file' | 'x' | 'loader' | 'refresh-cw' | 'info' | 'alert-triangle' | 'grip'
  size?: number
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 24
})

const iconClasses = computed(() => {
  return rfpCn(
    'shrink-0',
    props.className
  )
})
</script>
