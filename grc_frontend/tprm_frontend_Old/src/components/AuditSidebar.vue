<template>
  <Sidebar :collapsible="true" :default-collapsed="false">
    <!-- Header -->
    <div class="p-4 border-b border-border">
      <div v-if="!isCollapsed" class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
          <Shield class="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-foreground">SLA Audit</h1>
          <p class="text-xs text-muted-foreground">Management System</p>
        </div>
      </div>
      <div v-else class="flex justify-center">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
          <Shield class="w-5 h-5 text-white" />
        </div>
      </div>
    </div>

    <SidebarContent class="py-4">
      <!-- Main Navigation -->
      <SidebarGroup>
        <SidebarGroupLabel :class="isCollapsed ? 'sr-only' : ''">
          Main
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="item in mainItems" :key="item.title">
              <SidebarMenuButton :to="item.url" :active="isActive(item.url)">
                <component :is="item.icon" :class="isCollapsed ? 'h-5 w-5' : 'mr-3 h-4 w-4 flex-shrink-0'" />
                <span v-if="!isCollapsed" class="truncate">{{ item.title }}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <!-- Management Navigation -->
      <SidebarGroup>
        <SidebarGroupLabel :class="isCollapsed ? 'sr-only' : ''">
          Management
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="item in managementItems" :key="item.title">
              <SidebarMenuButton :to="item.url" :active="isActive(item.url)">
                <component :is="item.icon" :class="isCollapsed ? 'h-5 w-5' : 'mr-3 h-4 w-4 flex-shrink-0'" />
                <span v-if="!isCollapsed" class="truncate">{{ item.title }}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
  </Sidebar>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import { 
  FileText, 
  CheckSquare, 
  Eye, 
  BarChart3, 
  Settings, 
  Plus,
  Clock,
  User,
  Shield
} from 'lucide-vue-next'
import Sidebar from '@/components/ui/Sidebar.vue'
import SidebarContent from '@/components/ui/SidebarContent.vue'
import SidebarGroup from '@/components/ui/SidebarGroup.vue'
import SidebarGroupLabel from '@/components/ui/SidebarGroupLabel.vue'
import SidebarGroupContent from '@/components/ui/SidebarGroupContent.vue'
import SidebarMenu from '@/components/ui/SidebarMenu.vue'
import SidebarMenuItem from '@/components/ui/SidebarMenuItem.vue'
import SidebarMenuButton from '@/components/ui/SidebarMenuButton.vue'

const route = useRoute()
const sidebarState = inject('sidebarState', { isCollapsed: false })

const isCollapsed = computed(() => sidebarState.isCollapsed)

const mainItems = [
  { title: "Dashboard", url: "/", icon: BarChart3 },
  { title: "Create Audit", url: "/audit/create", icon: Plus },
  { title: "My Audits", url: "/audit/my-audits", icon: FileText },
  { title: "Review Queue", url: "/audit/review", icon: Eye },
  { title: "Reports", url: "/reports", icon: CheckSquare },
]

const managementItems = [
  { title: "SLA Management", url: "/sla", icon: Shield },
  { title: "User Management", url: "/users", icon: User },
  { title: "Audit History", url: "/audit/history", icon: Clock },
  { title: "Settings", url: "/settings", icon: Settings },
]

const isActive = (path: string) => route.path === path
</script>
