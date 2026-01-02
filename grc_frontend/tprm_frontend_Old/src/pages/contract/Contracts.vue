<template>
  <div class="space-y-6">
    <!-- Main Content -->
    <div>
      <!-- Header -->
      <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Contracts</h1>
        <p class="text-muted-foreground">Manage your contract portfolio</p>
      </div>
      <Button @click="go('/contracts/new')" class="gap-2">
        <Plus class="w-4 h-4" />
        New Contract
      </Button>
    </div>

    <!-- Tabs -->
    <Tabs v-model="activeTab" class="space-y-6">
      <TabsList class="grid w-full grid-cols-2">
        <TabsTrigger value="contracts">Contracts</TabsTrigger>
        <TabsTrigger value="renewals">Renewals</TabsTrigger>
      </TabsList>
      


      <TabsContent value="contracts" class="space-y-6">
        <!-- Filters -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle class="flex items-center gap-2">
                <Filter class="w-5 h-5" />
                Filters
              </CardTitle>
              <Button 
                variant="outline" 
                size="sm" 
                @click="showAdvancedFilters = !showAdvancedFilters"
                class="gap-2"
              >
                <Filter class="w-4 h-4" />
                {{ showAdvancedFilters ? 'Hide' : 'Show' }} Advanced Filters
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <!-- Primary Filters -->
            <div class="flex flex-col gap-4">
              <!-- First Row - 3 Filters -->
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Select v-model="statusFilter">
                  <SelectTrigger>
                    <SelectValue>
                      {{ statusFilter === 'all' ? 'All Statuses' : statusFilter.replace(/_/g, ' ') }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="ACTIVE">Active</SelectItem>
                    <SelectItem value="DRAFT">Draft</SelectItem>
                    <SelectItem value="APPROVED">Approved</SelectItem>
                    <SelectItem value="PENDING_ASSIGNMENT">Pending Assignment</SelectItem>
                    <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
                    <SelectItem value="UNDER_NEGOTIATION">Under Negotiation</SelectItem>
                    <SelectItem value="EXPIRED">Expired</SelectItem>
                    <SelectItem value="TERMINATED">Terminated</SelectItem>
                    <SelectItem value="REJECTED">Rejected</SelectItem>
                  </SelectContent>
                </Select>

                <Select v-model="typeFilter">
                  <SelectTrigger>
                    <SelectValue>
                      {{ getContractTypeLabel(typeFilter) }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="MASTER_AGREEMENT">Master Agreement</SelectItem>
                    <SelectItem value="SOW">Statement of Work</SelectItem>
                    <SelectItem value="PURCHASE_ORDER">Purchase Order</SelectItem>
                    <SelectItem value="SERVICE_AGREEMENT">Service Agreement</SelectItem>
                    <SelectItem value="LICENSE">License</SelectItem>
                    <SelectItem value="NDA">NDA</SelectItem>
                  </SelectContent>
                </Select>

                <Select v-model="contractKindFilter">
                  <SelectTrigger>
                    <SelectValue>
                      {{ getContractKindLabel(contractKindFilter) }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Contract Kinds</SelectItem>
                    <SelectItem value="MAIN">Main Contract</SelectItem>
                    <SelectItem value="SUBCONTRACT">Subcontract</SelectItem>
                    <SelectItem value="AMENDMENT">Amendment</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <!-- Second Row - Advanced Filters -->
              <div v-if="showAdvancedFilters" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Select v-model="riskLevelFilter">
                  <SelectTrigger>
                    <SelectValue>
                      {{ riskLevelFilter === 'all' ? 'All Risk Levels' : riskLevelFilter + ' Risk' }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Risk Levels</SelectItem>
                    <SelectItem value="Low">Low Risk</SelectItem>
                    <SelectItem value="Medium">Medium Risk</SelectItem>
                    <SelectItem value="High">High Risk</SelectItem>
                  </SelectContent>
                </Select>

                <Select v-model="priorityFilter">
                  <SelectTrigger>
                    <SelectValue>
                      {{ priorityFilter === 'all' ? 'All Priorities' : priorityFilter.charAt(0).toUpperCase() + priorityFilter.slice(1) }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Priorities</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>

                <Select v-model="contractCategoryFilter">
                  <SelectTrigger>
                    <SelectValue>
                      {{ contractCategoryFilter === 'all' ? 'All Categories' : contractCategoryFilter.charAt(0).toUpperCase() + contractCategoryFilter.slice(1) }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    <SelectItem value="goods">Goods</SelectItem>
                    <SelectItem value="services">Services</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="consulting">Consulting</SelectItem>
                    <SelectItem value="others">Others</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <!-- Clear All Button -->
              <div v-if="showAdvancedFilters" class="flex justify-start">
                <Button 
                  variant="outline" 
                  @click="clearAllFilters"
                  class="gap-2"
                >
                  <XCircle class="w-4 h-4" />
                  Clear All
                </Button>
              </div>

              <!-- Active Filters Summary -->
              <div v-if="getActiveFiltersCount() > 0" class="flex items-center gap-2 pt-2 border-t">
                <span class="text-sm text-muted-foreground">Active filters:</span>
                <Badge variant="secondary" class="gap-1">
                  {{ getActiveFiltersCount() }} filter{{ getActiveFiltersCount() > 1 ? 's' : '' }}
                </Badge>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  @click="clearAllFilters"
                  class="gap-1 h-7 text-xs"
                >
                  <XCircle class="w-3 h-3" />
                  Clear
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Results Summary -->
        <div class="flex items-center justify-between">
          <p class="text-sm text-muted-foreground">
            Showing {{ contracts.length }} of {{ pagination.total_count }} contracts
          </p>
          <Button variant="outline" size="sm" class="gap-2">
            <Download class="w-4 h-4" />
            Export
          </Button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p class="mt-4 text-muted-foreground">Loading contracts...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="text-center py-12">
          <div class="text-destructive mb-4">
            <FileText class="mx-auto h-12 w-12" />
          </div>
          <h3 class="text-lg font-semibold text-foreground mb-2">Error Loading Contracts</h3>
          <p class="text-muted-foreground mb-4">{{ error }}</p>
          <Button @click="loadContracts" variant="outline">
            <RefreshCw class="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </div>

        <!-- Contracts Table -->
        <Card v-else>
          <CardContent class="p-0">
            <div class="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Contract</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Expiry</TableHead>
                    <TableHead class="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow 
                    v-for="contract in contracts" 
                    :key="contract.contract_id" 
                    class="hover:bg-muted/50"
                  >
                    <TableCell>
                      <div class="space-y-1.5">
                        <!-- Title Row -->
                        <div class="flex items-start justify-between gap-2">
                          <span class="font-semibold text-foreground leading-tight">
                            {{ contract.contract_title || 'N/A' }}
                          </span>
                          <!-- Contract Kind Badge (right-aligned) -->
                          <Badge 
                            v-if="contract.contract_kind && contract.contract_kind !== 'MAIN'" 
                            :class="getContractKindBadgeClass(contract.contract_kind)"
                            class="text-xs px-2 py-0.5 shrink-0"
                          >
                            {{ getContractKindLabel(contract.contract_kind) }}
                          </Badge>
                        </div>
                        
                        <!-- Details Row -->
                        <div class="flex items-center gap-2 text-xs text-muted-foreground">
                          <!-- Contract Number -->
                          <span class="font-mono truncate max-w-[200px]" :title="contract.contract_number">
                            {{ contract.contract_number || 'N/A' }}
                          </span>
                          
                          <!-- Version -->
                          <span v-if="contract.version_number" class="shrink-0">
                            • v{{ contract.version_number }}
                          </span>
                          
                          <!-- Parent Contract -->
                          <span v-if="contract.parent_contract_id" class="shrink-0">
                            • Parent: {{ contract.parent_contract_id }}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div class="font-medium">{{ contract.vendor?.company_name || 'N/A' }}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{{ contract.contract_type || 'N/A' }}</Badge>
                    </TableCell>
                    <TableCell>
                      <div class="font-medium">
                        ${{ (contract.contract_value || 0).toLocaleString() }}
                      </div>
                      <div class="text-sm text-muted-foreground">
                        {{ contract.currency || 'USD' }}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge :class="getStatusBadgeClass(contract.status)">
                        {{ contract.status || 'N/A' }}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge :class="getRiskBadgeClass(getRiskLevel(contract.contract_risk_score))" variant="outline">
                        {{ getRiskLevel(contract.contract_risk_score) }}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div class="text-sm">
                        {{ contract.end_date ? new Date(contract.end_date).toLocaleDateString() : 'N/A' }}
                      </div>
                      <div 
                        v-if="contract.end_date && getDaysUntilExpiry(contract.end_date) > 0 && getDaysUntilExpiry(contract.end_date) <= 90"
                        class="text-xs text-warning"
                      >
                        {{ getDaysUntilExpiry(contract.end_date) }} days left
                      </div>
                      <div 
                        v-if="contract.end_date && getDaysUntilExpiry(contract.end_date) <= 0"
                        class="text-xs text-destructive"
                      >
                        Expired
                      </div>
                    </TableCell>
                    <TableCell class="text-right">
                      <div class="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          @click="go(`/contracts/${contract.contract_id}`)"
                          title="View Contract"
                        >
                          <Eye class="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          @click="go(`/contracts/${contract.contract_id}/edit-advanced`)"
                          title="Edit Contract"
                        >
                          <Edit class="w-4 h-4" />
                        </Button>
                        <Button
                          v-if="contract.status === 'APPROVED'"
                          variant="ghost"
                          size="icon"
                          @click="openActivateDialog(contract)"
                          title="Activate Contract"
                          class="text-green-600 hover:text-green-700"
                        >
                          <CheckCircle class="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          @click="go(`/contracts/${contract.contract_id}/renewal`)"
                          title="Initiate Renewal"
                        >
                          <RefreshCw class="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          @click="openArchiveDialog(contract)"
                          title="Archive Contract"
                          class="text-orange-600 hover:text-orange-700"
                        >
                          <Archive class="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            <!-- Pagination Controls -->
            <div v-if="pagination.total_pages > 1" class="flex flex-col sm:flex-row items-center justify-between px-6 py-4 border-t bg-slate-50 dark:bg-slate-800/50 gap-4">
              <div class="flex items-center text-sm text-muted-foreground">
                <span class="hidden sm:inline">Page {{ pagination.page }} of {{ pagination.total_pages }} • </span>
                <span>Showing {{ ((pagination.page - 1) * pagination.page_size) + 1 }} to {{ Math.min(pagination.page * pagination.page_size, pagination.total_count) }} of {{ pagination.total_count }} contracts</span>
              </div>
              
              <div class="flex items-center space-x-2">
                <!-- Page Size Selector -->
                <div class="flex items-center space-x-2">
                  <span class="text-sm text-muted-foreground">Show:</span>
                  <Select :model-value="pagination.page_size.toString()" @update:model-value="changePageSize">
                    <SelectTrigger class="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="20">20</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                  <span class="text-sm text-muted-foreground">per page</span>
                </div>
                
                <!-- Pagination Buttons -->
                <div class="flex items-center space-x-1 flex-wrap justify-center">
                  <!-- First Page -->
                  <Button
                    variant="outline"
                    size="sm"
                    :disabled="pagination.page === 1"
                    @click="goToPage(1)"
                    class="h-8 w-8 p-0"
                  >
                    <span class="sr-only">First page</span>
                    <ChevronLeft class="h-4 w-4" />
                    <ChevronLeft class="h-4 w-4 -ml-1" />
                  </Button>
                  
                  <!-- Previous Page -->
                  <Button
                    variant="outline"
                    size="sm"
                    :disabled="!pagination.has_previous"
                    @click="goToPage(pagination.page - 1)"
                    class="h-8 w-8 p-0"
                  >
                    <span class="sr-only">Previous page</span>
                    <ChevronLeft class="h-4 w-4" />
                  </Button>
                  
                  <!-- Page Numbers -->
                  <div class="flex items-center space-x-1">
                    <template v-for="page in getVisiblePages()" :key="page">
                      <Button
                        v-if="page !== '...'"
                        :variant="page === pagination.page ? 'default' : 'outline'"
                        size="sm"
                        @click="goToPage(page)"
                        class="h-8 w-8 p-0"
                      >
                        {{ page }}
                      </Button>
                      <span v-else class="px-2 text-muted-foreground">...</span>
                    </template>
                  </div>
                  
                  <!-- Next Page -->
                  <Button
                    variant="outline"
                    size="sm"
                    :disabled="!pagination.has_next"
                    @click="goToPage(pagination.page + 1)"
                    class="h-8 w-8 p-0"
                  >
                    <span class="sr-only">Next page</span>
                    <ChevronRight class="h-4 w-4" />
                  </Button>
                  
                  <!-- Last Page -->
                  <Button
                    variant="outline"
                    size="sm"
                    :disabled="pagination.page === pagination.total_pages"
                    @click="goToPage(pagination.total_pages)"
                    class="h-8 w-8 p-0"
                  >
                    <span class="sr-only">Last page</span>
                    <ChevronRight class="h-4 w-4" />
                    <ChevronRight class="h-4 w-4 -ml-1" />
                  </Button>
                </div>
              </div>
            </div>

            <div v-if="contracts.length === 0" class="text-center py-12">
              <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 class="mt-2 text-sm font-semibold text-foreground">No contracts found</h3>
              <p class="mt-1 text-sm text-muted-foreground">
                Try adjusting your search or filter criteria.
              </p>
              <div class="mt-6">
                <Button @click="go('/contracts/new')">
                  <Plus class="w-4 h-4 mr-2" />
                  Create new contract
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="renewals" class="space-y-6">
        <!-- Renewal Header -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 class="text-2xl font-bold text-foreground">Contract Renewals</h2>
            <p class="text-muted-foreground">Manage contract renewal requests and decisions</p>
          </div>
        </div>

        <!-- Renewal Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium text-blue-700">Total Renewals</CardTitle>
              <RefreshCw class="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div class="text-3xl font-bold text-blue-700">{{ contractRenewals.length }}</div>
              <p class="text-xs text-muted-foreground">
                Active renewal requests
              </p>
              <div class="mt-2 text-xs text-blue-600">
                {{ contractRenewals.filter(r => r.renewal_decision === 'pending').length }} pending
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium text-orange-700">Pending Decisions</CardTitle>
              <Clock class="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div class="text-3xl font-bold text-orange-600">
                {{ contractRenewals.filter(r => r.renewal_decision === 'pending').length }}
              </div>
              <p class="text-xs text-muted-foreground">
                Awaiting decision
              </p>
              <div class="mt-2 text-xs text-orange-600">
                {{ contractRenewals.filter(r => {
                  const dueDate = new Date(r.decision_due_date);
                  const today = new Date();
                  return dueDate < today;
                }).length }} overdue
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium text-green-700">Approved</CardTitle>
              <CheckCircle class="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div class="text-3xl font-bold text-green-600">
                {{ contractRenewals.filter(r => r.renewal_decision === 'approved').length }}
              </div>
              <p class="text-xs text-muted-foreground">
                Renewals approved
              </p>
              <div class="mt-2 text-xs text-green-600">
                {{ getApprovalRate() }}% success rate
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle class="text-sm font-medium text-red-700">Rejected</CardTitle>
              <XCircle class="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div class="text-3xl font-bold text-red-600">
                {{ contractRenewals.filter(r => r.renewal_decision === 'rejected').length }}
              </div>
              <p class="text-xs text-muted-foreground">
                Renewals rejected
              </p>
              <div class="mt-2 text-xs text-red-600">
                {{ getRejectionRate() }}% rejection rate
              </div>
            </CardContent>
          </Card>
        </div>


        <!-- Renewals Table -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <RefreshCw class="w-5 h-5" />
              Renewal Requests ({{ contractRenewals.length }})
            </CardTitle>
            <CardDescription>Track all contract renewal requests and their current status</CardDescription>
          </CardHeader>
          <CardContent class="p-0">
            <div class="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Renewal ID</TableHead>
                    <TableHead>Contract</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Renewal Date</TableHead>
                    <TableHead>Decision Due</TableHead>
                    <TableHead>Risk Score</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Decision</TableHead>
                    <TableHead>Decided By</TableHead>
                    <TableHead class="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow 
                    v-for="renewal in contractRenewals" 
                    :key="renewal.renewal_id" 
                    class="hover:bg-muted/50"
                  >
                    <TableCell>
                      <div class="font-medium text-sm">{{ renewal.renewal_id }}</div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div class="font-medium">{{ renewal.contract_title || 'N/A' }}</div>
                        <div class="text-sm text-muted-foreground">
                          {{ renewal.contract_id }}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div class="font-medium">{{ renewal.vendor?.company_name || 'N/A' }}</div>
                    </TableCell>
                    <TableCell>
                      <div class="text-sm font-medium">
                        {{ renewal.contract_value ? `$${renewal.contract_value.toLocaleString()}` : 'N/A' }}
                      </div>
                      <div class="text-xs text-muted-foreground">{{ renewal.currency || 'USD' }}</div>
                    </TableCell>
                    <TableCell>
                      <div class="text-sm">{{ new Date(renewal.renewal_date).toLocaleDateString() }}</div>
                    </TableCell>
                    <TableCell>
                      <div class="text-sm">{{ new Date(renewal.decision_due_date).toLocaleDateString() }}</div>
                      <div 
                        v-if="renewal.renewal_decision === 'pending'"
                        :class="getDaysUntilDueClass(renewal.decision_due_date)"
                      >
                        {{ getDaysUntilDue(renewal.decision_due_date) }}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div class="text-sm font-medium">
                        {{ renewal.contract_risk_score ? `${renewal.contract_risk_score}%` : 'N/A' }}
                      </div>
                      <div 
                        v-if="renewal.contract_risk_score"
                        :class="getRiskClass(renewal.contract_risk_score)"
                      >
                        {{ getRiskLevel(renewal.contract_risk_score) }} Risk
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge 
                        v-if="renewal.renewal_decision === 'pending'"
                        variant="outline" 
                        class="text-orange-600 border-orange-600"
                      >
                        <Clock class="w-3 h-3 mr-1" />
                        Pending
                      </Badge>
                      <Badge v-else :class="getRenewalDecisionBadgeClass(renewal.renewal_decision)">
                        {{ renewal.renewal_decision.toUpperCase() }}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div class="text-sm font-medium">
                        {{ getDecisionText(renewal.renewal_decision) }}
                      </div>
                      <div v-if="renewal.decision_date" class="text-xs text-muted-foreground">
                        {{ new Date(renewal.decision_date).toLocaleDateString() }}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div v-if="renewal.decided_by" class="flex items-center gap-2">
                        <User class="w-4 h-4 text-muted-foreground" />
                        <span class="text-sm">{{ renewal.decided_by }}</span>
                      </div>
                      <span v-else class="text-sm text-muted-foreground">-</span>
                    </TableCell>
                    <TableCell class="text-right">
                      <div class="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          @click="go(`/renewals/${renewal.renewal_id}`)"
                          title="View Renewal Details"
                        >
                          <Eye class="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          @click="go(`/contracts/${renewal.contract_id}`)"
                          title="View Contract"
                        >
                          <FileText class="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            <div v-if="contractRenewals.length === 0" class="text-center py-12">
              <RefreshCw class="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 class="mt-2 text-sm font-semibold text-foreground">No renewal requests</h3>
              <p class="mt-1 text-sm text-muted-foreground">
                Start renewal processes for contracts approaching expiration.
              </p>
              <Button class="mt-4" variant="outline">
                <RefreshCw class="w-4 h-4 mr-2" />
                Start First Renewal
              </Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>

    </div>

    <!-- Archive Dialog -->
    <Dialog v-model:open="archiveDialogOpen">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2">
            <Archive class="w-5 h-5 text-orange-600" />
            Archive Contract
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to archive this contract? This action will move the contract to the archive.
          </DialogDescription>
        </DialogHeader>
        
        <div v-if="contractToArchive" class="space-y-4">
          <!-- Contract Info -->
          <div class="bg-muted p-4 rounded-lg">
            <h4 class="font-medium text-foreground">{{ contractToArchive.contract_title }}</h4>
            <p class="text-sm text-muted-foreground">{{ contractToArchive.contract_number }}</p>
            <p class="text-sm text-muted-foreground">{{ contractToArchive.vendor?.company_name }}</p>
          </div>
          
          <!-- Archive Form -->
          <div class="space-y-4">
            <div>
              <Label for="archive_reason">Archive Reason *</Label>
              <Select v-model="archiveForm.archive_reason">
                <SelectTrigger>
                  <SelectValue placeholder="Select reason" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CONTRACT_EXPIRED">Contract Expired</SelectItem>
                  <SelectItem value="EARLY_TERMINATION">Early Termination</SelectItem>
                  <SelectItem value="PROJECT_COMPLETED">Project Completed</SelectItem>
                  <SelectItem value="MUTUAL_AGREEMENT">Mutual Agreement</SelectItem>
                  <SelectItem value="BREACH">Breach of Contract</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label for="archive_comments">Comments</Label>
              <textarea
                id="archive_comments"
                v-model="archiveForm.archive_comments"
                placeholder="Optional comments about the archive"
                rows="3"
                class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                id="can_be_restored"
                v-model="archiveForm.can_be_restored"
                type="checkbox"
                class="rounded border-gray-300"
              />
              <Label for="can_be_restored" class="text-sm">
                Allow this contract to be restored later
              </Label>
            </div>
          </div>
        </div>
        
        <DialogFooter class="gap-2">
          <Button variant="outline" @click="closeArchiveDialog" :disabled="archiveLoading">
            Cancel
          </Button>
          <Button 
            @click="handleArchiveContract" 
            :disabled="!archiveForm.archive_reason || archiveLoading"
            class="bg-orange-600 hover:bg-orange-700"
          >
            <Archive v-if="!archiveLoading" class="w-4 h-4 mr-2" />
            <div v-else class="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            {{ archiveLoading ? 'Archiving...' : 'Archive Contract' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Activation Dialog -->
    <Dialog v-model:open="activateDialogOpen">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2">
            <CheckCircle class="w-5 h-5 text-green-600" />
            Activate Contract
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to activate this contract? This will change the status from "Approved" to "Active".
          </DialogDescription>
        </DialogHeader>
        
        <div v-if="contractToActivate" class="space-y-4">
          <!-- Contract Info -->
          <div class="bg-muted p-4 rounded-lg">
            <h4 class="font-medium text-foreground">{{ contractToActivate.contract_title }}</h4>
            <p class="text-sm text-muted-foreground">{{ contractToActivate.contract_number }}</p>
            <p class="text-sm text-muted-foreground">{{ contractToActivate.vendor?.company_name }}</p>
            <div class="mt-2">
              <Badge class="bg-yellow-100 text-yellow-800">Current: APPROVED</Badge>
              <span class="mx-2 text-muted-foreground">→</span>
              <Badge class="bg-green-100 text-green-800">New: ACTIVE</Badge>
            </div>
          </div>
          
          <!-- Activation Form -->
          <div class="space-y-4">
            <div>
              <Label for="activation_comments">Activation Comments (Optional)</Label>
              <textarea
                id="activation_comments"
                v-model="activateForm.activation_comments"
                placeholder="Add any comments about the activation..."
                rows="3"
                class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                id="notify_vendor"
                v-model="activateForm.notify_vendor"
                type="checkbox"
                class="rounded border-gray-300"
              />
              <Label for="notify_vendor" class="text-sm">
                Notify vendor about contract activation
              </Label>
            </div>
          </div>
        </div>
        
        <DialogFooter class="gap-2">
          <Button variant="outline" @click="closeActivateDialog" :disabled="activateLoading">
            Cancel
          </Button>
          <Button 
            @click="handleActivateContract" 
            :disabled="activateLoading"
            class="bg-green-600 hover:bg-green-700"
          >
            <CheckCircle v-if="!activateLoading" class="w-4 h-4 mr-2" />
            <div v-else class="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            {{ activateLoading ? 'Activating...' : 'Activate Contract' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Input, Label, Textarea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
  Tabs, TabsContent, TabsList, TabsTrigger,
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle
} from '@/components/ui_contract'
import { 
  FileText, Filter, Plus, Eye, Edit, Download, RefreshCw, 
  Calendar, Bell, CheckCircle, XCircle, Clock, User, Archive, ChevronLeft, ChevronRight
} from 'lucide-vue-next'
import contractsApi from '../../services/contractsApi'

const router = useRouter()
const go = (path) => router.push(path)

// State
const statusFilter = ref('all')
const typeFilter = ref('all')
const contractKindFilter = ref('all')
const riskLevelFilter = ref('all')
const priorityFilter = ref('all')
const contractCategoryFilter = ref('all')
const activeTab = ref('contracts')
const loading = ref(false)
const error = ref(null)
const showAdvancedFilters = ref(false)


// Data
const contracts = ref([])
const contractRenewals = ref([])
const contractStats = ref({})
const pagination = ref({
  page: 1,
  page_size: 20,
  total_pages: 1,
  total_count: 0,
  has_next: false,
  has_previous: false
})

// Archive dialog state
const archiveDialogOpen = ref(false)
const contractToArchive = ref(null)
const archiveForm = ref({
  archive_reason: '',
  archive_comments: '',
  can_be_restored: true
})
const archiveLoading = ref(false)

// Activation dialog state
const activateDialogOpen = ref(false)
const contractToActivate = ref(null)
const activateForm = ref({
  activation_comments: '',
  notify_vendor: true
})
const activateLoading = ref(false)


// Mock renewal data (fallback)
const mockContractRenewals = ref([
  {
    renewal_id: "REN-001",
    contract_id: "CNT-2024-001",
    renewal_date: "2024-03-15",
    notification_sent_date: "2024-02-15",
    decision_due_date: "2024-04-15",
    renewal_decision: "pending",
    new_contract_id: null,
    decided_by: null,
    decision_date: null,
    comments: "Contract up for renewal - Cloud Infrastructure Services",
    contract_value: 500000,
    currency: "USD",
    start_date: "2024-04-01",
    end_date: "2027-03-31",
    renewal_terms: "3-year renewal with 15% cost increase and enhanced SLA requirements",
    auto_renewal: false,
    notice_period_days: 60,
    contract_type: "SERVICE_CONTRACT",
    contract_category: "technology",
    termination_clause: "both",
    liability_cap: 1000000,
    insurance_requirements: "General liability: $2M, Professional liability: $1M",
    data_protection_clauses: "GDPR compliance required, data residency in EU",
    dispute_resolution: "mediation",
    governing_law: "California, USA",
    contract_risk_score: 65.5,
    priority: "high",
    compliance_status: "under_review"
  },
  {
    renewal_id: "REN-002",
    contract_id: "CNT-2024-002",
    renewal_date: "2024-02-20",
    notification_sent_date: "2024-01-20",
    decision_due_date: "2024-03-20",
    renewal_decision: "approved",
    new_contract_id: "CNT-2024-002-REN",
    decided_by: "John Smith",
    decision_date: "2024-02-25",
    comments: "Renewal approved with updated terms",
    contract_value: 250000,
    currency: "USD",
    start_date: "2024-03-01",
    end_date: "2026-02-28",
    renewal_terms: "2-year renewal with same terms and pricing",
    auto_renewal: true,
    notice_period_days: 30,
    contract_type: "SOW",
    contract_category: "services",
    termination_clause: "convenience",
    liability_cap: 500000,
    insurance_requirements: "General liability: $1M",
    data_protection_clauses: "Standard data protection terms",
    dispute_resolution: "negotiation",
    governing_law: "New York, USA",
    contract_risk_score: 35.0,
    priority: "medium",
    compliance_status: "compliant"
  },
  {
    renewal_id: "REN-003",
    contract_id: "CNT-2024-003",
    renewal_date: "2024-01-10",
    notification_sent_date: "2023-12-10",
    decision_due_date: "2024-02-10",
    renewal_decision: "rejected",
    new_contract_id: null,
    decided_by: "Sarah Johnson",
    decision_date: "2024-01-15",
    comments: "Renewal rejected due to performance issues",
    contract_value: 750000,
    currency: "USD",
    start_date: "2024-02-01",
    end_date: "2027-01-31",
    renewal_terms: "3-year renewal with performance improvement requirements",
    auto_renewal: false,
    notice_period_days: 90,
    contract_type: "MASTER_AGREEMENT",
    contract_category: "consulting",
    termination_clause: "cause",
    liability_cap: 1500000,
    insurance_requirements: "General liability: $3M, Professional liability: $2M",
    data_protection_clauses: "Enhanced security requirements, regular audits",
    dispute_resolution: "arbitration",
    governing_law: "Texas, USA",
    contract_risk_score: 85.0,
    priority: "urgent",
    compliance_status: "non_compliant"
  }
])

// Computed - removed filteredContracts as we now use server-side pagination


// API Functions
const loadContracts = async () => {
  try {
    loading.value = true
    error.value = null
    
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      status: statusFilter.value !== 'all' ? statusFilter.value : undefined,
      contract_type: typeFilter.value !== 'all' ? typeFilter.value : undefined,
      contract_kind: contractKindFilter.value !== 'all' ? contractKindFilter.value : undefined,
      priority: priorityFilter.value !== 'all' ? priorityFilter.value : undefined,
      contract_category: contractCategoryFilter.value !== 'all' ? contractCategoryFilter.value : undefined,
      risk_level: riskLevelFilter.value !== 'all' ? riskLevelFilter.value : undefined,
      ordering: '-created_at'
    }
    
    // Remove undefined values
    Object.keys(params).forEach(key => {
      if (params[key] === undefined) {
        delete params[key]
      }
    })
    
    console.log('🔍 Loading contracts with filters:', params)
    
    const response = await contractsApi.getContracts(params)
    
    if (response.success) {
      contracts.value = response.data || []
      pagination.value = response.pagination || pagination.value
    } else {
      throw new Error(response.message || 'Failed to load contracts')
    }
  } catch (err) {
    console.error('Error loading contracts:', err)
    error.value = err.message || 'Failed to load contracts'
    contracts.value = []
  } finally {
    loading.value = false
  }
}

const loadContractRenewals = async () => {
  try {
    console.log('🔄 Loading contract renewals...')
    console.log('🔑 Auth token:', localStorage.getItem('session_token') ? 'Present' : 'Missing')
    
    const response = await contractsApi.getContractRenewals()
    console.log('📊 Contract renewals response:', response)
    
    if (response.success) {
      // Transform the API data to match frontend expectations
      const transformedRenewals = (response.data || []).map(renewal => ({
        ...renewal,
        // Map renewal_decision values to frontend expected values
        renewal_decision: mapRenewalDecision(renewal.renewal_decision),
        // Use decided_by_display if available, otherwise fallback to decided_by
        decided_by: renewal.decided_by_display || renewal.decided_by,
        // Ensure contract_title is available
        contract_title: renewal.contract_title || 'N/A',
        // Ensure vendor data is properly structured
        vendor: renewal.vendor || null
      }))
      
      contractRenewals.value = transformedRenewals
      console.log('✅ Contract renewals loaded:', contractRenewals.value.length, 'items')
      console.log('📋 Sample renewal data:', contractRenewals.value[0])
    } else {
      console.warn('⚠️ Contract renewals API returned success=false:', response.message)
      console.warn('⚠️ Full response:', response)
      // Fallback to mock data
      contractRenewals.value = mockContractRenewals.value
    }
  } catch (err) {
    console.error('❌ Error loading contract renewals:', err)
    console.error('❌ Error status:', err.response?.status)
    console.error('❌ Error details:', err.response?.data)
    console.error('❌ Full error:', err)
    // Fallback to mock data
    contractRenewals.value = mockContractRenewals.value
  }
}

const loadContractStats = async () => {
  try {
    const response = await contractsApi.getContractStats()
    
    if (response.success) {
      contractStats.value = response.data || {}
    }
  } catch (err) {
    console.error('Error loading contract stats:', err)
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadContracts(),
    loadContractRenewals(),
    loadContractStats()
  ])
})

// Watchers
watch([
  statusFilter, 
  typeFilter, 
  contractKindFilter, 
  riskLevelFilter, 
  priorityFilter, 
  contractCategoryFilter
], () => {
  // Reset to first page when filters change
  pagination.value.page = 1
  loadContracts()
}, { deep: true })


// Methods
const getContractTypeLabel = (type) => {
  const labels = {
    'all': 'All Types',
    'MASTER_AGREEMENT': 'Master Agreement',
    'SOW': 'Statement of Work',
    'PURCHASE_ORDER': 'Purchase Order',
    'SERVICE_AGREEMENT': 'Service Agreement',
    'LICENSE': 'License',
    'NDA': 'NDA'
  }
  return labels[type] || type
}

const getContractKindLabel = (kind) => {
  const labels = {
    'all': 'All Contract Kinds',
    'MAIN': 'Main Contract',
    'SUBCONTRACT': 'Subcontract',
    'AMENDMENT': 'Amendment'
  }
  return labels[kind] || kind
}

const clearAllFilters = () => {
  statusFilter.value = 'all'
  typeFilter.value = 'all'
  contractKindFilter.value = 'all'
  riskLevelFilter.value = 'all'
  priorityFilter.value = 'all'
  contractCategoryFilter.value = 'all'
}

const getActiveFiltersCount = () => {
  let count = 0
  if (statusFilter.value !== 'all') count++
  if (typeFilter.value !== 'all') count++
  if (contractKindFilter.value !== 'all') count++
  if (riskLevelFilter.value !== 'all') count++
  if (priorityFilter.value !== 'all') count++
  if (contractCategoryFilter.value !== 'all') count++
  return count
}

const mapRenewalDecision = (backendDecision) => {
  const decisionMap = {
    'PENDING': 'pending',
    'RENEW': 'approved',
    'RENEGOTIATE': 'approved',
    'TERMINATE': 'rejected'
  }
  return decisionMap[backendDecision] || 'pending'
}

// Pagination Methods
const goToPage = (page) => {
  if (page >= 1 && page <= pagination.value.total_pages && page !== pagination.value.page) {
    pagination.value.page = page
    loadContracts()
  }
}

const changePageSize = (newSize) => {
  const newPageSize = parseInt(newSize)
  if (newPageSize !== pagination.value.page_size) {
    pagination.value.page_size = newPageSize
    pagination.value.page = 1 // Reset to first page when changing page size
    loadContracts()
  }
}

const getVisiblePages = () => {
  const current = pagination.value.page
  const total = pagination.value.total_pages
  const pages = []
  
  if (total <= 7) {
    // Show all pages if 7 or fewer
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // Always show first page
    pages.push(1)
    
    if (current <= 4) {
      // Show first 5 pages + ellipsis + last page
      for (let i = 2; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      // Show first page + ellipsis + last 5 pages
      pages.push('...')
      for (let i = total - 4; i <= total; i++) {
        pages.push(i)
      }
    } else {
      // Show first page + ellipsis + current-1, current, current+1 + ellipsis + last page
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(total)
    }
  }
  
  return pages
}

const getDaysUntilExpiry = (endDate) => {
  const today = new Date()
  const expiry = new Date(endDate)
  return Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 3600 * 24))
}

const getStatusBadgeClass = (status) => {
  const variants = {
    // Backend format (uppercase)
    'ACTIVE': 'bg-success text-success-foreground',
    'DRAFT': 'bg-muted text-muted-foreground',
    'UNDER_REVIEW': 'bg-warning text-warning-foreground',
    'UNDER_NEGOTIATION': 'bg-warning text-warning-foreground',
    'PENDING_ASSIGNMENT': 'bg-warning text-warning-foreground',
    'APPROVED': 'bg-blue-100 text-blue-800',
    'REJECTED': 'bg-destructive text-destructive-foreground',
    'EXPIRED': 'bg-destructive text-destructive-foreground',
    'TERMINATED': 'bg-destructive text-destructive-foreground',
    // Legacy format (title case) - for backwards compatibility
    'Active': 'bg-success text-success-foreground',
    'Draft': 'bg-muted text-muted-foreground',
    'Review': 'bg-warning text-warning-foreground',
    'Expired': 'bg-destructive text-destructive-foreground',
    'Terminated': 'bg-destructive text-destructive-foreground',
    'Renewed': 'bg-success text-success-foreground'
  }
  return variants[status] || ''
}

const getRiskBadgeClass = (risk) => {
  const variants = {
    'Low': 'bg-success/10 text-success border-success/20',
    'Medium': 'bg-warning/10 text-warning border-warning/20',
    'High': 'bg-destructive/10 text-destructive border-destructive/20'
  }
  return variants[risk] || ''
}

const getRenewalDecisionBadgeClass = (decision) => {
  const variants = {
    'pending': 'bg-yellow-100 text-yellow-800',
    'approved': 'bg-green-100 text-green-800',
    'rejected': 'bg-red-100 text-red-800',
    'extended': 'bg-blue-100 text-blue-800',
    'terminated': 'bg-gray-100 text-gray-800',
    // Handle backend values as well
    'PENDING': 'bg-yellow-100 text-yellow-800',
    'RENEW': 'bg-green-100 text-green-800',
    'RENEGOTIATE': 'bg-green-100 text-green-800',
    'TERMINATE': 'bg-red-100 text-red-800'
  }
  return variants[decision] || ''
}

const getContractByRenewal = (contractId) => {
  return contracts.value.find(contract => contract.contract_id === contractId)
}

const getDaysUntilDue = (dueDate) => {
  const due = new Date(dueDate)
  const today = new Date()
  const daysDiff = Math.ceil((due.getTime() - today.getTime()) / (1000 * 3600 * 24))
  return daysDiff > 0 ? `${daysDiff} days left` : `${Math.abs(daysDiff)} days overdue`
}

const getDaysUntilDueClass = (dueDate) => {
  const due = new Date(dueDate)
  const today = new Date()
  const daysDiff = Math.ceil((due.getTime() - today.getTime()) / (1000 * 3600 * 24))
  
  if (daysDiff < 0) return 'text-xs text-red-600'
  if (daysDiff <= 7) return 'text-xs text-orange-600'
  return 'text-xs text-muted-foreground'
}

const getRiskLevel = (score) => {
  if (score >= 80) return 'High'
  if (score >= 60) return 'Medium'
  return 'Low'
}

const getRiskClass = (score) => {
  if (score >= 80) return 'text-xs text-red-600'
  if (score >= 60) return 'text-xs text-orange-600'
  return 'text-xs text-green-600'
}

const getDecisionText = (decision) => {
  const texts = {
    'pending': 'Pending',
    'approved': 'Approved',
    'rejected': 'Rejected',
    'extended': 'Extended',
    'terminated': 'Terminated',
    // Handle backend values as well
    'PENDING': 'Pending',
    'RENEW': 'Approved',
    'RENEGOTIATE': 'Approved',
    'TERMINATE': 'Rejected'
  }
  return texts[decision] || 'N/A'
}

const getApprovalRate = () => {
  const approved = contractRenewals.value.filter(r => r.renewal_decision === 'approved').length
  return contractRenewals.value.length > 0 ? Math.round((approved / contractRenewals.value.length) * 100) : 0
}

const getRejectionRate = () => {
  const rejected = contractRenewals.value.filter(r => r.renewal_decision === 'rejected').length
  return contractRenewals.value.length > 0 ? Math.round((rejected / contractRenewals.value.length) * 100) : 0
}

// Contract Kind Badge methods
const getContractKindBadgeClass = (contractKind) => {
  const classes = {
    'MAIN': 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800',
    'AMENDMENT': 'bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800',
    'SUBCONTRACT': 'bg-indigo-100 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:border-indigo-800'
  }
  return classes[contractKind] || 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700'
}

// Archive methods
const openArchiveDialog = (contract) => {
  contractToArchive.value = contract
  archiveForm.value = {
    archive_reason: '',
    archive_comments: '',
    can_be_restored: true
  }
  archiveDialogOpen.value = true
}

const closeArchiveDialog = () => {
  archiveDialogOpen.value = false
  contractToArchive.value = null
  archiveForm.value = {
    archive_reason: '',
    archive_comments: '',
    can_be_restored: true
  }
}


const handleArchiveContract = async () => {
  if (!contractToArchive.value || !archiveForm.value.archive_reason) {
    return
  }

  try {
    archiveLoading.value = true
    
    // Create a clean copy of the form data
    const formData = {
      archive_reason: archiveForm.value.archive_reason,
      archive_comments: archiveForm.value.archive_comments || '',
      can_be_restored: archiveForm.value.can_be_restored
    }
    
    const response = await contractsApi.archiveContract(contractToArchive.value.contract_id, formData)
    
    if (response.success) {
      // Remove the contract from the current list
      contracts.value = contracts.value.filter(c => c.contract_id !== contractToArchive.value.contract_id)
      
      // Update pagination
      pagination.value.total_count = Math.max(0, pagination.value.total_count - 1)
      
      // Close dialog
      closeArchiveDialog()
      
      // Show success message (you could add a toast notification here)
      console.log('Contract archived successfully')
    } else {
      throw new Error(response.message || 'Failed to archive contract')
    }
  } catch (error) {
    console.error('Error archiving contract:', error)
    // You could add error handling here (toast notification, etc.)
  } finally {
    archiveLoading.value = false
  }
}

// Activation methods
const openActivateDialog = (contract) => {
  contractToActivate.value = contract
  activateForm.value = {
    activation_comments: '',
    notify_vendor: true
  }
  activateDialogOpen.value = true
}

const closeActivateDialog = () => {
  activateDialogOpen.value = false
  contractToActivate.value = null
  activateForm.value = {
    activation_comments: '',
    notify_vendor: true
  }
}

const handleActivateContract = async () => {
  if (!contractToActivate.value) {
    return
  }

  try {
    activateLoading.value = true
    
    // Create activation data - use ACTIVE (uppercase) as per backend model
    const activationData = {
      status: 'ACTIVE',
      activation_comments: activateForm.value.activation_comments || '',
      notify_vendor: activateForm.value.notify_vendor
    }
    
    // Use PATCH for partial update (only status field)
    const response = await contractsApi.patchContract(contractToActivate.value.contract_id, activationData)
    
    if (response.success) {
      // Update the contract in the current list with backend format
      const contractIndex = contracts.value.findIndex(c => c.contract_id === contractToActivate.value.contract_id)
      if (contractIndex !== -1) {
        contracts.value[contractIndex].status = 'ACTIVE'
      }
      
      // Close dialog
      closeActivateDialog()
      
      // Show success message
      console.log('Contract activated successfully')
    } else {
      throw new Error(response.message || 'Failed to activate contract')
    }
  } catch (error) {
    console.error('Error activating contract:', error)
    // You could add error handling here (toast notification, etc.)
  } finally {
    activateLoading.value = false
  }
}

</script>

