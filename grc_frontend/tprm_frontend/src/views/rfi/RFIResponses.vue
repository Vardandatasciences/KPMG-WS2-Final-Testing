<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">RFI Vendor Responses</h1>
        <p class="text-muted-foreground">
          View and compare responses from vendors across RFIs
        </p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" @click="fetchResponses">
          <RefreshCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }" />
          Refresh
        </Button>
        <Button class="compare-ai-btn" @click="onCompareWithAI" :disabled="selectedCount === 0">
          <Sparkles class="h-4 w-4 mr-2" />
          Compare with AI
          <span v-if="selectedCount > 0" class="ml-2 bg-white/20 px-2 py-0.5 rounded text-sm">{{ selectedCount }}</span>
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <Card class="phase-card">
      <div class="p-6">
        <div class="flex flex-col gap-4">
          <div class="flex flex-wrap items-end gap-3">
            <div class="min-w-[200px]">
              <label class="block text-sm font-medium text-gray-700 mb-1">RFI</label>
              <Select v-model="filters.rfi_id">
                <SelectTrigger class="w-full">
                  <SelectValue placeholder="All RFIs" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All RFIs</SelectItem>
                  <SelectItem v-for="r in rfiList" :key="r.rfi_id" :value="String(r.rfi_id)">
                    {{ r.rfi_number }} – {{ r.rfi_title }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="min-w-[160px]">
              <label class="block text-sm font-medium text-gray-700 mb-1">Evaluation status</label>
              <Select v-model="filters.evaluation_status">
                <SelectTrigger class="w-full">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="SUBMITTED">Submitted</SelectItem>
                  <SelectItem value="UNDER_EVALUATION">Under Evaluation</SelectItem>
                  <SelectItem value="SHORTLISTED">Shortlisted</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="AWARDED">Awarded</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="min-w-[160px]">
              <label class="block text-sm font-medium text-gray-700 mb-1">Submission status</label>
              <Select v-model="filters.submission_status">
                <SelectTrigger class="w-full">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="SUBMITTED">Submitted</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="flex-1 min-w-[200px]">
              <label class="block text-sm font-medium text-gray-700 mb-1">Vendor search</label>
              <Input
                v-model="filters.vendor_search"
                placeholder="Vendor name, company, or email..."
                class="w-full"
              />
            </div>
            <Button variant="secondary" @click="applyFilters">Apply filters</Button>
            <Button variant="outline" @click="clearFilters">Clear</Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- View toggle + content -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex rounded-lg border border-gray-200 p-1 bg-gray-50">
        <button
          type="button"
          :class="[viewMode === 'cards' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900']"
          class="rounded-md px-3 py-2 flex items-center gap-2 text-sm font-medium transition-colors"
          @click="viewMode = 'cards'"
        >
          <LayoutGrid class="h-4 w-4" />
          Cards
        </button>
        <button
          type="button"
          :class="[viewMode === 'table' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900']"
          class="rounded-md px-3 py-2 flex items-center gap-2 text-sm font-medium transition-colors"
          @click="viewMode = 'table'"
        >
          <Table2 class="h-4 w-4" />
          Table
        </button>
      </div>
      <p class="text-sm text-muted-foreground">
        {{ filteredResponses.length }} response{{ filteredResponses.length !== 1 ? 's' : '' }}
      </p>
    </div>

    <!-- Cards view -->
    <div v-if="viewMode === 'cards'" class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="r in filteredResponses"
        :key="r.response_id"
        class="phase-card cursor-pointer transition-all hover:shadow-xl border-l-4"
        :class="[
          { 'ring-2 ring-blue-500 border-l-blue-500': selectedIds.has(r.response_id) },
          getStatusBorderClass(r.evaluation_status)
        ]"
        @click="toggleSelect(r.response_id)"
      >
        <div class="p-6 space-y-4">
          <!-- Header with vendor info and checkbox -->
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 mb-1">
                <div class="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {{ getInitials(r.vendor_name || r.org || 'V') }}
                </div>
                <div class="min-w-0 flex-1">
                  <h3 class="font-bold text-gray-900 truncate text-lg" :title="r.vendor_name || r.org">
                    {{ r.vendor_name || r.org || 'Unknown vendor' }}
                  </h3>
                  <p v-if="r.contact_email" class="text-xs text-muted-foreground truncate mt-0.5">
                    {{ r.contact_email }}
                  </p>
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              :checked="selectedIds.has(r.response_id)"
              class="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              @click.stop
              @change="toggleSelect(r.response_id)"
            />
          </div>

          <!-- RFI Info -->
          <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div class="flex items-center gap-2 mb-1">
              <FileText class="h-4 w-4 text-gray-500" />
              <span class="text-xs font-medium text-gray-600 uppercase tracking-wide">RFI</span>
            </div>
            <p class="font-semibold text-gray-900 text-sm" :title="r.rfi_title">
              {{ r.rfi_title || r.rfi_number || 'Untitled RFI' }}
            </p>
            <p v-if="r.rfi_number && r.rfi_title" class="text-xs text-muted-foreground mt-0.5">
              {{ r.rfi_number }}
            </p>
          </div>

          <!-- Status badges -->
          <div class="flex flex-wrap gap-2">
            <Badge :class="evalStatusClass(r.evaluation_status)" class="px-3 py-1 text-xs font-semibold">
              {{ formatEvalStatus(r.evaluation_status) }}
            </Badge>
            <Badge variant="outline" class="px-3 py-1 text-xs">
              {{ r.submission_status || 'Draft' }}
            </Badge>
          </div>

          <!-- Key metrics grid -->
          <div class="grid grid-cols-2 gap-3 pt-2 border-t border-gray-200">
            <!-- Proposed Value -->
            <div v-if="r.proposed_value != null" class="bg-blue-50 rounded-lg p-3 border border-blue-100">
              <div class="flex items-center gap-1.5 mb-1">
                <DollarSign class="h-3.5 w-3.5 text-blue-600" />
                <span class="text-xs font-medium text-blue-700">Proposed Value</span>
              </div>
              <p class="font-bold text-blue-900 text-lg">{{ formatCurrency(r.proposed_value) }}</p>
            </div>

            <!-- Score -->
            <div v-if="r.overall_score != null || r.weighted_final_score != null || r.technical_score != null || r.commercial_score != null" class="bg-green-50 rounded-lg p-3 border border-green-100">
              <div class="flex items-center gap-1.5 mb-1">
                <Sparkles class="h-3.5 w-3.5 text-green-600" />
                <span class="text-xs font-medium text-green-700">Score</span>
              </div>
              <div class="space-y-1">
                <div v-if="r.overall_score != null || r.weighted_final_score != null" class="flex items-baseline gap-2">
                  <p class="font-bold text-green-900 text-lg">
                    {{ r.overall_score ?? r.weighted_final_score }}
                  </p>
                  <div class="flex-1">
                    <div class="h-2 bg-green-200 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all"
                        :style="{ width: `${Math.min(100, ((parseFloat(r.overall_score ?? r.weighted_final_score ?? 0)) / 100) * 100)}%` }"
                      ></div>
                    </div>
                  </div>
                </div>
                <div v-if="(r.technical_score != null || r.commercial_score != null) && !r.overall_score && !r.weighted_final_score" class="flex gap-2 text-xs">
                  <span v-if="r.technical_score != null" class="text-green-700">Tech: {{ r.technical_score }}</span>
                  <span v-if="r.commercial_score != null" class="text-green-700">Comm: {{ r.commercial_score }}</span>
                </div>
              </div>
            </div>

            <!-- Completion Percentage -->
            <div v-if="r.completion_percentage != null" class="bg-purple-50 rounded-lg p-3 border border-purple-100">
              <div class="flex items-center gap-1.5 mb-1">
                <span class="text-xs font-medium text-purple-700">Completion</span>
              </div>
              <div class="flex items-baseline gap-2">
                <p class="font-bold text-purple-900 text-lg">{{ r.completion_percentage }}%</p>
                <div class="flex-1">
                  <div class="h-2 bg-purple-200 rounded-full overflow-hidden">
                    <div 
                      class="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full transition-all"
                      :style="{ width: `${Math.min(100, parseFloat(r.completion_percentage ?? 0))}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Submission Date -->
            <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
              <div class="flex items-center gap-1.5 mb-1">
                <Calendar class="h-3.5 w-3.5 text-gray-600" />
                <span class="text-xs font-medium text-gray-700">Submitted</span>
              </div>
              <p class="font-semibold text-gray-900 text-sm">
                {{ formatDate(r.submitted_at || r.submission_date || r.created_at) }}
              </p>
            </div>
          </div>

          <!-- Additional scores breakdown -->
          <div v-if="(r.technical_score != null || r.commercial_score != null) && (r.overall_score != null || r.weighted_final_score != null)" class="pt-2 border-t border-gray-200">
            <div class="flex gap-4 text-xs">
              <div v-if="r.technical_score != null" class="flex items-center gap-1">
                <span class="text-muted-foreground">Technical:</span>
                <span class="font-semibold text-gray-900">{{ r.technical_score }}</span>
              </div>
              <div v-if="r.commercial_score != null" class="flex items-center gap-1">
                <span class="text-muted-foreground">Commercial:</span>
                <span class="font-semibold text-gray-900">{{ r.commercial_score }}</span>
              </div>
            </div>
          </div>

          <!-- Additional info if available -->
          <div v-if="r.contact_name || r.contact_phone" class="pt-2 border-t border-gray-200 space-y-1">
            <div v-if="r.contact_name" class="flex items-center gap-2 text-xs text-muted-foreground">
              <Users class="h-3.5 w-3.5" />
              <span>{{ r.contact_name }}</span>
            </div>
            <div v-if="r.contact_phone" class="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{{ r.contact_phone }}</span>
            </div>
          </div>

          <!-- View button -->
          <div class="pt-2 border-t border-gray-200">
            <Button
              variant="outline"
              size="sm"
              class="w-full"
              @click.stop="viewResponse(r.response_id)"
            >
              <Eye class="h-4 w-4 mr-2" />
              View Response
            </Button>
          </div>
        </div>
      </Card>
    </div>

    <!-- Table view -->
    <Card v-if="viewMode === 'table'" class="phase-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-300">
            <tr>
              <th class="text-left py-4 px-4 w-10">
                <input
                  type="checkbox"
                  :checked="selectedCount === filteredResponses.length && filteredResponses.length > 0"
                  :indeterminate.prop="selectedCount > 0 && selectedCount < filteredResponses.length"
                  class="h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="text-left py-4 px-4 font-bold text-gray-800">Vendor</th>
              <th class="text-left py-4 px-4 font-bold text-gray-800">RFI</th>
              <th class="text-left py-4 px-4 font-bold text-gray-800">Status</th>
              <th class="text-right py-4 px-4 font-bold text-gray-800">Proposed Value</th>
              <th class="text-center py-4 px-4 font-bold text-gray-800">Scores</th>
              <th class="text-left py-4 px-4 font-bold text-gray-800">Submitted</th>
              <th class="text-left py-4 px-4 font-bold text-gray-800">Completion</th>
              <th class="text-left py-4 px-4 font-bold text-gray-800">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in filteredResponses"
              :key="r.response_id"
              class="border-b border-gray-200 hover:bg-blue-50/50 transition-colors"
              :class="{ 'bg-blue-50': selectedIds.has(r.response_id) }"
              @click="toggleSelect(r.response_id)"
            >
              <td class="py-4 px-4" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedIds.has(r.response_id)"
                  class="h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
                  @change="toggleSelect(r.response_id)"
                />
              </td>
              <td class="py-4 px-4">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                    {{ getInitials(r.vendor_name || r.org || 'V') }}
                  </div>
                  <div>
                    <div class="font-semibold text-gray-900">{{ r.vendor_name || r.org || '—' }}</div>
                    <div v-if="r.contact_email" class="text-xs text-muted-foreground mt-0.5">{{ r.contact_email }}</div>
                    <div v-if="r.contact_phone" class="text-xs text-muted-foreground">{{ r.contact_phone }}</div>
                  </div>
                </div>
              </td>
              <td class="py-4 px-4">
                <div class="font-semibold text-gray-900">{{ r.rfi_title || r.rfi_number || '—' }}</div>
                <div v-if="r.rfi_number && r.rfi_title" class="text-xs text-muted-foreground mt-0.5">{{ r.rfi_number }}</div>
              </td>
              <td class="py-4 px-4">
                <div class="flex flex-col gap-1.5">
                  <Badge :class="evalStatusClass(r.evaluation_status)" class="w-fit text-xs font-semibold px-2 py-0.5">
                    {{ formatEvalStatus(r.evaluation_status) }}
                  </Badge>
                  <Badge variant="outline" class="w-fit text-xs px-2 py-0.5">
                    {{ r.submission_status || 'Draft' }}
                  </Badge>
                </div>
              </td>
              <td class="py-4 px-4 text-right">
                <div v-if="r.proposed_value != null" class="flex items-center justify-end gap-1">
                  <DollarSign class="h-4 w-4 text-green-600" />
                  <span class="font-bold text-gray-900">{{ formatCurrency(r.proposed_value) }}</span>
                </div>
                <span v-else class="text-muted-foreground">—</span>
              </td>
              <td class="py-4 px-4">
                <div class="space-y-1.5">
                  <div v-if="r.overall_score != null || r.weighted_final_score != null" class="flex items-center justify-center gap-2">
                    <Sparkles class="h-3.5 w-3.5 text-green-600" />
                    <span class="font-bold text-green-700">{{ r.overall_score ?? r.weighted_final_score }}</span>
                    <div class="w-16 h-1.5 bg-green-200 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full"
                        :style="{ width: `${Math.min(100, ((parseFloat(r.overall_score ?? r.weighted_final_score ?? 0)) / 100) * 100)}%` }"
                      ></div>
                    </div>
                  </div>
                  <div v-else-if="r.technical_score != null || r.commercial_score != null" class="flex items-center justify-center gap-3 text-xs">
                    <span v-if="r.technical_score != null" class="text-gray-700">
                      <span class="text-muted-foreground">Tech:</span> <span class="font-semibold">{{ r.technical_score }}</span>
                    </span>
                    <span v-if="r.commercial_score != null" class="text-gray-700">
                      <span class="text-muted-foreground">Comm:</span> <span class="font-semibold">{{ r.commercial_score }}</span>
                    </span>
                  </div>
                  <span v-else class="text-muted-foreground text-center block">—</span>
                </div>
              </td>
              <td class="py-4 px-4">
                <div class="flex items-center gap-1.5">
                  <Calendar class="h-3.5 w-3.5 text-gray-500" />
                  <span class="text-gray-700">{{ formatDate(r.submitted_at || r.submission_date || r.created_at) }}</span>
                </div>
              </td>
              <td class="py-4 px-4">
                <div v-if="r.completion_percentage != null" class="flex items-center gap-2">
                  <div class="flex-1 w-20 h-2 bg-purple-200 rounded-full overflow-hidden">
                    <div 
                      class="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
                      :style="{ width: `${Math.min(100, parseFloat(r.completion_percentage ?? 0))}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-semibold text-purple-700">{{ r.completion_percentage }}%</span>
                </div>
                <span v-else class="text-muted-foreground">—</span>
              </td>
              <td class="py-4 px-4">
                <Button
                  variant="outline"
                  size="sm"
                  @click.stop="viewResponse(r.response_id)"
                >
                  <Eye class="h-4 w-4 mr-1" />
                  View
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Empty state -->
    <Card v-if="filteredResponses.length === 0 && !loading" class="phase-card">
      <div class="p-12 text-center">
        <FileText class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 class="text-lg font-semibold mb-2">No responses found</h3>
        <p class="text-muted-foreground mb-4">
          {{ hasActiveFilters ? 'No responses match your filters. Try adjusting them.' : 'There are no RFI responses yet.' }}
        </p>
        <Button v-if="hasActiveFilters" variant="outline" @click="clearFilters">Clear filters</Button>
      </div>
    </Card>

    <!-- Loading state -->
    <Card v-if="loading" class="phase-card">
      <div class="p-12 text-center">
        <RefreshCw class="h-8 w-8 mx-auto text-muted-foreground mb-4 animate-spin" />
        <p class="text-muted-foreground">Loading responses...</p>
      </div>
    </Card>

    <!-- Response Detail Modal -->
    <div
      v-if="showResponseModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      @click.self="closeResponseModal"
    >
      <Card class="phase-card max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">RFI Response Details</h2>
            <p v-if="selectedResponse" class="text-sm text-muted-foreground mt-1">
              {{ selectedResponse.vendor_name || selectedResponse.org || 'Vendor' }} - {{ selectedResponse.rfi_title || selectedResponse.rfi_number }}
            </p>
          </div>
          <Button variant="outline" size="sm" @click="closeResponseModal">
            <X class="h-5 w-5" />
          </Button>
        </div>

        <div v-if="loadingResponse" class="p-12 text-center">
          <RefreshCw class="h-8 w-8 mx-auto text-muted-foreground mb-4 animate-spin" />
          <p class="text-muted-foreground">Loading response details...</p>
        </div>

        <div v-else-if="selectedResponse" class="overflow-y-auto flex-1 p-6 space-y-6">
          <!-- Vendor Information -->
          <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
              <Users class="h-5 w-5" />
              Vendor Information
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <span class="text-sm font-medium text-gray-600">Vendor Name</span>
                <p class="text-gray-900 font-semibold">{{ selectedResponse.vendor_name || '—' }}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-600">Organization</span>
                <p class="text-gray-900 font-semibold">{{ selectedResponse.org || '—' }}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-600">Contact Email</span>
                <p class="text-gray-900">{{ selectedResponse.contact_email || '—' }}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-600">Contact Phone</span>
                <p class="text-gray-900">{{ selectedResponse.contact_phone || '—' }}</p>
              </div>
              <div v-if="selectedResponse.vendor_id">
                <span class="text-sm font-medium text-gray-600">Vendor ID</span>
                <p class="text-gray-900">{{ selectedResponse.vendor_id }}</p>
              </div>
            </div>
          </div>

          <!-- RFI Information -->
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
              <FileText class="h-5 w-5" />
              RFI Information
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <span class="text-sm font-medium text-gray-600">RFI Title</span>
                <p class="text-gray-900 font-semibold">{{ selectedResponse.rfi_title || '—' }}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-600">RFI Number</span>
                <p class="text-gray-900">{{ selectedResponse.rfi_number || '—' }}</p>
              </div>
              <div v-if="selectedResponse.rfi_id">
                <span class="text-sm font-medium text-gray-600">RFI ID</span>
                <p class="text-gray-900">{{ selectedResponse.rfi_id }}</p>
              </div>
            </div>
          </div>

          <!-- Status & Evaluation -->
          <div class="bg-green-50 rounded-lg p-4 border border-green-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
              <Sparkles class="h-5 w-5" />
              Status & Evaluation
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <span class="text-sm font-medium text-gray-600">Evaluation Status</span>
                <div class="mt-1">
                  <Badge :class="evalStatusClass(selectedResponse.evaluation_status)">
                    {{ formatEvalStatus(selectedResponse.evaluation_status) }}
                  </Badge>
                </div>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-600">Submission Status</span>
                <div class="mt-1">
                  <Badge variant="outline">{{ selectedResponse.submission_status || 'Draft' }}</Badge>
                </div>
              </div>
              <div v-if="selectedResponse.auto_rejected">
                <span class="text-sm font-medium text-gray-600">Auto Rejected</span>
                <p class="text-red-600 font-semibold">Yes</p>
              </div>
              <div v-if="selectedResponse.rejection_reason">
                <span class="text-sm font-medium text-gray-600">Rejection Reason</span>
                <p class="text-gray-900">{{ selectedResponse.rejection_reason }}</p>
              </div>
            </div>
          </div>

          <!-- Scores -->
          <div class="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
              <DollarSign class="h-5 w-5" />
              Scores & Values
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="selectedResponse.proposed_value != null">
                <span class="text-sm font-medium text-gray-600">Proposed Value</span>
                <p class="text-gray-900 font-bold text-lg">{{ formatCurrency(selectedResponse.proposed_value) }}</p>
              </div>
              <div v-if="selectedResponse.overall_score != null">
                <span class="text-sm font-medium text-gray-600">Overall Score</span>
                <p class="text-gray-900 font-bold text-lg">{{ selectedResponse.overall_score }}</p>
              </div>
              <div v-if="selectedResponse.weighted_final_score != null">
                <span class="text-sm font-medium text-gray-600">Weighted Final Score</span>
                <p class="text-gray-900 font-bold text-lg">{{ selectedResponse.weighted_final_score }}</p>
              </div>
              <div v-if="selectedResponse.technical_score != null">
                <span class="text-sm font-medium text-gray-600">Technical Score</span>
                <p class="text-gray-900 font-semibold">{{ selectedResponse.technical_score }}</p>
              </div>
              <div v-if="selectedResponse.commercial_score != null">
                <span class="text-sm font-medium text-gray-600">Commercial Score</span>
                <p class="text-gray-900 font-semibold">{{ selectedResponse.commercial_score }}</p>
              </div>
              <div v-if="selectedResponse.completion_percentage != null">
                <span class="text-sm font-medium text-gray-600">Completion Percentage</span>
                <p class="text-gray-900 font-semibold">{{ selectedResponse.completion_percentage }}%</p>
              </div>
            </div>
          </div>

          <!-- Submission Details -->
          <div class="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
              <Calendar class="h-5 w-5" />
              Submission Details
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="selectedResponse.submitted_at">
                <span class="text-sm font-medium text-gray-600">Submitted At</span>
                <p class="text-gray-900">{{ formatDate(selectedResponse.submitted_at) }}</p>
              </div>
              <div v-if="selectedResponse.submission_date">
                <span class="text-sm font-medium text-gray-600">Submission Date</span>
                <p class="text-gray-900">{{ formatDate(selectedResponse.submission_date) }}</p>
              </div>
              <div v-if="selectedResponse.submitted_by">
                <span class="text-sm font-medium text-gray-600">Submitted By</span>
                <p class="text-gray-900">{{ selectedResponse.submitted_by }}</p>
              </div>
              <div v-if="selectedResponse.submission_source">
                <span class="text-sm font-medium text-gray-600">Submission Source</span>
                <p class="text-gray-900 capitalize">{{ selectedResponse.submission_source }}</p>
              </div>
              <div v-if="selectedResponse.last_saved_at">
                <span class="text-sm font-medium text-gray-600">Last Saved At</span>
                <p class="text-gray-900">{{ formatDate(selectedResponse.last_saved_at) }}</p>
              </div>
              <div v-if="selectedResponse.created_at">
                <span class="text-sm font-medium text-gray-600">Created At</span>
                <p class="text-gray-900">{{ formatDate(selectedResponse.created_at) }}</p>
              </div>
            </div>
          </div>

          <!-- Evaluation Details -->
          <div v-if="selectedResponse.evaluated_by || selectedResponse.evaluation_date || selectedResponse.evaluation_comments" class="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
              <Sparkles class="h-5 w-5" />
              Evaluation Details
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="selectedResponse.evaluated_by">
                <span class="text-sm font-medium text-gray-600">Evaluated By</span>
                <p class="text-gray-900">{{ selectedResponse.evaluated_by }}</p>
              </div>
              <div v-if="selectedResponse.evaluation_date">
                <span class="text-sm font-medium text-gray-600">Evaluation Date</span>
                <p class="text-gray-900">{{ formatDate(selectedResponse.evaluation_date) }}</p>
              </div>
              <div v-if="selectedResponse.evaluation_comments" class="col-span-2">
                <span class="text-sm font-medium text-gray-600">Evaluation Comments</span>
                <p class="text-gray-900 mt-1 whitespace-pre-wrap">{{ selectedResponse.evaluation_comments }}</p>
              </div>
            </div>
          </div>

          <!-- Proposal Data -->
          <div v-if="selectedResponse.proposal_data && Object.keys(selectedResponse.proposal_data).length > 0" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3">Proposal Data</h3>
            <div class="bg-white rounded-lg p-4 max-h-64 overflow-y-auto">
              <pre class="text-xs text-gray-700 whitespace-pre-wrap">{{ JSON.stringify(selectedResponse.proposal_data, null, 2) }}</pre>
            </div>
          </div>

          <!-- Documents -->
          <div v-if="selectedResponse.response_documents && selectedResponse.response_documents.length > 0" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="font-bold text-lg text-gray-900 mb-3">Response Documents</h3>
            <div class="space-y-2">
              <div v-for="(doc, idx) in selectedResponse.response_documents" :key="idx" class="bg-white rounded p-2 border border-gray-200">
                <p class="text-sm text-gray-900">{{ doc.name || doc.filename || `Document ${idx + 1}` }}</p>
                <p v-if="doc.url" class="text-xs text-blue-600 mt-1">
                  <a :href="doc.url" target="_blank" rel="noopener noreferrer" class="hover:underline">View Document</a>
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t border-gray-200 flex justify-end">
          <Button @click="closeResponseModal">Close</Button>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { rfpUseToast } from '@/composables/rfpUseToast'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'
import rfiResponseService from '@/services/rfiResponseService'

// Components
import Card from '@/components_rfp/Card.vue'
import Button from '@/components_rfp/Button.vue'
import Badge from '@/components_rfp/rfpBadge.vue'
import Input from '@/components_rfp/ui/Input.vue'
import Select from '@/components_rfp/ui/Select.vue'
import SelectContent from '@/components_rfp/ui/SelectContent.vue'
import SelectItem from '@/components_rfp/ui/SelectItem.vue'
import SelectTrigger from '@/components_rfp/ui/SelectTrigger.vue'
import SelectValue from '@/components_rfp/ui/SelectValue.vue'

// Icons
import { RefreshCw, Sparkles, LayoutGrid, Table2, FileText, DollarSign, Calendar, Users, Eye, X } from 'lucide-vue-next'

const { success, error: toastError } = rfpUseToast()
const { getAuthHeaders } = useRfpApi()
const API_BASE_URL = getTprmApiV1BaseUrl()

const loading = ref(false)
const viewMode = ref<'cards' | 'table'>('cards')
const responses = ref<any[]>([])
const rfiList = ref<any[]>([])
const selectedIds = ref(new Set<number>())
const showResponseModal = ref(false)
const selectedResponse = ref<any>(null)
const loadingResponse = ref(false)

const filters = ref({
  rfi_id: '',
  evaluation_status: '',
  submission_status: '',
  vendor_search: ''
})

const filteredResponses = computed(() => responses.value)

const selectedCount = computed(() => selectedIds.value.size)

const hasActiveFilters = computed(() =>
  !!(
    filters.value.rfi_id ||
    filters.value.evaluation_status ||
    filters.value.submission_status ||
    filters.value.vendor_search
  )
)

function toggleSelect(id: number) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

function toggleSelectAll() {
  if (selectedCount.value === filteredResponses.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(filteredResponses.value.map((r: any) => r.response_id))
  }
}

function onCompareWithAI() {
  // Placeholder for future: Compare with AI
  if (selectedIds.value.size === 0) {
    toastError('Select at least one response to compare.')
    return
  }
  success('Compare with AI will be available in a future release.')
}

async function fetchRFIList() {
  try {
    console.log('[RFIResponses] Fetching RFI list from:', `${API_BASE_URL}/rfis/`)
    let allRFIs = []
    let nextUrl = `${API_BASE_URL}/rfis/`
    
    // Fetch all pages if pagination is enabled
    while (nextUrl) {
      const response = await axios.get(nextUrl, { headers: getAuthHeaders() })
      console.log('[RFIResponses] RFI list response:', {
        status: response.status,
        hasData: !!response.data,
        isArray: Array.isArray(response.data),
        hasResults: !!(response.data && response.data.results),
        hasNext: !!(response.data && response.data.next)
      })
      
      if (response.data && Array.isArray(response.data)) {
        allRFIs = response.data
        nextUrl = null
      } else if (response.data && response.data.results) {
        allRFIs = allRFIs.concat(response.data.results)
        if (response.data.next) {
          // Handle both absolute and relative URLs
          if (response.data.next.startsWith('http')) {
            nextUrl = response.data.next
          } else {
            nextUrl = response.data.next.startsWith('/') 
              ? `${API_BASE_URL}${response.data.next}`
              : `${API_BASE_URL}/rfis/${response.data.next}`
          }
        } else {
          nextUrl = null
        }
      } else {
        console.warn('[RFIResponses] Unexpected RFI list format:', response.data)
        break
      }
    }
    
    rfiList.value = allRFIs
    console.log('[RFIResponses] Loaded', allRFIs.length, 'RFIs for dropdown')
  } catch (e) {
    console.error('Failed to load RFI list', e)
    console.error('Error details:', {
      message: e.message,
      response: e.response?.data,
      status: e.response?.status
    })
    rfiList.value = []
  }
}

async function fetchResponses() {
  loading.value = true
  try {
    console.log('[RFIResponses] Fetching responses with filters:', filters.value)
    const params: Record<string, string> = {}
    if (filters.value.rfi_id) params.rfi_id = filters.value.rfi_id
    if (filters.value.evaluation_status) params.evaluation_status = filters.value.evaluation_status
    if (filters.value.submission_status) params.submission_status = filters.value.submission_status
    if (filters.value.vendor_search) params.vendor_search = filters.value.vendor_search

    const data = await rfiResponseService.getResponses(params)
    console.log('[RFIResponses] Received data:', {
      hasData: !!data,
      hasResults: !!(data && data.results),
      resultsCount: data?.results?.length || 0,
      dataKeys: data ? Object.keys(data) : []
    })
    
    responses.value = data?.results ?? []
    console.log('[RFIResponses] Set responses.value to', responses.value.length, 'items')
  } catch (e) {
    console.error('[RFIResponses] Failed to load RFI responses', e)
    console.error('[RFIResponses] Error details:', {
      message: e.message,
      response: e.response?.data,
      status: e.response?.status,
      url: e.config?.url
    })
    toastError('Failed to load responses. Please check your connection and try again.')
    responses.value = []
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  fetchResponses()
}

function clearFilters() {
  filters.value = { rfi_id: '', evaluation_status: '', submission_status: '', vendor_search: '' }
  fetchResponses()
}

function formatEvalStatus(s: string) {
  const map: Record<string, string> = {
    DRAFT: 'Draft',
    SUBMITTED: 'Submitted',
    UNDER_EVALUATION: 'Under Evaluation',
    SHORTLISTED: 'Shortlisted',
    REJECTED: 'Rejected',
    AWARDED: 'Awarded'
  }
  return map[s] || s || '—'
}

function evalStatusClass(s: string) {
  switch (s) {
    case 'DRAFT': return 'bg-gray-100 text-gray-800'
    case 'SUBMITTED': return 'bg-blue-100 text-blue-800'
    case 'UNDER_EVALUATION': return 'bg-amber-100 text-amber-800'
    case 'SHORTLISTED': return 'bg-green-100 text-green-800'
    case 'REJECTED': return 'bg-red-100 text-red-800'
    case 'AWARDED': return 'bg-emerald-100 text-emerald-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

function formatDate(d: string | null | undefined) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { dateStyle: 'medium' })
}

function formatCurrency(val: string | number | null | undefined) {
  if (val == null) return '—'
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (Number.isNaN(n)) return '—'
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(n)
}

function getInitials(name: string) {
  if (!name || name === 'V') return 'V'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

function getStatusBorderClass(status: string) {
  switch (status) {
    case 'DRAFT': return 'border-l-gray-400'
    case 'SUBMITTED': return 'border-l-blue-500'
    case 'UNDER_EVALUATION': return 'border-l-amber-500'
    case 'SHORTLISTED': return 'border-l-green-500'
    case 'REJECTED': return 'border-l-red-500'
    case 'AWARDED': return 'border-l-emerald-500'
    default: return 'border-l-gray-400'
  }
}

async function viewResponse(responseId: number) {
  showResponseModal.value = true
  loadingResponse.value = true
  selectedResponse.value = null
  
  try {
    const response = await axios.get(`${API_BASE_URL}/rfi-responses/${responseId}/`, {
      headers: getAuthHeaders()
    })
    selectedResponse.value = response.data
  } catch (e) {
    console.error('[RFIResponses] Failed to load response details', e)
    toastError('Failed to load response details.')
    closeResponseModal()
  } finally {
    loadingResponse.value = false
  }
}

function closeResponseModal() {
  showResponseModal.value = false
  selectedResponse.value = null
}

onMounted(() => {
  fetchRFIList()
  fetchResponses()
})
</script>

<style scoped>
.phase-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm transition-all duration-200;
}

.phase-card:hover {
  @apply shadow-lg;
}

.text-muted-foreground {
  @apply text-gray-500;
}

.compare-ai-btn {
  @apply bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:from-violet-700 hover:to-indigo-700 shadow-md hover:shadow-lg transition-all;
}

/* Card hover effects */
.phase-card.cursor-pointer:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Progress bar animations */
@keyframes progressFill {
  from {
    width: 0%;
  }
}

.phase-card .rounded-full {
  animation: progressFill 0.8s ease-out;
}
</style>
