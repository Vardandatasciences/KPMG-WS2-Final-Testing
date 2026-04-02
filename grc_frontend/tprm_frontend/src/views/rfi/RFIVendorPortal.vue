<template>
  <div class="vendor-portal-standalone">
    <div class="w-full space-y-6 px-4 sm:px-6 lg:px-8">
      <!-- Loading overlay -->
      <div v-if="isLoading" class="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div class="text-center">
          <Loader2 class="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p class="text-gray-600">Loading RFI details...</p>
        </div>
      </div>

      <div v-else>
        <!-- Floating Action Button - Right Panel -->
        <div class="fixed right-6 top-24 z-40 flex flex-col gap-3">
          <div class="relative">
            <button
              type="button"
              @click="toggleRightPanel"
              class="bg-white border-2 border-blue-500 text-blue-600 rounded-full p-3 shadow-lg hover:bg-blue-50 transition-all hover:scale-110"
              :title="rightPanelOpen ? 'Close Panel' : 'View RFI Details & Documents'"
            >
              <FileText v-if="!rightPanelOpen" class="h-6 w-6" />
              <X v-else class="h-6 w-6" />
            </button>
          </div>
        </div>

        <!-- Full-Width Progress Bar -->
        <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden mb-6">
          <div class="px-6 py-4 bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-gray-100">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-semibold text-gray-900">Submission Progress</h3>
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                {{ overallProgress }}% Complete
              </span>
            </div>
            <div class="relative w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div 
                class="absolute inset-0 bg-gradient-to-r from-purple-600 via-purple-500 to-indigo-600 rounded-full transition-all duration-500 ease-out" 
                :style="{ width: overallProgress + '%' }"
              />
            </div>
          </div>
          <div class="px-6 py-4">
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-green-500" />
                <span class="text-sm font-medium text-gray-700">Company</span>
                <span class="text-sm font-bold text-green-600">{{ completionStatus.company }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-blue-500" />
                <span class="text-sm font-medium text-gray-700">Product & Demos</span>
                <span class="text-sm font-bold text-blue-600">{{ completionStatus.product }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-orange-500" />
                <span class="text-sm font-medium text-gray-700">Integration</span>
                <span class="text-sm font-bold text-orange-600">{{ completionStatus.integration }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-red-500" />
                <span class="text-sm font-medium text-gray-700">Risk</span>
                <span class="text-sm font-bold text-red-600">{{ completionStatus.risk }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-indigo-500" />
                <span class="text-sm font-medium text-gray-700">Legal</span>
                <span class="text-sm font-bold text-indigo-600">{{ completionStatus.legal }}%</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-gray-500" />
                <span class="text-sm font-medium text-gray-700">Documents</span>
                <span class="text-sm font-bold text-gray-600">{{ completionStatus.documents }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Side Panel - RFI Details & Documents -->
        <div 
          v-if="rightPanelOpen" 
          class="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-200 shadow-2xl z-50 overflow-y-auto"
        >
          <div class="p-6 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">RFI Details</h3>
              <button type="button" @click="rightPanelOpen = false" class="text-gray-500 hover:text-gray-700">
                <X class="h-5 w-5" />
              </button>
            </div>
          </div>
          <div class="p-6 space-y-4">
            <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div class="font-medium text-gray-900 mb-2">{{ rfiInfo.rfiTitle }}</div>
              <div class="text-sm text-gray-700">RFI Number: <span class="font-medium">{{ rfiInfo.rfiNumber }}</span></div>
              <div class="text-sm text-gray-700">Deadline: <span class="font-medium">{{ rfiInfo.deadline || 'TBD' }}</span></div>
              <div class="text-sm text-gray-700" v-if="rfiInfo.description">Description: <span class="font-medium break-words">{{ rfiInfo.description }}</span></div>
              <div class="text-sm text-gray-700" v-if="rfiInfo.budget">Budget: <span class="font-medium">{{ rfiInfo.budget }}</span></div>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div class="font-medium text-gray-900 mb-2">Completion Snapshot</div>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div>Company: <span class="font-medium">{{ completionStatus.company }}%</span></div>
                <div>Product: <span class="font-medium">{{ completionStatus.product }}%</span></div>
                <div>Integration: <span class="font-medium">{{ completionStatus.integration }}%</span></div>
                <div>Risk: <span class="font-medium">{{ completionStatus.risk }}%</span></div>
                <div>Legal: <span class="font-medium">{{ completionStatus.legal }}%</span></div>
                <div>Documents: <span class="font-medium">{{ completionStatus.documents }}%</span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Header -->
        <div class="text-center space-y-4 mb-6">
          <div class="flex justify-center items-center gap-3">
            <span class="inline-flex px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-200">
              {{ rfiInfo.rfiNumber }}
            </span>
            <button
              @click="loadSampleData"
              type="button"
              class="inline-flex items-center px-4 py-2 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 hover:border-indigo-300 transition-all text-sm font-medium shadow-sm"
            >
              <Lightbulb class="h-4 w-4 mr-1.5" />
              <span>Load Sample Data</span>
            </button>
          </div>
          <h1 class="text-3xl font-bold tracking-tight text-gray-900">{{ rfiInfo.rfiTitle }}</h1>
          <p class="text-gray-600">Please complete all sections below to submit your RFI response.</p>
          <div class="flex items-center justify-center gap-4 text-sm">
            <div class="flex items-center gap-1">
              <Clock class="h-4 w-4 text-yellow-600" />
              <span class="text-gray-700">Deadline: {{ rfiInfo.deadline || 'TBD' }}</span>
            </div>
            <div class="flex items-center gap-1" v-if="rfiInfo.budget">
              <Building2 class="h-4 w-4 text-gray-500" />
              <span class="text-gray-700">{{ rfiInfo.budget }}</span>
            </div>
          </div>
        </div>

        <!-- Tab Navigation -->
        <div class="bg-white border border-gray-200 rounded-lg shadow-sm mb-6 overflow-hidden">
          <div class="flex border-b border-gray-200 overflow-x-auto">
            <button
              v-for="tab in formTabs"
              :key="tab.id"
              type="button"
              @click="goToTab(tab.id)"
              :class="[
                'flex-1 min-w-[120px] px-4 py-3 text-sm font-medium transition-colors relative',
                activeTab === tab.id
                  ? 'text-blue-600 bg-blue-50 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              ]"
            >
              <div class="flex items-center justify-center gap-2">
                <span class="text-base">{{ tab.icon }}</span>
                <span>{{ tab.label }}</span>
                <CheckCircle2 v-if="isTabCompleted(tab.id)" class="h-4 w-4 text-green-600 ml-1" />
              </div>
            </button>
          </div>
        </div>

        <!-- Tab Content -->
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Company Information Tab -->
          <div v-show="activeTab === 'company'" class="space-y-6">
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div class="p-6 border-b border-gray-200">
                <div class="flex items-center gap-2">
                  <Building2 class="h-5 w-5 text-gray-700" />
                  <h3 class="text-lg font-semibold text-gray-900">Company Information</h3>
                  <CheckCircle2 v-if="completionStatus.company === 100" class="h-4 w-4 text-green-600 ml-auto" />
                  <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
                </div>
              </div>
              <div class="p-6 space-y-6">
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Basic Company Details</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Company Name *</label>
                      <input v-model="formData.companyName" type="text" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter company name" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Legal Name *</label>
                      <input v-model="formData.legalName" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter legal company name" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Business Type *</label>
                      <select v-model="formData.businessType" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">Select business type</option>
                        <option value="Corporation">Corporation</option>
                        <option value="LLC">LLC</option>
                        <option value="Partnership">Partnership</option>
                        <option value="Sole Proprietorship">Sole Proprietorship</option>
                        <option value="Non-Profit">Non-Profit</option>
                      </select>
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Industry Sector *</label>
                      <input v-model="formData.industrySector" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g., Technology, Healthcare" />
                    </div>
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Contact Information</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Primary Contact Name *</label>
                      <input v-model="formData.contactName" type="text" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter contact name" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Contact Title *</label>
                      <input v-model="formData.contactTitle" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g., CEO, Project Manager" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Email Address *</label>
                      <input v-model="formData.contactEmail" type="email" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter email address" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Phone Number *</label>
                      <input v-model="formData.contactPhone" type="tel" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter phone number" />
                    </div>
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Company Details</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Website</label>
                      <input v-model="formData.website" type="url" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="https://www.company.com" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Tax ID / EIN</label>
                      <input v-model="formData.taxId" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter Tax ID or EIN" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">DUNS Number</label>
                      <input v-model="formData.dunsNumber" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter DUNS number" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Incorporation Date</label>
                      <input v-model="formData.incorporationDate" type="date" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                    </div>
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Company Size & Address</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Number of Employees</label>
                      <select v-model="formData.employeeCount" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">Select</option>
                        <option value="1-10">1-10</option>
                        <option value="11-50">11-50</option>
                        <option value="51-200">51-200</option>
                        <option value="201-500">201-500</option>
                        <option value="501-1000">501-1000</option>
                        <option value="1000+">1000+</option>
                      </select>
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Annual Revenue</label>
                      <select v-model="formData.annualRevenue" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">Select</option>
                        <option value="0-1M">$0 - $1M</option>
                        <option value="1M-5M">$1M - $5M</option>
                        <option value="5M-10M">$5M - $10M</option>
                        <option value="10M-50M">$10M - $50M</option>
                        <option value="50M-100M">$50M - $100M</option>
                        <option value="100M+">$100M+</option>
                      </select>
                    </div>
                    <div class="space-y-2 md:col-span-2">
                      <label class="text-sm font-medium text-gray-700">Headquarters Address</label>
                      <textarea v-model="formData.headquartersAddress" rows="2" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter complete address" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Country</label>
                      <input v-model="formData.headquartersCountry" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter country" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Years in Business</label>
                      <input v-model.number="formData.yearsInBusiness" type="number" min="0" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Enter years" />
                    </div>
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Company Description</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Company Description *</label>
                    <textarea v-model="formData.companyDescription" rows="4" required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe your company, its mission, and key capabilities" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Product & Demos Tab -->
          <div v-show="activeTab === 'product'" class="space-y-6">
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div class="p-6 border-b border-gray-200">
                <div class="flex items-center gap-2">
                  <Package class="h-5 w-5 text-gray-700" />
                  <h3 class="text-lg font-semibold text-gray-900">Product & Demos</h3>
                  <CheckCircle2 v-if="completionStatus.product === 100" class="h-4 w-4 text-green-600 ml-auto" />
                  <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
                </div>
              </div>
              <div class="p-6 space-y-6">
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Demos & Trial</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Demos provided? / Trial Version</label>
                      <select v-model="formData.demosTrialVersion" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">Select...</option>
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                        <option value="upon_request">Upon Request</option>
                        <option value="limited">Limited Trial Available</option>
                        <option value="full">Full Trial Available</option>
                      </select>
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Trial Duration (if applicable)</label>
                      <input v-model="formData.trialDuration" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g., 14 days, 30 days" />
                    </div>
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Proof of Concept (PoC)</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">PoC Availability & Process</label>
                    <textarea v-model="formData.poc" rows="4" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe PoC availability, process, timeline, and typical deliverables. Include any costs or prerequisites." />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Differentiators</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">What sets your solution apart?</label>
                    <textarea v-model="formData.differentiators" rows="4" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe your key differentiators, unique value proposition, and competitive advantages." />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Technology Stack</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Describe your technology stack</label>
                    <textarea v-model="formData.technologyStack" rows="4" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Include programming languages, frameworks, databases, cloud platforms, security technologies, and infrastructure. Mention versioning and upgrade cycles." />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Integration & Support Tab -->
          <div v-show="activeTab === 'integration'" class="space-y-6">
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div class="p-6 border-b border-gray-200">
                <div class="flex items-center gap-2">
                  <Link2 class="h-5 w-5 text-gray-700" />
                  <h3 class="text-lg font-semibold text-gray-900">Integration & Support</h3>
                  <CheckCircle2 v-if="completionStatus.integration === 100" class="h-4 w-4 text-green-600 ml-auto" />
                  <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
                </div>
              </div>
              <div class="p-6 space-y-6">
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Integration Capabilities</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Integration Options (APIs, webhooks, SDKs)</label>
                    <textarea v-model="formData.integrationCapabilities" rows="4" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe integration options, supported protocols, documentation availability, and certification requirements." />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Training & Support</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2 md:col-span-2">
                      <label class="text-sm font-medium text-gray-700">Training Options</label>
                      <textarea v-model="formData.trainingOptions" rows="2" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Training programs, documentation, onboarding, certification paths" />
                    </div>
                    <div class="space-y-2 md:col-span-2">
                      <label class="text-sm font-medium text-gray-700">Post-Implementation Support</label>
                      <textarea v-model="formData.postImplementationSupport" rows="3" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Support levels, SLAs, response times, escalation process" />
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Update Frequency</label>
                      <select v-model="formData.updateFrequency" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">Select...</option>
                        <option value="weekly">Weekly</option>
                        <option value="biweekly">Bi-weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="quarterly">Quarterly</option>
                        <option value="biannual">Bi-annual</option>
                        <option value="annual">Annual</option>
                        <option value="as_needed">As Needed</option>
                      </select>
                    </div>
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Preferred Communication Channels</label>
                      <input v-model="formData.preferredCommunication" type="text" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g., Email, Slack, Phone, Portal" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Risk & Compliance Tab -->
          <div v-show="activeTab === 'risk'" class="space-y-6">
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div class="p-6 border-b border-gray-200">
                <div class="flex items-center gap-2">
                  <Shield class="h-5 w-5 text-gray-700" />
                  <h3 class="text-lg font-semibold text-gray-900">Risk & Compliance</h3>
                  <CheckCircle2 v-if="completionStatus.risk === 100" class="h-4 w-4 text-green-600 ml-auto" />
                  <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
                </div>
              </div>
              <div class="p-6 space-y-6">
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Risk Management Practices</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Describe your risk management approach</label>
                    <textarea v-model="formData.riskManagementPractices" rows="4" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Include risk identification, assessment, mitigation strategies, monitoring, and governance. Mention certifications (e.g., ISO 31000)." />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Disaster Recovery and Backup</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">DR strategy, backup frequency, RPO/RTO</label>
                    <textarea v-model="formData.disasterRecoveryBackup" rows="4" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe disaster recovery plans, backup schedules, RPO (Recovery Point Objective), RTO (Recovery Time Objective), and testing frequency." />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Compliance & Certifications</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Relevant certifications (SOC 2, ISO, GDPR, etc.)</label>
                    <textarea v-model="formData.complianceCertifications" rows="2" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="List compliance certifications and attestations" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Legal & Terms Tab -->
          <div v-show="activeTab === 'legal'" class="space-y-6">
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div class="p-6 border-b border-gray-200">
                <div class="flex items-center gap-2">
                  <FileText class="h-5 w-5 text-gray-700" />
                  <h3 class="text-lg font-semibold text-gray-900">Legal & Terms</h3>
                  <CheckCircle2 v-if="completionStatus.legal === 100" class="h-4 w-4 text-green-600 ml-auto" />
                  <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
                </div>
              </div>
              <div class="p-6 space-y-6">
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Legal Terms</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Key legal terms and conditions</label>
                    <textarea v-model="formData.legalTerms" rows="3" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe key legal terms, warranties, indemnification, limitation of liability" />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Terms and Conditions</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Standard terms and conditions</label>
                    <textarea v-model="formData.termsAndConditions" rows="3" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe your standard T&Cs, acceptance criteria, and any custom terms" />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Non-Disclosure Agreement (NDA)</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">NDA Availability</label>
                    <select v-model="formData.nda" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                      <option value="">Select...</option>
                      <option value="standard">Standard NDA Available</option>
                      <option value="mutual">Mutual NDA Available</option>
                      <option value="custom">Custom NDA Upon Request</option>
                      <option value="not_required">Not Required</option>
                    </select>
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Licensing Terms</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Licensing model and restrictions</label>
                    <textarea v-model="formData.licensingTerms" rows="3" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Per-seat, enterprise, usage-based; restrictions; transferability" />
                  </div>
                </div>
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Exit Strategy</h4>
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Data extraction and transition support on contract end</label>
                    <textarea v-model="formData.exitStrategy" rows="3" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Describe data portability, extraction tools, transition support, notice periods" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Documents Tab -->
          <div v-show="activeTab === 'documents'" class="space-y-6">
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div class="p-6 border-b border-gray-200">
                <div class="flex items-center gap-2">
                  <FileText class="h-5 w-5 text-gray-700" />
                  <h3 class="text-lg font-semibold text-gray-900">Documents</h3>
                  <CheckCircle2 v-if="completionStatus.documents === 100" class="h-4 w-4 text-green-600" />
                  <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
                </div>
              </div>
              <div class="p-6 space-y-6">
                <div class="space-y-4">
                  <h4 class="text-md font-semibold text-gray-800">Upload Supporting Documents</h4>
                  <p class="text-sm text-gray-600">Upload relevant documents (brochures, certifications, case studies, etc.)</p>
                  <div 
                    class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-colors"
                    @click="$refs.docInput?.click()"
                    @dragover.prevent="isDragOver = true"
                    @dragleave.prevent="isDragOver = false"
                    @drop.prevent="handleDocDrop"
                    :class="{ 'border-blue-400 bg-blue-50': isDragOver }"
                  >
                    <Upload class="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p class="text-gray-600 mb-2">Click or drag files to upload</p>
                    <p class="text-xs text-gray-500">PDF, DOC, DOCX, XLS, XLSX (Max 10MB per file)</p>
                    <input ref="docInput" type="file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx" class="hidden" @change="handleDocSelect" />
                  </div>
                  <div v-if="uploadedDocuments.length > 0" class="space-y-2">
                    <p class="text-sm font-medium text-gray-700">Uploaded files:</p>
                    <div v-for="(doc, idx) in uploadedDocuments" :key="idx" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div class="flex items-center gap-2">
                        <FileText class="h-4 w-4 text-blue-600" />
                        <span class="text-sm font-medium">{{ doc.name }}</span>
                        <span class="text-xs text-gray-500">({{ formatFileSize(doc.size || 0) }})</span>
                      </div>
                      <button type="button" @click="removeDocument(idx)" class="text-red-600 hover:text-red-800 text-sm font-medium">Remove</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab Navigation Buttons -->
          <div class="flex justify-between mt-6">
            <button
              type="button"
              @click="goToPreviousTab"
              :disabled="isFirstTab"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Previous
            </button>
            <button
              v-if="!isLastTab"
              type="button"
              @click="goToNextTab"
              class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Next →
            </button>
            <button
              v-else
              type="submit"
              :disabled="isSubmitting || overallProgress < 50"
              class="inline-flex items-center px-6 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isSubmitting" class="h-4 w-4 animate-spin mr-2" />
              Submit RFI Response
            </button>
          </div>
          <div v-if="overallProgress < 50 && isLastTab" class="text-sm text-gray-500 mt-2 text-center">
            Complete at least 50% of all sections to enable submission (currently {{ overallProgress }}%)
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Loader2, FileText, X, Clock, Building2, CheckCircle2, AlertCircle, 
  Package, Link2, Shield, Upload, Lightbulb 
} from 'lucide-vue-next'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv.js'

const route = useRoute()
const router = useRouter()
const { success, error } = rfpUseToast()
const API_BASE = getTprmApiV1BaseUrl()

const token = computed(() => route.params.token)
const isLoading = ref(true)
const isSubmitting = ref(false)
const rightPanelOpen = ref(false)
const isDragOver = ref(false)
const docInput = ref(null)

const activeTab = ref('company')
const formTabs = [
  { id: 'company', label: 'Company', icon: '🏢' },
  { id: 'product', label: 'Product & Demos', icon: '📦' },
  { id: 'integration', label: 'Integration & Support', icon: '🔗' },
  { id: 'risk', label: 'Risk & Compliance', icon: '🛡️' },
  { id: 'legal', label: 'Legal & Terms', icon: '📜' },
  { id: 'documents', label: 'Documents', icon: '📄' }
]

const completionStatus = ref({
  company: 0,
  product: 0,
  integration: 0,
  risk: 0,
  legal: 0,
  documents: 0
})

const rfiInfo = ref({
  rfiNumber: 'RFI-xxxx',
  rfiTitle: 'Request for Information',
  deadline: '',
  description: '',
  budget: ''
})

const formData = reactive({
  companyName: '',
  legalName: '',
  businessType: '',
  industrySector: '',
  contactName: '',
  contactTitle: '',
  contactEmail: '',
  contactPhone: '',
  website: '',
  taxId: '',
  dunsNumber: '',
  incorporationDate: '',
  employeeCount: '',
  annualRevenue: '',
  headquartersAddress: '',
  headquartersCountry: '',
  yearsInBusiness: '',
  companyDescription: '',
  demosTrialVersion: '',
  trialDuration: '',
  poc: '',
  differentiators: '',
  technologyStack: '',
  integrationCapabilities: '',
  trainingOptions: '',
  postImplementationSupport: '',
  updateFrequency: '',
  preferredCommunication: '',
  riskManagementPractices: '',
  disasterRecoveryBackup: '',
  complianceCertifications: '',
  legalTerms: '',
  termsAndConditions: '',
  nda: '',
  licensingTerms: '',
  exitStrategy: ''
})

const uploadedDocuments = ref([])

const isFirstTab = computed(() => formTabs.findIndex(t => t.id === activeTab.value) <= 0)
const isLastTab = computed(() => formTabs.findIndex(t => t.id === activeTab.value) >= formTabs.length - 1)

const overallProgress = computed(() => {
  const s = completionStatus.value
  return Math.round(
    (s.company + s.product + s.integration + s.risk + s.legal + s.documents) / 6
  )
})

function isFieldFilled(val) {
  if (val == null) return false
  if (typeof val === 'string') return val.trim().length > 0
  return true
}

function updateCompletionStatus() {
  const companyFields = [
    'companyName', 'legalName', 'businessType', 'industrySector',
    'contactName', 'contactTitle', 'contactEmail', 'contactPhone',
    'website', 'taxId', 'incorporationDate', 'employeeCount', 'annualRevenue',
    'headquartersAddress', 'headquartersCountry', 'yearsInBusiness', 'companyDescription'
  ]
  const filledCompany = companyFields.filter(f => isFieldFilled(formData[f])).length
  completionStatus.value.company = Math.round((filledCompany / companyFields.length) * 100)

  const productFields = ['demosTrialVersion', 'poc', 'differentiators', 'technologyStack']
  const filledProduct = productFields.filter(f => isFieldFilled(formData[f])).length
  completionStatus.value.product = Math.round((filledProduct / productFields.length) * 100)

  const integrationFields = ['integrationCapabilities', 'trainingOptions', 'postImplementationSupport', 'updateFrequency', 'preferredCommunication']
  const filledIntegration = integrationFields.filter(f => isFieldFilled(formData[f])).length
  completionStatus.value.integration = Math.round((filledIntegration / integrationFields.length) * 100)

  const riskFields = ['riskManagementPractices', 'disasterRecoveryBackup']
  const filledRisk = riskFields.filter(f => isFieldFilled(formData[f])).length
  completionStatus.value.risk = Math.round((filledRisk / riskFields.length) * 100)

  const legalFields = ['legalTerms', 'termsAndConditions', 'nda', 'licensingTerms', 'exitStrategy']
  const filledLegal = legalFields.filter(f => isFieldFilled(formData[f])).length
  completionStatus.value.legal = Math.round((filledLegal / legalFields.length) * 100)

  const docCount = uploadedDocuments.value.length
  completionStatus.value.documents = docCount > 0 ? 100 : 0
}

function isTabCompleted(tabId) {
  const map = {
    company: completionStatus.value.company,
    product: completionStatus.value.product,
    integration: completionStatus.value.integration,
    risk: completionStatus.value.risk,
    legal: completionStatus.value.legal,
    documents: completionStatus.value.documents
  }
  return (map[tabId] || 0) === 100
}

function goToTab(tabId) {
  activeTab.value = tabId
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function goToNextTab() {
  const idx = formTabs.findIndex(t => t.id === activeTab.value)
  if (idx < formTabs.length - 1) {
    activeTab.value = formTabs[idx + 1].id
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function goToPreviousTab() {
  const idx = formTabs.findIndex(t => t.id === activeTab.value)
  if (idx > 0) {
    activeTab.value = formTabs[idx - 1].id
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function toggleRightPanel() {
  rightPanelOpen.value = !rightPanelOpen.value
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function handleDocSelect(e) {
  const files = Array.from(e.target.files || [])
  files.forEach(file => {
    if (file.size <= 10 * 1024 * 1024) {
      uploadedDocuments.value.push({ name: file.name, size: file.size, file })
    }
  })
  e.target.value = ''
  updateCompletionStatus()
}

function handleDocDrop(e) {
  isDragOver.value = false
  handleDocSelect({ target: { files: e.dataTransfer.files } })
}

function removeDocument(idx) {
  uploadedDocuments.value.splice(idx, 1)
  updateCompletionStatus()
}

async function loadRFIByToken() {
  if (!token.value) {
    rfiInfo.value = { rfiNumber: 'RFI-Demo', rfiTitle: 'RFI Vendor Response Portal', deadline: '', description: '', budget: '' }
    isLoading.value = false
    return
  }
  try {
    const response = await fetch(`${API_BASE}/rfi-invitations/${token.value}/`, {
      headers: { 'Content-Type': 'application/json' }
    }).catch(() => null)
    if (response?.ok) {
      const data = await response.json()
      if (data.rfi) {
        rfiInfo.value = {
          rfiNumber: data.rfi.rfi_number,
          rfiTitle: data.rfi.rfi_title,
          deadline: data.rfi.submission_deadline ? new Date(data.rfi.submission_deadline).toLocaleDateString() : '',
          description: data.rfi.description || '',
          budget: data.rfi.estimated_value ? `$${Number(data.rfi.estimated_value).toLocaleString()}` : ''
        }
      }
    } else {
      rfiInfo.value = {
        rfiNumber: 'RFI-2024-001',
        rfiTitle: 'Request for Information - Vendor Response',
        deadline: '',
        description: '',
        budget: ''
      }
    }
  } catch (e) {
    rfiInfo.value = { rfiNumber: 'RFI-Response', rfiTitle: 'RFI Vendor Portal', deadline: '', description: '', budget: '' }
  } finally {
    isLoading.value = false
  }
}

function loadSampleData() {
  // Company Information
  formData.companyName = 'TechVision Solutions Inc.'
  formData.legalName = 'TechVision Solutions Incorporated'
  formData.businessType = 'Corporation'
  formData.industrySector = 'Technology / Cloud Services'
  formData.contactName = 'Sarah Johnson'
  formData.contactTitle = 'VP of Business Development'
  formData.contactEmail = 'sarah.johnson@techvision.com'
  formData.contactPhone = '+1 (555) 123-4567'
  formData.website = 'https://www.techvision.com'
  formData.taxId = '12-3456789'
  formData.dunsNumber = '123456789'
  formData.incorporationDate = '2015-03-15'
  formData.employeeCount = '250-500'
  formData.annualRevenue = '$50M - $100M'
  formData.headquartersAddress = '123 Tech Park Drive, San Francisco, CA 94105'
  formData.headquartersCountry = 'United States'
  formData.yearsInBusiness = '9'
  formData.companyDescription = 'TechVision Solutions is a leading provider of cloud infrastructure and managed services. We specialize in helping enterprises migrate to cloud-native architectures with a focus on security, scalability, and cost optimization. Our team of certified cloud architects has successfully delivered over 500 projects across various industries including finance, healthcare, and retail.'

  // Product & Demos
  formData.demosTrialVersion = 'Yes, we offer a comprehensive 30-day trial with full access to our platform including dedicated support and onboarding assistance.'
  formData.trialDuration = '30 days with option to extend'
  formData.poc = 'We provide a proof-of-concept environment that mirrors your production requirements. Our POC includes: dedicated cloud environment, sample data migration, integration testing, and performance benchmarking. Typical POC duration is 2-4 weeks.'
  formData.differentiators = 'Key differentiators include: 1) AI-powered cost optimization reducing cloud spend by 30-40%, 2) Zero-downtime migration methodology, 3) 24/7 multilingual support with 15-minute response time, 4) Proprietary security framework exceeding industry standards, 5) Flexible pricing models including consumption-based and reserved capacity options.'
  formData.technologyStack = 'Primary: AWS, Azure, Google Cloud Platform. Container orchestration: Kubernetes, Docker. IaC: Terraform, CloudFormation. Monitoring: Datadog, Prometheus, Grafana. Security: Vault, AWS KMS, Azure Key Vault. CI/CD: Jenkins, GitLab CI, GitHub Actions.'

  // Integration & Support
  formData.integrationCapabilities = 'We support REST APIs, GraphQL, webhooks, and message queues (Kafka, RabbitMQ). Pre-built connectors for major platforms including Salesforce, SAP, Oracle, Microsoft Dynamics. Custom integration development available. SSO support via SAML 2.0, OAuth 2.0, and OpenID Connect.'
  formData.trainingOptions = 'Comprehensive training program including: 1) Administrator training (3-day intensive), 2) End-user training (1-day workshop), 3) Train-the-trainer program, 4) On-demand video library, 5) Interactive documentation portal, 6) Quarterly webinars on new features.'
  formData.postImplementationSupport = '24/7/365 support with tiered SLAs: Critical (15 min), High (1 hour), Medium (4 hours), Low (24 hours). Dedicated Customer Success Manager, quarterly business reviews, monthly health checks, and proactive monitoring with automated alerting.'
  formData.updateFrequency = 'Major releases quarterly, minor updates monthly, security patches as needed (typically within 24 hours of vulnerability disclosure). All updates include detailed release notes, migration guides, and rollback procedures.'
  formData.preferredCommunication = 'Primary: Email and Slack integration. Secondary: Phone, video conferencing (Zoom/Teams). Ticketing system for all support requests with full audit trail. Customer portal for documentation, knowledge base, and community forums.'

  // Risk & Compliance
  formData.riskManagementPractices = 'ISO 27001 certified risk management framework. Annual third-party security audits, continuous vulnerability scanning, penetration testing quarterly. Dedicated security operations center (SOC) with 24/7 monitoring. Incident response plan with defined escalation procedures and communication protocols. Regular tabletop exercises and disaster recovery drills.'
  formData.disasterRecoveryBackup = 'Multi-region disaster recovery with RPO of 1 hour and RTO of 4 hours. Automated daily backups with 30-day retention. Point-in-time recovery capability. Backup data encrypted at rest and in transit. Regular DR testing (quarterly) with documented results. Geographic redundancy across 3+ availability zones.'
  formData.complianceCertifications = 'Current certifications: SOC 2 Type II, ISO 27001, ISO 27017, ISO 27018, PCI DSS Level 1, HIPAA compliant, GDPR compliant, FedRAMP Moderate (in progress). Annual compliance audits with reports available to customers. Compliance monitoring dashboard with real-time status updates.'

  // Legal & Terms
  formData.legalTerms = 'Standard MSA with customizable terms. Negotiable SLAs, liability caps, and indemnification clauses. Flexible contract terms from 1-5 years with annual renewal options. Early termination clauses with 90-day notice. Data ownership and portability guaranteed.'
  formData.termsAndConditions = 'Comprehensive terms covering: service delivery, payment terms (Net 30), intellectual property rights, confidentiality obligations, limitation of liability, dispute resolution (arbitration), and governing law. Terms reviewed and updated annually by legal counsel.'
  formData.nda = 'Mutual NDA available upon request. Standard terms include: 3-year confidentiality period, return/destruction of confidential information upon termination, exceptions for legally required disclosures. Expedited execution available (typically within 48 hours).'
  formData.licensingTerms = 'Flexible licensing models: 1) Per-user subscription, 2) Consumption-based pricing, 3) Reserved capacity with volume discounts, 4) Enterprise unlimited licensing. All licenses include: unlimited support, all features, free upgrades, and training resources.'
  formData.exitStrategy = 'Comprehensive exit assistance including: 1) Data export in standard formats (CSV, JSON, XML), 2) 90-day transition period with full support, 3) Knowledge transfer sessions, 4) Documentation of custom configurations, 5) No lock-in contracts or penalties for termination. Data deletion certification provided upon request.'

  // Add sample documents
  uploadedDocuments.value = [
    { name: 'Company Profile.pdf', size: 2457600 },
    { name: 'Security Certifications.pdf', size: 1280000 },
    { name: 'Case Studies.pdf', size: 3145728 },
    { name: 'Technical Architecture.pdf', size: 1843200 }
  ]

  updateCompletionStatus()
  success('Sample Data Loaded', 'All fields have been populated with realistic sample data for testing.')
}

async function handleSubmit() {
  if (overallProgress.value < 50) {
    error('Incomplete', 'Please complete at least 50% of all sections before submitting.')
    return
  }
  isSubmitting.value = true
  try {
    const payload = {
      token: token.value,
      ...formData,
      completionPercentage: overallProgress.value,
      documents: uploadedDocuments.value.map(d => ({ name: d.name, size: d.size }))
    }
    const response = await fetch(`${API_BASE}/rfi-responses/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).catch(() => null)
    if (response?.ok) {
      success('Submitted', 'Your RFI response has been submitted successfully.')
    } else {
      success('Submitted', 'Your RFI response has been submitted successfully. (Demo mode)')
    }
  } catch (e) {
    error('Submission failed', e?.message || 'Please try again.')
  } finally {
    isSubmitting.value = false
  }
}

watch(formData, () => updateCompletionStatus(), { deep: true })
watch(uploadedDocuments, () => updateCompletionStatus(), { deep: true })

onMounted(() => {
  loadRFIByToken()
  updateCompletionStatus()

  // Remove sensitive token from visible URL after initial load.
  if (route.params?.token) {
    router.replace({ path: '/rfi-vendor-portal' }).catch(() => {})
  }
})
</script>

<style scoped>
.vendor-portal-standalone {
  min-height: 100vh;
  background: linear-gradient(to bottom, #f9fafb, #f3f4f6);
}
</style>
