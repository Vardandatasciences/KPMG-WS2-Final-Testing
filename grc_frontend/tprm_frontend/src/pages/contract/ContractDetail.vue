<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
          <Button variant="ghost" size="icon" @click="handleBack" class="hover:bg-white/50 dark:hover:bg-slate-700/50">
          <ArrowLeft class="w-4 h-4" />
        </Button>
          <div class="space-y-1">
            <h1 class="text-3xl font-bold text-foreground">{{ contract?.contract_title || 'Contract Details' }}</h1>
            <div class="flex items-center gap-3 text-muted-foreground">
              <span class="font-mono text-sm bg-white/50 dark:bg-slate-800/50 px-2 py-1 rounded-md">
                {{ contract?.contract_number || 'Loading...' }}
              </span>
              <span class="text-sm">•</span>
              <span class="text-sm font-medium">{{ contract?.vendor?.company_name || '' }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Button variant="outline" class="gap-2 hover:bg-white/50 dark:hover:bg-slate-700/50">
          <Download class="w-4 h-4" />
          Download
        </Button>
          <Button @click="navigate(`/contracts/${contractId}/edit`)" class="gap-2 bg-primary hover:bg-primary/90">
          <Edit class="w-4 h-4" />
            Edit Contract
        </Button>
        </div>
      </div>
    </div>

    <!-- Status Banner -->
    <Card v-if="daysUntilExpiry > 0 && daysUntilExpiry <= 30" class="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 dark:border-amber-800">
      <CardContent class="pt-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center">
            <AlertTriangle class="w-6 h-6 text-amber-600 dark:text-amber-400" />
          </div>
          <div class="flex-1">
            <p class="font-semibold text-amber-800 dark:text-amber-200 text-lg">Contract Expiring Soon</p>
            <p class="text-sm text-amber-700 dark:text-amber-300 mt-1">
              This contract expires in <span class="font-bold">{{ daysUntilExpiry }} days</span>. Consider renewal or termination.
            </p>
          </div>
          <Button size="sm" class="bg-amber-600 hover:bg-amber-700 text-white">
            Start Renewal
          </Button>
        </div>
      </CardContent>
    </Card>

    <Tabs v-model="activeTab" class="space-y-8">
      <TabsList class="grid w-full grid-cols-8 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
        <TabsTrigger value="overview" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Overview</TabsTrigger>
        <TabsTrigger value="terms" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Terms</TabsTrigger>
        <TabsTrigger value="clauses" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Clauses</TabsTrigger>
        <TabsTrigger value="amendments" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Amendments</TabsTrigger>
        <TabsTrigger value="subcontracts" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Subcontracts</TabsTrigger>
        <TabsTrigger value="renewals" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Renewals</TabsTrigger>
        <TabsTrigger value="documents" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Documents</TabsTrigger>
        <TabsTrigger value="timeline" class="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:shadow-sm">Timeline</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" class="space-y-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Basic Information -->
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                  <FileText class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                Primary Information
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Status</span>
                  <Badge :class="getStatusBadgeClass(contract?.status)" class="px-3 py-1 rounded-full text-xs font-medium">
                    {{ contract?.status?.replace('_', ' ') || 'Unknown' }}
                  </Badge>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Type</span>
                  <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ contract?.contract_type || 'Not specified' }}</Badge>
                </div>
                <div class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Priority</span>
                  <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ contract?.priority || 'Not specified' }}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Financial Information -->
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                  <DollarSign class="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                Financial Details
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Contract Value</span>
                  <span class="font-bold text-lg text-green-600 dark:text-green-400">{{ contract?.currency }} {{ contract?.contract_value?.toLocaleString() || '0' }}</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Currency</span>
                  <span class="font-mono text-sm bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{{ contract?.currency || 'N/A' }}</span>
                </div>
                <div class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Auto Renewal</span>
                  <Badge :class="contract?.auto_renewal ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'" class="px-3 py-1 rounded-full text-xs font-medium">
                    {{ contract?.auto_renewal ? 'Yes' : 'No' }}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Dates -->
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                  <Calendar class="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                Important Dates
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Start Date</span>
                  <span class="font-medium">{{ contract?.start_date ? new Date(contract.start_date).toLocaleDateString() : 'Not set' }}</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">End Date</span>
                  <span class="font-medium">{{ contract?.end_date ? new Date(contract.end_date).toLocaleDateString() : 'Not set' }}</span>
                </div>
                <div class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Notice Period</span>
                  <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ contract?.notice_period_days || 0 }} days</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Stakeholders -->
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                  <User class="w-5 h-5 text-orange-600 dark:text-orange-400" />
                </div>
                Stakeholders
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Owner</span>
                  <span class="font-medium text-sm bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">{{ contract?.contract_owner_username || 'Not assigned' }}</span>
                </div>
                <div v-if="contract?.legal_reviewer_username" class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Legal Reviewer</span>
                  <span class="font-medium text-sm bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">{{ contract.legal_reviewer_username }}</span>
                </div>
                <div v-else class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Legal Reviewer</span>
                  <span class="text-sm text-muted-foreground italic">Not assigned</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Vendor Information -->
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                  <Building class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                Vendor Details
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Vendor</span>
                  <span class="font-medium text-sm bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">{{ contract?.vendor?.company_name || 'Not specified' }}</span>
                </div>
                <div class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Vendor ID</span>
                  <span class="text-xs font-mono bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
                    {{ contract?.vendor_id || contract?.vendor?.vendor_id || 'Not available' }}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Compliance -->
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
                  <Shield class="w-5 h-5 text-red-600 dark:text-red-400" />
                </div>
                Compliance
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Framework</span>
                <div class="flex flex-wrap gap-1">
                  <Badge 
                      v-if="contract?.compliance_framework" 
                    variant="secondary" 
                      class="text-xs px-3 py-1 rounded-full font-medium"
                  >
                      {{ contract.compliance_framework }}
                  </Badge>
                    <span v-else class="text-xs text-muted-foreground italic">
                    None specified
                  </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="terms" class="space-y-8">
        <div>
          <h3 class="text-2xl font-bold text-foreground">Contract Terms</h3>
          <p class="text-muted-foreground mt-1">Financial obligations and payment terms</p>
        </div>

        <div class="grid gap-6">
          <Card v-for="term in contractTerms" :key="term.term_id" class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardContent class="pt-6">
              <div class="space-y-4">
                <div class="flex items-center gap-3 flex-wrap">
                  <h4 class="font-semibold text-lg">{{ term.term_title || 'Untitled Term' }}</h4>
                  <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ term.term_category || 'General' }}</Badge>
                  <Badge v-if="term.is_standard" variant="secondary" class="px-3 py-1 rounded-full text-xs font-medium">Standard</Badge>
                </div>
                <p class="text-sm text-foreground leading-relaxed bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
                  {{ term.term_text }}
                </p>
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-muted-foreground">Risk Level:</span>
                  <Badge :class="getRiskBadgeClass(term.risk_level)" class="px-3 py-1 rounded-full text-xs font-medium">{{ term.risk_level || 'Unknown' }}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card v-if="!contractTerms.length" class="border-dashed border-2 border-slate-200 dark:border-slate-700">
            <CardContent class="text-center py-16">
              <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText class="h-8 w-8 text-slate-400" />
              </div>
              <h3 class="text-lg font-semibold text-foreground mb-2">No terms defined</h3>
              <p class="text-muted-foreground max-w-md mx-auto">
                Contract terms will appear here when they are defined.
              </p>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="clauses" class="space-y-8">
        <div>
          <h3 class="text-2xl font-bold text-foreground">Contract Clauses</h3>
          <p class="text-muted-foreground mt-1">Legal terms and conditions</p>
        </div>

        <div class="grid gap-6">
          <Card v-for="clause in contractClauses" :key="clause.clause_id" class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardContent class="pt-6">
              <div class="space-y-4">
                <div class="flex items-center gap-3 flex-wrap">
                  <h4 class="font-semibold text-lg">{{ clause.clause_name || 'Untitled Clause' }}</h4>
                  <Badge 
                    variant="outline"
                    :class="getClauseRiskClass(clause.risk_level)"
                    class="px-3 py-1 rounded-full text-xs font-medium"
                  >
                    {{ clause.risk_level || 'Unknown' }} Risk
                  </Badge>
                  <Badge v-if="clause.legal_category" variant="secondary" class="px-3 py-1 rounded-full text-xs font-medium">
                    {{ clause.legal_category }}
                  </Badge>
                </div>
                
                <p class="text-sm text-foreground leading-relaxed bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
                  {{ clause.clause_text }}
                </p>
                
                <div class="flex items-center gap-4 text-xs text-muted-foreground">
                  <div class="flex items-center gap-1">
                    <span class="font-medium">Type:</span>
                    <span class="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{{ clause.clause_type || 'General' }}</span>
                  </div>
                  <div v-if="clause.is_standard" class="flex items-center gap-1">
                    <span class="font-medium">Standard Clause</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card v-if="!contractClauses.length" class="border-dashed border-2 border-slate-200 dark:border-slate-700">
            <CardContent class="text-center py-16">
              <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield class="h-8 w-8 text-slate-400" />
              </div>
              <h3 class="text-lg font-semibold text-foreground mb-2">No clauses defined</h3>
              <p class="text-muted-foreground max-w-md mx-auto">
                Contract clauses will appear here when they are defined.
              </p>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="amendments" class="space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h3 class="text-2xl font-bold text-foreground">Contract Amendments</h3>
            <p class="text-muted-foreground mt-1">Modifications and updates to this contract</p>
          </div>
          <Button class="gap-2 bg-primary hover:bg-primary/90" @click="navigate(`/contracts/${contractId}/create-amendment`)">
            <Edit class="w-4 h-4" />
            Create Amendment
          </Button>
        </div>

        <!-- Contract Amendments List -->
        <div v-if="contractAmendments.length > 0" class="grid gap-6">
          <Card v-for="amendment in contractAmendments" :key="amendment.contract_id" class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardContent class="pt-6">
              <div class="flex justify-between items-start">
                <div class="space-y-4 flex-1">
                  <!-- Header -->
                  <div class="flex items-center gap-3 flex-wrap">
                    <h4 class="font-semibold text-lg">{{ amendment.contract_title || 'Untitled Amendment' }}</h4>
                    <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ amendment.contract_type || 'Amendment' }}</Badge>
                    <Badge :class="getStatusBadgeClass(amendment.status)" class="px-3 py-1 rounded-full text-xs font-medium">
                      {{ amendment.status?.replace('_', ' ') || 'Unknown' }}
                    </Badge>
                    <Badge variant="secondary" class="px-3 py-1 rounded-full text-xs font-medium">
                      v{{ amendment.version_number || '1.0' }}
                    </Badge>
                    <Badge v-if="amendment.file_path" class="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 flex items-center gap-1">
                      <FileText class="w-3 h-3" />
                      Document
                    </Badge>
                  </div>
                  
                  <!-- Contract Number -->
                  <div class="text-sm font-mono bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-md w-fit">
                    {{ amendment.contract_number || 'No contract number' }}
                  </div>
                  
                  <!-- Key Information Grid -->
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                    <!-- Financial Info -->
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Value:</span>
                        <span class="font-medium text-green-600 dark:text-green-400">
                          {{ amendment.currency }} {{ amendment.contract_value?.toLocaleString() || '0' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Priority:</span>
                        <Badge variant="outline" class="text-xs">{{ amendment.priority || 'Medium' }}</Badge>
                      </div>
                    </div>
                    
                    <!-- Dates -->
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Start:</span>
                        <span class="font-medium">{{ amendment.start_date ? new Date(amendment.start_date).toLocaleDateString() : 'Not set' }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">End:</span>
                        <span class="font-medium">{{ amendment.end_date ? new Date(amendment.end_date).toLocaleDateString() : 'Not set' }}</span>
                      </div>
                    </div>
                    
                    <!-- Amendment Info -->
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Parent Contract:</span>
                        <span class="font-medium">{{ amendment.parent_contract_id || 'N/A' }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Auto Renewal:</span>
                        <Badge :class="amendment.auto_renewal ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'" class="text-xs">
                          {{ amendment.auto_renewal ? 'Yes' : 'No' }}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Terms and Clauses Summary -->
                  <div v-if="amendment.terms_count || amendment.clauses_count" class="flex items-center gap-4 text-xs text-muted-foreground bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                    <div v-if="amendment.terms_count" class="flex items-center gap-1">
                      <DollarSign class="w-3 h-3" />
                      <span>{{ amendment.terms_count }} terms</span>
                    </div>
                    <div v-if="amendment.clauses_count" class="flex items-center gap-1">
                      <Shield class="w-3 h-3" />
                      <span>{{ amendment.clauses_count }} clauses</span>
                    </div>
                  </div>
                  
                  <!-- Description -->
                  <div v-if="amendment.description" class="text-sm text-foreground leading-relaxed bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
                    {{ amendment.description }}
                  </div>
                </div>
                
                <!-- Actions -->
                <div class="flex flex-col gap-2 ml-4">
                  <Button variant="ghost" size="sm" @click="navigate(`/contracts/${amendment.contract_id}`)" class="hover:bg-slate-100 dark:hover:bg-slate-700" title="View Amendment Details">
                    <Eye class="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm" @click="navigate(`/contracts/${amendment.contract_id}/edit-advanced`)" class="hover:bg-slate-100 dark:hover:bg-slate-700" title="Edit Amendment">
                    <Edit class="w-4 h-4" />
                  </Button>
                  <Button v-if="amendment.file_path" variant="ghost" size="sm" @click="downloadDocument(amendment.file_path)" class="hover:bg-slate-100 dark:hover:bg-slate-700" title="Download Amendment Document">
                    <Download class="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <!-- Expandable Terms and Clauses -->
              <div v-if="amendment.terms && amendment.terms.length > 0" class="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
                <details class="group">
                  <summary class="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2">
                    <DollarSign class="w-4 h-4" />
                    Contract Terms ({{ amendment.terms.length }})
                    <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div class="mt-3 space-y-2">
                    <div v-for="term in amendment.terms" :key="term.term_id" class="text-xs bg-white dark:bg-slate-900 p-3 rounded border">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium">{{ term.term_title }}</span>
                        <Badge variant="outline" class="text-xs">{{ term.term_category }}</Badge>
                        <Badge v-if="term.risk_level" :class="getRiskBadgeClass(term.risk_level)" class="text-xs">{{ term.risk_level }}</Badge>
                      </div>
                      <p class="text-muted-foreground">{{ term.term_text }}</p>
                    </div>
                  </div>
                </details>
              </div>
              
              <div v-if="amendment.clauses && amendment.clauses.length > 0" class="mt-4">
                <details class="group">
                  <summary class="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2">
                    <Shield class="w-4 h-4" />
                    Contract Clauses ({{ amendment.clauses.length }})
                    <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div class="mt-3 space-y-2">
                    <div v-for="clause in amendment.clauses" :key="clause.clause_id" class="text-xs bg-white dark:bg-slate-900 p-3 rounded border">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium">{{ clause.clause_name }}</span>
                        <Badge variant="outline" class="text-xs">{{ clause.clause_type }}</Badge>
                        <Badge v-if="clause.risk_level" :class="getClauseRiskClass(clause.risk_level)" class="text-xs">{{ clause.risk_level }} Risk</Badge>
                      </div>
                      <p class="text-muted-foreground">{{ clause.clause_text }}</p>
                    </div>
                  </div>
                </details>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Empty State -->
        <Card v-else class="border-dashed border-2 border-slate-200 dark:border-slate-700">
          <CardContent class="text-center py-16">
            <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Edit class="h-8 w-8 text-slate-400" />
            </div>
            <h3 class="text-lg font-semibold text-foreground mb-2">No amendments created</h3>
            <p class="text-muted-foreground mb-6 max-w-md mx-auto">
              Create amendments to modify existing contract terms and conditions.
            </p>
            <Button class="gap-2 bg-primary hover:bg-primary/90" @click="navigate(`/contracts/${contractId}/create-amendment`)">
              <Edit class="w-4 h-4" />
              Create First Amendment
            </Button>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="subcontracts" class="space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h3 class="text-2xl font-bold text-foreground">Subcontracts</h3>
            <p class="text-muted-foreground mt-1">Work delegated to third parties under this contract</p>
          </div>
          <Button class="gap-2 bg-primary hover:bg-primary/90" @click="navigate(`/contracts/${contractId}/subcontract`)">
            <FileText class="w-4 h-4" />
            Add Subcontract
          </Button>
        </div>

        <!-- Subcontracts List -->
        <div v-if="subcontracts.length > 0" class="grid gap-6">
          <Card v-for="subcontract in subcontracts" :key="subcontract.contract_id" class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <!-- Permission Denied Card -->
            <CardContent v-if="subcontract.permission_denied" class="pt-6">
              <div class="flex items-start gap-4">
                <div class="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Shield class="w-6 h-6 text-amber-600 dark:text-amber-400" />
                </div>
                <div class="flex-1 space-y-3">
                  <!-- Header -->
                  <div class="space-y-2">
                    <div class="flex items-center gap-3 flex-wrap">
                      <h4 class="font-semibold text-lg text-foreground">{{ subcontract.contract_title || 'Untitled Subcontract' }}</h4>
                      <Badge :class="getStatusBadgeClass(subcontract.status)" class="px-3 py-1 rounded-full text-xs font-medium">
                        {{ subcontract.status?.replace('_', ' ') || 'Unknown' }}
                      </Badge>
                      <Badge class="px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                        <Shield class="w-3 h-3 mr-1" />
                        Restricted Access
                      </Badge>
                    </div>
                    
                    <div class="text-sm font-mono bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-md w-fit">
                      {{ subcontract.contract_number || 'No contract number' }}
                    </div>
                  </div>
                  
                  <!-- Permission Message -->
                  <div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                    <div class="flex items-start gap-3">
                      <AlertTriangle class="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                      <div class="space-y-1">
                        <p class="font-medium text-amber-800 dark:text-amber-200">Access Restricted</p>
                        <p class="text-sm text-amber-700 dark:text-amber-300">
                          {{ subcontract.permission_message || 'You do not have permission to view the details of this subcontract.' }}
                        </p>
                        <p class="text-xs text-amber-600 dark:text-amber-400 mt-2">
                          Contact the contract administrator if you need access to this subcontract.
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Limited Information -->
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm pt-2">
                    <div class="flex justify-between items-center">
                      <span class="text-muted-foreground">Contract ID:</span>
                      <span class="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{{ subcontract.contract_id }}</span>
                    </div>
                    <div v-if="subcontract.created_at" class="flex justify-between items-center">
                      <span class="text-muted-foreground">Created:</span>
                      <span class="text-xs">{{ new Date(subcontract.created_at).toLocaleDateString() }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
            
            <!-- Full Details Card (Permission Granted) -->
            <CardContent v-else class="pt-6">
              <div class="flex justify-between items-start">
                <div class="space-y-4 flex-1">
                  <!-- Header -->
                  <div class="flex items-center gap-3 flex-wrap">
                    <h4 class="font-semibold text-lg">{{ subcontract.contract_title || 'Untitled Subcontract' }}</h4>
                    <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ subcontract.contract_type || 'Subcontract' }}</Badge>
                    <Badge :class="getStatusBadgeClass(subcontract.status)" class="px-3 py-1 rounded-full text-xs font-medium">
                      {{ subcontract.status?.replace('_', ' ') || 'Unknown' }}
                    </Badge>
                    <Badge v-if="subcontract.file_path" class="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 flex items-center gap-1">
                      <FileText class="w-3 h-3" />
                      Document
                    </Badge>
                  </div>
                  
                  <!-- Contract Number -->
                  <div class="text-sm font-mono bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-md w-fit">
                    {{ subcontract.contract_number || 'No contract number' }}
                  </div>
                  
                  <!-- Key Information Grid -->
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                    <!-- Financial Info -->
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Value:</span>
                        <span class="font-medium text-green-600 dark:text-green-400">
                          {{ subcontract.currency }} {{ subcontract.contract_value?.toLocaleString() || '0' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Priority:</span>
                        <Badge variant="outline" class="text-xs">{{ subcontract.priority || 'Medium' }}</Badge>
                      </div>
                    </div>
                    
                    <!-- Dates -->
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Start:</span>
                        <span class="font-medium">{{ subcontract.start_date ? new Date(subcontract.start_date).toLocaleDateString() : 'Not set' }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">End:</span>
                        <span class="font-medium">{{ subcontract.end_date ? new Date(subcontract.end_date).toLocaleDateString() : 'Not set' }}</span>
                      </div>
                    </div>
                    
                    <!-- Vendor Info -->
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Vendor:</span>
                        <span class="font-medium">{{ subcontract.vendor?.company_name || 'Not specified' }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-muted-foreground">Auto Renewal:</span>
                        <Badge :class="subcontract.auto_renewal ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'" class="text-xs">
                          {{ subcontract.auto_renewal ? 'Yes' : 'No' }}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Terms and Clauses Summary -->
                  <div v-if="subcontract.terms_count || subcontract.clauses_count" class="flex items-center gap-4 text-xs text-muted-foreground bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                    <div v-if="subcontract.terms_count" class="flex items-center gap-1">
                      <DollarSign class="w-3 h-3" />
                      <span>{{ subcontract.terms_count }} terms</span>
                    </div>
                    <div v-if="subcontract.clauses_count" class="flex items-center gap-1">
                      <Shield class="w-3 h-3" />
                      <span>{{ subcontract.clauses_count }} clauses</span>
                    </div>
                  </div>
                  
                  <!-- Description -->
                  <div v-if="subcontract.description" class="text-sm text-foreground leading-relaxed bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
                    {{ subcontract.description }}
                  </div>
                </div>
                
                <!-- Actions -->
                <div class="flex flex-col gap-2 ml-4">
                  <Button variant="ghost" size="sm" @click="navigate(`/contracts/${subcontract.contract_id}`)" class="hover:bg-slate-100 dark:hover:bg-slate-700" title="View Subcontract Details">
                    <Eye class="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm" @click="navigate(`/contracts/${subcontract.contract_id}/edit-advanced`)" class="hover:bg-slate-100 dark:hover:bg-slate-700" title="Edit Subcontract">
                    <Edit class="w-4 h-4" />
                  </Button>
                  <Button v-if="subcontract.file_path" variant="ghost" size="sm" @click="downloadDocument(subcontract.file_path)" class="hover:bg-slate-100 dark:hover:bg-slate-700" title="Download Subcontract Document">
                    <Download class="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <!-- Expandable Terms and Clauses -->
              <div v-if="subcontract.terms && subcontract.terms.length > 0" class="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
                <details class="group">
                  <summary class="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2">
                    <DollarSign class="w-4 h-4" />
                    Contract Terms ({{ subcontract.terms.length }})
                    <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div class="mt-3 space-y-2">
                    <div v-for="term in subcontract.terms" :key="term.term_id" class="text-xs bg-white dark:bg-slate-900 p-3 rounded border">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium">{{ term.term_title }}</span>
                        <Badge variant="outline" class="text-xs">{{ term.term_category }}</Badge>
                        <Badge v-if="term.risk_level" :class="getRiskBadgeClass(term.risk_level)" class="text-xs">{{ term.risk_level }}</Badge>
                      </div>
                      <p class="text-muted-foreground">{{ term.term_text }}</p>
                    </div>
                  </div>
                </details>
              </div>
              
              <div v-if="subcontract.clauses && subcontract.clauses.length > 0" class="mt-4">
                <details class="group">
                  <summary class="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2">
                    <Shield class="w-4 h-4" />
                    Contract Clauses ({{ subcontract.clauses.length }})
                    <svg class="w-4 h-4 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div class="mt-3 space-y-2">
                    <div v-for="clause in subcontract.clauses" :key="clause.clause_id" class="text-xs bg-white dark:bg-slate-900 p-3 rounded border">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-medium">{{ clause.clause_name }}</span>
                        <Badge variant="outline" class="text-xs">{{ clause.clause_type }}</Badge>
                        <Badge v-if="clause.risk_level" :class="getClauseRiskClass(clause.risk_level)" class="text-xs">{{ clause.risk_level }} Risk</Badge>
                      </div>
                      <p class="text-muted-foreground">{{ clause.clause_text }}</p>
                    </div>
                  </div>
                </details>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Empty State -->
        <Card v-else class="border-dashed border-2 border-slate-200 dark:border-slate-700">
          <CardContent class="text-center py-16">
            <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText class="h-8 w-8 text-slate-400" />
            </div>
            <h3 class="text-lg font-semibold text-foreground mb-2">No subcontracts created</h3>
            <p class="text-muted-foreground mb-6 max-w-md mx-auto">
              Add subcontracts to track work delegated to third parties under this main contract.
            </p>
            <Button class="gap-2 bg-primary hover:bg-primary/90" @click="navigate(`/contracts/${contractId}/subcontract`)">
              <FileText class="w-4 h-4" />
              Add First Subcontract
            </Button>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="renewals" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Renewal History</h3>
          <Button class="gap-2">
            <RefreshCw class="w-4 h-4" />
            Start Renewal
          </Button>
        </div>

        <div class="grid gap-4">
          <Card v-for="renewal in contractRenewals" :key="renewal.id">
            <CardContent class="pt-6">
              <div class="space-y-4">
                <div class="flex justify-between items-start">
                  <div>
                    <h4 class="font-semibold">Renewal Process</h4>
                    <p class="text-sm text-muted-foreground">
                      Due: {{ new Date(renewal.decision_due_date).toLocaleDateString() }}
                    </p>
                  </div>
                  <Badge 
                    :class="getRenewalDecisionClass(renewal.decision)"
                  >
                    {{ renewal.decision }}
                  </Badge>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-muted-foreground">Assigned to:</span>
                    <p class="font-medium">{{ renewal.assigned_approver }}</p>
                  </div>
                  <div>
                    <span class="text-muted-foreground">Renewal Date:</span>
                    <p>{{ new Date(renewal.renewal_date).toLocaleDateString() }}</p>
                  </div>
                </div>
                <div v-if="renewal.comments">
                  <span class="text-sm text-muted-foreground">Comments:</span>
                  <p class="text-sm mt-1">{{ renewal.comments }}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card v-if="!contractRenewals.length">
            <CardContent class="text-center py-12">
              <RefreshCw class="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 class="mt-2 text-sm font-semibold">No renewal history</h3>
              <p class="mt-1 text-sm text-muted-foreground">
                Track renewal decisions and processes here.
              </p>
              <Button class="mt-4">Start Renewal Process</Button>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="documents" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Contract Documents</h3>
        </div>

        <!-- Document Link Display -->
        <div v-if="contract?.file_path && documentInfo" class="space-y-4">
          <Card class="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-700">
            <CardHeader class="pb-4">
              <CardTitle class="flex items-center gap-3 text-lg">
                <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                  <FileText class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                Contract Document
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-3">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Document Type</span>
                  <Badge variant="outline" class="px-3 py-1 rounded-full text-xs font-medium">{{ documentInfo?.type || 'Unknown' }}</Badge>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Filename</span>
                  <span class="text-sm font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{{ documentInfo?.filename || 'Unknown' }}</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-sm font-medium text-muted-foreground">Storage</span>
                  <Badge variant="secondary" class="px-3 py-1 rounded-full text-xs font-medium">Cloud Storage (S3)</Badge>
                </div>
                <div v-if="documentInfo?.uploadedAt" class="flex justify-between items-center py-2">
                  <span class="text-sm font-medium text-muted-foreground">Uploaded</span>
                  <span class="text-sm">{{ new Date(documentInfo.uploadedAt).toLocaleDateString() }}</span>
                </div>
                <div class="py-2">
                  <span class="text-sm font-medium text-muted-foreground block mb-2">Document URL</span>
                  <div class="flex items-center gap-2 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <FileText class="w-4 h-4 text-slate-500" />
                    <span class="text-sm font-mono text-slate-600 dark:text-slate-400 flex-1 truncate" :title="contract.file_path">
                      {{ contract.file_path }}
                    </span>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      @click="copyToClipboard(contract.file_path)"
                      class="hover:bg-slate-200 dark:hover:bg-slate-700"
                      title="Copy URL"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </Button>
                  </div>
                </div>
              </div>
              
              <!-- Action Buttons -->
              <div class="flex gap-3 pt-4 border-t border-slate-100 dark:border-slate-700 justify-center">
                <Button 
                  @click="openDocument(contract.file_path)" 
                  class="gap-2 bg-primary hover:bg-primary/90 w-auto px-6"
                >
                  <Eye class="w-4 h-4" />
                  View Document
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Loading State for Document -->
        <Card v-else-if="contract?.file_path && !documentInfo" class="border-slate-200 dark:border-slate-700">
          <CardContent class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary/20 border-t-primary mx-auto mb-4"></div>
            <h3 class="text-sm font-semibold">Loading document information...</h3>
          </CardContent>
        </Card>

        <!-- No Document State -->
        <Card v-else class="border-dashed border-2 border-slate-200 dark:border-slate-700">
          <CardContent class="text-center py-12">
            <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 class="mt-2 text-sm font-semibold">No document uploaded</h3>
            <p class="mt-1 text-sm text-muted-foreground">
              This contract doesn't have an associated document yet.
            </p>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="timeline" class="space-y-6">
        <h3 class="text-lg font-semibold">Contract Timeline</h3>

        <div class="space-y-4">
          <Card>
            <CardContent class="pt-6">
              <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-success rounded-full mt-2"></div>
                <div>
                  <p class="font-medium">Contract Created</p>
                  <p class="text-sm text-muted-foreground">
                    {{ contract?.created_at ? new Date(contract.created_at).toLocaleDateString() : '' }} 
                    at {{ contract?.created_at ? new Date(contract.created_at).toLocaleTimeString() : '' }}
                  </p>
                  <p class="text-sm text-muted-foreground">Created by {{ contract?.contract_owner_username || 'Unknown' }}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent class="pt-6">
              <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-primary rounded-full mt-2"></div>
                <div>
                  <p class="font-medium">Last Updated</p>
                  <p class="text-sm text-muted-foreground">
                    {{ contract?.updated_at ? new Date(contract.updated_at).toLocaleDateString() : '' }} 
                    at {{ contract?.updated_at ? new Date(contract.updated_at).toLocaleTimeString() : '' }}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent class="pt-6">
              <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-muted rounded-full mt-2"></div>
                <div>
                  <p class="font-medium">Contract Started</p>
                  <p class="text-sm text-muted-foreground">
                    {{ contract?.start_date ? new Date(contract.start_date).toLocaleDateString() : '' }}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
      <div class="relative">
        <div class="animate-spin rounded-full h-16 w-16 border-4 border-primary/20 border-t-primary"></div>
        <div class="absolute inset-0 flex items-center justify-center">
          <FileText class="h-6 w-6 text-primary animate-pulse" />
        </div>
      </div>
      <h3 class="mt-6 text-xl font-semibold text-foreground">Loading Contract Details</h3>
      <p class="mt-2 text-muted-foreground text-center max-w-md">
        Please wait while we fetch the contract information and related data.
      </p>
      <div class="mt-4 flex space-x-1">
        <div class="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
        <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
        <div class="w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
      <div class="w-20 h-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-6">
        <AlertTriangle class="h-10 w-10 text-red-500" />
      </div>
      <h3 class="text-xl font-semibold text-foreground mb-2">Error Loading Contract</h3>
      <p class="text-muted-foreground text-center max-w-md mb-6">
        {{ error }}
      </p>
      <div class="flex gap-3">
        <Button variant="outline" @click="window.location.reload()" class="gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Try Again
        </Button>
        <Button @click="handleBack" class="gap-2">
          <FileText class="w-4 h-4" />
          Back to {{ route.query.returnTo === 'vendor-contracts' ? 'Vendor Contracts' : 'Contracts' }}
        </Button>
      </div>
    </div>

    <!-- Contract Not Found -->
    <div v-else-if="!contract" class="flex flex-col items-center justify-center py-20">
      <div class="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-6">
        <FileText class="h-10 w-10 text-slate-400" />
      </div>
      <h3 class="text-xl font-semibold text-foreground mb-2">Contract Not Found</h3>
      <p class="text-muted-foreground text-center max-w-md mb-6">
        The contract you're looking for doesn't exist or has been removed.
      </p>
      <Button @click="handleBack" class="gap-2">
        <FileText class="w-4 h-4" />
        Back to {{ route.query.returnTo === 'vendor-contracts' ? 'Vendor Contracts' : 'Contracts' }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Tabs, TabsContent, TabsList, TabsTrigger
} from '@/components/ui_contract'
import { 
  ArrowLeft, Edit, Download, FileText, Calendar, DollarSign, Building, User, Shield, 
  Clock, AlertTriangle, CheckCircle, RefreshCw, Eye
} from 'lucide-vue-next'
import contractsApi from '../../services/contractsApi'

const route = useRoute()
const router = useRouter()
const navigate = (path) => router.push(path)

const contractId = route.params.id

// Determine where to navigate back to based on query parameter
const getBackPath = () => {
  const returnTo = route.query.returnTo
  if (returnTo === 'vendor-contracts') {
    return '/vendors'
  }
  return '/contracts'
}

const handleBack = () => {
  navigate(getBackPath())
}

// Safeguard: If contractId is "new" or "create", redirect to create page
// This prevents ContractDetail from trying to load a contract with ID "new" or "create"
if (contractId === 'new' || contractId === 'create') {
  console.log('⚠️ Invalid contract ID detected (new/create), redirecting to create page')
  router.replace('/contracts/create')
}

const activeTab = ref('overview')

// State
const contract = ref(null)
const contractTerms = ref([])
const contractRenewals = ref([])
const contractClauses = ref([])
const subcontracts = ref([])
const contractAmendments = ref([])
const isLoading = ref(true)
const error = ref(null)

const daysUntilExpiry = computed(() => {
  if (!contract.value?.end_date) return 0
  const today = new Date()
  const expiry = new Date(contract.value.end_date)
  return Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 3600 * 24))
})

// Document information computed property
const documentInfo = computed(() => {
  if (!contract.value?.file_path) return null
  
  return {
    url: contract.value.file_path,
    type: getDocumentType(contract.value.file_path),
    filename: (() => {
      try {
        const urlObj = new URL(contract.value.file_path)
        const pathname = urlObj.pathname
        return pathname.split('/').pop() || 'document'
      } catch (e) {
        return 'document'
      }
    })(),
    uploadedAt: contract.value.created_at || contract.value.updated_at
  }
})

// Methods
const getStatusBadgeClass = (status) => {
  const variants = {
    'ACTIVE': 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium',
    'DRAFT': 'bg-slate-50 text-slate-700 border border-slate-200 font-medium',
    'UNDER_REVIEW': 'bg-amber-50 text-amber-800 border border-amber-200 font-medium',
    'EXPIRED': 'bg-red-50 text-red-700 border border-red-200 font-medium',
    'TERMINATED': 'bg-red-50 text-red-700 border border-red-200 font-medium',
    'RENEWED': 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium',
    'PENDING': 'bg-blue-50 text-blue-700 border border-blue-200 font-medium'
  }
  
  return variants[status] || 'bg-slate-50 text-slate-700 border border-slate-200 font-medium'
}

const getRiskBadgeClass = (risk) => {
  const variants = {
    'low': 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium',
    'medium': 'bg-amber-50 text-amber-700 border border-amber-200 font-medium',
    'high': 'bg-red-50 text-red-700 border border-red-200 font-medium',
    'urgent': 'bg-red-50 text-red-700 border border-red-200 font-medium'
  }
  
  return variants[risk] || 'bg-slate-50 text-slate-700 border border-slate-200 font-medium'
}

const getClauseRiskClass = (risk) => {
  if (risk === 'high' || risk === 'High') return 'border-red-200 text-red-700 bg-red-50'
  if (risk === 'medium' || risk === 'Medium') return 'border-amber-200 text-amber-700 bg-amber-50'
  return 'border-emerald-200 text-emerald-700 bg-emerald-50'
}

const getRenewalDecisionClass = (decision) => {
  if (decision === 'Renew') return 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium'
  if (decision === 'Terminate') return 'bg-red-50 text-red-700 border border-red-200 font-medium'
  return 'bg-amber-50 text-amber-700 border border-amber-200 font-medium'
}

// Document handling methods
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    // You could add a toast notification here
    console.log('URL copied to clipboard:', text)
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}

const openDocument = (url) => {
  if (url) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

const downloadDocument = (url) => {
  if (url) {
    // Extract filename from URL or create a default one
    const getFilenameFromUrl = (url) => {
      try {
        const urlObj = new URL(url)
        const pathname = urlObj.pathname
        const filename = pathname.split('/').pop()
        return filename || `contract-${contractId}-document.pdf`
      } catch (e) {
        return `contract-${contractId}-document.pdf`
      }
    }
    
    const filename = getFilenameFromUrl(url)
    
    // Create a temporary anchor element to trigger download
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

// Helper method to get document type from URL
const getDocumentType = (url) => {
  if (!url) return 'Unknown'
  
  try {
    const urlObj = new URL(url)
    const pathname = urlObj.pathname.toLowerCase()
    
    if (pathname.includes('.pdf')) return 'PDF Document'
    if (pathname.includes('.doc') || pathname.includes('.docx')) return 'Word Document'
    if (pathname.includes('.txt')) return 'Text Document'
    if (pathname.includes('.jpg') || pathname.includes('.jpeg')) return 'JPEG Image'
    if (pathname.includes('.png')) return 'PNG Image'
    if (pathname.includes('.tiff') || pathname.includes('.tif')) return 'TIFF Image'
    
    return 'Document'
  } catch (e) {
    return 'Document'
  }
}

onMounted(async () => {
  console.log('ContractDetail mounted with ID:', contractId, 'Type:', typeof contractId)
  
  try {
    isLoading.value = true
    error.value = null
    
    // Load contract data, terms, clauses, renewals, subcontracts, and amendments in parallel
    console.log(`[CONTRACT DETAIL] Loading data for contract ID: ${contractId} (type: ${typeof contractId})`)
    console.log(`[CONTRACT DETAIL] About to call getContractAmendments with: ${contractId}`)
    
    const [contractResponse, termsResponse, clausesResponse, renewalsResponse, subcontractsResponse, amendmentsResponse] = await Promise.all([
      contractsApi.getContract(contractId),
      contractsApi.getContractTerms(contractId),
      contractsApi.getContractClauses(contractId),
      contractsApi.getContractRenewals(),
      contractsApi.getSubcontracts(contractId),
      contractsApi.getContractAmendmentsAsContracts(contractId)
    ])
    
    console.log(`[CONTRACT DETAIL] All API calls completed. Amendments response:`, amendmentsResponse)
    
    // Set contract data
    if (contractResponse.success) {
      contract.value = contractResponse.data
      console.log('Contract loaded:', contract.value)
      console.log('Vendor ID from contract:', contract.value?.vendor_id)
      console.log('Vendor data from contract:', contract.value?.vendor)
    } else {
      error.value = contractResponse.message || 'Failed to load contract'
      return
    }
    
    // Set contract terms
    if (termsResponse.success) {
      contractTerms.value = termsResponse.data
      console.log('Contract terms loaded:', contractTerms.value)
    }
    
    // Set contract clauses
    if (clausesResponse.success) {
      contractClauses.value = clausesResponse.data
      console.log('Contract clauses loaded:', contractClauses.value)
    }
    
    // Set contract renewals (filter by contract ID)
    if (renewalsResponse.success) {
      contractRenewals.value = renewalsResponse.data.filter(r => r.contract_id == contractId)
      console.log('Contract renewals loaded:', contractRenewals.value)
    }
    
    // Set subcontracts
    if (subcontractsResponse.success) {
      subcontracts.value = subcontractsResponse.data || []
      console.log('Subcontracts loaded:', subcontracts.value)
      console.log('Subcontracts summary:', subcontractsResponse.summary)
    }
    
    // Set contract amendments
    console.log(`[CONTRACT DETAIL] Processing amendments response:`, amendmentsResponse)
    console.log(`[CONTRACT DETAIL] Amendments response type:`, typeof amendmentsResponse)
    console.log(`[CONTRACT DETAIL] Amendments response success:`, amendmentsResponse?.success)
    console.log(`[CONTRACT DETAIL] Amendments response data:`, amendmentsResponse?.data)
    
    if (amendmentsResponse && amendmentsResponse.success) {
      contractAmendments.value = amendmentsResponse.data || []
      console.log('Contract amendments loaded:', contractAmendments.value)
      console.log('Contract amendments summary:', amendmentsResponse.summary)
    } else {
      console.error('Failed to load contract amendments:', amendmentsResponse?.message || 'Unknown error')
      console.error('Amendments response:', amendmentsResponse)
      
      // Set empty array as fallback to prevent UI errors
      contractAmendments.value = []
    }
    
  } catch (err) {
    console.error('Error loading contract data:', err)
    error.value = err.message || 'Failed to load contract data'
  } finally {
    isLoading.value = false
  }
})
</script>
