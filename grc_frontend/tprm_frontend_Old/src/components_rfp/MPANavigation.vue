<template>
  <nav class="border-b border-border bg-card">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <h1 class="text-xl font-bold text-primary">RFP Management System</h1>
        </div>
        <div class="flex items-center space-x-4">
          <button @click="navigateTo('Dashboard')" class="nav-link" :class="{ active: isActivePage('Dashboard') }">Dashboard</button>
          <button @click="navigateTo('RFPWorkflow')" class="nav-link" :class="{ active: isActivePage('RFPWorkflow') }">Workflow</button>
          <div class="relative group">
            <button class="nav-link">
              Evaluation workflow
              <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>
            <div class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div class="py-1">
                <button @click="navigateTo('ApprovalManagement')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Workflow creation</button>
                <button @click="navigateTo('MyApprovals')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">My Approvals</button>
                <button @click="navigateTo('AllApprovals')" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">All Approvals</button>
              </div>
            </div>
          </div>
          <DevPhasesDropdown />
          <button @click="navigateTo('Analytics')" class="nav-link" :class="{ active: isActivePage('Analytics') }">Analytics</button>
          <button @click="navigateTo('DraftManager')" class="nav-link" :class="{ active: isActivePage('DraftManager') }">Drafts</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import DevPhasesDropdown from './DevPhasesDropdown.vue'

const router = useRouter()
const route = useRoute()

const currentPage = computed(() => {
  return route.name || 'dashboard'
})

const isActivePage = (page: string) => {
  return currentPage.value === page
}

const navigateTo = (routeName: string) => {
  router.push({ name: routeName })
}
</script>

<style scoped>
.nav-link {
  @apply relative inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors;
}

.nav-link:hover {
  @apply bg-accent text-accent-foreground;
}

.nav-link.active {
  @apply bg-primary text-primary-foreground;
}
</style>
