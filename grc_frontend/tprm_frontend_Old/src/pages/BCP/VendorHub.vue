<template>
  <div class="container mx-auto p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <svg class="h-8 w-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
        </svg>
        <h1 class="text-3xl font-bold">Vendor Hub Overview</h1>
      </div>
      <button class="btn btn--outline">
        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        Export KPIs
      </button>
    </div>

    <!-- Search and Filters -->
    <div class="search-and-filters">
      <div class="search-input-wrapper">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input
          class="search-input input"
          placeholder="Search Vendor"
          v-model="searchTerm"
          @input="handleSearch"
        />
      </div>
      <div class="filter-wrapper">
        <svg class="filter-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
        </svg>
        <select class="filter-select select" v-model="statusFilter" @change="handleFilterChange">
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
    </div>

    <!-- KPI Summary Cards -->
    <div class="kpi-cards-grid">
      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Total Vendors</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ kpiData.totalVendors }}</div>
          <div class="text-xs text-muted-foreground">
            Active: {{ kpiData.activeVendors }} | Inactive: {{ kpiData.inactiveVendors }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Active Plans</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ kpiData.vendorsWithActivePlans }}</div>
          <div class="text-xs text-muted-foreground">
            Vendors with active plans
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Testing Assignments</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ kpiData.vendorsWithTesting }}</div>
          <div class="text-xs text-muted-foreground">
            Vendors with active testing
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground flex items-center gap-2">
            Avg Pass Rate
            <svg class="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
          </h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ kpiData.avgPassRate }}%</div>
          <div class="text-xs text-muted-foreground">
            Pending Evaluations: {{ kpiData.vendorsWithPendingEval }}
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title flex items-center gap-2">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Quick Stats
        </h3>
      </div>
      <div class="card-content">
        <div class="quick-stats-grid">
          <div>
            <div class="font-medium text-muted-foreground">Total Plans</div>
            <div class="text-lg font-semibold">{{ kpiData.totalPlans }}</div>
            <div class="text-xs text-muted-foreground">
              Approved: {{ kpiData.approvedPlans }} | Pending: {{ kpiData.pendingPlans }} | Rejected: {{ kpiData.rejectedPlans }}
            </div>
          </div>
          <div>
            <div class="font-medium text-muted-foreground">Testing Assignments</div>
            <div class="text-lg font-semibold">{{ kpiData.totalTestingAssignments }}</div>
            <div class="text-xs text-muted-foreground">
              In Progress: {{ kpiData.inProgressTesting }} | Completed: {{ kpiData.completedTesting }}
            </div>
          </div>
          <div>
            <div class="font-medium text-muted-foreground">Evaluations</div>
            <div class="text-lg font-semibold">{{ kpiData.totalEvaluations }}</div>
            <div class="text-xs text-muted-foreground">
              In Progress: {{ kpiData.inProgressEvaluations }} | Completed: {{ kpiData.completedEvaluations }}
            </div>
          </div>
          <div>
            <div class="font-medium text-muted-foreground">Avg Test Pass Rate</div>
            <div class="text-lg font-semibold">{{ kpiData.avgTestPassRate }}%</div>
            <div class="text-xs text-muted-foreground">
              Across all vendors
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Vendor Table -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Vendor Directory</h3>
      </div>
      <div class="card-content">
        <table class="table">
          <thead>
            <tr>
              <th>Vendor ID</th>
              <th>Vendor Name</th>
              <th>Active Plans</th>
              <th>Active Testing</th>
              <th>Evaluations</th>
              <th>Pass Rate</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="vendor in filteredVendors" :key="vendor.id">
              <td class="font-mono">{{ vendor.id }}</td>
              <td class="font-medium">{{ vendor.name }}</td>
              <td>{{ vendor.activePlans }}</td>
              <td>{{ vendor.activeTesting }}</td>
              <td>{{ vendor.evaluations }}</td>
              <td>
                <span :class="['badge', getPassRateBadge(vendor.passRate)]">
                  {{ vendor.passRate }}%
                </span>
              </td>
              <td>
                <button
                  class="btn btn--outline btn--sm"
                  @click="handleOpenVendor(vendor.id)"
                >
                  Open ▶
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './VendorHub.css'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const searchTerm = ref("")
const statusFilter = ref("all")

const kpiData = {
  totalVendors: 85,
  activeVendors: 67,
  inactiveVendors: 18,
  vendorsWithActivePlans: 70,
  avgPassRate: 73,
  vendorsWithTesting: 45,
  vendorsWithPendingEval: 33,
  totalPlans: 152,
  approvedPlans: 90,
  pendingPlans: 43,
  rejectedPlans: 19,
  totalTestingAssignments: 105,
  inProgressTesting: 45,
  completedTesting: 60,
  totalEvaluations: 80,
  inProgressEvaluations: 15,
  completedEvaluations: 65,
  avgTestPassRate: 75
}

const vendorData = [
  {
    id: "V-001",
    name: "Mau Cloud Services",
    activePlans: 12,
    activeTesting: 9,
    evaluations: 8,
    passRate: 85,
    status: "active"
  },
  {
    id: "V-002", 
    name: "CoreNet Pvt Ltd",
    activePlans: 7,
    activeTesting: 5,
    evaluations: 6,
    passRate: 78,
    status: "active"
  },
  {
    id: "V-003",
    name: "FinEdge Ltd", 
    activePlans: 6,
    activeTesting: 4,
    evaluations: 4,
    passRate: 72,
    status: "active"
  },
  {
    id: "V-004",
    name: "Branch Systems",
    activePlans: 8,
    activeTesting: 6,
    evaluations: 7,
    passRate: 80,
    status: "active"
  },
  {
    id: "V-005",
    name: "GlobalNet Tech",
    activePlans: 5,
    activeTesting: 3,
    evaluations: 4,
    passRate: 65,
    status: "inactive"
  }
]

const filteredVendors = computed(() => {
  return vendorData.filter(vendor => {
    const matchesSearch = vendor.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
                         vendor.id.toLowerCase().includes(searchTerm.value.toLowerCase())
    const matchesStatus = statusFilter.value === "all" || vendor.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

const handleSearch = async () => {
  // Search is handled automatically by the computed property
  // This function can be used for additional search logic if needed
  if (searchTerm.value.trim()) {
    await showInfo('Searching Vendors', `Searching for vendors matching "${searchTerm.value}"`, {
      action: 'vendor_search',
      search_term: searchTerm.value,
      results_count: filteredVendors.value.length
    })
    PopupService.success(`Searching for vendors matching "${searchTerm.value}"`, 'Searching Vendors')
  }
}

const handleFilterChange = async () => {
  // Filter change is handled automatically by the computed property
  // This function can be used for additional filter logic if needed
  await showInfo('Filter Applied', `Filtering vendors by status: ${statusFilter.value}`, {
    action: 'vendor_filter',
    filter_type: 'status',
    filter_value: statusFilter.value,
    results_count: filteredVendors.value.length
  })
  PopupService.success(`Filtering vendors by status: ${statusFilter.value}`, 'Filter Applied')
}

const getPassRateBadge = (passRate: number) => {
  if (passRate >= 80) return "badge--default"
  if (passRate >= 70) return "badge--secondary" 
  return "badge--destructive"
}

const handleOpenVendor = async (vendorId: string) => {
  try {
    await showInfo('Opening Vendor', `Opening vendor details for ID: ${vendorId}`, {
      action: 'vendor_open',
      vendor_id: vendorId
    })
    PopupService.success(`Opening vendor details for ID: ${vendorId}`, 'Opening Vendor')
    router.push(`/vendor-overview/${vendorId}`)
  } catch (error) {
    await showError('Navigation Failed', 'Failed to open vendor details. Please try again.', {
      action: 'vendor_open_failed',
      vendor_id: vendorId,
      error_message: error.message
    })
    PopupService.error('Failed to open vendor details. Please try again.', 'Navigation Failed')
  }
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Vendor Hub')
})
</script>
