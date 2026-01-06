<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p class="text-muted-foreground">
          Welcome back! Here's an overview of your RFP activities.
        </p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" as-child>
          <a href="/rfp-list">
            <FileText class="h-4 w-4 mr-2" />
            Manage RFPs
          </a>
        </Button>
        <Button variant="outline" as-child>
          <a href="/rfp-analytics">
            <BarChart3 class="h-4 w-4 mr-2" />
            View Analytics
          </a>
        </Button>
        <Button as-child class="gradient-primary">
          <a href="/rfp-creation">
            <Plus class="h-4 w-4 mr-2" />
            Create RFP
          </a>
        </Button>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-4 gap-3">
      <Card v-for="(kpi, index) in kpiData" :key="index" :class="`phase-card enhanced-card compact-card border-l-4 ${kpi.borderColor}`">
        <div class="flex flex-row items-center justify-between p-3">
          <div class="flex-1 pr-2">
            <h3 class="text-sm font-semibold text-gray-700 mb-1 leading-tight">{{ kpi.title }}</h3>
            <div class="text-3xl font-bold text-gray-900 mb-1 leading-none">{{ kpi.value }}</div>
            <div class="flex items-center text-xs font-medium text-gray-600 mt-1">
              <component 
                :is="kpi.trend === 'up' ? TrendingUp : TrendingDown" 
                :class="`h-3.5 w-3.5 mr-1 ${kpi.trend === 'up' ? 'text-success' : 'text-destructive'}`" 
              />
              <span class="truncate">{{ kpi.change }}</span>
            </div>
          </div>
          <div :class="`icon-wrapper-compact bg-blue-100`">
            <component :is="kpi.icon" :class="`h-12 w-12 text-blue-600`" />
          </div>
        </div>
      </Card>
    </div>

    <!-- Recent RFPs -->
    <Card class="phase-card">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-lg font-semibold">Recent RFPs</h3>
            <p class="text-sm text-muted-foreground">
              Your most recent RFP activities
            </p>
          </div>
          <Button variant="outline" size="sm" as-child>
            <a href="/rfp-list">
              View All
              <ArrowRight class="h-4 w-4 ml-2" />
            </a>
          </Button>
        </div>
        <div class="space-y-4">
          <div 
            v-for="rfp in recentRFPs" 
            :key="rfp.id" 
            class="flex flex-col sm:flex-row sm:items-center justify-between p-4 border border-border rounded-lg hover-lift cursor-pointer"
            @click="navigateToPhase(rfp.phase)"
          >
            <div class="space-y-2 sm:space-y-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-medium">{{ rfp.id }}</span>
                <Badge :class="getStatusColor(rfp.status)">
                  {{ rfp.status }}
                </Badge>
              </div>
              <h3 class="font-medium">{{ rfp.title }}</h3>
              <div class="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Phase {{ rfp.phase }}/{{ rfp.totalPhases }}</span>
                <span>{{ rfp.value }}</span>
                <span class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ rfp.deadline }}
                </span>
                <span class="flex items-center gap-1">
                  <Users class="h-3 w-3" />
                  {{ rfp.vendors }} vendors
                </span>
              </div>
            </div>
            <div class="mt-3 sm:mt-0 sm:w-32">
              <Progress :value="(rfp.phase / rfp.totalPhases) * 100" class="h-2" />
              <span class="text-xs text-muted-foreground mt-1 block">
                {{ Math.round((rfp.phase / rfp.totalPhases) * 100) }}% complete
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw, onMounted, computed } from 'vue'
import Card from '@/components_rfp/Card.vue'
import Button from '@/components_rfp/Button.vue'
import Badge from '@/components_rfp/rfpBadge.vue'
import Progress from '@/components_rfp/rfpProgress.vue'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
// Router removed - using MPA navigation
import { useRFPStore } from '@/store/index_rfp'

// Icons
const FileText = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>'
})

const Building2 = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>'
})

const Target = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
})

const DollarSign = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" /></svg>'
})

const TrendingUp = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>'
})

const TrendingDown = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>'
})

const Clock = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
})

const Users = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" /></svg>'
})

const Plus = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>'
})

const ArrowRight = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>'
})

const BarChart3 = markRaw({
  template: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>'
})

// Navigation functions for MPA
const navigateToPage = (url: string) => {
  window.location.href = url
}
const rfpStore = useRFPStore()

// Fetch RFPs when component mounts
onMounted(async () => {
  await loggingService.logRFPView()
  try {
    await rfpStore.fetchRFPs()
    console.log('RFPs loaded:', rfpStore.rfps)
  } catch (error) {
    console.error('Error loading RFPs:', error)
  }
})

// Computed properties for KPIs based on real data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const kpiData = computed(() => [
  {
    title: "Active RFPs",
    value: rfpStore.rfps.filter((rfp: any) => rfp.status === 'in_review' || rfp.status === 'published' || rfp.status === 'submission_open').length.toString(),
    change: "Real-time data",
    trend: "up",
    icon: FileText,
    borderColor: "border-l-blue-500",
  },
  {
    title: "Draft RFPs",
    value: rfpStore.rfps.filter((rfp: any) => rfp.status === 'draft').length.toString(),
    change: "Real-time data",
    trend: "up",
    icon: Building2,
    borderColor: "border-l-blue-500",
  },
  {
    title: "Total RFPs",
    value: rfpStore.rfps.length.toString(),
    change: "Real-time data",
    trend: "up",
    icon: Target,
    borderColor: "border-l-blue-500",
  },
  {
    title: "Evaluation Criteria",
    value: rfpStore.rfps.reduce((total: number, rfp: any) => total + (rfp.criteriaCount || 0), 0).toString(),
    change: "Real-time data",
    trend: "up",
    icon: DollarSign,
    borderColor: "border-l-blue-500",
  },
])

// Recent RFPs Data - use real data from store
const recentRFPs = computed(() => {
  return rfpStore.rfps.slice(0, 4).map((rfp: any) => ({
    id: rfp.rfp_number || rfp.id,
    title: rfp.title,
    status: rfp.status,
    phase: getPhaseFromStatus(rfp.status),
    totalPhases: 10,
    value: formatBudget(rfp.budgetMin, rfp.budgetMax),
    deadline: formatDate(rfp.deadline),
    vendors: 0, // TODO: Add vendor count when available
  }))
})

// Helper functions
const getPhaseFromStatus = (status: string) => {
  switch (status) {
    case 'draft': return 1
    case 'in_review': return 2
    case 'published': return 3
    case 'submission_open': return 4
    case 'evaluation': return 6
    case 'awarded': return 9
    case 'cancelled': return 10
    default: return 1
  }
}

const formatBudget = (min: string, max: string) => {
  if (!min && !max) return 'Not specified'
  if (min && max) return `$${Number(min).toLocaleString()} - $${Number(max).toLocaleString()}`
  if (min) return `$${Number(min).toLocaleString()}+`
  if (max) return `Up to $${Number(max).toLocaleString()}`
  return 'Not specified'
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'Not set'
  return new Date(dateString).toLocaleDateString()
}

// Helper functions
const getStatusColor = (status: string) => {
  switch (status) {
    case "draft": return "status-badge draft"
    case "review": return "status-badge review"
    case "active": return "status-badge active"
    case "evaluation": return "status-badge evaluation"
    case "awarded": return "status-badge awarded"
    case "rejected": return "status-badge rejected"
    default: return "status-badge draft"
  }
}

const navigateToPhase = (phase: number) => {
  // Map phase numbers to new route names
  const phaseRoutes = {
    1: '/rfp-creation',
    2: '/rfp-approval', 
    3: '/rfp-vendor-selection',
    4: '/rfp-url-generation',
    5: '/vendor-portal',
    6: '/rfp-evaluation',
    7: '/rfp-comparison',
    8: '/rfp-consensus',
    9: '/rfp-consensus', // Award is now combined with Consensus
    10: '/rfp-dashboard'
  }
  
  const route = phaseRoutes[phase] || '/rfp-creation'
  window.location.href = route
}
</script>

<style scoped>
/* Dashboard-specific styles to match React version */
.phase-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm;
}

.enhanced-card {
  @apply transition-all duration-200 hover:shadow-lg hover:border-gray-300;
}

.compact-card {
  @apply overflow-hidden;
  min-height: auto;
  background: linear-gradient(145deg, #ffffff 0%, #f9fafb 100%);
}

.icon-wrapper-compact {
  @apply p-2 rounded-lg flex items-center justify-center flex-shrink-0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease-in-out;
}

.enhanced-card:hover .icon-wrapper-compact {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.icon-wrapper {
  @apply p-3 rounded-xl flex items-center justify-center flex-shrink-0;
}

.hover-lift {
  @apply transition-all duration-200 hover:shadow-md hover:-translate-y-0.5;
}

.text-muted-foreground {
  @apply text-gray-500;
}

.text-success {
  @apply text-green-600;
}

.text-destructive {
  @apply text-red-600;
}

.text-warning {
  @apply text-yellow-600;
}

.text-info {
  @apply text-blue-600;
}

.text-primary {
  @apply text-blue-600;
}

.bg-destructive {
  @apply bg-red-100;
}

.text-destructive-foreground {
  @apply text-red-800;
}

.bg-warning {
  @apply bg-yellow-100;
}

.text-warning-foreground {
  @apply text-yellow-800;
}

.bg-muted {
  @apply bg-gray-100;
}

.text-muted-foreground {
  @apply text-gray-600;
}

.status-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full;
}

.status-badge.draft {
  @apply bg-gray-100 text-gray-800;
}

.status-badge.review {
  @apply bg-blue-100 text-blue-800;
}

.status-badge.active {
  @apply bg-green-100 text-green-800;
}

.status-badge.evaluation {
  @apply bg-yellow-100 text-yellow-800;
}

.status-badge.awarded {
  @apply bg-purple-100 text-purple-800;
}

.status-badge.rejected {
  @apply bg-red-100 text-red-800;
}

.gradient-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800;
}
</style>
