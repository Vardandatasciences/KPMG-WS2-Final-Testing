<template>
  <div class="page-layout">
    <!-- Sidebar -->
    <PolicySidebar />
    
    <!-- Header/Navbar -->
    <GlobalNavbar />
    
    <!-- Main Content Area -->
    <main class="page-layout__content" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <div class="page-layout__content-inner">
        <slot />
      </div>
    </main>
  </div>
</template>

<script>
import PolicySidebar from './Policy/Sidebar.vue'
import GlobalNavbar from './GlobalNavbar.vue'
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'PageLayout',
  components: {
    PolicySidebar,
    GlobalNavbar
  },
  setup() {
    const isSidebarCollapsed = ref(false)
    let observer = null
    
    const checkSidebarState = () => {
      const sidebarElement = document.querySelector('.sidebar')
      if (sidebarElement) {
        isSidebarCollapsed.value = sidebarElement.classList.contains('collapsed')
      }
    }
    
    onMounted(() => {
      // Check initial state
      checkSidebarState()
      
      // Use MutationObserver to watch for sidebar class changes
      const sidebarElement = document.querySelector('.sidebar')
      if (sidebarElement) {
        observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
              checkSidebarState()
            }
          })
        })
        
        observer.observe(sidebarElement, {
          attributes: true,
          attributeFilter: ['class']
        })
      }
      
      // Also listen for custom events if sidebar emits them
      const handleSidebarToggle = (event) => {
        if (event.detail && typeof event.detail.isCollapsed !== 'undefined') {
          isSidebarCollapsed.value = event.detail.isCollapsed
        }
      }
      window.addEventListener('sidebar-toggle', handleSidebarToggle)
      
      // Cleanup function will be called in onUnmounted
      return () => {
        window.removeEventListener('sidebar-toggle', handleSidebarToggle)
      }
    })
    
    onUnmounted(() => {
      if (observer) {
        observer.disconnect()
      }
    })
    
    return {
      isSidebarCollapsed
    }
  }
}
</script>

<style scoped>
.page-layout {
  position: relative;
  min-height: 100vh;
}

.page-layout__content {
  margin-top: 80px; /* Space for fixed header */
  margin-left: 5px; /* Space for fixed sidebar (reduced from 256px) */
  min-height: calc(100vh - 80px);
  transition: margin-left 0.3s ease;
}

.page-layout__content.sidebar-collapsed {
  margin-left: 60px; /* Space for collapsed sidebar (60px width) */
}

.page-layout__content-inner {
  padding: 12px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
</style>
