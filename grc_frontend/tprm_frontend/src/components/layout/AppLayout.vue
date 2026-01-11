<template>
  <div class="h-screen">
    <!-- TPRM Sidebar commented out -->
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
// TPRM Sidebar commented out
// import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'

const isSidebarCollapsed = ref(false)

// TPRM Sidebar toggle handler commented out
// const handleSidebarToggle = (collapsed) => {
//   isSidebarCollapsed.value = collapsed
// }
</script>

<style scoped>
.main-content {
  margin-left: 240px; /* 240px margin to prevent overlap with GRC sidebar */
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.3s ease;
}

@media (min-width: 640px) {
  .main-content {
    margin-left: 240px; /* 240px margin to prevent overlap with GRC sidebar */
  }
  
  .main-content.sidebar-collapsed {
    margin-left: 240px; /* Keep 240px margin even when sidebar is collapsed */
  }
}
</style>
