<template>
  <nav class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex">
          <div class="flex-shrink-0 flex items-center">
            <router-link to="/" class="text-xl font-bold text-gray-900">
              RFP Manager
            </router-link>
          </div>
          <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
            <router-link
              v-for="item in navigationItems"
              :key="item.name"
              :to="item.href"
              :class="[
                isActive(item.href)
                  ? 'border-blue-500 text-gray-900'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
                'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium'
              ]"
            >
              {{ item.name }}
            </router-link>
            
            <!-- Evaluation Workflow Dropdown -->
            <div class="relative" @click.stop>
              <button
                @click="toggleEvaluationMenu"
                :class="[
                  isEvaluationActive
                    ? 'border-blue-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
                  'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium'
                ]"
              >
                Evaluation Workflow
                <svg class="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              <!-- Dropdown Menu -->
              <div
                v-if="evaluationMenuOpen"
                class="absolute left-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
              >
                <router-link
                  to="/evaluation-workflow/create"
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  @click="closeEvaluationMenu"
                >
                  Create Workflow
                </router-link>
                <router-link
                  to="/evaluation-workflow/list"
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  @click="closeEvaluationMenu"
                >
                  View Workflows
                </router-link>
                <router-link
                  to="/evaluation-workflow/assign"
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  @click="closeEvaluationMenu"
                >
                  Assign Workflow
                </router-link>
                <router-link
                  to="/rfp-approval/change-request-manager"
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  @click="closeEvaluationMenu"
                >
                  Change Requests
                </router-link>
              </div>
            </div>
          </div>
        </div>
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <button
              class="bg-white p-1 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <span class="sr-only">View notifications</span>
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM9 7H4l5-5v5z" />
              </svg>
            </button>
          </div>
          <div class="ml-3 relative">
            <div>
              <button
                class="bg-white rounded-full flex text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                @click="toggleUserMenu"
              >
                <span class="sr-only">Open user menu</span>
                <div class="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                  <span class="text-sm font-medium text-gray-700">U</span>
                </div>
              </button>
            </div>
            <div
              v-if="userMenuOpen"
              class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none"
            >
              <a href="#" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Your Profile</a>
              <a href="#" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Settings</a>
              <a href="#" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Sign out</a>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Mobile menu -->
    <div class="sm:hidden">
      <div class="pt-2 pb-3 space-y-1">
        <router-link
          v-for="item in navigationItems"
          :key="item.name"
          :to="item.href"
          :class="[
            isActive(item.href)
              ? 'bg-blue-50 border-blue-500 text-blue-700'
              : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700',
            'block pl-3 pr-4 py-2 border-l-4 text-base font-medium'
          ]"
        >
          {{ item.name }}
        </router-link>
        
        <!-- Mobile Evaluation Workflow Menu -->
        <div class="border-t border-gray-200 pt-2 mt-2">
          <div class="pl-3 pr-4 py-2 text-base font-medium text-gray-500">
            Evaluation Workflow
          </div>
          <div class="pl-6 space-y-1">
            <router-link
              to="/evaluation-workflow/create"
              class="block pl-3 pr-4 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700"
            >
              Create Workflow
            </router-link>
            <router-link
              to="/evaluation-workflow/list"
              class="block pl-3 pr-4 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700"
            >
              View Workflows
            </router-link>
            <router-link
              to="/evaluation-workflow/assign"
              class="block pl-3 pr-4 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700"
            >
              Assign Workflow
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const userMenuOpen = ref(false)
const evaluationMenuOpen = ref(false)

const navigationItems = [
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'RFP Workflow', href: '/workflow' },
  { name: 'Vendors', href: '/vendors' },
  { name: 'Evaluations', href: '/evaluations' },
  { name: 'Documents', href: '/documents' },
  { name: 'Communications', href: '/communications' }
]

const isActive = (href: string) => {
  return route.path === href || route.path.startsWith(href + '/')
}

const isEvaluationActive = computed(() => {
  return route.path.startsWith('/evaluation-workflow')
})

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
  evaluationMenuOpen.value = false // Close evaluation menu when opening user menu
}

const toggleEvaluationMenu = () => {
  evaluationMenuOpen.value = !evaluationMenuOpen.value
  userMenuOpen.value = false // Close user menu when opening evaluation menu
}

const closeEvaluationMenu = () => {
  evaluationMenuOpen.value = false
}

// Close menus when clicking outside
document.addEventListener('click', (event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    userMenuOpen.value = false
    evaluationMenuOpen.value = false
  }
})
</script>

<style scoped>
/* Additional component-specific styles can be added here */
</style>
