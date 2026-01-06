<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button @click="navigate('/contracts')" class="p-2 hover:bg-muted rounded-md">
          <ArrowLeft class="w-4 h-4" />
        </button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">Contract Details</h1>
          <p class="text-muted-foreground">View contract information and manage amendments</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="navigate('/contracts')" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
          <ArrowLeft class="w-4 h-4" />
          Back to Contracts
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <h3 class="mt-2 text-sm font-semibold text-foreground">Loading contract...</h3>
    </div>

    <div v-else-if="error" class="text-center py-12">
      <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 class="mt-2 text-sm font-semibold text-foreground">Error loading contract</h3>
      <p class="mt-1 text-sm text-muted-foreground">{{ error }}</p>
      <div class="mt-6">
        <button @click="loadContract()" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
          Retry
        </button>
        <button @click="navigate('/contracts')" class="ml-2 px-4 py-2 border rounded-md hover:bg-muted">
          Back to Contracts
        </button>
      </div>
    </div>

    <div v-else-if="!contract" class="text-center py-12">
      <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 class="mt-2 text-sm font-semibold text-foreground">Contract not found</h3>
      <p class="mt-1 text-sm text-muted-foreground">
        The contract you're looking for doesn't exist.
      </p>
      <div class="mt-6">
        <button @click="navigate('/contracts')" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
          Back to Contracts
        </button>
      </div>
    </div>

    <div v-else>
      <!-- All Contract Information in Single Page -->
      <div class="space-y-8">
          <!-- Basic Information Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Basic Information
              </h3>
              <p class="text-sm text-muted-foreground">Update the fundamental contract details</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Title</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.contract_title || 'N/A' }}
                  </div>
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Number</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.contract_number || 'N/A' }}
                  </div>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Type</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ getContractTypeDisplay(contract?.contract_type) || 'N/A' }}
                  </div>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Risk Score</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.contract_risk_score || 'N/A' }}
                  </div>
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium text-muted-foreground">Description</label>
                <div class="px-3 py-2 bg-muted rounded-md text-foreground min-h-[80px]">
                  {{ contract?.description || 'No description provided' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Vendor Information Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Building class="w-5 h-5" />
                Vendor Information
              </h3>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Vendor</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ getVendorDisplay(contract?.vendor_id) || 'N/A' }}
                  </div>
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Vendor ID</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.vendor_id || 'N/A' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

          <!-- Financial Details Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <DollarSign class="w-5 h-5" />
                Financial Details
              </h3>
              <p class="text-sm text-muted-foreground">Update contract value and financial terms</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Value</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.contract_value ? `$${contract.contract_value.toLocaleString()}` : 'N/A' }}
                  </div>
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Currency</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.currency || 'N/A' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

          <!-- Contract Dates & Terms Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Calendar class="w-5 h-5" />
                Contract Dates & Terms
              </h3>
              <p class="text-sm text-muted-foreground">Set contract duration and renewal terms</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Start Date</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.start_date || 'N/A' }}
                  </div>
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">End Date</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.end_date || 'N/A' }}
                  </div>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Notice Period (Days)</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.notice_period_days || 'N/A' }}
                </div>
              </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Auto Renewal</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ contract?.auto_renewal ? 'Yes' : 'No' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

          <!-- Contract Stakeholders Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Users class="w-5 h-5" />
                Contract Stakeholders
              </h3>
              <p class="text-sm text-muted-foreground">Assign contract owner and reviewers</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Owner</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ getUserDisplay(contract?.contract_owner) || 'N/A' }}
                  </div>
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Legal Reviewer</label>
                  <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                    {{ getUserDisplay(contract?.legal_reviewer) || 'N/A' }}
                </div>
              </div>
            </div>
          </div>
        </div>

          <!-- Contract Amendments -->
        <div class="space-y-6">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">Contract Amendments</h3>
            <button 
              @click="navigate(`/contracts/${contractId}/create-amendment`)"
              class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
                  <Plus class="w-4 h-4" />
                  Create Amendment
                </button>
          </div>


          <!-- Amendments List -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Amendments List ({{ contractAmendments.length }})
              </h3>
              <p class="text-sm text-muted-foreground">Track all contract amendments and their approval status</p>
            </div>
            <div class="p-6 space-y-4">
              <div v-if="contractAmendments.length > 0" class="space-y-4">
                <div v-for="amendment in contractAmendments" :key="amendment.amendment_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                          <FileText class="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <h4 class="font-medium">{{ amendment.amendment_number }} 
                            <span v-if="amendment.amendment_version" class="text-sm text-muted-foreground">v{{ amendment.amendment_version }}</span>
                          </h4>
                          <p class="text-sm text-muted-foreground">
                            {{ amendment.amendment_date }} • {{ amendment.effective_date }}
                          </p>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <span :class="getWorkflowStatusClass(amendment.workflow_status)" class="px-2 py-1 rounded-full text-xs font-medium">
                          {{ amendment.workflow_status?.toUpperCase() || 'PENDING' }}
                        </span>
                        <span v-if="amendment.affected_area" :class="getAffectedAreaClass(amendment.affected_area)" class="px-2 py-1 rounded-full text-xs font-medium">
                          {{ amendment.affected_area?.toUpperCase() }}
                        </span>
                      </div>
                    </div>

                    <!-- Basic Information -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span class="font-medium">Reason:</span>
                        <p class="text-muted-foreground">{{ amendment.amendment_reason }}</p>
                      </div>
                      <div v-if="amendment.changes_summary">
                        <span class="font-medium">Changes Summary:</span>
                        <p class="text-muted-foreground">{{ amendment.changes_summary }}</p>
                      </div>
                      <div v-if="amendment.justification">
                        <span class="font-medium">Justification:</span>
                        <p class="text-muted-foreground">{{ amendment.justification }}</p>
                      </div>
                      <div v-if="amendment.financial_impact">
                        <span class="font-medium">Financial Impact:</span>
                        <p class="text-muted-foreground">${{ amendment.financial_impact }}</p>
                      </div>
                    </div>

                    <!-- Stakeholders -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div v-if="amendment.initiated_by_display">
                        <span class="font-medium">Initiated By:</span>
                        <p class="text-muted-foreground">{{ amendment.initiated_by_display }}</p>
                      </div>
                      <div v-if="amendment.approved_by_display">
                        <span class="font-medium">Approved By:</span>
                        <p class="text-muted-foreground">{{ amendment.approved_by_display }}</p>
                      </div>
                      <div v-if="amendment.initiated_date">
                        <span class="font-medium">Initiated Date:</span>
                        <p class="text-muted-foreground">{{ amendment.initiated_date }}</p>
                      </div>
                      <div v-if="amendment.approval_date">
                        <span class="font-medium">Approval Date:</span>
                        <p class="text-muted-foreground">{{ amendment.approval_date }}</p>
                      </div>
                    </div>

                    <!-- Affected Items -->
                    <div v-if="amendment.amended_clause_ids_list?.length > 0 || amendment.amended_term_ids_list?.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div v-if="amendment.amended_clause_ids_list?.length > 0">
                        <span class="font-medium">Amended Clauses:</span>
                        <p class="text-muted-foreground">{{ amendment.amended_clause_ids_list.join(', ') }}</p>
                      </div>
                      <div v-if="amendment.amended_term_ids_list?.length > 0">
                        <span class="font-medium">Amended Terms:</span>
                        <p class="text-muted-foreground">{{ amendment.amended_term_ids_list.join(', ') }}</p>
                      </div>
                    </div>

                    <!-- Supporting Documents -->
                    <div v-if="amendment.supporting_documents_list?.length > 0" class="text-sm">
                      <span class="font-medium">Supporting Documents:</span>
                      <div class="mt-1 flex flex-wrap gap-1">
                        <span v-for="doc in amendment.supporting_documents_list" :key="doc" class="px-2 py-1 bg-muted rounded text-xs">
                          {{ doc }}
                        </span>
                      </div>
                    </div>

                    <!-- Notes -->
                    <div v-if="amendment.amendment_notes" class="text-sm">
                      <span class="font-medium">Notes:</span>
                      <p class="text-muted-foreground">{{ amendment.amendment_notes }}</p>
                    </div>

                    <div class="flex items-center gap-2 pt-2 border-t">
                      <button class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <FileText class="w-4 h-4" />
                        View Details
                      </button>
                      <button v-if="amendment.workflow_status === 'pending' || amendment.workflow_status === 'draft'" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <FileText class="w-4 h-4" />
                        Edit
                      </button>
                      <button @click="handleRemoveAmendment(amendment.amendment_id)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted text-red-600 hover:text-red-700">
                        <Trash2 class="w-4 h-4" />
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-12">
                <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 class="mt-2 text-sm font-semibold">No amendments created</h3>
                <p class="mt-1 text-sm text-muted-foreground">
                  Create amendments to modify existing contract terms and conditions.
                </p>
                <button class="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90" @click="showAmendmentForm = true">
                  Create First Amendment
                </button>
            </div>
          </div>
        </div>

        <!-- Subcontracts -->
        <div class="space-y-6">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">Subcontracts</h3>
            <button class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90" @click="navigate(`/contracts/${contractId}/create-subcontract`)">
              <Plus class="w-4 h-4" />
              Add Subcontract
            </button>
          </div>

          <div class="border rounded-lg bg-card">
            <div class="p-6 text-center">
              <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 class="mt-2 text-sm font-semibold">No subcontracts created</h3>
              <p class="mt-1 text-sm text-muted-foreground">
                Add subcontracts to track work delegated to third parties.
              </p>
              <button class="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90" @click="navigate(`/contracts/${contractId}/create-subcontract`)">
                Add First Subcontract
              </button>
            </div>
          </div>
        </div>

          <!-- Compliance Frameworks Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Shield class="w-5 h-5" />
                Compliance Frameworks
              </h3>
              <p class="text-sm text-muted-foreground">Select applicable compliance frameworks</p>
            </div>
            <div class="p-6 space-y-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-muted-foreground">Compliance Framework</label>
              <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                {{ contract?.compliance_framework || 'No compliance frameworks specified' }}
              </div>
            </div>
          </div>
        </div>

          <!-- Contract Terms Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileCheck class="w-5 h-5" />
                Contract Terms
              </h3>
            <p class="text-sm text-muted-foreground">View contract terms and create amendments</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Terms List</h3>
              <div class="flex gap-2">
                <button @click="showAmendTermForm = !showAmendTermForm" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  <FileText class="w-4 h-4" />
                  Amend Term
                </button>
              </div>
            </div>
            
            <!-- Amend Term Form -->
            <div v-if="showAmendTermForm" class="border rounded-lg bg-card p-6 mb-6">
                <h4 class="text-lg font-semibold mb-4">Amend Contract Term</h4>
                <div class="space-y-4">
                  <div class="space-y-2">
                    <label class="text-sm font-medium">Select Term to Amend</label>
                    <select v-model="selectedTermForAmendment" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                      <option value="">Select a term to amend</option>
                      <option v-for="term in contractTerms" :key="term.term_id" :value="term">
                        {{ term.term_title || `Term #${term.term_id}` }} - {{ term.term_category || 'No Category' }}
                      </option>
                    </select>
                  </div>
                  
                  <div v-if="selectedTermForAmendment" class="space-y-4">
                    <div class="p-4 bg-muted rounded-md">
                      <h5 class="font-medium mb-2">Current Term Details:</h5>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div><strong>Category:</strong> {{ selectedTermForAmendment.term_category || 'N/A' }}</div>
                        <div><strong>Title:</strong> {{ selectedTermForAmendment.term_title || 'N/A' }}</div>
                        <div><strong>Risk Level:</strong> {{ selectedTermForAmendment.risk_level || 'N/A' }}</div>
                        <div><strong>Status:</strong> {{ selectedTermForAmendment.compliance_status || 'N/A' }}</div>
                        <div class="md:col-span-2"><strong>Text:</strong> {{ selectedTermForAmendment.term_text || 'N/A' }}</div>
                      </div>
                    </div>
                    
                    <div class="space-y-2">
                      <label class="text-sm font-medium">Amendment Reason *</label>
                      <textarea
                        v-model="termAmendmentReason"
                        placeholder="Describe why this term needs to be amended..."
                        rows="3"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                    </div>
                    
                    <div class="space-y-2">
                      <label class="text-sm font-medium">Proposed Changes *</label>
                      <textarea
                        v-model="termAmendmentChanges"
                        placeholder="Describe the specific changes you want to make..."
                        rows="3"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                    </div>
                    
                    <div class="flex gap-2">
                      <button @click="createTermAmendment" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                        <FileText class="w-4 h-4" />
                        Create Amendment
                      </button>
                      <button @click="cancelTermAmendment" class="px-4 py-2 border rounded-md hover:bg-muted">
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="space-y-4">
                <div v-for="(term, index) in contractTerms" :key="term.term_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h4 class="font-medium">{{ term.term_title || `Term #${index + 1}` }}</h4>
                      <button @click="selectTermForAmendment(term)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <FileText class="w-4 h-4" />
                        Amend
                      </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span class="font-medium text-muted-foreground">Category:</span>
                        <p class="text-foreground">{{ term.term_category || 'N/A' }}</p>
                      </div>
                      
                      <div>
                        <span class="font-medium text-muted-foreground">Risk Level:</span>
                        <p class="text-foreground">{{ term.risk_level || 'N/A' }}</p>
                      </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Compliance Status:</span>
                        <p class="text-foreground">{{ term.compliance_status || 'N/A' }}</p>
                      </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Approval Status:</span>
                        <p class="text-foreground">{{ term.approval_status || 'N/A' }}</p>
                      </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Version:</span>
                        <p class="text-foreground">{{ term.version_number || 'N/A' }}</p>
                      </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Standard Term:</span>
                        <p class="text-foreground">{{ term.is_standard ? 'Yes' : 'No' }}</p>
                      </div>
                    </div>

                    <div class="space-y-2">
                      <span class="font-medium text-muted-foreground">Term Text:</span>
                      <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                        {{ term.term_text || 'No term text provided' }}
                    </div>
                    </div>
                  </div>
                </div>
                
                <div v-if="contractTerms.length === 0" class="text-center py-8 text-muted-foreground">
                  No contract terms available.
                </div>
              </div>
            </div>
          </div>
        </div>

          <!-- Contract Clauses Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Contract Clauses Library
              </h3>
            <p class="text-sm text-muted-foreground">View contract clauses and create amendments</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Clauses List</h3>
                <div class="flex gap-2">
                  <button @click="showAmendClauseForm = !showAmendClauseForm" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                    <FileText class="w-4 h-4" />
                    Amend Clause
                </button>
                </div>
              </div>
              
              <!-- Amend Clause Form -->
              <div v-if="showAmendClauseForm" class="border rounded-lg bg-card p-6 mb-6">
                <h4 class="text-lg font-semibold mb-4">Amend Contract Clause</h4>
              <div class="space-y-4">
                  <div class="space-y-2">
                    <label class="text-sm font-medium">Select Clause to Amend</label>
                    <select v-model="selectedClauseForAmendment" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                      <option value="">Select a clause to amend</option>
                      <option v-for="clause in contractClauses" :key="clause.clause_id" :value="clause">
                        {{ clause.clause_name || `Clause #${clause.clause_id}` }} - {{ clause.clause_type || 'No Type' }}
                      </option>
                    </select>
                    </div>
                    
                  <div v-if="selectedClauseForAmendment" class="space-y-4">
                    <div class="p-4 bg-muted rounded-md">
                      <h5 class="font-medium mb-2">Current Clause Details:</h5>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div><strong>Name:</strong> {{ selectedClauseForAmendment.clause_name || 'N/A' }}</div>
                        <div><strong>Type:</strong> {{ selectedClauseForAmendment.clause_type || 'N/A' }}</div>
                        <div><strong>Risk Level:</strong> {{ selectedClauseForAmendment.risk_level || 'N/A' }}</div>
                        <div><strong>Legal Category:</strong> {{ selectedClauseForAmendment.legal_category || 'N/A' }}</div>
                        <div><strong>Version:</strong> {{ selectedClauseForAmendment.version_number || 'N/A' }}</div>
                        <div><strong>Standard:</strong> {{ selectedClauseForAmendment.is_standard ? 'Yes' : 'No' }}</div>
                        <div class="md:col-span-2"><strong>Text:</strong> {{ selectedClauseForAmendment.clause_text || 'N/A' }}</div>
                      </div>
                    </div>
                    
                      <div class="space-y-2">
                      <label class="text-sm font-medium">Amendment Reason *</label>
                      <textarea
                        v-model="clauseAmendmentReason"
                        placeholder="Describe why this clause needs to be amended..."
                        rows="3"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                      </div>
                      
                      <div class="space-y-2">
                      <label class="text-sm font-medium">Proposed Changes *</label>
                      <textarea
                        v-model="clauseAmendmentChanges"
                        placeholder="Describe the specific changes you want to make..."
                        rows="3"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                      </div>

                    <div class="flex gap-2">
                      <button @click="createClauseAmendment" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                        <FileText class="w-4 h-4" />
                        Create Amendment
                      </button>
                      <button @click="cancelClauseAmendment" class="px-4 py-2 border rounded-md hover:bg-muted">
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
                      </div>

              <div class="space-y-4">
                <div v-for="(clause, index) in contractClauses" :key="clause.clause_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h4 class="font-medium">{{ clause.clause_name || `Clause #${index + 1}` }}</h4>
                      <button @click="selectClauseForAmendment(clause)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <FileText class="w-4 h-4" />
                        Amend
                      </button>
                      </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span class="font-medium text-muted-foreground">Type:</span>
                        <p class="text-foreground">{{ clause.clause_type || 'N/A' }}</p>
                      </div>
                      
                      <div>
                        <span class="font-medium text-muted-foreground">Risk Level:</span>
                        <p class="text-foreground">{{ clause.risk_level || 'N/A' }}</p>
                    </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Legal Category:</span>
                        <p class="text-foreground">{{ clause.legal_category || 'N/A' }}</p>
                    </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Version:</span>
                        <p class="text-foreground">{{ clause.version_number || 'N/A' }}</p>
                    </div>

                      <div>
                        <span class="font-medium text-muted-foreground">Standard Clause:</span>
                        <p class="text-foreground">{{ clause.is_standard ? 'Yes' : 'No' }}</p>
                  </div>
                </div>
                
                    <div class="space-y-2">
                      <span class="font-medium text-muted-foreground">Clause Text:</span>
                      <div class="px-3 py-2 bg-muted rounded-md text-foreground">
                        {{ clause.clause_text || 'No clause text provided' }}
                </div>
              </div>
            </div>
          </div>
                
                <div v-if="contractClauses.length === 0" class="text-center py-8 text-muted-foreground">
                  No contract clauses available.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import { 
  ArrowLeft, Save, Send, FileText, Building, DollarSign, Calendar, 
  Shield, Users, FileCheck, Plus, Trash2 
} from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'

// Router and route
const router = useRouter()
const route = useRoute()
const navigate = (path) => router.push(path)
const { showSuccess, showError, showWarning, showInfo } = useNotifications()
const contractId = parseInt(route.params.id)

// Reactive state
const contract = ref(null)
const loading = ref(false)
const error = ref(null)

// Form data
const formData = ref({
  contract_title: '',
  contract_number: '',
  vendor_id: '',
  contract_type: '',
  contract_value: '',
  currency: 'USD',
  start_date: '',
  end_date: '',
  contract_owner: '',
  legal_reviewer: '',
  auto_renewal: false,
  notice_period_days: 30,
  contract_risk_score: '',
  compliance_framework: '',
  description: ''
})

// Contract terms, clauses, and amendments
const contractTerms = ref([])
const contractClauses = ref([])
const contractAmendments = ref([])

// Amendment forms
const showAmendTermForm = ref(false)
const showAmendClauseForm = ref(false)
const selectedTermForAmendment = ref(null)
const selectedClauseForAmendment = ref(null)
const termAmendmentReason = ref('')
const termAmendmentChanges = ref('')
const clauseAmendmentReason = ref('')
const clauseAmendmentChanges = ref('')

// Users and vendors
const users = ref([])
const legalReviewers = ref([])
const vendors = ref([])

// Removed tabs configuration - now showing all information in single page

// Removed unused mock data and compliance frameworks array

// Methods - removed unused form handling methods since contract is now read-only


const handleRemoveAmendment = async (amendmentId) => {
  if (!confirm('Are you sure you want to delete this amendment?')) {
    return
  }

  try {
    loading.value = true
    const response = await contractsApi.deleteContractAmendment(contractId, amendmentId)
    
    // Handle both response formats
    if (response.success !== false) {
  contractAmendments.value = contractAmendments.value.filter(a => a.amendment_id !== amendmentId)
  PopupService.success('Amendment has been removed from the contract.', 'Amendment Removed')
    } else {
      throw new Error(response.message || 'Failed to delete amendment')
    }
  } catch (error) {
    console.error('Error deleting amendment:', error)
    PopupService.error(`Error deleting amendment: ${error.message}`, 'Deletion Error')
  } finally {
    loading.value = false
  }
}

// Term amendment methods
const selectTermForAmendment = (term) => {
  selectedTermForAmendment.value = term
  showAmendTermForm.value = true
  termAmendmentReason.value = ''
  termAmendmentChanges.value = ''
}

const createTermAmendment = async () => {
  if (!selectedTermForAmendment.value || !termAmendmentReason.value || !termAmendmentChanges.value) {
    PopupService.warning('Please fill in all required fields for the term amendment.', 'Required Fields Missing')
    return
  }

  try {
    loading.value = true
    
    const amendmentData = {
      amendment_number: `T${Date.now()}`,
      amendment_reason: termAmendmentReason.value,
      changes_summary: termAmendmentChanges.value,
      amendment_date: new Date().toISOString().split('T')[0],
      effective_date: new Date().toISOString().split('T')[0],
      workflow_status: 'pending',
      affected_area: 'terms',
      amended_term_ids: selectedTermForAmendment.value.term_id.toString(),
      initiated_by: contract.value?.contract_owner || null,
      initiated_date: new Date().toISOString().split('T')[0],
      amendment_version: '1.0'
    }

    const response = await contractsApi.createContractAmendment(contractId, amendmentData)
    
    if (response.success !== false) {
      const amendment = response.success ? response.data : response
      contractAmendments.value.unshift(amendment)
      cancelTermAmendment()
      PopupService.success('Term amendment created successfully.', 'Amendment Created')
    } else {
      throw new Error(response.message || 'Failed to create term amendment')
    }
  } catch (error) {
    console.error('Error creating term amendment:', error)
    PopupService.error(`Error creating term amendment: ${error.message}`, 'Creation Error')
  } finally {
    loading.value = false
  }
}

const cancelTermAmendment = () => {
  showAmendTermForm.value = false
  selectedTermForAmendment.value = null
  termAmendmentReason.value = ''
  termAmendmentChanges.value = ''
}

// Clause amendment methods
const selectClauseForAmendment = (clause) => {
  selectedClauseForAmendment.value = clause
  showAmendClauseForm.value = true
  clauseAmendmentReason.value = ''
  clauseAmendmentChanges.value = ''
}

const createClauseAmendment = async () => {
  if (!selectedClauseForAmendment.value || !clauseAmendmentReason.value || !clauseAmendmentChanges.value) {
    PopupService.warning('Please fill in all required fields for the clause amendment.', 'Required Fields Missing')
    return
  }

  try {
    loading.value = true
    
    const amendmentData = {
      amendment_number: `C${Date.now()}`,
      amendment_reason: clauseAmendmentReason.value,
      changes_summary: clauseAmendmentChanges.value,
      amendment_date: new Date().toISOString().split('T')[0],
      effective_date: new Date().toISOString().split('T')[0],
      workflow_status: 'pending',
      affected_area: 'clauses',
      amended_clause_ids: selectedClauseForAmendment.value.clause_id.toString(),
      initiated_by: contract.value?.contract_owner || null,
      initiated_date: new Date().toISOString().split('T')[0],
      amendment_version: '1.0'
    }

    const response = await contractsApi.createContractAmendment(contractId, amendmentData)
    
    if (response.success !== false) {
      const amendment = response.success ? response.data : response
      contractAmendments.value.unshift(amendment)
      cancelClauseAmendment()
      PopupService.success('Clause amendment created successfully.', 'Amendment Created')
    } else {
      throw new Error(response.message || 'Failed to create clause amendment')
    }
  } catch (error) {
    console.error('Error creating clause amendment:', error)
    PopupService.error(`Error creating clause amendment: ${error.message}`, 'Creation Error')
  } finally {
    loading.value = false
  }
}

const cancelClauseAmendment = () => {
  showAmendClauseForm.value = false
  selectedClauseForAmendment.value = null
  clauseAmendmentReason.value = ''
  clauseAmendmentChanges.value = ''
}

// Removed old methods that are no longer needed since we're making the contract read-only

const getAmendmentStatusClass = (status) => {
  const statusConfig = {
    approved: 'px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800',
    pending_approval: 'px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800',
    rejected: 'px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800',
    draft: 'px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800'
  }
  return statusConfig[status] || statusConfig.draft
}

const getAmendmentTypeClass = (type) => {
  const typeConfig = {
    critical: 'px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800',
    major: 'px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800',
    minor: 'px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800'
  }
  return typeConfig[type] || typeConfig.minor
}

const getWorkflowStatusClass = (status) => {
  const statusConfig = {
    pending: 'bg-yellow-100 text-yellow-800',
    under_review: 'bg-blue-100 text-blue-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800'
  }
  return statusConfig[status] || statusConfig.pending
}

const getAffectedAreaClass = (area) => {
  const areaConfig = {
    terms: 'bg-purple-100 text-purple-800',
    clauses: 'bg-indigo-100 text-indigo-800',
    both: 'bg-pink-100 text-pink-800'
  }
  return areaConfig[area] || 'bg-gray-100 text-gray-800'
}

// Helper functions for display
const getContractTypeDisplay = (type) => {
  const typeMap = {
    'MASTER_AGREEMENT': 'Master Service Agreement (MSA)',
    'NDA': 'Non-Disclosure Agreement (NDA)',
    'SOW': 'Statement of Work (SOW)',
    'SERVICE_AGREEMENT': 'Service Agreement',
    'PURCHASE_ORDER': 'Purchase Order',
    'LICENSE': 'License'
  }
  return typeMap[type] || type
}

const getVendorDisplay = (vendorId) => {
  const vendor = vendors.value.find(v => v.vendor_id === vendorId)
  return vendor ? `${vendor.company_name} (${vendor.vendor_code})` : null
}

const getUserDisplay = (userId) => {
  const user = users.value.find(u => u.userid === userId)
  return user ? `${user.first_name} ${user.last_name} (${user.username})` : null
}

// Load data functions
const loadContract = async () => {
  try {
    loading.value = true
    console.log('Loading contract with ID:', contractId)
    const response = await contractsApi.getContract(contractId)
    console.log('Contract response:', response)
    
    // Handle both response formats (with success property or direct data)
    if (response.success !== false) {
      const contractData = response.success ? response.data : response
      contract.value = contractData
      
    // Pre-populate form with existing contract data
    formData.value = {
        contract_title: contractData.contract_title || '',
        contract_number: contractData.contract_number || '',
        vendor_id: contractData.vendor_id || '',
        contract_type: contractData.contract_type || '',
        contract_value: contractData.contract_value?.toString() || '',
        currency: contractData.currency || 'USD',
        start_date: contractData.start_date || '',
        end_date: contractData.end_date || '',
        contract_owner: contractData.contract_owner || '',
        legal_reviewer: contractData.legal_reviewer || '',
        auto_renewal: contractData.auto_renewal || false,
        notice_period_days: contractData.notice_period_days || 30,
        contract_risk_score: contractData.contract_risk_score?.toString() || '',
        compliance_framework: contractData.compliance_framework || '',
        description: contractData.description || ''
      }
      console.log('Contract loaded successfully:', contractData)
      
      // Show success notification
      await showSuccess('Contract Loaded', `Contract "${contractData.contract_title}" loaded successfully.`, {
        action: 'contract_loaded',
        contract_id: contractId,
        contract_title: contractData.contract_title
      })
    } else {
      throw new Error(response.message || 'Failed to load contract')
    }
  } catch (error) {
    console.error('Error loading contract:', error)
    error.value = error.message
    
    // Show error notification
    await showError('Loading Failed', 'Failed to load contract. Please try again.', {
      action: 'contract_loading_failed',
      contract_id: contractId,
      error_message: error.message
    })
  } finally {
    loading.value = false
  }
}

const loadContractTerms = async () => {
  try {
    const response = await contractsApi.getContractTerms(contractId)
    // Handle both response formats
    if (response.success !== false) {
      contractTerms.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading contract terms:', error)
  }
}

const loadContractClauses = async () => {
  try {
    const response = await contractsApi.getContractClauses(contractId)
    // Handle both response formats
    if (response.success !== false) {
      contractClauses.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading contract clauses:', error)
  }
}

const loadContractAmendments = async () => {
  try {
    const response = await contractsApi.getContractAmendments(contractId)
    // Handle both response formats
    if (response.success !== false) {
      contractAmendments.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading contract amendments:', error)
  }
}

const loadUsers = async () => {
  try {
    const response = await contractsApi.getUsers()
    // Handle both response formats
    if (response.success !== false) {
      users.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading users:', error)
  }
}

const loadLegalReviewers = async () => {
  try {
    const response = await contractsApi.getLegalReviewers()
    // Handle both response formats
    if (response.success !== false) {
      legalReviewers.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading legal reviewers:', error)
  }
}

const loadVendors = async () => {
  try {
    const response = await contractsApi.getVendors()
    // Handle both response formats
    if (response.success !== false) {
      vendors.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading vendors:', error)
  }
}

// Initialize component
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Edit Contract', contractId)
  try {
    await Promise.all([
      loadContract(),
      loadContractTerms(),
      loadContractClauses(),
      loadContractAmendments(),
      loadUsers(),
      loadLegalReviewers(),
      loadVendors()
    ])
  } catch (error) {
    console.error('Error during component initialization:', error)
    error.value = 'Failed to load contract data. Please refresh the page.'
  }
})
</script>
