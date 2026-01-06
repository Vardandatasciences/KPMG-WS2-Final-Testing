<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-50 flex flex-col transition-all duration-300 border-r border-border bg-background',
      isCollapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Sidebar Header -->
    <div class="flex h-16 items-center justify-between border-b px-4">
      <div v-if="!isCollapsed" class="flex items-center gap-2">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <FileCheck class="h-4 w-4" />
        </div>
        <span class="text-lg font-semibold">ContractHub</span>
      </div>
      <button 
        @click="toggleSidebar" 
        class="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-muted"
      >
        <PanelLeftClose v-if="!isCollapsed" class="h-4 w-4" />
        <PanelLeftOpen v-else class="h-4 w-4" />
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 space-y-2 p-4 overflow-y-auto">
      <!-- Contract Management Section -->
      <div class="space-y-1">
        <div 
          v-if="!isCollapsed" 
          class="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider"
        >
          Contract Management
        </div>
        
        <!-- Contract Items -->
        <div v-for="item in contractItems" :key="item.title" class="space-y-1">
          <div
            v-if="!item.subItems"
            @click="navigateTo(item.url)"
            :class="[
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all cursor-pointer',
              isActive(item.url) 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            ]"
          >
            <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
            <span v-if="!isCollapsed" class="flex-1">{{ item.title }}</span>
          </div>
          
          <!-- Collapsible Item with Sub-items -->
          <Collapsible v-else v-model:open="item.isOpen" class="space-y-1">
            <CollapsibleTrigger
              :class="[
                'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all',
                hasActiveSubItem(item.subItems) 
                  ? 'bg-muted text-foreground' 
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              ]"
            >
              <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
              <span v-if="!isCollapsed" class="flex-1 text-left">{{ item.title }}</span>
              <ChevronDown 
                v-if="!isCollapsed" 
                :class="[
                  'h-4 w-4 transition-transform',
                  item.isOpen ? 'rotate-180' : ''
                ]" 
              />
            </CollapsibleTrigger>
            
            <CollapsibleContent v-if="!isCollapsed" class="space-y-1">
              <div v-for="subItem in item.subItems" :key="subItem.title" class="ml-6 space-y-1">
                <!-- Regular sub-item -->
                <div
                  v-if="!subItem.subItems"
                  @click="navigateTo(subItem.url)"
                  :class="[
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all cursor-pointer',
                    isActive(subItem.url) 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  ]"
                >
                  <component v-if="subItem.icon" :is="subItem.icon" class="h-4 w-4 flex-shrink-0" />
                  <span class="flex-1">{{ subItem.title }}</span>
                </div>
                
                <!-- Nested sub-item with its own sub-items -->
                <Collapsible v-else v-model:open="subItem.isOpen" class="space-y-1">
                  <CollapsibleTrigger
                    :class="[
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all',
                      hasActiveSubItem(subItem.subItems) 
                        ? 'bg-muted text-foreground' 
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    ]"
                  >
                    <component v-if="subItem.icon" :is="subItem.icon" class="h-4 w-4 flex-shrink-0" />
                    <span class="flex-1 text-left">{{ subItem.title }}</span>
                    <ChevronDown 
                      :class="[
                        'h-4 w-4 transition-transform',
                        subItem.isOpen ? 'rotate-180' : ''
                      ]" 
                    />
                  </CollapsibleTrigger>
                  
                  <CollapsibleContent class="space-y-1">
                    <div v-for="nestedItem in subItem.subItems" :key="nestedItem.title" class="ml-6">
                      <div
                        @click="navigateTo(nestedItem.url)"
                        :class="[
                          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all cursor-pointer',
                          isActive(nestedItem.url) 
                            ? 'bg-primary text-primary-foreground' 
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        ]"
                      >
                        <span class="flex-1">{{ nestedItem.title }}</span>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>
    </nav>

    <!-- Footer -->
    <div v-if="!isCollapsed" class="border-t p-4">
      <div class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground">
        <User class="h-4 w-4" />
        <div class="flex-1">
          <div class="font-medium text-foreground">{{ currentUser?.username || 'testuser1' }}</div>
          <div class="text-xs">Contract Manager</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { mapGetters } from 'vuex'
import { 
  FileCheck, 
  BarChart3, 
  FileText, 
  Plus, 
  Eye, 
  Users, 
  CheckCircle, 
  Archive, 
  Search, 
  TrendingUp,
  PanelLeftClose, 
  PanelLeftOpen, 
  ChevronDown,
  User
} from 'lucide-vue-next'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui_contract'

const router = useRouter()
const route = useRoute()

// Sidebar state
const isCollapsed = ref(false)

// Get current user from store
const currentUser = computed(() => {
  // This would come from Vuex store in a real app
  return { username: 'testuser1' }
})

// Contract navigation items
const contractItems = ref([
  { 
    title: "Contract Dashboard", 
    url: "/contractdashboard", 
    icon: BarChart3
  },
  { 
    title: "All Contracts", 
    url: "/contracts", 
    icon: FileText
  },
  { 
    title: "Create Contract", 
    url: "/contracts/new", 
    icon: Plus
  },
  { 
    title: "Vendors", 
    url: "/vendors", 
    icon: Users
  },
  { 
    title: "Approvals", 
    url: "/approvals", 
    icon: CheckCircle
  },
  { 
    title: "Archive", 
    url: "/archive", 
    icon: Archive
  },
  { 
    title: "Search", 
    url: "/search", 
    icon: Search
  },
  { 
    title: "Analytics", 
    url: "/analytics", 
    icon: TrendingUp
  },
  { 
    title: "Audit", 
    url: "/audit/dashboard", 
    icon: Eye,
    isOpen: false,
    subItems: [
      { title: "Audit Dashboard", url: "/audit/dashboard" },
      { title: "All Audits", url: "/audit/all" },
      { title: "Create Audit", url: "/audit/create" },
      { title: "Audit Reports", url: "/audit/reports" },
    ]
  },
])

// Navigation methods
const navigateTo = (url) => {
  router.push(url)
}

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const isActive = (url) => {
  return route.path === url
}

const hasActiveSubItem = (subItems) => {
  return subItems.some(item => isActive(item.url))
}
</script>
