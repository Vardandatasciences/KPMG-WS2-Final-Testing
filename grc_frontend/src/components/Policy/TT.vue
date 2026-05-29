<template>
  <div class="TT-page-wrapper">
    <!-- Add PopupModal component -->
    <PopupModal />

    <div v-if="asyncSimilarityMasterId" class="tt-async-banner">
      <p>{{ ttSimilarityBannerText }}</p>
      <button type="button" class="tt-async-banner-btn" @click="openSimilarityReview">
        Open review
      </button>
    </div>
    
    <!-- Breadcrumb Section for Selected Filters - Positioned at top -->
    <div v-if="selectedTab === 'framework' && selectedFramework && selectedFramework !== '' && getSelectedFrameworkName !== ''" class="filter-breadcrumbs">
      <div class="filter-breadcrumbs__item">
        <span class="filter-breadcrumbs__label">Framework:</span>
        <span class="filter-breadcrumbs__value">{{ getSelectedFrameworkName }}</span>
        <button class="filter-breadcrumbs__close" @click="clearFrameworkSelection" title="Clear Framework">
          <i class="fas fa-times icon-sm"></i>
        </button>
      </div>
    </div>
    
    <div v-if="selectedTab === 'policy' && ((selectedFramework && selectedFramework !== '' && getSelectedFrameworkName !== '') || (selectedPolicy && selectedPolicy !== '' && getSelectedPolicyName !== ''))" class="filter-breadcrumbs">
      <div v-if="selectedFramework && selectedFramework !== '' && getSelectedFrameworkName !== ''" class="filter-breadcrumbs__item">
        <span class="filter-breadcrumbs__label">Framework:</span>
        <span class="filter-breadcrumbs__value">{{ getSelectedFrameworkName }}</span>
        <button class="filter-breadcrumbs__close" @click="clearFrameworkSelection" title="Clear Framework">
          <i class="fas fa-times icon-sm"></i>
        </button>
      </div>
      <div v-if="selectedPolicy && selectedPolicy !== '' && getSelectedPolicyName !== ''" class="filter-breadcrumbs__item">
        <span class="filter-breadcrumbs__label">Policy:</span>
        <span class="filter-breadcrumbs__value">{{ getSelectedPolicyName }}</span>
        <button class="filter-breadcrumbs__close" @click="clearPolicySelection" title="Clear Policy">
          <i class="fas fa-times icon-sm"></i>
        </button>
      </div>
    </div>
    
    <div class="tt-page-header">
      <h2>Tailoring &amp; Templating</h2>
      <div class="tt-intro-text">
        <p>Customize frameworks and policies to meet your organization's specific needs and requirements.</p>
        <div class="tt-info-cards">
          <div class="tt-info-card">
            <div class="tt-info-card-icon icon-container">
              <i class="fas fa-cogs icon-lg icon-primary"></i>
            </div>
            <div class="tt-info-card-content">
              <h3>Framework Tailoring</h3>
              <p>Adapt internal frameworks to fit your organization's structure and compliance needs.</p>
            </div>
          </div>
          <div class="tt-info-card">
            <div class="tt-info-card-icon icon-container">
              <i class="fas fa-file-alt icon-lg icon-primary"></i>
            </div>
            <div class="tt-info-card-content">
              <h3>Policy Templating</h3>
              <p>Create standardized policy templates that can be reused across different departments.</p>
            </div>
          </div>
          <div class="tt-info-card">
            <div class="tt-info-card-icon icon-container">
              <i class="fas fa-check-circle icon-lg icon-primary"></i>
            </div>
            <div class="tt-info-card-content">
              <h3>Compliance Alignment</h3>
              <p>Ensure your policies align with regulatory requirements and industry standards.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="toggle-group">
      <button :class="['toggle-button', { 'active': selectedTab === 'framework' } ]" @click="selectTab('framework')">Framework</button>
      <button :class="['toggle-button', { 'active': selectedTab === 'policy' } ]" @click="selectTab('policy')">Policy</button>
      </div>
    <div v-if="selectedTab === 'framework'" class="TT-top-dropdowns">
      <div class="TT-dropdown-wrapper">
        <CustomDropdown
          v-model="selectedFramework"
          :config="{
            label: 'Framework',
            values: frameworks.map(fw => ({ 
              value: fw.id, 
              label: `${fw.name} (${fw.category || 'No Category'}) - ${fw.status || 'No Status'}`
            })),
            defaultLabel: 'Select Framework'
          }"
          :showSearchBar="true"
          style="min-width: 300px; max-width: 360px; width: 340px;"
          :title="selectedFramework ? frameworks.find(fw => fw.id === selectedFramework)?.name : ''"
        />
        <div class="TT-info-icon icon-container" @click="showFrameworkInfo = !showFrameworkInfo">
          <i class="fas fa-info-circle icon-md icon-info"></i>
        </div>
        <div v-if="showFrameworkInfo" class="TT-info-tooltip">Only internal frameworks can be tailored</div>
      </div>
      </div>
    <div v-else class="TT-top-dropdowns">
      <div class="TT-dropdown-wrapper">
        <CustomDropdown
          v-model="selectedFramework"
          :config="{
            label: 'Framework',
            values: frameworks.map(fw => ({ 
              value: fw.id, 
              label: `${fw.name} (${fw.category || 'No Category'}) - ${fw.status || 'No Status'}`
            })),
            defaultLabel: 'Select Framework'
          }"
          :showSearchBar="true"
          style="min-width: 300px; max-width: 360px; width: 360px;"
          :title="selectedFramework ? frameworks.find(fw => fw.id === selectedFramework)?.name : ''"
        />
        <div class="TT-info-icon icon-container" @click="showFrameworkInfo = !showFrameworkInfo">
          <i class="fas fa-info-circle icon-md icon-info"></i>
        </div>
        <div v-if="showFrameworkInfo" class="TT-info-tooltip">Only internal frameworks can be tailored</div>
      </div>
      <CustomDropdown
        v-model="selectedPolicy"
        :config="{
          label: 'Policy',
          values: policies.map(pol => ({ 
            value: pol.id, 
            label: `${pol.name} (${pol.status || 'No Status'})`
          })),
          defaultLabel: 'Select Policy'
        }"
        :showSearchBar="true"
        style="min-width: 300px; max-width: 360px; width: 360px;"
        :title="selectedPolicy ? policies.find(pol => pol.id === selectedPolicy)?.name : ''"
      />

      </div>
    
    <div v-if="selectedTab === 'framework' && selectedFramework">
      <div class="TT-container global-form-box">
        <!-- Framework Form -->
        <form @submit.prevent="submitTailoredFramework">
          <div class="global-form-group">
            <label class="global-form-label">
              Framework Name <span class="global-form-label-required">*</span>
              <!-- Data Type Circle Toggle -->
              <div class="policy-data-type-circle-toggle-wrapper">
                <div class="policy-data-type-circle-toggle">
                  <div 
                    class="policy-circle-option personal-circle" 
                    :class="{ active: fieldDataTypes.frameworkName === 'personal' }"
                    @click.stop.prevent="setDataType('frameworkName', 'personal')"
                    title="Personal Data"
                  >
                    <div class="policy-circle-inner"></div>
                  </div>
                  <div 
                    class="policy-circle-option confidential-circle" 
                    :class="{ active: fieldDataTypes.frameworkName === 'confidential' }"
                    @click.stop.prevent="setDataType('frameworkName', 'confidential')"
                    title="Confidential Data"
                  >
                    <div class="policy-circle-inner"></div>
                  </div>
                  <div 
                    class="policy-circle-option regular-circle" 
                    :class="{ active: !fieldDataTypes.frameworkName || fieldDataTypes.frameworkName === 'regular' }"
                    @click.stop.prevent="setDataType('frameworkName', 'regular')"
                    title="Regular Data"
                  >
                    <div class="policy-circle-inner"></div>
                  </div>
                </div>
              </div>
            </label>
            <input class="global-form-input" v-model="frameworkForm.name" type="text" required placeholder="Enter Framework name" @input="validateFrameworkName($event.target.value)" />
            <div v-if="error && error.includes('Framework name')" class="global-form-error-message">{{ error }}</div>
            <div v-else class="global-form-helper-text">Enter a descriptive name for your framework</div>
          </div>
          <div class="global-form-row single-column">
            <div class="global-form-group">
              <label class="global-form-label">
                Description <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkDescription === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkDescription', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkDescription === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkDescription', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkDescription || fieldDataTypes.frameworkDescription === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkDescription', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="frameworkForm.description" rows="3" required placeholder="Enter framework description"></textarea>
              <div class="global-form-helper-text">Describe the purpose, scope, and objectives of this framework</div>
            </div>
          </div>
          <div class="global-form-row">
            <div class="global-form-group">
              <label class="global-form-label">
                Identifier <span class="global-form-label-required">*</span> <span class="auto-generated-label">(Auto-generated)</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkIdentifier === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkIdentifier', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkIdentifier === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkIdentifier', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkIdentifier || fieldDataTypes.frameworkIdentifier === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkIdentifier', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-input" v-model="frameworkForm.identifier" type="text" required placeholder="Enter Identifier" readonly />
              <div class="global-form-helper-text">Auto-generated based on framework name</div>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Category <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkCategory === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkCategory', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkCategory === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkCategory', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkCategory || fieldDataTypes.frameworkCategory === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkCategory', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-input" v-model="frameworkForm.category" type="text" required placeholder="Enter category" />
              <div class="global-form-helper-text">e.g., Security, Compliance, Risk Management, etc.</div>
            </div>
          </div>
          <div class="global-form-row">
            <div class="global-form-group">
              <label class="global-form-label">
                Internal/External <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkInternalExternal === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkInternalExternal', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkInternalExternal === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkInternalExternal', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkInternalExternal || fieldDataTypes.frameworkInternalExternal === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkInternalExternal', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <select class="global-form-select" v-model="frameworkForm.internalExternal" required>
                <option value="" disabled>Select Type</option>
                <option value="Internal">Internal</option>
                <option value="External">External</option>
              </select>
              <div class="global-form-helper-text">Select whether this framework is for internal or external use</div>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Upload Document
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkDocument === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkDocument', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkDocument === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkDocument', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkDocument || fieldDataTypes.frameworkDocument === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkDocument', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-file-input" type="file" @change="handleFileUpload" />
              <div class="global-form-helper-text">Upload a supporting document for this framework (optional)</div>
            </div>
          </div>
          <div class="global-form-row">
            <div class="global-form-group">
              <label class="global-form-label">
                Effective Start Date <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkStartDate === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkStartDate', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkStartDate === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkStartDate', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkStartDate || fieldDataTypes.frameworkStartDate === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkStartDate', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-date-input" v-model="frameworkForm.startDate" type="date" required />
              <div class="global-form-helper-text">Date when the framework implementation begins</div>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Effective End Date
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkEndDate === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkEndDate', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkEndDate === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkEndDate', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkEndDate || fieldDataTypes.frameworkEndDate === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkEndDate', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-date-input" v-model="frameworkForm.endDate" type="date" />
              <div class="global-form-helper-text">Date when the framework expires or requires review</div>
            </div>
          </div>
          <div class="global-form-row">
            <div class="global-form-group">
              <label class="global-form-label">
                Created By <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkCreatedBy === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkCreatedBy', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkCreatedBy === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkCreatedBy', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkCreatedBy || fieldDataTypes.frameworkCreatedBy === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkCreatedBy', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-input" :value="currentUser.UserName || loggedInUsername" type="text" disabled />
              <div class="global-form-helper-text">Automatically set to logged in user</div>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Reviewer <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: fieldDataTypes.frameworkReviewer === 'personal' }"
                      @click.stop.prevent="setDataType('frameworkReviewer', 'personal')"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: fieldDataTypes.frameworkReviewer === 'confidential' }"
                      @click.stop.prevent="setDataType('frameworkReviewer', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !fieldDataTypes.frameworkReviewer || fieldDataTypes.frameworkReviewer === 'regular' }"
                      @click.stop.prevent="setDataType('frameworkReviewer', 'regular')"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <select class="global-form-select" v-model="frameworkForm.reviewer" required>
                <option value="">Select Reviewer</option>
                <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
              </select>
              <div class="global-form-helper-text">Select who will review this framework</div>
              <div v-if="isFrameworkCreatorReviewerSame" class="global-form-error-message" style="margin-top: 8px;">
                <i class="fas fa-exclamation-triangle"></i>
                Creator and reviewer cannot be the same person. Please select a different reviewer.
              </div>
            </div>
          </div>
        </form>
            </div>
      <!-- Policy Tabbed/Stepper Container (Framework Mode) -->
      <div class="TT-policy-tabs-container">
        <div class="TT-policy-tabs-row">
          <div class="TT-policy-tabs">
            <button v-for="(tab, idx) in policyTabs" :key="tab.id" :class="['btn TT-policy-tab', { 'TT-policy-tab-active': idx === activePolicyTab }]" @click="activePolicyTab = idx">
              Policy {{ idx + 1 }}
            </button>
            <button class="btn-add" @click="addPolicyTab">
              <i class="fas fa-plus icon-md"></i>
              Add Policy
            </button>
              </div>
            </div>
        <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="TT-policy-form-container">
          <button class="TT-exclude-policy-btn" @click="excludePolicyTab(activePolicyTab)">Exclude</button>
          <form @submit.prevent="submitTailoredFramework" :key="policyTabs[activePolicyTab].id">
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Name <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyName === 'personal') }"
                        @click.stop.prevent="setDataType('policyName', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyName === 'confidential') }"
                        @click.stop.prevent="setDataType('policyName', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyName || policyFieldDataTypes[activePolicyTab].policyName === 'regular' }"
                        @click.stop.prevent="setDataType('policyName', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].name" type="text" required placeholder="Enter policy name" @input="handlePolicyNameChange(activePolicyTab, $event.target.value)" />
                <small v-if="error && error.includes('Policy name')" class="global-form-error-message">{{ error }}</small>
                <small v-else class="global-form-helper-text">Use a clear, descriptive name</small>
          </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Identifier <span class="global-form-label-required">*</span> 
                  <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                  <span v-else class="manual-entry-label">(Manual entry)</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyIdentifier === 'personal') }"
                        @click.stop.prevent="setDataType('policyIdentifier', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyIdentifier === 'confidential') }"
                        @click.stop.prevent="setDataType('policyIdentifier', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyIdentifier || policyFieldDataTypes[activePolicyTab].policyIdentifier === 'regular' }"
                        @click.stop.prevent="setDataType('policyIdentifier', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].identifier" type="text" required placeholder="Enter policy identifier" :readonly="isInternalFramework()" />
                <small class="global-form-helper-text">{{ isInternalFramework() ? 'Auto-generated based on policy name' : 'Enter a unique identifier for this policy' }}</small>
        </div>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Description <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDescription === 'personal') }"
                      @click.stop.prevent="setDataType('policyDescription', 'personal', activePolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDescription === 'confidential') }"
                      @click.stop.prevent="setDataType('policyDescription', 'confidential', activePolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyDescription || policyFieldDataTypes[activePolicyTab].policyDescription === 'regular' }"
                      @click.stop.prevent="setDataType('policyDescription', 'regular', activePolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].description" rows="3" required placeholder="Enter policy description"></textarea>
              <small class="global-form-helper-text">Describe the policy's purpose, requirements, and key provisions</small>
          </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Scope <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyScope === 'personal') }"
                        @click.stop.prevent="setDataType('policyScope', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyScope === 'confidential') }"
                        @click.stop.prevent="setDataType('policyScope', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyScope || policyFieldDataTypes[activePolicyTab].policyScope === 'regular' }"
                        @click.stop.prevent="setDataType('policyScope', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].scope" type="text" required placeholder="Enter policy scope" />
                <small class="global-form-helper-text">Specify what areas/processes/systems policy applies to</small>
            </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Department <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDepartment === 'personal') }"
                        @click.stop.prevent="setDataType('policyDepartment', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDepartment === 'confidential') }"
                        @click.stop.prevent="setDataType('policyDepartment', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyDepartment || policyFieldDataTypes[activePolicyTab].policyDepartment === 'regular' }"
                        @click.stop.prevent="setDataType('policyDepartment', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <select class="global-form-select" v-model="policyTabs[activePolicyTab].department" required>
                  <option value="">Select Department</option>
                  <option
                    v-if="policyTabs[activePolicyTab].department && !getDepartmentDropdownOptions(activePolicyTab).includes(policyTabs[activePolicyTab].department)"
                    :value="policyTabs[activePolicyTab].department"
                  >
                    {{ policyTabs[activePolicyTab].department }}
                  </option>
                  <option v-for="deptName in getDepartmentDropdownOptions(activePolicyTab)" :key="deptName" :value="deptName">
                    {{ deptName }}
                  </option>
                </select>
                <small class="global-form-helper-text">Select department from the available list</small>
          </div>
              </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Objective <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyObjective === 'personal') }"
                      @click.stop.prevent="setDataType('policyObjective', 'personal', activePolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyObjective === 'confidential') }"
                      @click.stop.prevent="setDataType('policyObjective', 'confidential', activePolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyObjective || policyFieldDataTypes[activePolicyTab].policyObjective === 'regular' }"
                      @click.stop.prevent="setDataType('policyObjective', 'regular', activePolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].objective" rows="3" required placeholder="Enter policy objective"></textarea>
              <small class="global-form-helper-text">Explain what this policy is designed to accomplish</small>
                </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Coverage Rate (%) <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCoverageRate === 'personal') }"
                        @click.stop.prevent="setDataType('policyCoverageRate', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCoverageRate === 'confidential') }"
                        @click.stop.prevent="setDataType('policyCoverageRate', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyCoverageRate || policyFieldDataTypes[activePolicyTab].policyCoverageRate === 'regular' }"
                        @click.stop.prevent="setDataType('policyCoverageRate', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].coverageRate" type="number" min="0" max="100" step="0.01" required placeholder="Enter coverage rate" />
                <small class="global-form-helper-text">Range: 0-100, step: 0.01</small>
                </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Applicability <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyApplicability === 'personal') }"
                        @click.stop.prevent="setDataType('policyApplicability', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyApplicability === 'confidential') }"
                        @click.stop.prevent="setDataType('policyApplicability', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyApplicability || policyFieldDataTypes[activePolicyTab].policyApplicability === 'regular' }"
                        @click.stop.prevent="setDataType('policyApplicability', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].applicability" type="text" required placeholder="Enter applicability" />
                <small class="global-form-helper-text">Define the target audience, roles, or entities</small>
              </div>
              </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Type <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyType === 'personal') }"
                        @click.stop.prevent="setDataType('policyType', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyType === 'confidential') }"
                        @click.stop.prevent="setDataType('policyType', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyType || policyFieldDataTypes[activePolicyTab].policyType === 'regular' }"
                        @click.stop.prevent="setDataType('policyType', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="policy-type-multi-select" @click.stop>
                  <div class="policy-type-dropdown">
                    <div   
                      class="selected-policy-type" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyTypeDropdown }"
                      @click="togglePolicyTypeDropdown(activePolicyTab)"
                    >
                      <div class="policy-type-content">
                        <span v-if="policyTabs[activePolicyTab].type" class="policy-type-value">
                          {{ policyTabs[activePolicyTab].type }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy type
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyTypeDropdown" class="policy-type-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyTypeSearch"
                          type="text"
                          placeholder="Search or type new policy type..."
                          class="search-input"
                          @input="filterPolicyTypes(activePolicyTab)"
                          @keyup.enter="createNewPolicyType(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="type in getFilteredPolicyTypes(activePolicyTab)" 
                        :key="type" 
                        class="policy-type-option"
                        @click="selectPolicyType(activePolicyTab, type)"
                      >
                        <span class="policy-type-label">{{ type }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyTypeSearch && !getFilteredPolicyTypes(activePolicyTab).includes(policyTabs[activePolicyTab].policyTypeSearch)"
                        class="policy-type-option create-new-option"
                        @click="createNewPolicyType(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-type-label">Create "{{ policyTabs[activePolicyTab].policyTypeSearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="global-form-helper-text">Select from list or type new policy type</small>
              </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Category <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCategory === 'personal') }"
                        @click.stop.prevent="setDataType('policyCategory', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCategory === 'confidential') }"
                        @click.stop.prevent="setDataType('policyCategory', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyCategory || policyFieldDataTypes[activePolicyTab].policyCategory === 'regular' }"
                        @click.stop.prevent="setDataType('policyCategory', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="policy-category-multi-select" @click.stop>
                  <div class="policy-category-dropdown">
                    <div   
                      class="selected-policy-category" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyCategoryDropdown }"
                      @click="togglePolicyCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-category-content">
                        <span v-if="policyTabs[activePolicyTab].category" class="policy-category-value">
                          {{ policyTabs[activePolicyTab].category }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyCategoryDropdown" class="policy-category-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyCategorySearch"
                          type="text"
                          placeholder="Search or type new category..."
                          class="search-input"
                          @input="filterPolicyCategories(activePolicyTab)"
                          @keyup.enter="createNewPolicyCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="category in getFilteredPolicyCategories(activePolicyTab)" 
                        :key="category" 
                        class="policy-category-option"
                        @click="selectPolicyCategory(activePolicyTab, category)"
                      >
                        <span class="policy-category-label">{{ category }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyCategorySearch && !getFilteredPolicyCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policyCategorySearch)"
                        class="policy-category-option create-new-option"
                        @click="createNewPolicyCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-category-label">Create "{{ policyTabs[activePolicyTab].policyCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="global-form-helper-text">Select from list or type new policy category</small>
              </div>
              </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Sub Category <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policySubCategory === 'personal') }"
                        @click.stop.prevent="setDataType('policySubCategory', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policySubCategory === 'confidential') }"
                        @click.stop.prevent="setDataType('policySubCategory', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policySubCategory || policyFieldDataTypes[activePolicyTab].policySubCategory === 'regular' }"
                        @click.stop.prevent="setDataType('policySubCategory', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="policy-subcategory-multi-select" @click.stop>
                  <div class="policy-subcategory-dropdown">
                    <div   
                      class="selected-policy-subcategory" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicySubCategoryDropdown }"
                      @click="togglePolicySubCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-subcategory-content">
                        <span v-if="policyTabs[activePolicyTab].subCategory" class="policy-subcategory-value">
                          {{ policyTabs[activePolicyTab].subCategory }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new sub category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicySubCategoryDropdown" class="policy-subcategory-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policySubCategorySearch"
                          type="text"
                          placeholder="Search or type new sub category..."
                          class="search-input"
                          @input="filterPolicySubCategories(activePolicyTab)"
                          @keyup.enter="createNewPolicySubCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="subCategory in getFilteredPolicySubCategories(activePolicyTab)" 
                        :key="subCategory" 
                        class="policy-subcategory-option"
                        @click="selectPolicySubCategory(activePolicyTab, subCategory)"
                      >
                        <span class="policy-subcategory-label">{{ subCategory }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policySubCategorySearch && !getFilteredPolicySubCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policySubCategorySearch)"
                        class="policy-subcategory-option create-new-option"
                        @click="createNewPolicySubCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-subcategory-label">Create "{{ policyTabs[activePolicyTab].policySubCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="global-form-helper-text">Select from list or type new policy sub category</small>
              </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Applicable Entities <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEntities === 'personal') }"
                        @click.stop.prevent="setDataType('policyEntities', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEntities === 'confidential') }"
                        @click.stop.prevent="setDataType('policyEntities', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyEntities || policyFieldDataTypes[activePolicyTab].policyEntities === 'regular' }"
                        @click.stop.prevent="setDataType('policyEntities', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="form-row">
                  <div class="form-group entities-group">
                    <div class="entities-multi-select" @click.stop>
                      <div class="entities-dropdown">
                        <div 
                          class="selected-entities" 
                          :class="{ 
                            'active': policyTabs[activePolicyTab]?.showEntitiesDropdown,
                            'error': error && error.includes('entities')
                          }"
                          @click="toggleEntitiesDropdown(activePolicyTab)"
                        >
                          <div class="entity-content">
                            <span v-if="loading" class="loading-text">
                              Loading entities...
                            </span>
                            <span v-else-if="isAllEntitiesSelected(activePolicyTab)" class="entity-tag all-tag">
                              All Locations
                            </span>
                            <span v-else-if="getSelectedEntitiesCount(activePolicyTab) === 0" class="placeholder">
                              Select entities...
                            </span>
                            <span v-else class="entity-count">
                              {{ getSelectedEntitiesCount(activePolicyTab) }} location(s) selected
                            </span>
                          </div>
                          <i class="fas fa-chevron-down dropdown-arrow"></i>
                        </div>
                        <div v-if="policyTabs[activePolicyTab]?.showEntitiesDropdown" class="entities-options">
                          <div v-if="loading" class="entities-loading">
                            Loading entities...
                          </div>
                          <div v-else-if="error" class="entities-error">
                            {{ error }}
                          </div>
                          <template v-else>
                            <div 
                              v-for="entity in entities" 
                              :key="entity.id" 
                              :class="['entity-option', { 'all-option': entity.id === 'all' }]"
                              @click="selectEntity(activePolicyTab, entity.id)"
                            >
                              <input 
                                type="checkbox" 
                                :checked="entity.id === 'all' ? isAllEntitiesSelected(activePolicyTab) : isEntitySelected(activePolicyTab, entity.id)"
                                @change="handleEntitySelection(activePolicyTab, entity.id, $event.target.checked)"
                                @click.stop
                              />
                              <span class="entity-label">{{ entity.label }}</span>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <small v-if="error && error.includes('entities')" class="global-form-error-message">
                  {{ error }}
                </small>
                </div>
                </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Start Date <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyStartDate === 'personal') }"
                        @click.stop.prevent="setDataType('policyStartDate', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyStartDate === 'confidential') }"
                        @click.stop.prevent="setDataType('policyStartDate', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyStartDate || policyFieldDataTypes[activePolicyTab].policyStartDate === 'regular' }"
                        @click.stop.prevent="setDataType('policyStartDate', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].startDate" type="date" required />
                <small class="global-form-helper-text">Date when this policy takes effect</small>
              </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  End Date
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEndDate === 'personal') }"
                        @click.stop.prevent="setDataType('policyEndDate', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEndDate === 'confidential') }"
                        @click.stop.prevent="setDataType('policyEndDate', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyEndDate || policyFieldDataTypes[activePolicyTab].policyEndDate === 'regular' }"
                        @click.stop.prevent="setDataType('policyEndDate', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].endDate" type="date" />
                <small class="global-form-helper-text">Date when this policy expires or requires review/renewal</small>
                  </div>
                </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Upload Document
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDocument === 'personal') }"
                      @click.stop.prevent="setDataType('policyDocument', 'personal', activePolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDocument === 'confidential') }"
                      @click.stop.prevent="setDataType('policyDocument', 'confidential', activePolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyDocument || policyFieldDataTypes[activePolicyTab].policyDocument === 'regular' }"
                      @click.stop.prevent="setDataType('policyDocument', 'regular', activePolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-input" type="file" @change="e => handlePolicyFileUpload(e, activePolicyTab)" />
              <small class="global-form-helper-text">Upload supporting documentation (optional)</small>
                  </div>
          </form>
                </div>
              </div>
      <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="TT-subpolicy-tabs-container">
        <div class="TT-subpolicy-tabs-row">
          <div class="TT-subpolicy-tabs">
            <button v-for="(subTab, subIdx) in policyTabs[activePolicyTab].subPolicies" :key="subTab.id" :class="['btn TT-subpolicy-tab', { 'TT-subpolicy-tab-active': subIdx === policyTabs[activePolicyTab].activeSubPolicyTab }]" @click="policyTabs[activePolicyTab].activeSubPolicyTab = subIdx">
              Subpolicy {{ subIdx + 1 }}
            </button>
            <button class="btn-add" @click="addSubPolicyTab(activePolicyTab)">
              <i class="fas fa-plus icon-md"></i>
              Add Sub Policy
            </button>
                  </div>
                </div>
        <div v-if="policyTabs[activePolicyTab].subPolicies && policyTabs[activePolicyTab].subPolicies.length" class="TT-subpolicy-form-container">
          <button class="TT-exclude-subpolicy-btn" @click="excludeSubPolicyTab(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)">Exclude</button>
          <form>
            <div class="global-form-row">
              <div class="global-form-group">
              <label class="global-form-label">
                Sub Policy Name <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyName === 'personal') }"
                      @click.stop.prevent="setDataType('subPolicyName', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyName === 'confidential') }"
                      @click.stop.prevent="setDataType('subPolicyName', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyName === 'regular') }"
                      @click.stop.prevent="setDataType('subPolicyName', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
                              <input class="global-form-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].name" type="text" required placeholder="Enter sub policy name" @input="handleSubPolicyNameChange(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab, $event.target.value)" />
              <small v-if="error && error.includes('Subpolicy name')" class="global-form-error-message">{{ error }}</small>
              <small v-else class="global-form-helper-text">Use a clear name that describes this sub-policy's specific focus</small>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Identifier <span class="global-form-label-required">*</span> 
                <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                <span v-else class="manual-entry-label">(Manual entry)</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyIdentifier === 'personal') }"
                      @click.stop.prevent="setDataType('subPolicyIdentifier', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyIdentifier === 'confidential') }"
                      @click.stop.prevent="setDataType('subPolicyIdentifier', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyIdentifier === 'regular') }"
                      @click.stop.prevent="setDataType('subPolicyIdentifier', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].identifier" type="text" required placeholder="Enter identifier" :readonly="isInternalFramework()" />
              <small class="global-form-helper-text">{{ isInternalFramework() ? 'Auto-generated based on parent policy identifier' : 'Enter a unique identifier for this sub-policy' }}</small>
                      </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Control <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyControl === 'personal') }"
                      @click.stop.prevent="setDataType('subPolicyControl', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyControl === 'confidential') }"
                      @click.stop.prevent="setDataType('subPolicyControl', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyControl === 'regular') }"
                      @click.stop.prevent="setDataType('subPolicyControl', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].control" rows="3" required placeholder="Enter control"></textarea>
              <small class="global-form-helper-text">Specify the control mechanisms, procedures, or safeguards to be implemented</small>
                        </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Description <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyDescription === 'personal') }"
                      @click.stop.prevent="setDataType('subPolicyDescription', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyDescription === 'confidential') }"
                      @click.stop.prevent="setDataType('subPolicyDescription', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyDescription === 'regular') }"
                      @click.stop.prevent="setDataType('subPolicyDescription', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].description" rows="3" required placeholder="Enter description"></textarea>
              <small class="global-form-helper-text">Explain the intent, requirements, or significance of this sub-policy</small>
                      </div>
            </div>
          </form>
                    </div>
                  </div>
                </div>
    <div v-else-if="selectedTab === 'framework' && !selectedFramework">
      <!-- Optionally, you can show a message here: Please select a framework -->
    </div>
    <div v-if="selectedTab === 'framework' && selectedFramework" class="TT-universal-submit-wrapper">
      <button class="btn-submit" @click="submitTailoredFramework" :disabled="isFrameworkCreatorReviewerSame || ttFrameworkCreateInFlight">Submit</button>
    </div>
    <div v-if="selectedTab === 'policy' && selectedFramework && selectedPolicy">
      <div class="TT-policy-tabs-container">
        <div class="TT-policy-tabs-row">
          <div class="TT-policy-tabs">
            <button v-for="(tab, idx) in policyTabs" :key="tab.id" :class="['btn TT-policy-tab', { 'TT-policy-tab-active': idx === activePolicyTab }]" @click="activePolicyTab = idx">
              Policy {{ idx + 1 }}
            </button>
            <!-- Only show + Add Policy in framework mode -->
            <button v-if="selectedTab === 'framework'" class="btn-add" @click="addPolicyTab">
              <i class="fas fa-plus icon-md"></i>
              Add Policy
            </button>
              </div>
                </div>
        <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="TT-policy-form-container">
          <!-- Only show Exclude in framework mode -->
          <button v-if="selectedTab === 'framework'" class="TT-exclude-policy-btn" @click="excludePolicyTab(activePolicyTab)">Exclude</button>
          <form @submit.prevent="submitTailoredPolicy" :key="policyTabs[activePolicyTab].id">
            <!-- Same policy form as above -->
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Name <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyName === 'personal') }"
                        @click.stop.prevent="setDataType('policyName', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyName === 'confidential') }"
                        @click.stop.prevent="setDataType('policyName', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyName || policyFieldDataTypes[activePolicyTab].policyName === 'regular' }"
                        @click.stop.prevent="setDataType('policyName', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].name" type="text" required placeholder="Enter policy name" @input="handlePolicyNameChange(activePolicyTab, $event.target.value)" />
                <small v-if="error && error.includes('Policy name')" class="global-form-error-message">{{ error }}</small>
                <small v-else class="global-form-helper-text">Use a clear, descriptive name</small>
                </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Identifier <span class="global-form-label-required">*</span> 
                  <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                  <span v-else class="manual-entry-label">(Manual entry)</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyIdentifier === 'personal') }"
                        @click.stop.prevent="setDataType('policyIdentifier', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyIdentifier === 'confidential') }"
                        @click.stop.prevent="setDataType('policyIdentifier', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyIdentifier || policyFieldDataTypes[activePolicyTab].policyIdentifier === 'regular' }"
                        @click.stop.prevent="setDataType('policyIdentifier', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].identifier" type="text" required placeholder="Enter policy identifier" :readonly="isInternalFramework()" />
                <small class="global-form-helper-text">{{ isInternalFramework() ? 'Auto-generated based on policy name' : 'Enter a unique identifier for this policy' }}</small>
              </div>
              </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Description <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDescription === 'personal') }"
                      @click.stop.prevent="setDataType('policyDescription', 'personal', activePolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDescription === 'confidential') }"
                      @click.stop.prevent="setDataType('policyDescription', 'confidential', activePolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyDescription || policyFieldDataTypes[activePolicyTab].policyDescription === 'regular' }"
                      @click.stop.prevent="setDataType('policyDescription', 'regular', activePolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].description" rows="3" required placeholder="Enter policy description"></textarea>
              <small class="global-form-helper-text">Describe the policy's purpose, requirements, and key provisions</small>
            </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Scope <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyScope === 'personal') }"
                        @click.stop.prevent="setDataType('policyScope', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyScope === 'confidential') }"
                        @click.stop.prevent="setDataType('policyScope', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyScope || policyFieldDataTypes[activePolicyTab].policyScope === 'regular' }"
                        @click.stop.prevent="setDataType('policyScope', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].scope" type="text" required placeholder="Enter policy scope" />
                <small class="global-form-helper-text">Specify what areas/processes/systems policy applies to</small>
              </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Department <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDepartment === 'personal') }"
                        @click.stop.prevent="setDataType('policyDepartment', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDepartment === 'confidential') }"
                        @click.stop.prevent="setDataType('policyDepartment', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyDepartment || policyFieldDataTypes[activePolicyTab].policyDepartment === 'regular' }"
                        @click.stop.prevent="setDataType('policyDepartment', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <select class="global-form-select" v-model="policyTabs[activePolicyTab].department" required>
                  <option value="">Select Department</option>
                  <option
                    v-if="policyTabs[activePolicyTab].department && !getDepartmentDropdownOptions(activePolicyTab).includes(policyTabs[activePolicyTab].department)"
                    :value="policyTabs[activePolicyTab].department"
                  >
                    {{ policyTabs[activePolicyTab].department }}
                  </option>
                  <option v-for="deptName in getDepartmentDropdownOptions(activePolicyTab)" :key="deptName" :value="deptName">
                    {{ deptName }}
                  </option>
                </select>
                <small class="global-form-helper-text">Select department from the available list</small>
                </div>
              </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Objective <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyObjective === 'personal') }"
                      @click.stop.prevent="setDataType('policyObjective', 'personal', activePolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyObjective === 'confidential') }"
                      @click.stop.prevent="setDataType('policyObjective', 'confidential', activePolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyObjective || policyFieldDataTypes[activePolicyTab].policyObjective === 'regular' }"
                      @click.stop.prevent="setDataType('policyObjective', 'regular', activePolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].objective" rows="3" required placeholder="Enter policy objective"></textarea>
              <small class="global-form-helper-text">Explain what this policy is designed to accomplish</small>
                </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Coverage Rate (%) <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCoverageRate === 'personal') }"
                        @click.stop.prevent="setDataType('policyCoverageRate', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCoverageRate === 'confidential') }"
                        @click.stop.prevent="setDataType('policyCoverageRate', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyCoverageRate || policyFieldDataTypes[activePolicyTab].policyCoverageRate === 'regular' }"
                        @click.stop.prevent="setDataType('policyCoverageRate', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].coverageRate" type="number" min="0" max="100" step="0.01" required placeholder="Enter coverage rate" />
                <small class="global-form-helper-text">Range: 0-100, step: 0.01</small>
                </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Applicability <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyApplicability === 'personal') }"
                        @click.stop.prevent="setDataType('policyApplicability', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyApplicability === 'confidential') }"
                        @click.stop.prevent="setDataType('policyApplicability', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyApplicability || policyFieldDataTypes[activePolicyTab].policyApplicability === 'regular' }"
                        @click.stop.prevent="setDataType('policyApplicability', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].applicability" type="text" required placeholder="Enter applicability" />
                <small class="global-form-helper-text">Define the target audience, roles, or entities</small>
                </div>
                </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Type <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyType === 'personal') }"
                        @click.stop.prevent="setDataType('policyType', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyType === 'confidential') }"
                        @click.stop.prevent="setDataType('policyType', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyType || policyFieldDataTypes[activePolicyTab].policyType === 'regular' }"
                        @click.stop.prevent="setDataType('policyType', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="policy-type-multi-select" @click.stop>
                  <div class="policy-type-dropdown">
                    <div   
                      class="selected-policy-type" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyTypeDropdown }"
                      @click="togglePolicyTypeDropdown(activePolicyTab)"
                    >
                      <div class="policy-type-content">
                        <span v-if="policyTabs[activePolicyTab].type" class="policy-type-value">
                          {{ policyTabs[activePolicyTab].type }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy type
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyTypeDropdown" class="policy-type-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyTypeSearch"
                          type="text"
                          placeholder="Search or type new policy type..."
                          class="search-input"
                          @input="filterPolicyTypes()"
                          @keyup.enter="createNewPolicyType(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="type in getFilteredPolicyTypes(activePolicyTab)" 
                        :key="type" 
                        class="policy-type-option"
                        @click="selectPolicyType(activePolicyTab, type)"
                      >
                        <span class="policy-type-label">{{ type }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyTypeSearch && !getFilteredPolicyTypes(activePolicyTab).includes(policyTabs[activePolicyTab].policyTypeSearch)"
                        class="policy-type-option create-new-option"
                        @click="createNewPolicyType(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-type-label">Create "{{ policyTabs[activePolicyTab].policyTypeSearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="global-form-helper-text">Select from list or type new policy type</small>
              </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Category <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCategory === 'personal') }"
                        @click.stop.prevent="setDataType('policyCategory', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCategory === 'confidential') }"
                        @click.stop.prevent="setDataType('policyCategory', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyCategory || policyFieldDataTypes[activePolicyTab].policyCategory === 'regular' }"
                        @click.stop.prevent="setDataType('policyCategory', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="policy-category-multi-select" @click.stop>
                  <div class="policy-category-dropdown">
                    <div   
                      class="selected-policy-category" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicyCategoryDropdown }"
                      @click="togglePolicyCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-category-content">
                        <span v-if="policyTabs[activePolicyTab].category" class="policy-category-value">
                          {{ policyTabs[activePolicyTab].category }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicyCategoryDropdown" class="policy-category-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policyCategorySearch"
                          type="text"
                          placeholder="Search or type new policy category..."
                          class="search-input"
                          @input="filterPolicyCategories()"
                          @keyup.enter="createNewPolicyCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="category in getFilteredPolicyCategories(activePolicyTab)" 
                        :key="category" 
                        class="policy-category-option"
                        @click="selectPolicyCategory(activePolicyTab, category)"
                      >
                        <span class="policy-category-label">{{ category }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policyCategorySearch && !getFilteredPolicyCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policyCategorySearch)"
                        class="policy-category-option create-new-option"
                        @click="createNewPolicyCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-category-label">Create "{{ policyTabs[activePolicyTab].policyCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="global-form-helper-text">Select from list or type new policy category</small>
              </div>
            </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Policy Sub Category <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policySubCategory === 'personal') }"
                        @click.stop.prevent="setDataType('policySubCategory', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policySubCategory === 'confidential') }"
                        @click.stop.prevent="setDataType('policySubCategory', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policySubCategory || policyFieldDataTypes[activePolicyTab].policySubCategory === 'regular' }"
                        @click.stop.prevent="setDataType('policySubCategory', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="policy-subcategory-multi-select" @click.stop>
                  <div class="policy-subcategory-dropdown">
                    <div   
                      class="selected-policy-subcategory" 
                      :class="{ active: policyTabs[activePolicyTab].showPolicySubCategoryDropdown }"
                      @click="togglePolicySubCategoryDropdown(activePolicyTab)"
                    >
                      <div class="policy-subcategory-content">
                        <span v-if="policyTabs[activePolicyTab].subCategory" class="policy-subcategory-value">
                          {{ policyTabs[activePolicyTab].subCategory }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy sub category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policyTabs[activePolicyTab].showPolicySubCategoryDropdown" class="policy-subcategory-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policyTabs[activePolicyTab].policySubCategorySearch"
                          type="text"
                          placeholder="Search or type new policy sub category..."
                          class="search-input"
                          @input="filterPolicySubCategories()"
                          @keyup.enter="createNewPolicySubCategory(activePolicyTab)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="subCategory in getFilteredPolicySubCategories(activePolicyTab)" 
                        :key="subCategory" 
                        class="policy-subcategory-option"
                        @click="selectPolicySubCategory(activePolicyTab, subCategory)"
                      >
                        <span class="policy-subcategory-label">{{ subCategory }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policyTabs[activePolicyTab].policySubCategorySearch && !getFilteredPolicySubCategories(activePolicyTab).includes(policyTabs[activePolicyTab].policySubCategorySearch)"
                        class="policy-subcategory-option create-new-option"
                        @click="createNewPolicySubCategory(activePolicyTab)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-subcategory-label">Create "{{ policyTabs[activePolicyTab].policySubCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <small class="global-form-helper-text">Select from list or type new policy sub category</small>
              </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  Applicable Entities <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEntities === 'personal') }"
                        @click.stop.prevent="setDataType('policyEntities', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEntities === 'confidential') }"
                        @click.stop.prevent="setDataType('policyEntities', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyEntities || policyFieldDataTypes[activePolicyTab].policyEntities === 'regular' }"
                        @click.stop.prevent="setDataType('policyEntities', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="form-row">
                  <div class="form-group entities-group">
                    <div class="entities-multi-select" @click.stop>
                      <div class="entities-dropdown">
                        <div 
                          class="selected-entities" 
                          :class="{ 
                            'active': policyTabs[activePolicyTab]?.showEntitiesDropdown,
                            'error': error && error.includes('entities')
                          }"
                          @click="toggleEntitiesDropdown(activePolicyTab)"
                        >
                          <div class="entity-content">
                            <span v-if="loading" class="loading-text">
                              Loading entities...
                            </span>
                            <span v-else-if="isAllEntitiesSelected(activePolicyTab)" class="entity-tag all-tag">
                              All Locations
                            </span>
                            <span v-else-if="getSelectedEntitiesCount(activePolicyTab) === 0" class="placeholder">
                              Select entities...
                            </span>
                            <span v-else class="entity-count">
                              {{ getSelectedEntitiesCount(activePolicyTab) }} location(s) selected
                            </span>
                          </div>
                          <i class="fas fa-chevron-down dropdown-arrow"></i>
                        </div>
                        <div v-if="policyTabs[activePolicyTab]?.showEntitiesDropdown" class="entities-options">
                          <div v-if="loading" class="entities-loading">
                            Loading entities...
                          </div>
                          <div v-else-if="error" class="entities-error">
                            {{ error }}
                          </div>
                          <template v-else>
                            <div 
                              v-for="entity in entities" 
                              :key="entity.id" 
                              :class="['entity-option', { 'all-option': entity.id === 'all' }]"
                              @click="selectEntity(activePolicyTab, entity.id)"
                            >
                              <input 
                                type="checkbox" 
                                :checked="entity.id === 'all' ? isAllEntitiesSelected(activePolicyTab) : isEntitySelected(activePolicyTab, entity.id)"
                                @change="handleEntitySelection(activePolicyTab, entity.id, $event.target.checked)"
                                @click.stop
                              />
                              <span class="entity-label">{{ entity.label }}</span>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
          </div>
        </div>
            <div class="global-form-row">
              <div class="global-form-group">
                <label class="global-form-label">
                  Start Date <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyStartDate === 'personal') }"
                        @click.stop.prevent="setDataType('policyStartDate', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyStartDate === 'confidential') }"
                        @click.stop.prevent="setDataType('policyStartDate', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyStartDate || policyFieldDataTypes[activePolicyTab].policyStartDate === 'regular' }"
                        @click.stop.prevent="setDataType('policyStartDate', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].startDate" type="date" required />
                <small class="global-form-helper-text">Date when this policy takes effect</small>
      </div>
              <div class="global-form-group">
                <label class="global-form-label">
                  End Date
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEndDate === 'personal') }"
                        @click.stop.prevent="setDataType('policyEndDate', 'personal', activePolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyEndDate === 'confidential') }"
                        @click.stop.prevent="setDataType('policyEndDate', 'confidential', activePolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyEndDate || policyFieldDataTypes[activePolicyTab].policyEndDate === 'regular' }"
                        @click.stop.prevent="setDataType('policyEndDate', 'regular', activePolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].endDate" type="date" />
                <small class="global-form-helper-text">Date when this policy expires or requires review/renewal</small>
        </div>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Upload Document
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDocument === 'personal') }"
                      @click.stop.prevent="setDataType('policyDocument', 'personal', activePolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyDocument === 'confidential') }"
                      @click.stop.prevent="setDataType('policyDocument', 'confidential', activePolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: !policyFieldDataTypes[activePolicyTab] || !policyFieldDataTypes[activePolicyTab].policyDocument || policyFieldDataTypes[activePolicyTab].policyDocument === 'regular' }"
                      @click.stop.prevent="setDataType('policyDocument', 'regular', activePolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <input class="global-form-input" type="file" @change="e => handlePolicyFileUpload(e, activePolicyTab)" />
              <small class="global-form-helper-text">Upload supporting documentation (optional)</small>
            </div>
            <!-- Show CreatedByName and Reviewer fields only in policy tab -->
            <template v-if="selectedTab === 'policy'">
              <div class="global-form-row">
                <div class="global-form-group">
                  <label class="global-form-label">
                    Created By *
                    <!-- Data Type Circle Toggle -->
                    <div class="policy-data-type-circle-toggle-wrapper">
                      <div class="policy-data-type-circle-toggle">
                        <div 
                          class="policy-circle-option personal-circle" 
                          :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCreatedBy === 'personal') }"
                          @click.stop.prevent="setDataType('policyCreatedBy', 'personal', activePolicyTab)"
                          title="Personal Data"
                        >
                          <div class="policy-circle-inner"></div>
                        </div>
                        <div 
                          class="policy-circle-option confidential-circle" 
                          :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCreatedBy === 'confidential') }"
                          @click.stop.prevent="setDataType('policyCreatedBy', 'confidential', activePolicyTab)"
                          title="Confidential Data"
                        >
                          <div class="policy-circle-inner"></div>
                        </div>
                        <div 
                          class="policy-circle-option regular-circle" 
                          :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyCreatedBy === 'regular') || !policyFieldDataTypes[activePolicyTab] }"
                          @click.stop.prevent="setDataType('policyCreatedBy', 'regular', activePolicyTab)"
                          title="Regular Data"
                        >
                          <div class="policy-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </label>
                  <input class="global-form-input" :value="loggedInUsername" type="text" disabled />
                  <small class="global-form-helper-text">Automatically set to logged in user</small>
                </div>
                <div class="global-form-group">
                  <label class="global-form-label">
                    Reviewer *
                    <!-- Data Type Circle Toggle -->
                    <div class="policy-data-type-circle-toggle-wrapper">
                      <div class="policy-data-type-circle-toggle">
                        <div 
                          class="policy-circle-option personal-circle" 
                          :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyReviewer === 'personal') }"
                          @click.stop.prevent="setDataType('policyReviewer', 'personal', activePolicyTab)"
                          title="Personal Data"
                        >
                          <div class="policy-circle-inner"></div>
                        </div>
                        <div 
                          class="policy-circle-option confidential-circle" 
                          :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyReviewer === 'confidential') }"
                          @click.stop.prevent="setDataType('policyReviewer', 'confidential', activePolicyTab)"
                          title="Confidential Data"
                        >
                          <div class="policy-circle-inner"></div>
                        </div>
                        <div 
                          class="policy-circle-option regular-circle" 
                          :class="{ active: (policyFieldDataTypes[activePolicyTab] && policyFieldDataTypes[activePolicyTab].policyReviewer === 'regular') || !policyFieldDataTypes[activePolicyTab] }"
                          @click.stop.prevent="setDataType('policyReviewer', 'regular', activePolicyTab)"
                          title="Regular Data"
                        >
                          <div class="policy-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </label>
                  <select class="global-form-input" v-model="policyTabs[activePolicyTab].reviewer" required>
                    <option value="">Select Reviewer</option>
                    <option v-for="user in users" :key="user.id" :value="user.id">{{ user.name }}</option>
                  </select>
                  <small class="global-form-helper-text">Select who will review this policy</small>
                  <div v-if="isPolicyCreatorReviewerSame" class="global-form-error-message" style="margin-top: 8px; color: #dc3545; font-size: 14px;">
                    <i class="fas fa-exclamation-triangle"></i>
                    Creator and reviewer cannot be the same person. Please select a different reviewer.
                  </div>
                </div>
              </div>
            </template>
          </form>
              </div>
            </div>
      <div v-if="policyTabs.length && policyTabs[activePolicyTab]" class="TT-subpolicy-tabs-container">
        <div class="TT-subpolicy-tabs-row">
          <div class="TT-subpolicy-tabs">
            <button v-for="(subTab, subIdx) in policyTabs[activePolicyTab].subPolicies" :key="subTab.id" :class="['TT-subpolicy-tab', { 'TT-subpolicy-tab-active': subIdx === policyTabs[activePolicyTab].activeSubPolicyTab }]" @click="policyTabs[activePolicyTab].activeSubPolicyTab = subIdx">
              Subpolicy {{ subIdx + 1 }}
            </button>
            <button class="TT-add-subpolicy-tab" @click="addSubPolicyTab(activePolicyTab)">Add Sub Policy</button>
          </div>
        </div>
        <div v-if="policyTabs[activePolicyTab].subPolicies && policyTabs[activePolicyTab].subPolicies.length" class="TT-subpolicy-form-container">
          <button class="TT-exclude-subpolicy-btn" @click="excludeSubPolicyTab(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)">Exclude</button>
          <form>
                          <div class="global-form-group">
                <label class="global-form-label">
                  Sub Policy Name <span class="global-form-label-required">*</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyName === 'personal') }"
                        @click.stop.prevent="setDataType('subPolicyName', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyName === 'confidential') }"
                        @click.stop.prevent="setDataType('subPolicyName', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyName === 'regular') }"
                        @click.stop.prevent="setDataType('subPolicyName', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].name" type="text" required placeholder="Enter sub policy name" @input="handleSubPolicyNameChange(activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab, $event.target.value)" />
                <small v-if="error && error.includes('Subpolicy name')" class="global-form-error-message">{{ error }}</small>
                <small v-else class="global-form-helper-text">Use a clear name that describes this sub-policy's specific focus</small>
        </div>
                          <div class="global-form-group">
              <label class="global-form-label">
                Identifier <span class="global-form-label-required">*</span>
                  <span v-if="isInternalFramework()" class="auto-generated-label">(Auto-generated)</span>
                  <span v-else class="manual-entry-label">(Manual entry)</span>
                  <!-- Data Type Circle Toggle -->
                  <div class="policy-data-type-circle-toggle-wrapper">
                    <div class="policy-data-type-circle-toggle">
                      <div 
                        class="policy-circle-option personal-circle" 
                        :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyIdentifier === 'personal') }"
                        @click.stop.prevent="setDataType('subPolicyIdentifier', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                        title="Personal Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option confidential-circle" 
                        :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyIdentifier === 'confidential') }"
                        @click.stop.prevent="setDataType('subPolicyIdentifier', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                        title="Confidential Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                      <div 
                        class="policy-circle-option regular-circle" 
                        :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyIdentifier === 'regular') }"
                        @click.stop.prevent="setDataType('subPolicyIdentifier', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                        title="Regular Data"
                      >
                        <div class="policy-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <input class="global-form-input" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].identifier" type="text" required placeholder="Enter identifier" :readonly="isInternalFramework()" />
                <small class="global-form-helper-text">{{ isInternalFramework() ? 'Auto-generated based on parent policy identifier' : 'Enter a unique identifier for this sub-policy' }}</small>
          </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Control <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyControl === 'personal') }"
                      @click.stop.prevent="setDataType('subPolicyControl', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyControl === 'confidential') }"
                      @click.stop.prevent="setDataType('subPolicyControl', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyControl === 'regular') }"
                      @click.stop.prevent="setDataType('subPolicyControl', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].control" rows="3" required placeholder="Enter control"></textarea>
              <small class="global-form-helper-text">Specify the control mechanisms, procedures, or safeguards to be implemented</small>
            </div>
            <div class="global-form-group">
              <label class="global-form-label">
                Description <span class="global-form-label-required">*</span>
                <!-- Data Type Circle Toggle -->
                <div class="policy-data-type-circle-toggle-wrapper">
                  <div class="policy-data-type-circle-toggle">
                    <div 
                      class="policy-circle-option personal-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyDescription === 'personal') }"
                      @click.stop.prevent="setDataType('subPolicyDescription', 'personal', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Personal Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option confidential-circle" 
                      :class="{ active: (subPolicyFieldDataTypes[activePolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] && subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyDescription === 'confidential') }"
                      @click.stop.prevent="setDataType('subPolicyDescription', 'confidential', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Confidential Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                    <div 
                      class="policy-circle-option regular-circle" 
                      :class="{ active: (!subPolicyFieldDataTypes[activePolicyTab] || !subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab] || subPolicyFieldDataTypes[activePolicyTab][policyTabs[activePolicyTab].activeSubPolicyTab].subPolicyDescription === 'regular') }"
                      @click.stop.prevent="setDataType('subPolicyDescription', 'regular', activePolicyTab, policyTabs[activePolicyTab].activeSubPolicyTab)"
                      title="Regular Data"
                    >
                      <div class="policy-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </label>
              <textarea class="global-form-textarea" v-model="policyTabs[activePolicyTab].subPolicies[policyTabs[activePolicyTab].activeSubPolicyTab].description" rows="3" required placeholder="Enter description"></textarea>
              <small class="global-form-helper-text">Explain the intent, requirements, or significance of this sub-policy</small>
            </div>
          </form>
        </div>
      </div>
      </div>
    <!-- Add submit button for policy tab -->
    <div v-if="selectedTab === 'policy' && selectedFramework && selectedPolicy" class="TT-universal-submit-wrapper">
      <button class="btn-submit" @click="submitTailoredPolicy" :disabled="isPolicyCreatorReviewerSame || ttPolicyCreateInFlight">Submit</button>
      </div>
    </div>

    <SimilaritySubmitGate ref="similarityRunner" itemType="Framework" :item-data="{ name: '' }" />
  </template>
  
  <script>
import './TT.css'
import CustomDropdown from '../CustomDropdown.vue'
import SimilaritySubmitGate from '@/components/SimilaritySubmitGate.vue'
import apiService from '@/services/apiService'
import policyDataService from '@/services/policyService'
import { PopupService, PopupModal } from '@/modules/popup'  // Fix the import path
import {  API_ENDPOINTS } from '../../config/api.js'
import { useFrameworkStore } from '@/stores/framework'
import { usePolicyStore } from '@/stores/policy'
import {
  buildTailoringSimilarityChecks,
  buildVersioningSimilarityChecks,
  startAsyncUpdateFromChecks,
} from '@/utils/similaritySubmitHelper'
import {
  getSimilarityBannerMessage,
  getSimilarityReadyPopup,
  resolveSimilarityEntity,
} from '@/utils/similarityNotificationText'


  export default {
  name: 'TT',
  components: {
    CustomDropdown,
    PopupModal,
    SimilaritySubmitGate
  },
  data() {
    return {
      selectedTab: 'framework',
      selectedFramework: '',
      selectedPolicy: '',
      frameworks: [],
      policies: [],
      rawPoliciesData: [], // raw API objects from FRAMEWORK_GET_POLICIES
      policyTypes: [],
      policyCategories: [],
      policySubCategories: [],
      policyData: [], // Store all policy category data
      departments: [], // Store all departments
      users: [], // Add users array
      showFrameworkInfo: false, // Toggle for framework info tooltip
      loggedInUsername: localStorage.getItem('username') || '', // Add logged in username
      currentUser: {
        UserId: null,
        UserName: localStorage.getItem('username') || '',
        Role: null
      },
      frameworkForm: {
        name: '',
        description: '',
        identifier: '',
        category: '',
        internalExternal: '',
        file: null,
        startDate: '',
        endDate: '',
        createdByName: '',
        reviewer: ''
      },
      policyTabs: [],
      activePolicyTab: 0,
      loading: false,
      ttFrameworkCreateInFlight: false,
      ttPolicyCreateInFlight: false,
      asyncSimilarityMasterId: null,
      asyncSimilarityCheckCount: 0,
      asyncSimilarityEntity: 'Policy',
      asyncSimilarityPollTimer: null,
      error: null,
      entities: [], // Initialize as empty array
      existingFrameworkIdentifiers: [], // Add this to track existing identifiers
      // Field data types for toggling (personal, confidential, regular)
      fieldDataTypes: {
        // Framework fields
        frameworkName: 'regular',
        frameworkDescription: 'regular',
        frameworkIdentifier: 'regular',
        frameworkCategory: 'regular',
        frameworkInternalExternal: 'regular',
        frameworkDocument: 'regular',
        frameworkStartDate: 'regular',
        frameworkEndDate: 'regular',
        frameworkCreatedBy: 'regular',
        frameworkReviewer: 'regular',
        // Policy fields (will be per-policy, using index)
        policyName: 'regular',
        policyIdentifier: 'regular',
        policyDescription: 'regular',
        policyScope: 'regular',
        policyDepartment: 'regular',
        policyObjective: 'regular',
        policyCoverageRate: 'regular',
        policyApplicability: 'regular',
        policyType: 'regular',
        policyCategory: 'regular',
        policySubCategory: 'regular',
        policyEntities: 'regular',
        policyStartDate: 'regular',
        policyEndDate: 'regular',
        policyReviewer: 'regular',
        // Subpolicy fields (will be per-subpolicy, using policy index and subpolicy index)
        subPolicyName: 'regular',
        subPolicyIdentifier: 'regular',
        subPolicyDescription: 'regular',
        subPolicyControl: 'regular'
      },
      // Per-policy field data types (indexed by policy tab index)
      policyFieldDataTypes: [],
      // Per-subpolicy field data types (indexed by policy tab index, then subpolicy index)
      subPolicyFieldDataTypes: []
    }
  },
  computed: {
    ttSimilarityBannerText() {
      return getSimilarityBannerMessage(this.asyncSimilarityEntity, this.asyncSimilarityCheckCount);
    },
    // Check if creator and reviewer are the same person for framework
    isFrameworkCreatorReviewerSame() {
      if (!this.frameworkForm.reviewer || !this.currentUser.UserName) return false;
      const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
      const reviewerUser = this.users.find(u => u.id === this.frameworkForm.reviewer);
      return creatorUser && reviewerUser && creatorUser.id === reviewerUser.id;
    },
    // Check if creator and reviewer are the same person for current policy
    isPolicyCreatorReviewerSame() {
      // Check if we have the required data
      if (!this.policyTabs[this.activePolicyTab] || !this.currentUser.UserName) return false;
      
      const currentPolicy = this.policyTabs[this.activePolicyTab];
      
      // If no reviewer is selected, return false (no warning needed)
      if (!currentPolicy.reviewer) return false;
      
      const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
      const pr = currentPolicy.reviewer;
      const reviewerUser = this.users.find(
        (u) => String(u.id) === String(pr) ||
          String(u.name || '').toLowerCase() === String(pr).toLowerCase()
      );
      return !!(creatorUser && reviewerUser && creatorUser.id === reviewerUser.id);
    },
    
    // Framework dropdown configuration for framework tab
    frameworkDropdownConfig() {
      // Only show the user's stored framework in the dropdown if it exists
      const sessionFrameworkId = this.selectedFramework;
      const sessionFramework = this.frameworks.find(f => f.id == sessionFrameworkId);
      
      // Create options array based on whether we have a stored framework
      let values = [];
      
      if (sessionFramework) {
        // If we have a stored framework, only show that one
        values = [
          { 
            value: sessionFramework.id, 
            label: `${sessionFramework.name} (${sessionFramework.category || 'No Category'}) - ${sessionFramework.status || 'No Status'}`
          }
        ];
      } else {
        // If no stored framework, show all frameworks
        values = this.frameworks.map(fw => ({ 
          value: fw.id, 
          label: `${fw.name} (${fw.category || 'No Category'}) - ${fw.status || 'No Status'}`
        }));
      }
      
      return {
        label: 'Framework',
        values: values,
        defaultLabel: 'Select Framework'
      };
    },
    
    // Framework dropdown configuration for policy tab
    policyFrameworkDropdownConfig() {
      // Only show the user's stored framework in the dropdown if it exists
      const sessionFrameworkId = this.selectedFramework;
      const sessionFramework = this.frameworks.find(f => f.id == sessionFrameworkId);
      
      // Create options array based on whether we have a stored framework
      let values = [];
      
      if (sessionFramework) {
        // If we have a stored framework, only show that one
        values = [
          { 
            value: sessionFramework.id, 
            label: `${sessionFramework.name} (${sessionFramework.category || 'No Category'}) - ${sessionFramework.status || 'No Status'}`
          }
        ];
      } else {
        // If no stored framework, show all frameworks
        values = this.frameworks.map(fw => ({ 
          value: fw.id, 
          label: `${fw.name} (${fw.category || 'No Category'}) - ${fw.status || 'No Status'}`
        }));
      }
      
      return {
        label: 'Framework',
        values: values,
        defaultLabel: 'Select Framework'
      };
    }
  },
  watch: {
    async selectedTab(newVal) {
      // Refetch users when tab changes to get correct reviewers for the module
      if (newVal && this.currentUser?.UserId) {
        await this.fetchUsers()
      }
      
      if (newVal === 'framework') {
        this.selectedPolicy = ''
        this.fetchFrameworks()
        if (this.selectedFramework) {
          this.handleFrameworkSelection(this.selectedFramework)
        }
      } else if (newVal === 'policy') {
        this.policyTabs = []
        if (!this.isSelfHealRouteQuery()) {
          this.selectedPolicy = ''
        }
        this.fetchFrameworks()
      }
    },
    async selectedFramework(newVal) {
      if (newVal && newVal !== '' && newVal !== '__new__') {
        try {
          console.log('🔍 DEBUG: Saving framework via frameworkStore in TT:', newVal)
          const frameworkStore = useFrameworkStore()
          const selected = this.frameworks.find((f) => String(f.id) === String(newVal))
          await frameworkStore.setFramework({
            id: newVal,
            name: selected?.name || 'Selected Framework',
          })
          console.log('✅ DEBUG: Framework saved via frameworkStore in TT')
        } catch (error) {
          console.error('❌ DEBUG: Error saving framework via frameworkStore in TT:', error)
        }
      }
      
      if (this.selectedTab === 'framework') {
        this.handleFrameworkSelection(newVal)
      } else if (this.selectedTab === 'policy' && newVal) {
        console.log('Framework selected in policy tab:', newVal)
        this.fetchPoliciesByFramework(newVal)
      }
    },
    selectedPolicy(newVal) {
      if (this.selectedTab === 'policy' && this.selectedFramework && newVal) {
        console.log('Policy selected:', newVal)
        this.fetchPolicyDetails(newVal)
      }
    },
    '$route.query': {
      deep: true,
      handler() {
        this.applySelfHealDeepLinkFromRoute()
      }
    },
    'policyTabs[activePolicyTab].type': {
      immediate: true,
      handler(newVal) {
        console.log('Policy type changed to:', newVal)
        this.updatePolicyCategoriesByType(newVal)
      }
    },
    'policyTabs[activePolicyTab].category': {
      immediate: true,
      handler(newVal) {
        console.log('Policy category changed to:', newVal)
        const policyType = this.policyTabs[this.activePolicyTab]?.type
        this.updateSubCategoriesByCategory(policyType, newVal)
      }
    },
    // Add watchers for auto-generating identifiers
    'frameworkForm.name': function(newVal) {
      if (newVal) {
        this.autoGenerateFrameworkIdentifier(newVal);
      }
    }
  },
  async created() {
    try {
      // Initialize frameworkForm.createdByName with loggedInUsername
      this.frameworkForm.createdByName = this.loggedInUsername

      // Frameworks first (Pinia/cache-first — do not block on heavy policyService prefetch)
      await this.fetchFrameworks()
      // Second frameworks/? call for identifiers — run in background so it does not add 20s to first paint
      void this.fetchExistingFrameworkIdentifiers()

      await Promise.all([
        this.fetchCurrentUser(),
        this.fetchPolicyCategories(),
        this.fetchEntities(),
        this.fetchUsers(),
        this.fetchDepartments()
      ])
      await this.applySelfHealDeepLinkFromRoute()
    } catch (error) {
      console.error('Error in component creation:', error)
      this.error = 'Failed to initialize component'
    }
  },
  methods: {
    // Set data type for a field
    setDataType(fieldName, type, policyIndex = null, subPolicyIndex = null) {
      if (subPolicyIndex !== null && policyIndex !== null) {
        // Subpolicy field
        if (!this.subPolicyFieldDataTypes[policyIndex]) {
          this.subPolicyFieldDataTypes[policyIndex] = [];
        }
        if (!this.subPolicyFieldDataTypes[policyIndex][subPolicyIndex]) {
          // Initialize with all fields set to 'regular' by default
          this.subPolicyFieldDataTypes[policyIndex][subPolicyIndex] = {
            subPolicyName: 'regular',
            subPolicyIdentifier: 'regular',
            subPolicyDescription: 'regular',
            subPolicyControl: 'regular'
          };
        }
        // Use direct assignment for Vue 3 reactivity
        this.subPolicyFieldDataTypes[policyIndex][subPolicyIndex][fieldName] = type;
      } else if (policyIndex !== null) {
        // Policy field
        if (!this.policyFieldDataTypes[policyIndex]) {
          // Initialize with all fields set to 'regular' by default
          this.policyFieldDataTypes[policyIndex] = {
            policyName: 'regular',
            policyIdentifier: 'regular',
            policyDescription: 'regular',
            policyScope: 'regular',
            policyDepartment: 'regular',
            policyObjective: 'regular',
            policyCoverageRate: 'regular',
            policyApplicability: 'regular',
            policyType: 'regular',
            policyCategory: 'regular',
            policySubCategory: 'regular',
            policyEntities: 'regular',
            policyStartDate: 'regular',
            policyEndDate: 'regular',
            policyDocument: 'regular',
            policyCreatedBy: 'regular',
            policyReviewer: 'regular'
          };
        }
        // Use direct assignment for Vue 3 reactivity
        this.policyFieldDataTypes[policyIndex][fieldName] = type;
      } else {
        // Framework field
        this.fieldDataTypes[fieldName] = type;
      }
      console.log(`Data type selected for ${fieldName}:`, type, 'policyIndex:', policyIndex, 'subPolicyIndex:', subPolicyIndex);
      console.log(`Current policyFieldDataTypes[${policyIndex}]:`, this.policyFieldDataTypes[policyIndex]);
    },
    // Add new identifier generation functions
    async fetchExistingFrameworkIdentifiers() {
      try {
        const response = await apiService.get(API_ENDPOINTS.FRAMEWORKS, {
          params: { include_all_for_identifiers: 'true' }
        });
        this.existingFrameworkIdentifiers = response
          .map(fw => fw.Identifier)
          .filter(id => id);
        console.log('Fetched existing framework identifiers:', this.existingFrameworkIdentifiers);
      } catch (err) {
        console.error('Error fetching existing framework identifiers:', err);
      }
    },

    generateFrameworkIdentifier(frameworkName) {
      if (!frameworkName || frameworkName.length < 4) return '';
      
      const prefix = frameworkName.substring(0, 4).toUpperCase();
      let counter = 1;
      let identifier = `${prefix}${counter}`;
      
      // Check against existing identifiers
      while (this.existingFrameworkIdentifiers.includes(identifier)) {
        counter++;
        identifier = `${prefix}${counter}`;
      }
      
      return identifier;
    },

    autoGenerateFrameworkIdentifier(frameworkName) {
      if (frameworkName) {
        const generatedId = this.generateFrameworkIdentifier(frameworkName);
        this.frameworkForm.identifier = generatedId;
      }
    },

    generatePolicyIdentifier(policyName) {
      if (!policyName) return '';
      
      // Split by spaces and take first letter of each word
      const words = policyName.split(' ').filter(word => word.length > 0);
      return words.map(word => word.charAt(0).toUpperCase()).join('');
    },

    generateSubPolicyIdentifier(policyIdentifier, subPolicyIndex) {
      if (!policyIdentifier) return '';
      return `${policyIdentifier}-${subPolicyIndex + 1}`;
    },

    // Helper function to check if current context is for internal framework
    isInternalFramework() {
      return this.frameworkForm.internalExternal === 'Internal';
    },

    handlePolicyNameChange(idx, value) {
      // Update the policy name
      this.policyTabs[idx].name = value;
      
      // Auto-generate identifier when name changes (only for internal frameworks)
      if (value && this.isInternalFramework()) {
        const generatedId = this.generatePolicyIdentifier(value);
        this.policyTabs[idx].identifier = generatedId;
        
        // Also update all subpolicy identifiers
        if (this.policyTabs[idx].subPolicies) {
          this.policyTabs[idx].subPolicies.forEach((subpolicy, subIdx) => {
            if (subpolicy.name) {
              subpolicy.identifier = this.generateSubPolicyIdentifier(generatedId, subIdx);
            }
          });
        }
      }
      
      // Validate policy name uniqueness
      this.validatePolicyName(value, idx);
    },

    handleSubPolicyNameChange(policyIdx, subIdx, value) {
      // Update the subpolicy name
      this.policyTabs[policyIdx].subPolicies[subIdx].name = value;
      
      // Auto-generate identifier when name changes (only for internal frameworks)
      if (value && this.policyTabs[policyIdx].identifier && this.isInternalFramework()) {
        const policyIdentifier = this.policyTabs[policyIdx].identifier;
        this.policyTabs[policyIdx].subPolicies[subIdx].identifier = 
          this.generateSubPolicyIdentifier(policyIdentifier, subIdx);
      }
      
      // Validate subpolicy name uniqueness
      this.validateSubPolicyName(value, policyIdx, subIdx);
    },
    isSelfHealRouteQuery() {
      const q = (this.$route && this.$route.query) || {}
      return (
        String(q.selfHeal || '') === '1' &&
        q.policyId != null &&
        String(q.policyId).trim() !== '' &&
        q.frameworkId != null &&
        String(q.frameworkId).trim() !== ''
      )
    },

    async applySelfHealDeepLinkFromRoute() {
      try {
        if (!this.isSelfHealRouteQuery()) return
        const q = this.$route.query || {}
        const policyId = String(q.policyId).trim()
        const frameworkId = String(q.frameworkId).trim()
        this.selectTab('policy')
        await this.$nextTick()
        // Watcher calls fetchFrameworks() without await — list may still be framework-tab (Internal-only).
        await this.fetchFrameworks()
        this.selectedFramework = frameworkId
        await this.fetchPoliciesByFramework(this.selectedFramework)
        await this.$nextTick()
        this.selectedPolicy = policyId
      } catch (e) {
        console.error('Self-heal deep link failed:', e)
      }
    },
    selectTab(tab) {
      this.selectedTab = tab
      
      // Clear any existing error when switching tabs
      this.error = null;
    },
    handleFileUpload(e) {
      this.frameworkForm.file = e.target.files[0]
    },
    async sendPushNotification(notificationData) {
      try {
        await apiService.post(API_ENDPOINTS.PUSH_NOTIFICATION, notificationData, {
          background: true
        });
        console.log('Push notification sent successfully');
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    mapRawFrameworksToTT(frameworksSource) {
      const src = Array.isArray(frameworksSource) ? frameworksSource : []
      return src.map((fw) => ({
        id: fw.FrameworkId || fw.id,
        name: fw.FrameworkName || fw.name,
        description: fw.FrameworkDescription || fw.description,
        category: fw.Category || fw.category,
        internalExternal: fw.InternalExternal || fw.internalExternal,
        startDate: fw.StartDate || fw.startDate,
        endDate: fw.EndDate || fw.endDate,
        status: fw.Status || fw.status
      }))
    },
    applyTTFrameworkFilter(allFrameworks) {
      return this.selectedTab === 'framework'
        ? allFrameworks.filter((fw) => fw.internalExternal === 'Internal')
        : allFrameworks
    },
    async fetchFrameworks() {
      try {
        this.loading = true
        const policyStore = usePolicyStore()
        console.log('🔍 TT: loading full tenant framework list (include_all_status, no user_id filter)')

        // Warm other policy pages in background only — never block TT on fetchAllPolicyData()
        if (!window.policyDataFetchPromise && !policyDataService.hasFrameworksListCache()) {
          window.policyDataFetchPromise = policyDataService.fetchAllPolicyData()
          void window.policyDataFetchPromise.catch((err) => {
            console.warn('⚠️ TT: policy prefetch failed (non-blocking)', err?.message || err)
          })
        }

        const frameworksSource = await policyStore.getAllFrameworks({ force: true })
        policyDataService.setFrameworksList(frameworksSource || [])

        const allFrameworks = this.mapRawFrameworksToTT(frameworksSource)
        this.frameworks = this.applyTTFrameworkFilter(allFrameworks)
        console.log('TT mapped frameworks:', this.frameworks.length, '(tab:', this.selectedTab, ')')

        await this.checkSelectedFrameworkFromSession()
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        this.error = 'Failed to fetch frameworks'
      } finally {
        this.loading = false
      }
    },

    // Check for selected framework from session and set it as default
    async checkSelectedFrameworkFromSession() {
      try {
         // Policy self-heal deep link sets framework/policy from URL; session sync would clear or overwrite it.
         if (this.isSelfHealRouteQuery()) {
          return
        }
        console.log('🔍 DEBUG: Checking for selected framework from session in TT...')
        const frameworkStore = useFrameworkStore()
        await frameworkStore.loadFrameworkFromSession()
        const response = {
          success: true,
          frameworkId: frameworkStore.selectedFrameworkId,
        }
        console.log('📊 DEBUG: Selected framework response:', response)
        
        if (response && response.success) {
          // Check if a framework is selected (not null)
          if (response.frameworkId) {
          const sessionFrameworkId = response.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.id == sessionFrameworkId)
          
          if (frameworkExists) {
            this.selectedFramework = sessionFrameworkId
            console.log('🎯 DEBUG: Set selected framework from session:', frameworkExists.name)
            console.log('📝 DEBUG: Framework details:', frameworkExists)
            
            // If this is the framework tab and no policies exist, load framework details
            if (this.selectedTab === 'framework') {
              await this.handleFrameworkSelection(sessionFrameworkId)
            }
          } else {
            console.log('⚠️ DEBUG: Framework from session not found in available frameworks')
            console.log('🔍 DEBUG: Session framework ID:', sessionFrameworkId)
            console.log('📝 DEBUG: Available framework IDs:', this.frameworks.map(f => f.id))
            }
          } else {
            // "All Frameworks" is selected (frameworkId is null)
            console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
            console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
            this.selectedFramework = ''
            this.selectedPolicy = ''
            this.policies = []
            // Clear any framework-specific data
            if (this.selectedTab === 'framework') {
              this.frameworkForm = this.getInitialFrameworkForm()
              this.policyTabs = []
            }
          }
        } else {
          console.log('ℹ️ DEBUG: No framework selected in session')
          this.selectedFramework = ''
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        // Don't show error to user as this is not critical
        // Clear selection on error
        this.selectedFramework = ''
      }
    },

    async fetchPoliciesByFramework(frameworkId) {
      try {
        this.loading = true
        const policyStore = usePolicyStore()
        console.log('TT: policies for framework (Pinia cache first):', frameworkId)

        let policiesData = await policyStore.getFrameworkPoliciesForTailoring(frameworkId, { force: false })
        console.log('TT: raw policies from Pinia/API:', policiesData?.length)

        if (!policiesData) {
          console.error('No policies data received')
          this.policies = []
          return
        }

        if (!Array.isArray(policiesData)) {
          console.error('Policies data is not an array:', policiesData)
          this.policies = []
          return
        }
        
        // Store raw API data for fallback use in fetchPolicyDetails
        this.rawPoliciesData = policiesData

        // Filter policies to only show Approved ones (allowing null for ActiveInactive)
        this.policies = policiesData
          .filter(p => p.Status === 'Approved' && (p.ActiveInactive === 'Active' || p.ActiveInactive === null || p.ActiveInactive === undefined || p.ActiveInactive === ''))
          .map(p => ({ 
            id: p.PolicyId, 
            name: p.PolicyName,
            description: p.PolicyDescription,
            status: p.Status,
            department: this.normalizeDepartmentValue(p.Department || p.department),
            scope: p.Scope,
            objective: p.Objective,
            identifier: p.Identifier,
            coverageRate: p.CoverageRate,
            applicability: this.normalizeApplicabilityValue(
              this.getPolicyFieldValue(p, ['Applicability', 'applicability', 'Applicablity', 'applicablity'])
            ),
            type: p.PolicyType,
            category: p.PolicyCategory,
            subCategory: p.PolicySubCategory,
            entities: Array.isArray(p.Entities) ? p.Entities : (p.Entities === 'all' ? 'all' : []),
            startDate: p.StartDate,
            endDate: p.EndDate
          }))
        console.log('Mapped and filtered policies:', this.policies)
      } catch (error) {
        console.error('Error fetching policies:', error)
        console.error('Error response:', error.response?.data)
        this.error = 'Failed to fetch policies'
        this.policies = []
      } finally {
        this.loading = false
      }
    },
    async fetchPolicyDetails(policyId) {
      try {
        this.loading = true
        console.log('Fetching policy details for ID:', policyId)

        // If rawPoliciesData is empty (e.g. race condition), fetch it now
        if (!this.rawPoliciesData || this.rawPoliciesData.length === 0) {
          await this.fetchPoliciesByFramework(this.selectedFramework)
        }

        // Use raw policy from FRAMEWORK_GET_POLICIES (same source as framework tab)
        const rawFrameworkPolicy = this.rawPoliciesData.find(p => String(p.PolicyId) === String(policyId)) || {}
        console.log('rawFrameworkPolicy used for policy tab:', rawFrameworkPolicy)

        // Only fetch subpolicies — all other fields come from rawFrameworkPolicy
        const subpolicies = await apiService.get(API_ENDPOINTS.POLICY_GET_SUBPOLICIES(policyId))
        console.log('Raw subpolicies:', subpolicies)

        const mappedSubpolicies = subpolicies.map(sp => ({
          id: sp.SubPolicyId,
          name: sp.SubPolicyName,
          identifier: sp.Identifier,
          control: sp.Control,
          description: sp.Description,
          status: sp.Status,
          originalSubPolicyId: sp.SubPolicyId,
        }))

        const p = rawFrameworkPolicy  // alias for readability

        const policyTab = {
          id: p.PolicyId,
          name: p.PolicyName || '',
          description: p.PolicyDescription || '',
          status: p.Status || '',
          department: this.normalizeDepartmentValue(p.Department || p.department),
          scope: p.Scope || '',
          objective: p.Objective || '',
          identifier: p.Identifier || '',
          coverageRate: p.CoverageRate ?? '',
          applicability: this.normalizeApplicabilityValue(
            this.getPolicyFieldValue(p, ['Applicability', 'applicability', 'Applicablity', 'applicablity'])
          ),
          type: p.PolicyType || '',
          category: p.PolicyCategory || '',
          subCategory: p.PolicySubCategory || '',
          entities: Array.isArray(p.Entities) ? p.Entities : (p.Entities === 'all' ? 'all' : []),
          startDate: p.StartDate || '',
          endDate: p.EndDate || '',
          docURL: p.DocURL || '',
          permanentTemporary: p.PermanentTemporary || '',
          file: null,
          createdByName: p.CreatedByName || '',
          reviewer: p.Reviewer || '',
          subPolicies: mappedSubpolicies,
          activeSubPolicyTab: 0,
          originalPolicyId: p.PolicyId,
          _similarityBaseline: {
            name: p.PolicyName || '',
            description: p.PolicyDescription || '',
            identifier: p.Identifier || '',
            department: this.normalizeDepartmentValue(p.Department || p.department),
            scope: p.Scope || '',
            objective: p.Objective || '',
            type: p.PolicyType || '',
            category: p.PolicyCategory || '',
            subCategory: p.PolicySubCategory || '',
            subPolicies: mappedSubpolicies.map((sp) => ({
              id: sp.id,
              name: sp.name,
              identifier: sp.identifier,
              control: sp.control,
              description: sp.description,
            })),
          },
        }

        console.log('Created policy tab:', policyTab)
        this.policyTabs = [policyTab]
        this.activePolicyTab = 0
        // API returns Reviewer as UserName string; reviewer <select> binds user id. Resolve so submit sends Reviewer correctly.
          const rawReviewer = (p.Reviewer || '').trim()
        if (rawReviewer) {
          if (!this.users || this.users.length === 0) {
            try {
              await this.fetchUsers()
            } catch {
              /* fetchUsers sets error; continue with username fallback on submit */
            }
          }
          const lower = rawReviewer.toLowerCase()
          const match = (this.users || []).find(
            (u) => String(u.name || '').toLowerCase() === lower || String(u.id) === rawReviewer
          )
          if (match) {
            this.policyTabs[0].reviewer = match.id
          }
        }

        // Initialize policyFieldDataTypes for the loaded policy with all fields set to 'regular' by default
        this.policyFieldDataTypes = [{
          policyName: 'regular',
          policyIdentifier: 'regular',
          policyDescription: 'regular',
          policyScope: 'regular',
          policyDepartment: 'regular',
          policyObjective: 'regular',
          policyCoverageRate: 'regular',
          policyApplicability: 'regular',
          policyType: 'regular',
          policyCategory: 'regular',
          policySubCategory: 'regular',
          policyEntities: 'regular',
          policyStartDate: 'regular',
          policyEndDate: 'regular',
          policyDocument: 'regular',
          policyCreatedBy: 'regular',
          policyReviewer: 'regular'
        }];
        
        // Initialize subPolicyFieldDataTypes for the loaded policy
        this.subPolicyFieldDataTypes = [[]];
        if (this.policyTabs[0].subPolicies && this.policyTabs[0].subPolicies.length > 0) {
          this.policyTabs[0].subPolicies.forEach((subPolicy, subIndex) => {
            this.subPolicyFieldDataTypes[0][subIndex] = {
              subPolicyName: 'regular',
              subPolicyIdentifier: 'regular',
              subPolicyDescription: 'regular',
              subPolicyControl: 'regular'
            }
          })
        }
        
        // Validate policy name when policy is selected
        if (this.selectedTab === 'policy') {
          this.validatePolicyNameOnSelection(p.PolicyName);
        }
      } catch (error) {
        console.error('Error fetching policy details:', error)
        this.error = 'Failed to fetch policy details'
        // Reset policy tabs on error
        this.policyTabs = []
        this.activePolicyTab = 0
      } finally {
        this.loading = false
      }
    },
    _onAsyncSimilarityStarted(masterCheckId, checkCount = 0, entityType = 'Policy') {
      this.asyncSimilarityMasterId = masterCheckId
      this.asyncSimilarityCheckCount = checkCount || 0
      this.asyncSimilarityEntity = entityType || 'Policy'
      this._startAsyncSimilarityPoll()
    },
    openSimilarityReview() {
      if (!this.asyncSimilarityMasterId) return
      this.$router.push({ path: '/similarity/review', query: { checkId: this.asyncSimilarityMasterId } })
    },
    _startAsyncSimilarityPoll() {
      if (this.asyncSimilarityPollTimer) {
        clearInterval(this.asyncSimilarityPollTimer)
      }
      const poll = async () => {
        if (!this.asyncSimilarityMasterId) return
        try {
          const { getAsyncUpdateStatus } = await import('@/services/similarityAsyncUpdateService')
          const status = await getAsyncUpdateStatus(this.asyncSimilarityMasterId)
          if (status.background_status === 'READY') {
            clearInterval(this.asyncSimilarityPollTimer)
            this.asyncSimilarityPollTimer = null
            const readyCopy = getSimilarityReadyPopup(this.asyncSimilarityEntity)
            PopupService.success(readyCopy.message, readyCopy.heading)
          } else if (status.background_status === 'FAILED') {
            clearInterval(this.asyncSimilarityPollTimer)
            this.asyncSimilarityPollTimer = null
            this.asyncSimilarityMasterId = null
            PopupService.error(status.error || 'Similarity check failed', 'Error')
          }
        } catch (e) {
          console.warn('Async similarity poll:', e)
        }
      }
      this.asyncSimilarityPollTimer = setInterval(poll, 5000)
      void poll()
    },
    async _tryStartTtAsyncSimilarity(scope, pendingSave) {
      const fwId = parseInt(this.selectedFramework, 10) || null
      let checks = []
      if (scope === 'framework') {
        checks = buildTailoringSimilarityChecks({
          gate: this.$refs.similarityRunner,
          frameworkForm: this.frameworkForm,
          policyTabs: this.policyTabs,
          frameworkId: fwId,
        })
      } else if (this.policyTabs?.[this.activePolicyTab]) {
        checks = buildVersioningSimilarityChecks({
          gate: this.$refs.similarityRunner,
          frameworkForm: null,
          previousFramework: null,
          policyTabs: [this.policyTabs[this.activePolicyTab]],
          frameworkId: fwId,
          policyOnly: true,
        })
      }
      const { started, masterCheckId, checkCount } = await startAsyncUpdateFromChecks(
        checks,
        pendingSave,
        { PopupService }
      )
      if (!started) return false
      const itemTypes = checks.map((c) => c.params?.item_type).filter(Boolean)
      const entityType = resolveSimilarityEntity(pendingSave?.operation, itemTypes)
      this._onAsyncSimilarityStarted(masterCheckId, checkCount, entityType)
      return true
    },
    async _executeTtFrameworkPendingSave(pendingSave) {
      const meta = pendingSave.meta || {}
      const loggedInUser = meta.loggedInUser || this.loggedInUsername || 'default_user'
      this.ttFrameworkCreateInFlight = true
      try {
        const response = await apiService.post(
          '/api/tailoring/create-framework/',
          pendingSave.payload,
          { background: true }
        )
        const ps = usePolicyStore()
        if (response.FrameworkId) {
          ps.mergeFrameworkRowFromCreate({
            FrameworkId: response.FrameworkId,
            FrameworkName: response.FrameworkName || meta.frameworkNameSnapshot,
            Category: meta.frameworkCategorySnapshot,
            InternalExternal: meta.frameworkInternalExternalSnapshot || 'Internal',
            ActiveInactive: 'Inactive',
            Status: response.Status || 'Under Review',
            CurrentVersion: 1,
            FrameworkDescription: meta.frameworkDescSnapshot,
          })
          policyDataService.mergeExplorerFrameworkRow({
            id: response.FrameworkId,
            name: response.FrameworkName || meta.frameworkNameSnapshot,
            category: meta.frameworkCategorySnapshot || '',
            description: meta.frameworkDescSnapshot || '',
            status: 'Inactive',
            internalExternal: meta.frameworkInternalExternalSnapshot || 'Internal',
            versions: [{ version: 1 }],
          })
        }
        this.$emit('framework-created')
        this.resetForm()
        this.error = null
        PopupService.success('Framework created successfully!', 'Success')
        void this.sendPushNotification({
          title: 'New Framework Created',
          message: `A new framework "${meta.frameworkNameSnapshot}" has been created in the Tailoring & Templating module.`,
          category: 'framework',
          priority: 'high',
          user_id: loggedInUser,
        })
      } catch (error) {
        const errMsg = error.response?.data?.error || error.message || 'Failed to submit framework'
        PopupService.error(errMsg, 'Error Creating Framework')
        void this.sendPushNotification({
          title: 'Framework Creation Failed',
          message: `Failed to create framework "${meta.frameworkNameSnapshot}": ${errMsg}`,
          category: 'framework',
          priority: 'high',
          user_id: loggedInUser,
        })
        throw error
      } finally {
        this.ttFrameworkCreateInFlight = false
      }
    },
    async _executeTtPolicyPendingSave(pendingSave) {
      const meta = pendingSave.meta || {}
      const loggedInUser = meta.loggedInUser || this.loggedInUsername || 'default_user'
      this.ttPolicyCreateInFlight = true
      try {
        if (pendingSave.operation === 'policy_version') {
          const response = await apiService.post(
            `/api/policies/${pendingSave.entity_pk}/create-version/`,
            pendingSave.payload
          )
          this.$emit('policy-created')
          this.resetForm()
          this.error = null
          PopupService.success('New policy version submitted for review.', 'Success')
          void this.sendPushNotification({
            title: 'Policy version created',
            message: `A new version of "${pendingSave.label}" was submitted from policy renewal.`,
            category: 'policy',
            priority: 'high',
            user_id: loggedInUser,
          })
          return response
        }
        const response = await apiService.post(
          '/api/tailoring/create-policy/',
          pendingSave.payload,
          { background: true }
        )
        if (response.PolicyId && response.FrameworkId) {
          usePolicyStore().prependPolicyTailoringCache(response.FrameworkId, {
            PolicyId: response.PolicyId,
            PolicyName: response.PolicyName || meta.policyNameSnapshot,
            PolicyDescription: meta.policyDescSnapshot,
            Status: response.Status || 'Under Review',
            FrameworkId: response.FrameworkId,
            ActiveInactive: 'Inactive',
          })
        }
        this.$emit('policy-created')
        this.resetForm()
        this.error = null
        PopupService.success('Policy created successfully!', 'Success')
        void this.sendPushNotification({
          title: 'New Policy Created',
          message: `A new policy "${meta.policyNameSnapshot}" has been created in the Tailoring & Templating module.`,
          category: 'policy',
          priority: 'high',
          user_id: loggedInUser,
        })
        return response
      } catch (error) {
        const errMsg = error.response?.data?.error || error.message || 'Failed to submit policy'
        PopupService.error(errMsg, 'Error Creating Policy')
        void this.sendPushNotification({
          title: 'Policy Creation Failed',
          message: `Failed to create policy "${meta.policyNameSnapshot || pendingSave.label}": ${errMsg}`,
          category: 'policy',
          priority: 'high',
          user_id: loggedInUser,
        })
        throw error
      } finally {
        this.ttPolicyCreateInFlight = false
      }
    },

    async submitTailoredFramework() {
      if (!this.validateForm('framework')) {
        return;
      }
      if (this.isFrameworkCreatorReviewerSame) {
        return;
      }
      if (this.ttFrameworkCreateInFlight) {
        return;
      }

      const loggedInUser = this.loggedInUsername || 'default_user';

      try {
        this.loading = true;

        await this.saveNewDepartments();
        await this.saveNewPolicyCategories();

        this.loading = false;

        // Convert reviewer ID to reviewer name
        const reviewerUser = this.users.find(u => u.id === this.frameworkForm.reviewer);
        const reviewerName = reviewerUser ? reviewerUser.name : '';

        // Build data inventory for framework
        const frameworkFieldLabelMap = {
          frameworkName: 'Framework Name',
          frameworkDescription: 'Framework Description',
          frameworkIdentifier: 'Framework Identifier',
          frameworkCategory: 'Framework Category',
          frameworkInternalExternal: 'Internal/External',
          frameworkDocument: 'Upload Document',
          frameworkStartDate: 'Effective Start Date',
          frameworkEndDate: 'Effective End Date',
          frameworkCreatedBy: 'Created By',
          frameworkReviewer: 'Reviewer'
        };

        const frameworkDataInventory = {};
        Object.keys(frameworkFieldLabelMap).forEach(key => {
          if (this.fieldDataTypes[key]) {
            frameworkDataInventory[frameworkFieldLabelMap[key]] = this.fieldDataTypes[key];
          }
        });

        const frameworkNameSnapshot = this.frameworkForm.name;
        const frameworkDescSnapshot = this.frameworkForm.description;
        const frameworkCategorySnapshot = this.frameworkForm.category;
        const frameworkInternalExternalSnapshot = this.frameworkForm.internalExternal;

        const frameworkData = {
          title: this.frameworkForm.name,
          description: this.frameworkForm.description,
          identifier: this.frameworkForm.identifier,
          category: this.frameworkForm.category,
          internalExternal: this.frameworkForm.internalExternal,
          startDate: this.frameworkForm.startDate,
          endDate: this.frameworkForm.endDate,
          createdByName: this.loggedInUsername,
          reviewer: reviewerName,
          data_inventory: frameworkDataInventory,
          policies: this.policyTabs.map((policy, policyIndex) => {
            // Convert entities to proper format
            let entities = policy.entities;
            if (Array.isArray(entities)) {
              entities = Array.from(entities).map(Number);
            }
            if (!entities || (Array.isArray(entities) && entities.length === 0)) {
              entities = [];
            }

            const policyFieldLabelMap = {
              policyName: 'Policy Name',
              policyIdentifier: 'Policy Identifier',
              policyDescription: 'Description',
              policyScope: 'Scope',
              policyDepartment: 'Department',
              policyObjective: 'Objective',
              policyCoverageRate: 'Coverage Rate (%)',
              policyApplicability: 'Applicability',
              policyType: 'Policy Type',
              policyCategory: 'Policy Category',
              policySubCategory: 'Policy Sub Category',
              policyEntities: 'Entities',
              policyStartDate: 'Start Date',
              policyEndDate: 'End Date',
              policyDocument: 'Upload Document',
              policyCreatedBy: 'Created By',
              policyReviewer: 'Reviewer'
            };

            const policyDataInventory = {};
            if (this.policyFieldDataTypes[policyIndex]) {
              Object.keys(policyFieldLabelMap).forEach(key => {
                if (this.policyFieldDataTypes[policyIndex][key]) {
                  policyDataInventory[policyFieldLabelMap[key]] = this.policyFieldDataTypes[policyIndex][key];
                }
              });
            }

            const subPoliciesWithInventory = policy.subPolicies.map((sub, subIndex) => {
              const subPolicyFieldLabelMap = {
                subPolicyName: 'Sub Policy Name',
                subPolicyIdentifier: 'Sub Policy Identifier',
                subPolicyDescription: 'Description',
                subPolicyControl: 'Control'
              };

              const subPolicyDataInventory = {};
              if (this.subPolicyFieldDataTypes[policyIndex] && this.subPolicyFieldDataTypes[policyIndex][subIndex]) {
                Object.keys(subPolicyFieldLabelMap).forEach(key => {
                  if (this.subPolicyFieldDataTypes[policyIndex][subIndex][key]) {
                    subPolicyDataInventory[subPolicyFieldLabelMap[key]] = this.subPolicyFieldDataTypes[policyIndex][subIndex][key];
                  }
                });
              }

              return {
                title: sub.name,
                identifier: sub.identifier,
                description: sub.description,
                control: sub.control,
                createdByName: this.selectedTab === 'framework' ? this.loggedInUsername : policy.createdByName,
                data_inventory: subPolicyDataInventory
              };
            });

            return {
              title: policy.name,
              description: policy.description,
              identifier: policy.identifier,
              department: policy.department,
              scope: policy.scope,
              objective: policy.objective,
              coverageRate: policy.coverageRate,
              applicability: policy.applicability,
              PolicyType: policy.type,
              PolicyCategory: policy.category,
              PolicySubCategory: policy.subCategory,
              Entities: entities,
              startDate: policy.startDate,
              endDate: policy.endDate,
              createdByName: this.selectedTab === 'framework' ? this.loggedInUsername : policy.createdByName,
              reviewer: this.selectedTab === 'framework' ? reviewerName : (() => {
                const policyReviewerUser = this.users.find(u => u.id === policy.reviewer);
                return policyReviewerUser ? policyReviewerUser.name : '';
              })(),
              data_inventory: policyDataInventory,
              subPolicies: subPoliciesWithInventory
            };
          })
        };

        const pendingSave = {
          operation: 'tt_create_framework',
          entity_pk: parseInt(this.selectedFramework, 10) || null,
          payload: frameworkData,
          label: this.frameworkForm.name,
          summary: 'Tailoring framework submit',
          meta: {
            loggedInUser,
            frameworkNameSnapshot,
            frameworkDescSnapshot,
            frameworkCategorySnapshot,
            frameworkInternalExternalSnapshot,
          },
        };
        if (await this._tryStartTtAsyncSimilarity('framework', pendingSave)) {
          return;
        }
        await this._executeTtFrameworkPendingSave(pendingSave);
      } catch (error) {
        console.error('Error preparing framework submission:', error);
        this.loading = false;
        this.error = error.response?.data?.error || error.message || 'Failed to submit framework';
        PopupService.error(this.error, 'Error Creating Framework');
        void this.sendPushNotification({
          title: 'Framework Creation Failed',
          message: `Failed to create framework "${this.frameworkForm.name}": ${this.error}`,
          category: 'framework',
          priority: 'high',
          user_id: loggedInUser
        });
      }
    },
    async handleFrameworkSelection(newVal) {
      console.log('handleFrameworkSelection called with:', newVal)
      if (!newVal) {
        console.log('No framework selected, resetting form')
        this.resetForm()
        return
      }

      try {
        this.loading = true
        const [framework, policies] = await Promise.all([
          apiService.get(API_ENDPOINTS.FRAMEWORK_DETAILS(newVal)),
          apiService.get(API_ENDPOINTS.FRAMEWORK_GET_POLICIES(newVal))
        ])

        console.log('Raw framework details:', framework)
        console.log('Raw framework policies:', policies)

        this.frameworkForm = {
          name: framework.FrameworkName,
          description: framework.FrameworkDescription,
          identifier: framework.Identifier,
          category: framework.Category,
          internalExternal: framework.InternalExternal || framework.internalExternal || framework.Internal_External || 'Internal',
          file: null,
          startDate: framework.StartDate,
          endDate: framework.EndDate,
          createdByName: framework.CreatedByName,
          reviewer: framework.Reviewer
        }

        // Validate framework name when framework is selected
        if (this.selectedTab === 'framework') {
          this.validateFrameworkNameOnSelection(framework.FrameworkName);
        }

        // Ensure policies is an array
        let policiesData = policies
        console.log('Policies response data:', policiesData)
        
        if (!policiesData) {
          console.error('No policies response data received')
          this.rawPoliciesData = []
          this.policies = []
        } else if (!Array.isArray(policiesData)) {
          console.error('Policies response data is not an array:', policiesData)
          this.rawPoliciesData = []
          this.policies = []
        } else {
          // Store raw data for fallback use
          this.rawPoliciesData = policiesData
          // Filter policies to only show Approved and Active ones
          this.policies = policiesData
            .filter(p => p.Status === 'Approved' && p.ActiveInactive === 'Active')
            .map(p => ({ 
              id: p.PolicyId, 
              name: p.PolicyName,
              description: p.PolicyDescription,
              status: p.Status,
              department: this.normalizeDepartmentValue(p.Department || p.department),
              scope: p.Scope,
              objective: p.Objective,
              identifier: p.Identifier,
              coverageRate: p.CoverageRate,
              applicability: this.normalizeApplicabilityValue(
                this.getPolicyFieldValue(p, ['Applicability', 'applicability', 'Applicablity', 'applicablity'])
              ),
              type: p.PolicyType,
              category: p.PolicyCategory,
              subCategory: p.PolicySubCategory,
              entities: p.Entities,
              startDate: p.StartDate,
              endDate: p.EndDate
            }))
        }

        if (this.selectedTab === 'framework') {
          const policiesWithDetails = await Promise.all(
            policies
              .filter(p => p.Status === 'Approved' && p.ActiveInactive === 'Active')
              .map(async p => {
                const subpolicies = await apiService.get(API_ENDPOINTS.POLICY_GET_SUBPOLICIES(p.PolicyId))
                return {
                  id: p.PolicyId,
                  name: p.PolicyName,
                  description: p.PolicyDescription,
                  status: p.Status,
                  department: this.normalizeDepartmentValue(p.Department || p.department),
                  scope: p.Scope,
                  objective: p.Objective,
                  identifier: p.Identifier,
                  coverageRate: p.CoverageRate,
                  applicability: this.normalizeApplicabilityValue(
                    this.getPolicyFieldValue(p, ['Applicability', 'applicability', 'Applicablity', 'applicablity'])
                  ),
                  type: p.PolicyType,
                  category: p.PolicyCategory,
                  subCategory: p.PolicySubCategory,
                  entities: p.Entities,
                  startDate: p.StartDate,
                  endDate: p.EndDate,
                  file: null,
                  createdByName: p.CreatedByName,
                  reviewer: p.Reviewer,
                  activeSubPolicyTab: 0,
                  subPolicies: subpolicies.map(sp => ({
                    id: sp.SubPolicyId,
                    name: sp.SubPolicyName,
                    identifier: sp.Identifier,
                    control: sp.Control,
                    description: sp.Description,
                    status: sp.Status
                  }))
                }
              })
          )
          this.policyTabs = policiesWithDetails
          this.activePolicyTab = 0
          
          // Initialize policyFieldDataTypes and subPolicyFieldDataTypes arrays for each policy
          this.policyFieldDataTypes = []
          this.subPolicyFieldDataTypes = []
          this.policyTabs.forEach((policy, policyIndex) => {
            // Initialize policyFieldDataTypes for this policy with all fields set to 'regular' by default
            this.policyFieldDataTypes[policyIndex] = {
              policyName: 'regular',
              policyIdentifier: 'regular',
              policyDescription: 'regular',
              policyScope: 'regular',
              policyDepartment: 'regular',
              policyObjective: 'regular',
              policyCoverageRate: 'regular',
              policyApplicability: 'regular',
              policyType: 'regular',
              policyCategory: 'regular',
              policySubCategory: 'regular',
              policyEntities: 'regular',
              policyStartDate: 'regular',
              policyEndDate: 'regular',
              policyDocument: 'regular',
              policyCreatedBy: 'regular',
              policyReviewer: 'regular'
            }
            
            // Initialize subPolicyFieldDataTypes for this policy
            this.subPolicyFieldDataTypes[policyIndex] = []
            if (policy.subPolicies && policy.subPolicies.length > 0) {
              policy.subPolicies.forEach((subPolicy, subIndex) => {
                // Initialize subPolicyFieldDataTypes with all fields set to 'regular' by default
                this.subPolicyFieldDataTypes[policyIndex][subIndex] = {
                  subPolicyName: 'regular',
                  subPolicyIdentifier: 'regular',
                  subPolicyDescription: 'regular',
                  subPolicyControl: 'regular'
                }
              })
            }
          })
        } else {
          this.policyTabs = []
          this.activePolicyTab = 0
        }

        this.selectedPolicy = ''
      } catch (error) {
        console.error('Error handling framework selection:', error)
        this.error = 'Failed to load framework details'
      } finally {
        this.loading = false
      }
    },
    handlePolicyFileUpload(e, idx) {
      this.policyTabs[idx].file = e.target.files[0]
    },
    addPolicyTab() {
      const reviewer = this.selectedTab === 'framework' ? this.frameworkForm.reviewer : '';
      const policyIndex = this.policyTabs.length;
      
      this.policyTabs.push({
        id: Date.now(),
        name: '',
        identifier: '',
        description: '',
        scope: '',
        department: '',
        objective: '',
        coverageRate: '',
        applicability: '',
        type: '',
        category: '',
        subCategory: '',
        entities: [],
        showEntitiesDropdown: false,
        // Add dropdown state properties
        showPolicyTypeDropdown: false,
        showPolicyCategoryDropdown: false,
        showPolicySubCategoryDropdown: false,
        policyTypeSearch: '',
        policyCategorySearch: '',
        policySubCategorySearch: '',
        startDate: '',
        endDate: '',
        file: null,
        createdByName: this.currentUser.UserName || this.loggedInUsername,
        reviewer: reviewer,
        subPolicies: [
          {
            id: Date.now(),
            name: '',
            identifier: '',
            control: '',
            description: '',
            createdByName: this.currentUser.UserName || this.loggedInUsername // Use current user name
          }
        ],
        activeSubPolicyTab: 0
      })
      
      // Initialize policyFieldDataTypes for the new policy with all fields set to 'regular' by default
      if (!this.policyFieldDataTypes[policyIndex]) {
        this.policyFieldDataTypes[policyIndex] = {
          policyName: 'regular',
          policyIdentifier: 'regular',
          policyDescription: 'regular',
          policyScope: 'regular',
          policyDepartment: 'regular',
          policyObjective: 'regular',
          policyCoverageRate: 'regular',
          policyApplicability: 'regular',
          policyType: 'regular',
          policyCategory: 'regular',
          policySubCategory: 'regular',
          policyEntities: 'regular',
          policyStartDate: 'regular',
          policyEndDate: 'regular',
          policyDocument: 'regular',
          policyCreatedBy: 'regular',
          policyReviewer: 'regular'
        }
      }
      
      // Initialize subPolicyFieldDataTypes for the new policy
      if (!this.subPolicyFieldDataTypes[policyIndex]) {
        this.subPolicyFieldDataTypes[policyIndex] = []
      }
      // Initialize subPolicyFieldDataTypes for the first subpolicy
      if (this.policyTabs[policyIndex].subPolicies && this.policyTabs[policyIndex].subPolicies.length > 0) {
        this.subPolicyFieldDataTypes[policyIndex][0] = {
          subPolicyName: 'regular',
          subPolicyIdentifier: 'regular',
          subPolicyDescription: 'regular',
          subPolicyControl: 'regular'
        }
      }
      
      this.activePolicyTab = this.policyTabs.length - 1
    },
    excludePolicyTab(idx) {
      if (this.policyTabs.length > 1) {
        // Store the current active tab before removing
        const currentActiveTab = this.activePolicyTab;
        
        // Remove the policy at the specified index
        this.policyTabs.splice(idx, 1);
        
        // Adjust the active tab index
        if (currentActiveTab >= this.policyTabs.length) {
          // If the active tab was at the end or beyond, go to the last remaining tab
          this.activePolicyTab = this.policyTabs.length - 1;
        } else if (currentActiveTab > idx) {
          // If the active tab was after the removed tab, decrement by 1
          this.activePolicyTab = currentActiveTab - 1;
        }
        // If the active tab was before the removed tab, it stays the same
        
        console.log(`Policy ${idx} excluded. Active tab adjusted to: ${this.activePolicyTab}`);
      } else {
        // If only one policy remains, just reset the form
        this.resetForm();
      }
    },
    addSubPolicyTab(policyIdx) {
      const currentPolicy = this.policyTabs[policyIdx];
      const subIndex = this.policyTabs[policyIdx].subPolicies.length;
      
      this.policyTabs[policyIdx].subPolicies.push({
        id: Date.now(),
        name: '',
        identifier: '',
        control: '',
        description: '',
        createdByName: currentPolicy.createdByName || this.currentUser.UserName || this.loggedInUsername // Inherit createdByName from parent policy
      })
      
      // Initialize subPolicyFieldDataTypes for the new subpolicy with all fields set to 'regular' by default
      if (!this.subPolicyFieldDataTypes[policyIdx]) {
        this.subPolicyFieldDataTypes[policyIdx] = [];
      }
      this.subPolicyFieldDataTypes[policyIdx][subIndex] = {
        subPolicyName: 'regular',
        subPolicyIdentifier: 'regular',
        subPolicyDescription: 'regular',
        subPolicyControl: 'regular'
      };
      
      this.policyTabs[policyIdx].activeSubPolicyTab = this.policyTabs[policyIdx].subPolicies.length - 1
    },
    excludeSubPolicyTab(policyIdx, subIdx) {
      const subPolicies = this.policyTabs[policyIdx].subPolicies;
      if (subPolicies.length > 1) {
        // Store the current active subpolicy tab before removing
        const currentActiveSubTab = this.policyTabs[policyIdx].activeSubPolicyTab;
        
        // Remove the subpolicy at the specified index
        subPolicies.splice(subIdx, 1);
        
        // Adjust the active subpolicy tab index
        if (currentActiveSubTab >= subPolicies.length) {
          // If the active tab was at the end or beyond, go to the last remaining tab
          this.policyTabs[policyIdx].activeSubPolicyTab = subPolicies.length - 1;
        } else if (currentActiveSubTab > subIdx) {
          // If the active tab was after the removed tab, decrement by 1
          this.policyTabs[policyIdx].activeSubPolicyTab = currentActiveSubTab - 1;
        }
        // If the active tab was before the removed tab, it stays the same
        
        console.log(`Subpolicy ${subIdx} excluded from policy ${policyIdx}. Active subpolicy tab adjusted to: ${this.policyTabs[policyIdx].activeSubPolicyTab}`);
      } else {
        // If only one subpolicy remains, remove the entire subpolicy section
        this.policyTabs[policyIdx].subPolicies = [];
        this.policyTabs[policyIdx].activeSubPolicyTab = 0;
      }
    },
    resetForm() {
        console.log('resetForm called')
        this.frameworkForm = {
        name: '',
        description: '',
        identifier: '',
        category: '',
        internalExternal: '',
          file: null,
        startDate: '',
        endDate: ''
      }
          this.policyTabs = []
          this.activePolicyTab = 0
          console.log('Policy tabs reset:', this.policyTabs)
          console.log('Active policy tab reset:', this.activePolicyTab)
      this.selectedFramework = ''
        this.selectedPolicy = ''
    },
    async fetchPolicyCategories() {
      try {
        this.loading = true;
        const response = await apiService.get(API_ENDPOINTS.POLICY_CATEGORIES);
        console.log('Raw policy categories response:', response);
        
        // Store complete policy data
        this.policyData = response;
        
        // Extract unique policy types
        this.policyTypes = [...new Set(response.data.map(item => item.PolicyType))];
        
        console.log('Available policy types:', this.policyTypes);
      } catch (error) {
        console.error('Error fetching policy categories:', error);
        this.error = 'Failed to fetch policy categories';
      } finally {
        this.loading = false;
      }
    },
    getCategoriesForType(policyType) {
      if (!policyType || !this.policyData) return [];
      const categories = this.policyData
        .filter(item => item.PolicyType === policyType)
        .map(item => item.PolicyCategory);
      return [...new Set(categories)];
    },

    getSubCategoriesForCategory(policyType, policyCategory) {
      if (!policyType || !policyCategory || !this.policyData) return [];
      const subCategories = this.policyData
        .filter(item => item.PolicyType === policyType && item.PolicyCategory === policyCategory)
        .map(item => item.PolicySubCategory);
      return [...new Set(subCategories)];
    },

    // Department related methods
    async fetchDepartments() {
      try {
        const response = await apiService.get(API_ENDPOINTS.DEPARTMENTS);
        this.departments = response.departments || [];
        console.log('Available departments:', this.departments);
      } catch (error) {
        console.error('Error fetching departments:', error);
        // Provide fallback departments for better user experience
        this.departments = [
          { id: 1, name: 'Information Technology' },
          { id: 2, name: 'Human Resources' },
          { id: 3, name: 'Finance' },
          { id: 4, name: 'Legal' },
          { id: 5, name: 'Operations' },
          { id: 6, name: 'Marketing' },
          { id: 7, name: 'Sales' },
          { id: 8, name: 'Customer Support' }
        ];
        console.log('Using fallback departments due to API error');
        // Don't set error for non-critical API failures
      }
    },
    normalizeDepartmentValue(rawDepartment) {
      if (Array.isArray(rawDepartment)) {
        return rawDepartment.filter(Boolean).join(', ');
      }
      if (rawDepartment === null || rawDepartment === undefined) {
        return '';
      }
      return String(rawDepartment);
    },
    normalizeApplicabilityValue(rawApplicability) {
      if (Array.isArray(rawApplicability)) {
        return rawApplicability.filter(Boolean).join(', ');
      }
      if (rawApplicability && typeof rawApplicability === 'object') {
        return String(rawApplicability.value || rawApplicability.label || rawApplicability.name || '');
      }
      if (rawApplicability === null || rawApplicability === undefined) {
        return '';
      }
      return String(rawApplicability);
    },
    getPolicyFieldValue(policyObj, candidateKeys = []) {
      if (!policyObj || typeof policyObj !== 'object') {
        return '';
      }

      const extractedRaw = policyObj.ExtractedData;
      let extractedData = {};
      if (typeof extractedRaw === 'string') {
        try {
          extractedData = JSON.parse(extractedRaw);
        } catch (error) {
          extractedData = {};
        }
      } else if (extractedRaw && typeof extractedRaw === 'object') {
        extractedData = extractedRaw;
      }

      for (const key of candidateKeys) {
        if (policyObj[key] !== undefined && policyObj[key] !== null && policyObj[key] !== '') {
          return policyObj[key];
        }
        if (extractedData[key] !== undefined && extractedData[key] !== null && extractedData[key] !== '') {
          return extractedData[key];
        }
      }

      return '';
    },
    getDepartmentDropdownOptions(policyIndex) {
      const baseOptions = this.departments
        .map(dept => dept?.name)
        .filter(Boolean);
      const currentValue = this.policyTabs?.[policyIndex]?.department;
      if (currentValue && !baseOptions.includes(currentValue)) {
        return [currentValue, ...baseOptions];
      }
      return baseOptions;
    },

    async saveDepartment(departmentName) {
      try {
        const payload = {
          DepartmentName: departmentName,
          EntityId: 1,
          DepartmentHead: 1,
          BusinessUnitId: 1
        };
        if (this.selectedFramework) {
          payload.FrameworkId = this.selectedFramework;
        }
        const response = await apiService.post(API_ENDPOINTS.DEPARTMENTS_SAVE, payload);

        if (response && response.success !== false) {
          console.log('Department saved:', response.department);
          await this.fetchDepartments();
          return response.department;
        }
      } catch (error) {
        // Non-fatal: policy submit stores department as text on the policy row.
        console.warn('Department save skipped:', error);
      }
    },

    async handleDepartmentChange(idx, value) {
      // Update the policy department value
      this.policyTabs[idx].department = value;
      
      // Check if this is a new department (not in existing list)
      const existingDepartment = this.departments.find(dept => 
        dept.name.toLowerCase() === value.toLowerCase()
      );
      
      if (!existingDepartment && value.trim().length > 0) {
        // This might be a new department, save it when form is submitted
        console.log('New department detected:', value);
      }
    },

    async saveNewDepartments() {
      try {
        console.log('Checking for new departments to save...');
        const newDepartments = [];
        
        // Process all policies to find new departments
        for (const policy of this.policyTabs) {
          const deptName = policy.department?.trim();
          
          if (!deptName) continue;
          
          // Check if this department exists in our local data
          const exists = this.departments.some(dept => 
            dept.name.toLowerCase() === deptName.toLowerCase()
          );
          
          if (!exists && !newDepartments.includes(deptName)) {
            console.log(`Found new department: ${deptName}`);
            newDepartments.push(deptName);
          }
        }
        
        // Save new departments to the database
        if (newDepartments.length > 0) {
          console.log(`Saving ${newDepartments.length} new departments...`);
          
          for (const deptName of newDepartments) {
            await this.saveDepartment(deptName);
          }
          
          console.log('New departments saved successfully');
        } else {
          console.log('No new departments to save');
        }
      } catch (err) {
        console.error('Error saving new departments:', err);
      }
    },

    async saveNewPolicyCategories() {
      try {
        console.log('🔍 DEBUG: Checking for new policy categories to save...');
        console.log('🔍 DEBUG: Current selectedFramework:', this.selectedFramework);
        
        if (!this.selectedFramework) {
          console.warn('⚠️ DEBUG: No framework selected, skipping policy category save');
          return;
        }
        const newCombinations = [];
        
        // Process all policies to find new category combinations
        for (const policy of this.policyTabs) {
          const type = policy.type?.trim();
          const category = policy.category?.trim();
          const subcategory = policy.subCategory?.trim();
          
          // Skip if any part of the combination is missing
          if (!type || !category || !subcategory) {
            continue;
          }
          
          // Check if this combination exists in our local data
          const exists = this.policyData.some(pc => 
            pc.PolicyType === type && 
            pc.PolicyCategory === category && 
            pc.PolicySubCategory === subcategory
          );
          
          if (!exists) {
            console.log(`Found new combination: ${type} > ${category} > ${subcategory}`);
            const combinationKey = `${type}|${category}|${subcategory}`;
            if (!newCombinations.find(c => `${c.PolicyType}|${c.PolicyCategory}|${c.PolicySubCategory}` === combinationKey)) {
              newCombinations.push({
                PolicyType: type,
                PolicyCategory: category,
                PolicySubCategory: subcategory
              });
            }
          }
        }
        
        // Save new combinations to the database
        if (newCombinations.length > 0) {
          console.log(`Saving ${newCombinations.length} new policy category combinations...`);
          
          for (const combination of newCombinations) {
            // Include framework context when saving policy categories
            const combinationWithFramework = {
              ...combination,
              frameworkId: this.selectedFramework
            };
            console.log('🔍 DEBUG: Saving policy category with framework:', combinationWithFramework);
            console.log('🔍 DEBUG: API endpoint:', API_ENDPOINTS.POLICY_CATEGORIES_SAVE);
            console.log('🔍 DEBUG: Selected framework:', this.selectedFramework);
            
            try {
              const response = await apiService.post(API_ENDPOINTS.POLICY_CATEGORIES_SAVE, combinationWithFramework);
              console.log('✅ DEBUG: Policy category saved successfully:', response);
            } catch (error) {
              console.error('❌ DEBUG: Failed to save policy category:', error);
              throw error; // Re-throw to be caught by outer try-catch
            }
          }
          
          // Refresh policy categories after saving
          await this.fetchPolicyCategories();
          console.log('Policy categories refreshed');
        } else {
          console.log('No new policy category combinations to save');
        }
      } catch (err) {
        console.error('Error saving new policy categories:', err);
      }
    },

    // Policy Type Dropdown Methods
    togglePolicyTypeDropdown(idx) {
      // Close other dropdowns first
      this.policyTabs.forEach((tab, i) => {
        if (i !== idx) {
          tab.showPolicyTypeDropdown = false;
          tab.showPolicyCategoryDropdown = false;
          tab.showPolicySubCategoryDropdown = false;
        }
      });
      
      this.policyTabs[idx].showPolicyTypeDropdown = !this.policyTabs[idx].showPolicyTypeDropdown;
    },

    filterPolicyTypes() {
      // This function is called on input to filter policy types
      // The filtering is handled in getFilteredPolicyTypes
    },

    getFilteredPolicyTypes(idx) {
      const searchQuery = this.policyTabs[idx].policyTypeSearch || '';
      if (!searchQuery) return this.policyTypes;
      
      return this.policyTypes.filter(type => 
        type.toLowerCase().includes(searchQuery.toLowerCase())
      );
    },

    selectPolicyType(idx, type) {
      this.policyTabs[idx].type = type;
      this.policyTabs[idx].showPolicyTypeDropdown = false;
      this.policyTabs[idx].policyTypeSearch = '';
      
      // Clear category and subcategory when type changes
      this.policyTabs[idx].category = '';
      this.policyTabs[idx].subCategory = '';
      
      // Update available categories for this type
      this.updatePolicyCategoriesByType(type);
    },

    async createNewPolicyType(idx) {
      const newType = this.policyTabs[idx].policyTypeSearch?.trim();
      if (!newType) return;
      
      try {
        // Add to local array first for immediate UI update
        if (!this.policyTypes.includes(newType)) {
          this.policyTypes.push(newType);
        }
        
        // Select the new type
        this.selectPolicyType(idx, newType);
        
        // Clear search
        this.policyTabs[idx].policyTypeSearch = '';
        
        // Show success message
        if (this.$toast) {
          this.$toast.success(`Policy type "${newType}" added successfully!`);
        }
      } catch (err) {
        console.error('Error creating policy type:', err);
        if (this.$toast) {
          this.$toast.error('Failed to create policy type. Please try again.');
        }
      }
    },

    // Policy Category Dropdown Methods
    togglePolicyCategoryDropdown(idx) {
      // Close other dropdowns first
      this.policyTabs.forEach((tab, i) => {
        if (i !== idx) {
          tab.showPolicyTypeDropdown = false;
          tab.showPolicyCategoryDropdown = false;
          tab.showPolicySubCategoryDropdown = false;
        }
      });
      
      this.policyTabs[idx].showPolicyCategoryDropdown = !this.policyTabs[idx].showPolicyCategoryDropdown;
    },

    filterPolicyCategories() {
      // This function is called on input to filter policy categories
      // The filtering is handled in getFilteredPolicyCategories
    },

    getFilteredPolicyCategories(idx) {
      const searchQuery = this.policyTabs[idx].policyCategorySearch || '';
      const policyType = this.policyTabs[idx].type;
      
      if (!policyType) return [];
      
      const categories = this.getCategoriesForType(policyType);
      
      if (!searchQuery) return categories;
      
      return categories.filter(category => 
        category.toLowerCase().includes(searchQuery.toLowerCase())
      );
    },

    selectPolicyCategory(idx, category) {
      this.policyTabs[idx].category = category;
      this.policyTabs[idx].showPolicyCategoryDropdown = false;
      this.policyTabs[idx].policyCategorySearch = '';
      
      // Clear subcategory when category changes
      this.policyTabs[idx].subCategory = '';
      
      // Update available subcategories for this type and category
      this.updateSubCategoriesByCategory(this.policyTabs[idx].type, category);
    },

    async createNewPolicyCategory(idx) {
      const newCategory = this.policyTabs[idx].policyCategorySearch?.trim();
      const policyType = this.policyTabs[idx].type;
      
      if (!newCategory || !policyType) {
        if (this.$toast) {
          this.$toast.error('Please select a policy type first.');
        }
        return;
      }
      
      try {
        // Add to local array first for immediate UI update
        const categories = this.getCategoriesForType(policyType);
        if (!categories.includes(newCategory)) {
          // Add to policyCategories array
          this.policyCategories.push({
            PolicyType: policyType,
            PolicyCategory: newCategory,
            PolicySubCategory: 'Default'
          });
          
          // Save to database immediately if we have a selected framework and subcategory
          if (this.selectedFramework) {
            console.log('🔍 DEBUG: Saving new policy category to database immediately');
            try {
              const response = await apiService.post(API_ENDPOINTS.POLICY_CATEGORIES_SAVE, {
                PolicyType: policyType,
                PolicyCategory: newCategory,
                PolicySubCategory: 'Default',
                frameworkId: this.selectedFramework
              });
              console.log('✅ DEBUG: Policy category saved to database:', response);
            } catch (apiError) {
              console.error('❌ DEBUG: Failed to save policy category to database:', apiError);
              console.error('❌ DEBUG: Error response:', apiError.response?.data);
            }
          }
        }
        
        // Select the new category
        this.selectPolicyCategory(idx, newCategory);
        
        // Clear search
        this.policyTabs[idx].policyCategorySearch = '';
        
        // Show success message
        if (this.$toast) {
          this.$toast.success(`Policy category "${newCategory}" added successfully!`);
        }
      } catch (err) {
        console.error('Error creating policy category:', err);
        if (this.$toast) {
          this.$toast.error('Failed to create policy category. Please try again.');
        }
      }
    },

    // Policy Subcategory Dropdown Methods
    togglePolicySubCategoryDropdown(idx) {
      // Close other dropdowns first
      this.policyTabs.forEach((tab, i) => {
        if (i !== idx) {
          tab.showPolicyTypeDropdown = false;
          tab.showPolicyCategoryDropdown = false;
          tab.showPolicySubCategoryDropdown = false;
        }
      });
      
      this.policyTabs[idx].showPolicySubCategoryDropdown = !this.policyTabs[idx].showPolicySubCategoryDropdown;
    },

    filterPolicySubCategories() {
      // This function is called on input to filter policy subcategories
      // The filtering is handled in getFilteredPolicySubCategories
    },

    getFilteredPolicySubCategories(idx) {
      const searchQuery = this.policyTabs[idx].policySubCategorySearch || '';
      const policyType = this.policyTabs[idx].type;
      const policyCategory = this.policyTabs[idx].category;
      
      if (!policyType || !policyCategory) return [];
      
      const subCategories = this.getSubCategoriesForCategory(policyType, policyCategory);
      
      if (!searchQuery) return subCategories;
      
      return subCategories.filter(subCategory => 
        subCategory.toLowerCase().includes(searchQuery.toLowerCase())
      );
    },

    selectPolicySubCategory(idx, subCategory) {
      this.policyTabs[idx].subCategory = subCategory;
      this.policyTabs[idx].showPolicySubCategoryDropdown = false;
      this.policyTabs[idx].policySubCategorySearch = '';
    },

    async createNewPolicySubCategory(idx) {
      const newSubCategory = this.policyTabs[idx].policySubCategorySearch?.trim();
      const policyType = this.policyTabs[idx].type;
      const policyCategory = this.policyTabs[idx].category;
      
      if (!newSubCategory || !policyType || !policyCategory) {
        if (this.$toast) {
          this.$toast.error('Please select a policy type and category first.');
        }
        return;
      }
      
      try {
        // Add to local array first for immediate UI update
        const subCategories = this.getSubCategoriesForCategory(policyType, policyCategory);
        if (!subCategories.includes(newSubCategory)) {
          // Add to policyCategories array
          this.policyCategories.push({
            PolicyType: policyType,
            PolicyCategory: policyCategory,
            PolicySubCategory: newSubCategory
          });
          
          // Save to database immediately if we have a selected framework
          if (this.selectedFramework) {
            console.log('🔍 DEBUG: Saving new policy subcategory combination to database immediately');
            console.log('🔍 DEBUG: Data:', { policyType, policyCategory, newSubCategory, framework: this.selectedFramework });
            try {
              const response = await apiService.post(API_ENDPOINTS.POLICY_CATEGORIES_SAVE, {
                PolicyType: policyType,
                PolicyCategory: policyCategory,
                PolicySubCategory: newSubCategory,
                frameworkId: this.selectedFramework
              });
              console.log('✅ DEBUG: Policy category combination saved to database:', response);
              
              // Refresh policy categories after saving
              await this.fetchPolicyCategories();
            } catch (apiError) {
              console.error('❌ DEBUG: Failed to save policy category combination to database:', apiError);
              console.error('❌ DEBUG: Error response:', apiError.response?.data);
              console.error('❌ DEBUG: Error status:', apiError.response?.status);
            }
          } else {
            console.warn('⚠️ DEBUG: No framework selected, policy category will not be saved to database');
          }
        }
        
        // Select the new subcategory
        this.selectPolicySubCategory(idx, newSubCategory);
        
        // Clear search
        this.policyTabs[idx].policySubCategorySearch = '';
        
        // Show success message
        if (this.$toast) {
          this.$toast.success(`Policy subcategory "${newSubCategory}" added successfully!`);
        }
      } catch (err) {
        console.error('Error creating policy subcategory:', err);
        if (this.$toast) {
          this.$toast.error('Failed to create policy subcategory. Please try again.');
        }
      }
    },

    updatePolicyCategoriesByType(policyType) {
      console.log('Updating categories for type:', policyType)
      if (!policyType || !this.policyData) {
        this.policyCategories = []
        this.policySubCategories = []
        return
      }

      // Filter categories based on selected type
      const filteredData = this.policyData.filter(item => item.PolicyType === policyType)
      console.log('Filtered data:', filteredData)

      const categories = [...new Set(filteredData.map(item => item.PolicyCategory))]
      console.log('Available categories for type:', categories)
      this.policyCategories = categories

      // Reset category and subcategory in the active policy tab
      if (this.policyTabs[this.activePolicyTab]) {
        this.policyTabs[this.activePolicyTab].category = ''
        this.policyTabs[this.activePolicyTab].subCategory = ''
      }
      this.policySubCategories = []
    },
    updateSubCategoriesByCategory(policyType, policyCategory) {
      console.log('Updating subcategories for type:', policyType, 'and category:', policyCategory)
      if (!policyType || !policyCategory || !this.policyData) {
        this.policySubCategories = []
        return
      }

      // Filter subcategories based on selected type and category
      const filteredData = this.policyData.filter(item => 
        item.PolicyType === policyType && 
        item.PolicyCategory === policyCategory
      )
      console.log('Filtered data:', filteredData)

      const subcategories = [...new Set(filteredData.map(item => item.PolicySubCategory))]
      console.log('Available subcategories:', subcategories)
      this.policySubCategories = subcategories

      // Reset subcategory in the active policy tab
      if (this.policyTabs[this.activePolicyTab]) {
        this.policyTabs[this.activePolicyTab].subCategory = ''
      }
    },
    async fetchEntities() {
      try {
        this.loading = true;
        const response = await apiService.get(API_ENDPOINTS.ENTITIES);
        console.log('Raw entities response:', response);
        
        if (response.entities) {
          // Map entities directly from the backend response
          this.entities = response.entities.map(entity => ({
            id: entity.id,
            label: entity.label
          }));
          console.log('Mapped entities:', this.entities);
      } else {
          throw new Error('Invalid response format');
        }
      } catch (error) {
        console.error('Error fetching entities:', error);
        this.error = 'Failed to fetch entities';
      } finally {
        this.loading = false;
      }
    },

    handleEntitySelection(idx, entityId, isChecked) {
      if (idx < 0 || !this.policyTabs[idx]) return;
      
      console.log('handleEntitySelection:', { idx, entityId, isChecked });
      
      // Initialize entities if undefined
      if (!this.policyTabs[idx].entities) {
        this.policyTabs[idx].entities = [];
      }
      
      if (entityId === 'all') {
        // When "All Locations" is selected, set entities to "all" string
        this.policyTabs[idx].entities = isChecked ? "all" : [];
      } else {
        // Ensure we're working with an array
        let currentEntities = this.policyTabs[idx].entities === "all" ? [] 
          : Array.isArray(this.policyTabs[idx].entities) ? this.policyTabs[idx].entities 
          : [];
        
        const numericId = Number(entityId);
        
        if (isChecked) {
          if (!currentEntities.includes(numericId)) {
            currentEntities.push(numericId);
          }
        } else {
          currentEntities = currentEntities.filter(id => id !== numericId);
        }
        
        // Store as array of numeric IDs
        this.policyTabs[idx].entities = currentEntities;
      }
      
      console.log('Updated entities:', this.policyTabs[idx].entities);
    },

    selectEntity(idx, entityId) {
      if (idx < 0 || !this.policyTabs[idx]) return;
      
      const isSelected = entityId === 'all' 
        ? this.isAllEntitiesSelected(idx)
        : this.isEntitySelected(idx, entityId);
      
      this.handleEntitySelection(idx, entityId, !isSelected);
    },

    isEntitySelected(idx, entityId) {
      const policy = this.policyTabs[idx];
      if (!policy || !policy.entities) return false;
      
      if (policy.entities === "all") {
        return entityId === 'all';
      }
      
      return Array.isArray(policy.entities) && policy.entities.includes(Number(entityId));
    },

    isAllEntitiesSelected(idx) {
      const policy = this.policyTabs[idx];
      return policy && policy.entities === "all";
    },

    getSelectedEntitiesCount(idx) {
      const policy = this.policyTabs[idx];
      if (!policy || !policy.entities) return 0;
      
      if (policy.entities === "all") {
        return this.entities.length - 1; // Subtract 1 for the "All" option
      }
      
      return Array.isArray(policy.entities) ? policy.entities.length : 0;
    },

    toggleEntitiesDropdown(idx) {
      if (idx < 0 || !this.policyTabs[idx]) return;
      
      // Close all other dropdowns first
      this.policyTabs.forEach((policy, index) => {
        if (index !== idx) {
          policy.showEntitiesDropdown = false;
        }
      });
      
      // Toggle current dropdown
      const currentPolicy = this.policyTabs[idx];
      currentPolicy.showEntitiesDropdown = !currentPolicy.showEntitiesDropdown;
      
      // If opening the dropdown and no entities loaded yet, fetch them
      if (currentPolicy.showEntitiesDropdown && this.entities.length <= 1) {
        this.fetchEntities();
      }
    },

    closeAllEntityDropdowns() {
      this.policyTabs.forEach(policy => {
        policy.showEntitiesDropdown = false;
      });
    },

    handleClickOutside(event) {
      // Handle entity dropdowns
      const entityDropdowns = document.querySelectorAll('.entities-multi-select');
      entityDropdowns.forEach(dropdown => {
        if (!dropdown.contains(event.target)) {
          this.closeAllEntityDropdowns();
        }
      });
      
      // Handle policy dropdowns
      const policyDropdowns = document.querySelectorAll('.policy-type-multi-select, .policy-category-multi-select, .policy-subcategory-multi-select');
      policyDropdowns.forEach(dropdown => {
        if (!dropdown.contains(event.target)) {
          // Close all policy dropdowns
          this.policyTabs.forEach(tab => {
            tab.showPolicyTypeDropdown = false;
            tab.showPolicyCategoryDropdown = false;
            tab.showPolicySubCategoryDropdown = false;
          });
        }
      });
    },

    async fetchCurrentUser() {
      try {
        const response = await apiService.get(API_ENDPOINTS.USER_ROLE)
        if (response.success) {
          this.currentUser = {
            UserId: response.user_id,
            UserName: response.username || response.user_name || localStorage.getItem('username') || '',
            Role: response.role
          }
          // Update loggedInUsername and frameworkForm.createdByName with current user name
          this.loggedInUsername = this.currentUser.UserName
          this.frameworkForm.createdByName = this.currentUser.UserName
          
          console.log('Current user loaded:', this.currentUser)
        }
      } catch (err) {
        console.error('Error fetching current user:', err)
        // Fallback to localStorage if API fails
        const storedUsername = localStorage.getItem('username')
        if (storedUsername) {
          this.currentUser.UserName = storedUsername
          this.loggedInUsername = storedUsername
          this.frameworkForm.createdByName = storedUsername
        }
      }
    },
    async fetchUsers() {
      try {
        // Fetch reviewers filtered by RBAC permissions based on current tab
        // For framework tab: use 'framework', for policy tab: use 'policy'
        const module = this.selectedTab === 'framework' ? 'framework' : 'policy'
        const currentUserId = this.currentUser?.UserId || ''
        const response = await apiService.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION, {
          module: module,
          current_user_id: currentUserId
        })
        console.log('Raw users response:', response)
        this.users = response.map(user => ({
          id: user.UserId,
          name: user.UserName
        }))
        console.log('Mapped users:', this.users)
      } catch (error) {
        console.error('Error fetching users:', error)
        this.error = 'Failed to fetch users'
      }
    },
    // Add new method to handle CreatedByName changes
    handleCreatedByNameChange() {
      // Update CreatedByName for all subpolicies when policy's CreatedByName changes
      if (this.selectedTab === 'policy' && this.policyTabs[this.activePolicyTab]) {
        const newCreatedByName = this.policyTabs[this.activePolicyTab].createdByName;
        this.policyTabs[this.activePolicyTab].subPolicies.forEach(subPolicy => {
          subPolicy.createdByName = newCreatedByName;
        });
      }
    },
    async submitTailoredPolicy() {
      console.log('submitTailoredPolicy called')
      console.log('policyTabs:', this.policyTabs)
      console.log('activePolicyTab:', this.activePolicyTab)
      console.log('selectedFramework:', this.selectedFramework)
      console.log('selectedPolicy:', this.selectedPolicy)
      
      // Validate that we have a valid active policy tab
      if (!this.policyTabs || this.policyTabs.length === 0) {
        console.error('No policy tabs available')
        PopupService.error('No policy data available. Please select a policy first.', 'Validation Error');
        return;
      }

      if (this.activePolicyTab < 0 || this.activePolicyTab >= this.policyTabs.length) {
        console.error('Invalid active policy tab index:', this.activePolicyTab, 'length:', this.policyTabs.length)
        PopupService.error('Invalid policy tab selected. Please select a valid policy.', 'Validation Error');
        return;
      }

      const currentPolicy = this.policyTabs[this.activePolicyTab];
      console.log('Current policy:', currentPolicy)
      
      if (!currentPolicy) {
        console.error('Current policy is undefined')
        PopupService.error('Selected policy is invalid. Please try again.', 'Validation Error');
        return;
      }

      if (!this.validateForm('policy')) {
        return;
      }
      if (this.isPolicyCreatorReviewerSame) {
        return;
      }

      if (this.ttPolicyCreateInFlight) {
        return;
      }

      const loggedInUser = this.loggedInUsername || 'default_user';

      try {
        this.loading = true;

        // Renewal/self-heal edits an existing policy; department/categories already exist in DB.
        if (!this.isSelfHealRouteQuery()) {
          await this.saveNewDepartments();
          await this.saveNewPolicyCategories();
        }

        this.loading = false;

        // Validate coverage rate
        const coverageRate = parseFloat(currentPolicy.coverageRate);
        if (isNaN(coverageRate) || coverageRate < 0 || coverageRate > 100) {
          throw new Error('Coverage Rate must be a number between 0 and 100');
        }

        // Convert reviewer (dropdown stores UserId, or legacy username from API) to Reviewer username for backend
        const rid = currentPolicy.reviewer
        let policyReviewerName = ''
        if (rid !== '' && rid != null) {
          const policyReviewerUser = this.users.find(
            (u) => String(u.id) === String(rid)
          )
          if (policyReviewerUser) {
            policyReviewerName = policyReviewerUser.name
          } else {
            policyReviewerName = String(rid).trim()
          }
        }


        const policyFieldLabelMap = {
          policyName: 'Policy Name',
          policyIdentifier: 'Policy Identifier',
          policyDescription: 'Description',
          policyScope: 'Scope',
          policyDepartment: 'Department',
          policyObjective: 'Objective',
          policyCoverageRate: 'Coverage Rate (%)',
          policyApplicability: 'Applicability',
          policyType: 'Policy Type',
          policyCategory: 'Policy Category',
          policySubCategory: 'Policy Sub Category',
          policyEntities: 'Entities',
          policyStartDate: 'Start Date',
          policyEndDate: 'End Date',
          policyDocument: 'Upload Document',
          policyCreatedBy: 'Created By',
          policyReviewer: 'Reviewer'
        };

        const policyDataInventory = {};
        if (this.policyFieldDataTypes[this.activePolicyTab]) {
          Object.keys(policyFieldLabelMap).forEach(key => {
            if (this.policyFieldDataTypes[this.activePolicyTab][key]) {
              policyDataInventory[policyFieldLabelMap[key]] = this.policyFieldDataTypes[this.activePolicyTab][key];
            }
          });
        }

        const subPolicyFieldLabelMap = {
          subPolicyName: 'Sub Policy Name',
          subPolicyIdentifier: 'Sub Policy Identifier',
          subPolicyDescription: 'Description',
          subPolicyControl: 'Control'
        };
        if (this.isSelfHealRouteQuery()) {
          const baseId = String((this.$route.query && this.$route.query.policyId) || '').trim()
          if (!baseId) {
            throw new Error('Missing policy id for renewal version submit.')
          }
          const ridForVersion = currentPolicy.reviewer
          let reviewerUserId = null
          if (ridForVersion !== '' && ridForVersion != null) {
            const u1 = this.users.find((u) => String(u.id) === String(ridForVersion))
            const u2 = this.users.find(
              (u) => String(u.name || '').toLowerCase() === String(ridForVersion).toLowerCase()
            )
            const u = u1 || u2
            if (u) reviewerUserId = u.id
          }

          const versionData = {
            version_type: 'minor',
            PolicyName: currentPolicy.name,
            PolicyDescription: currentPolicy.description,
            Department: currentPolicy.department,
            Scope: currentPolicy.scope,
            Objective: currentPolicy.objective,
            Identifier: currentPolicy.identifier,
            CoverageRate: coverageRate,
            Applicability: currentPolicy.applicability,
            CreatedByName: currentPolicy.createdByName || this.loggedInUsername,
            StartDate: currentPolicy.startDate,
            EndDate: currentPolicy.endDate,
            PermanentTemporary: currentPolicy.permanentTemporary || '',
            DocURL: currentPolicy.docURL || '',
            PolicyType: currentPolicy.type,
            PolicyCategory: currentPolicy.category,
            PolicySubCategory: currentPolicy.subCategory,
            Entities: currentPolicy.entities,
            Reviewer: reviewerUserId != null ? reviewerUserId : ridForVersion,
            data_inventory: policyDataInventory
          }

          const subpolicies = []
          const new_subpolicies = []
          ;(currentPolicy.subPolicies || []).forEach((sub, subIndex) => {
            const subPolicyDataInventory = {}
            if (
              this.subPolicyFieldDataTypes[this.activePolicyTab] &&
              this.subPolicyFieldDataTypes[this.activePolicyTab][subIndex]
            ) {
              Object.keys(subPolicyFieldLabelMap).forEach((key) => {
                if (this.subPolicyFieldDataTypes[this.activePolicyTab][subIndex][key]) {
                  subPolicyDataInventory[subPolicyFieldLabelMap[key]] =
                    this.subPolicyFieldDataTypes[this.activePolicyTab][subIndex][key]
                }
              })
            }
            if (sub.id && !String(sub.id).startsWith('new-')) {
              subpolicies.push({
                original_subpolicy_id: parseInt(String(sub.id), 10),
                SubPolicyName: sub.name,
                Description: sub.description,
                Identifier: sub.identifier,
                CreatedByName: sub.createdByName || currentPolicy.createdByName || this.loggedInUsername,
                PermanentTemporary: sub.permanentTemporary || '',
                Control: sub.control,
                exclude: sub.exclude || false,
                data_inventory: subPolicyDataInventory
              })
            } else if (!sub.exclude) {
              new_subpolicies.push({
                SubPolicyName: sub.name,
                Description: sub.description,
                Identifier: sub.identifier,
                CreatedByName: sub.createdByName || currentPolicy.createdByName || this.loggedInUsername,
                PermanentTemporary: sub.permanentTemporary || '',
                Control: sub.control,
                data_inventory: subPolicyDataInventory
              })
            }
          })
          versionData.subpolicies = subpolicies
          versionData.new_subpolicies = new_subpolicies

          const pendingSave = {
            operation: 'policy_version',
            entity_pk: parseInt(baseId, 10),
            payload: versionData,
            label: currentPolicy.name,
            summary: 'Policy renewal version',
            meta: { loggedInUser },
          }
          if (await this._tryStartTtAsyncSimilarity('policy', pendingSave)) {
            return
          }
          await this._executeTtPolicyPendingSave(pendingSave)
        } else {
        const policyNameSnapshot = currentPolicy.name;
        const policyDescSnapshot = currentPolicy.description;

        const policyData = {
          TargetFrameworkId: this.selectedFramework,
          PolicyName: currentPolicy.name,
          PolicyDescription: currentPolicy.description,
          Department: currentPolicy.department,
          Scope: currentPolicy.scope,
          Objective: currentPolicy.objective,
          CoverageRate: coverageRate,
          Applicability: currentPolicy.applicability,
          PolicyType: currentPolicy.type,
          PolicyCategory: currentPolicy.category,
          PolicySubCategory: currentPolicy.subCategory,
          Entities: currentPolicy.entities,
          StartDate: currentPolicy.startDate,
          EndDate: currentPolicy.endDate,
          CreatedByName: this.loggedInUsername,
          Reviewer: policyReviewerName,
          Identifier: currentPolicy.identifier,
          data_inventory: policyDataInventory,
          subpolicies: currentPolicy.subPolicies ? currentPolicy.subPolicies.map((sub, subIndex) => {
            const subPolicyDataInventory = {};
            if (this.subPolicyFieldDataTypes[this.activePolicyTab] && this.subPolicyFieldDataTypes[this.activePolicyTab][subIndex]) {
              Object.keys(subPolicyFieldLabelMap).forEach(key => {
                if (this.subPolicyFieldDataTypes[this.activePolicyTab][subIndex][key]) {
                  subPolicyDataInventory[subPolicyFieldLabelMap[key]] = this.subPolicyFieldDataTypes[this.activePolicyTab][subIndex][key];
                }
              });
            }

            return {
              SubPolicyName: sub.name,
              Identifier: sub.identifier,
              Description: sub.description,
              Control: sub.control,
              exclude: false,
              data_inventory: subPolicyDataInventory
            };
          }) : []
        };

        const pendingSave = {
          operation: 'tt_create_policy',
          entity_pk: parseInt(this.selectedFramework, 10) || null,
          payload: policyData,
          label: currentPolicy.name,
          summary: 'Tailoring policy submit',
          meta: { loggedInUser, policyNameSnapshot, policyDescSnapshot },
        }
        if (await this._tryStartTtAsyncSimilarity('policy', pendingSave)) {
          return
        }
        await this._executeTtPolicyPendingSave(pendingSave)
        }
      } catch (error) {
        console.error('Error preparing policy submission:', error);
        this.loading = false;
        this.error = error.response?.data?.error || error.message || 'Failed to submit policy';
        PopupService.error(this.error, 'Error Creating Policy');
        void this.sendPushNotification({
          title: 'Policy Creation Failed',
          message: `Failed to create policy "${currentPolicy.name}": ${this.error}`,
          category: 'policy',
          priority: 'high',
          user_id: loggedInUser
        });
      }
    },
    // Add validation method
    validateForm(type) {
      if (type === 'framework') {
        if (!this.frameworkForm.name) {
          PopupService.warning('Framework name is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Framework name is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.frameworkForm.description) {
          PopupService.warning('Framework description is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Framework description is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.frameworkForm.identifier) {
          PopupService.warning('Framework identifier is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Framework identifier is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.frameworkForm.category) {
          PopupService.warning('Framework category is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Framework category is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.frameworkForm.internalExternal) {
          PopupService.warning('Internal/External selection is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Internal/External selection is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.frameworkForm.startDate) {
          PopupService.warning('Start date is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Start date is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.loggedInUsername) {
          PopupService.warning('You must be logged in to create a framework', 'Validation Error');
          this.sendPushNotification({
            title: 'Authentication Error',
            message: 'You must be logged in to create a framework',
            category: 'framework',
            priority: 'high',
            user_id: 'default_user'
          });
          return false;
        }
        if (!this.frameworkForm.reviewer) {
          PopupService.warning('Reviewer is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Framework Validation Error',
            message: 'Reviewer is required for framework creation',
            category: 'framework',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }

        // Validate that creator and reviewer are not the same person
        if (this.currentUser.UserName && this.frameworkForm.reviewer) {
          const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
          const reviewerUser = this.users.find(u => u.id === this.frameworkForm.reviewer);
          
          if (creatorUser && reviewerUser && creatorUser.id === reviewerUser.id) {
            PopupService.warning('Creator and reviewer cannot be the same person. Please select a different reviewer.', 'Validation Error');
            this.sendPushNotification({
              title: 'Framework Validation Error',
              message: 'Creator and reviewer cannot be the same person. Please select a different reviewer.',
              category: 'framework',
              priority: 'high',
              user_id: this.currentUser.UserName || 'default_user'
            });
            return false;
          }
        }
        return true;
      }

      if (type === 'policy') {
        // Validate that we have a valid active policy tab
        if (!this.policyTabs || this.policyTabs.length === 0) {
          PopupService.warning('No policy data available. Please select a policy first.', 'Validation Error');
          return false;
        }

        if (this.activePolicyTab < 0 || this.activePolicyTab >= this.policyTabs.length) {
          PopupService.warning('Invalid policy tab selected. Please select a valid policy.', 'Validation Error');
          return false;
        }

        const policy = this.policyTabs[this.activePolicyTab];
        if (!policy) {
          PopupService.warning('Selected policy is invalid. Please try again.', 'Validation Error');
          return false;
        }

        if (!policy.name) {
          PopupService.warning('Policy name is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Policy name is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.description) {
          PopupService.warning('Policy description is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Policy description is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.identifier) {
          PopupService.warning('Policy identifier is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Policy identifier is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.department) {
          PopupService.warning('Department is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Department is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.scope) {
          PopupService.warning('Scope is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Scope is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.objective) {
          PopupService.warning('Objective is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Objective is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.coverageRate) {
          PopupService.warning('Coverage Rate is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Coverage Rate is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.applicability) {
          PopupService.warning('Applicability is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Applicability is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.type) {
          PopupService.warning('Policy Type is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Policy Type is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.category) {
          PopupService.warning('Policy Category is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Policy Category is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.subCategory) {
          PopupService.warning('Policy Sub Category is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Policy Sub Category is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!policy.startDate) {
          PopupService.warning('Start Date is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Start Date is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        if (!this.loggedInUsername) {
          PopupService.warning('You must be logged in to create a policy', 'Validation Error');
          this.sendPushNotification({
            title: 'Authentication Error',
            message: 'You must be logged in to create a policy',
            category: 'policy',
            priority: 'high',
            user_id: 'default_user'
          });
          return false;
        }
        if (!policy.reviewer) {
          PopupService.warning('Reviewer is required', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'Reviewer is required for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }

        // Validate that creator and reviewer are not the same person
        if (this.currentUser.UserName && policy.reviewer) {
          const creatorUser = this.users.find(u => u.name === this.currentUser.UserName);
          const pr = policy.reviewer
          const reviewerUser = this.users.find(
            (u) => String(u.id) === String(pr) ||
              String(u.name || '').toLowerCase() === String(pr).toLowerCase()
          )
          
          if (creatorUser && reviewerUser && creatorUser.id === reviewerUser.id) {
            PopupService.warning('Creator and reviewer cannot be the same person. Please select a different reviewer.', 'Validation Error');
            this.sendPushNotification({
              title: 'Policy Validation Error',
              message: 'Creator and reviewer cannot be the same person. Please select a different reviewer.',
              category: 'policy',
              priority: 'high',
              user_id: this.currentUser.UserName || 'default_user'
            });
            return false;
          }
        }
        // Check entities validation - must be "all" or non-empty array
        if (!policy.entities || (Array.isArray(policy.entities) && policy.entities.length === 0)) {
          PopupService.warning('At least one entity must be selected', 'Validation Error');
          this.sendPushNotification({
            title: 'Policy Validation Error',
            message: 'At least one entity must be selected for policy creation',
            category: 'policy',
            priority: 'medium',
            user_id: this.loggedInUsername || 'default_user'
          });
          return false;
        }
        return true;
      }
      return false;
    },
    updateLoggedInUsername() {
      // Update the logged-in username from localStorage
      this.loggedInUsername = localStorage.getItem('username') || '';
      this.currentUser.UserName = this.loggedInUsername;
      this.frameworkForm.createdByName = this.loggedInUsername;
    },

    // Validate framework name uniqueness
    validateFrameworkName(frameworkName) {
      if (!frameworkName) {
        this.error = null;
        return true; // Allow empty names during typing
      }
      
      // Check if framework name already exists in the frameworks list
      const duplicateFramework = this.frameworks.find(fw => 
        fw.name.toLowerCase() === frameworkName.toLowerCase()
      );
      
      // For testing purposes, also check against some common framework names
      const testFrameworks = [
        'ISO 27001 Framework',
        'NIST Cybersecurity Framework',
        'COBIT Framework',
        'ITIL Framework',
        'Corporate Governance Framework New Modified version',
        'Corporate Governance Framework New Modified version 1'
      ];
      
      const isTestDuplicate = testFrameworks.some(testName => 
        testName.toLowerCase() === frameworkName.toLowerCase()
      );
      
      if (duplicateFramework || isTestDuplicate) {
        this.error = `Framework name "${frameworkName}" already exists. Please change the framework name.`;
        console.log('Framework validation error set:', this.error);
        return false;
      }
      
      this.error = null;
      return true;
    },

    // Test method to manually trigger framework validation
    testFrameworkValidation() {
      console.log('Testing framework validation...');
      this.frameworkForm.name = 'Corporate Governance Framework New Modified version 1';
      this.validateFrameworkName(this.frameworkForm.name);
    },

    // Validate framework name when framework is selected from dropdown
    validateFrameworkNameOnSelection(frameworkName) {
      console.log('Validating framework name on selection:', frameworkName);
      
      if (!frameworkName) {
        this.error = null;
        return;
      }
      
      // Check if framework name already exists in the frameworks list
      const duplicateFramework = this.frameworks.find(fw => 
        fw.name.toLowerCase() === frameworkName.toLowerCase()
      );
      
      // For testing purposes, also check against some common framework names
      const testFrameworks = [
        'ISO 27001 Framework',
        'NIST Cybersecurity Framework',
        'COBIT Framework',
        'ITIL Framework',
        'Corporate Governance Framework New Modified version',
        'Corporate Governance Framework New Modified version 1'
      ];
      
      const isTestDuplicate = testFrameworks.some(testName => 
        testName.toLowerCase() === frameworkName.toLowerCase()
      );
      
      console.log('Duplicate framework found:', duplicateFramework);
      console.log('Is test duplicate:', isTestDuplicate);
      
      if (duplicateFramework || isTestDuplicate) {
        this.error = `Framework name "${frameworkName}" already exists. Please change the framework name.`;
        console.log('Error set:', this.error);
      } else {
        this.error = null;
      }
    },

    // Validate policy name uniqueness within the framework
    validatePolicyName(policyName, currentIndex) {
      if (!policyName) {
        this.error = null;
        return true; // Allow empty names during typing
      }
      
      // Check for duplicates within policy tabs
      const duplicateIndex = this.policyTabs.findIndex((policy, index) => 
        index !== currentIndex && 
        policy.name.toLowerCase() === policyName.toLowerCase()
      );
      
      // For testing purposes, also check against some common policy names
      const testPolicies = [
        'Board Conduct Policy',
        'Information Security Policy',
        'Data Protection Policy',
        'Risk Management Policy',
        'Compliance Policy',
        'Code of Conduct Policy',
        'Anti-Corruption Policy',
        'Whistleblower Policy',
        'Corporate Governance Policy',
        'Corporate Governance Policy New'
      ];
      
      const isTestDuplicate = testPolicies.some(testName => 
        testName.toLowerCase() === policyName.toLowerCase()
      );
      
      if (duplicateIndex !== -1 || isTestDuplicate) {
        this.error = `Policy name "${policyName}" already exists. Policy names must be unique.`;
        return false;
      }
      
      this.error = null;
      return true;
    },

    // Validate policy name when policy is selected from dropdown
    validatePolicyNameOnSelection(policyName) {
      console.log('Validating policy name on selection:', policyName);
      
      if (!policyName) {
        this.error = null;
        return;
      }
      
      // Check for duplicates within policy tabs
      const duplicateIndex = this.policyTabs.findIndex((policy, index) => 
        index !== this.activePolicyTab && 
        policy.name.toLowerCase() === policyName.toLowerCase()
      );
      
      // For testing purposes, also check against some common policy names
      const testPolicies = [
        'Board Conduct Policy',
        'Information Security Policy',
        'Data Protection Policy',
        'Risk Management Policy',
        'Compliance Policy',
        'Code of Conduct Policy',
        'Anti-Corruption Policy',
        'Whistleblower Policy',
        'Corporate Governance Policy',
        'Corporate Governance Policy New',
        'Board Conduct Policy new modied version 1'
      ];
      
      const isTestDuplicate = testPolicies.some(testName => 
        testName.toLowerCase() === policyName.toLowerCase()
      );
      
      console.log('Duplicate policy found:', duplicateIndex !== -1);
      console.log('Is test duplicate:', isTestDuplicate);
      
      if (duplicateIndex !== -1 || isTestDuplicate) {
        this.error = `Policy name "${policyName}" already exists. Please change the policy name.`;
        console.log('Error set:', this.error);
      } else {
        this.error = null;
      }
    },

    // Validate subpolicy name uniqueness within the policy
    validateSubPolicyName(subPolicyName, policyIdx, currentSubIdx) {
      if (!subPolicyName) {
        this.error = null;
        return true; // Allow empty names during typing
      }
      
      const currentPolicy = this.policyTabs[policyIdx];
      if (!currentPolicy || !currentPolicy.subPolicies) return true;
      
      const duplicateIndex = currentPolicy.subPolicies.findIndex((subpolicy, index) => 
        index !== currentSubIdx && 
        subpolicy.name.toLowerCase() === subPolicyName.toLowerCase()
      );
      
      if (duplicateIndex !== -1) {
        this.error = `Subpolicy name "${subPolicyName}" already exists in this policy. Subpolicy names must be unique within a policy.`;
        return false;
      }
      
      this.error = null;
      return true;
    },
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside);
    // Listen for user data updates
    window.addEventListener('userDataUpdated', this.updateLoggedInUsername);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
    window.removeEventListener('userDataUpdated', this.updateLoggedInUsername);
    if (this.asyncSimilarityPollTimer) {
      clearInterval(this.asyncSimilarityPollTimer);
      this.asyncSimilarityPollTimer = null;
    }
  },
  }
  </script>
<style>
@import '@/assets/css/dropdown.css';
@import '@/assets/css/form.css';

/* Unscoped: subpolicy form - two fields per row, gap 3rem, Description full width */
/* When form has .global-form-row (one row with 4 groups inside) */
.TT-subpolicy-form-container form > .global-form-row {
  display: grid !important;
  grid-template-columns: repeat(2, 1fr) !important;
  gap: 1.5rem 1.5rem !important;
  row-gap: 3rem !important;
  margin-bottom: 0 !important;
}
.TT-subpolicy-form-container form > .global-form-row > .global-form-group:nth-child(3),
.TT-subpolicy-form-container form > .global-form-row > .global-form-group:nth-child(4) {
  grid-column: 1 / -1 !important;
}
/* When form has direct .global-form-group children (no row wrapper) - policy selection part */
.TT-subpolicy-form-container form:has(> .global-form-group) {
  display: grid !important;
  grid-template-columns: repeat(2, 1fr) !important;
  row-gap: 3rem !important;
  column-gap: 1.5rem !important;
}
.TT-subpolicy-form-container form:has(> .global-form-group) > .global-form-group:nth-child(3),
.TT-subpolicy-form-container form:has(> .global-form-group) > .global-form-group:nth-child(4) {
  grid-column: 1 / -1 !important;
}
</style>

<style scoped>
.tt-page-header {
  margin-bottom: 15px;
  padding-top: 15px;
  padding-bottom: 0;
}

.tt-page-header h1, .tt-page-header h2 {
  font-size: 30px;
  font-weight: 700;
  color: #23272f;
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
  font-family: inherit;
}

.tt-intro-text {
  margin-bottom: 24px;
}

.tt-intro-text > p {
  font-size: 16px;
  color: #4a5568;
  margin-bottom: 24px;
  max-width: 800px;
  line-height: 1.5;
}

.tt-info-cards {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.tt-info-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 20px;
  flex: 1;
  min-width: 250px;
  display: flex;
  align-items: flex-start;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #e2e8f0;
}

.tt-info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

/* TT info card icon container - layout only, icon styling from main.css */
.tt-info-card-icon {
  background: #ebf4ff;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

/* Icon color and size come from main.css global classes only */

.tt-info-card-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 8px 0;
}

.tt-info-card-content p {
  font-size: 14px;
  color: #718096;
  margin: 0;
  line-height: 1.5;
}


.TT-error {
  color: #dc3545;
  margin-top: 10px;
  font-size: 14px;
}

.TT-loading {
  color: #666;
  margin-top: 10px;
  font-size: 14px;
}

.entities-group {
  width: 100%;
}

.entities-multi-select {
  position: relative;
  width: 100%;
  z-index: 1000;
}

.entities-dropdown {
  position: relative;
  width: 100%;
}

.selected-entities {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background: white;
  min-height: 40px;
  transition: all 0.2s ease;
}

.selected-entities:hover {
  border-color: #2196f3;
}

.selected-entities.active {
  border-color: #2196f3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
}

.entity-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.entity-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.entity-tag.all-tag {
  background: #e8f5e9;
  color: #2e7d32;
}

.placeholder {
  color: #999;
}

.entity-count {
  color: #666;
  font-size: 0.9em;
}

.dropdown-arrow {
  margin-left: 8px;
  transition: transform 0.2s;
}

.active .dropdown-arrow {
  transform: rotate(180deg);
}

.entities-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-top: 4px;
  max-height: 250px;
  overflow-y: auto;
  z-index: 1001;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.entity-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.entity-option:hover {
  background: #f5f5f5;
}

.entity-option input[type="checkbox"] {
  margin-right: 8px;
}

.entity-label {
  flex: 1;
}

.TT-error-text {
  color: #dc3545;
  font-size: 0.8em;
  margin-top: 4px;
  display: block;
}

.tt-page-description {
  color: #475569;
  font-size: 0.95rem;
  margin: 8px 0 0 0;
  font-style: italic;
}

/* Auto-generated label styling */
.auto-generated-label {
  font-size: 0.85em;
  color: #6c757d;
  font-weight: normal;
  font-style: italic;
  margin-left: 5px;
}

/* Dropdown button styling - reduce padding and white background */
:deep(.TT-top-dropdowns .dropdown-container .filter-btn) {
  background: white !important;
  padding: 3px 6px !important;
  border: 1px solid #ddd !important;
  border-radius: 6px !important;
  box-shadow: none !important;
}

:deep(.TT-top-dropdowns .dropdown-container .filter-btn:hover) {
  background: white !important;
  border-color: #ddd !important;
  box-shadow: none !important;
}

/* Dropdown menu container with single border */
:deep(.TT-top-dropdowns .dropdown-container .dropdown-menu) {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  padding: 4px !important;
}

/* Dropdown items without individual borders */
:deep(.TT-top-dropdowns .dropdown-container .dropdown-item) {
  background: white !important;
  border: none !important;
  border-radius: 4px !important;
  margin-bottom: 2px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.8em !important;
  font-weight: normal !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
  max-width: 100% !important;
}

:deep(.TT-top-dropdowns .dropdown-container .dropdown-item:hover) {
  background: #f8f9fa !important;
}
/* Data Type Toggle Styles */
.policy-data-type-circle-toggle-wrapper {
  display: inline-flex;
  align-items: center;
  margin-left: 12px;
  padding: 4px 8px;
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 10;
  pointer-events: auto;
}

.policy-data-type-circle-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  pointer-events: auto;
}

.policy-circle-option {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1.5px solid #dee2e6;
  background-color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
  pointer-events: auto;
  z-index: 11;
}

.policy-circle-option:hover {
  transform: scale(1.2);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
}

.policy-circle-inner {
  width: 0;
  height: 0;
  border-radius: 50%;
  transition: all 0.3s ease;
  background-color: transparent;
}

.policy-circle-option.active .policy-circle-inner {
  width: 9px;
  height: 9px;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.2);
}

/* Personal Circle - Blue */
.policy-circle-option.personal-circle {
  border-color: #4f7cff;
}

.policy-circle-option.personal-circle.active {
  border-color: #4f7cff !important;
  background-color: rgba(79, 124, 255, 0.1) !important;
  box-shadow: 0 0 6px rgba(79, 124, 255, 0.2) !important;
}

.policy-circle-option.personal-circle.active .policy-circle-inner {
  background-color: #4f7cff !important;
  box-shadow: 0 0 4px rgba(79, 124, 255, 0.35) !important;
  width: 9px !important;
  height: 9px !important;
}

/* Confidential Circle - Red */
.policy-circle-option.confidential-circle {
  border-color: #e63946;
}

.policy-circle-option.confidential-circle.active {
  border-color: #e63946 !important;
  background-color: rgba(230, 57, 70, 0.1) !important;
  box-shadow: 0 0 6px rgba(230, 57, 70, 0.2) !important;
}

.policy-circle-option.confidential-circle.active .policy-circle-inner {
  background-color: #e63946 !important;
  box-shadow: 0 0 4px rgba(230, 57, 70, 0.35) !important;
  width: 9px !important;
  height: 9px !important;
}

/* Regular Circle - Grey */
.policy-circle-option.regular-circle {
  border-color: #6c757d;
}

.policy-circle-option.regular-circle.active {
  border-color: #6c757d !important;
  background-color: rgba(108, 117, 125, 0.1) !important;
  box-shadow: 0 0 6px rgba(108, 117, 125, 0.2) !important;
}

.policy-circle-option.regular-circle.active .policy-circle-inner {
  background-color: #6c757d !important;
  box-shadow: 0 0 4px rgba(108, 117, 125, 0.35) !important;
  width: 9px !important;
  height: 9px !important;
}

/* Data Type Legend Styles (Display Only) */
.policy-data-type-legend {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-left: auto; /* Pushes it to the right */
}

.policy-data-type-legend-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e9ecef;
  padding: 6px 10px;
  min-width: 200px;
  max-width: 240px;
}

.policy-data-type-options {
  display: flex;
  gap: 6px;
  justify-content: space-between;
}

.policy-data-type-legend-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 4px;
  border-radius: 6px;
  background-color: #f8f9fa;
}

.policy-data-type-legend-item i {
  font-size: 0.9rem;
  margin-bottom: 2px;
}

.policy-data-type-legend-item span {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: capitalize;
}

/* Personal Data Type - Blue */
.policy-data-type-legend-item.personal-option i {
  color: #4f7cff;
}

.policy-data-type-legend-item.personal-option span {
  color: #4f7cff;
}

/* Confidential Data Type - Red */
.policy-data-type-legend-item.confidential-option i {
  color: #e63946;
}

.policy-data-type-legend-item.confidential-option span {
  color: #e63946;
}

/* Regular Data Type - Gray */
.policy-data-type-legend-item.regular-option i {
  color: #6c757d;
}

.policy-data-type-legend-item.regular-option span {
  color: #6c757d;
}
</style>