<template>
  <div>
    <!-- Inlined Toaster component -->
    <div>
      <div v-for="toast in toasts" :key="toast.id" class="toast">
        <div class="grid gap-1">
          <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
          <div v-if="toast.description" class="toast-description">{{ toast.description }}</div>
        </div>
        <div v-if="toast.action" class="toast-action">{{ toast.action }}</div>
        <button class="toast-close" @click="dismiss(toast.id)">×</button>
      </div>
    </div>
    
    <!-- Inlined Sonner component -->
    <div class="toaster group">
      <!-- Sonner toast container -->
    </div>
    
    <!-- Main Application Container -->
    <div class="risk-app-container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="text-2xl font-bold text-gray-900">Vendor Risk Dashboard</h1>
          <p class="text-gray-600">Analyze and manage third-party risk assessments with AI-powered insights</p>
        </div>
      </div>

      <!-- Filters Section - Separate Layout -->
      <div class="filters-top-section">
      <div class="filters-container">
        <div class="filter-row">
          <!-- Filter dropdowns -->
          <div class="filter-dropdowns">
            <!-- Vendor Filter -->
            <div class="relative" ref="vendorSelectRef">
              <button
                type="button"
                class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                @click="toggleVendorSelect"
              >
                <span v-if="filters.vendor" class="line-clamp-1">{{ getVendorDisplayName(filters.vendor) }}</span>
                <span v-else class="text-muted-foreground">{{ vendorsLoading ? 'Loading...' : `All Vendors (${vendorOptions.length - 1})` }}</span>
                <ChevronDown class="h-4 w-4 opacity-50" />
              </button>
              
              <div v-if="vendorSelectOpen" class="absolute z-[99999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-y-auto rounded-md border bg-white text-gray-900 shadow-lg">
                  <div class="p-1">
                    <!-- Debug info -->
                    <div v-if="vendorOptions.length === 0" class="p-2 text-sm text-gray-500">
                      No vendors available
                    </div>
                    <div 
                      v-for="option in vendorOptions" 
                      :key="option.value"
                      class="relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-blue-100 transition-colors"
                      @click.stop="selectVendorOption(option.value)"
                    >
                      <span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                        <Check v-if="filters.vendor === option.value" class="h-4 w-4 text-blue-600" />
                      </span>
                      <div class="flex items-center gap-2">
                        <span class="text-gray-900">{{ option.label }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Note: Date filters are UI-only for now -->
            <!-- Inlined SimpleSelect component -->
            <div class="relative" ref="moduleSelectRef">
              <button
                type="button"
                class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                @click="toggleModuleSelect"
              >
                <span v-if="filters.module" class="line-clamp-1">{{ filters.module }}</span>
                <span v-else class="text-muted-foreground">{{ modulesLoading ? 'Loading...' : 'Module' }}</span>
                <ChevronDown class="h-4 w-4 opacity-50" />
              </button>
              
              <div v-if="moduleSelectOpen" class="absolute z-[99999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-white text-gray-900 shadow-lg">
                  <div class="p-1">
                    <div 
                      v-for="option in moduleOptions" 
                      :key="option.value"
                      class="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                      @click="selectModuleOption(option.value)"
                    >
                      <span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                        <Check v-if="filters.module === option.value" class="h-4 w-4" />
                      </span>
                      <div class="flex items-center gap-2">
                        <span>{{ option.label }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Inlined SimpleSelect component -->
            <div class="relative" ref="prioritySelectRef">
              <button
                type="button"
                class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                @click="togglePrioritySelect"
              >
                <span v-if="filters.priority" class="line-clamp-1">{{ filters.priority }}</span>
                <span v-else class="text-muted-foreground">Priority</span>
                <ChevronDown class="h-4 w-4 opacity-50" />
              </button>
              
              <div v-if="prioritySelectOpen" class="absolute z-[99999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-white text-gray-900 shadow-lg">
                  <div class="p-1">
                    <div 
                      v-for="option in priorityOptions" 
                      :key="option.value"
                      class="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                      @click="selectPriorityOption(option.value)"
                    >
                      <span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                        <Check v-if="filters.priority === option.value" class="h-4 w-4" />
                      </span>
                      <div class="flex items-center gap-2">
                        <span>{{ option.label }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Inlined SimpleSelect component -->
            <div class="relative" ref="dateSelectRef">
              <button
                type="button"
                class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                @click="toggleDateSelect"
              >
                <span v-if="filters.date" class="line-clamp-1">{{ filters.date }}</span>
                <span v-else class="text-muted-foreground">Date</span>
                <ChevronDown class="h-4 w-4 opacity-50" />
              </button>
              
              <div v-if="dateSelectOpen" class="absolute z-[99999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-white text-gray-900 shadow-lg">
                  <div class="p-1">
                    <div 
                      v-for="option in dateOptions" 
                      :key="option.value"
                      class="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                      @click="selectDateOption(option.value)"
                    >
                      <span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                        <Check v-if="filters.date === option.value" class="h-4 w-4" />
                      </span>
                      <div class="flex items-center gap-2">
                        <span>{{ option.label }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Search and Action buttons row -->
          <div class="search-and-actions">
            <div class="search-container">
              <Search class="search-icon" />
              <input
                placeholder="Search risks..."
                v-model="searchTerm"
                class="search-input"
                @input="handleSearchInput"
              />
            </div>
            
            <button 
              class="action-button"
              @click="resetFilters"
            >
              <RotateCcw class="h-4 w-4" />
              Reset
            </button>
            
            <button 
              class="action-button"
              @click="handleOpenAiModal"
            >
              <Brain class="h-4 w-4" />
              Llama 2 Risk Generation
            </button>
          </div>
        </div>
      </div>


      <!-- Main Content Section - Separate Layout -->
      <div class="main-content-section">
      <!-- Main Content Grid -->
      <div class="risk-workspace-two-column">
        <!-- Risk Table Column -->
        <div class="risk-table-column">
          <!-- Inlined Card component -->
          <div class="risk-table-container">
            <div class="column-title">
              Predicted Risks
            </div>
            
            <!-- Loading State -->
            <div v-if="risksLoading" class="flex items-center justify-center py-8">
              <RefreshCw class="h-6 w-6 animate-spin mr-2" />
              <span>Loading risks...</span>
            </div>
            
            <!-- Risk Table -->
            <div v-else class="relative overflow-auto">
              <!-- Inlined Table component -->
              <div class="relative w-full overflow-auto">
                <table class="w-full caption-bottom text-sm">
                    <!-- Inlined TableHeader component -->
                    <thead class="[&_tr]:border-b">
                      <!-- Inlined TableRow component -->
                      <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                        <!-- Inlined TableHead component -->
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-20">Risk ID</th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 min-w-60">Risk Title</th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-20 text-center">Likelihood</th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-16 text-center">Impact</th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-16 text-center">Exposure</th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-16 text-center">Score</th>
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-20 text-center">Priority</th>
                      </tr>
                    </thead>
                    <!-- Inlined TableBody component -->
                    <tbody class="[&_tr:last-child]:border-0">
                      <template v-for="risk in sortedRisks" :key="risk.id">
                        <!-- Inlined TableRow component -->
                        <tr
                          class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted cursor-pointer hover:bg-muted/50 transition-colors"
                          :data-priority="risk.priority"
                          @click="handleRiskClick(risk.id)"
                        >
                          <!-- Inlined TableCell component -->
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-mono text-sm">{{ risk.id }}</td>
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-medium">{{ risk.title }}</td>
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-center">{{ risk.likelihood }}</td>
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-center">{{ risk.impact }}</td>
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-center">{{ risk.exposure_rating || 3 }}</td>
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-center font-semibold">
                            <span class="score-badge" :class="risk.priority.toLowerCase()">{{ risk.score }}</span>
                          </td>
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-center">
                            <span class="priority-badge" :class="`priority-badge-${risk.priority.toLowerCase()}`">{{ risk.priority }}</span>
                          </td>
                        </tr>
                        <tr v-if="expandedRisk === risk.id" :key="`${risk.id}-details`" class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                          <td colspan="6" class="p-0">
                            <div class="bg-muted/30 border-t p-6 space-y-4">
                              <div class="flex items-center justify-between">
                                <h3 class="text-lg font-semibold flex items-center gap-2">
                                  Risk Details
                                  <span class="text-sm font-medium">{{ risk.priority }}</span>
                                </h3>
                                <!-- Inlined Button component -->
                                <button
                                  class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3"
                                  @click="expandedRisk = null"
                                >
                                  <ChevronUp class="h-4 w-4" />
                                </button>
                              </div>
                              
                              <div class="grid grid-cols-3 gap-4">
                                <div>
                                  <p class="text-sm font-medium text-muted-foreground">Risk ID</p>
                                  <p class="font-mono">{{ risk.id }}</p>
                                </div>
                                <div>
                                  <p class="text-sm font-medium text-muted-foreground">Source</p>
                                  <p class="font-medium">Entity Data</p>
                                </div>
                                <div>
                                  <p class="text-sm font-medium text-muted-foreground">Score</p>
                                  <p class="font-semibold">{{ risk.score }}</p>
                                </div>
                                <div>
                                  <p class="text-sm font-medium text-muted-foreground">Exposure Rating</p>
                                  <p class="font-semibold">{{ risk.exposure_rating || 3 }}</p>
                                </div>
                                <div>
                                  <p class="text-sm font-medium text-muted-foreground">L × I × E × 1.33</p>
                                  <p>{{ risk.likelihood }} × {{ risk.impact }} × {{ risk.exposure_rating || 3 }} × 1.33</p>
                                </div>
                              </div>
                              
                              <div>
                                <p class="text-sm font-medium text-muted-foreground mb-2">Title</p>
                                <p class="font-medium">{{ risk.title }}</p>
                              </div>

                              <div>
                                <p class="text-sm font-medium text-muted-foreground mb-2">Description</p>
                                <p class="text-sm leading-relaxed">{{ risk.description }}</p>
                              </div>

                              <div>
                                <p class="text-sm font-medium text-muted-foreground mb-2">AI Explanation</p>
                                <p class="text-sm leading-relaxed">{{ risk.ai_explanation }}</p>
                              </div>

                              <div>
                                <p class="text-sm font-medium text-muted-foreground mb-2">Suggested Mitigations</p>
                                <ul class="space-y-1">
                    <li 
                      v-for="(mitigation, index) in parseMitigations(risk.suggested_mitigations)" 
                      :key="index" 
                      class="text-sm flex items-start gap-2"
                    >
                      <span class="text-primary">•</span>
                      {{ mitigation }}
                    </li>
                                </ul>
                              </div>

                            </div>
                          </td>
                        </tr>
                      </template>
                    </tbody>
                  </table>
                </div>
                <!-- Pagination Controls -->
                <div class="mt-4 flex items-center justify-between">
                  <div class="text-sm text-muted-foreground">
                    Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, risksData && risksData.count || 0) }} of {{ risksData && risksData.count || 0 }} results
                  </div>
                  <div class="flex items-center gap-2" v-if="totalPages > 1">
                    <!-- Previous Button -->
                    <button
                      @click="goToPreviousPage"
                      :disabled="currentPage <= 1"
                      class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-3"
                    >
                      <ChevronLeft class="h-4 w-4" />
                      Previous
                    </button>
                    
                    <!-- Page Numbers -->
                    <div class="flex items-center gap-1">
                      <template v-for="page in getPageNumbers()" :key="page">
                        <button
                          v-if="page !== '...'"
                          @click="goToPage(page)"
                          :class="`
                            inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 w-9
                            ${currentPage === page ? 'bg-primary text-primary-foreground' : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'}
                          `"
                        >
                          {{ page }}
                        </button>
                        <span v-else class="px-2 text-muted-foreground">...</span>
                      </template>
                    </div>
                    
                    <!-- Next Button -->
                    <button
                      @click="goToNextPage"
                      :disabled="currentPage >= totalPages"
                      class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-3"
                    >
                      Next
                      <ChevronRight class="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

        <!-- Risk Heatmap Column -->
        <div class="risk-heatmap-column">
          <!-- Inlined Card component -->
          <div class="risk-heatmap-container">
            <div class="column-title">
              Risk Heatmap
            </div>
            <div v-if="dashboardLoading" class="flex items-center justify-center py-8">
              <RefreshCw class="h-6 w-6 animate-spin mr-2" />
              <span>Loading heatmap...</span>
            </div>
            
            <!-- Risk Heatmap -->
            <div v-else class="space-y-4">
                <!-- How to Read the Heatmap Section -->
                <div class="bg-muted/50 p-4 rounded-lg border">
                  <h3 class="text-sm font-semibold mb-2 text-foreground">How to Read the Risk Heatmap</h3>
                  <div class="text-xs text-muted-foreground space-y-2">
                    <p>
                      <strong>Risk Score Calculation:</strong> Each cell shows a risk score calculated using the formula 
                      <span class="font-medium text-foreground">Likelihood × Impact × Exposure × 1.33</span>.
                    </p>
                    <p>
                      <strong>Color Coding:</strong> Colors indicate risk severity levels - darker colors represent higher risk scores.
                      The number in each cell shows the calculated risk score, and the number in parentheses shows how many risks fall into that category.
                    </p>
                    <p>
                      <strong>Reading the Grid:</strong> 
                      • <span class="font-medium text-foreground">Horizontal axis (→)</span> represents Impact levels (1-5)
                      • <span class="font-medium text-foreground">Vertical axis (↑)</span> represents Likelihood levels (1-5)
                      • <span class="font-medium text-foreground">Hover over cells</span> to see detailed information
                    </p>
                    <p>
                      <strong>Risk Prioritization:</strong> Focus on the top-right corner (high impact, high likelihood) for critical risks that need immediate attention.
                    </p>
                  </div>
                </div>

                <!-- Risk Heatmap Grid -->
                <div class="heatmap-wrapper">
                  <!-- Title and axis labels -->
                  <div class="heatmap-title mb-3 text-center">
                    <div class="text-sm font-medium text-muted-foreground">Risk Score Matrix</div>
                    <div class="text-xs text-muted-foreground mt-1">Impact (→) vs Likelihood (↑)</div>
                  </div>
                  
                  <!-- Main heatmap grid -->
                  <div class="heatmap-grid">
                    <!-- Top header with Impact levels -->
                    <div class="heatmap-header">
                      <div class="heatmap-corner"></div>
                      <div class="heatmap-impact-header">
                        <div class="heatmap-impact-label">Impact →</div>
                        <div class="heatmap-impact-values">
                          <div v-for="impact in [1, 2, 3, 4, 5]" :key="`impact-${impact}`" class="heatmap-header-cell">
                            {{ impact }}
                          </div>
                        </div>
                      </div>
                  </div>

                    <!-- Likelihood levels and risk cells -->
                    <div class="heatmap-body">
                      <div class="heatmap-likelihood-sidebar">
                        <div class="heatmap-likelihood-label">
                          <div class="likelihood-text">Likelihood</div>
                          <div class="likelihood-arrow">↑</div>
                    </div>
                        <div class="heatmap-likelihood-values">
                          <div v-for="likelihood in [5, 4, 3, 2, 1]" :key="`likelihood-${likelihood}`" class="heatmap-likelihood-cell">
                            {{ likelihood }}
                          </div>
                        </div>
                      </div>
                      
                      <!-- Risk matrix cells -->
                      <div class="heatmap-matrix">
                        <div v-for="likelihood in [5, 4, 3, 2, 1]" :key="`row-${likelihood}`" class="heatmap-row">
                          <div
                            v-for="impact in [1, 2, 3, 4, 5]"
                            :key="`cell-${likelihood}-${impact}`"
                            :class="`heatmap-cell ${getCellColor(likelihood, impact)}`"
                            :title="getCellCount(dashboardData && dashboardData.recent_risks || [], likelihood, impact) > 0 ? `${getCellCount(dashboardData && dashboardData.recent_risks || [], likelihood, impact)} risk(s) - Score: ${likelihood * impact * 3 * 1.33}` : `Risk score: ${Math.round(likelihood * impact * 3 * 1.33)}`"
                          >
                            <div class="cell-content">
                              <div class="cell-score">{{ Math.round(likelihood * impact * 3 * 1.33) }}</div>
                              <div v-if="getCellCount(dashboardData && dashboardData.recent_risks || [], likelihood, impact) > 0" class="cell-count">
                          ({{ getCellCount(dashboardData && dashboardData.recent_risks || [], likelihood, impact) }})
                        </div>
                      </div>
                    </div>
                  </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Legend -->
                <div class="heatmap-legend">
                  <div class="legend-title">Risk Severity Legend</div>
                  <div class="legend-items">
                    <div class="legend-item">
                      <div class="legend-color bg-risk-none"></div>
                      <div class="legend-text">
                        <span class="legend-label">Minimal</span>
                        <span class="legend-range">(5-15)</span>
                    </div>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color bg-risk-low"></div>
                      <div class="legend-text">
                        <span class="legend-label">Low</span>
                        <span class="legend-range">(16-35)</span>
                    </div>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color bg-risk-medium"></div>
                      <div class="legend-text">
                        <span class="legend-label">Moderate</span>
                        <span class="legend-range">(36-55)</span>
                    </div>
                  </div>
                    <div class="legend-item">
                      <div class="legend-color bg-risk-high"></div>
                      <div class="legend-text">
                        <span class="legend-label">High</span>
                        <span class="legend-range">(56-75)</span>
                      </div>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color bg-risk-critical"></div>
                      <div class="legend-text">
                        <span class="legend-label">Critical</span>
                        <span class="legend-range">(76-100)</span>
                      </div>
                    </div>
                  </div>
                  <div class="legend-note">
                    <p class="text-xs text-muted-foreground">
                      <strong>Score Formula:</strong> Likelihood × Impact × Exposure × 1.33
                    </p>
                    <p class="text-xs text-muted-foreground mt-1">
                      Hover over cells to see risk counts and detailed scores
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>

    </div>
    
    <!-- AI Risk Generation Modal -->
    <Teleport to="body">
      <div v-if="aiModalOpen" class="modal-overlay">
        <!-- Overlay -->
        <div 
          class="modal-backdrop"
          @click="handleAiModalOpenChange(false)"
        ></div>
        
        <!-- Content -->
        <div class="modal-content">
          <div class="modal-close-btn">
            <button @click="handleAiModalOpenChange(false)" class="close-button">
              <span class="sr-only">Close</span>
              ×
            </button>
          </div>
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="modal-title">
              <Brain class="modal-icon" />
              <span>Llama 2 Risk Generation</span>
            </div>
            <p class="modal-description">
              Select a module to generate Llama 2-powered risk predictions. The AI will analyze existing data from the selected module and create relevant risk assessments based on the actual module data.
            </p>
          </div>
          
          <!-- Modal Body -->
          <div class="modal-body">
            <div class="form-group">
              <label for="module-select" class="form-label">
                Select Module
              </label>
              <!-- Module Select Dropdown -->
              <div class="select-wrapper" ref="aiModuleSelectRef">
                <button
                  type="button"
                  class="select-button"
                  @click="toggleAiModuleSelect"
                >
                  <span v-if="selectedAiModule" class="select-text">{{ selectedAiModule }}</span>
                  <span v-else class="select-placeholder">Choose a module...</span>
                  <ChevronDown class="select-icon" />
                </button>
                
                <div v-if="aiModuleSelectOpen" class="select-dropdown" style="z-index: 999999;">
                  <div class="select-options">
                    <div 
                      v-for="option in aiModuleOptions" 
                      :key="option.value"
                      class="select-option"
                      @click="selectAiModuleOption(option.value)"
                    >
                      <span class="option-check">
                        <Check v-if="selectedAiModule === option.value" class="check-icon" />
                      </span>
                      <span class="option-text">{{ option.label }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="selectedAiModule" class="selected-module-info">
              <div class="info-header">
                <strong>Selected:</strong> {{ selectedAiModule }}
              </div>
              <p class="info-description">
                Llama 2 will analyze existing data from this module and generate 2-5 relevant risk predictions with detailed explanations and mitigation strategies based on the actual module data.
              </p>
              <div class="info-note">
                <strong>Note:</strong> Only modules with unprocessed data can generate risks. If you see an error, try selecting a different module.
              </div>
            </div>
          </div>
          
          <!-- Modal Footer -->
          <div class="modal-footer">
            <button
              class="btn-secondary"
              @click="aiModalOpen = false"
              :disabled="isGenerating"
            >
              Cancel
            </button>
            <button
              class="btn-primary"
              @click="handleGenerateRisks"
              :disabled="!selectedAiModule || isGenerating"
            >
              <template v-if="isGenerating">
                <Loader2 class="btn-icon animate-spin" />
                Generating...
              </template>
              <template v-else>
                <Brain class="btn-icon" />
                Generate Risks
              </template>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    
    <!-- Results Modal -->
    <Teleport to="body">
      <div v-if="resultsModalOpen" class="fixed inset-0 z-50">
        <!-- Overlay -->
        <div 
          class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm animate-in fade-in-0"
          @click="resultsModalOpen = false"
        />
        
        <!-- Content -->
        <div class="fixed left-[50%] top-[50%] z-50 grid w-full max-w-4xl translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 animate-in fade-in-0 zoom-in-95 slide-in-from-left-1/2 slide-in-from-top-[48%] sm:rounded-lg max-h-[80vh] overflow-y-auto">
          <!-- Inlined DialogHeader -->
          <div class="flex flex-col space-y-1.5 text-center sm:text-left">
            <!-- Inlined DialogTitle -->
            <h2 class="text-lg font-semibold leading-none tracking-tight flex items-center gap-2">
              <CheckCircle class="w-5 h-5 text-green-600" />
              Risk Generation Results
            </h2>
            <!-- Inlined DialogDescription -->
            <p class="text-sm text-muted-foreground">
              <div v-if="generationResults" class="space-y-2">
                <p class="text-sm text-muted-foreground">
                  {{ generationResults.message }}
                </p>
                <div class="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Module: <strong>{{ generationResults.module_name }}</strong></span>
                  <span>•</span>
                  <span>Data Source: <strong>{{ generationResults.data_source }}</strong></span>
                </div>
              </div>
              <span v-else>Generated risks will appear here</span>
            </p>
          </div>

        <div v-if="isGenerating" class="flex items-center justify-center py-8">
          <div class="flex items-center gap-2">
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span class="text-sm text-muted-foreground">
              Generating risks with Llama 2...
            </span>
          </div>
        </div>

        <div v-if="generationResults && !isGenerating" class="space-y-6">
          <!-- Summary Section -->
          <div class="space-y-4">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center gap-2 mb-2">
                <Info class="w-4 h-4 text-blue-600" />
                <h3 class="font-medium text-blue-900">Generation Summary</h3>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span class="text-blue-600 font-medium">Total Risks:</span>
                  <span class="ml-1 text-blue-900">{{ generationResults.risks.length }}</span>
                </div>
                <div>
                  <span class="text-blue-600 font-medium">Llama Generated:</span>
                  <span class="ml-1 text-blue-900">{{ generationResults.risk_types.llama_generated }}</span>
                </div>
                <div>
                  <span class="text-blue-600 font-medium">Mock Risks:</span>
                  <span class="ml-1 text-blue-900">{{ generationResults.risk_types.mock_risks }}</span>
                </div>
                <div>
                  <span class="text-blue-600 font-medium">Average Score:</span>
                  <span class="ml-1 text-blue-900">
                    {{ Math.round(generationResults.risks.reduce((sum, r) => sum + r.score, 0) / generationResults.risks.length) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Priority Breakdown -->
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
              <div class="flex items-center gap-2 mb-2">
                <Info class="w-4 h-4 text-green-600" />
                <h3 class="font-medium text-green-900">Priority Breakdown</h3>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span class="text-green-600 font-medium">Critical:</span>
                  <span class="ml-1 text-green-900">
                    {{ generationResults.risks.filter(r => r.priority === 'Critical').length }}
                  </span>
                </div>
                <div>
                  <span class="text-green-600 font-medium">High:</span>
                  <span class="ml-1 text-green-900">
                    {{ generationResults.risks.filter(r => r.priority === 'High').length }}
                  </span>
                </div>
                <div>
                  <span class="text-green-600 font-medium">Medium:</span>
                  <span class="ml-1 text-green-900">
                    {{ generationResults.risks.filter(r => r.priority === 'Medium').length }}
                  </span>
                </div>
                <div>
                  <span class="text-green-600 font-medium">Low:</span>
                  <span class="ml-1 text-green-900">
                    {{ generationResults.risks.filter(r => r.priority === 'Low').length }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Risks List -->
          <div class="space-y-4">
            <h3 class="text-lg font-semibold">Generated Risks</h3>
            <div class="space-y-4">
              <div
                v-for="risk in generationResults.risks"
                :key="risk.id"
                class="border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div class="flex items-start justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium flex items-center gap-1">
                      <component :is="getPriorityIcon(risk.priority)" class="w-4 h-4" />
                      {{ risk.priority }}
                    </span>
                    <!-- Inlined Badge component -->
                    <div
                      class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground"
                      :class="risk.ai_explanation ? 'bg-purple-100 text-purple-800 border-purple-200' : 'bg-orange-100 text-orange-800 border-orange-200'"
                    >
                      {{ risk.ai_explanation ? "Llama Generated" : "Mock Risk" }}
                    </div>
                    <span class="text-sm text-muted-foreground">
                      ID: {{ risk.id }}
                    </span>
                  </div>
                    <div class="text-right text-sm">
                      <div class="text-muted-foreground">Score: {{ risk.score }}</div>
                      <div class="text-muted-foreground">
                        L: {{ risk.likelihood }} | I: {{ risk.impact }} | E: {{ risk.exposure_rating || 3 }}
                      </div>
                    </div>
                </div>

                <h4 class="font-medium text-lg mb-2">{{ risk.title }}</h4>
                <p class="text-sm text-muted-foreground mb-3">
                  {{ risk.description }}
                </p>

                <!-- AI Explanation -->
                <div class="bg-gray-50 rounded p-3 mb-3">
                  <h5 class="font-medium text-sm mb-1 text-gray-700">
                    Llama 2 Analysis:
                  </h5>
                  <p class="text-sm text-gray-600">
                    {{ risk.ai_explanation }}
                  </p>
                </div>

                <!-- Suggested Mitigations -->
                <div v-if="risk.suggested_mitigations && risk.suggested_mitigations.length > 0" class="bg-green-50 rounded p-3">
                  <h5 class="font-medium text-sm mb-2 text-green-700">
                    Suggested Mitigations:
                  </h5>
                  <ul class="space-y-1">
                    <li 
                      v-for="(mitigation, idx) in parseMitigations(risk.suggested_mitigations)" 
                      :key="idx" 
                      class="text-sm text-green-600 flex items-start gap-2"
                    >
                      <span class="text-green-500 mt-1">•</span>
                      {{ mitigation }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex justify-end gap-2 pt-4 border-t">
            <!-- Inlined Button component -->
            <button 
              class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
              @click="resultsModalOpen = false"
            >
              Close
            </button>
            <!-- Inlined Button component -->
            <button 
              class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              @click="resultsModalOpen = false"
            >
              View in Dashboard
            </button>
          </div>
        </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import './VendorRiskScoring.css'
import { ref, computed, watch, onMounted, onUnmounted, reactive } from 'vue';
import { Download, RotateCcw, Search, Shield, ChevronDown, Check, RefreshCw, Brain, Loader2, ChevronUp, CheckCircle, AlertTriangle, Info, ChevronLeft, ChevronRight } from "lucide-vue-next";
import { useNotifications } from '@/composables/useNotifications';
import notificationService from '@/services/notificationService';
import loggingService from '@/services/loggingService';
import { getTprmApiUrl } from '@/utils/backendEnv';

// ===== INLINED API SERVICE =====
const API_BASE_URL = getTprmApiUrl('vendor-risk');

// ===== DATA STRUCTURES =====
// Risk object structure

const Risk = {
  id: '',
  title: '',
  description: '',
  likelihood: 0,
  impact: 0,
  exposure_rating: 0,
  score: 0,
  priority: 'Low',
  ai_explanation: '',
  suggested_mitigations: [],
  status: '',
  created_at: '',
  updated_at: ''
};

// Module object structure
const Module = {
  module_id: 0,
  name: '',
  description: '',
  created_at: '',
  updated_at: ''
};

// Dashboard data structure
const DashboardData = {
  statistics: {
    total_risks: 0,
    critical_risks: 0,
    high_risks: 0,
    medium_risks: 0,
    low_risks: 0,
    average_score: 0
  },
  recent_risks: [],
  modules: []
};

// API Error class
class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(`API Error: ${response.status} - ${errorText}`, response.status);
  }
  
  // Handle empty responses
  const text = await response.text();
  if (!text) {
    return {};
  }
  
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new ApiError(`Failed to parse JSON response: ${error}`);
  }
}

// Helper to get auth headers with JWT token
const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  const headers = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

const api = {
  // Get dashboard data
  async getDashboard() {
    const response = await fetch(`${API_BASE_URL}/dashboard/`, {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse(response);
  },

  // Get all risks with optional filters
  async getRisks(params) {
    const url = new URL(`${API_BASE_URL}/risks/`);
    console.log('=== getRisks called ===');
    console.log('Raw params:', params);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          console.log(`Adding URL param: ${key} = ${value} (type: ${typeof value})`);
          url.searchParams.append(key, value.toString());
        } else {
          console.log(`Skipping URL param: ${key} = ${value}`);
        }
      });
    }
    
    console.log('Final API URL:', url.toString());

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    const data = await handleResponse(response);
    console.log('Risks API response:', data); // Debug log
    console.log('Response count:', data?.count);
    console.log('Response results length:', data?.results?.length);
    // Handle both paginated and non-paginated responses
    if (data && typeof data === 'object' && 'results' in data) {
      return data;
    } else {
      const risksArray = data;
      return { results: risksArray, count: risksArray.length };
    }
  },

  // Get modules
  async getModules() {
    const response = await fetch(`${API_BASE_URL}/modules/`, {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    const data = await handleResponse(response);
    console.log('Modules API response:', data); // Debug log
    // Handle both paginated and non-paginated responses
    if (data && typeof data === 'object' && 'results' in data) {
      return data.results;
    }
    return data;
  },

  // Get vendors
  async getVendors() {
    const response = await fetch(`${API_BASE_URL}/vendors/`, {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    const data = await handleResponse(response);
    console.log('Vendors API response:', data); // Debug log
    return data;
  },

  // Generate Llama 2 risks for a specific module
  async generateLlamaRisks(moduleName) {
    const response = await fetch(`${API_BASE_URL}/generate-risks/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify({ module_name: moduleName }),
    });
    return handleResponse(response);
  },
};

// ===== SIMPLE TOAST SYSTEM =====
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const toasts = ref([])

function showToast(toastData) {
  const id = Date.now().toString()
  const newToast = {
    id,
    ...toastData,
    open: true
  }
  toasts.value.unshift(newToast)
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    dismiss(id)
  }, 5000)
}

function dismiss(toastId) {
  const index = toasts.value.findIndex(t => t.id === toastId)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

// ===== MAIN COMPONENT LOGIC =====

const filters = ref({
  vendor: "",
  module: "All",
  priority: "All",
  date: "This Month"
});

const searchTerm = ref("");
const expandedRisk = ref(null);

// Dropdown state management for inlined SimpleSelect components
const vendorSelectOpen = ref(false);
const moduleSelectOpen = ref(false);
const prioritySelectOpen = ref(false);
const dateSelectOpen = ref(false);
const aiModuleSelectOpen = ref(false);

const vendorSelectRef = ref();
const moduleSelectRef = ref();
const prioritySelectRef = ref();
const dateSelectRef = ref();
const aiModuleSelectRef = ref();

// AI Modal state
const aiModalOpen = ref(false);
const selectedAiModule = ref("");
const isGenerating = ref(false);
const resultsModalOpen = ref(false);
const generationResults = ref(null);

// Data state
const dashboardData = ref(null);
const dashboardLoading = ref(false);
const dashboardError = ref(null);

const modulesData = ref(null);
const modulesLoading = ref(false);
const modulesError = ref(null);

const vendorsData = ref(null);
const vendorsLoading = ref(false);
const vendorsError = ref(null);

const risksData = ref(null);
const risksLoading = ref(false);
const risksError = ref(null);

// Pagination state
const currentPage = ref(1);
const totalPages = ref(1);
const pageSize = 20;


// Heatmap data
const impactLevels = [5, 4, 3, 2, 1];
const likelihoodLevels = [1, 2, 3, 4, 5];

// Dropdown toggle functions
const toggleVendorSelect = () => {
  vendorSelectOpen.value = !vendorSelectOpen.value;
  // Close other dropdowns
  moduleSelectOpen.value = false;
  prioritySelectOpen.value = false;
  dateSelectOpen.value = false;
};

const toggleModuleSelect = () => {
  moduleSelectOpen.value = !moduleSelectOpen.value;
  // Close other dropdowns
  vendorSelectOpen.value = false;
  prioritySelectOpen.value = false;
  dateSelectOpen.value = false;
};

const togglePrioritySelect = () => {
  prioritySelectOpen.value = !prioritySelectOpen.value;
  // Close other dropdowns
  vendorSelectOpen.value = false;
  moduleSelectOpen.value = false;
  dateSelectOpen.value = false;
};

const toggleDateSelect = () => {
  dateSelectOpen.value = !dateSelectOpen.value;
  // Close other dropdowns
  vendorSelectOpen.value = false;
  moduleSelectOpen.value = false;
  prioritySelectOpen.value = false;
};

const toggleAiModuleSelect = () => {
  aiModuleSelectOpen.value = !aiModuleSelectOpen.value;
};

 // Option selection functions
 const selectVendorOption = (value) => {
   console.log('=== VENDOR SELECTED ===');
   console.log('Selected vendor value:', value);
   console.log('Selected vendor value type:', typeof value);
   console.log('filters.vendor before:', filters.value.vendor);
   
   const selectedVendor = vendorOptions.value.find(v => v.value === value);
   console.log('Selected vendor details:', selectedVendor);
   console.log('All vendor options:', vendorOptions.value);
   
   // Update the filter
   filters.value.vendor = value;
   console.log('filters.vendor after:', filters.value.vendor);
   console.log('All filters after update:', filters.value);
   
   // Check riskFilters that will be sent
   setTimeout(() => {
     console.log('riskFilters that will be sent:', riskFilters.value);
   }, 100);
   
   // Close the dropdown
   vendorSelectOpen.value = false;
   console.log('Dropdown closed');
 };

const selectModuleOption = (value) => {
  filters.value.module = value;
  moduleSelectOpen.value = false;
};

const selectPriorityOption = (value) => {
  filters.value.priority = value;
  prioritySelectOpen.value = false;
};

const selectDateOption = (value) => {
  filters.value.date = value;
  dateSelectOpen.value = false;
};

const selectAiModuleOption = (value) => {
  selectedAiModule.value = value;
  aiModuleSelectOpen.value = false;
};

// Helper function to get vendor display name
const getVendorDisplayName = (vendorId) => {
  if (!vendorId || !vendorsData.value) return 'All Vendors';
  
  const vendor = vendorsData.value.find(v => 
    (v.id && v.id.toString() === vendorId) || 
    (v.vendor_id && v.vendor_id.toString() === vendorId)
  );
  return vendor ? (vendor.company_name || vendor.legal_name || `Vendor ${vendor.id || vendor.vendor_id}`) : 'All Vendors';
};

// Click outside handler
const handleClickOutside = (event) => {
  if (vendorSelectRef.value && !vendorSelectRef.value.contains(event.target)) {
    vendorSelectOpen.value = false;
  }
  if (moduleSelectRef.value && !moduleSelectRef.value.contains(event.target)) {
    moduleSelectOpen.value = false;
  }
  if (prioritySelectRef.value && !prioritySelectRef.value.contains(event.target)) {
    prioritySelectOpen.value = false;
  }
  if (dateSelectRef.value && !dateSelectRef.value.contains(event.target)) {
    dateSelectOpen.value = false;
  }
  if (aiModuleSelectRef.value && !aiModuleSelectRef.value.contains(event.target)) {
    aiModuleSelectOpen.value = false;
  }
};

onMounted(async () => {
  await loggingService.logPageView('Vendor', 'Vendor Risk Scoring');
  document.addEventListener('click', handleClickOutside);
  // Load initial data
  fetchDashboard();
  fetchModules();
  fetchVendors();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

// Computed filter options
const vendorOptions = computed(() => {
  if (!vendorsData.value) {
    console.log('=== VENDOR OPTIONS COMPUTE ===');
    console.log('vendorsData.value is null/undefined');
    return [{ value: "", label: "All Vendors" }];
  }
  
  console.log('=== BUILDING VENDOR OPTIONS ===');
  console.log('vendorsData.value:', vendorsData.value);
  
  const vendorList = vendorsData.value.map((vendor, index) => {
    console.log(`Vendor ${index}:`, {
      raw: vendor,
      id: vendor.id,
      vendor_id: vendor.vendor_id,
      id_type: typeof vendor.id,
      vendor_id_type: typeof vendor.vendor_id
    });
    
    const vendorId = vendor.id ? vendor.id.toString() : vendor.vendor_id?.toString() || '';
    const vendorLabel = vendor.company_name || vendor.legal_name || `Vendor ${vendor.id || vendor.vendor_id}`;
    
    console.log(`  -> Mapped to: value="${vendorId}" (type: ${typeof vendorId}), label="${vendorLabel}"`);
    
    return {
      value: vendorId,
      label: vendorLabel
    };
  });

  console.log('=== VENDOR OPTIONS COMPUTED ===');
  console.log('Total vendors:', vendorList.length);
  console.log('Final vendor options:', vendorList);
  
  // Add "All" option at the beginning
  return [
    { value: "", label: "All Vendors" },
    ...vendorList
  ];
});

const moduleOptions = computed(() => [
  { value: "All", label: "All Modules" },
  ...(modulesData.value && modulesData.value.map(module => ({
    value: module.name,
    label: module.name
  })) || [])
]);

const aiModuleOptions = computed(() => {
  return modulesData.value && modulesData.value.map(module => ({
    value: module.name,
    label: module.name,
    badge: module.description
  })) || [];
});

const priorityOptions = computed(() => [
  { value: "All", label: "All Priorities" },
  { value: "Critical", label: "Critical" },
  { value: "High", label: "High" },
  { value: "Medium", label: "Medium" },
  { value: "Low", label: "Low" }
]);

const dateOptions = computed(() => [
  { value: "This Month", label: "This Month" },
  { value: "Last Month", label: "Last Month" },
  { value: "Last 3 Months", label: "Last 3 Months" },
  { value: "Last 6 Months", label: "Last 6 Months" }
]);

   // Filter risks based on current filters
   const riskFilters = computed(() => {
     // Ensure vendor_id is sent as string if it exists and is not empty
     let vendorId = undefined;
     if (filters.value.vendor) {
       const trimmed = String(filters.value.vendor).trim();
       vendorId = trimmed.length > 0 ? trimmed : undefined;
     }
     
     const filterObj = {
       vendor_id: vendorId,
       module: filters.value.module !== "All" ? filters.value.module : undefined,
       priority: filters.value.priority !== "All" ? filters.value.priority : undefined,
       search: searchTerm.value && searchTerm.value.trim() ? searchTerm.value.trim() : undefined,
       // Note: date filters are not supported by the API yet
       // They can be added to the backend if needed
     };
     console.log('Risk filters changed:', filterObj);
     console.log('Search term value:', searchTerm.value);
     console.log('Selected vendor ID:', filters.value.vendor, '-> converted to:', vendorId);
     return filterObj;
   });

// Sort risks by Risk ID in ascending order
const sortedRisks = computed(() => {
  const risks = risksData.value && risksData.value.results || [];
  return [...risks].sort((a, b) => {
    // Extract numeric part from Risk ID (e.g., "R-1000" -> 1000)
    const aNum = parseInt(a.id.split('-')[1]) || 0;
    const bNum = parseInt(b.id.split('-')[1]) || 0;
    return aNum - bNum;
  });
});

// Data fetching functions
const fetchDashboard = async () => {
  dashboardLoading.value = true;
  try {
    dashboardData.value = await api.getDashboard();
  } catch (error) {
    console.error('Error fetching dashboard:', error);
    dashboardError.value = error;
  } finally {
    dashboardLoading.value = false;
  }
};

const fetchModules = async () => {
  modulesLoading.value = true;
  try {
    modulesData.value = await api.getModules();
  } catch (error) {
    console.error('Error fetching modules:', error);
    modulesError.value = error;
  } finally {
    modulesLoading.value = false;
  }
};

const fetchVendors = async () => {
  vendorsLoading.value = true;
  try {
    vendorsData.value = await api.getVendors();
    console.log('Fetched vendors data:', vendorsData.value);
    console.log('Number of vendors:', vendorsData.value ? vendorsData.value.length : 0);
  } catch (error) {
    console.error('Error fetching vendors:', error);
    vendorsError.value = error;
  } finally {
    vendorsLoading.value = false;
  }
};

   // Function to fetch risks with filters
   const fetchRisks = async (filters, page = 1) => {
     risksLoading.value = true;
     try {
       const filtersWithPage = { ...filters, page };
       console.log('=== FETCHING RISKS FROM FRONTEND ===');
       console.log('Selected vendor ID:', filters.vendor_id);
       console.log('All filters:', filtersWithPage);
       
       const response = await api.getRisks(filtersWithPage);
       risksData.value = response;
       
       // Update pagination state
       currentPage.value = page;
       totalPages.value = Math.ceil(response.count / pageSize);
       
       console.log('Risks fetched - Total count:', response.count);
       console.log('Risks data:', response);
       console.log('Pagination - Current page:', currentPage.value, 'Total pages:', totalPages.value);
     } catch (error) {
       console.error('Error fetching risks:', error);
       risksError.value = error;
     } finally {
       risksLoading.value = false;
     }
   };

// Watch for filter changes and fetch data
watch(riskFilters, (newFilters) => {
  console.log('Filters changed, fetching risks:', newFilters);
  currentPage.value = 1; // Reset to first page when filters change
  fetchRisks(newFilters, 1);
}, { immediate: true });

// Pagination functions
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    fetchRisks(riskFilters.value, page);
  }
};

const goToPreviousPage = () => {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1);
  }
};

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    goToPage(currentPage.value + 1);
  }
};

// Generate page numbers for pagination display
const getPageNumbers = () => {
  const pages = [];
  const current = currentPage.value;
  const total = totalPages.value;
  
  if (total <= 7) {
    // Show all pages if total is 7 or less
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // Always show first page
    pages.push(1);
    
    if (current <= 4) {
      // Show pages 2, 3, 4, 5 and ... before last
      for (let i = 2; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    } else if (current >= total - 3) {
      // Show ... after first, then last 4 pages
      pages.push('...');
      for (let i = total - 4; i <= total; i++) {
        pages.push(i);
      }
    } else {
      // Show ... current-1, current, current+1 ... last
      pages.push('...');
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    }
  }
  
  return pages;
};

// Watch for search term changes
watch(searchTerm, (newValue, oldValue) => {
  console.log('Search term changed from:', oldValue, 'to:', newValue);
});

// Watch for filter changes
watch(filters, (newValue, oldValue) => {
  console.log('Filters changed from:', oldValue, 'to:', newValue);
}, { deep: true });

const resetFilters = () => {
  filters.value = {
    vendor: "", // This will show "All Vendors"
    module: "All",
    priority: "All",
    date: "This Month"
  };
  searchTerm.value = "";
};

const handleSearchInput = (event) => {
  const target = event.target;
  console.log('Search input event:', target.value);
  searchTerm.value = target.value;
};

const handleRiskClick = (riskId) => {
  expandedRisk.value = expandedRisk.value === riskId ? null : riskId;
};

// Heatmap functions
const getCellColor = (likelihood, impact) => {
  const score = Math.round(likelihood * impact * 3 * 1.33);
  if (score >= 76) return "bg-risk-critical";
  if (score >= 56) return "bg-risk-high";
  if (score >= 36) return "bg-risk-medium";
  if (score >= 16) return "bg-risk-low";
  return "bg-risk-none";
};

const getCellCount = (risks, likelihood, impact) => {
  return risks.filter(risk => risk.likelihood === likelihood && risk.impact === impact).length;
};

// AI Risk Generation functions
const handleGenerateRisks = async () => {
  if (!selectedAiModule.value) {
    showToast({
      title: "Error",
      description: "Please select a module to generate risks for.",
      variant: "destructive",
    });
    return;
  }

  isGenerating.value = true;
  try {
    const result = await api.generateLlamaRisks(selectedAiModule.value);
    
    // Set the results and show the results modal
    generationResults.value = result;
    resultsModalOpen.value = true;
    aiModalOpen.value = false;
    selectedAiModule.value = "";
    
    // Refresh the risks data
    fetchRisks(riskFilters.value, currentPage.value);
  } catch (error) {
    console.error("Error generating Llama 2 risks:", error);
    
    // Extract error message from the response
    let errorMessage = "Failed to generate Llama 2 risks. Please try again.";
    if (error && error.response && error.response.data && error.response.data.error) {
      errorMessage = error.response.data.error;
    } else if (error && error.message) {
      errorMessage = error.message;
    }
    
    showToast({
      title: "Error",
      description: errorMessage,
      variant: "destructive",
    });
  } finally {
    isGenerating.value = false;
  }
};

const handleOpenAiModal = () => {
  console.log('Opening AI modal...');
  aiModalOpen.value = true;
  console.log('aiModalOpen value:', aiModalOpen.value);
};

const handleAiModalOpenChange = (newOpen) => {
  console.log('Changing AI modal open state to:', newOpen);
  aiModalOpen.value = newOpen;
  if (!newOpen) {
    selectedAiModule.value = "";
  }
};

const parseMitigations = (mitigations) => {
  if (!mitigations) return [];
  
  // If it's already an array, return it
  if (Array.isArray(mitigations)) return mitigations;
  
  // If it's a string, try to parse it as JSON
  if (typeof mitigations === 'string') {
    try {
      const parsed = JSON.parse(mitigations);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      // If it's not valid JSON, split by newlines and clean up
      return mitigations
        .split(/[\n\r]+/)
        .map(m => m.trim())
        .filter(m => m && m !== '[' && m !== ']' && m !== '"');
    }
  }
  
  return [];
};

const getPriorityIcon = (priority) => {
  switch (priority) {
    case 'Critical':
      return AlertTriangle;
    case 'High':
      return AlertTriangle;
    case 'Medium':
      return Info;
    case 'Low':
      return CheckCircle;
    default:
      return Info;
  }
};

</script>

<style scoped>
/* @apply directives are Tailwind CSS utilities - lint warnings can be ignored */
.toast {
  @apply fixed top-4 right-4 z-50 flex w-full max-w-sm items-center justify-between rounded-lg border bg-background p-4 shadow-lg;
}

.toast-title {
  @apply text-sm font-semibold;
}

.toast-description {
  @apply text-sm text-muted-foreground;
}

.toast-action {
  @apply ml-4;
}

.toast-close {
  @apply ml-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2;
}

.toaster {
  position: fixed;
  top: 0;
  z-index: 100;
  display: flex;
  max-height: 100vh;
  width: 100%;
  flex-direction: column-reverse;
  padding: 1rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  z-index: 100000;
  background: white;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 100%;
  max-width: 32rem;
  max-height: 90vh;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  z-index: 10;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
}

.close-button:hover {
  background: #f3f4f6;
  color: #374151;
}

/* Modal Header Styles */
.modal-header {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #f3f4f6;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.modal-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #a855f7;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 0.25rem;
}

.modal-description {
  font-size: 0.875rem;
  opacity: 0.9;
  line-height: 1.4;
  margin: 0;
}

/* Modal Body Styles */
.modal-body {
  padding: 1.5rem;
  background: #fafafa;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

/* Select Dropdown Styles */
.select-wrapper {
  position: relative;
}

.select-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.75rem 1rem;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.select-button:hover {
  border-color: #9ca3af;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.select-button:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.select-text {
  color: #374151;
  font-weight: 500;
}

.select-placeholder {
  color: #9ca3af;
}

.select-icon {
  width: 1rem;
  height: 1rem;
  color: #6b7280;
  transition: transform 0.2s ease;
}

.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 50;
  margin-top: 0.25rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.select-options {
  max-height: 12rem;
  overflow-y: auto;
}

.select-option {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.select-option:hover {
  background: #f9fafb;
}

.option-check {
  width: 1rem;
  height: 1rem;
  margin-right: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.check-icon {
  width: 0.875rem;
  height: 0.875rem;
  color: #10b981;
}

.option-text {
  font-size: 0.875rem;
  color: #374151;
}

/* Selected Module Info */
.selected-module-info {
  background: linear-gradient(135deg, #e0f2fe 0%, #f3e5f5 100%);
  border: 1px solid #b3e5fc;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.info-header {
  font-size: 0.875rem;
  color: #0d47a1;
  margin-bottom: 0.5rem;
}

.info-description {
  font-size: 0.8125rem;
  color: #37474f;
  line-height: 1.4;
  margin: 0.5rem 0;
}

.info-note {
  font-size: 0.75rem;
  color: #f57c00;
  background: rgba(255, 193, 7, 0.1);
  padding: 0.5rem;
  border-radius: 4px;
  border-left: 3px solid #ffc107;
  margin-top: 0.75rem;
}

/* Modal Footer */
.modal-footer {
  padding: 1rem 1.5rem 1.5rem 1.5rem;
  background: white;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* Button Styles */
.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  width: 1rem;
  height: 1rem;
}

/* Entity Risk Generation Styles */
.entity-risk-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.entity-risk-container {
  padding: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 20px;
}

.entity-dropdowns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.dropdown-group {
  display: flex;
  flex-direction: column;
}

.dropdown-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.entity-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  color: #111827;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.entity-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.entity-select:disabled {
  background: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
}

.generate-button-group {
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.generate-entity-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.generate-entity-btn:hover:not(:disabled) {
  background: #2563eb;
}

.generate-entity-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.entity-results {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.results-header {
  margin-bottom: 16px;
}

.results-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.results-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-tag {
  background: #f3f4f6;
  color: #374151;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.entity-risks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.entity-risk-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.entity-risk-card.priority-critical {
  border-left: 4px solid #dc2626;
}

.entity-risk-card.priority-high {
  border-left: 4px solid #ea580c;
}

.entity-risk-card.priority-medium {
  border-left: 4px solid #d97706;
}

.entity-risk-card.priority-low {
  border-left: 4px solid #65a30d;
}

.risk-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.risk-card-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  flex: 1;
  margin-right: 12px;
}

.risk-badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.priority-badge, .score-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.priority-badge.priority-critical {
  background: #fecaca;
  color: #991b1b;
}

.priority-badge.priority-high {
  background: #fed7aa;
  color: #9a3412;
}

.priority-badge.priority-medium {
  background: #fef3c7;
  color: #92400e;
}

.priority-badge.priority-low {
  background: #dcfce7;
  color: #166534;
}

.score-badge {
  background: #f3f4f6;
  color: #374151;
}

.risk-metrics {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 4px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.metric-label {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-weight: 600;
  color: #111827;
  font-size: 12px;
}

.risk-description {
  margin-bottom: 12px;
  color: #374151;
  font-size: 13px;
  line-height: 1.4;
}

.risk-explanation {
  padding: 8px;
  background: #eff6ff;
  border-radius: 4px;
  border-left: 3px solid #3b82f6;
  font-size: 12px;
  color: #1e40af;
  line-height: 1.4;
}

.no-tables-message {
  margin-top: 8px;
}

.no-tables-message p {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 6px;
  color: #92400e;
  font-size: 13px;
  line-height: 1.4;
}

/* Dropdown positioning fixes */
.filter-dropdowns {
  position: relative;
  z-index: 1;
}

.filter-dropdowns .relative {
  position: relative;
  z-index: 1;
}

.filter-dropdowns .relative .absolute {
  position: absolute;
  z-index: 99999;
  top: 100%;
  left: 0;
  right: 0;
}

/* Ensure dropdowns don't get clipped */
.filters-top-section {
  overflow: visible;
}

.filters-container {
  overflow: visible;
}

/* Additional dropdown styling */
.absolute.z-\[99999\] {
  z-index: 99999 !important;
}

.absolute.z-\[99999\] .max-h-96 {
  background: white;
  border: 1px solid #e5e7eb;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

</style>
