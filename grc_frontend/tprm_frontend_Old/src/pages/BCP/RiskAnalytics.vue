<template>
  <div>
    
    <!-- Full-Screen Heatmap View -->
    <div v-if="isFullScreenHeatmap" class="fullscreen-heatmap-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <!-- Use existing header layout -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="text-2xl font-bold text-gray-900">TPRM – Risk Dashboard</h1>
          <p class="text-gray-600">Analyze and manage third-party risk assessments with AI-powered insights</p>
        </div>
        <div class="header-actions">
          <button 
            class="back-to-table-button"
            @click="backToTableView"
          >
            <ChevronLeft class="h-4 w-4" />
            Back to Table
          </button>
      </div>
    </div>
    
      <!-- Full-Screen Heatmap Content -->
      <div class="fullscreen-heatmap-content">
        <div v-if="dashboardLoading" class="flex items-center justify-center py-16">
          <RefreshCw class="h-8 w-8 animate-spin mr-3" />
          <span class="text-lg">Loading heatmap...</span>
    </div>
    
        <!-- Full-Screen Risk Heatmap -->
        <div v-else class="fullscreen-heatmap-wrapper">
          <!-- How to Read the Heatmap Section -->
          <div class="fullscreen-heatmap-instructions">
            <h3 class="text-lg font-semibold mb-3 text-foreground">How to Read the Risk Heatmap</h3>
            <div class="text-sm text-muted-foreground space-y-2">
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

          <!-- Full-Screen Risk Heatmap Grid -->
          <div class="fullscreen-heatmap-grid">
            <!-- Title and axis labels -->
            <div class="fullscreen-heatmap-title-section">
              <div class="text-lg font-medium text-muted-foreground">Risk Score Matrix</div>
              <div class="text-sm text-muted-foreground mt-1">Impact (→) vs Likelihood (↑)</div>
            </div>
            
            <!-- Main heatmap grid -->
            <div class="fullscreen-heatmap-grid-container">
              <!-- Top header with Impact levels -->
              <div class="fullscreen-heatmap-header">
                <div class="fullscreen-heatmap-corner"></div>
                <div class="fullscreen-heatmap-impact-header">
                  <div class="fullscreen-heatmap-impact-label">Impact →</div>
                  <div class="fullscreen-heatmap-impact-values">
                    <div v-for="impact in [1, 2, 3, 4, 5]" :key="`impact-${impact}`" class="fullscreen-heatmap-header-cell">
                      {{ impact }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Likelihood levels and risk cells -->
              <div class="fullscreen-heatmap-body">
                <div class="fullscreen-heatmap-likelihood-sidebar">
                  <div class="fullscreen-heatmap-likelihood-label">
                    <div class="fullscreen-likelihood-text">Likelihood</div>
                    <div class="fullscreen-likelihood-arrow">↑</div>
                  </div>
                  <div class="fullscreen-heatmap-likelihood-values">
                    <div v-for="likelihood in [5, 4, 3, 2, 1]" :key="`likelihood-${likelihood}`" class="fullscreen-heatmap-likelihood-cell">
                      {{ likelihood }}
                    </div>
                  </div>
                </div>
                
                <!-- Risk matrix cells -->
                <div class="fullscreen-heatmap-matrix">
                  <div v-for="likelihood in [5, 4, 3, 2, 1]" :key="`row-${likelihood}`" class="fullscreen-heatmap-row">
                    <div
                      v-for="impact in [1, 2, 3, 4, 5]"
                      :key="`cell-${likelihood}-${impact}`"
                      :class="`fullscreen-heatmap-cell ${getCellColor(likelihood, impact)}`"
                      :title="getCellCount(dashboardData?.recent_risks || [], likelihood, impact) > 0 ? `${getCellCount(dashboardData?.recent_risks || [], likelihood, impact)} risk(s) - Score: ${likelihood * impact * 3 * 1.33}` : `Risk score: ${Math.round(likelihood * impact * 3 * 1.33)}`"
                    >
                      <div class="fullscreen-cell-content">
                        <div class="fullscreen-cell-score">{{ Math.round(likelihood * impact * 3 * 1.33) }}</div>
                        <div v-if="getCellCount(dashboardData?.recent_risks || [], likelihood, impact) > 0" class="fullscreen-cell-count">
                          ({{ getCellCount(dashboardData?.recent_risks || [], likelihood, impact) }})
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Full-Screen Legend -->
          <div class="fullscreen-heatmap-legend">
            <div class="fullscreen-legend-title">Risk Severity Legend</div>
            <div class="fullscreen-legend-items">
              <div class="fullscreen-legend-item">
                <div class="fullscreen-legend-color bg-risk-none"></div>
                <div class="fullscreen-legend-text">
                  <span class="fullscreen-legend-label">Minimal</span>
                  <span class="fullscreen-legend-range">(5-15)</span>
                </div>
              </div>
              <div class="fullscreen-legend-item">
                <div class="fullscreen-legend-color bg-risk-low"></div>
                <div class="fullscreen-legend-text">
                  <span class="fullscreen-legend-label">Low</span>
                  <span class="fullscreen-legend-range">(16-35)</span>
                </div>
              </div>
              <div class="fullscreen-legend-item">
                <div class="fullscreen-legend-color bg-risk-medium"></div>
                <div class="fullscreen-legend-text">
                  <span class="fullscreen-legend-label">Moderate</span>
                  <span class="fullscreen-legend-range">(36-55)</span>
                </div>
              </div>
              <div class="fullscreen-legend-item">
                <div class="fullscreen-legend-color bg-risk-high"></div>
                <div class="fullscreen-legend-text">
                  <span class="fullscreen-legend-label">High</span>
                  <span class="fullscreen-legend-range">(56-75)</span>
                </div>
              </div>
              <div class="fullscreen-legend-item">
                <div class="fullscreen-legend-color bg-risk-critical"></div>
                <div class="fullscreen-legend-text">
                  <span class="fullscreen-legend-label">Critical</span>
                  <span class="fullscreen-legend-range">(76-100)</span>
                </div>
              </div>
            </div>
            <div class="fullscreen-legend-note">
              <p class="text-sm text-muted-foreground">
                <strong>Score Formula:</strong> Likelihood × Impact × Exposure × 1.33
              </p>
              <p class="text-sm text-muted-foreground mt-1">
                Hover over cells to see risk counts and detailed scores
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Application Container (Table View) -->
    <div v-else class="risk-app-container">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="text-2xl font-bold text-gray-900">TPRM – Risk Dashboard</h1>
          <p class="text-gray-600">Analyze and manage third-party risk assessments with AI-powered insights</p>
        </div>
      </div>

      <!-- Filters Section - Separate Layout -->
      <div class="filters-top-section">
      <div class="filters-container">
        <div class="filter-row">
          <!-- Filter dropdowns -->
          <div class="filter-dropdowns">
            <!-- Note: Risk Type and Date filters are UI-only for now -->
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
              
              <div v-if="moduleSelectOpen" class="absolute z-[9999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md">
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
            <div class="relative" ref="riskTypeSelectRef">
              <button
                type="button"
                class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                @click="toggleRiskTypeSelect"
              >
                <span v-if="filters.riskType" class="line-clamp-1">{{ filters.riskType }}</span>
                <span v-else class="text-muted-foreground">Risk Type</span>
                <ChevronDown class="h-4 w-4 opacity-50" />
              </button>
              
              <div v-if="riskTypeSelectOpen" class="absolute z-[9999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md">
                  <div class="p-1">
                    <div 
                      v-for="option in riskTypeOptions" 
                      :key="option.value"
                      class="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                      @click="selectRiskTypeOption(option.value)"
                    >
                      <span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                        <Check v-if="filters.riskType === option.value" class="h-4 w-4" />
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
              
              <div v-if="prioritySelectOpen" class="absolute z-[9999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md">
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
              
              <div v-if="dateSelectOpen" class="absolute z-[9999] mt-1 w-full">
                <div class="max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md">
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
              @click="toggleHeatmapView"
            >
              <Shield class="h-4 w-4" />
              Risk Heatmap
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
                        <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 w-20 text-center">Type</th>
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
                          <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 text-center">
                            <span class="text-sm font-medium">{{ risk.risk_type || 'Current' }}</span>
                          </td>
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
                          <td colspan="7" class="p-0">
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
                                  <p class="text-sm font-medium text-muted-foreground">Risk Type</p>
                                  <p class="font-medium">{{ risk.risk_type || 'Current' }}</p>
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
                                    v-for="(mitigation, index) in risk.suggested_mitigations" 
                                    :key="index" 
                                    class="text-sm flex items-start gap-2"
                                  >
                                    <span class="text-primary">•</span>
                                    {{ mitigation }}
                                  </li>
                                </ul>
                              </div>

                              <div class="flex gap-2 pt-4 border-t">
                                <button class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 bg-primary text-primary-foreground hover:bg-primary/90 h-9 rounded-md px-3">Assign Owner</button>
                                <button class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3">Create Task</button>
                                <button class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3">Acknowledge</button>
                                <button class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3">Mark Mitigated</button>
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
                    Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, risksData?.count || 0) }} of {{ risksData?.count || 0 }} results
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
                          @click="goToPage(page as number)"
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
                            :title="getCellCount(dashboardData?.recent_risks || [], likelihood, impact) > 0 ? `${getCellCount(dashboardData?.recent_risks || [], likelihood, impact)} risk(s) - Score: ${likelihood * impact * 3 * 1.33}` : `Risk score: ${Math.round(likelihood * impact * 3 * 1.33)}`"
                          >
                            <div class="cell-content">
                              <div class="cell-score">{{ Math.round(likelihood * impact * 3 * 1.33) }}</div>
                              <div v-if="getCellCount(dashboardData?.recent_risks || [], likelihood, impact) > 0" class="cell-count">
                          ({{ getCellCount(dashboardData?.recent_risks || [], likelihood, impact) }})
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
    
    
          </div>
</template>

<script setup lang="ts">
import './RiskAnalytics.css'
import { ref, computed, watch, onMounted, onUnmounted, reactive } from 'vue';
import { Download, RotateCcw, Search, Shield, ChevronDown, Check, RefreshCw, ChevronUp, CheckCircle, AlertTriangle, Info, ChevronLeft, ChevronRight } from "lucide-vue-next";
import { useNotifications } from '@/composables/useNotifications';
import { PopupService } from '@/popup/popupService';
import loggingService from '@/services/loggingService';

// ===== INLINED API SERVICE =====
const API_BASE_URL = 'https://grc-tprm.vardaands.com/api/tprm';

interface Risk {
  id: string;
  title: string;
  description: string;
  likelihood: number;
  impact: number;
  exposure_rating: number;
  score: number;
  priority: "Critical" | "High" | "Medium" | "Low";
  ai_explanation: string;
  suggested_mitigations: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

interface Module {
  module_id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

interface DashboardData {
  statistics: {
    total_risks: number;
    critical_risks: number;
    high_risks: number;
    medium_risks: number;
    low_risks: number;
    average_score: number;
  };
  recent_risks: Risk[];
  modules: Module[];
}

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    
    // Handle 403 Forbidden - permission denied
    if (response.status === 403) {
      try {
        const errorData = JSON.parse(errorText);
        const errorMessage = errorData.error || errorData.message || 'You do not have permission to access this resource.';
        const errorCode = errorData.code || '403';
        
        // Store error info in sessionStorage
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: errorMessage,
          code: errorCode,
          timestamp: new Date().toISOString(),
          path: window.location.pathname
        }));
        
        // Redirect to access denied page
        window.location.href = '/access-denied';
      } catch (e) {
        // If JSON parsing fails, just redirect with generic message
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: 'You do not have permission to access this resource.',
          code: '403',
          timestamp: new Date().toISOString(),
          path: window.location.pathname
        }));
        window.location.href = '/access-denied';
      }
    }
    
    throw new ApiError(`API Error: ${response.status} - ${errorText}`, response.status);
  }
  
  // Handle empty responses
  const text = await response.text();
  if (!text) {
    return {} as T;
  }
  
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new ApiError(`Failed to parse JSON response: ${error}`);
  }
}

// Helper to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

const api = {
  // Get dashboard data
  async getDashboard(): Promise<DashboardData> {
    const response = await fetch(`${API_BASE_URL}/risk-analysis/dashboard/`, {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<DashboardData>(response);
  },

  // Get all risks with optional filters
  async getRisks(params?: {
    module?: string;
    priority?: string;
    status?: string;
    search?: string;
    min_score?: number;
    max_score?: number;
    page?: number;
  }): Promise<{ results: Risk[]; count: number; next?: string; previous?: string }> {
    const url = new URL(`${API_BASE_URL}/risk-analysis/risks/`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, value.toString());
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    const data = await handleResponse<{ results: Risk[]; count: number; next?: string; previous?: string } | Risk[]>(response);
    console.log('Risks API response:', data); // Debug log
    // Handle both paginated and non-paginated responses
    if (data && typeof data === 'object' && 'results' in data) {
      return data as { results: Risk[]; count: number; next?: string; previous?: string };
    } else {
      const risksArray = data as Risk[];
      return { results: risksArray, count: risksArray.length };
    }
  },

  // Get modules
  async getModules(): Promise<Module[]> {
    const response = await fetch(`${API_BASE_URL}/risk-analysis/modules/`, {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    const data = await handleResponse<{ results: Module[]; count: number } | Module[]>(response);
    console.log('Modules API response:', data); // Debug log
    // Handle both paginated and non-paginated responses
    if (data && typeof data === 'object' && 'results' in data) {
      return (data as { results: Module[]; count: number }).results;
    }
    return data as Module[];
  },

};


// ===== MAIN COMPONENT LOGIC =====

const { showSuccess, showError, showWarning, showInfo } = useNotifications();

const filters = ref({
  module: "All",
  riskType: "All",
  priority: "All",
  date: "This Month"
});

const searchTerm = ref("");
const expandedRisk = ref<string | null>(null);

// Full-screen heatmap view state
const isFullScreenHeatmap = ref(false);

// Sidebar state detection
const isSidebarCollapsed = ref(false);

// Function to detect sidebar state
const detectSidebarState = () => {
  const sidebar = document.querySelector('[data-sidebar]') || document.querySelector('.sidebar') || document.querySelector('#sidebar');
  if (sidebar) {
    const rect = sidebar.getBoundingClientRect();
    isSidebarCollapsed.value = rect.width < 200; // Consider collapsed if width < 200px
  }
};

// Function to detect header height
const detectHeaderHeight = () => {
  const header = document.querySelector('[data-header]') || document.querySelector('.app-header') || document.querySelector('#header') || document.querySelector('.vendor-guard-header');
  if (header) {
    const rect = header.getBoundingClientRect();
    document.documentElement.style.setProperty('--header-height', `${rect.height}px`);
  } else {
    // Fallback to default height
    document.documentElement.style.setProperty('--header-height', '60px');
  }
};

// Dropdown state management for inlined SimpleSelect components
const moduleSelectOpen = ref(false);
const riskTypeSelectOpen = ref(false);
const prioritySelectOpen = ref(false);
const dateSelectOpen = ref(false);

const moduleSelectRef = ref<HTMLElement>();
const riskTypeSelectRef = ref<HTMLElement>();
const prioritySelectRef = ref<HTMLElement>();
const dateSelectRef = ref<HTMLElement>();


// Data state
const dashboardData = ref<DashboardData | null>(null);
const dashboardLoading = ref(false);
const dashboardError = ref<any>(null);

const modulesData = ref<Module[] | null>(null);
const modulesLoading = ref(false);
const modulesError = ref<any>(null);

const risksData = ref<any>(null);
const risksLoading = ref(false);
const risksError = ref<any>(null);

// Pagination state
const currentPage = ref(1);
const totalPages = ref(1);
const pageSize = 20;


// Heatmap data
const impactLevels = [5, 4, 3, 2, 1];
const likelihoodLevels = [1, 2, 3, 4, 5];

// Dropdown toggle functions
const toggleModuleSelect = () => {
  moduleSelectOpen.value = !moduleSelectOpen.value;
  // Close other dropdowns
  riskTypeSelectOpen.value = false;
  prioritySelectOpen.value = false;
  dateSelectOpen.value = false;
};

const toggleRiskTypeSelect = () => {
  riskTypeSelectOpen.value = !riskTypeSelectOpen.value;
  // Close other dropdowns
  moduleSelectOpen.value = false;
  prioritySelectOpen.value = false;
  dateSelectOpen.value = false;
};

const togglePrioritySelect = () => {
  prioritySelectOpen.value = !prioritySelectOpen.value;
  // Close other dropdowns
  moduleSelectOpen.value = false;
  riskTypeSelectOpen.value = false;
  dateSelectOpen.value = false;
};

const toggleDateSelect = () => {
  dateSelectOpen.value = !dateSelectOpen.value;
  // Close other dropdowns
  moduleSelectOpen.value = false;
  riskTypeSelectOpen.value = false;
  prioritySelectOpen.value = false;
};


// Option selection functions
const selectModuleOption = (value: string) => {
  filters.value.module = value;
  moduleSelectOpen.value = false;
};

const selectRiskTypeOption = (value: string) => {
  filters.value.riskType = value;
  riskTypeSelectOpen.value = false;
};

const selectPriorityOption = (value: string) => {
  filters.value.priority = value;
  prioritySelectOpen.value = false;
};

const selectDateOption = (value: string) => {
  filters.value.date = value;
  dateSelectOpen.value = false;
};


// Click outside handler
const handleClickOutside = (event: Event) => {
  if (moduleSelectRef.value && !moduleSelectRef.value.contains(event.target as Node)) {
    moduleSelectOpen.value = false;
  }
  if (riskTypeSelectRef.value && !riskTypeSelectRef.value.contains(event.target as Node)) {
    riskTypeSelectOpen.value = false;
  }
  if (prioritySelectRef.value && !prioritySelectRef.value.contains(event.target as Node)) {
    prioritySelectOpen.value = false;
  }
  if (dateSelectRef.value && !dateSelectRef.value.contains(event.target as Node)) {
    dateSelectOpen.value = false;
  }
};

onMounted(async () => {
  await loggingService.logPageView('BCP', 'Risk Analytics');
  document.addEventListener('click', handleClickOutside);
  // Load initial data
  fetchDashboard();
  fetchModules();
  // Detect initial sidebar and header state
  detectSidebarState();
  detectHeaderHeight();
  
  // Watch for sidebar changes
  const sidebar = document.querySelector('[data-sidebar]') || document.querySelector('.sidebar') || document.querySelector('#sidebar');
  if (sidebar) {
    const resizeObserver = new ResizeObserver(() => {
      detectSidebarState();
    });
    resizeObserver.observe(sidebar);
    
    // Store observer for cleanup
    (window as any).sidebarResizeObserver = resizeObserver;
  }
  
  // Watch for header changes
  const header = document.querySelector('[data-header]') || document.querySelector('.app-header') || document.querySelector('#header') || document.querySelector('.vendor-guard-header');
  if (header) {
    const headerResizeObserver = new ResizeObserver(() => {
      detectHeaderHeight();
    });
    headerResizeObserver.observe(header);
    
    // Store observer for cleanup
    (window as any).headerResizeObserver = headerResizeObserver;
  }
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  // Cleanup ResizeObservers
  if ((window as any).sidebarResizeObserver) {
    (window as any).sidebarResizeObserver.disconnect();
    delete (window as any).sidebarResizeObserver;
  }
  if ((window as any).headerResizeObserver) {
    (window as any).headerResizeObserver.disconnect();
    delete (window as any).headerResizeObserver;
  }
});

// Computed filter options
const moduleOptions = computed(() => [
  { value: "All", label: "All Modules" },
  ...(modulesData.value?.map(module => ({
    value: module.name,
    label: module.name
  })) || [])
]);


const riskTypeOptions = computed(() => [
  { value: "All", label: "All Types" },
  { value: "Inherent", label: "Inherent" },
  { value: "Emerging", label: "Emerging" },
  { value: "Current", label: "Current" },
  { value: "Residual", label: "Residual" },
  { value: "Accepted", label: "Accepted" }
]);

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
  const filterObj = {
    module: filters.value.module !== "All" ? filters.value.module : undefined,
    priority: filters.value.priority !== "All" ? filters.value.priority : undefined,
    risk_type: filters.value.riskType !== "All" ? filters.value.riskType : undefined,
    search: searchTerm.value || undefined,
    // Note: date filters are not supported by the API yet
    // They can be added to the backend if needed
  };
  console.log('Risk filters changed:', filterObj);
  console.log('Search term value:', searchTerm.value);
  return filterObj;
});

// Sort risks by Risk ID in ascending order
const sortedRisks = computed(() => {
  const risks = risksData.value?.results || [];
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

// Function to fetch risks with filters
const fetchRisks = async (filters: any, page: number = 1) => {
  risksLoading.value = true;
  try {
    const filtersWithPage = { ...filters, page };
    console.log('Fetching risks with filters:', filtersWithPage);
    const response = await api.getRisks(filtersWithPage);
    risksData.value = response;
    
    // Update pagination state
    currentPage.value = page;
    totalPages.value = Math.ceil(response.count / pageSize);
    
    console.log('Risks fetched:', response);
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
const goToPage = (page: number) => {
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
const getPageNumbers = (): (number | string)[] => {
  const pages: (number | string)[] = [];
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
    module: "All",
    riskType: "All", 
    priority: "All",
    date: "This Month"
  };
  searchTerm.value = "";
};

const handleSearchInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  console.log('Search input event:', target.value);
  searchTerm.value = target.value;
};

const handleRiskClick = (riskId: string) => {
  expandedRisk.value = expandedRisk.value === riskId ? null : riskId;
};

// Heatmap functions
const getCellColor = (likelihood: number, impact: number) => {
  const score = Math.round(likelihood * impact * 3 * 1.33);
  if (score >= 76) return "bg-risk-critical";
  if (score >= 56) return "bg-risk-high";
  if (score >= 36) return "bg-risk-medium";
  if (score >= 16) return "bg-risk-low";
  return "bg-risk-none";
};

const getCellCount = (risks: Risk[], likelihood: number, impact: number) => {
  return risks.filter(risk => risk.likelihood === likelihood && risk.impact === impact).length;
};


const getPriorityIcon = (priority: string) => {
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

// Toggle between table and full-screen heatmap view
const toggleHeatmapView = () => {
  detectSidebarState(); // Detect sidebar state before switching
  detectHeaderHeight(); // Detect header height before switching
  isFullScreenHeatmap.value = !isFullScreenHeatmap.value;
};

const backToTableView = () => {
  isFullScreenHeatmap.value = false;
};

</script>

