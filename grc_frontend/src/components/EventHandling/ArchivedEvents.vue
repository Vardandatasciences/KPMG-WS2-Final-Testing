<template>
  <div class="archived-events-container">
    <!-- Header Section -->
    <div class="archived-events-header">
      <h1 class="archived-events-title">Archived Events</h1>
      <p class="archived-events-subtitle">Repository for archived events and queue items</p>
      <p v-if="isRevalidatingArchived" class="archived-events-revalidating" aria-live="polite">
        Updating…
      </p>
    </div>

    <!-- Tabs Section -->
    <div class="archived-events-navigation">
      <div class="toggle-group">
        <button
          @click="setActiveTab('events')"
          :class="['toggle-button', { active: activeTab === 'events' }]"
        >
          Archived Events
          <span class="archived-events-tab-badge">
            {{ archivedEvents.length }}
          </span>
        </button>
        <button
          @click="setActiveTab('queue')"
          :class="['toggle-button', { active: activeTab === 'queue' }]"
        >
          Archived Queue Items
          <span class="archived-events-tab-badge">
            {{ archivedQueueItems.length }}
          </span>
        </button>
      </div>
    </div>

    <!-- Tab Content -->
    <div v-if="activeTab === 'events'" class="archived-events-content">
      <!-- Empty State for Archived Events -->
      <div v-if="archivedEvents.length === 0" class="archived-events-empty">
        <div class="archived-events-empty-content">
          <div class="archived-events-empty-icon">
            <svg class="archived-events-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
          </div>
          <h3 class="archived-events-empty-title">No Archived Events</h3>
          <p class="archived-events-empty-subtitle">Archived events will appear here when available.</p>
        </div>
      </div>

      <!-- Archived Events Table -->
      <div v-else class="archived-events-table-container">
        <div class="archived-events-table-wrapper">
          <table class="archived-events-table">
            <thead class="archived-events-table-header">
              <tr>
                <th class="archived-events-table-th archived-events-title-col">EVENT TITLE</th>
                <th class="archived-events-table-th archived-events-id-col">EVENT ID</th>
                <th class="archived-events-table-th archived-events-framework-col">FRAMEWORK</th>
                <th class="archived-events-table-th archived-events-category-col">CATEGORY</th>
                <th class="archived-events-table-th archived-events-owner-col">OWNER</th>
                <th class="archived-events-table-th archived-events-date-col">DATE CREATED</th>
                <th class="archived-events-table-th archived-events-actions-col">ACTIONS</th>
              </tr>
            </thead>
            <tbody class="archived-events-table-body">
              <tr v-for="(event, index) in archivedEvents" :key="event.id" 
                  :class="`archived-events-table-row archived-events-row-${index} ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                <td class="archived-events-table-td archived-events-title-cell" data-label="Event Title">
                  <button
                    @click="handleEventClick(event)"
                    :class="`archived-events-title-link archived-events-title-link-${index}`"
                  >
                    {{ event.title }}
                  </button>
                </td>
                <td class="archived-events-table-td archived-events-id-cell" data-label="Event ID">
                  {{ event.id }}
                </td>
                <td class="archived-events-table-td archived-events-framework-cell" data-label="Framework">
                  <div class="archived-events-framework-status">
                    <span class="archived-events-status-dot archived-events-framework-dot"></span>
                    <span class="archived-events-status-text archived-events-framework-text">
                      {{ event.framework }}
                    </span>
                  </div>
                </td>
                <td class="archived-events-table-td archived-events-category-cell" data-label="Category">
                  {{ event.category }}
                </td>
                <td class="archived-events-table-td archived-events-owner-cell" data-label="Owner">
                  {{ event.owner }}
                </td>
                <td class="archived-events-table-td archived-events-date-cell" data-label="Date Created">
                  {{ event.dateCreated }}
                </td>
                <td class="archived-events-table-td archived-events-actions-cell" data-label="Actions">
                  <div class="archived-events-actions">
                    <button
                      @click="handleEventClick(event)"
                      class="action-btn view archived-events-view-btn"
                      title="View Event"
                    >
                      <i class="fas fa-eye"></i>
                    </button>
                    <div
                      @click="handleUnarchive(event.id, 'event')"
                      :disabled="processingItems.has(event.id)"
                      :class="`event-action-icon event-unarchive-icon-${index} ${processingItems.has(event.id) ? 'icon-disabled' : ''}`"
                      title="Unarchive"
                    >
                      <svg v-if="!processingItems.has(event.id)" class="action-icon-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                      </svg>
                      <svg v-else class="action-icon-svg icon-spinning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                      </svg>
                    </div>
                    <div
                      @click="handleDelete(event.id, 'event')"
                      :disabled="processingItems.has(event.id)"
                      :class="`event-action-icon event-delete-icon-${index} ${processingItems.has(event.id) ? 'icon-disabled' : ''}`"
                      title="Delete Permanently"
                    >
                      <svg v-if="!processingItems.has(event.id)" class="action-icon-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                      <svg v-else class="action-icon-svg icon-spinning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'queue'" class="archived-events-content">
      <!-- Empty State for Archived Queue Items -->
      <div v-if="archivedQueueItems.length === 0" class="archived-events-empty">
        <div class="archived-events-empty-content">
          <div class="archived-events-empty-icon">
            <svg class="archived-events-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
          </div>
          <h3 class="archived-events-empty-title">No Archived Queue Items</h3>
          <p class="archived-events-empty-subtitle">Archived queue items will appear here when available.</p>
        </div>
      </div>

      <!-- Archived Queue Items Table -->
      <div v-else class="archived-events-table-container">
        <div class="archived-events-table-wrapper">
          <table class="archived-events-table">
            <thead class="archived-events-table-header">
              <tr>
                <th class="archived-events-table-th archived-events-source-col">SOURCE SYSTEM</th>
                <th class="archived-events-table-th archived-events-title-col">RAW TITLE</th>
                <th class="archived-events-table-th archived-events-type-col">SUGGESTED TYPE</th>
                <th class="archived-events-table-th archived-events-timestamp-col">TIMESTAMP</th>
                <th class="archived-events-table-th archived-events-actions-col">ACTIONS</th>
              </tr>
            </thead>
            <tbody class="archived-events-table-body">
              <tr v-for="(item, index) in archivedQueueItems" :key="item.id" 
                  :class="`archived-events-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                <td class="archived-events-table-td archived-events-source-cell" data-label="Source System">
                  <div class="archived-events-source-status">
                    <span class="archived-events-status-dot archived-events-source-dot"></span>
                    <span class="archived-events-status-text archived-events-source-text">
                      {{ item.sourceSystem }}
                    </span>
                  </div>
                </td>
                <td class="archived-events-table-td archived-events-title-cell" data-label="Raw Title">
                  <button
                    @click="handleQueueItemClick(item)"
                    class="archived-events-title-link"
                  >
                    {{ item.rawTitle }}
                  </button>
                </td>
                <td class="archived-events-table-td archived-events-type-cell" data-label="Suggested Type">
                  <div class="archived-events-type-status">
                    <span class="archived-events-status-dot archived-events-type-dot"></span>
                    <span class="archived-events-status-text archived-events-type-text">
                      {{ item.suggestedType }}
                    </span>
                  </div>
                </td>
                <td class="archived-events-table-td archived-events-timestamp-cell" data-label="Timestamp">
                  {{ item.timestamp }}
                </td>
                <td class="archived-events-table-td archived-events-actions-cell" data-label="Actions">
                  <div class="archived-events-actions">
                    <button
                      @click="handleQueueItemClick(item)"
                      class="action-btn view archived-events-view-btn"
                      title="View Queue Item"
                    >
                      <i class="fas fa-eye"></i>
                    </button>
                    <button
                      @click="handleUnarchive(item.id, 'queue')"
                      :disabled="processingItems.has(item.id)"
                      class="archived-events-action-btn archived-events-action-btn-unarchive"
                      :class="{ 'archived-events-action-btn-disabled': processingItems.has(item.id) }"
                      title="Unarchive"
                    >
                      <svg v-if="!processingItems.has(item.id)" class="archived-events-action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                      </svg>
                      <svg v-else class="archived-events-action-icon archived-events-spinning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                      </svg>
                    </button>
                    <button
                      @click="handleDelete(item.id, 'queue')"
                      :disabled="processingItems.has(item.id)"
                      class="archived-events-action-btn archived-events-action-btn-delete"
                      :class="{ 'archived-events-action-btn-disabled': processingItems.has(item.id) }"
                      title="Delete Permanently"
                    >
                      <svg v-if="!processingItems.has(item.id)" class="archived-events-action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                      <svg v-else class="archived-events-action-icon archived-events-spinning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Event View Popup -->
    <EventViewPopup
      v-if="selectedEvent"
      :event="selectedEvent"
      :is-open="showPopup"
      :show-action-buttons="false"
      @close="closePopup"
    />

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted, onActivated } from 'vue'
import { storeToRefs } from 'pinia'
// import { useRouter } from 'vue-router' // Unused import
import { eventService } from '../../services/api'
import EventViewPopup from './EventViewPopup.vue'
import { PopupService } from '../../modules/popus/popupService'
import PopupModal from '../../modules/popus/PopupModal.vue'
import apiService from '@/services/apiService.js'
import { useEventsStore } from '@/stores/events'

export default {
  name: 'ArchivedEvents',
  components: {
    EventViewPopup,
    PopupModal
  },
  setup() {
    const eventsStore = useEventsStore()
    const { archivedEvents, archivedQueueItems, lastFetchedArchived } = storeToRefs(eventsStore)
    const activeTab = ref('events')
    const error = ref(null)
    const isRevalidatingArchived = computed(
      () =>
        eventsStore.revalidatingArchived ||
        (eventsStore.loading.archived && archivedEvents.value.length > 0)
    )
    const processingItems = ref(new Set()) // Track items being processed
    const selectedFrameworkFromSession = ref(null)
    const selectedEvent = ref(null)
    const showPopup = ref(false)

    const setActiveTab = (tab) => {
      activeTab.value = tab
      
      // Fetch data when switching to queue tab if not already loaded
      if (tab === 'queue' && !lastFetchedArchived.value) {
        void fetchArchivedDomainSafe({ force: false })
      }
    }

    const handleEventClick = (event) => {
      selectedEvent.value = event
      showPopup.value = true
    }

    const handleQueueItemClick = (queueItem) => {
      // Convert queue item to event format for the popup
      const eventData = {
        id: queueItem.id,
        title: queueItem.rawTitle,
        EventTitle: queueItem.rawTitle,
        description: queueItem.description || '',
        framework: queueItem.framework,
        FrameworkName: queueItem.framework,
        category: queueItem.category,
        Category: queueItem.category,
        owner: 'Unknown',
        status: 'Archived',
        Status: 'Archived',
        priority: queueItem.priority,
        Priority: queueItem.priority,
        dateCreated: queueItem.dateCreated,
        CreatedAt: queueItem.dateCreated,
        linkedRecordId: queueItem.linkedRecordId,
        LinkedRecordId: queueItem.linkedRecordId,
        linkedRecordName: queueItem.linkedRecordName,
        LinkedRecordName: queueItem.linkedRecordName,
        sourceSystem: queueItem.sourceSystem,
        suggestedType: queueItem.suggestedType,
        timestamp: queueItem.timestamp
      }
      selectedEvent.value = eventData
      showPopup.value = true
    }

    const closePopup = () => {
      showPopup.value = false
    }

    const handleUnarchive = async (id, type) => {
      try {
        // Add to processing items
        processingItems.value.add(id)
        
        // Get current user ID (you might need to adjust this based on your auth system)
        const userId = 1 // TODO: Get actual user ID from auth context
        
        const response = await eventService.unarchiveEvent(id, userId)
        
        if (response.data.success) {
          console.log(`Successfully unarchived ${type}:`, id)
          
          // Remove the item from the current list immediately
          if (type === 'event') {
            eventsStore.removeArchivedEventLocal(id)
          } else if (type === 'queue') {
            eventsStore.removeArchivedQueueItemLocal(id)
          }
          
          // Emit a custom event to notify other components that an event was unarchived
          window.dispatchEvent(new CustomEvent('eventUnarchived', {
            detail: { eventId: id, eventType: type }
          }))
          
          // Show success popup
          PopupService.success('Item unarchived successfully', 'Success')
        } else {
          PopupService.error(response.data.message || 'Failed to unarchive item', 'Error')
        }
      } catch (err) {
        console.error('Error unarchiving item:', err)
        PopupService.error('Failed to unarchive item. Please try again.', 'Error')
      } finally {
        // Remove from processing items
        processingItems.value.delete(id)
      }
    }

    const handleDelete = async (id, type) => {
      try {
        // Show confirmation popup
        PopupService.confirm(
          'Are you sure you want to permanently delete this item? This action cannot be undone.',
          'Confirm Deletion',
          async () => {
            // User confirmed, proceed with deletion
            await performDelete(id, type)
          },
          () => {
            // User cancelled, do nothing
            console.log('Delete cancelled by user')
          }
        )
      } catch (err) {
        console.error('Error in delete confirmation:', err)
        PopupService.error('Failed to show delete confirmation. Please try again.', 'Error')
      }
    }

    const performDelete = async (id, type) => {
      try {
        
        // Add to processing items
        processingItems.value.add(id)
        
        // Get current user ID (you might need to adjust this based on your auth system)
        const userId = 1 // TODO: Get actual user ID from auth context
        
        const response = await eventService.deleteEventPermanently(id, userId)
        
        if (response.data.success) {
          console.log(`Successfully deleted ${type}:`, id)
          
          // Remove the item from the current list immediately
          if (type === 'event') {
            eventsStore.removeArchivedEventLocal(id)
          } else if (type === 'queue') {
            eventsStore.removeArchivedQueueItemLocal(id)
          }
          
          // Show success popup
          PopupService.success('Item deleted successfully', 'Success')
        } else {
          PopupService.error(response.data.message || 'Failed to delete item', 'Error')
        }
      } catch (err) {
        console.error('Error deleting item:', err)
        PopupService.error('Failed to delete item. Please try again.', 'Error')
      } finally {
        // Remove from processing items
        processingItems.value.delete(id)
      }
    }

    // Check for selected framework from session (similar to other modules)
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in ArchivedEvents...')
        const response = await apiService.get('/api/frameworks/get-selected/')
        
        console.log('🔍 DEBUG: Framework response in ArchivedEvents:', response)
        
        if (response && response.frameworkId) {
          const frameworkIdFromSession = response.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for ArchivedEvents:', frameworkIdFromSession)
          
          // Set the selected framework from session
          selectedFrameworkFromSession.value = frameworkIdFromSession
          console.log('📊 DEBUG: Events are now filtered by framework:', frameworkIdFromSession)
          console.log('📊 DEBUG: selectedFrameworkFromSession.value set to:', selectedFrameworkFromSession.value)
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - showing all events')
          selectedFrameworkFromSession.value = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework in ArchivedEvents:', error)
        selectedFrameworkFromSession.value = null
      }
    }

    const fetchArchivedDomainSafe = async ({ force = false } = {}) => {
      try {
        error.value = null
        console.log('[ArchivedEvents] Fetching archived domain via Pinia (stale-while-revalidate)...')
        await eventsStore.fetchArchivedDomain({ force })
        console.log('Archived events loaded:', archivedEvents.value.length)
      } catch (err) {
        console.error('Error fetching archived events:', err)
        const cached = (eventsStore.events || []).filter((event) => event.status === 'Archived')
        if (cached.length) {
          eventsStore.$patch({ archivedEvents: cached })
          console.log('[ArchivedEvents] API failed, using main-list archived slice:', cached.length)
        } else if (!archivedEvents.value.length) {
          PopupService.error('Failed to fetch archived events. Please try again.', 'Error')
        }
      }
    }

    onMounted(async () => {
      await checkSelectedFrameworkFromSession()
      await fetchArchivedDomainSafe({ force: false })
    })

    onActivated(async () => {
      await fetchArchivedDomainSafe({ force: false })
    })

    return {
      activeTab,
      selectedEvent,
      showPopup,
      error,
      archivedEvents,
      archivedQueueItems,
      lastFetchedArchived,
      isRevalidatingArchived,
      processingItems,
      selectedFrameworkFromSession,
      setActiveTab,
      handleEventClick,
      handleQueueItemClick,
      closePopup,
      handleUnarchive,
      handleDelete,
      fetchArchivedDomainSafe
    }
  }
}
</script>

<style>
/* Archived Events Container - Single container for whole page */
.archived-events-container {
  padding: 10px 5px;
  padding-top: 40px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  border: none;
  min-height: 100vh;
  margin-left: -20px;
  position: relative;
  z-index: 1;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  width: 100%;
}

/* Archived Events Header */
.archived-events-header {
  margin-bottom: 32px;
}

.archived-events-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.archived-events-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.archived-events-revalidating {
  margin: 8px 0 0;
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}


/* Archived Events Tabs - Now using global toggle-group and toggle-button */
.archived-events-navigation {
  margin-bottom: 32px;
  display: flex;
  width: 100%;
}

.archived-events-navigation .toggle-group {
  margin: 0;
  width: 100%;
}

/* Ensure toggle buttons display content (text + badge) in a row */
.archived-events-navigation .toggle-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Badge styling for toggle buttons - scoped to ArchivedEvents */
.archived-events-tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 6px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #4b5563;
  font-size: 0.875rem;
  font-weight: 600;
  flex-shrink: 0;
  transition: all 0.2s ease;
  visibility: visible !important;
  opacity: 1 !important;
  line-height: 1;
}

.archived-events-navigation .toggle-button.active .archived-events-tab-badge {
  background: #3d5afe;
  color: white;
}

/* Colorblindness support for badges */
[data-colorblind="protanopia"] .archived-events-tab-badge,
[data-colorblind="deuteranopia"] .archived-events-tab-badge,
[data-colorblind="tritanopia"] .archived-events-tab-badge {
  background: #d1d5db;
  color: #374151;
}

[data-colorblind="protanopia"] .archived-events-navigation .toggle-button.active .archived-events-tab-badge,
[data-colorblind="deuteranopia"] .archived-events-navigation .toggle-button.active .archived-events-tab-badge {
  background: #3d5afe;
  color: white;
}

[data-colorblind="tritanopia"] .archived-events-navigation .toggle-button.active .archived-events-tab-badge {
  background: #7c3aed;
  color: white;
}

/* Empty State */
.archived-events-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.archived-events-empty-content {
  text-align: center;
}

.archived-events-empty-icon {
  margin-bottom: 16px;
}

.archived-events-empty-svg {
  width: 48px;
  height: 48px;
  color: #9ca3af;
  margin: 0 auto;
}

.archived-events-empty-title {
  font-size: 1.1rem;
  color: #6b7280;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.archived-events-empty-subtitle {
  font-size: 0.9rem;
  color: #9ca3af;
  margin: 0;
}

/* Archived Events Content */
.archived-events-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Archived Events Table */
.archived-events-table-container {
  overflow: hidden;
}

.archived-events-table-wrapper {
  overflow-x: auto;
}

.archived-events-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.archived-events-table-header {
  background: transparent;
}

.archived-events-table-th {
  padding: 16px 20px;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
  background: transparent;
  box-shadow: none;
}

.archived-events-title-col {
  min-width: 250px;
}

.archived-events-id-col {
  min-width: 100px;
  max-width: 100px;
}

.archived-events-framework-col {
  min-width: 150px;
}

.archived-events-category-col {
  min-width: 120px;
  max-width: 120px;
}

.archived-events-owner-col {
  min-width: 150px;
}

.archived-events-date-col {
  min-width: 140px;
  max-width: 140px;
}

.archived-events-source-col {
  min-width: 150px;
}

.archived-events-type-col {
  min-width: 150px;
}

.archived-events-timestamp-col {
  min-width: 140px;
  max-width: 140px;
}

.archived-events-actions-col {
  min-width: 120px;
  max-width: 120px;
}

.archived-events-table-body {
  background: transparent;
}

.archived-events-table-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #e5e7eb;
}

.archived-events-table-row:hover {
  background: #f9fafb !important;
  transform: none;
  box-shadow: none !important;
}

.events-row-even {
  background: transparent;
}

.events-row-odd {
  background: transparent;
}

.archived-events-table-td {
  padding: 16px 20px;
  font-size: 0.9rem;
  color: #374151;
  vertical-align: middle;
  text-align: left;
  display: table-cell;
}

.archived-events-title-cell {
  text-align: left;
}

/* Event Title Links - Remove all blue containers */
.archived-events-title-link,
.archived-events-title-link-0,
.archived-events-title-link-1,
.archived-events-title-link-2,
.archived-events-title-link-3,
.archived-events-title-link-4 {
  color: #374151 !important;
  text-decoration: none !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  text-align: left !important;
  display: block !important;
  width: 100% !important;
  background: none !important;
  border: none !important;
  padding: 8px 0 !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  line-height: 1.4 !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

.archived-events-title-link:hover,
.archived-events-title-link-0:hover,
.archived-events-title-link-1:hover,
.archived-events-title-link-2:hover,
.archived-events-title-link-3:hover,
.archived-events-title-link-4:hover {
  color: #1f2937 !important;
  text-decoration: underline !important;
  background: none !important;
  box-shadow: none !important;
}

.archived-events-id-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 600;
}

.archived-events-framework-cell {
  text-align: left;
}

.archived-events-framework-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.archived-events-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.archived-events-status-text {
  font-size: 0.75rem;
  font-weight: 600;
}

.archived-events-framework-dot {
  background-color: #60A5FA;
}

.archived-events-framework-text {
  color: #60A5FA;
}

.archived-events-category-cell {
  font-weight: 500;
  color: #6b7280;
}

.archived-events-owner-cell {
  font-weight: 500;
  color: #374151;
}

.archived-events-date-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.85rem;
  color: #6b7280;
}

.archived-events-source-cell {
  text-align: left;
}

.archived-events-source-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.archived-events-source-dot {
  background-color: #A78BFA;
}

.archived-events-source-text {
  color: #A78BFA;
}

.archived-events-type-cell {
  text-align: left;
}

.archived-events-type-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.archived-events-type-dot {
  background-color: #FBBF24;
}

.archived-events-type-text {
  color: #FBBF24;
}

.archived-events-timestamp-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.85rem;
  color: #6b7280;
}

.archived-events-actions-cell {
  text-align: left;
  vertical-align: middle;
}

.archived-events-actions {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  height: 100%;
  min-height: 48px;
}

/* New Action Icons - Completely different class names, no containers */
.event-action-icon,
.event-view-icon-0,
.event-view-icon-1,
.event-view-icon-2,
.event-view-icon-3,
.event-view-icon-4,
.event-unarchive-icon-0,
.event-unarchive-icon-1,
.event-unarchive-icon-2,
.event-unarchive-icon-3,
.event-unarchive-icon-4,
.event-delete-icon-0,
.event-delete-icon-1,
.event-delete-icon-2,
.event-delete-icon-3,
.event-delete-icon-4 {
  display: inline-block !important;
  cursor: pointer !important;
  padding: 2px !important;
  margin: 0 6px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  transition: opacity 0.2s ease !important;
}

.event-action-icon:hover,
.event-view-icon-0:hover,
.event-view-icon-1:hover,
.event-view-icon-2:hover,
.event-view-icon-3:hover,
.event-view-icon-4:hover,
.event-unarchive-icon-0:hover,
.event-unarchive-icon-1:hover,
.event-unarchive-icon-2:hover,
.event-unarchive-icon-3:hover,
.event-unarchive-icon-4:hover,
.event-delete-icon-0:hover,
.event-delete-icon-1:hover,
.event-delete-icon-2:hover,
.event-delete-icon-3:hover,
.event-delete-icon-4:hover {
  opacity: 0.6 !important;
  background: transparent !important;
  box-shadow: none !important;
  transform: none !important;
}

/* Archived Events View Button - Using main.css action-btn.view styles */
.archived-events-view-btn,
.archived-events-view-btn.action-btn,
.archived-events-view-btn.action-btn.view {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  padding: 2px !important;
  margin: 0 6px !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: none !important;
  text-shadow: none !important;
  outline: none !important;
  border-radius: 0 !important;
}

.archived-events-view-btn:hover,
.archived-events-view-btn.action-btn:hover,
.archived-events-view-btn.action-btn.view:hover {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  text-shadow: none !important;
  border-radius: 0 !important;
}

.archived-events-view-btn i.fa-eye {
  font-size: 18px !important; /* Keep same size as original SVG */
  color: #6b7280 !important;
  transition: all 0.2s ease !important;
}

.archived-events-view-btn:hover i.fa-eye {
  color: #3b82f6 !important; /* Blue on hover */
}

/* Colorblindness Support - Tritanopia - Maximum specificity to override main.css */
html[data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn i.fa-eye,
html[data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn i.fas.fa-eye,
html[data-colorblind="tritanopia"] .archived-events-table-body .archived-events-actions .action-btn.view.archived-events-view-btn i.fa-eye {
  color: #7c3aed !important; /* Purple for tritanopia - override inherit */
}

html[data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn:hover i.fa-eye,
html[data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn:hover i.fas.fa-eye,
html[data-colorblind="tritanopia"] .archived-events-table-body .archived-events-actions .action-btn.view.archived-events-view-btn:hover i.fa-eye {
  color: #7c3aed !important; /* Purple for tritanopia on hover */
}

html[data-theme="dark"][data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn i.fa-eye,
html[data-theme="dark"][data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn i.fas.fa-eye,
html[data-theme="dark"][data-colorblind="tritanopia"] .archived-events-table-body .archived-events-actions .action-btn.view.archived-events-view-btn i.fa-eye {
  color: #7c3aed !important; /* Purple for tritanopia in dark theme */
}

html[data-theme="dark"][data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn:hover i.fa-eye,
html[data-theme="dark"][data-colorblind="tritanopia"] .archived-events-actions .action-btn.view.archived-events-view-btn:hover i.fas.fa-eye,
html[data-theme="dark"][data-colorblind="tritanopia"] .archived-events-table-body .archived-events-actions .action-btn.view.archived-events-view-btn:hover i.fa-eye {
  color: #6d28d9 !important; /* Darker purple for tritanopia on hover in dark theme */
}

.event-unarchive-icon-0,
.event-unarchive-icon-1,
.event-unarchive-icon-2,
.event-unarchive-icon-3,
.event-unarchive-icon-4 {
  color: #059669 !important;
}

.event-unarchive-icon-0:hover,
.event-unarchive-icon-1:hover,
.event-unarchive-icon-2:hover,
.event-unarchive-icon-3:hover,
.event-unarchive-icon-4:hover {
  color: #047857 !important;
}

.event-delete-icon-0,
.event-delete-icon-1,
.event-delete-icon-2,
.event-delete-icon-3,
.event-delete-icon-4 {
  color: #dc2626 !important;
}

.event-delete-icon-0:hover,
.event-delete-icon-1:hover,
.event-delete-icon-2:hover,
.event-delete-icon-3:hover,
.event-delete-icon-4:hover {
  color: #b91c1c !important;
}

.action-icon-svg {
  width: 18px !important;
  height: 18px !important;
  display: block !important;
}

.icon-disabled {
  opacity: 0.3 !important;
  cursor: not-allowed !important;
  pointer-events: none !important;
}

.icon-disabled:hover {
  opacity: 0.3 !important;
}

.icon-spinning {
  animation: icon-spin 1s linear infinite;
}

@keyframes icon-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes archived-events-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .archived-events-container {
    margin-left: 0;
    padding: 16px;
  }
  
  .archived-events-title {
    font-size: 1.5rem;
  }
  
  .archived-events-navigation .toggle-group {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .archived-events-navigation .toggle-button {
    font-size: 0.9rem;
  }
  
  .archived-events-table-th,
  .archived-events-table-td {
    padding: 12px 8px;
  }
  
  .archived-events-actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .archived-events-action-btn {
    width: 28px;
    height: 28px;
  }
  
  .archived-events-action-icon {
    width: 14px;
    height: 14px;
  }
}

/* Animations */
@keyframes archived-events-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.archived-events-table-container,
.archived-events-empty {
  animation: archived-events-fadeIn 0.5s ease-out;
}

/* Focus states for accessibility - handled by global toggle-button styles */

.archived-events-title-link:focus,
.archived-events-action-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.archived-events-table-wrapper::-webkit-scrollbar {
  height: 8px;
}

.archived-events-table-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.archived-events-table-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.archived-events-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
