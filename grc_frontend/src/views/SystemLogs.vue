<template>
  <div class="system-logs-page large">
    <div class="header-row">
      <h1>System Logs</h1>
      <div class="header-info" v-if="isAdmin">
        <span class="admin-badge">Administrator View - All Logs</span>
      </div>
      <div class="header-info" v-else>
        <span class="user-badge">Your Logs Only</span>
      </div>
    </div>
    
    <div class="search-filter-row">
      <input v-model="search" placeholder="Search logs..." class="search-input" />
      <div class="filters">
        <label class="date-label">From Date:</label>
        <input 
          type="date" 
          v-model="startDate" 
          placeholder="Start Date" 
          class="date-input"
        />
        <label class="date-label">To Date:</label>
        <input 
          type="date" 
          v-model="endDate" 
          placeholder="End Date" 
          class="date-input"
        />
        <button class="refresh-btn" @click="loadLogs" :disabled="loading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          Refresh
        </button>
        <button class="clear-btn" @click="clearDateFilters" :disabled="loading">
          Clear Dates
        </button>
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading system logs...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadLogs" class="retry-btn">Retry</button>
    </div>

    <!-- Logs table -->
    <div v-else class="logs-container">
      <div class="logs-info">
        <span>Total: {{ totalCount }} logs</span>
        <span>Showing: {{ logs.length }} logs (Page {{ currentPage }} of {{ totalPages }})</span>
      </div>
      <div class="table-wrapper">
        <table class="logs-table">
          <thead>
            <tr>
              <th @click="sortBy('Timestamp')" class="sortable">
                Timestamp
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'Timestamp'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('UserName')" class="sortable">
                User
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'UserName'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('Module')" class="sortable">
                Module
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'Module'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('ActionType')" class="sortable">
                Action Type
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'ActionType'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('EntityType')" class="sortable">
                Entity Type
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'EntityType'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('LogLevel')" class="sortable">
                Log Level
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'LogLevel'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('Description')" class="sortable">
                Description
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'Description'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th @click="sortBy('IPAddress')" class="sortable">
                IP Address
                <span class="sort-icon">
                  <i v-if="sortColumn !== 'IPAddress'" class="fas fa-sort"></i>
                  <i v-else-if="sortDirection === 'asc'" class="fas fa-sort-up"></i>
                  <i v-else class="fas fa-sort-down"></i>
                </span>
              </th>
              <th>Additional Info</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in paginatedLogs" :key="log.LogId" :class="getLogLevelClass(log.LogLevel)">
              <td>{{ formatTimestamp(log.Timestamp) }}</td>
              <td>{{ log.UserName || 'Unknown' }}</td>
              <td>{{ log.Module || 'N/A' }}</td>
              <td>{{ log.ActionType || 'N/A' }}</td>
              <td>{{ log.EntityType || 'N/A' }}</td>
              <td>
                <span :class="['log-level-badge', log.LogLevel?.toLowerCase()]">
                  {{ log.LogLevel || 'INFO' }}
                </span>
              </td>
              <td class="description-cell" :title="log.Description">
                {{ truncateText(log.Description, 100) }}
              </td>
              <td>{{ log.IPAddress || 'N/A' }}</td>
              <td class="additional-info-cell" :title="formatAdditionalInfo(log.AdditionalInfo)">
                <span v-if="log.AdditionalInfo" class="info-badge" @click="showAdditionalInfo(log)">
                  <i class="fas fa-info-circle"></i> View
                </span>
                <span v-else>N/A</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div class="pagination" v-if="totalCount > 0">
        <button 
          @click="goToPage(1)" 
          :disabled="currentPage === 1"
          class="page-btn"
          title="First Page"
        >
          ««
        </button>
        <button 
          @click="goToPage(currentPage - 1)" 
          :disabled="currentPage === 1"
          class="page-btn"
        >
          Previous
        </button>
        
        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            @click="goToPage(page)"
            :class="['page-number-btn', { active: page === currentPage }]"
          >
            {{ page }}
          </button>
        </div>
        
        <button 
          @click="goToPage(currentPage + 1)" 
          :disabled="currentPage === totalPages"
          class="page-btn"
        >
          Next
        </button>
        <button 
          @click="goToPage(totalPages)" 
          :disabled="currentPage === totalPages"
          class="page-btn"
          title="Last Page"
        >
          »»
        </button>
        
        <span class="page-info">
          Page {{ currentPage }} of {{ totalPages }} ({{ totalCount }} total logs)
        </span>
        
        <div class="page-size-selector">
          <label>Per page:</label>
          <select v-model="pageSize" @change="changePageSize" class="page-size-select">
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !error && filteredLogs.length === 0" class="empty-state">
      <p>No logs found</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { API_BASE_URL } from '../config/api.js';

// Define component name
defineOptions({
  name: 'SystemLogsPage'
});

const loading = ref(false);
const error = ref(null);
const logs = ref([]);
const isAdmin = ref(false);
const totalCount = ref(0);
const currentPage = ref(1);
const pageSize = ref(50);

const search = ref('');
const startDate = ref('');
const endDate = ref('');

// Sorting
const sortColumn = ref('Timestamp');
const sortDirection = ref('desc'); // Default to descending for newest first

// Computed properties
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const matchesSearch = 
      !search.value ||
      (log.Description && log.Description.toLowerCase().includes(search.value.toLowerCase())) ||
      (log.UserName && log.UserName.toLowerCase().includes(search.value.toLowerCase())) ||
      (log.Module && log.Module.toLowerCase().includes(search.value.toLowerCase())) ||
      (log.ActionType && log.ActionType.toLowerCase().includes(search.value.toLowerCase()));
    
    return matchesSearch;
  });
});

const totalPages = computed(() => {
  // Use totalCount from backend for accurate pagination
  return Math.ceil(totalCount.value / pageSize.value);
});

const sortedLogs = computed(() => {
  if (!logs.value || logs.value.length === 0) {
    return [];
  }
  
  const sorted = [...logs.value];
  
  sorted.sort((a, b) => {
    let aValue = a[sortColumn.value];
    let bValue = b[sortColumn.value];
    
    // Handle null/undefined values
    if (aValue == null) aValue = '';
    if (bValue == null) bValue = '';
    
    // Handle Timestamp as date
    if (sortColumn.value === 'Timestamp') {
      const aDate = new Date(aValue);
      const bDate = new Date(bValue);
      return sortDirection.value === 'asc' 
        ? aDate - bDate 
        : bDate - aDate;
    }
    
    // Handle numeric values
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortDirection.value === 'asc' 
        ? aValue - bValue 
        : bValue - aValue;
    }
    
    // Handle string values (case-insensitive)
    const aStr = String(aValue).toLowerCase();
    const bStr = String(bValue).toLowerCase();
    
    if (aStr < bStr) {
      return sortDirection.value === 'asc' ? -1 : 1;
    }
    if (aStr > bStr) {
      return sortDirection.value === 'asc' ? 1 : -1;
    }
    return 0;
  });
  
  return sorted;
});

const paginatedLogs = computed(() => {
  // Return sorted logs (client-side sorting on current page)
  return sortedLogs.value;
});

// Calculate visible page numbers for pagination
const visiblePages = computed(() => {
  const pages = [];
  const total = totalPages.value;
  const current = currentPage.value;
  const maxVisible = 7; // Show max 7 page numbers
  
  if (total <= maxVisible) {
    // Show all pages if total is less than max visible
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // Show pages around current page
    let start = Math.max(1, current - Math.floor(maxVisible / 2));
    let end = Math.min(total, start + maxVisible - 1);
    
    // Adjust start if we're near the end
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
  }
  
  return pages;
});

// Methods
const loadLogs = async () => {
  loading.value = true;
  error.value = null;
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Build query parameters
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString()
    });
    
    // Add date filters if provided (format: YYYY-MM-DD for backend)
    if (startDate.value) {
      // Ensure date is in YYYY-MM-DD format
      const startDateFormatted = new Date(startDate.value).toISOString().split('T')[0];
      params.append('start_date', startDateFormatted);
    }
    if (endDate.value) {
      // Ensure date is in YYYY-MM-DD format
      const endDateFormatted = new Date(endDate.value).toISOString().split('T')[0];
      params.append('end_date', endDateFormatted);
    }

    const response = await fetch(`${API_BASE_URL}/api/system-logs/?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to load logs: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (data.success) {
      logs.value = data.data || [];
      totalCount.value = data.total_count || 0;
      isAdmin.value = data.is_admin || false;
      currentPage.value = data.page || 1;
    } else {
      throw new Error(data.error || 'Failed to load logs');
    }
  } catch (err) {
    console.error('Error loading system logs:', err);
    error.value = err.message || 'Failed to load system logs';
    logs.value = [];
  } finally {
    loading.value = false;
  }
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const truncateText = (text, maxLength) => {
  if (!text) return 'N/A';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

const getLogLevelClass = (logLevel) => {
  if (!logLevel) return '';
  return `log-level-${logLevel.toLowerCase()}`;
};

const formatAdditionalInfo = (additionalInfo) => {
  if (!additionalInfo) return 'N/A';
  if (typeof additionalInfo === 'string') {
    try {
      additionalInfo = JSON.parse(additionalInfo);
    } catch (e) {
      return additionalInfo;
    }
  }
  if (typeof additionalInfo === 'object') {
    return JSON.stringify(additionalInfo, null, 2);
  }
  return String(additionalInfo);
};

const showAdditionalInfo = (log) => {
  const info = formatAdditionalInfo(log.AdditionalInfo);
  if (info && info !== 'N/A') {
    alert(`Additional Info for Log ${log.LogId}:\n\n${info}`);
  }
};

// Sort by column
const sortBy = (column) => {
  if (sortColumn.value === column) {
    // Toggle direction if clicking the same column
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    // Set new column and default to ascending
    sortColumn.value = column;
    sortDirection.value = 'asc';
  }
};

// Navigate to specific page
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    loadLogs();
  }
};

// Change page size
const changePageSize = () => {
  currentPage.value = 1;
  loadLogs();
};

// Clear date filters
const clearDateFilters = () => {
  startDate.value = '';
  endDate.value = '';
  currentPage.value = 1;
  loadLogs();
};

// Watch for date filter changes and reset to page 1, then reload
// Use a debounce to avoid too many API calls while user is selecting dates
let dateFilterTimeout = null;
watch([startDate, endDate], () => {
  currentPage.value = 1;
  
  // Clear existing timeout
  if (dateFilterTimeout) {
    clearTimeout(dateFilterTimeout);
  }
  
  // Debounce the API call by 500ms
  dateFilterTimeout = setTimeout(() => {
    loadLogs();
  }, 500);
});

// Watch for page changes
watch(currentPage, () => {
  loadLogs();
});

// Load logs on mount
onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.system-logs-page {
  padding: 24px;
  width: calc(100% - 280px);
  max-width: calc(100vw - 280px);
  height: calc(100vh - 80px);
  max-height: calc(100vh - 80px);
  margin: 0 0 0 280px; /* Account for sidebar width */
  overflow-y: auto;
  overflow-x: hidden !important;
  box-sizing: border-box;
  position: relative;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.system-logs-page::-webkit-scrollbar {
  width: 8px;
}

.system-logs-page::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.system-logs-page::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.system-logs-page::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.header-row h1 {
  margin: 0;
  font-size: 28px;
  color: #333;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  flex: 1;
  min-width: 0;
}

.header-info {
  display: flex;
  gap: 10px;
}

.admin-badge, .user-badge {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.admin-badge {
  background-color: #f0f0f0;
  color: #333;
}

.user-badge {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

.search-filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.search-input {
  flex: 1;
  min-width: 200px;
  max-width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.date-input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.date-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  white-space: normal;
  word-wrap: break-word;
}

.clear-btn {
  padding: 10px 20px;
  background-color: #999;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.clear-btn:hover:not(:disabled) {
  background-color: #777;
}

.clear-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn {
  padding: 10px 20px;
  background-color: #666;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #555;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #666;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #666;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-btn:hover {
  background-color: #555;
}

.logs-container {
  margin-top: 20px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logs-info {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
  flex-wrap: wrap;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.table-wrapper {
  overflow-x: hidden !important;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: calc(100vh - 450px);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  position: relative;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.table-wrapper::-webkit-scrollbar {
  width: 8px;
}

.table-wrapper::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.table-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.logs-table {
  width: 100% !important;
  max-width: 100% !important;
  border-collapse: collapse;
  background-color: white;
  table-layout: fixed;
  box-sizing: border-box;
  min-width: 0;
}

.logs-table thead {
  background-color: #f5f5f5;
}

.logs-table th {
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  position: relative;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.logs-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.logs-table th.sortable:hover {
  background-color: #e8e8e8;
}

.sort-icon {
  margin-left: 8px;
  font-size: 12px;
  color: #666;
  display: inline-block;
  min-width: 12px;
}

.logs-table th.sortable.active .sort-icon {
  color: #333;
  font-weight: 700;
}

.logs-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #eee;
  font-size: 14px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.logs-table tbody tr:hover {
  background-color: #f9f9f9;
}

.log-level-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.log-level-badge.info {
  background-color: #f0f0f0;
  color: #333;
}

.log-level-badge.warning {
  background-color: #fff3e0;
  color: #f57c00;
}

.log-level-badge.error {
  background-color: #ffebee;
  color: #d32f2f;
}

.log-level-badge.debug {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

.description-cell {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  min-width: 0;
  box-sizing: border-box;
}

.log-level-info {
  background-color: #f9f9f9;
}

.log-level-warning {
  background-color: #fff3e0;
}

.log-level-error {
  background-color: #ffebee;
}

.log-level-debug {
  background-color: #f3e5f5;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 4px;
  flex-wrap: wrap;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.page-btn {
  padding: 8px 16px;
  background-color: #666;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  min-width: 80px;
}

.page-btn:hover:not(:disabled) {
  background-color: #555;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 5px;
  align-items: center;
}

.page-number-btn {
  padding: 8px 12px;
  background-color: white;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  min-width: 40px;
  transition: all 0.2s;
}

.page-number-btn:hover {
  background-color: #f0f0f0;
  border-color: #999;
}

.page-number-btn.active {
  background-color: #666;
  color: white;
  border-color: #666;
  font-weight: 600;
}

.page-info {
  font-size: 14px;
  color: #666;
  margin: 0 10px;
  white-space: nowrap;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 10px;
}

.page-size-selector label {
  font-size: 14px;
  color: #666;
}

.page-size-select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
}

.page-size-select:hover {
  border-color: #999;
}

/* Column width adjustments for better layout */
.logs-table th:nth-child(1),
.logs-table td:nth-child(1) {
  width: 12%;
  min-width: 0;
  max-width: 15%;
}

.logs-table th:nth-child(2),
.logs-table td:nth-child(2) {
  width: 10%;
  min-width: 0;
  max-width: 12%;
}

.logs-table th:nth-child(3),
.logs-table td:nth-child(3) {
  width: 10%;
  min-width: 0;
  max-width: 12%;
}

.logs-table th:nth-child(4),
.logs-table td:nth-child(4) {
  width: 12%;
  min-width: 0;
  max-width: 15%;
}

.logs-table th:nth-child(5),
.logs-table td:nth-child(5) {
  width: 10%;
  min-width: 0;
  max-width: 12%;
}

.logs-table th:nth-child(6),
.logs-table td:nth-child(6) {
  width: 8%;
  min-width: 0;
  max-width: 10%;
}

.logs-table th:nth-child(7),
.logs-table td:nth-child(7) {
  width: 20%;
  min-width: 0;
  max-width: 25%;
}

.logs-table th:nth-child(8),
.logs-table td:nth-child(8) {
  width: 10%;
  min-width: 0;
  max-width: 12%;
}

.logs-table th:nth-child(9),
.logs-table td:nth-child(9) {
  width: 8%;
  min-width: 0;
  max-width: 10%;
}

@media (max-width: 1024px) {
  .system-logs-page {
    width: calc(100% - 240px);
    max-width: calc(100vw - 240px);
    margin-left: 240px;
    padding: 16px;
  }
  
  .table-wrapper {
    max-height: calc(100vh - 400px);
  }
}

@media (max-width: 768px) {
  .system-logs-page {
    margin-left: 0;
    width: 100%;
    max-width: 100%;
    padding: 10px;
    height: calc(100vh - 60px);
    max-height: calc(100vh - 60px);
  }
  
  .search-filter-row {
    flex-direction: column;
  }
  
  .filters {
    flex-direction: column;
  }
  
  .logs-table {
    font-size: 12px;
  }
  
  .logs-table th,
  .logs-table td {
    padding: 8px 4px;
    font-size: 11px;
  }
  
  .table-wrapper {
    max-height: calc(100vh - 350px);
  }
}
</style>
