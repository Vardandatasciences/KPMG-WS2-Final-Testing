<template>
  <div class="domains-container">
    <div class="header">
      <h1><i class="fas fa-sitemap"></i> Domain Management</h1>
      <p class="subtitle">Organize frameworks by domain. Drag and drop frameworks to assign them to domains.</p>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading domains and frameworks...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <div class="error-message">
        <i class="fas fa-exclamation-circle"></i>
        <p>{{ error }}</p>
        <button @click="fetchDomains" class="retry-btn">Retry</button>
      </div>
    </div>

    <div v-else class="domains-content">
      <!-- Domains with their frameworks -->
      <div 
        v-for="domain in domains" 
        :key="domain.domain_id" 
        class="domain-section domain-card"
        @drop="onDrop($event, domain.domain_id)"
        @dragover="onDragOver($event)"
        @dragleave="onDragLeave"
      >
        <div class="domain-header">
          <h2>
            <i class="fas fa-folder"></i>
            {{ domain.domain_name }}
            <span class="framework-count">({{ domain.frameworks.length }})</span>
          </h2>
        </div>
        
        <div class="frameworks-list">
          <div
            v-for="framework in domain.frameworks"
            :key="framework.framework_id"
            class="framework-item"
            draggable="true"
            @dragstart="onDragStart($event, framework, domain.domain_id)"
            @dragend="onDragEnd"
            :class="{ 'dragging': draggedFramework?.framework_id === framework.framework_id }"
          >
            <div class="framework-content">
              <i class="fas fa-grip-vertical drag-handle"></i>
              <div class="framework-info">
                <h3>{{ framework.framework_name }}</h3>
                <div class="framework-meta">
                  <span class="version">v{{ framework.current_version }}</span>
                  <span class="status" :class="getStatusClass(framework.status)">
                    {{ framework.status }}
                  </span>
                </div>
              </div>
              <button 
                @click="removeFrameworkFromDomain(framework.framework_id)"
                class="remove-btn"
                title="Remove from domain"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div 
            v-if="domain.frameworks.length === 0"
            class="empty-state"
          >
            <i class="fas fa-inbox"></i>
            <p>No frameworks assigned. Drag frameworks here to assign them to this domain.</p>
          </div>
        </div>
      </div>

      <!-- Unlinked Frameworks Section -->
      <div 
        class="domain-section domain-card unlinked-section"
        @drop="onDrop($event, null)"
        @dragover="onDragOver($event)"
        @dragleave="onDragLeave"
      >
        <div class="domain-header">
          <h2>
            <i class="fas fa-folder-open"></i>
            Unlinked Frameworks
            <span class="framework-count">({{ unlinkedFrameworks.length }})</span>
          </h2>
        </div>
        
        <div class="frameworks-list">
          <div
            v-for="framework in unlinkedFrameworks"
            :key="framework.framework_id"
            class="framework-item"
            draggable="true"
            @dragstart="onDragStart($event, framework, null)"
            @dragend="onDragEnd"
            :class="{ 'dragging': draggedFramework?.framework_id === framework.framework_id }"
          >
            <div class="framework-content">
              <i class="fas fa-grip-vertical drag-handle"></i>
              <div class="framework-info">
                <h3>{{ framework.framework_name }}</h3>
                <div class="framework-meta">
                  <span class="version">v{{ framework.current_version }}</span>
                  <span class="status" :class="getStatusClass(framework.status)">
                    {{ framework.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div 
            v-if="unlinkedFrameworks.length === 0"
            class="empty-state"
          >
            <i class="fas fa-check-circle"></i>
            <p>All frameworks are assigned to domains.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Success/Error Toast -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      <i :class="toast.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'DomainManagement',
  setup() {
    const domains = ref([])
    const unlinkedFrameworks = ref([])
    const loading = ref(true)
    const error = ref(null)
    const draggedFramework = ref(null)
    const draggedFromDomain = ref(null)
    const toast = ref({ show: false, message: '', type: 'success' })
    const scrollInterval = ref(null)
    const dragOverElement = ref(null)

    const fetchDomains = async () => {
      try {
        loading.value = true
        error.value = null
        
        const token = localStorage.getItem('access_token')
        const response = await axios.get(API_ENDPOINTS.GET_DOMAINS_WITH_FRAMEWORKS, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.data.status === 'success') {
          domains.value = response.data.domains || []
          unlinkedFrameworks.value = response.data.unlinked_frameworks || []
        } else {
          error.value = response.data.message || 'Failed to load domains'
        }
      } catch (err) {
        console.error('Error fetching domains:', err)
        error.value = err.response?.data?.message || 'Failed to load domains and frameworks'
      } finally {
        loading.value = false
      }
    }

    const onDragStart = (event, framework, fromDomainId) => {
      draggedFramework.value = framework
      draggedFromDomain.value = fromDomainId
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', framework.framework_id)
      
      // Add visual feedback
      const frameworkItem = event.currentTarget
      frameworkItem.style.opacity = '0.5'
      frameworkItem.style.cursor = 'grabbing'
      
      // Create a custom drag image
      const dragImage = frameworkItem.cloneNode(true)
      dragImage.style.width = frameworkItem.offsetWidth + 'px'
      dragImage.style.opacity = '0.8'
      document.body.appendChild(dragImage)
      dragImage.style.position = 'absolute'
      dragImage.style.top = '-1000px'
      event.dataTransfer.setDragImage(dragImage, event.offsetX, event.offsetY)
      setTimeout(() => document.body.removeChild(dragImage), 0)
      
      // Start auto-scroll detection
      startAutoScroll()
    }

    const onDragEnd = (event) => {
      const frameworkItem = event.currentTarget
      frameworkItem.style.opacity = '1'
      frameworkItem.style.cursor = 'move'
      
      // Stop auto-scroll
      stopAutoScroll()
      
      // Clear drag over state
      if (dragOverElement.value) {
        dragOverElement.value.classList.remove('drag-over')
        dragOverElement.value = null
      }
    }

    // Auto-scroll functionality
    const startAutoScroll = () => {
      const scrollSpeed = 15
      const scrollZone = 80 // pixels from edge to trigger scroll
      let lastMouseY = 0
      let lastMouseX = 0
      
      const handleDragOver = (e) => {
        const windowHeight = window.innerHeight
        const windowWidth = window.innerWidth
        const mouseY = e.clientY
        const mouseX = e.clientX
        lastMouseY = mouseY
        lastMouseX = mouseX
        
        // Check if near top or bottom of viewport
        if (mouseY < scrollZone) {
          // Scroll up
          if (!scrollInterval.value) {
            scrollInterval.value = setInterval(() => {
              window.scrollBy(0, -scrollSpeed)
              // Also scroll scrollable containers
              scrollScrollableContainers(lastMouseX, lastMouseY)
            }, 16) // ~60fps
          }
        } else if (mouseY > windowHeight - scrollZone) {
          // Scroll down
          if (!scrollInterval.value) {
            scrollInterval.value = setInterval(() => {
              window.scrollBy(0, scrollSpeed)
              // Also scroll scrollable containers
              scrollScrollableContainers(lastMouseX, lastMouseY)
            }, 16)
          }
        } else {
          // Check for horizontal scrolling if needed
          if (mouseX < scrollZone) {
            if (!scrollInterval.value) {
              scrollInterval.value = setInterval(() => {
                window.scrollBy(-scrollSpeed, 0)
              }, 16)
            }
          } else if (mouseX > windowWidth - scrollZone) {
            if (!scrollInterval.value) {
              scrollInterval.value = setInterval(() => {
                window.scrollBy(scrollSpeed, 0)
              }, 16)
            }
          } else {
            // Stop scrolling if not near edges
            stopAutoScroll()
          }
        }
      }
      
      // Add global drag over listener with passive: false for better control
      document.addEventListener('dragover', handleDragOver, { passive: false })
      
      // Store cleanup function
      window._dragOverHandler = handleDragOver
    }

    // Helper function to scroll scrollable containers (like frameworks-list)
    const scrollScrollableContainers = (mouseX, mouseY) => {
      const elements = document.querySelectorAll('.frameworks-list')
      elements.forEach((element) => {
        const rect = element.getBoundingClientRect()
        const isInside = mouseX >= rect.left && mouseX <= rect.right && 
                        mouseY >= rect.top && mouseY <= rect.bottom
        
        if (isInside && element.scrollHeight > element.clientHeight) {
          // Check if mouse is near top or bottom of the container
          const relativeY = mouseY - rect.top
          const containerHeight = rect.height
          const scrollZone = 60
          
          if (relativeY < scrollZone) {
            // Near top - scroll up
            const scrollAmount = Math.max(1, scrollZone - relativeY) / 2
            element.scrollTop = Math.max(0, element.scrollTop - scrollAmount)
          } else if (relativeY > containerHeight - scrollZone) {
            // Near bottom - scroll down
            const scrollAmount = Math.max(1, (relativeY - (containerHeight - scrollZone)) / 2)
            element.scrollTop = Math.min(
              element.scrollHeight - element.clientHeight,
              element.scrollTop + scrollAmount
            )
          }
        }
      })
    }

    const stopAutoScroll = () => {
      if (scrollInterval.value) {
        clearInterval(scrollInterval.value)
        scrollInterval.value = null
      }
      if (window._dragOverHandler) {
        document.removeEventListener('dragover', window._dragOverHandler)
        window._dragOverHandler = null
      }
    }

    // Enhanced drag over handler for visual feedback
    const onDragOver = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      
      // Add visual feedback to drop zone
      const target = event.currentTarget
      if (dragOverElement.value !== target) {
        if (dragOverElement.value) {
          dragOverElement.value.classList.remove('drag-over')
        }
        target.classList.add('drag-over')
        dragOverElement.value = target
      }
    }

    const onDragLeave = (event) => {
      // Only remove class if we're actually leaving the element
      const relatedTarget = event.relatedTarget
      const currentTarget = event.currentTarget
      
      // Check if we're still within the drop zone
      if (!currentTarget.contains(relatedTarget)) {
        currentTarget.classList.remove('drag-over')
        if (dragOverElement.value === currentTarget) {
          dragOverElement.value = null
        }
      }
    }

    const onDrop = async (event, targetDomainId) => {
      event.preventDefault()
      
      if (!draggedFramework.value) return

      const frameworkId = draggedFramework.value.framework_id
      const fromDomainId = draggedFromDomain.value
      
      // Don't do anything if dropped in the same place
      if (fromDomainId === targetDomainId) {
        draggedFramework.value = null
        draggedFromDomain.value = null
        return
      }

      try {
        const token = localStorage.getItem('access_token')
        const response = await axios.post(
          API_ENDPOINTS.UPDATE_FRAMEWORK_DOMAIN,
          {
            framework_id: frameworkId,
            domain_id: targetDomainId
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )

        if (response.data.status === 'success') {
          showToast('Framework moved successfully', 'success')
          
          // Update local state immediately for better UX
          const framework = draggedFramework.value
          
          // Remove from old location
          if (fromDomainId === null) {
            // Was in unlinked
            unlinkedFrameworks.value = unlinkedFrameworks.value.filter(
              f => f.framework_id !== frameworkId
            )
          } else {
            // Was in a domain
            const fromDomain = domains.value.find(d => d.domain_id === fromDomainId)
            if (fromDomain) {
              fromDomain.frameworks = fromDomain.frameworks.filter(
                f => f.framework_id !== frameworkId
              )
            }
          }
          
          // Add to new location
          if (targetDomainId === null) {
            // Moving to unlinked
            unlinkedFrameworks.value.push(framework)
          } else {
            // Moving to a domain
            const targetDomain = domains.value.find(d => d.domain_id === targetDomainId)
            if (targetDomain) {
              targetDomain.frameworks.push(framework)
            }
          }
        } else {
          showToast(response.data.message || 'Failed to update framework domain', 'error')
          // Refresh data on error
          await fetchDomains()
        }
      } catch (err) {
        console.error('Error updating framework domain:', err)
        showToast(err.response?.data?.message || 'Failed to update framework domain', 'error')
        // Refresh data on error
        await fetchDomains()
      } finally {
        draggedFramework.value = null
        draggedFromDomain.value = null
      }
    }

    const removeFrameworkFromDomain = async (frameworkId) => {
      if (!confirm('Are you sure you want to remove this framework from its domain?')) {
        return
      }

      try {
        const token = localStorage.getItem('access_token')
        const response = await axios.post(
          API_ENDPOINTS.UPDATE_FRAMEWORK_DOMAIN,
          {
            framework_id: frameworkId,
            domain_id: null
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )

        if (response.data.status === 'success') {
          showToast('Framework removed from domain', 'success')
          await fetchDomains()
        } else {
          showToast(response.data.message || 'Failed to remove framework', 'error')
        }
      } catch (err) {
        console.error('Error removing framework:', err)
        showToast(err.response?.data?.message || 'Failed to remove framework', 'error')
      }
    }

    const getStatusClass = (status) => {
      const statusLower = (status || '').toLowerCase()
      if (statusLower.includes('active')) return 'status-active'
      if (statusLower.includes('review')) return 'status-review'
      if (statusLower.includes('draft')) return 'status-draft'
      return 'status-default'
    }

    const showToast = (message, type = 'success') => {
      toast.value = { show: true, message, type }
      setTimeout(() => {
        toast.value.show = false
      }, 3000)
    }

    onMounted(() => {
      fetchDomains()
    })

    // Cleanup on unmount
    onUnmounted(() => {
      stopAutoScroll()
    })

    return {
      domains,
      unlinkedFrameworks,
      loading,
      error,
      draggedFramework,
      onDragStart,
      onDragEnd,
      onDrop,
      onDragOver,
      onDragLeave,
      removeFrameworkFromDomain,
      getStatusClass,
      toast,
      fetchDomains
    }
  }
}
</script>

<style scoped>
.domains-container {
  padding: 24px;
  margin-left: 240px; /* Account for sidebar width */
  margin-top: 80px; /* Account for navbar height */
  width: calc(100% - 240px);
  max-width: calc(100vw - 240px);
  height: calc(100vh - 80px);
  max-height: calc(100vh - 80px);
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.domains-container::-webkit-scrollbar {
  width: 8px;
}

.domains-container::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.domains-container::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.domains-container::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.header {
  margin-bottom: 32px;
}

.header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  flex-wrap: wrap;
}

.header h1 i {
  color: #003399;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #003399;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #d32f2f;
}

.error-message i {
  font-size: 48px;
  margin-bottom: 16px;
}

.retry-btn {
  margin-top: 16px;
  padding: 10px 24px;
  background: #003399;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn:hover {
  background: #002266;
}

.domains-content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.domain-section {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  box-sizing: border-box;
}

.domain-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: fit-content;
}

.domain-section:hover {
  border-color: #003399;
  box-shadow: 0 4px 12px rgba(0, 51, 153, 0.15);
}

.domain-section.drag-over {
  border-color: #003399;
  background: #f0f4ff;
  box-shadow: 0 6px 16px rgba(0, 51, 153, 0.2);
}

.unlinked-section {
  border-color: #ff9800;
  background: #fff8f0;
}

.unlinked-section:hover {
  border-color: #f57c00;
}

.domain-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
  flex-shrink: 0;
}

.domain-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  min-width: 0;
  flex: 1;
}

.domain-header h2 i {
  color: #003399;
}

.unlinked-section .domain-header h2 i {
  color: #ff9800;
}

.framework-count {
  font-size: 14px;
  font-weight: 400;
  color: #666;
  margin-left: 8px;
}

.frameworks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 400px);
  scroll-behavior: smooth;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.frameworks-list::-webkit-scrollbar {
  width: 8px;
}

.frameworks-list::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.frameworks-list::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.frameworks-list::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.framework-item {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  cursor: grab;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  user-select: none;
  -webkit-user-select: none;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
}

.framework-item:active {
  cursor: grabbing;
}

.framework-item:hover {
  background: #f0f4ff;
  border-color: #003399;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 51, 153, 0.15);
}

.framework-item.dragging {
  opacity: 0.5;
  border-color: #003399;
  background: #e8f0fe;
}

.framework-content {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  width: 100%;
}

.drag-handle {
  color: #999;
  cursor: grab;
  font-size: 16px;
}

.drag-handle:active {
  cursor: grabbing;
}

.framework-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.framework-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  line-height: 1.4;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
}

.framework-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.version {
  font-size: 12px;
  color: #666;
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 4px;
}

.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-active {
  background: #c8e6c9;
  color: #2e7d32;
}

.status-review {
  background: #fff9c4;
  color: #f57f17;
}

.status-draft {
  background: #ffccbc;
  color: #d84315;
}

.status-default {
  background: #e0e0e0;
  color: #616161;
}

.remove-btn {
  background: transparent;
  border: none;
  color: #d32f2f;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: #ffebee;
  color: #b71c1c;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

.toast.success {
  background: #4caf50;
  color: white;
}

.toast.error {
  background: #f44336;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 1400px) {
  .domains-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .domains-container {
    padding: 16px;
    margin-left: 0;
    width: 100%;
    max-width: 100vw;
    margin-top: 60px;
    height: calc(100vh - 60px);
    max-height: calc(100vh - 60px);
  }

  .domain-section {
    padding: 16px;
  }

  .framework-content {
    flex-wrap: wrap;
  }
  
  .frameworks-list {
    max-height: calc(100vh - 350px);
  }
}
</style>

