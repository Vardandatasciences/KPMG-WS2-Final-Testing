<template>
  <div class="h-screen">
    <!-- TPRM Sidebar temporarily commented out -->
    <!-- <AppSidebar @sidebar-toggle="handleSidebarToggle" /> -->
    <div class="main-content" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <AppHeader />
      <main class="flex-1 overflow-x-hidden overflow-y-auto bg-background">
        <div class="container mx-auto px-6 py-8">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
// TPRM Sidebar temporarily commented out
// import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'

const isSidebarCollapsed = ref(false)

const handleSidebarToggle = (collapsed) => {
  isSidebarCollapsed.value = collapsed
}
</script>

<style scoped>
.main-content {
  margin-left: 240px; /* 240px margin to account for GRC sidebar */
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.3s ease;
}

@media (min-width: 640px) {
  /* 240px left margin to prevent overlap with GRC sidebar */
  .main-content {
    margin-left: 240px; /* GRC sidebar width */
  }
  
  .main-content.sidebar-collapsed {
    margin-left: 240px; /* Keep same margin even if TPRM sidebar was collapsed */
  }
}
</style>
