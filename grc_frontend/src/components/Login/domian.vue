<template>
  <div class="domains-container">
    <!-- Modern Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <i class="fas fa-sitemap"></i>
          <div>
            <h1>Domain Management</h1>
            <p class="subtitle">Organize and manage frameworks across different domains using drag & drop</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ domains.length }}</span>
            <span class="stat-label">Domains</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ totalFrameworks }}</span>
            <span class="stat-label">Total Frameworks</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading domains and frameworks...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-message">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Unable to Load Domains</h3>
        <p>{{ error }}</p>
        <button @click="fetchDomains" class="retry-btn">
          <i class="fas fa-redo"></i> Try Again
        </button>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div v-else class="tabs-container">
      <div class="tabs-navigation">
        <button
          v-for="domain in domains"
          :key="domain.domain_id"
          :class="['tab-button', { 'active': activeTab === domain.domain_id }]"
          @click="activeTab = domain.domain_id"
        >
          <i class="fas fa-folder"></i>
          <span>{{ domain.domain_name }}</span>
          <span class="tab-count">{{ domain.frameworks.length }}</span>
        </button>
        
        <button
          :class="['tab-button unlinked-tab', { 'active': activeTab === 'unlinked' }]"
          @click="activeTab = 'unlinked'"
        >
          <i class="fas fa-layer-group"></i>
          <span>Unassigned</span>
          <span class="tab-count warning">{{ unlinkedFrameworks.length }}</span>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Domain Content -->
        <div
          v-for="domain in domains"
          :key="domain.domain_id"
          v-show="activeTab === domain.domain_id"
          class="tab-panel"
          @drop="onDrop($event, domain.domain_id)"
          @dragover="onDragOver($event)"
          @dragleave="onDragLeave"
        >
          <div class="panel-header">
            <div class="panel-title">
              <i class="fas fa-folder-open"></i>
              <h2>{{ domain.domain_name }}</h2>
            </div>
            <span class="panel-badge">{{ domain.frameworks.length }} Frameworks</span>
          </div>

          <div class="frameworks-grid">
            <div
              v-for="framework in domain.frameworks"
              :key="framework.framework_id"
              class="framework-card"
              draggable="true"
              @dragstart="onDragStart($event, framework, domain.domain_id)"
              @dragend="onDragEnd"
              :class="{ 'is-dragging': draggedFramework?.framework_id === framework.framework_id }"
            >
              <div class="card-header">
                <i class="fas fa-grip-vertical drag-icon"></i>
                <h3>{{ framework.framework_name }}</h3>
                <button 
                  @click="removeFrameworkFromDomain(framework.framework_id)"
                  class="remove-btn"
                  title="Remove from domain"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <div class="card-footer">
                <span class="version-badge">v{{ framework.current_version }}</span>
                <span class="status-badge" :class="getStatusClass(framework.status)">
                  <i class="fas fa-circle"></i> {{ framework.status }}
                </span>
              </div>
            </div>

            <!-- Empty State -->
            <div 
              v-if="domain.frameworks.length === 0"
              class="empty-state"
            >
              <i class="fas fa-inbox"></i>
              <h3>No Frameworks Assigned</h3>
              <p>Drag and drop frameworks from the "Unassigned" tab to add them here</p>
            </div>
          </div>
        </div>

        <!-- Unlinked Frameworks Content -->
        <div
          v-show="activeTab === 'unlinked'"
          class="tab-panel unlinked-panel"
          @drop="onDrop($event, null)"
          @dragover="onDragOver($event)"
          @dragleave="onDragLeave"
        >
          <div class="panel-header">
            <div class="panel-title">
              <i class="fas fa-layer-group"></i>
              <h2>Unassigned Frameworks</h2>
            </div>
            <span class="panel-badge warning">{{ unlinkedFrameworks.length }} Frameworks</span>
          </div>

          <div class="frameworks-grid">
            <div
              v-for="framework in unlinkedFrameworks"
              :key="framework.framework_id"
              class="framework-card unlinked-card"
              draggable="true"
              @dragstart="onDragStart($event, framework, null)"
              @dragend="onDragEnd"
              :class="{ 'is-dragging': draggedFramework?.framework_id === framework.framework_id }"
            >
              <div class="card-header">
                <i class="fas fa-grip-vertical drag-icon"></i>
                <h3>{{ framework.framework_name }}</h3>
              </div>
              <div class="card-footer">
                <span class="version-badge">v{{ framework.current_version }}</span>
                <span class="status-badge" :class="getStatusClass(framework.status)">
                  <i class="fas fa-circle"></i> {{ framework.status }}
                </span>
              </div>
            </div>

            <!-- Empty State -->
            <div 
              v-if="unlinkedFrameworks.length === 0"
              class="empty-state success"
            >
              <i class="fas fa-check-circle"></i>
              <h3>All Frameworks Assigned!</h3>
              <p>Every framework has been assigned to a domain</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <transition name="toast">
      <div v-if="toast.show" :class="['toast-notification', toast.type]">
        <i :class="toast.type === 'success' ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
        <span>{{ toast.message }}</span>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
    const activeTab = ref(null) // Active tab tracking

    // Computed property for total frameworks count
    const totalFrameworks = computed(() => {
      const domainFrameworksCount = domains.value.reduce((sum, domain) => sum + domain.frameworks.length, 0)
      return domainFrameworksCount + unlinkedFrameworks.value.length
    })

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
          
          // Set default active tab to first domain or unlinked if no domains
          if (domains.value.length > 0) {
            activeTab.value = domains.value[0].domain_id
          } else {
            activeTab.value = 'unlinked'
          }
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
      totalFrameworks,
      activeTab,
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
/* Main Container - min-height allows content to grow so full page scrolls */
.domains-container {
  margin-left: 240px;
  margin-top: 80px;
  width: calc(100% - 240px);
  min-height: calc(100vh - 80px);
  background: #ffffff;
  overflow: visible;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* Modern Header */
.page-header {
  background: white;
  border-bottom: 1px solid #e1e8ed;
  padding: 24px 32px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title > i {
  font-size: 32px;
  color: #003399;
  background: linear-gradient(135deg, #003399 0%, #0055cc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-title h1 {
  font-size: 26px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.subtitle {
  color: #64748b;
  font-size: 14px;
  margin: 0;
  font-weight: 400;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #003399;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: linear-gradient(to bottom, transparent, #cbd5e1, transparent);
}

/* Loading & Error States */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(0, 51, 153, 0.1);
  border-top: 4px solid #003399;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-container p {
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
}

.error-message {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  max-width: 400px;
}

.error-message i {
  font-size: 56px;
  color: #ef4444;
  margin-bottom: 20px;
}

.error-message h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 8px 0;
}

.error-message p {
  color: #64748b;
  font-size: 14px;
  margin: 0 0 24px 0;
}

.retry-btn {
  padding: 12px 28px;
  background: linear-gradient(135deg, #003399 0%, #0055cc 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 51, 153, 0.2);
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 51, 153, 0.3);
}

/* Tabs Container - allow content to flow so page scroll shows all content */
.tabs-container {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  overflow: visible;
}

/* Tabs Navigation */
.tabs-navigation {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px 32px;
  background: white;
  border-bottom: 2px solid #e2e8f0;
  flex-shrink: 0;
}

/* Tab Button */
.tab-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 20px;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  flex: 0 0 calc(33.333% - 8px);
  min-width: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tab-button i {
  font-size: 16px;
  flex-shrink: 0;
}

.tab-button span:first-of-type {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-button:hover {
  color: #003399;
  background: #f0f7ff;
  border-color: #003399;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 51, 153, 0.15);
}

.tab-button.active {
  color: white;
  background: linear-gradient(135deg, #003399 0%, #0055cc 100%);
  border-color: #003399;
  box-shadow: 0 4px 12px rgba(0, 51, 153, 0.25);
}

.tab-button.active .tab-count {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

.tab-button.unlinked-tab:hover {
  color: #f59e0b;
  background: #fffbf0;
  border-color: #f59e0b;
}

.tab-button.unlinked-tab.active {
  color: white;
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  border-color: #f59e0b;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
}

.tab-count {
  background: #e2e8f0;
  color: #475569;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  min-width: 28px;
  text-align: center;
  flex-shrink: 0;
}

.tab-button.unlinked-tab .tab-count.warning {
  background: #fed7aa;
  color: #92400e;
}

.tab-button.unlinked-tab.active .tab-count.warning {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

/* Tab Content - scrollable when tall; overflow-y auto with visible scrollbar */
.tab-content {
  flex: 1 1 auto;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: min(600px, 60vh);
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f8fafc;
}

.tab-content::-webkit-scrollbar {
  width: 10px;
}

.tab-content::-webkit-scrollbar-track {
  background: #f8fafc;
}

.tab-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

.tab-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Tab Panel */
.tab-panel {
  padding: 32px;
  min-height: calc(100% - 64px);
  transition: background 0.3s ease;
}

.tab-panel.drag-over {
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
}

.tab-panel.unlinked-panel.drag-over {
  background: linear-gradient(135deg, #fffbf0 0%, #ffffff 100%);
}

/* Panel Header */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e2e8f0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.panel-title i {
  font-size: 28px;
  color: #003399;
}

.unlinked-panel .panel-title i {
  color: #f59e0b;
}

.panel-title h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.panel-badge {
  background: #f1f5f9;
  color: #475569;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
}

.panel-badge.warning {
  background: #fef3c7;
  color: #92400e;
}

/* Frameworks Grid */
.frameworks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  width: 100%;
}

/* Framework Cards */
.framework-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px;
  cursor: grab;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  -webkit-user-select: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.framework-card:hover {
  border-color: #003399;
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 51, 153, 0.12);
}

.framework-card:active {
  cursor: grabbing;
}

.framework-card.is-dragging {
  opacity: 0.5;
  transform: scale(0.98) rotate(2deg);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.2);
}

.unlinked-card {
  border-color: #fed7aa;
  background: linear-gradient(135deg, #fffbf5 0%, white 100%);
}

.unlinked-card:hover {
  border-color: #fbbf24;
  box-shadow: 0 8px 20px rgba(251, 191, 36, 0.15);
}

/* Card Header */
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.drag-icon {
  color: #94a3b8;
  font-size: 14px;
  cursor: grab;
  margin-top: 2px;
  transition: color 0.2s;
}

.framework-card:hover .drag-icon {
  color: #003399;
}

.drag-icon:active {
  cursor: grabbing;
}

.card-header h3 {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.remove-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

/* Card Footer */
.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.version-badge {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  text-transform: capitalize;
}

.status-badge i {
  font-size: 6px;
}

.status-badge.status-active {
  background: #dcfce7;
  color: #15803d;
}

.status-badge.status-review {
  background: #fef3c7;
  color: #ca8a04;
}

.status-badge.status-draft {
  background: #fee2e2;
  color: #dc2626;
}

.status-badge.status-default {
  background: #f1f5f9;
  color: #475569;
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 40px;
  text-align: center;
  color: #94a3b8;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  min-height: 400px;
}

.empty-state i {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.3;
  color: #94a3b8;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 12px 0;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  color: #94a3b8;
  max-width: 400px;
}

.empty-state.success {
  border-color: #86efac;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.empty-state.success i {
  opacity: 0.5;
  color: #16a34a;
}

.empty-state.success h3 {
  color: #15803d;
}

.empty-state.success p {
  color: #16a34a;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  bottom: 32px;
  right: 32px;
  padding: 16px 24px;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 9999;
  backdrop-filter: blur(10px);
  font-weight: 500;
  font-size: 14px;
  min-width: 280px;
}

.toast-notification.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.toast-notification.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.toast-notification i {
  font-size: 18px;
}

/* Toast Animation */
.toast-enter-active {
  animation: toastIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.toast-leave-active {
  animation: toastOut 0.3s ease-in;
}

@keyframes toastIn {
  from {
    transform: translateX(120%) scale(0.8);
    opacity: 0;
  }
  to {
    transform: translateX(0) scale(1);
    opacity: 1;
  }
}

@keyframes toastOut {
  from {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  to {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
}

/* Responsive Design */
@media (max-width: 1400px) {
  .frameworks-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 1024px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-stats {
    width: 100%;
    justify-content: center;
  }

  .tab-button {
    flex: 0 0 calc(50% - 6px);
  }

  .frameworks-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .domains-container {
    margin-left: 0;
    width: 100%;
    margin-top: 60px;
    min-height: calc(100vh - 60px);
    overflow: visible;
  }

  .page-header {
    padding: 16px 20px;
  }

  .header-title h1 {
    font-size: 22px;
  }

  .subtitle {
    font-size: 13px;
  }

  .header-stats {
    padding: 10px 16px;
    gap: 16px;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 10px;
  }

  .tabs-navigation {
    padding: 12px 20px;
    gap: 10px;
  }

  .tab-button {
    flex: 0 0 100%;
    padding: 14px 16px;
    font-size: 13px;
  }

  .tab-button i {
    font-size: 14px;
  }

  .tab-panel {
    padding: 20px;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 24px;
  }

  .panel-title {
    gap: 12px;
  }

  .panel-title i {
    font-size: 24px;
  }

  .panel-title h2 {
    font-size: 20px;
  }

  .frameworks-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .toast-notification {
    bottom: 20px;
    right: 20px;
    left: 20px;
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .header-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .tab-button {
    padding: 12px 14px;
    font-size: 12px;
  }

  .tab-button i {
    font-size: 13px;
  }

  .tab-count {
    padding: 3px 8px;
    font-size: 11px;
    min-width: 24px;
  }

  .framework-card {
    padding: 14px;
  }

  .card-header h3 {
    font-size: 13px;
  }

  .empty-state {
    padding: 60px 20px;
    min-height: 300px;
  }

  .empty-state i {
    font-size: 48px;
  }

  .empty-state h3 {
    font-size: 18px;
  }

  .empty-state p {
    font-size: 13px;
  }
}
</style>

