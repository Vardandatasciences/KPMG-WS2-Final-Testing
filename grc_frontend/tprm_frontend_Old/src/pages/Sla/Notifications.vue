<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-foreground mb-2">Notification Center</h1>
        <p class="text-muted-foreground">
          Monitor and manage all your risk management notifications from one central dashboard.
        </p>
      </div>
    </div>
    
    <!-- Stats Section -->
    <div v-if="statsLoading" class="grid grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="animate-pulse">
        <div class="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div class="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
            <div class="h-4 bg-muted rounded w-1/2"></div>
            <div class="h-4 w-4 bg-muted rounded"></div>
          </div>
          <div class="p-6 pt-0">
            <div class="h-8 bg-muted rounded w-1/2 mb-2"></div>
            <div class="h-3 bg-muted rounded w-3/4"></div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="statsError || !stats" class="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div class="p-4">
        <p class="text-destructive">{{ statsError || 'No data available' }}</p>
      </div>
    </div>
    
    <div v-else class="grid grid-cols-4 gap-4">
      <!-- Total Sent Card -->
      <div class="relative overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm">
        <div class="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
          <h3 class="text-sm font-medium text-muted-foreground">Total Sent</h3>
          <Bell class="h-4 w-4 text-muted-foreground" />
        </div>
        <div class="p-6 pt-0">
          <div class="text-2xl font-bold text-foreground">{{ (stats.total_sent || 0).toLocaleString() }}</div>
          <div class="flex items-center space-x-1 text-xs">
            <TrendingUp class="h-3 w-3 text-success" />
            <span class="text-success">+{{ stats.trends.sent_change }}%</span>
            <span class="text-muted-foreground">vs last month</span>
          </div>
        </div>
      </div>

      <!-- Read Rate Card -->
      <div class="relative overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm">
        <div class="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
          <h3 class="text-sm font-medium text-muted-foreground">Read Rate</h3>
          <CheckCircle class="h-4 w-4 text-muted-foreground" />
        </div>
        <div class="p-6 pt-0">
          <div class="text-2xl font-bold text-foreground">
            {{ stats.total_sent > 0 ? ((stats.total_read / stats.total_sent) * 100).toFixed(1) : '0.0' }}%
          </div>
          <div class="flex items-center space-x-1 text-xs">
            <TrendingDown class="h-3 w-3 text-destructive" />
            <span class="text-destructive">{{ stats.trends.read_rate_change }}%</span>
            <span class="text-muted-foreground">vs last month</span>
          </div>
          <div class="relative h-4 w-full overflow-hidden rounded-full bg-secondary mt-2">
            <div 
              class="h-full w-full flex-1 bg-primary transition-all"
              :style="{ transform: `translateX(-${100 - (stats.total_sent > 0 ? (stats.total_read / stats.total_sent) * 100 : 0)}%)` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Unread Card -->
      <div class="relative overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm">
        <div class="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
          <h3 class="text-sm font-medium text-muted-foreground">Unread</h3>
          <Clock class="h-4 w-4 text-muted-foreground" />
        </div>
        <div class="p-6 pt-0">
          <div class="text-2xl font-bold text-foreground">{{ stats.total_unread || 0 }}</div>
          <div class="text-xs text-muted-foreground">
            {{ stats.total_sent > 0 ? ((stats.total_unread / stats.total_sent) * 100).toFixed(1) : '0.0' }}% of total sent
          </div>
          <div class="relative h-4 w-full overflow-hidden rounded-full bg-secondary mt-2">
            <div 
              class="h-full w-full flex-1 bg-primary transition-all"
              :style="{ transform: `translateX(-${100 - (stats.total_sent > 0 ? (stats.total_unread / stats.total_sent) * 100 : 0)}%)` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Critical Alerts Card -->
      <div class="relative overflow-hidden border-l-4 border-l-critical rounded-lg border bg-card text-card-foreground shadow-sm">
        <div class="flex flex-row items-center justify-between space-y-0 pb-2 p-6">
          <h3 class="text-sm font-medium text-muted-foreground">Critical Alerts</h3>
          <AlertTriangle class="h-4 w-4 text-critical" />
        </div>
        <div class="p-6 pt-0">
          <div class="text-2xl font-bold text-foreground">{{ stats.by_priority.critical || 0 }}</div>
          <div class="flex items-center space-x-1 text-xs">
            <TrendingUp class="h-3 w-3 text-critical" />
            <span class="text-critical">+{{ stats.trends.critical_alerts_change }}%</span>
            <span class="text-muted-foreground">requires attention</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters Section -->
    <div class="space-y-4">
      <!-- Filter Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <button
            @click="isExpanded = !isExpanded"
            class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 border border-input bg-background hover:bg-accent hover:text-accent-foreground flex items-center space-x-2"
          >
            <Filter class="h-4 w-4" />
            <span>Filters</span>
            <span v-if="activeFiltersCount > 0" class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 ml-1">
              {{ activeFiltersCount }}
            </span>
          </button>
          
          <!-- Quick Filters -->
          <button
            @click="filters.unread_only = !filters.unread_only"
            :class="[
              'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 flex items-center space-x-1',
              filters.unread_only 
                ? 'bg-blue-100 text-blue-800 hover:bg-blue-200 border-blue-200' 
                : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
            ]"
          >
            <CheckCircle class="h-3 w-3" />
            <span>Unread Only</span>
            <span v-if="unreadCount > 0" class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-blue-100 text-blue-800 hover:bg-blue-200 ml-1 text-xs">
              {{ unreadCount }}
            </span>
          </button>
          
          <button
            @click="toggleCriticalFilter"
            :class="[
              'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 flex items-center space-x-1',
              filters.priority?.includes('critical') 
                ? 'bg-red-100 text-red-800 hover:bg-red-200 border-red-200' 
                : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
            ]"
          >
            <AlertTriangle class="h-3 w-3" />
            <span>Critical</span>
            <span v-if="criticalCount > 0" class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-red-100 text-red-800 hover:bg-red-200 ml-1 text-xs">
              {{ criticalCount }}
            </span>
          </button>
          
          <button
            @click="toggleRiskAlertsFilter"
            :class="[
              'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 flex items-center space-x-1',
              (filters.type?.includes('risk_alert') || filters.type?.includes('security_alert'))
                ? 'bg-orange-100 text-orange-800 hover:bg-orange-200 border-orange-200' 
                : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
            ]"
          >
            <AlertTriangle class="h-3 w-3" />
            <span>Risk Alerts</span>
            <span v-if="riskAlertsCount > 0" class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-orange-100 text-orange-800 hover:bg-orange-200 ml-1 text-xs">
              {{ riskAlertsCount }}
            </span>
          </button>
        </div>

        <button
          v-if="activeFiltersCount > 0"
          @click="clearFilters"
          class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3 hover:bg-accent hover:text-accent-foreground flex items-center space-x-1 text-muted-foreground hover:text-destructive"
        >
          <X class="h-4 w-4" />
          <span>Clear All</span>
        </button>
      </div>

      <!-- Active Filters Display -->
      <div v-if="activeFiltersCount > 0" class="flex flex-wrap gap-2">
        <span
          v-for="priority in filters.priority"
          :key="priority"
          class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground flex items-center space-x-1"
        >
          <span class="capitalize">{{ priority }}</span>
          <X 
            class="h-3 w-3 cursor-pointer hover:text-destructive" 
            @click="removePriorityFilter(priority)"
          />
        </span>
        <span
          v-for="type in filters.type"
          :key="type"
          class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground flex items-center space-x-1"
        >
          <span>{{ type.replace('_', ' ') }}</span>
          <X 
            class="h-3 w-3 cursor-pointer hover:text-destructive" 
            @click="removeTypeFilter(type)"
          />
        </span>
        <span
          v-for="status in filters.status"
          :key="status"
          class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground flex items-center space-x-1"
        >
          <span class="capitalize">{{ status }}</span>
          <X 
            class="h-3 w-3 cursor-pointer hover:text-destructive" 
            @click="removeStatusFilter(status)"
          />
        </span>
        <span
          v-if="filters.unread_only"
          class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground flex items-center space-x-1"
        >
          <span>Unread Only</span>
          <X 
            class="h-3 w-3 cursor-pointer hover:text-destructive" 
            @click="filters.unread_only = false"
          />
        </span>
      </div>

      <!-- Expanded Filters -->
      <div v-if="isExpanded" class="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div class="flex flex-col space-y-1.5 p-6">
          <h3 class="text-lg font-semibold leading-none tracking-tight">Advanced Filters</h3>
        </div>
        <div class="p-6 pt-0 space-y-6">
          <!-- Priority Filters -->
          <div>
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Priority</label>
            <div class="grid grid-cols-2 gap-3 mt-2">
              <div v-for="option in priorityOptions" :key="option.value" class="flex items-center space-x-2">
                <input
                  :id="`priority-${option.value}`"
                  type="checkbox"
                  :checked="filters.priority?.includes(option.value) || false"
                  @change="handlePriorityChange(option.value, ($event.target as HTMLInputElement).checked)"
                  class="peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
                />
                <label :for="`priority-${option.value}`" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center space-x-2">
                  <div :class="`w-2 h-2 rounded-full bg-${option.color}`" />
                  <span>{{ option.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="shrink-0 bg-border h-[1px] w-full"></div>

          <!-- Type Filters -->
          <div>
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Notification Types</label>
            <div class="grid grid-cols-2 gap-3 mt-2">
              <div v-for="option in typeOptions" :key="option.value" class="flex items-center space-x-2">
                <input
                  :id="`type-${option.value}`"
                  type="checkbox"
                  :checked="filters.type?.includes(option.value) || false"
                  @change="handleTypeChange(option.value, ($event.target as HTMLInputElement).checked)"
                  class="peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
                />
                <label :for="`type-${option.value}`" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  {{ option.label }}
                </label>
              </div>
            </div>
          </div>

          <div class="shrink-0 bg-border h-[1px] w-full"></div>

          <!-- Status Filters -->
          <div>
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Status</label>
            <div class="grid grid-cols-3 gap-3 mt-2">
              <div v-for="option in statusOptions" :key="option.value" class="flex items-center space-x-2">
                <input
                  :id="`status-${option.value}`"
                  type="checkbox"
                  :checked="filters.status?.includes(option.value) || false"
                  @change="handleStatusChange(option.value, ($event.target as HTMLInputElement).checked)"
                  class="peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
                />
                <label :for="`status-${option.value}`" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 capitalize">
                  {{ option.label }}
                </label>
              </div>
            </div>
          </div>

          <div class="shrink-0 bg-border h-[1px] w-full"></div>

          <!-- Date Range -->
          <div>
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Date Range</label>
            <div class="grid grid-cols-2 gap-3 mt-2">
              <div>
                <label for="date-from" class="text-xs text-muted-foreground">From</label>
                <input
                  id="date-from"
                  type="date"
                  :value="filters.date_from || ''"
                  @input="filters.date_from = ($event.target as HTMLInputElement).value || undefined"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm mt-1"
                />
              </div>
              <div>
                <label for="date-to" class="text-xs text-muted-foreground">To</label>
                <input
                  id="date-to"
                  type="date"
                  :value="filters.date_to || ''"
                  @input="filters.date_to = ($event.target as HTMLInputElement).value || undefined"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm mt-1"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Notifications List -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-semibold text-foreground">Recent Notifications</h2>
        <div class="flex items-center gap-2">
          <span v-if="notificationsLoading" class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 text-sm">
            Loading...
          </span>
          <span v-else-if="notificationsError" class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80 text-sm">
            Error
          </span>
          
          <!-- Bulk Actions -->
          <div v-if="!notificationsLoading && !notificationsError && (stats?.total_unread > 0 || stats?.total_sent > 0)" class="flex items-center gap-2">
            <button
              @click="markAllAsRead"
              :disabled="bulkActionLoading || !stats || stats.total_unread === 0"
              class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-4 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              <CheckCircle class="h-4 w-4" />
              <span>Read All</span>
              <span v-if="stats && stats.total_unread > 0" class="ml-1 text-xs bg-blue-500 px-1.5 py-0.5 rounded-full">
                {{ stats.total_unread }}
              </span>
            </button>
            <button
              @click="deleteAllNotifications"
              :disabled="bulkActionLoading || !stats || stats.total_sent === 0"
              class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-4 bg-red-600 text-white hover:bg-red-700 disabled:bg-gray-400"
            >
              <X class="h-4 w-4" />
              <span>Delete All</span>
              <span v-if="stats && stats.total_sent > 0" class="ml-1 text-xs bg-red-500 px-1.5 py-0.5 rounded-full">
                {{ stats.total_sent }}
              </span>
            </button>
          </div>
          
          <!-- View Toggle -->
          <div class="flex items-center bg-muted rounded-md p-1">
            <button
              @click="viewMode = 'list'"
              :class="[
                'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3',
                viewMode === 'list' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              <LayoutList class="h-4 w-4" />
              <span class="hidden sm:inline">List</span>
            </button>
            <button
              @click="viewMode = 'table'"
              :class="[
                'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3',
                viewMode === 'table' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              ]"
            >
              <Table class="h-4 w-4" />
              <span class="hidden sm:inline">Table</span>
            </button>
          </div>
        </div>
      </div>

      <div v-if="notificationsLoading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="animate-pulse rounded-lg border bg-card text-card-foreground shadow-sm">
          <div class="p-4">
            <div class="h-4 bg-muted rounded w-3/4 mb-2"></div>
            <div class="h-3 bg-muted rounded w-1/2"></div>
          </div>
        </div>
      </div>
      
      <div v-else-if="notificationsError" class="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div class="p-4">
          <p class="text-destructive">{{ notificationsError }}</p>
        </div>
      </div>
      
      <!-- List View -->
      <div v-else-if="viewMode === 'list'" class="relative h-[600px] overflow-y-auto">
        <div class="h-full w-full rounded-[inherit]">
          <div class="space-y-3">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              @click="handleNotificationClick(notification)"
              :class="[
                'transition-all duration-200 hover:shadow-md cursor-pointer rounded-lg border bg-card text-card-foreground shadow-sm',
                notification.status !== 'read' 
                  ? 'border-l-4 border-l-primary bg-primary/5' 
                  : 'border-l-4 border-l-transparent'
              ]"
            >
              <div class="p-4">
                <div class="flex items-start justify-between space-x-4">
                  <div class="flex items-start space-x-3 flex-1">
                    <div :class="[
                      'p-2 rounded-lg',
                      notification.priority === 'critical' ? 'bg-red-100' :
                      notification.priority === 'high' ? 'bg-orange-100' :
                      notification.priority === 'medium' ? 'bg-yellow-100' :
                      'bg-green-100'
                    ]">
                      <AlertTriangle :class="[
                        'h-4 w-4',
                        notification.priority === 'critical' ? 'text-red-600' :
                        notification.priority === 'high' ? 'text-orange-600' :
                        notification.priority === 'medium' ? 'text-yellow-600' :
                        'text-green-600'
                      ]" />
                    </div>
                    
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center space-x-2 mb-1">
                        <h3 :class="[
                          'font-medium text-sm',
                          notification.status !== 'read' ? 'text-foreground' : 'text-muted-foreground'
                        ]">
                          {{ notification.title }}
                        </h3>
                        <span :class="[
                          'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-xs',
                          getPriorityBadgeClass(notification.priority)
                        ]">
                          {{ notification.priority.toUpperCase() }}
                        </span>
                      </div>
                      
                      <p class="text-sm text-muted-foreground line-clamp-2 mb-2">
                        {{ notification.message }}
                      </p>
                      
                      <div class="flex items-center space-x-4 text-xs text-muted-foreground">
                        <span class="flex items-center space-x-1">
                          <Clock class="h-3 w-3" />
                          <span>{{ formatTimeAgo(notification.created_at) }}</span>
                        </span>
                        <span class="capitalize">
                          {{ notification.notification_type.replace('_', ' ') }}
                        </span>
                        <span class="flex items-center space-x-1">
                          <template v-if="notification.status === 'read'">
                            <CheckCircle class="h-3 w-3" />
                            <span>Read</span>
                          </template>
                          <template v-else>
                            <Eye class="h-3 w-3" />
                            <span>Unread</span>
                          </template>
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex items-center space-x-2">
                    <button
                      v-if="notification.status !== 'read'"
                      @click.stop="markAsRead(notification.id)"
                      class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 w-8 p-0 hover:bg-accent hover:text-accent-foreground"
                    >
                      <CheckCircle class="h-4 w-4" />
                    </button>
                    <button
                      @click.stop="dismissNotification(notification.id)"
                      class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 w-8 p-0 text-muted-foreground hover:text-destructive hover:bg-accent hover:text-accent-foreground"
                    >
                      <X class="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Table View -->
      <div v-else-if="viewMode === 'table'" class="relative h-[600px] overflow-y-auto">
        <div class="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-muted/50">
                <tr class="border-b border-border">
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground text-xs">Status</th>
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground text-xs">Priority</th>
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground text-xs">Title</th>
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground text-xs">Message</th>
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground text-xs">Type</th>
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground text-xs">Time</th>
                  <th class="h-12 px-4 text-center align-middle font-medium text-muted-foreground text-xs">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="notification in notifications"
                  :key="notification.id"
                  @click="handleNotificationClick(notification)"
                  :class="[
                    'border-b border-border transition-colors hover:bg-muted/50 cursor-pointer',
                    notification.status !== 'read' ? 'bg-primary/5' : ''
                  ]"
                >
                  <!-- Status Column -->
                  <td class="p-4 align-middle">
                    <div class="flex items-center space-x-2">
                      <template v-if="notification.status === 'read'">
                        <CheckCircle class="h-4 w-4 text-green-600" />
                        <span class="text-xs text-green-600">Read</span>
                      </template>
                      <template v-else>
                        <Eye class="h-4 w-4 text-blue-600" />
                        <span class="text-xs text-blue-600 font-medium">Unread</span>
                      </template>
                    </div>
                  </td>
                  
                  <!-- Priority Column -->
                  <td class="p-4 align-middle">
                    <span :class="[
                      'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                      getPriorityBadgeClass(notification.priority)
                    ]">
                      {{ notification.priority.toUpperCase() }}
                    </span>
                  </td>
                  
                  <!-- Title Column -->
                  <td class="p-4 align-middle">
                    <div class="flex items-center space-x-2">
                      <div :class="[
                        'p-2 rounded-lg',
                        notification.priority === 'critical' ? 'bg-red-100' :
                        notification.priority === 'high' ? 'bg-orange-100' :
                        notification.priority === 'medium' ? 'bg-yellow-100' :
                        'bg-green-100'
                      ]">
                        <AlertTriangle :class="[
                          'h-3 w-3',
                          notification.priority === 'critical' ? 'text-red-600' :
                          notification.priority === 'high' ? 'text-orange-600' :
                          notification.priority === 'medium' ? 'text-yellow-600' :
                          'text-green-600'
                        ]" />
                      </div>
                      <span :class="[
                        'font-medium text-sm',
                        notification.status !== 'read' ? 'text-foreground' : 'text-muted-foreground'
                      ]">
                        {{ notification.title }}
                      </span>
                    </div>
                  </td>
                  
                  <!-- Message Column -->
                  <td class="p-4 align-middle max-w-md">
                    <p class="text-sm text-muted-foreground line-clamp-2">
                      {{ notification.message }}
                    </p>
                  </td>
                  
                  <!-- Type Column -->
                  <td class="p-4 align-middle">
                    <span class="text-xs text-muted-foreground capitalize px-2 py-1 bg-muted rounded">
                      {{ notification.notification_type.replace('_', ' ') }}
                    </span>
                  </td>
                  
                  <!-- Time Column -->
                  <td class="p-4 align-middle">
                    <div class="flex items-center space-x-1 text-xs text-muted-foreground">
                      <Clock class="h-3 w-3" />
                      <span>{{ formatTimeAgo(notification.created_at) }}</span>
                    </div>
                  </td>
                  
                  <!-- Actions Column -->
                  <td class="p-4 align-middle">
                    <div class="flex items-center justify-center space-x-2">
                      <button
                        v-if="notification.status !== 'read'"
                        @click.stop="markAsRead(notification.id)"
                        class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 w-8 p-0 hover:bg-accent hover:text-accent-foreground"
                        title="Mark as read"
                      >
                        <CheckCircle class="h-4 w-4" />
                      </button>
                      <button
                        @click.stop="dismissNotification(notification.id)"
                        class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 w-8 p-0 text-muted-foreground hover:text-destructive hover:bg-accent hover:text-accent-foreground"
                        title="Dismiss"
                      >
                        <X class="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <div v-if="!notificationsLoading && !notificationsError && notifications.length === 0" class="text-center py-12">
        <Bell class="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
        <h3 class="text-lg font-medium text-muted-foreground mb-2">No notifications found</h3>
        <p class="text-sm text-muted-foreground">Try adjusting your filters or check back later.</p>
      </div>
    </div>
  </div>
  
  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  Filter, X, CheckCircle, AlertTriangle, Clock, Eye, Bell,
  TrendingUp, TrendingDown, LayoutList, Table
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

// Types
interface NotificationFilters {
  unread_only?: boolean
  priority?: string[]
  type?: string[]
  status?: string[]
  date_from?: string
  date_to?: string
}

interface Notification {
  id: string
  title: string
  message: string
  notification_type: string
  priority: string
  status: string
  created_at: string
  read_at?: string
}

interface NotificationStats {
  total_sent: number
  total_read: number
  total_unread: number
  by_priority: {
    critical?: number
    high?: number
    medium?: number
    low?: number
  }
  trends: {
    sent_change: number
    read_rate_change: number
    critical_alerts_change: number
  }
}

// Reactive state
const filters = reactive<NotificationFilters>({})
const isExpanded = ref(false)
const viewMode = ref<'list' | 'table'>('list')

const notifications = ref<Notification[]>([])
const notificationsLoading = ref(true)
const notificationsError = ref<string | null>(null)

const stats = ref<NotificationStats | null>(null)
const statsLoading = ref(true)
const statsError = ref<string | null>(null)

const criticalCount = ref(0)
const riskAlertsCount = ref(0)
const bulkActionLoading = ref(false)

// Use notification count composable to share state with sidebar
const { unreadCount, setUnreadCount, refreshNotificationCount } = useNotificationCount()

// Filter options
const priorityOptions = [
  { value: 'critical', label: 'Critical', color: 'critical' },
  { value: 'high', label: 'High', color: 'high' },
  { value: 'medium', label: 'Medium', color: 'medium' },
  { value: 'low', label: 'Low', color: 'low' }
]

const typeOptions = [
  { value: 'risk_alert', label: 'Risk Alerts' },
  { value: 'performance_alert', label: 'Performance' },
  { value: 'system_alert', label: 'System' },
  { value: 'compliance_alert', label: 'Compliance' },
  { value: 'security_alert', label: 'Security' },
  { value: 'vendor_update', label: 'Vendor Updates' },
  { value: 'user_action', label: 'User Actions' },
  { value: 'maintenance', label: 'Maintenance' }
]

const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'sent', label: 'Sent' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'read', label: 'Read' },
  { value: 'failed', label: 'Failed' }
]

// Computed properties
const activeFiltersCount = computed(() => {
  let count = 0
  if (filters.priority?.length) count += filters.priority.length
  if (filters.type?.length) count += filters.type.length
  if (filters.status?.length) count += filters.status.length
  if (filters.unread_only) count += 1
  if (filters.date_from || filters.date_to) count += 1
  return count
})

// Computed property for unread count in current filtered view
const currentViewUnreadCount = computed(() => {
  return notifications.value.filter(n => n.status !== 'read').length
})

// Import API service
import apiService from '@/services/api'
import notificationService from '@/services/notificationService'
import { useNotificationCount } from '@/composables/useNotificationCount'
import loggingService from '@/services/loggingService'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'

// Helper function to fetch ALL notifications across all pages
const fetchAllNotifications = async (filters: NotificationFilters = {}) => {
  try {
    // Use the API service method that handles pagination
    const allNotifications = await apiService.getAllNotifications(filters)
    return allNotifications
  } catch (err) {
    console.error('Error fetching all notifications:', err)
    // Fallback: try single page fetch
    const response: any = await apiService.getNotifications(filters)
    return Array.isArray(response) ? response : (response.results || [])
  }
}

// Methods
const fetchNotifications = async () => {
  try {
    notificationsLoading.value = true
    const apiFilters = {
      unread_only: filters.unread_only,
      priority: filters.priority,
      type: filters.type,
      status: filters.status,
      date_from: filters.date_from,
      date_to: filters.date_to,
    }
    const response: any = await apiService.getNotifications(apiFilters)
    const notificationsList = Array.isArray(response) ? response : (response.results || [])
    notifications.value = notificationsList
    notificationsError.value = null
    
    // Counts are now managed by fetchStats function for consistency
  } catch (err) {
    console.error('Failed to fetch notifications:', err)
    notifications.value = []
    notificationsError.value = 'Failed to load notifications'
    setUnreadCount(0) // Sync with sidebar
    criticalCount.value = 0
    riskAlertsCount.value = 0
  } finally {
    notificationsLoading.value = false
  }
}

const fetchStats = async () => {
  try {
    statsLoading.value = true
    const data: any = await apiService.getNotificationStats()
    stats.value = data
    statsError.value = null
    
    // Update counts from stats data
    setUnreadCount(data.total_unread) // Sync with sidebar
    criticalCount.value = data.by_priority.critical || 0
    
    // Calculate risk alerts count
    const allNotifications = await apiService.getNotifications({})
    const allNotificationsList = Array.isArray(allNotifications) ? allNotifications : (allNotifications.results || [])
    riskAlertsCount.value = allNotificationsList.filter((n: Notification) => 
      n.notification_type === 'risk_alert' || n.notification_type === 'security_alert'
    ).length
  } catch (err) {
    console.error('Failed to fetch stats:', err)
    // Set default stats if API fails
    stats.value = {
      total_sent: 0,
      total_read: 0,
      total_unread: 0,
      by_priority: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      },
      trends: {
        sent_change: 0,
        read_rate_change: 0,
        critical_alerts_change: 0
      }
    }
    statsError.value = 'Failed to load statistics'
    setUnreadCount(0) // Sync with sidebar
    criticalCount.value = 0
    riskAlertsCount.value = 0
  } finally {
    statsLoading.value = false
  }
}

// Helper function to update stats optimistically based on local actions
const updateStatsLocally = (action: 'mark_read' | 'delete', notifications: Notification[]) => {
  if (!stats.value || notifications.length === 0) return
  
  // Create a deep copy to avoid mutating the original
  const currentStats = {
    ...stats.value,
    by_priority: { ...stats.value.by_priority },
    trends: { ...stats.value.trends }
  }
  
  if (action === 'mark_read') {
    // Mark notifications as read
    const unreadNotifications = notifications.filter(n => n.status !== 'read')
    const unreadCount = unreadNotifications.length
    
    if (unreadCount > 0) {
      currentStats.total_read = (currentStats.total_read || 0) + unreadCount
      currentStats.total_unread = Math.max(0, (currentStats.total_unread || 0) - unreadCount)
      
      // Ensure total_sent is consistent
      if (currentStats.total_sent === undefined || currentStats.total_sent < currentStats.total_read) {
        currentStats.total_sent = currentStats.total_read + currentStats.total_unread
      }
    }
  } else if (action === 'delete') {
    // Delete notifications
    const deletedCount = notifications.length
    const deletedRead = notifications.filter(n => n.status === 'read').length
    const deletedUnread = deletedCount - deletedRead
    
    currentStats.total_sent = Math.max(0, (currentStats.total_sent || 0) - deletedCount)
    currentStats.total_read = Math.max(0, (currentStats.total_read || 0) - deletedRead)
    currentStats.total_unread = Math.max(0, (currentStats.total_unread || 0) - deletedUnread)
    
    // Update priority counts
    notifications.forEach(notification => {
      const priority = notification.priority
      if (currentStats.by_priority && currentStats.by_priority[priority] !== undefined) {
        currentStats.by_priority[priority] = Math.max(
          0,
          (currentStats.by_priority[priority] || 0) - 1
        )
      }
    })
    
    // Update critical count if needed
    const deletedCritical = notifications.filter(n => n.priority === 'critical').length
    if (deletedCritical > 0 && criticalCount.value > 0) {
      criticalCount.value = Math.max(0, criticalCount.value - deletedCritical)
    }
    
    // Update risk alerts count if needed
    const deletedRiskAlerts = notifications.filter(n => 
      n.notification_type === 'risk_alert' || n.notification_type === 'security_alert'
    ).length
    if (deletedRiskAlerts > 0 && riskAlertsCount.value > 0) {
      riskAlertsCount.value = Math.max(0, riskAlertsCount.value - deletedRiskAlerts)
    }
  }
  
  // Update the reactive stats object
  stats.value = currentStats
}

const handlePriorityChange = (priority: string, checked: boolean) => {
  const currentPriorities = filters.priority || []
  const newPriorities = checked
    ? [...currentPriorities, priority]
    : currentPriorities.filter(p => p !== priority)
  
  filters.priority = newPriorities.length > 0 ? newPriorities : undefined
}

const handleTypeChange = (type: string, checked: boolean) => {
  const currentTypes = filters.type || []
  const newTypes = checked
    ? [...currentTypes, type]
    : currentTypes.filter(t => t !== type)
  
  filters.type = newTypes.length > 0 ? newTypes : undefined
}

const handleStatusChange = (status: string, checked: boolean) => {
  const currentStatuses = filters.status || []
  const newStatuses = checked
    ? [...currentStatuses, status]
    : currentStatuses.filter(s => s !== status)
  
  filters.status = newStatuses.length > 0 ? newStatuses : undefined
}

const clearFilters = () => {
  Object.keys(filters).forEach(key => {
    delete filters[key as keyof NotificationFilters]
  })
}

const toggleCriticalFilter = () => {
  const hasCritical = filters.priority?.includes('critical')
  handlePriorityChange('critical', !hasCritical)
}

const toggleRiskAlertsFilter = () => {
  const hasRiskAlerts = filters.type?.includes('risk_alert') || filters.type?.includes('security_alert')
  if (hasRiskAlerts) {
    const newTypes = filters.type?.filter(t => t !== 'risk_alert' && t !== 'security_alert') || []
    filters.type = newTypes.length > 0 ? newTypes : undefined
  } else {
    const currentTypes = filters.type || []
    const newTypes = [...currentTypes, 'risk_alert', 'security_alert']
    filters.type = newTypes
  }
}

const removePriorityFilter = (priority: string) => {
  handlePriorityChange(priority, false)
}

const removeTypeFilter = (type: string) => {
  handleTypeChange(type, false)
}

const removeStatusFilter = (status: string) => {
  handleStatusChange(status, false)
}

const markAsRead = async (id: string) => {
  try {
    const notification = notifications.value.find(n => n.id === id)
    if (!notification) return
    
    await apiService.markNotificationAsRead(id)
    
    // Log the action
    await loggingService.logNotificationRead(id)
    
    // Update local state
    notifications.value = notifications.value.map(n => 
      n.id === id 
        ? { ...n, status: 'read', read_at: new Date().toISOString() }
        : n
    )
    
    // Update stats optimistically
    if (notification.status !== 'read') {
      updateStatsLocally('mark_read', [notification])
      setUnreadCount(Math.max(0, unreadCount.value - 1)) // Sync with sidebar
    }
    
    // Refresh stats from server to ensure accuracy
    await fetchStats()
  } catch (err) {
    console.error('Failed to mark notification as read:', err)
  }
}

const dismissNotification = async (id: string) => {
  try {
    const notification = notifications.value.find(n => n.id === id)
    if (!notification) return
    
    await apiService.dismissNotification(id)
    
    // Log the action
    await loggingService.logNotificationDismiss(id)
    
    // Remove from local state
    notifications.value = notifications.value.filter(n => n.id !== id)
    
    // Update stats optimistically
    updateStatsLocally('delete', [notification])
    
    // Update counts
    if (notification.status !== 'read') {
      setUnreadCount(Math.max(0, unreadCount.value - 1)) // Sync with sidebar
    }
    if (notification.priority === 'critical') {
      criticalCount.value = Math.max(0, criticalCount.value - 1)
    }
    if (notification.notification_type === 'risk_alert' || notification.notification_type === 'security_alert') {
      riskAlertsCount.value = Math.max(0, riskAlertsCount.value - 1)
    }
    
    // Refresh stats from server to ensure accuracy
    await fetchStats()
  } catch (err) {
    console.error('Failed to delete notification:', err)
  }
}

const handleNotificationClick = (notification: Notification) => {
  if (notification.status !== 'read') {
    markAsRead(notification.id)
  }
  console.log('Notification clicked:', notification)
}

const markAllAsRead = async () => {
  try {
    bulkActionLoading.value = true
    
    // Fetch ALL unread notifications across all pages (without filters) to mark them all as read
    console.log('📖 Fetching all unread notifications to mark as read...')
    const allUnreadNotifications = await fetchAllNotifications({ unread_only: true })
    
    if (allUnreadNotifications.length === 0) {
      console.log('ℹ️ No unread notifications found')
      bulkActionLoading.value = false
      PopupService.info('All notifications are already read.', 'No Action Needed')
      return
    }
    
    console.log(`📖 Marking ${allUnreadNotifications.length} unread notification(s) as read...`)
    
    // Mark all unread notifications as read
    const promises = allUnreadNotifications.map(notification => 
      apiService.markNotificationAsRead(notification.id).catch(err => {
        console.error(`Failed to mark notification ${notification.id} as read:`, err)
        return null // Continue with other notifications even if one fails
      })
    )
    
    const results = await Promise.all(promises)
    const successCount = results.filter(r => r !== null).length
    console.log(`✅ Successfully marked ${successCount}/${allUnreadNotifications.length} notifications as read`)
    
    // Log bulk action (fire and forget for performance)
    Promise.all(
      allUnreadNotifications.map(notification => 
        loggingService.logNotificationRead(notification.id).catch(() => {})
      )
    ).catch(() => {})
    
    // Update stats optimistically
    if (allUnreadNotifications.length > 0) {
      updateStatsLocally('mark_read', allUnreadNotifications)
    }
    
    // Update local filtered notifications state if they're in the current view
    notifications.value = notifications.value.map(notification => {
      const wasUnread = allUnreadNotifications.find(n => n.id === notification.id)
      return wasUnread 
        ? { ...notification, status: 'read', read_at: notification.read_at || new Date().toISOString() }
        : notification
    })
    
    // Update counts
    const previousUnread = unreadCount.value
    setUnreadCount(0) // All are now read
    await refreshNotificationCount() // Refresh from server
    
    // Refresh notifications and stats to get latest data from server
    await fetchNotifications()
    await fetchStats()
    
    console.log(`✅ Mark all as read completed. Previous unread: ${previousUnread}, Now: 0`)
    
    // Show success message
    PopupService.success(`Successfully marked ${successCount} notification(s) as read!`, 'Mark All Read')
    
  } catch (err) {
    console.error('❌ Failed to mark all notifications as read:', err)
    PopupService.error('Failed to mark all notifications as read. Please try again.', 'Operation Failed')
    // Still refresh to get accurate state
    await fetchNotifications()
    await fetchStats()
  } finally {
    bulkActionLoading.value = false
  }
}

const deleteAllNotifications = async () => {
  // Get total count from stats (all notifications, not just filtered)
  const totalNotificationCount = stats.value?.total_sent || 0
  if (totalNotificationCount === 0) {
    PopupService.info('No notifications to delete.', 'No Action Needed')
    return
  }
  
  if (!confirm(`Are you sure you want to delete all ${totalNotificationCount} notification(s)? This action cannot be undone.`)) {
    return
  }
  
  try {
    bulkActionLoading.value = true
    
    // Fetch ALL notifications across all pages (without filters) to delete them all
    console.log(`🗑️ Fetching all ${totalNotificationCount} notifications to delete...`)
    const allNotifications = await fetchAllNotifications({})
    
    if (allNotifications.length === 0) {
      console.log('ℹ️ No notifications found to delete')
      bulkActionLoading.value = false
      return
    }
    
    console.log(`🗑️ Deleting ${allNotifications.length} notification(s)...`)
    
    // Update stats optimistically before deletion
    updateStatsLocally('delete', allNotifications)
    
    // Delete all notifications
    const notificationIds = allNotifications.map(n => n.id)
    const promises = notificationIds.map(id => 
      apiService.dismissNotification(id).catch(err => {
        console.error(`Failed to delete notification ${id}:`, err)
        return null // Continue with other notifications even if one fails
      })
    )
    
    const results = await Promise.all(promises)
    const successCount = results.filter(r => r !== null).length
    console.log(`✅ Successfully deleted ${successCount}/${allNotifications.length} notifications`)
    
    // Log bulk action (fire and forget for performance)
    Promise.all(
      notificationIds.map(id => 
        loggingService.logNotificationDismiss(id).catch(() => {})
      )
    ).catch(() => {})
    
    // Clear all notifications from local filtered state
    notifications.value = []
    
    // Update counts
    setUnreadCount(0)
    criticalCount.value = 0
    riskAlertsCount.value = 0
    await refreshNotificationCount() // Refresh from server
    
    // Refresh notifications and stats to get latest data from server
    await fetchNotifications()
    await fetchStats()
    
    console.log(`✅ Delete all completed. Deleted ${successCount} notifications`)
    
    // Show success message
    PopupService.success(`Successfully deleted ${successCount} notification(s)!`, 'Delete All')
    
  } catch (err) {
    console.error('❌ Failed to delete all notifications:', err)
    PopupService.error('Failed to delete all notifications. Please try again.', 'Operation Failed')
    // Still refresh to get accurate state
    await fetchNotifications()
    await fetchStats()
  } finally {
    bulkActionLoading.value = false
  }
}

const getPriorityBadgeClass = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'border-transparent bg-red-100 text-red-800 hover:bg-red-200'
    case 'high':
      return 'border-transparent bg-orange-100 text-orange-800 hover:bg-orange-200'
    case 'medium':
      return 'border-transparent bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
    case 'low':
      return 'border-transparent bg-green-100 text-green-800 hover:bg-green-200'
    default:
      return 'border-transparent bg-gray-100 text-gray-800 hover:bg-gray-200'
  }
}

const formatTimeAgo = (dateString: string) => {
  const now = new Date()
  const date = new Date(dateString)
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`
  } else if (diffInMinutes < 1440) {
    return `${Math.floor(diffInMinutes / 60)}h ago`
  } else {
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }
}

// Listen for new notifications - set up subscription
let unsubscribe: (() => void) | null = null

// Lifecycle
onMounted(async () => {
  // Log page view
  await loggingService.logNotificationView()
  
  // Refresh notification count to ensure it's up to date
  await refreshNotificationCount()
  
  fetchNotifications()
  fetchStats()
  
  // Listen for new notifications
  unsubscribe = notificationService.subscribe((newNotification) => {
    // Add new notification to the list
    notifications.value.unshift(newNotification)
    
    // Update counts
    if (newNotification.status !== 'read') {
      setUnreadCount(unreadCount.value + 1) // Sync with sidebar
    }
    if (newNotification.priority === 'critical') {
      criticalCount.value += 1
    }
    if (newNotification.notification_type === 'risk_alert' || newNotification.notification_type === 'security_alert') {
      riskAlertsCount.value += 1
    }
    
    // Update stats
    if (stats.value) {
      stats.value.total_sent += 1
      stats.value.total_unread += 1
    }
  })
})

// Cleanup subscription on unmount - called at top level
onUnmounted(() => {
  if (unsubscribe) {
    unsubscribe()
  }
})

// Watchers
watch(filters, () => {
  fetchNotifications()
}, { deep: true })
</script>
