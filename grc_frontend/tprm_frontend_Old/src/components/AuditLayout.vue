<template>
  <div class="min-h-screen flex w-full bg-background">
    <AuditSidebar />
    <div class="flex-1 flex flex-col">
      <header class="h-14 flex items-center border-b border-border bg-card/50 backdrop-blur-sm px-4">
        <SidebarTrigger class="mr-4" />
        <div class="flex items-center space-x-2">
          <h2 class="text-lg font-semibold text-foreground">SLA Audit Management</h2>
        </div>
      </header>
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AuditSidebar from '@/components/AuditSidebar.vue'
import SidebarTrigger from '@/components/ui/SidebarTrigger.vue'
</script>
