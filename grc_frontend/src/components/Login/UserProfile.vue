<template>
  <div class="user-profile-container">
    <div v-if="!loading" class="tabs">
      <button
        v-for="tab in visibleTabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <i :class="tab.icon" class="tab-icon"></i>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading user profile...</p>
    </div>
    <div v-else class="tab-content">
      <div v-if="activeTab === 'account'" class="account-section">
          <!-- Error/Success Messages -->
          <div v-if="error" class="message error-message">
            <i class="fas fa-exclamation-circle"></i> {{ error }}
          </div>
          <div v-if="success" class="message success-message">
            <i class="fas fa-check-circle"></i> {{ success }}
          </div>
          
        <!-- Account Info Type Selector -->
        <div class="account-type-selector">
          <button 
            :class="['selector-btn', { active: accountInfoType === 'personal' }]" 
            @click="accountInfoType = 'personal'"
          >
            <i class="fas fa-user"></i> Personal Information
          </button>
          <button 
            :class="['selector-btn', { active: accountInfoType === 'business' }]" 
            @click="accountInfoType = 'business'"
          >
            <i class="fas fa-building"></i> Business Information
          </button>
        </div>
          
        <div class="account-container">
          <!-- Personal Information Section -->
          <div v-if="accountInfoType === 'personal'" class="account-section-content">
            <form class="profile-form" @submit.prevent="savePersonalInfo">
              <div class="section-header-with-edit">
                <div>
                  <h2 class="section-title"><i class="fas fa-user"></i> Personal Information</h2>
                  <p class="section-helper">Update your personal details and contact information.</p>
                </div>
                <div class="header-actions" style="display: flex; align-items: center; gap: 10px;">
                <button
                  v-if="!editModePersonal"
                  type="button"
                  class="edit-btn"
                  @click="enableEditMode('personal')"
                >
                  <i class="fas fa-edit"></i> Edit
                </button>
                  <div v-if="!editModePersonal" class="format-selector" style="position: relative;">
                    <button
                      type="button"
                      class="format-select-btn"
                      @click="showFormatDropdown = !showFormatDropdown"
                      style="padding: 8px 16px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer; display: flex; align-items: center; gap: 8px;"
                    >
                      <span>{{ selectedExportFormat.toUpperCase() || 'Select format' }}</span>
                      <i class="fas fa-chevron-down"></i>
                    </button>
                    <div
                      v-if="showFormatDropdown"
                      class="format-dropdown"
                      style="position: absolute; top: 100%; left: 0; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 1000; min-width: 180px; margin-top: 4px;"
                    >
                      <div
                        v-for="format in exportFormats"
                        :key="format.value"
                        @click="selectExportFormat(format.value)"
                        style="padding: 10px 16px; cursor: pointer; border-bottom: 1px solid #f0f0f0;"
                        :style="{ backgroundColor: selectedExportFormat === format.value ? '#f0f7ff' : 'white' }"
                        @mouseover="$event.target.style.backgroundColor = '#f5f5f5'"
                        @mouseleave="$event.target.style.backgroundColor = selectedExportFormat === format.value ? '#f0f7ff' : 'white'"
                      >
                        {{ format.label }}
                      </div>
                    </div>
                  </div>
                  <button
                    v-if="!editModePersonal"
                    type="button"
                    class="export-btn"
                    @click="initiatePortabilityExport"
                    :disabled="exportingData || !selectedExportFormat"
                    style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 8px;"
                  >
                    <i v-if="exportingData" class="fas fa-spinner fa-spin"></i>
                    <i v-else class="fas fa-download"></i>
                    {{ exportingData ? 'Exporting...' : 'Export' }}
                  </button>
                <div v-else class="edit-actions">
                  <button
                    type="button"
                    class="cancel-edit-btn"
                    @click="cancelEditMode('personal')"
                  >
                    <i class="fas fa-times"></i> Cancel
                  </button>
                  <button
                    type="button"
                    class="save-edits-btn"
                    @click="openRectificationModal('personal')"
                    :disabled="!hasPersonalChanges"
                  >
                    <i class="fas fa-save"></i> Save Edits
                  </button>
                  </div>
                </div>
              </div>
             
              <div class="form-row">
                <div class="form-group">
                  <label>First Name:</label>
                  <input 
                    type="text" 
                    :value="editModePersonal ? form.firstName : maskedData.firstName"
                    @input="updatePersonalField('firstName', $event.target.value)"
                    :disabled="!editModePersonal || loading" 
                  />
                </div>
                <div class="form-group">
                  <label>Last Name:</label>
                  <input 
                    type="text" 
                    :value="editModePersonal ? form.lastName : maskedData.lastName"
                    @input="updatePersonalField('lastName', $event.target.value)"
                    :disabled="!editModePersonal || loading" 
                  />
                </div>
              </div>
             
              <div class="form-row">
                <div class="form-group">
                  <label>Email:</label>
                  <input 
                    type="email" 
                    :value="editModePersonal ? form.email : maskedData.email"
                    @input="updatePersonalField('email', $event.target.value)"
                    :disabled="!editModePersonal || loading" 
                  />
                </div>
                <div class="form-group">
                  <label>Phone Number:</label>
                  <input 
                    type="text" 
                    :value="editModePersonal ? form.phone : maskedData.phone"
                    @input="updatePersonalField('phone', $event.target.value)"
                    :disabled="!editModePersonal || loading" 
                  />
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group full-width">
                  <label>Address:</label>
                  <textarea 
                    :value="editModePersonal ? form.address : maskedData.address"
                    @input="updatePersonalField('address', $event.target.value)"
                    :disabled="!editModePersonal || loading" 
                    rows="3"
                  ></textarea>
                </div>
              </div>
             
              <div v-if="!editModePersonal" class="form-row center">
                <button class="submit-btn" type="submit" :disabled="loading">
                  <i v-if="loading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-save"></i>
                  {{ loading ? 'Saving...' : 'Save Personal Info' }}
                </button>
              </div>
            </form>
          </div>
 
          <!-- Business Information Section -->
          <div v-if="accountInfoType === 'business'" class="account-section-content">
            <form class="profile-form" @submit.prevent="saveBusinessInfo">
              <div class="section-header-with-edit">
                <div>
                  <h2 class="section-title"><i class="fas fa-building"></i> Business Information</h2>
                  <p class="section-helper">View your organizational details and business unit information.</p>
                </div>
                <button
                  v-if="!editModeBusiness"
                  type="button"
                  class="edit-btn"
                  @click="enableEditMode('business')"
                >
                  <i class="fas fa-edit"></i> Edit
                </button>
                <div v-else class="edit-actions">
                  <button
                    type="button"
                    class="cancel-edit-btn"
                    @click="cancelEditMode('business')"
                  >
                    <i class="fas fa-times"></i> Cancel
                  </button>
                  <button
                    type="button"
                    class="save-edits-btn"
                    @click="openRectificationModal('business')"
                    :disabled="!hasBusinessChanges"
                  >
                    <i class="fas fa-save"></i> Save Edits
                  </button>
                </div>
              </div>
             
              <div class="form-row">
                <div class="form-group">
                  <label>Department:</label>
                  <input type="text" v-model="businessInfo.departmentName" :disabled="!editModeBusiness || loading" />
                </div>
                <div class="form-group">
                  <label>Business Unit:</label>
                  <input type="text" v-model="businessInfo.businessUnitDisplay" :disabled="!editModeBusiness || loading" />
                </div>
              </div>
             
              <div class="form-row">
                <div class="form-group">
                  <label>Entity:</label>
                  <input type="text" v-model="businessInfo.entityDisplay" :disabled="!editModeBusiness || loading" />
                </div>
                <div class="form-group">
                  <label>Location:</label>
                  <input type="text" v-model="businessInfo.location" :disabled="!editModeBusiness || loading" />
                </div>
              </div>
             
              <div class="form-group">
                <label>Department Head:</label>
                <input type="text" v-model="businessInfo.departmentHead" :disabled="!editModeBusiness || loading" />
              </div>
             
              <!-- User Role and Permissions Section -->
              <div class="permissions-section">
                <h3 class="section-subtitle"><i class="fas fa-user-shield"></i> Role & Permissions</h3>
                <div v-if="userPermissions.role" class="user-role">
                  <span class="role-badge">{{ userPermissions.role }}</span>
                </div>
               
                <div v-if="!userPermissions.modules || Object.keys(userPermissions.modules).length === 0" class="no-permissions">
                  <p>No permissions assigned.</p>
                </div>
               
                <div v-else class="permissions-container">
                  <div
                    v-for="(module, moduleName) in userPermissions.modules"
                    :key="moduleName"
                    class="permission-module"
                  >
                    <div class="module-header" @click="toggleModulePermissions(moduleName)">
                      <span class="module-name">
                        <i :class="getModuleIcon(moduleName)"></i>
                        {{ formatModuleName(moduleName) }}
                      </span>
                      <i :class="expandedModules.includes(moduleName) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                    </div>
                    <transition name="fade">
                      <div v-if="expandedModules.includes(moduleName)" class="module-permissions">
                        <div v-for="(value, permission) in module" :key="permission" class="permission-item">
                          <span class="permission-name">{{ formatPermissionName(permission) }}</span>
                          <span :class="['permission-value', value ? 'allowed' : 'denied']">
                            <i :class="value ? 'fas fa-check' : 'fas fa-times'"></i>
                          </span>
                        </div>
                      </div>
                    </transition>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
 
      <div v-else-if="activeTab === 'role'">
        <form class="profile-form">
          <h2 class="section-title"><i class="fas fa-exchange-alt"></i> Role Management</h2>
          <p class="section-helper">View or request changes to your user role. Role changes may require approval from an administrator.</p>
          <div class="form-row">
            <label>User Name:</label>
            <input type="text" v-model="form.username" />
            <label>Role:</label>
            <input type="text" v-model="form.role" />
          </div>
          <div class="form-row center">
            <button class="submit-btn" type="button">
              <i class="fas fa-check"></i> Request Role Change
            </button>
          </div>
        </form>
      </div>
      <div v-else-if="activeTab === 'password'">
        <div class="password-section">
          <h2 class="section-title"><i class="fas fa-key"></i>Password Management</h2>
          <p class="section-helper">Manage your password settings. You can update your password or reset it using the forgot password flow.</p>
          
          <!-- Reset Password Button -->
          <div class="reset-password-section">
            <div class="reset-password-card">
              <div class="reset-password-content">
                <div class="reset-password-icon">
                  <i class="fas fa-lock"></i>
                </div>
                <div class="reset-password-info">
                  <h3>Reset Password</h3>
                  <p>Use the forgot password flow to reset your password. You'll receive an OTP via email to verify your identity.</p>
                </div>
                <button 
                  class="reset-password-btn" 
                  @click="showForgotPasswordModal = true"
                  type="button"
                >
                  <i class="fas fa-key"></i>
                  Reset Password
                </button>
              </div>
            </div>
          </div>
          
          <!-- Divider -->
          <div class="password-divider">
            <span>OR</span>
          </div>
          
          <!-- Update Password Form -->
          <form class="profile-form password-form" @submit.prevent="updatePassword">
            <h3 class="section-subtitle"><i class="fas fa-edit"></i>Update Password</h3>
            <p class="section-helper">For your security, please enter your email and a new password. You will need to verify with an OTP sent to your registered email or phone.</p>
            
            <!-- Error/Success Messages -->
            <div v-if="error" class="message error-message">
              <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            <div v-if="success" class="message success-message">
              <i class="fas fa-check-circle"></i> {{ success }}
            </div>
            
            <div class="form-group email-with-verify">
              <label>Email</label>
              <div class="email-verify-wrapper">
                <input type="email" v-model="form.email" placeholder="Enter your email address" :disabled="loading" class="email-input" />
                <button class="verify-btn" type="button" :disabled="loading">
                  <i class="fas fa-shield-alt"></i> Verify
                </button>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>Enter OTP</label>
                <input type="text" v-model="form.otp" placeholder="Enter OTP" :disabled="loading" />
              </div>
              <div class="form-group">
                <label>New Password</label>
                <input type="password" v-model="form.newPassword" placeholder="Enter new password" :disabled="loading" />
              </div>
            </div>
            
            <div class="form-group">
              <label>Confirm Password</label>
              <input type="password" v-model="form.confirmPassword" placeholder="Re-enter new password" :disabled="loading" />
            </div>
            <div class="form-row password-submit-row">
              <button class="submit-btn" type="submit" style="width: 100%; max-width: 320px;" :disabled="loading">
                <i v-if="loading" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-paper-plane"></i> 
                {{ loading ? 'Updating...' : 'Update Password' }}
              </button>
            </div>
          </form>
        </div>
      </div>
      <div v-else-if="activeTab === 'notification'">
        <div class="notification-settings">
          <h2 class="section-title"><i class="fas fa-bell"></i> Notification Preferences</h2>
          <p class="section-helper">Manage how you receive notifications and update your contact details for alerts.</p>

          <!-- Email Notification Dropdown -->
          <div class="notif-dropdown-section">
            <div class="notification-row notif-dropdown-toggle" @click="notifDropdownOpen = notifDropdownOpen === 'email' ? null : 'email'">
              <span style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-envelope"></i> Email Notification updates
              </span>
              <label class="switch" @click.stop>
                <input type="checkbox" v-model="form.emailNotif" />
                <span class="slider"></span>
              </label>
              <span class="notif-dropdown-arrow">
                <i :class="notifDropdownOpen === 'email' ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
              </span>
            </div>
            <transition name="fade">
              <div v-if="notifDropdownOpen === 'email'" class="notif-dropdown-content">
                <form class="notif-change-form" @submit.prevent>
                  <div class="notif-form-row">
                    <label>Email</label>
                    <input type="email" v-model="form.notifEmail" placeholder="Enter new notification email" />
                  </div>
                  <div class="notif-form-row center">
                    <button class="submit-btn" type="submit" style="width: 100%; max-width: 320px;">
                      <i class="fas fa-save"></i> Save 
                    </button>
                  </div>
                </form>
              </div>
            </transition>
          </div>

          <!-- WhatsApp Notification Dropdown -->
          <div class="notif-dropdown-section">
            <div class="notification-row notif-dropdown-toggle" @click="notifDropdownOpen = notifDropdownOpen === 'whatsapp' ? null : 'whatsapp'">
              <span style="display: flex; align-items: center; gap: 10px;">
                <i class="fab fa-whatsapp"></i> WhatsApp Notification updates
              </span>
              <label class="switch" @click.stop>
                <input type="checkbox" v-model="form.whatsappNotif" />
                <span class="slider"></span>
              </label>
              <span class="notif-dropdown-arrow">
                <i :class="notifDropdownOpen === 'whatsapp' ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
              </span>
            </div>
            <transition name="fade">
              <div v-if="notifDropdownOpen === 'whatsapp'" class="notif-dropdown-content">
                <form class="notif-change-form" @submit.prevent>
                  <div class="notif-form-row">
                    <label>Mobile Number</label>
                    <input type="text" v-model="form.notifMobile" placeholder="Enter new WhatsApp number" />
                  </div>
                  <div class="notif-form-row center">
                    <button class="submit-btn" type="submit" style="width: 100%; max-width: 320px;">
                      <i class="fas fa-save"></i> Save 
                    </button>
                  </div>
                </form>
              </div>
            </transition>
          </div>
        </div>
      </div>
      <div v-else-if="activeTab === 'user-management'">
        <div class="user-management-section">
          <div class="user-management-header">
            <div class="header-content">
              <h2 class="section-title">
                <i class="fas fa-users"></i> 
                User Management
              </h2>
              <p class="section-helper">
                Create and manage user accounts. Only GRC Administrators can access this section.
              </p>
            </div>
          </div>
          
          <div class="user-management-actions">
            <button 
              @click="toggleCreateUserForm" 
              class="create-user-btn"
              :disabled="!isGRCAdministrator"
            >
              <i class="fas fa-user-plus"></i>
              {{ showCreateUserForm ? 'Cancel' : 'Create New User' }}
            </button>
            <button 
              @click="toggleManageUsersForm" 
              class="manage-users-btn"
              :disabled="!isGRCAdministrator"
            >
              <i class="fas fa-user-cog"></i>
              {{ showManageUsersForm ? 'Cancel' : 'Manage Users' }}
            </button>
            <button 
              @click="toggleAllUsersList" 
              class="all-users-btn"
              :disabled="!isGRCAdministrator"
            >
              <i class="fas fa-list"></i>
              {{ showAllUsersList ? 'Hide Users' : 'View All Users' }}
            </button>
          </div>
          
          <!-- Create User Form - Integrated directly below button -->
          <transition name="slide-down">
            <div v-if="showCreateUserForm && isGRCAdministrator" class="create-user-form-container">
              <div class="form-header">
                <h3 class="form-title">
                  <i class="fas fa-user-plus"></i>
                  Create New User Account
                </h3>
                <p class="form-description">
                  Fill in the required information to create a new user account. Password will be auto-generated in the format: Riskavaire@&lt;FirstName&gt;&lt;number&gt; and sent via email.
                </p>
              </div>
              
              <form @submit.prevent="createUser" class="profile-form create-user-form">
                <div class="form-grid">
                  <div class="form-group">
                    <label for="username">Username *</label>
                    <input 
                      type="text" 
                      id="username" 
                      v-model="createUserForm.username" 
                      placeholder="Enter username"
                      required
                      :disabled="createUserLoading"
                    />
                  </div>
                  
                  <!-- Password is auto-generated, no field needed -->
                  
                  <div class="form-group">
                    <label for="email">Email *</label>
                    <input 
                      type="email" 
                      id="email" 
                      v-model="createUserForm.email" 
                      placeholder="Enter email address"
                      required
                      :disabled="createUserLoading"
                    />
                  </div>
                  
                  <div class="form-group">
                    <label for="firstName">First Name *</label>
                    <input 
                      type="text" 
                      id="firstName" 
                      v-model="createUserForm.firstName" 
                      placeholder="Enter first name"
                      required
                      :disabled="createUserLoading"
                    />
                  </div>
                  
                  <div class="form-group">
                    <label for="lastName">Last Name *</label>
                    <input 
                      type="text" 
                      id="lastName" 
                      v-model="createUserForm.lastName" 
                      placeholder="Enter last name"
                      required
                      :disabled="createUserLoading"
                    />
                  </div>
                  
                  <div class="form-group">
                    <label for="department">Department *</label>
                    <select 
                      id="department" 
                      v-model="createUserForm.departmentId" 
                      required
                      :disabled="createUserLoading"
                    >
                      <option value="">Select a department</option>
                      <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                        {{ dept.name }}
                      </option>
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label for="phoneNumber">Phone Number *</label>
                    <input 
                      type="tel" 
                      id="phoneNumber" 
                      v-model="createUserForm.phoneNumber" 
                      placeholder="Enter phone number"
                      required
                      :disabled="createUserLoading"
                    />
                  </div>
                  
                  <div class="form-group">
                    <label for="address">Address *</label>
                    <textarea 
                      id="address" 
                      v-model="createUserForm.address" 
                      placeholder="Enter address"
                      required
                      :disabled="createUserLoading"
                      rows="3"
                    ></textarea>
                  </div>
                  
                  <div class="form-group">
                    <label for="role">Role *</label>
                    <select 
                      id="role" 
                      v-model="createUserForm.role" 
                      required
                      :disabled="createUserLoading"
                      @change="onRoleChange"
                    >
                      <option value="">Select a role</option>
                      <option v-for="role in availableRoles" :key="role" :value="role">
                        {{ role }}
                      </option>
                      <option value="__custom__">+ Add New Role</option>
                    </select>
                    <input 
                      v-if="showCustomRoleInput"
                      type="text" 
                      v-model="customRole"
                      placeholder="Enter new role name"
                      class="custom-role-input"
                      @keyup.enter="addCustomRole"
                      @blur="addCustomRole"
                    />
                  </div>
                  
                  <!-- <div class="form-group">
                    <label for="isActive">Status</label>
                    <select 
                      id="isActive" 
                      v-model="createUserForm.isActive" 
                      :disabled="createUserLoading"
                    >
                      <option value="Y">Active</option>
                      <option value="N">Inactive</option>
                    </select>
                  </div> -->
                </div>
                
                <!-- Permissions Section -->
                <div v-if="createUserForm.role && createUserForm.role !== '__custom__'" class="permissions-section">
                  <h3 class="section-subtitle">
                    <i class="fas fa-user-shield"></i> 
                    Permissions for {{ createUserForm.role }}
                  </h3>
                  
                  <!-- Global Select All -->
                  <div class="global-select-all">
                    <label class="select-all-item">
                      <input 
                        type="checkbox" 
                        v-model="selectAllPermissions"
                        @change="toggleAllPermissions"
                        :disabled="createUserLoading"
                      />
                      <span class="select-all-label">
                        <i class="fas fa-check-circle"></i>
                        Select All Permissions
                      </span>
                    </label>
                  </div>
                  
                  <div class="permissions-grid">
                    <div v-for="module in rbacModules" :key="module.name" class="permission-module">
                      <div class="module-header" @click="toggleModulePermissions(module.name)">
                        <span class="module-name">
                          <i :class="getModuleIcon(module.name)"></i>
                          {{ module.displayName }}
                        </span>
                        <div class="module-controls">
                          <label class="module-select-all">
                            <input 
                              type="checkbox" 
                              v-model="moduleSelectAll[module.name]"
                              @change="toggleModulePermissions(module.name)"
                              :disabled="createUserLoading"
                              @click.stop
                            />
                            <span class="module-select-all-label">Select All</span>
                          </label>
                          <i :class="expandedModules.includes(module.name) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                        </div>
                      </div>
                      <transition name="fade">
                        <div v-if="expandedModules.includes(module.name)" class="module-permissions">
                          <div v-for="permission in module.permissions" :key="permission.field" class="permission-item">
                            <label class="permission-checkbox">
                              <input 
                                type="checkbox" 
                                v-model="selectedPermissions[permission.field]"
                                @change="updateModuleSelectAll(module.name)"
                                :disabled="createUserLoading"
                              />
                              <span class="permission-name">{{ permission.label }}</span>
                            </label>
                          </div>
                        </div>
                      </transition>
                    </div>
                  </div>
                </div>
                
                <!-- Form Actions -->
                <div class="form-actions">
                  <button 
                    type="submit" 
                    class="submit-btn" 
                    :disabled="createUserLoading || !isCreateUserFormValid"
                  >
                    <i v-if="createUserLoading" class="fas fa-spinner fa-spin"></i>
                    <i v-else class="fas fa-user-plus"></i>
                    {{ createUserLoading ? 'Creating User...' : 'Create User' }}
                  </button>
                  
                  <button 
                    type="button" 
                    class="cancel-btn" 
                    @click="cancelCreateUser"
                    :disabled="createUserLoading"
                  >
                    <i class="fas fa-times"></i>
                    Cancel
                  </button>
                </div>
                
                <!-- Messages -->
                <div v-if="createUserError" class="message error-message">
                  <i class="fas fa-exclamation-circle"></i> {{ createUserError }}
                </div>
                <div v-if="createUserSuccess" class="message success-message">
                  <i class="fas fa-check-circle"></i> {{ createUserSuccess }}
                </div>
              </form>
            </div>
          </transition>
          
          <!-- Manage Users Form -->
          <transition name="slide-down">
            <div v-if="showManageUsersForm && isGRCAdministrator" class="manage-users-form-container">
              <div class="form-header">
                <h3 class="form-title">
                  <i class="fas fa-user-cog"></i>
                  Manage User Permissions
                </h3>
                <p class="form-description">
                  Select a user to view and edit their permissions.
                </p>
              </div>
              
              <div class="manage-users-content">
                <!-- User Selection Dropdown -->
                <div class="form-group">
                  <label for="selectedUser">Select User *</label>
                  <select 
                    id="selectedUser" 
                    v-model="selectedUserId" 
                    @change="onUserSelected"
                    :disabled="manageUsersLoading"
                    class="user-select-dropdown"
                  >
                    <option value="">-- Select a user --</option>
                    <option v-for="user in usersList" :key="user.UserId" :value="user.UserId">
                      {{ user.UserName }} ({{ user.FirstName }} {{ user.LastName }})
                    </option>
                  </select>
                </div>
                
                <!-- Loading State -->
                <div v-if="manageUsersLoading && selectedUserId" class="loading-permissions">
                  <div class="spinner"></div>
                  <p>Loading user permissions...</p>
                </div>
                
                <!-- Permissions Display -->
                <div v-if="selectedUserId && !manageUsersLoading && selectedUserPermissions" class="permissions-edit-section">
                  <h3 class="section-subtitle">
                    <i class="fas fa-user-shield"></i> 
                    Permissions for {{ selectedUserName }}
                  </h3>
                  
                  <!-- Global Select All -->
                  <div class="global-select-all">
                    <label class="select-all-item">
                      <input 
                        type="checkbox" 
                        v-model="selectAllManagePermissions"
                        @change="toggleAllManagePermissions"
                        :disabled="savingPermissions"
                      />
                      <span class="select-all-label">
                        <i class="fas fa-check-circle"></i>
                        Select All Permissions
                      </span>
                    </label>
                  </div>
                  
                  <div class="permissions-grid">
                    <div v-for="module in rbacModules" :key="module.name" class="permission-module">
                      <div class="module-header" @click="toggleModulePermissions(module.name)">
                        <span class="module-name">
                          <i :class="getModuleIcon(module.name)"></i>
                          {{ module.displayName }}
                        </span>
                        <div class="module-controls">
                          <label class="module-select-all">
                            <input 
                              type="checkbox" 
                              v-model="moduleSelectAllManage[module.name]"
                              @change="toggleModuleManagePermissions(module.name)"
                              :disabled="savingPermissions"
                              @click.stop
                            />
                            <span class="module-select-all-label">Select All</span>
                          </label>
                          <i :class="expandedModules.includes(module.name) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                        </div>
                      </div>
                      <transition name="fade">
                        <div v-if="expandedModules.includes(module.name)" class="module-permissions">
                          <div v-for="permission in module.permissions" :key="permission.field" class="permission-item">
                            <label class="permission-checkbox">
                              <input 
                                type="checkbox" 
                                v-model="selectedUserPermissions[permission.field]"
                                @change="updateModuleSelectAllManage(module.name)"
                                :disabled="savingPermissions"
                              />
                              <span class="permission-name">{{ permission.label }}</span>
                            </label>
                          </div>
                        </div>
                      </transition>
                    </div>
                  </div>
                  
                  <!-- Save Button -->
                  <div class="form-actions">
                    <button 
                      type="button" 
                      class="submit-btn" 
                      @click="saveUserPermissions"
                      :disabled="savingPermissions || !selectedUserId"
                    >
                      <i v-if="savingPermissions" class="fas fa-spinner fa-spin"></i>
                      <i v-else class="fas fa-save"></i>
                      {{ savingPermissions ? 'Saving...' : 'Save Permissions' }}
                    </button>
                    
                    <button 
                      type="button" 
                      class="cancel-btn" 
                      @click="cancelManageUsers"
                      :disabled="savingPermissions"
                    >
                      <i class="fas fa-times"></i>
                      Cancel
                    </button>
                  </div>
                  
                  <!-- Messages -->
                  <div v-if="manageUsersError" class="message error-message">
                    <i class="fas fa-exclamation-circle"></i> {{ manageUsersError }}
                  </div>
                  <div v-if="manageUsersSuccess" class="message success-message">
                    <i class="fas fa-check-circle"></i> {{ manageUsersSuccess }}
                  </div>
                </div>
              </div>
            </div>
          </transition>
          
          <!-- All Users List with Toggle -->
          <transition name="slide-down">
            <div v-if="showAllUsersList && isGRCAdministrator" class="all-users-list-container">
              <div class="form-header">
                <h3 class="form-title">
                  <i class="fas fa-users"></i>
                  All Users - Active/Inactive Status
                </h3>
                <p class="form-description">
                  View and manage user active/inactive status. Toggle the switch to activate or deactivate users.
                </p>
              </div>
              
              <div class="all-users-content">
                <!-- Loading State -->
                <div v-if="loadingAllUsers" class="loading-users">
                  <div class="spinner"></div>
                  <p>Loading users...</p>
                </div>
                
                <!-- Users Table -->
                <div v-else-if="allUsersList.length > 0" class="users-table-container">
                  <table class="users-table">
                    <thead>
                      <tr>
                        <th>User ID</th>
                        <th>Username</th>
                        <th>Full Name</th>
                        <th>Email</th>
                        <th>Department</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="user in allUsersList" :key="user.UserId" :class="{ 'inactive-user': user.IsActive === 'N' || user.IsActive === false }">
                        <td>{{ user.UserId }}</td>
                        <td>{{ user.UserName }}</td>
                        <td>{{ user.FirstName }} {{ user.LastName }}</td>
                        <td>{{ user.Email }}</td>
                        <td>{{ user.DepartmentName || user.DepartmentId || 'N/A' }}</td>
                        <td>
                          <span :class="['status-badge', (user.IsActive === 'Y' || user.IsActive === true) ? 'active' : 'inactive']">
                            {{ (user.IsActive === 'Y' || user.IsActive === true) ? 'Active' : 'Inactive' }}
                          </span>
                        </td>
                        <td>
                          <label class="status-toggle-switch">
                            <input 
                              type="checkbox" 
                              :checked="user.IsActive === 'Y' || user.IsActive === true"
                              @change="toggleUserStatus(user)"
                              :disabled="updatingUserStatus === user.UserId"
                            />
                            <span class="slider"></span>
                          </label>
                          <span v-if="updatingUserStatus === user.UserId" class="updating-indicator">
                            <i class="fas fa-spinner fa-spin"></i>
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                
                <!-- No Users Message -->
                <div v-else class="no-users-message">
                  <i class="fas fa-users"></i>
                  <p>No users found.</p>
                </div>
                
                <!-- Messages -->
                <div v-if="allUsersError" class="message error-message">
                  <i class="fas fa-exclamation-circle"></i> {{ allUsersError }}
                </div>
                <div v-if="allUsersSuccess" class="message success-message">
                  <i class="fas fa-check-circle"></i> {{ allUsersSuccess }}
                </div>
              </div>
            </div>
          </transition>
          
          <div v-if="!isGRCAdministrator" class="access-denied-message">
            <i class="fas fa-lock"></i>
            <p>Access Denied: Only GRC Administrators can manage users.</p>
            <p>Debug Info: User Role = "{{ userPermissions.role }}"</p>
            <p>Debug Info: isGRCAdministrator = {{ isGRCAdministrator }}</p>
            <button @click="forceAdminMode" class="debug-btn">Force Admin Mode (Debug)</button>
            <button @click="setVikramPatel" class="debug-btn">Set Vikram Patel (Debug)</button>
          </div>
        </div>
      </div>
      
      <!-- Consent Management Tab -->
      <div v-else-if="activeTab === 'consent-config'">
        <div class="consent-config-section">
          <!-- Tab Navigation within Consent Management -->
          <div class="consent-sub-tabs">
            <button 
              :class="['consent-sub-tab', { active: consentSubTab === 'my-consents' }]"
              @click="consentSubTab = 'my-consents'"
            >
              <i class="fas fa-shield-alt"></i> My Consents
            </button>
            <button 
              v-if="isGRCAdministrator"
              :class="['consent-sub-tab', { active: consentSubTab === 'configuration' }]"
              @click="consentSubTab = 'configuration'"
            >
              <i class="fas fa-cog"></i> Configuration
            </button>
          </div>

          <!-- My Consents Sub-tab (for all users) -->
          <div v-if="consentSubTab === 'my-consents'" class="consent-sub-content">
            <ConsentManagement />
          </div>

          <!-- Configuration Sub-tab (admin only) -->
          <div v-else-if="consentSubTab === 'configuration' && isGRCAdministrator" class="consent-sub-content">
            <div class="consent-config-header">
              <div class="header-content">
                <h2 class="section-title">
                  <i class="fas fa-cog"></i>
                  Content Management Configuration
                </h2>
                <p class="section-helper">
                  Configure consent requirements and data retention policies. Only GRC Administrators can access this section.
                </p>
              </div>
            </div>
            
            <!-- Content Management Type Selector -->
            <div class="content-type-selector">
              <button 
                :class="['selector-btn', { active: contentManagementType === 'consent' }]" 
                @click="contentManagementType = 'consent'"
              >
                <i class="fas fa-check-circle"></i> Consent Management
              </button>
              <button 
                :class="['selector-btn', { active: contentManagementType === 'retention' }]" 
                @click="contentManagementType = 'retention'"
              >
                <i class="fas fa-database"></i> Data Retention Configuration
              </button>
            </div>
            
            <div class="content-management-container">
            <!-- Consent Management Section -->
            <div v-if="contentManagementType === 'consent'" class="config-section-content">
              <div class="config-section-header">
                <h3 class="config-section-title">
                  <i class="fas fa-check-circle"></i>
                  Consent Management
                </h3>
                <p class="config-section-description">
                  Configure which actions require user consent
                </p>
              </div>
            
            <div class="consent-config-content">
            <!-- Info Card -->
            <div class="consent-info-card">
              <i class="fas fa-info-circle"></i>
              <div>
                <strong>About Consent Management</strong>
                <p>Enable or disable consent requirements for different actions. When enabled, users will need to accept consent before performing these actions. All consents are tracked and stored in the database.</p>
              </div>
            </div>

            <!-- Framework Info -->
            <div v-if="consentFrameworks.length > 0" class="consent-framework-info">
              <i class="fas fa-info-circle"></i>
              <span>Configuring consent for: <strong>{{ consentFrameworks.find(f => f.FrameworkId == consentFrameworkId)?.FrameworkName || 'Selected Framework' }}</strong></span>
              <button @click="showConsentFrameworkSelector = true" class="btn-change-framework" v-if="consentFrameworks.length > 1">
                <i class="fas fa-exchange-alt"></i> Change Framework
              </button>
            </div>

            <!-- Framework Selector -->
            <div v-if="showConsentFrameworkSelector" class="consent-framework-selector">
              <div class="framework-select-card">
                <h3><i class="fas fa-layer-group"></i> Select Framework</h3>
                <p>Please select a framework to configure consent settings:</p>
                <div class="framework-select-wrapper">
                  <select v-model="consentFrameworkId" @change="onConsentFrameworkChange" class="framework-select" :disabled="loadingConsentFrameworks">
                    <option value="">-- Select Framework --</option>
                    <option v-for="framework in consentFrameworks" :key="framework.FrameworkId" :value="framework.FrameworkId">
                      {{ framework.FrameworkName }}
                    </option>
                  </select>
                  <div v-if="loadingConsentFrameworks" class="loading-small">
                    <div class="spinner-small"></div>
                    <span>Loading frameworks...</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="loadingConsentConfigs" class="consent-loading">
              <div class="spinner"></div>
              <p>Loading consent configurations...</p>
            </div>

            <!-- Consent Configurations Table -->
            <div v-else-if="consentFrameworkId" class="consent-configurations-card">
              <div class="consent-card-header">
                <h3><i class="fas fa-cog"></i> Action Consent Settings</h3>
                <button @click="saveAllConsentConfigurations" class="btn-save" :disabled="savingConsentConfigs || consentModifiedConfigs.size === 0">
                  <i class="fas fa-save"></i>
                  {{ savingConsentConfigs ? 'Saving...' : 'Save All Changes' }}
                </button>
              </div>

              <div class="consent-table-container">
                <table class="consent-configurations-table">
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th class="text-center">Consent Required</th>
                      <th>Consent Text</th>
                      <th>Last Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="config in consentConfigurations" :key="config.config_id" class="consent-config-row">
                      <td>
                        <div class="consent-action-info">
                          <i :class="getConsentActionIcon(config.action_type)"></i>
                          <span class="consent-action-label">{{ config.action_label }}</span>
                        </div>
                      </td>
                      <td class="text-center">
                        <label class="consent-toggle-switch">
                          <input 
                            type="checkbox" 
                            v-model="config.is_enabled"
                            @change="markConsentConfigAsModified(config)"
                          >
                          <span class="consent-toggle-slider"></span>
                        </label>
                      </td>
                      <td>
                        <textarea
                          v-model="config.consent_text"
                          @input="markConsentConfigAsModified(config)"
                          :disabled="!config.is_enabled"
                          class="consent-text-input"
                          rows="2"
                          placeholder="Enter consent text that users will see..."
                        ></textarea>
                      </td>
                      <td class="text-muted">
                        <span v-if="config.updated_at">
                          {{ formatConsentDate(config.updated_at) }}
                          <br>
                          <small>by {{ config.updated_by_name || 'System' }}</small>
                        </span>
                        <span v-else>Never</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Success/Error Messages -->
            <transition name="fade">
              <div v-if="consentMessage" class="consent-alert" :class="consentMessageType">
                <i :class="consentMessageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
                {{ consentMessage }}
              </div>
            </transition>
            </div>
            </div>

            <!-- Data Retention Management Section -->
            <div v-if="contentManagementType === 'retention'" class="config-section-content">
              <div class="config-section-header">
                <h3 class="config-section-title">
                  <i class="fas fa-database"></i>
                  Data Retention Configuration
                </h3>
                <p class="config-section-description">
                  Configure data retention policies for modules and pages
                </p>
              </div>

              <div class="retention-config-content">
                <!-- Framework Info for Retention -->
                <div v-if="consentFrameworks.length > 0 && consentFrameworkId" class="retention-framework-info">
                  <i class="fas fa-info-circle"></i>
                  <span>Configuring retention for: <strong>{{ consentFrameworks.find(f => f.FrameworkId == consentFrameworkId)?.FrameworkName || 'Selected Framework' }}</strong></span>
                </div>

                <!-- Show message if no framework selected -->
                <div v-if="!consentFrameworkId" class="retention-no-framework">
                  <i class="fas fa-info-circle"></i>
                  <p>Please select a framework from the Consent Management section to configure data retention policies.</p>
                </div>

                <!-- Module Pages Tree (All Modules and Pages Where Data is Saved) -->
                <div v-if="consentFrameworkId" class="retention-pages-tree-section">
                  <ModulePagesTree
                    :key="`pages-tree-${consentFrameworkId}`"
                    :framework-id="consentFrameworkId"
                    :initial-configs="{ modules: retentionModuleConfigs, pages: retentionPageConfigs }"
                    @configs-saved="onRetentionConfigsSaved"
                  />
                </div>
              </div>
            </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Requests Tab -->
      <div v-else-if="activeTab === 'requests'" class="requests-section">
        <!-- Data Subject Requests -->
        <div class="requests-container">
          <h2 class="section-title">
            <i class="fas fa-file-alt"></i> Data Subject Requests
          </h2>
          <p class="section-helper">
            View all your data subject requests including access, rectification, erasure, and portability requests.
          </p>
          
          <!-- Risk Level Filter -->
          <div v-if="isAdminUser" class="requests-filters">
            <div class="filter-group">
              <label for="riskLevelFilter">
                <i class="fas fa-filter"></i> Filter by Risk Level:
              </label>
              <select id="riskLevelFilter" v-model="riskLevelFilter" class="filter-select">
                <option value="">All Risk Levels</option>
                <option value="High">High Risk</option>
                <option value="Medium">Medium Risk</option>
                <option value="Low">Low Risk</option>
                <option value="N/A">No Risk Analysis</option>
              </select>
              <button v-if="riskLevelFilter" @click="riskLevelFilter = ''" class="clear-filter-btn" title="Clear filter">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="filter-stats">
              <span class="filter-stat-item">
                <strong>Total (GRC):</strong> {{ dataSubjectRequests.length }}
              </span>
              <span class="filter-stat-item">
                <strong>Total (TPRM):</strong> {{ tprmAccessRequests.length }}
              </span>
              <span class="filter-stat-item">
                <strong>Filtered:</strong> {{ filteredRequests.length }}
              </span>
            </div>
          </div>
         
          <!-- Loading State -->
          <div v-if="loadingRequests || loadingTprmRequests" class="loading-container">
            <div class="spinner"></div>
            <p>Loading requests...</p>
          </div>
          
          <!-- Error State -->
          <div v-else-if="requestsError || tprmRequestsError" class="message error-message">
            <i class="fas fa-exclamation-circle"></i> {{ requestsError || tprmRequestsError }}
          </div>
         
          <!-- Requests Table -->
          <div v-else class="requests-table-container">
            <table class="requests-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User ID</th>
                  <th>User Name</th>
                  <th>Request Type</th>
                  <th>Risk Level</th>
                  <th>Status</th>
                  <th>Verification Status</th>
                  <th>Created At</th>
                  <th>Updated At</th>
                  <th>Approved By</th>
                  <th v-if="isAdminUser">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredRequests.length === 0">
                  <td :colspan="isAdminUser ? 11 : 10" class="no-requests">
                    <i class="fas fa-inbox"></i>
                    <p>No requests found.</p>
                  </td>
                </tr>
                <tr v-for="request in filteredRequests" :key="`${request.source || 'grc'}-${request.id}`" :class="getRequestRowClass(request)">
                  <td>{{ request.id }}</td>
                  <td>{{ request.user_id }}</td>
                  <td>{{ request.user_name || request.UserName || 'N/A' }}</td>
                  <td>
                    <span class="request-type-badge" :class="'type-' + (request.request_type || 'ACCESS').toLowerCase()">
                      {{ request.request_type_display || (request.source === 'tprm' ? 'TPRM Access' : 'Access') }}
                    </span>
                    <span v-if="request.source === 'tprm'" class="source-badge" style="margin-left: 5px; font-size: 10px; background: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px;">TPRM</span>
                  </td>
                  <td>
                    <span v-if="getRequestRiskLevel(request)" class="risk-level-badge" :class="'risk-level-' + getRequestRiskLevel(request).toLowerCase()">
                      <i class="fas fa-exclamation-triangle"></i>
                      {{ getRequestRiskLevel(request) }}
                    </span>
                    <span v-else class="risk-level-badge risk-level-na">
                      <i class="fas fa-minus"></i>
                      N/A
                    </span>
                  </td>
                  <td>
                    <span class="status-badge" :class="'status-' + request.status.toLowerCase().replace(' ', '-')">
                      {{ request.status_display }}
                    </span>
                  </td>
                  <td>
                    <span class="verification-badge" :class="'verification-' + request.verification_status.toLowerCase().replace(' ', '-')">
                      {{ request.verification_status_display }}
                    </span>
                  </td>
                  <td>{{ formatDate(request.created_at) }}</td>
                  <td>{{ formatDate(request.updated_at) }}</td>
                  <td>
                    <span v-if="request.approved_by_name">{{ request.approved_by_name }}</span>
                    <span v-else class="text-muted">N/A</span>
                  </td>
                  <td v-if="isAdminUser">
                    <div class="action-buttons">
                      <button
                        @click="viewRequestDetails(request)"
                        class="action-btn view-btn"
                        title="View Request Details"
                      >
                        <i class="fas fa-eye"></i> View Request
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
   
    <!-- Request Details Modal -->
    <div v-if="showRequestDetailsModal" class="modal-overlay" @click="closeRequestDetailsModal">
      <div class="modal-content request-details-modal" @click.stop>
        <div class="modal-header">
          <h3>
            <i class="fas fa-file-alt"></i>
            Request Details - {{ selectedRequest?.request_type_display || 'Rectification' }}
          </h3>
          <button class="modal-close-btn" @click="closeRequestDetailsModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="selectedRequest" class="request-details-content">
            <!-- Request Information -->
            <div class="request-info-section">
              <h4><i class="fas fa-info-circle"></i> Request Information</h4>
              <div class="info-grid">
                <div class="info-item">
                  <label>Request ID:</label>
                  <span>{{ selectedRequest.id }}</span>
                </div>
                <div class="info-item">
                  <label>User ID:</label>
                  <span>{{ selectedRequest.user_id }}</span>
                </div>
                <div class="info-item">
                  <label>User Name:</label>
                  <span>{{ selectedRequest.user_name }}</span>
                </div>
                <div class="info-item">
                  <label>Request Type:</label>
                  <span class="request-type-badge" :class="'type-' + selectedRequest.request_type.toLowerCase()">
                    {{ selectedRequest.request_type_display }}
                  </span>
                </div>
                <!-- Show ACCESS request specific fields (both GRC and TPRM) -->
                <div v-if="selectedRequest.request_type === 'ACCESS' || selectedRequest.source === 'tprm'" class="info-item">
                  <label>Requested URL:</label>
                  <span class="url-text">{{ selectedRequest.requested_url || selectedRequest.audit_trail?.requested_url || 'N/A' }}</span>
                </div>
                <div v-if="selectedRequest.request_type === 'ACCESS' || selectedRequest.source === 'tprm'" class="info-item">
                  <label>Feature:</label>
                  <span>{{ selectedRequest.requested_feature || selectedRequest.audit_trail?.requested_feature || 'N/A' }}</span>
                </div>
                <div v-if="selectedRequest.request_type === 'ACCESS' || selectedRequest.source === 'tprm'" class="info-item">
                  <label>Required Permission:</label>
                  <span class="permission-badge" v-if="selectedRequest.required_permission || selectedRequest.audit_trail?.required_permission">
                    {{ selectedRequest.required_permission || selectedRequest.audit_trail?.required_permission }}
                  </span>
                  <span v-else class="text-muted">N/A</span>
                </div>
                <div v-if="(selectedRequest.request_type === 'ACCESS' || selectedRequest.source === 'tprm') && (selectedRequest.message || selectedRequest.audit_trail?.message)" class="info-item">
                  <label>Message:</label>
                  <span>{{ selectedRequest.message || selectedRequest.audit_trail?.message }}</span>
                </div>
                <div v-if="selectedRequest.source === 'tprm'" class="info-item">
                  <label>Source:</label>
                  <span class="source-badge" style="background: #17a2b8; color: white; padding: 4px 8px; border-radius: 4px;">TPRM</span>
                </div>
                <!-- Show info_type for non-ACCESS requests -->
                <div v-if="selectedRequest.request_type !== 'ACCESS'" class="info-item">
                  <label>Requested From:</label>
                  <span class="info-type-badge" :class="getInfoTypeClass(selectedRequest.audit_trail?.info_type)">
                    <i :class="getInfoTypeIcon(selectedRequest.audit_trail?.info_type)"></i>
                    {{ getInfoTypeLabel(selectedRequest.audit_trail?.info_type) }}
                  </span>
                </div>
                <!-- Show Risk ID for risk requests -->
                <div v-if="selectedRequest.audit_trail?.info_type === 'risk' && selectedRequest.audit_trail?.risk_id" class="info-item">
                  <label>Risk ID:</label>
                  <span class="risk-id-badge">{{ selectedRequest.audit_trail.risk_id }}</span>
                </div>
                <!-- Show Risk Instance ID for risk_instance requests -->
                <div v-if="selectedRequest.audit_trail?.info_type === 'risk_instance' && selectedRequest.audit_trail?.risk_instance_id" class="info-item">
                  <label>Risk Instance ID:</label>
                  <span class="risk-id-badge">{{ selectedRequest.audit_trail.risk_instance_id }}</span>
                </div>
                <div v-if="selectedRequest.audit_trail?.info_type === 'risk_instance' && selectedRequest.audit_trail?.risk_id" class="info-item">
                  <label>Parent Risk ID:</label>
                  <span class="risk-id-badge">{{ selectedRequest.audit_trail.risk_id }}</span>
                </div>
                <div class="info-item">
                  <label>Status:</label>
                  <span class="status-badge" :class="'status-' + selectedRequest.status.toLowerCase().replace(' ', '-')">
                    {{ selectedRequest.status_display }}
                  </span>
                </div>
                <div class="info-item">
                  <label>Created At:</label>
                  <span>{{ formatDate(selectedRequest.created_at) }}</span>
                </div>
              </div>
            </div>
 
            <!-- Changes Section (only for non-ACCESS requests) -->
            <div v-if="selectedRequest.request_type !== 'ACCESS' && selectedRequest.audit_trail && selectedRequest.audit_trail.changes" class="changes-section">
              <h4><i class="fas fa-edit"></i> Requested Changes</h4>
              <div class="changes-list-container">
                <div
                  v-for="(change, field) in selectedRequest.audit_trail.changes"
                  :key="field"
                  class="change-item"
                >
                  <div class="change-field-name">
                    <i class="fas fa-tag"></i>
                    <strong>{{ formatFieldName(field) }}</strong>
                  </div>
                  <div class="change-values">
                    <div class="change-old">
                      <label>Current Value:</label>
                      <span>{{ change.old || 'N/A' }}</span>
                    </div>
                    <div class="change-arrow">
                      <i class="fas fa-arrow-right"></i>
                    </div>
                    <div class="change-new">
                      <label>New Value:</label>
                      <span>{{ change.new || 'N/A' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="selectedRequest.request_type !== 'ACCESS'" class="no-changes">
              <p><i class="fas fa-info-circle"></i> No changes found in this request.</p>
            </div>

            <!-- Impact Analysis Section (for risk and risk_instance requests) -->
            <div v-if="selectedRequest.request_type === 'RECTIFICATION' && (selectedRequest.audit_trail?.info_type === 'risk' || selectedRequest.audit_trail?.info_type === 'risk_instance')" class="impact-analysis-section">
              <div v-if="selectedRequest.audit_trail?.impact_analysis">
              <div class="impact-analysis-header-with-export">
                <h4><i class="fas fa-chart-line"></i> Impact Analysis</h4>
                <button 
                  @click="exportImpactAnalysis" 
                  class="export-impact-btn"
                  :disabled="exportingImpactAnalysis"
                  title="Export Impact Analysis as PDF"
                >
                  <i v-if="exportingImpactAnalysis" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-download"></i>
                  {{ exportingImpactAnalysis ? 'Exporting...' : 'Export PDF' }}
                </button>
              </div>
              <div class="impact-analysis-content">
                <!-- Risk Level Indicator -->
                <div class="impact-risk-level">
                  <div class="impact-risk-badge" :class="'risk-level-' + (selectedRequest.audit_trail.impact_analysis.riskLevel || 'medium').toLowerCase()">
                    <i class="fas fa-exclamation-triangle"></i>
                    Risk Level: {{ selectedRequest.audit_trail.impact_analysis.riskLevel || 'Medium' }}
                  </div>
                </div>

                <!-- Affected Modules -->
                <div class="impact-subsection" v-if="selectedRequest.audit_trail.impact_analysis.affectedModules && selectedRequest.audit_trail.impact_analysis.affectedModules.length > 0">
                  <h5><i class="fas fa-cubes"></i> Affected Modules</h5>
                  <ul class="impact-list">
                    <li v-for="module in selectedRequest.audit_trail.impact_analysis.affectedModules" :key="module">
                      <strong>{{ module }}</strong>
                    </li>
                  </ul>
                </div>

                <!-- Affected Users -->
                <div class="impact-subsection" v-if="selectedRequest.audit_trail.impact_analysis.affectedUsers && selectedRequest.audit_trail.impact_analysis.affectedUsers.length > 0">
                  <h5><i class="fas fa-users"></i> Affected Users</h5>
                  <ul class="impact-list">
                    <li v-for="user in selectedRequest.audit_trail.impact_analysis.affectedUsers" :key="user">
                      <strong>{{ user }}</strong>
                    </li>
                  </ul>
                </div>

                <!-- Dependencies -->
                <div class="impact-subsection" v-if="selectedRequest.audit_trail.impact_analysis.dependencies && selectedRequest.audit_trail.impact_analysis.dependencies.length > 0">
                  <h5><i class="fas fa-project-diagram"></i> Dependencies</h5>
                  <ul class="impact-list">
                    <li v-for="dependency in selectedRequest.audit_trail.impact_analysis.dependencies" :key="dependency">
                      <strong>{{ dependency }}</strong>
                    </li>
                  </ul>
                </div>

                <!-- Impact Report -->
                <div class="impact-subsection" v-if="selectedRequest.audit_trail.impact_analysis.affectedComponents || selectedRequest.audit_trail.impact_analysis.estimatedImpact">
                  <h5><i class="fas fa-file-alt"></i> Impact Report</h5>
                  <div class="impact-report">
                    <div class="impact-report-item" v-if="selectedRequest.audit_trail.impact_analysis.affectedComponents">
                      <span class="impact-report-label">Affected Components:</span>
                      <span class="impact-report-value">{{ selectedRequest.audit_trail.impact_analysis.affectedComponents.length || 0 }}</span>
                    </div>
                    <div class="impact-report-item" v-if="selectedRequest.audit_trail.impact_analysis.estimatedImpact">
                      <span class="impact-report-label">Estimated Impact:</span>
                      <span class="impact-report-value">{{ selectedRequest.audit_trail.impact_analysis.estimatedImpact }}</span>
                    </div>
                    <div class="impact-report-item" v-if="selectedRequest.audit_trail.impact_analysis.riskAssessment">
                      <span class="impact-report-label">Risk Assessment:</span>
                      <span class="impact-report-value" :class="'risk-assessment-' + (selectedRequest.audit_trail.impact_analysis.riskLevel || 'medium').toLowerCase()">
                        {{ selectedRequest.audit_trail.impact_analysis.riskAssessment }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Recommendations -->
                <div class="impact-subsection" v-if="selectedRequest.audit_trail.impact_analysis.recommendations && selectedRequest.audit_trail.impact_analysis.recommendations.length > 0">
                  <h5><i class="fas fa-lightbulb"></i> Recommendations</h5>
                  <ul class="impact-list">
                    <li v-for="(recommendation, index) in selectedRequest.audit_trail.impact_analysis.recommendations" :key="index">
                      {{ recommendation }}
                    </li>
                  </ul>
                </div>

                <!-- High-Risk Areas -->
                <div class="impact-warning" v-if="selectedRequest.audit_trail.impact_analysis.highRiskAreas && selectedRequest.audit_trail.impact_analysis.highRiskAreas.length > 0">
                  <i class="fas fa-exclamation-triangle"></i>
                  <div>
                    <strong>High-Risk Areas Detected:</strong>
                    <ul class="impact-list">
                      <li v-for="area in selectedRequest.audit_trail.impact_analysis.highRiskAreas" :key="area">{{ area }}</li>
                    </ul>
                  </div>
                </div>

                <!-- Mitigation Steps -->
                <div class="impact-subsection" v-if="selectedRequest.audit_trail.impact_analysis.mitigationSteps && selectedRequest.audit_trail.impact_analysis.mitigationSteps.length > 0">
                  <h5><i class="fas fa-shield-alt"></i> Suggested Mitigation Steps</h5>
                  <ul class="impact-list">
                    <li v-for="(step, index) in selectedRequest.audit_trail.impact_analysis.mitigationSteps" :key="index">
                      <strong>Step {{ index + 1 }}:</strong> {{ step }}
                    </li>
                  </ul>
                </div>
              </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-cancel-btn" @click="closeRequestDetailsModal">
            Close
          </button>
          <div v-if="selectedRequest && selectedRequest.status !== 'APPROVED' && selectedRequest.status !== 'REJECTED'" class="modal-action-buttons">
            <button
              class="modal-reject-btn"
              @click="handleRejectRequest(selectedRequest.id)"
              :disabled="processingRequestId === selectedRequest.id"
            >
              <i v-if="processingRequestId === selectedRequest.id" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-times"></i>
              {{ processingRequestId === selectedRequest.id ? 'Rejecting...' : 'Reject' }}
            </button>
            <button
              class="modal-approve-btn"
              @click="handleApproveRequest(selectedRequest.id)"
              :disabled="processingRequestId === selectedRequest.id"
            >
              <i v-if="processingRequestId === selectedRequest.id" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-check"></i>
              {{ processingRequestId === selectedRequest.id ? 'Approving...' : 'Approve & Apply Changes' }}
            </button>
          </div>
        </div>
      </div>
    </div>
 
    <!-- Rectification Request Modal -->
    <div v-if="showRectificationModal" class="modal-overlay" @click="closeRectificationModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>
            <i class="fas fa-file-alt"></i>
            Request Rectification of {{ currentEditType === 'personal' ? 'Personal' : 'Business' }} Information
          </h3>
          <button class="modal-close-btn" @click="closeRectificationModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="modal-message">
            You are requesting to update your {{ currentEditType === 'personal' ? 'personal' : 'business' }} information.
            The changes will be reviewed and approved by an administrator.
          </p>
          <div class="changes-summary" v-if="Object.keys(getChanges()).length > 0">
            <h4>Changes Summary:</h4>
            <ul class="changes-list">
              <li v-for="(change, field) in getChanges()" :key="field">
                <strong>{{ formatFieldName(field) }}:</strong>
                <span class="old-value">{{ change.old }}</span> →
                <span class="new-value">{{ change.new }}</span>
              </li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-cancel-btn" @click="closeRectificationModal">
            Cancel
          </button>
          <button class="modal-request-btn" @click="submitRectificationRequest" :disabled="submittingRectification">
            <i v-if="submittingRectification" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-paper-plane"></i>
            {{ submittingRectification ? 'Submitting...' : 'Request' }}
          </button>
        </div>
      </div>
    </div>
  
 
    <!-- Forgot Password Modal -->
    <ForgotPassword 
      :showModal="showForgotPasswordModal" 
      :username="''"
      @close="showForgotPasswordModal = false" 
    />

    <!-- OTP Verification Modal for Profile Editing -->
    <div v-if="showOtpModal" class="modal-overlay" @click.self="closeOtpModal">
      <div class="modal-content otp-modal">
        <div class="modal-header">
          <h3><i class="fas fa-shield-alt"></i> Mobile OTP Verification</h3>
          <button class="modal-close" @click="closeOtpModal">
            <i class="fas fa-times"></i>
          </button>
  </div>
        <div class="modal-body">
          <p class="otp-description">
            For security purposes, please verify your mobile number with an OTP before editing your personal information.
          </p>
          
          <div v-if="otpStep === 'send'" class="otp-step">
            <div class="form-group">
              <label>Mobile Number:</label>
              <input 
                type="text" 
                :value="maskedPhoneNumber" 
                disabled 
                class="disabled-input"
              />
            </div>
            <div v-if="otpError" class="message error-message">
              <i class="fas fa-exclamation-circle"></i> {{ otpError }}
            </div>
            <div v-if="otpSuccess" class="message success-message">
              <i class="fas fa-check-circle"></i> {{ otpSuccess }}
            </div>
            <button 
              class="submit-btn" 
              @click="sendProfileEditOtp" 
              :disabled="sendingOtp || loading"
            >
              <i v-if="sendingOtp" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
              {{ sendingOtp ? 'Sending OTP...' : 'Send OTP' }}
            </button>
          </div>

          <div v-if="otpStep === 'verify'" class="otp-step">
            <p class="otp-instruction">
              Enter the 6-digit OTP sent to your mobile number ending in <strong>{{ maskedPhoneNumber.slice(-4) }}</strong>
            </p>
            <div class="otp-input-container">
              <input
                v-for="(digit, index) in otpDigits"
                :key="index"
                ref="otpInputs"
                v-model="otpDigits[index]"
                type="text"
                maxlength="1"
                class="otp-input"
                @input="handleOtpInput(index, $event)"
                @keydown="handleOtpKeydown(index, $event)"
                @paste="handleOtpPaste($event)"
              />
            </div>
            <div v-if="otpError" class="message error-message">
              <i class="fas fa-exclamation-circle"></i> {{ otpError }}
            </div>
            <div class="otp-actions">
              <button 
                class="btn-secondary" 
                @click="resendOtp" 
                :disabled="resendingOtp || otpResendCooldown > 0"
              >
                <i v-if="resendingOtp" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-redo"></i>
                {{ resendingOtp ? 'Resending...' : (otpResendCooldown > 0 ? `Resend (${otpResendCooldown}s)` : 'Resend OTP') }}
              </button>
              <button 
                class="submit-btn" 
                @click="verifyProfileEditOtp" 
                :disabled="verifyingOtp || !isOtpComplete || loading"
              >
                <i v-if="verifyingOtp" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-check"></i>
                {{ verifyingOtp ? 'Verifying...' : 'Verify OTP' }}
              </button>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>

    <!-- Portability OTP Verification Modal -->
    <div v-if="showPortabilityOtpModal" class="modal-overlay" @click.self="closePortabilityOtpModal">
      <div class="modal-content otp-modal">
        <div class="modal-header">
          <h3><i class="fas fa-shield-alt"></i> Mobile OTP Verification for Data Export</h3>
          <button class="modal-close" @click="closePortabilityOtpModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="otp-description">
            For security purposes, please verify your mobile number with an OTP before exporting your data.
          </p>
          
          <div v-if="portabilityOtpStep === 'send'" class="otp-step">
            <div class="form-group">
              <label>Mobile Number:</label>
              <input 
                type="text" 
                :value="maskedPhoneNumber" 
                disabled 
                class="disabled-input"
              />
            </div>
            <div v-if="portabilityOtpError" class="message error-message">
              <i class="fas fa-exclamation-circle"></i> {{ portabilityOtpError }}
            </div>
            <div v-if="portabilityOtpSuccess" class="message success-message">
              <i class="fas fa-check-circle"></i> {{ portabilityOtpSuccess }}
            </div>
            <button 
              class="submit-btn" 
              @click="sendPortabilityOtp" 
              :disabled="sendingPortabilityOtp || loading"
            >
              <i v-if="sendingPortabilityOtp" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
              {{ sendingPortabilityOtp ? 'Sending OTP...' : 'Send OTP' }}
            </button>
          </div>

          <div v-if="portabilityOtpStep === 'verify'" class="otp-step">
            <p class="otp-instruction">
              Enter the 6-digit OTP sent to your mobile number ending in <strong>{{ maskedPhoneNumber.slice(-4) }}</strong>
            </p>
            <div class="otp-input-container">
              <input
                v-for="(digit, index) in portabilityOtpDigits"
                :key="index"
                ref="portabilityOtpInputs"
                v-model="portabilityOtpDigits[index]"
                type="text"
                maxlength="1"
                class="otp-input"
                @input="handlePortabilityOtpInput(index, $event)"
                @keydown="handlePortabilityOtpKeydown(index, $event)"
                @paste="handlePortabilityOtpPaste($event)"
              />
            </div>
            <div v-if="portabilityOtpError" class="message error-message">
              <i class="fas fa-exclamation-circle"></i> {{ portabilityOtpError }}
            </div>
            <div class="otp-actions">
              <button 
                class="btn-secondary" 
                @click="resendPortabilityOtp" 
                :disabled="resendingPortabilityOtp || portabilityOtpResendCooldown > 0"
              >
                <i v-if="resendingPortabilityOtp" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-redo"></i>
                {{ resendingPortabilityOtp ? 'Resending...' : (portabilityOtpResendCooldown > 0 ? `Resend (${portabilityOtpResendCooldown}s)` : 'Resend OTP') }}
              </button>
              <button 
                class="submit-btn" 
                @click="verifyPortabilityOtp" 
                :disabled="verifyingPortabilityOtp || !isPortabilityOtpComplete || loading"
              >
                <i v-if="verifyingPortabilityOtp" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-check"></i>
                {{ verifyingPortabilityOtp ? 'Verifying...' : 'Verify OTP' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  

  
</template>

<script>
// import { API_ENDPOINTS } from '@/config/api.js'
import { api } from '../../data/api';
import ConsentManagement from '../Consent/ConsentManagement.vue';
import ForgotPassword from './ForgotPassword.vue';
import ModulePagesTree from './DataRetention/ModulePagesTree.vue';

export default {
  name: 'UserProfile',
  components: {
    ConsentManagement,
    ForgotPassword,
    ModulePagesTree
  },
  data() {
    return {
      activeTab: 'account',
      accountInfoType: 'personal', // New property to track which info type is displayed
      consentSubTab: 'my-consents', // Sub-tab within Consent Management: 'my-consents' or 'configuration'
      contentManagementType: 'consent', // Track which content management section is displayed: 'consent' or 'retention'
      tabs: [
        { key: 'account', label: 'Account', icon: 'fas fa-user' },
        { key: 'role', label: 'Role', icon: 'fas fa-exchange-alt' },
        { key: 'password', label: 'Password', icon: 'fas fa-key' },
        { key: 'notification', label: 'Notification', icon: 'fas fa-bell' },
        { key: 'user-management', label: 'User Management', icon: 'fas fa-users', adminOnly: true },
        { key: 'consent-config', label: 'Consent Management', icon: 'fas fa-check-circle' },
        { key: 'requests', label: 'Requests', icon: 'fas fa-file-alt'}
      ],
      maskedData: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        address: '',
        username: ''
      },
      form: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        address: '',
        newPassword: '',
        confirmPassword: '',
        otp: '',
        emailNotif: false,
        whatsappNotif: false,
        notifEmail: '',
        notifMobile: ''
      },
      businessInfo: {
        departmentId: '',
        departmentName: '',
        businessUnitName: '',
        businessUnitCode: '',
        entityName: '',
        entityType: '',
        location: '',
        departmentHead: ''
      },
      notifDropdownOpen: null,
      loading: false,
      error: null,
      success: null,
      showForgotPasswordModal: false,
      userPermissions: {
        role: '',
        modules: {}
      },
      expandedModules: [],
      showCreateUserModal: false,
      isGRCAdministrator: false,
             showCreateUserForm: false, // New state for the integrated form
      showManageUsersForm: false, // State for manage users form
      showAllUsersList: false, // State for all users list
      allUsersList: [], // List of all users
      loadingAllUsers: false, // Loading state for fetching users
      updatingUserStatus: null, // User ID being updated
      allUsersError: null, // Error message for all users operations
      allUsersSuccess: null, // Success message for all users operations
      passwordFieldType: 'password', // For password visibility toggle
      usersList: [], // List of users for dropdown
      selectedUserId: '', // Selected user ID for editing
      selectedUserName: '', // Selected user name for display
      selectedUserRole: '', // Selected user role
      selectedUserPermissions: null, // Permissions for selected user
      manageUsersLoading: false, // Loading state for manage users
      savingPermissions: false, // Saving state for permissions
      manageUsersError: null, // Error message for manage users
      manageUsersSuccess: null, // Success message for manage users
      selectAllManagePermissions: false, // Select all for manage users
      moduleSelectAllManage: {}, // Module select all for manage users
      createUserForm: {
         username: '',
         email: '',
         firstName: '',
         lastName: '',
         phoneNumber: '',
         address: '',
         departmentId: '',
         role: '',
         isActive: 'Y'
       },
       showPasswordRequirements: false, // Show password requirements
       passwordErrors: [], // Password validation errors
       passwordChecks: { // Password validation checks
         hasUppercase: false,
         hasLowercase: false,
         hasNumber: false,
         hasSpecialChar: false
       },
      createUserLoading: false,
      createUserError: null,
      createUserSuccess: null,
      departments: [], // For department selection
      availableRoles: ['GRC Administrator', 'Risk Analyst', 'Compliance Officer', 'IT Manager', 'Business Analyst'],
      customRole: '',
      selectAllPermissions: false,
      moduleSelectAll: {},
      selectedPermissions: {},
      // Consent Configuration properties
      consentConfigurations: [],
      consentFrameworkId: null,
      consentFrameworks: [],
      loadingConsentConfigs: false,
      loadingConsentFrameworks: false,
      savingConsentConfigs: false,
      consentModifiedConfigs: new Set(),
      consentMessage: '',
      consentMessageType: 'success',
      showConsentFrameworkSelector: false,
      // Data Retention Configuration properties
      retentionModuleConfigs: {},
      retentionPageConfigs: {},
      // Data Subject Requests
      dataSubjectRequests: [],
      // TPRM Access Requests
      tprmAccessRequests: [],
      loadingRequests: false,
      loadingTprmRequests: false,
      requestsError: null,
      tprmRequestsError: null,
      processingRequestId: null,
      // Edit mode states
      editModePersonal: false,
      editModeBusiness: false,
      originalPersonalData: {},
      originalBusinessData: {},
      showRectificationModal: false,
      currentEditType: 'personal', // 'personal' or 'business'
      submittingRectification: false,
      // OTP Verification for profile editing
      showOtpModal: false,
      otpStep: 'send', // 'send' or 'verify'
      otpDigits: ['', '', '', '', '', ''],
      otpError: null,
      otpSuccess: null,
      sendingOtp: false,
      verifyingOtp: false,
      resendingOtp: false,
      otpResendCooldown: 0,
      otpResendTimer: null,
      // Portability OTP Verification
      showPortabilityOtpModal: false,
      portabilityOtpStep: 'send', // 'send' or 'verify'
      portabilityOtpDigits: ['', '', '', '', '', ''],
      portabilityOtpError: null,
      portabilityOtpSuccess: null,
      sendingPortabilityOtp: false,
      verifyingPortabilityOtp: false,
      resendingPortabilityOtp: false,
      portabilityOtpResendCooldown: 0,
      portabilityOtpResendTimer: null,
      exportingData: false,
      selectedExportFormat: 'json', // 'json', 'csv', 'xlsx', 'pdf', 'xml', 'txt'
      showFormatDropdown: false,
      exportFormats: [
        { value: 'json', label: 'JSON (.json)' },
        { value: 'csv', label: 'CSV (.csv)' },
        { value: 'xlsx', label: 'Excel (.xlsx)' },
        { value: 'pdf', label: 'PDF (.pdf)' },
        { value: 'xml', label: 'XML (.xml)' },
        { value: 'txt', label: 'Text (.txt)' }
      ],
      pendingEditType: null, // Store which edit type was requested
      showRequestDetailsModal: false,
      selectedRequest: null,
      riskLevelFilter: '',
      exportingImpactAnalysis: false,
      rbacModules: [
        {
          name: 'compliance',
          displayName: 'Compliance',
          permissions: [
            { field: 'view_all_compliance', label: 'View All Compliance' },
            { field: 'create_compliance', label: 'Create Compliance' },
            { field: 'edit_compliance', label: 'Edit Compliance' },
            { field: 'approve_compliance', label: 'Approve Compliance' },
            { field: 'compliance_performance_analytics', label: 'Compliance Performance Analytics' }
          ]
        },
        {
          name: 'policy',
          displayName: 'Policy',
          permissions: [
            { field: 'create_policy', label: 'Create Policy' },
            { field: 'edit_policy', label: 'Edit Policy' },
            { field: 'approve_policy', label: 'Approve Policy' },
            { field: 'create_framework', label: 'Create Framework' },
            { field: 'approve_framework', label: 'Approve Framework' },
            { field: 'view_all_policy', label: 'View All Policy' },
            { field: 'policy_performance_analytics', label: 'Policy Performance Analytics' }
          ]
        },
        {
          name: 'audit',
          displayName: 'Audit',
          permissions: [
            { field: 'assign_audit', label: 'Assign Audit' },
            { field: 'conduct_audit', label: 'Conduct Audit' },
            { field: 'review_audit', label: 'Review Audit' },
            { field: 'view_audit_reports', label: 'View Audit Reports' },
            { field: 'audit_performance_analytics', label: 'Audit Performance Analytics' }
          ]
        },
        {
          name: 'risk',
          displayName: 'Risk',
          permissions: [
            { field: 'create_risk', label: 'Create Risk' },
            { field: 'edit_risk', label: 'Edit Risk' },
            { field: 'approve_risk', label: 'Approve Risk' },
            { field: 'assign_risk', label: 'Assign Risk' },
            { field: 'evaluate_assigned_risk', label: 'Evaluate Assigned Risk' },
            { field: 'view_all_risk', label: 'View All Risk' },
            { field: 'risk_performance_analytics', label: 'Risk Performance Analytics' }
          ]
        },
        {
          name: 'incident',
          displayName: 'Incident',
          permissions: [
            { field: 'create_incident', label: 'Create Incident' },
            { field: 'edit_incident', label: 'Edit Incident' },
            { field: 'assign_incident', label: 'Assign Incident' },
            { field: 'evaluate_assigned_incident', label: 'Evaluate Assigned Incident' },
            { field: 'escalate_to_risk', label: 'Escalate to Risk' },
            { field: 'view_all_incident', label: 'View All Incident' },
            { field: 'incident_performance_analytics', label: 'Incident Performance Analytics' }
          ]
        }
      ]
    }
  },
  computed: {
    visibleTabs() {
      return this.tabs.filter(tab => {
        if (tab.adminOnly) {
          return this.isGRCAdministrator;
        }
        return true;
      });
    },
    isCreateUserFormValid() {
      return this.createUserForm.username && 
             this.createUserForm.email && 
             this.createUserForm.firstName && 
             this.createUserForm.lastName && 
             this.createUserForm.departmentId && 
             this.createUserForm.role;
            },
    isAdminUser() {
      const userId = parseInt(this.getCurrentUserId());
      return [1, 2, 3, 4].includes(userId);
    },
    hasAccessRequests() {
      // Check if any data subject requests are of type ACCESS
      return this.dataSubjectRequests.some(req => req.request_type === 'ACCESS');
    },
    maskedPhoneNumber() {
      return this.form.phone || this.maskedData.phone || '****';
    },
    isOtpComplete() {
      if (!this.otpDigits || !Array.isArray(this.otpDigits)) {
        return false;
      }
      return this.otpDigits.every(digit => digit !== '') && this.otpDigits.join('').length === 6;
    },
    filteredRequests() {
      // Combine GRC and TPRM requests
      const allRequests = [
        ...this.dataSubjectRequests.map(req => ({ ...req, source: 'grc' })),
        ...this.tprmAccessRequests.map(req => ({ ...req, source: 'tprm', request_type: 'ACCESS', request_type_display: 'TPRM Access' }))
      ];
      
      if (!this.riskLevelFilter) {
        return allRequests;
      }
      
      // Filter requests based on risk level
      // TPRM requests don't have risk levels, so always include them
      return allRequests.filter(request => {
        // Always include TPRM requests (they don't have risk levels)
        if (request.source === 'tprm') {
          return true;
        }
        
        // For GRC requests, apply risk level filter
        const riskLevel = this.getRequestRiskLevel(request);
        if (this.riskLevelFilter === 'N/A') {
          return !riskLevel;
        }
        return riskLevel === this.riskLevelFilter;
      });
    }
  },
  mounted() {
    this.loadUserData();
    this.loadDepartments(); // Load departments for the new form
    
    // Listen for login events
    window.addEventListener('userLoggedIn', this.handleUserLogin);
    
    // Initialize consent configuration if user is admin
    if (this.isGRCAdministrator) {
      this.initializeConsentConfiguration();
    }
  },
  
  watch: {
    isGRCAdministrator(newVal) {
      if (newVal && this.activeTab === 'consent-config') {
        this.initializeConsentConfiguration();
      }
    },
    activeTab(newTab) {
      if (newTab === 'consent-config') {
        // Reset to 'my-consents' sub-tab when switching to consent management
        this.consentSubTab = 'my-consents';
      } else if (newTab === 'requests') {
        // Load requests when switching to requests tab
        this.loadDataSubjectRequests();
        this.loadTprmAccessRequests();
      }
    },
    consentSubTab(newSubTab) {
      // When switching to configuration sub-tab, initialize if admin
      if (newSubTab === 'configuration' && this.isGRCAdministrator) {
        this.initializeConsentConfiguration();
      }
    }
  },

  beforeUnmount() {
    // Clean up event listener
    window.removeEventListener('userLoggedIn', this.handleUserLogin);
  },

  methods: {
    // Update personal field only if in edit mode
    updatePersonalField(field, value) {
      if (this.editModePersonal) {
        this.form[field] = value;
      }
    },
    
    // OTP Verification Methods
    async checkProfileEditVerification() {
      try {
        const { API_BASE_URL } = await import('../../config/api.js');
        const axios = (await import('axios')).default;
        
        const response = await axios.get(
          `${API_BASE_URL}/api/profile-edit-otp/check/`,
          { headers: this.getConsentAuthHeaders() }
        );
        
        return response.data.verified === true;
      } catch (error) {
        console.error('Error checking profile edit verification:', error);
        return false;
      }
    },
    
    async sendProfileEditOtp() {
      this.sendingOtp = true;
      this.otpError = null;
      this.otpSuccess = null;
      
      try {
        const { API_BASE_URL } = await import('../../config/api.js');
        const axios = (await import('axios')).default;
        
        const response = await axios.post(
          `${API_BASE_URL}/api/profile-edit-otp/send/`,
          {},
          { headers: this.getConsentAuthHeaders() }
        );
        
        if (response.data.success) {
          this.otpSuccess = response.data.message;
          this.otpStep = 'verify';
          this.otpDigits = ['', '', '', '', '', ''];
          this.startOtpResendCooldown();
          // Focus first OTP input
          this.$nextTick(() => {
            if (this.$refs.otpInputs && this.$refs.otpInputs[0]) {
              this.$refs.otpInputs[0].focus();
            }
          });
        } else {
          this.otpError = response.data.message || 'Failed to send OTP';
        }
      } catch (error) {
        console.error('Error sending profile edit OTP:', error);
        this.otpError = error.response?.data?.message || 'Failed to send OTP. Please try again.';
      } finally {
        this.sendingOtp = false;
      }
    },
    
    async verifyProfileEditOtp() {
      if (!this.isOtpComplete) {
        this.otpError = 'Please enter a valid 6-digit OTP';
        return;
      }
      
      this.verifyingOtp = true;
      this.otpError = null;
      
      try {
        const { API_BASE_URL } = await import('../../config/api.js');
        const axios = (await import('axios')).default;
        
        const otp = this.otpDigits.join('');
        const response = await axios.post(
          `${API_BASE_URL}/api/profile-edit-otp/verify/`,
          { otp: otp },
          { headers: this.getConsentAuthHeaders() }
        );
        
        if (response.data.success) {
          this.otpSuccess = response.data.message;
          
          // Enable edit mode for the pending type
          if (this.pendingEditType === 'personal') {
            // Reload user data to ensure we have the latest original unmasked data
            await this.loadUserData();
            
            // Wait for data to be loaded, then set original data and enable edit mode
            await this.$nextTick();
            
            this.originalPersonalData = {
              firstName: this.form.firstName,
              lastName: this.form.lastName,
              email: this.form.email,
              phone: this.form.phone || '',
              address: this.form.address || ''
            };
            
            // Enable edit mode
            this.editModePersonal = true;
            
            // Close modal after enabling edit mode
            this.closeOtpModal();
            
            // Show success message
            this.success = 'OTP verified successfully! You can now edit your personal information.';
            setTimeout(() => {
              this.success = null;
            }, 3000);
          }
          this.pendingEditType = null;
        } else {
          this.otpError = response.data.message || 'Invalid OTP. Please try again.';
          // Clear OTP inputs on error
          this.otpDigits = ['', '', '', '', '', ''];
          this.$nextTick(() => {
            if (this.$refs.otpInputs && this.$refs.otpInputs[0]) {
              this.$refs.otpInputs[0].focus();
            }
          });
        }
      } catch (error) {
        console.error('Error verifying profile edit OTP:', error);
        this.otpError = error.response?.data?.message || 'Failed to verify OTP. Please try again.';
        // Clear OTP inputs on error
        this.otpDigits = ['', '', '', '', '', ''];
        this.$nextTick(() => {
          if (this.$refs.otpInputs && this.$refs.otpInputs[0]) {
            this.$refs.otpInputs[0].focus();
          }
        });
      } finally {
        this.verifyingOtp = false;
      }
    },
    
    async resendOtp() {
      this.resendingOtp = true;
      this.otpError = null;
      this.otpSuccess = null;
      
      try {
        await this.sendProfileEditOtp();
      } finally {
        this.resendingOtp = false;
      }
    },
    
    closeOtpModal() {
      this.showOtpModal = false;
      this.otpStep = 'send';
      this.otpDigits = ['', '', '', '', '', ''];
      this.otpError = null;
      this.otpSuccess = null;
      this.pendingEditType = null;
      if (this.otpResendTimer) {
        clearInterval(this.otpResendTimer);
        this.otpResendTimer = null;
      }
      this.otpResendCooldown = 0;
    },
    
    startOtpResendCooldown() {
      this.otpResendCooldown = 60; // 60 seconds
      if (this.otpResendTimer) {
        clearInterval(this.otpResendTimer);
      }
      this.otpResendTimer = setInterval(() => {
        this.otpResendCooldown--;
        if (this.otpResendCooldown <= 0) {
          clearInterval(this.otpResendTimer);
          this.otpResendTimer = null;
        }
      }, 1000);
    },
    
    // Portability Export Methods
    async initiatePortabilityExport() {
      if (!this.selectedExportFormat) {
        this.error = 'Please select an export format';
        return;
      }
      // Directly export without OTP verification
      await this.exportUserData();
    },
    
    selectExportFormat(format) {
      this.selectedExportFormat = format;
      this.showFormatDropdown = false;
    },
    
    async sendPortabilityOtp() {
      this.sendingPortabilityOtp = true;
      this.portabilityOtpError = null;
      this.portabilityOtpSuccess = null;
      
      try {
        const { API_BASE_URL } = await import('../../config/api.js');
        const axios = (await import('axios')).default;
        
        const response = await axios.post(
          `${API_BASE_URL}/api/portability-otp/send/`,
          {},
          { headers: this.getConsentAuthHeaders() }
        );
        
        if (response.data.success) {
          this.portabilityOtpSuccess = response.data.message;
          this.portabilityOtpStep = 'verify';
          this.startPortabilityOtpResendCooldown();
          this.$nextTick(() => {
            if (this.$refs.portabilityOtpInputs && this.$refs.portabilityOtpInputs[0]) {
              this.$refs.portabilityOtpInputs[0].focus();
            }
          });
        } else {
          this.portabilityOtpError = response.data.message || 'Failed to send OTP';
        }
      } catch (error) {
        console.error('Error sending portability OTP:', error);
        this.portabilityOtpError = error.response?.data?.message || 'Failed to send OTP. Please try again.';
      } finally {
        this.sendingPortabilityOtp = false;
      }
    },
    
    async verifyPortabilityOtp() {
      this.verifyingPortabilityOtp = true;
      this.portabilityOtpError = null;
      
      const otp = this.portabilityOtpDigits.join('');
      
      if (otp.length !== 6) {
        this.portabilityOtpError = 'Please enter a complete 6-digit OTP';
        this.verifyingPortabilityOtp = false;
        return;
      }
      
      try {
        const { API_BASE_URL } = await import('../../config/api.js');
        const axios = (await import('axios')).default;
        
        const response = await axios.post(
          `${API_BASE_URL}/api/portability-otp/verify/`,
          { otp: otp },
          { headers: this.getConsentAuthHeaders() }
        );
        
        if (response.data.success) {
          this.portabilityOtpSuccess = response.data.message;
          // Close OTP modal and proceed with export
          this.closePortabilityOtpModal();
          await this.exportUserData();
        } else {
          this.portabilityOtpError = response.data.message || 'Invalid OTP. Please try again.';
          this.portabilityOtpDigits = ['', '', '', '', '', ''];
          this.$nextTick(() => {
            if (this.$refs.portabilityOtpInputs && this.$refs.portabilityOtpInputs[0]) {
              this.$refs.portabilityOtpInputs[0].focus();
            }
          });
        }
      } catch (error) {
        console.error('Error verifying portability OTP:', error);
        this.portabilityOtpError = error.response?.data?.message || 'Failed to verify OTP. Please try again.';
        this.portabilityOtpDigits = ['', '', '', '', '', ''];
        this.$nextTick(() => {
          if (this.$refs.portabilityOtpInputs && this.$refs.portabilityOtpInputs[0]) {
            this.$refs.portabilityOtpInputs[0].focus();
          }
        });
      } finally {
        this.verifyingPortabilityOtp = false;
      }
    },
    
    async resendPortabilityOtp() {
      this.resendingPortabilityOtp = true;
      this.portabilityOtpError = null;
      this.portabilityOtpSuccess = null;
      
      try {
        await this.sendPortabilityOtp();
      } finally {
        this.resendingPortabilityOtp = false;
      }
    },
    
    closePortabilityOtpModal() {
      this.showPortabilityOtpModal = false;
      this.portabilityOtpStep = 'send';
      this.portabilityOtpDigits = ['', '', '', '', '', ''];
      this.portabilityOtpError = null;
      this.portabilityOtpSuccess = null;
      if (this.portabilityOtpResendTimer) {
        clearInterval(this.portabilityOtpResendTimer);
        this.portabilityOtpResendTimer = null;
      }
      this.portabilityOtpResendCooldown = 0;
    },
    
    startPortabilityOtpResendCooldown() {
      this.portabilityOtpResendCooldown = 60; // 60 seconds
      if (this.portabilityOtpResendTimer) {
        clearInterval(this.portabilityOtpResendTimer);
      }
      this.portabilityOtpResendTimer = setInterval(() => {
        this.portabilityOtpResendCooldown--;
        if (this.portabilityOtpResendCooldown <= 0) {
          clearInterval(this.portabilityOtpResendTimer);
          this.portabilityOtpResendTimer = null;
        }
      }, 1000);
    },
    
    handlePortabilityOtpInput(index, event) {
      const value = event.target.value.replace(/[^0-9]/g, '');
      if (value) {
        this.portabilityOtpDigits[index] = value;
        if (index < 5 && this.$refs.portabilityOtpInputs) {
          this.$refs.portabilityOtpInputs[index + 1].focus();
        }
      } else {
        this.portabilityOtpDigits[index] = '';
      }
    },
    
    handlePortabilityOtpKeydown(index, event) {
      if (event.key === 'Backspace' && !this.portabilityOtpDigits[index] && index > 0 && this.$refs.portabilityOtpInputs) {
        this.$refs.portabilityOtpInputs[index - 1].focus();
      }
    },
    
    handlePortabilityOtpPaste(event) {
      event.preventDefault();
      const pastedData = event.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6);
      for (let i = 0; i < pastedData.length && i < 6; i++) {
        this.portabilityOtpDigits[i] = pastedData[i];
      }
      if (pastedData.length === 6 && this.$refs.portabilityOtpInputs) {
        this.$refs.portabilityOtpInputs[5].focus();
      }
    },
    
    get isPortabilityOtpComplete() {
      if (!this.portabilityOtpDigits || !Array.isArray(this.portabilityOtpDigits)) {
        return false;
      }
      return this.portabilityOtpDigits.every(digit => digit !== '') && this.portabilityOtpDigits.join('').length === 6;
    },
    
    async exportUserData() {
      this.exportingData = true;
      this.error = null;
      this.success = null;
      
      try {
        const { API_BASE_URL } = await import('../../config/api.js');
        const axios = (await import('axios')).default;
        
        const response = await axios.post(
          `${API_BASE_URL}/api/export-user-data-portability/`,
          { export_format: this.selectedExportFormat },
          { headers: this.getConsentAuthHeaders() }
        );
        
        if (response.data.status === 'success') {
          this.success = 'Data exported successfully!';
          // Open download link
          if (response.data.data && response.data.data.download_url) {
            window.open(response.data.data.download_url, '_blank');
          }
          // Reload requests to show the new portability request
          await this.loadDataSubjectRequests();
        } else {
          this.error = response.data.message || 'Failed to export data';
        }
      } catch (error) {
        console.error('Error exporting user data:', error);
        this.error = error.response?.data?.message || 'Failed to export data. Please try again.';
      } finally {
        this.exportingData = false;
      }
    },
    
    handleOtpInput(index, event) {
      const value = event.target.value.replace(/[^0-9]/g, '');
      if (value) {
        this.otpDigits[index] = value;
        // Move to next input
        if (index < 5 && this.$refs.otpInputs && this.$refs.otpInputs[index + 1]) {
          this.$refs.otpInputs[index + 1].focus();
        }
      } else {
        this.otpDigits[index] = '';
      }
    },
    
    handleOtpKeydown(index, event) {
      if (event.key === 'Backspace' && !this.otpDigits[index] && index > 0) {
        // Move to previous input on backspace
        if (this.$refs.otpInputs && this.$refs.otpInputs[index - 1]) {
          this.$refs.otpInputs[index - 1].focus();
        }
      }
    },
    
    handleOtpPaste(event) {
      event.preventDefault();
      const pastedData = event.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6);
      for (let i = 0; i < 6; i++) {
        this.otpDigits[i] = pastedData[i] || '';
      }
      // Focus last filled input or first empty
      const lastFilledIndex = Math.min(pastedData.length - 1, 5);
      this.$nextTick(() => {
        if (this.$refs.otpInputs && this.$refs.otpInputs[lastFilledIndex]) {
          this.$refs.otpInputs[lastFilledIndex].focus();
        }
      });
    },
    
    // Password validation function
    validatePassword() {
      const password = this.createUserForm.password || ''
      this.passwordErrors = []
      
      // Check minimum length
      if (password.length < 8) {
        this.passwordErrors.push('Password must be at least 8 characters long')
      }
      
      // Check for uppercase
      this.passwordChecks.hasUppercase = /[A-Z]/.test(password)
      if (!this.passwordChecks.hasUppercase && password.length > 0) {
        this.passwordErrors.push('Password must contain at least one uppercase letter')
      }
      
      // Check for lowercase
      this.passwordChecks.hasLowercase = /[a-z]/.test(password)
      if (!this.passwordChecks.hasLowercase && password.length > 0) {
        this.passwordErrors.push('Password must contain at least one lowercase letter')
      }
      
      // Check for number
      this.passwordChecks.hasNumber = /[0-9]/.test(password)
      if (!this.passwordChecks.hasNumber && password.length > 0) {
        this.passwordErrors.push('Password must contain at least one number')
      }
      
      // Check for special character (fixed regex - removed unnecessary escapes)
      this.passwordChecks.hasSpecialChar = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)
      if (!this.passwordChecks.hasSpecialChar && password.length > 0) {
        this.passwordErrors.push('Password must contain at least one special character')
      }
    },
    
    // Handle login event
    handleUserLogin(event) {
      if (event.detail && event.detail.user) {
        const userId = event.detail.user.UserId;
        if (userId) {
          console.log('Storing user ID in session storage:', userId);
          sessionStorage.setItem('userId', userId);
          this.loadUserData();
        }
      }
    },

    // Add a method to get the current user ID from all possible sources
    getCurrentUserId() {
      console.log('=== DEBUGGING USER ID RETRIEVAL ===');
      
      // Try to get from URL params first
      const urlParams = new URLSearchParams(window.location.search);
      let userId = urlParams.get('userId');
      
      if (userId) {
        console.log('Using userId from URL:', userId);
        return userId;
      }
      
      // Try localStorage user_id (primary source for JWT authentication)
      userId = localStorage.getItem('user_id');
      if (userId) {
        console.log('Using userId from localStorage user_id:', userId);
        return userId;
      }
      
      // Try session storage
      userId = sessionStorage.getItem('userId');
      if (userId) {
        console.log('Using userId from sessionStorage:', userId);
        return userId;
      }
      
      // Try from session user object
      const sessionUser = sessionStorage.getItem('user');
      console.log('Session user data:', sessionUser);
      if (sessionUser) {
        try {
          const parsedUser = JSON.parse(sessionUser);
          console.log('Parsed session user:', parsedUser);
          userId = parsedUser.UserId || parsedUser.userId;
          if (userId) {
            console.log('Using userId from session user object:', userId);
            return userId;
          }
        } catch (e) {
          console.error('Error parsing session user:', e);
        }
      }
      
      // Try localStorage user object
      const localUser = localStorage.getItem('user');
      console.log('Local user data:', localUser);
      if (localUser) {
        try {
          const parsedUser = JSON.parse(localUser);
          console.log('Parsed local user:', parsedUser);
          userId = parsedUser.UserId || parsedUser.userId;
          if (userId) {
            console.log('Using userId from localStorage user object:', userId);
            return userId;
          }
        } catch (e) {
          console.error('Error parsing local user:', e);
        }
      }
      
      // Check for username in localStorage that might help identify the user
      const userName = localStorage.getItem('user_name');
      const fullName = localStorage.getItem('fullName');
      const username = localStorage.getItem('username');
      console.log('Additional user info - userName:', userName, 'fullName:', fullName, 'username:', username);
      
      // TEMPORARY FIX: Check if the current user is vikram.patel and use the correct user ID
      // Based on the hardcoded mapping found in ComplianceApprover.vue
      if (userName === 'vikram.patel' || fullName === 'vikram.patel' || username === 'vikram.patel') {
        console.log('Detected vikram.patel, using user ID 2');
        return '2';
      }
      
      // Default to 1 if nothing else works
      console.log('No user ID found, using default: 1');
      return '1';
    },

    async loadUserData() {
      this.loading = true;
      this.error = null;

      try {
        const userId = this.getCurrentUserId();
        
        if (userId) {
          console.log('Fetching user profile for userId:', userId);
          
          // Fetch personal info using centralized API with JWT
          const profileResponse = await api.getUserProfile(userId);
          console.log('Profile data received:', profileResponse.data);
          
          if (profileResponse.data.status === 'success') {
            const data = profileResponse.data.data;
            console.log('Full profile data:', data);
            
            // Use original data for editing (if available), otherwise use masked
            this.form.firstName = data.original?.firstName || data.firstName || '';
            this.form.lastName = data.original?.lastName || data.lastName || '';
            this.form.email = data.original?.email || data.email || '';
            this.form.phone = data.original?.phoneNumber || data.phoneNumber || '';
            this.form.address = data.original?.address || data.address || '';
            
            // Store masked versions for display
            this.maskedData = {
              firstName: data.firstName || '',
              lastName: data.lastName || '',
              email: data.email || '',
              phone: data.phoneNumber || '',
              address: data.address || '',
              username: data.username || ''
            };
            
            console.log('Form data set:', {
              firstName: this.form.firstName,
              lastName: this.form.lastName,
              email: this.form.email,
              phone: this.form.phone,
              address: this.form.address
            });
            console.log('Masked data set:', this.maskedData);
            
            // Fetch business info using centralized API with JWT
            console.log('Fetching business info for userId:', userId);
            try {
              const businessResponse = await api.getUserBusinessInfo(userId);
              console.log('Business data received:', businessResponse.data);
              
              if (businessResponse.data.status === 'success') {
                const data = businessResponse.data.data;
                this.businessInfo = {
                  departmentId: data.DepartmentId,
                  departmentName: data.DepartmentName || 'N/A',
                  businessUnitName: data.BusinessUnitName || 'N/A',
                  businessUnitCode: data.BusinessUnitCode || '',
                  entityName: data.EntityName || 'N/A',
                  entityType: data.EntityType || '',
                  location: data.Location || 'N/A',
                  departmentHead: data.DepartmentHead || 'N/A',
                  businessUnitDisplay: (data.BusinessUnitName || 'N/A') + ' (' + (data.BusinessUnitCode || '') + ')',
                  entityDisplay: (data.EntityName || 'N/A') + ' - ' + (data.EntityType || '')
                };
              }
            } catch (businessError) {
              console.error('Failed to fetch business info:', businessError);
              this.error = 'Failed to load business information. Please try again.';
            }

            // Fetch user permissions using centralized API with JWT
            console.log('Fetching user permissions for userId:', userId);
            try {
              const permissionsResponse = await api.getUserPermissions(userId);
              console.log('Permissions data received:', permissionsResponse.data);
              if (permissionsResponse.data.status === 'success') {
                this.userPermissions = permissionsResponse.data.data;
                this.initializeExpandedModules();
                
                // Check if user is GRC Administrator
                console.log('User role from API:', this.userPermissions.role);
                console.log('Role type:', typeof this.userPermissions.role);
                console.log('Role length:', this.userPermissions.role ? this.userPermissions.role.length : 'null');
                console.log('Role comparison with "GRC Administrator":', this.userPermissions.role === 'GRC Administrator');
                console.log('Role comparison with "GRC Administrator" (trimmed):', this.userPermissions.role ? this.userPermissions.role.trim() === 'GRC Administrator' : false);
                
                // More robust role checking
                const userRole = this.userPermissions.role ? this.userPermissions.role.trim() : '';
                this.isGRCAdministrator = userRole === 'GRC Administrator' || 
                                         userRole === 'grc administrator' || 
                                         userRole === 'GRC ADMINISTRATOR' ||
                                         userRole.includes('GRC Administrator') ||
                                         userRole.includes('grc administrator');
                console.log('Is GRC Administrator:', this.isGRCAdministrator);
                console.log('Visible tabs:', this.visibleTabs);
              }
            } catch (permissionsError) {
              console.error('Failed to fetch user permissions:', permissionsError);
              this.error = 'Failed to load user permissions. Please try again.';
            }
          } else {
            console.error('Failed to fetch profile:', profileResponse.data);
            this.error = 'Failed to load profile information. Please try again.';
          }
        } else {
          console.error('No user ID found');
          this.error = 'User ID not found. Please log in again.';
        }
      } catch (error) {
        console.error('Error loading user data:', error);
        this.error = 'Failed to load user data. Please try again.';
      } finally {
        this.loading = false;
      }
    },

    async savePersonalInfo() {
      this.loading = true
      this.error = null
      this.success = null

      try {
        const userData = JSON.parse(localStorage.getItem('user') || '{}')
        
        // Here you would typically send the updated data to your backend
        // For now, we'll just update localStorage
        userData.firstName = this.form.firstName
        userData.lastName = this.form.lastName
        userData.email = this.form.email
        userData.phone = this.form.phone

        localStorage.setItem('user', JSON.stringify(userData))
        localStorage.setItem('user_name', `${this.form.firstName} ${this.form.lastName}`)
        localStorage.setItem('fullName', `${this.form.firstName} ${this.form.lastName}`)
        localStorage.setItem('username', `${this.form.firstName} ${this.form.lastName}`)
        localStorage.setItem('user_email', this.form.email)

        this.success = 'Personal information updated successfully!'
        window.dispatchEvent(new Event('userDataUpdated'))

      } catch (error) {
        console.error('Error saving personal info:', error)
        this.error = 'Failed to save personal info. Please try again.'
      } finally {
        this.loading = false
      }
    },

    async saveBusinessInfo() {

  this.loading = true

  this.error = null

  this.success = null

  try {

    // Here you would typically send the updated data to your backend

    // For now, we'll just update localStorage

    const userData = JSON.parse(localStorage.getItem('user') || '{}')

    userData.departmentName = this.businessInfo.departmentName

    userData.businessUnitName = this.businessInfo.businessUnitName

    userData.entityName = this.businessInfo.entityName

    userData.location = this.businessInfo.location

    userData.departmentHead = this.businessInfo.departmentHead

    localStorage.setItem('user', JSON.stringify(userData))

    localStorage.setItem('user_name', this.form.username)

    localStorage.setItem('user_email', this.form.email)

    this.success = 'Business information updated successfully!'

    // Emit event to update sidebar username

    window.dispatchEvent(new Event('userDataUpdated'))

  } catch (error) {

    console.error('Error saving business info:', error)

    this.error = 'Failed to save business info. Please try again.'

  } finally {

    this.loading = false

  }

},

async updatePassword() {

  this.loading = true

  this.error = null

  this.success = null

      
      try {
        if (this.form.newPassword !== this.form.confirmPassword) {
          this.error = 'Passwords do not match.'
          return
        }
        
        if (this.form.newPassword.length < 6) {
          this.error = 'Password must be at least 6 characters long.'
          return
        }
        
        // Here you would typically send the password update to your backend
        // For now, we'll just show a success message
        this.success = 'Password updated successfully!'
        this.form.newPassword = ''
        this.form.confirmPassword = ''
        this.form.otp = ''
        
      } catch (error) {
        console.error('Error updating password:', error)
        this.error = 'Failed to update password. Please try again.'
      } finally {
        this.loading = false
      }
    },
    
    async saveNotificationSettings() {
      this.loading = true
      this.error = null
      this.success = null
      
      try {
        // Here you would typically send the notification settings to your backend
        // For now, we'll just show a success message
        this.success = 'Notification settings updated successfully!'
        
      } catch (error) {
        console.error('Error saving notification settings:', error)
        this.error = 'Failed to save notification settings. Please try again.'
      } finally {
        this.loading = false
      }
    },

    formatModuleName(moduleName) {
      return moduleName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    },

    getModuleIcon(moduleName) {
      switch (moduleName) {
        case 'compliance':
          return 'fas fa-clipboard-check';
        case 'policy':
          return 'fas fa-file-contract';
        case 'audit':
          return 'fas fa-tasks';
        case 'risk':
          return 'fas fa-exclamation-triangle';
        case 'incident':
          return 'fas fa-shield-alt';
        default:
          return 'fas fa-cog';
      }
    },

    formatPermissionName(permissionName) {
      return permissionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    },

    toggleModulePermissions(moduleName) {
      const index = this.expandedModules.indexOf(moduleName);
      if (index > -1) {
        this.expandedModules.splice(index, 1);
      } else {
        this.expandedModules.push(moduleName);
      }
    },

         initializeExpandedModules() {
       if (this.userPermissions.modules && Object.keys(this.userPermissions.modules).length > 0) {
         this.expandedModules = [Object.keys(this.userPermissions.modules)[0]];
       }
     },

     forceAdminMode() {
       this.isGRCAdministrator = true;
       console.log('Forced admin mode enabled');
       console.log('Visible tabs after force:', this.visibleTabs);
     },

     // Temporary method to manually set user ID for testing
     setVikramPatel() {
       sessionStorage.setItem('userId', '2');
       console.log('Set user ID to 2 (vikram.patel)');
       this.loadUserData();
     },

     toggleCreateUserForm() {
       this.showCreateUserForm = !this.showCreateUserForm;
       if (!this.showCreateUserForm) {
         this.createUserForm = {
           username: '',
           password: '',
           email: '',
           firstName: '',
           lastName: '',
           phoneNumber: '',
           address: '',
           departmentId: '',
           role: '',
           isActive: 'Y'
         };
         this.customRole = '';
         this.selectAllPermissions = false;
         this.moduleSelectAll = {};
         this.selectedPermissions = {};
         this.createUserError = null;
         this.createUserSuccess = null;
         this.showPasswordRequirements = false;
         this.passwordErrors = [];
         this.passwordChecks = {
           hasUppercase: false,
           hasLowercase: false,
           hasNumber: false,
           hasSpecialChar: false
         };
       }
     },

     toggleManageUsersForm() {
       this.showManageUsersForm = !this.showManageUsersForm;
       if (this.showManageUsersForm) {
         this.loadUsersList();
       } else {
         this.resetManageUsersForm();
       }
     },

     resetManageUsersForm() {
       this.selectedUserId = '';
       this.selectedUserName = '';
       this.selectedUserRole = '';
       this.selectedUserPermissions = null;
       this.manageUsersError = null;
       this.manageUsersSuccess = null;
       this.selectAllManagePermissions = false;
       this.moduleSelectAllManage = {};
     },

     async loadUsersList() {
       this.manageUsersLoading = true;
       this.manageUsersError = null;
       
       try {
         const response = await api.getUsers();
         if (response.data && response.data.success && response.data.users) {
           this.usersList = response.data.users;
         } else if (Array.isArray(response.data)) {
           this.usersList = response.data;
         } else {
           throw new Error('Invalid response format');
         }
       } catch (error) {
         console.error('Error loading users list:', error);
         this.manageUsersError = 'Failed to load users list. Please try again.';
         this.usersList = [];
       } finally {
         this.manageUsersLoading = false;
       }
     },

     async onUserSelected() {
       if (!this.selectedUserId) {
         this.selectedUserPermissions = null;
         this.selectedUserName = '';
         return;
       }

       this.manageUsersLoading = true;
       this.manageUsersError = null;
       this.manageUsersSuccess = null;

       try {
         // Find user name
         const selectedUser = this.usersList.find(u => u.UserId == this.selectedUserId);
         this.selectedUserName = selectedUser ? `${selectedUser.FirstName} ${selectedUser.LastName}` : '';

         // Fetch user permissions
         const response = await api.getUserPermissions(this.selectedUserId);
         
         if (response.data && response.data.status === 'success' && response.data.data) {
           const permissionsData = response.data.data;
           
           // Store the role
           this.selectedUserRole = permissionsData.role || '';
           
           // Convert permissions from module structure to flat structure
           this.selectedUserPermissions = {};
           
           // Compliance permissions
           if (permissionsData.modules && permissionsData.modules.compliance) {
             Object.assign(this.selectedUserPermissions, permissionsData.modules.compliance);
           }
           
           // Policy permissions
           if (permissionsData.modules && permissionsData.modules.policy) {
             Object.assign(this.selectedUserPermissions, permissionsData.modules.policy);
           }
           
           // Audit permissions
           if (permissionsData.modules && permissionsData.modules.audit) {
             Object.assign(this.selectedUserPermissions, permissionsData.modules.audit);
           }
           
           // Risk permissions
           if (permissionsData.modules && permissionsData.modules.risk) {
             Object.assign(this.selectedUserPermissions, permissionsData.modules.risk);
           }
           
           // Incident permissions
           if (permissionsData.modules && permissionsData.modules.incident) {
             Object.assign(this.selectedUserPermissions, permissionsData.modules.incident);
           }

           // Initialize module select all states
           this.updateModuleSelectAllStates();
         } else {
           // If no permissions found, initialize with all false
           this.initializeEmptyPermissions();
         }
       } catch (error) {
         console.error('Error loading user permissions:', error);
         this.manageUsersError = 'Failed to load user permissions. Please try again.';
         this.selectedUserPermissions = null;
       } finally {
         this.manageUsersLoading = false;
       }
     },

     initializeEmptyPermissions() {
       this.selectedUserPermissions = {};
       this.rbacModules.forEach(module => {
         module.permissions.forEach(permission => {
           this.selectedUserPermissions[permission.field] = false;
         });
       });
       this.updateModuleSelectAllStates();
     },

     updateModuleSelectAllStates() {
       this.moduleSelectAllManage = {};
       this.rbacModules.forEach(module => {
         const allChecked = module.permissions.every(permission => 
           this.selectedUserPermissions[permission.field]
         );
         this.moduleSelectAllManage[module.name] = allChecked;
       });
       
       // Update global select all
       const allPermissions = Object.values(this.selectedUserPermissions);
       this.selectAllManagePermissions = allPermissions.length > 0 && allPermissions.every(p => p);
     },

     toggleAllManagePermissions() {
       this.rbacModules.forEach(module => {
         module.permissions.forEach(permission => {
           if (this.selectedUserPermissions) {
             this.selectedUserPermissions[permission.field] = this.selectAllManagePermissions;
           }
         });
         this.moduleSelectAllManage[module.name] = this.selectAllManagePermissions;
       });
     },

     toggleModuleManagePermissions(moduleName) {
       const module = this.rbacModules.find(m => m.name === moduleName);
       if (module && this.selectedUserPermissions) {
         const isChecked = this.moduleSelectAllManage[moduleName];
         module.permissions.forEach(permission => {
           this.selectedUserPermissions[permission.field] = isChecked;
         });
         this.updateModuleSelectAllStates();
       }
     },

     updateModuleSelectAllManage(moduleName) {
       const module = this.rbacModules.find(m => m.name === moduleName);
       if (module && this.selectedUserPermissions) {
         const allChecked = module.permissions.every(permission => 
           this.selectedUserPermissions[permission.field]
         );
         this.moduleSelectAllManage[moduleName] = allChecked;
         
         // Update global select all
         const allPermissions = Object.values(this.selectedUserPermissions);
         this.selectAllManagePermissions = allPermissions.length > 0 && allPermissions.every(p => p);
       }
     },

     async saveUserPermissions() {
       if (!this.selectedUserId || !this.selectedUserPermissions) {
         this.manageUsersError = 'Please select a user first.';
         return;
       }

       this.savingPermissions = true;
       this.manageUsersError = null;
       this.manageUsersSuccess = null;

       try {
         const { API_BASE_URL } = await import('../../config/api.js');
         const axios = (await import('axios')).default;
         const accessToken = localStorage.getItem('access_token');

         const response = await axios.put(
           `${API_BASE_URL}/api/user-permissions/${this.selectedUserId}/update/`,
           {
             permissions: this.selectedUserPermissions,
             role: this.selectedUserRole
           },
           {
             headers: {
               'Authorization': `Bearer ${accessToken}`,
               'Content-Type': 'application/json'
             }
           }
         );

         if (response.data && response.data.status === 'success') {
           this.manageUsersSuccess = 'User permissions updated successfully!';
           setTimeout(() => {
             this.manageUsersSuccess = null;
           }, 3000);
         } else {
           throw new Error(response.data.message || 'Failed to update permissions');
         }
       } catch (error) {
         console.error('Error saving user permissions:', error);
         this.manageUsersError = error.response?.data?.message || 
                                error.response?.data?.error || 
                                'Failed to save permissions. Please try again.';
       } finally {
         this.savingPermissions = false;
       }
     },

     cancelManageUsers() {
       this.toggleManageUsersForm();
     },
     
     toggleAllUsersList() {
       this.showAllUsersList = !this.showAllUsersList;
       if (this.showAllUsersList) {
         this.fetchAllUsers();
       } else {
         this.allUsersList = [];
         this.allUsersError = null;
         this.allUsersSuccess = null;
       }
     },
     
     async fetchAllUsers() {
       this.loadingAllUsers = true;
       this.allUsersError = null;
       this.allUsersSuccess = null;
       
       try {
         const accessToken = localStorage.getItem('access_token');
         const headers = {
           'Content-Type': 'application/json',
           'X-Requested-With': 'XMLHttpRequest'
         };
         
         if (accessToken) {
           headers['Authorization'] = `Bearer ${accessToken}`;
         }
         
         const response = await fetch('/api/users/', {
           method: 'GET',
           headers: headers,
           credentials: 'include'
         });
         
         const result = await response.json();
         
         if (response.ok && result.success) {
           this.allUsersList = result.users || [];
           this.allUsersSuccess = `Loaded ${this.allUsersList.length} users`;
           setTimeout(() => {
             this.allUsersSuccess = null;
           }, 3000);
         } else {
           this.allUsersError = result.error || result.message || 'Failed to fetch users';
         }
       } catch (error) {
         console.error('Error fetching users:', error);
         this.allUsersError = 'Network error. Please try again.';
       } finally {
         this.loadingAllUsers = false;
       }
     },
     
     async toggleUserStatus(user) {
       this.updatingUserStatus = user.UserId;
       this.allUsersError = null;
       this.allUsersSuccess = null;
       
       // Handle both string ('Y'/'N') and boolean (true/false) values
       const isCurrentlyActive = user.IsActive === 'Y' || user.IsActive === true;
       const newStatus = isCurrentlyActive ? 'N' : 'Y';
       const oldStatus = user.IsActive;
       
       // Optimistically update UI
       user.IsActive = newStatus;
       
       try {
         const accessToken = localStorage.getItem('access_token');
         const headers = {
           'Content-Type': 'application/json',
           'X-Requested-With': 'XMLHttpRequest'
         };
         
         if (accessToken) {
           headers['Authorization'] = `Bearer ${accessToken}`;
         }
         
         const response = await fetch(`/api/users/${user.UserId}/status/`, {
           method: 'PATCH',
           headers: headers,
           credentials: 'include',
           body: JSON.stringify({
             isActive: newStatus
           })
         });
         
         const result = await response.json();
         
         if (response.ok && result.success) {
           this.allUsersSuccess = `User ${user.UserName} is now ${newStatus === 'Y' ? 'Active' : 'Inactive'}`;
           setTimeout(() => {
             this.allUsersSuccess = null;
           }, 3000);
         } else {
           this.allUsersError = result.message || result.error || 'Failed to update user status';
           // Revert the toggle
           user.IsActive = oldStatus;
         }
       } catch (error) {
         console.error('Error updating user status:', error);
         this.allUsersError = 'Network error. Please try again.';
         // Revert the toggle
         user.IsActive = oldStatus;
       } finally {
         this.updatingUserStatus = null;
       }
     },

           async createUser() {
        this.createUserLoading = true;
        this.createUserError = null;
        this.createUserSuccess = null;

        try {
          const userId = this.getCurrentUserId();
          if (!userId) {
            this.createUserError = 'User ID not found. Please log in again.';
            return;
          }

          // Check if current user is GRC Administrator
          if (!this.isGRCAdministrator) {
            this.createUserError = 'Only GRC Administrators can create users.';
            return;
          }

          const newUser = {
            username: this.createUserForm.username,
            // Password will be auto-generated by backend
            email: this.createUserForm.email,
            firstName: this.createUserForm.firstName,
            lastName: this.createUserForm.lastName,
            phoneNumber: this.createUserForm.phoneNumber,
            address: this.createUserForm.address,
            departmentId: this.createUserForm.departmentId,
            role: this.createUserForm.role === '__custom__' ? this.customRole : this.createUserForm.role,
            isActive: this.createUserForm.isActive,
            permissions: this.selectedPermissions
          };

          // Make the actual API call to create user
          console.log('Making API call to create user:', newUser);
          
          try {
            console.log('Making API call to:', '/api/register/');
            console.log('Request data:', newUser);
            console.log('Access token:', localStorage.getItem('access_token'));
            
            // Try with JWT first, then fallback to session-based auth
            let response;
            const accessToken = localStorage.getItem('access_token');
            
            if (accessToken) {
              console.log('Using JWT authentication');
              response = await fetch('/api/register/', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${accessToken}`,
                  'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(newUser)
              });
            } else {
              console.log('Using session-based authentication');
              response = await fetch('/api/register/', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include', // Include cookies for session auth
                body: JSON.stringify(newUser)
              });
            }

            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            const result = await response.json();
            console.log('API response:', result);

            if (response.ok && result.success) {
              this.createUserSuccess = 'User created successfully!';
              setTimeout(() => {
                this.toggleCreateUserForm();
              }, 2000);
            } else {
              this.createUserError = result.message || 'Failed to create user. Please try again.';
            }
          } catch (apiError) {
            console.error('API call failed:', apiError);
            this.createUserError = 'Network error. Please check your connection and try again.';
          }
          
        } catch (error) {
          console.error('Error creating user:', error);
          this.createUserError = 'Failed to create user. Please try again.';
        } finally {
          this.createUserLoading = false;
        }
      },

     cancelCreateUser() {
       this.toggleCreateUserForm();
     },

     onRoleChange() {
       if (this.createUserForm.role === '__custom__') {
         this.showCustomRoleInput = true;
       } else {
         this.showCustomRoleInput = false;
         this.customRole = '';
       }
     },

     addCustomRole() {
       if (this.customRole.trim() && this.createUserForm.role === '__custom__') {
         this.availableRoles.push(this.customRole.trim());
         this.createUserForm.role = this.customRole.trim();
         this.showCustomRoleInput = false;
       }
     },

           togglePasswordVisibility() {
        // Toggle password visibility
        this.passwordFieldType = this.passwordFieldType === 'password' ? 'text' : 'password';
      },

           toggleAllPermissions() {
        // Toggle all permissions based on selectAllPermissions
        this.rbacModules.forEach(module => {
          module.permissions.forEach(permission => {
            this.selectedPermissions[permission.field] = this.selectAllPermissions;
          });
          this.moduleSelectAll[module.name] = this.selectAllPermissions;
        });
      },

           updateModuleSelectAll(moduleName) {
        const module = this.rbacModules.find(m => m.name === moduleName);
        if (module) {
          const allChecked = module.permissions.every(permission => 
            this.selectedPermissions[permission.field]
          );
          this.moduleSelectAll[moduleName] = allChecked;
        }
      },

           async loadDepartments() {
        try {
          // For now, use mock data since we don't have the actual API
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
        } catch (error) {
          console.error('Error loading departments:', error);
        }
      },

      // Consent Configuration Methods
      async initializeConsentConfiguration() {
        // Get framework ID from storage
        this.consentFrameworkId = localStorage.getItem('framework_id') || 
                                  localStorage.getItem('selectedFrameworkId') ||
                                  sessionStorage.getItem('framework_id');
        
        if (this.consentFrameworkId) {
          this.consentFrameworkId = parseInt(this.consentFrameworkId);
          if (isNaN(this.consentFrameworkId)) {
            this.consentFrameworkId = null;
          }
        }
        
        if (this.consentFrameworkId) {
          await this.loadConsentConfigurations();
        } else {
          await this.loadConsentFrameworks();
          if (this.consentFrameworks.length > 0) {
            this.consentFrameworkId = this.consentFrameworks[0].FrameworkId;
            localStorage.setItem('framework_id', this.consentFrameworkId);
            await this.loadConsentConfigurations();
          } else {
            this.showConsentFrameworkSelector = true;
          }
        }
      },

      async loadConsentFrameworks() {
        try {
          this.loadingConsentFrameworks = true;
          const { API_BASE_URL } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
          
          const response = await axios.get(`${API_BASE_URL}/api/frameworks/`, {
            headers: this.getConsentAuthHeaders()
          });
          
          if (response.data && Array.isArray(response.data)) {
            this.consentFrameworks = response.data.filter(f => f.Status === 'Approved' && f.ActiveInactive === 'Active');
          }
        } catch (error) {
          console.error('Error loading frameworks:', error);
          this.showConsentMessage('Failed to load frameworks', 'error');
        } finally {
          this.loadingConsentFrameworks = false;
        }
      },

      onConsentFrameworkChange() {
        if (this.consentFrameworkId) {
          localStorage.setItem('framework_id', this.consentFrameworkId);
          this.showConsentFrameworkSelector = false;
          this.loadConsentConfigurations();
        }
      },

      async loadConsentConfigurations() {
        if (!this.consentFrameworkId) {
          await this.loadConsentFrameworks();
          this.showConsentFrameworkSelector = true;
          return;
        }

        try {
          this.loadingConsentConfigs = true;
          const { API_BASE_URL } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
          
          const userId = this.getCurrentUserId(); // Get current user ID for created_by
          
          const response = await axios.get(`${API_BASE_URL}/api/consent/configurations/`, {
            params: { 
              framework_id: this.consentFrameworkId,
              created_by: userId // Send user ID so backend can set created_by when creating defaults
            },
            headers: this.getConsentAuthHeaders()
          });

          if (response.data.status === 'success') {
            this.consentConfigurations = response.data.data;
            this.consentConfigurations.sort((a, b) => a.action_label.localeCompare(b.action_label));
            this.consentModifiedConfigs.clear();
          } else {
            this.showConsentMessage(response.data.message || 'Failed to load consent configurations', 'error');
          }
        } catch (error) {
          console.error('Error loading consent configurations:', error);
          const errorMsg = error.response?.data?.message || 'Failed to load consent configurations';
          this.showConsentMessage(errorMsg, 'error');
          
          if (error.response?.status === 400 && errorMsg.includes('framework_id')) {
            await this.loadConsentFrameworks();
            this.showConsentFrameworkSelector = true;
          }
        } finally {
          this.loadingConsentConfigs = false;
        }
      },

      markConsentConfigAsModified(config) {
        this.consentModifiedConfigs.add(config.config_id);
      },

      async saveAllConsentConfigurations() {
        if (this.consentModifiedConfigs.size === 0) {
          this.showConsentMessage('No changes to save', 'info');
          return;
        }

        try {
          this.savingConsentConfigs = true;
          const { API_BASE_URL } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
          const userId = this.getCurrentUserId();
          
          const configsToUpdate = this.consentConfigurations
            .filter(c => this.consentModifiedConfigs.has(c.config_id))
            .map(c => ({
              config_id: c.config_id,
              is_enabled: c.is_enabled,
              consent_text: c.consent_text
            }));

          const response = await axios.put(
            `${API_BASE_URL}/api/consent/configurations/bulk-update/`,
            {
              configs: configsToUpdate,
              updated_by: userId
            },
            { headers: this.getConsentAuthHeaders() }
          );

          if (response.data.status === 'success') {
            this.showConsentMessage('Consent configurations saved successfully', 'success');
            this.consentModifiedConfigs.clear();
            await this.loadConsentConfigurations();
          } else {
            throw new Error(response.data.message || 'Failed to save configurations');
          }
        } catch (error) {
          console.error('Error saving consent configurations:', error);
          const errorMessage = error.response?.data?.message || 
                              error.response?.data?.error ||
                              error.message || 
                              'Failed to save consent configurations. Please try again.';
          this.showConsentMessage(errorMessage, 'error');
        } finally {
          this.savingConsentConfigs = false;
        }
      },

      getConsentActionIcon(actionType) {
        const iconMap = {
          'create_policy': 'fas fa-file-alt',
          'create_compliance': 'fas fa-clipboard-check',
          'create_audit': 'fas fa-search',
          'create_incident': 'fas fa-exclamation-triangle',
          'create_risk': 'fas fa-shield-alt',
          'create_event': 'fas fa-calendar-alt',
          'upload_policy': 'fas fa-upload',
          'upload_audit': 'fas fa-upload',
          'upload_incident': 'fas fa-upload',
          'upload_risk': 'fas fa-upload',
          'upload_event': 'fas fa-upload'
        };
        return iconMap[actionType] || 'fas fa-cog';
      },

      formatConsentDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'short', 
          day: 'numeric' 
        });
      },

      showConsentMessage(msg, type = 'success') {
        this.consentMessage = msg;
        this.consentMessageType = type;
        setTimeout(() => {
          this.consentMessage = '';
        }, 5000);
      },
      async loadDataSubjectRequests() {
        this.loadingRequests = true;
        this.requestsError = null;
       
        try {
          const userId = this.getCurrentUserId();
          if (!userId) {
            throw new Error('User ID not found');
          }
          
          const { API_BASE_URL } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
          
          const response = await axios.get(
            `${API_BASE_URL}/api/data-subject-requests/${userId}/`,
            { headers: this.getConsentAuthHeaders() }
          );
          
          if (response.data.status === 'success') {
            this.dataSubjectRequests = response.data.data || [];
          } else {
            throw new Error(response.data.message || 'Failed to load requests');
          }
        } catch (error) {
          console.error('Error loading data subject requests:', error);
          this.requestsError = error.response?.data?.message ||
                             error.response?.data?.error ||
                             error.message ||
                             'Failed to load data subject requests. Please try again.';
        } finally {
          this.loadingRequests = false;
        }
      },
      
      async loadTprmAccessRequests() {
        this.loadingTprmRequests = true;
        this.tprmRequestsError = null;
       
        try {
          const userId = this.getCurrentUserId();
          if (!userId) {
            throw new Error('User ID not found');
          }
          
          const { API_ENDPOINTS } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
          
          console.log('🔵 [UserProfile] Loading TPRM access requests for user:', userId);
          console.log('🔵 [UserProfile] API Endpoint:', API_ENDPOINTS.TPRM_ACCESS_REQUESTS(userId));
          
          const response = await axios.get(
            API_ENDPOINTS.TPRM_ACCESS_REQUESTS(userId),
            { headers: this.getConsentAuthHeaders() }
          );
          
          console.log('🔵 [UserProfile] TPRM access requests response:', response.data);
          
          if (response.data.status === 'success') {
            const rawRequests = response.data.data || [];
            console.log('🔵 [UserProfile] Raw TPRM requests received:', rawRequests.length, rawRequests);
            
            // Transform TPRM requests to match GRC request format
            this.tprmAccessRequests = rawRequests.map(req => {
              // Build user name from available fields
              let userName = 'N/A';
              if (req.UserName) {
                userName = req.UserName;
              } else if (req.FirstName || req.LastName) {
                userName = `${req.FirstName || ''} ${req.LastName || ''}`.trim();
              } else if (req.user_id) {
                userName = `User ${req.user_id}`;
              }
              
              // Build approver name
              let approvedByName = null;
              if (req.ApproverFirstName && req.ApproverLastName) {
                approvedByName = `${req.ApproverFirstName} ${req.ApproverLastName}`;
              } else if (req.ApproverFirstName) {
                approvedByName = req.ApproverFirstName;
              }
              
              const transformed = {
                ...req,
                request_type: 'ACCESS',
                request_type_display: 'TPRM Access',
                status_display: req.status === 'APPROVED' ? 'Approved' : 
                              req.status === 'REJECTED' ? 'Rejected' : 'Requested',
                verification_status: 'N/A',
                verification_status_display: 'N/A',
                user_name: userName,
                approved_by_name: approvedByName
              };
              
              console.log('🔵 [UserProfile] Transformed TPRM request:', {
                id: transformed.id,
                user_id: transformed.user_id,
                status: transformed.status,
                user_name: transformed.user_name
              });
              
              return transformed;
            });
            
            console.log('🔵 [UserProfile] Total TPRM access requests loaded:', this.tprmAccessRequests.length);
            console.log('🔵 [UserProfile] Combined requests (GRC + TPRM):', 
              this.dataSubjectRequests.length + this.tprmAccessRequests.length);
          } else {
            throw new Error(response.data.message || 'Failed to load TPRM requests');
          }
        } catch (error) {
          console.error('🔴 [UserProfile] Error loading TPRM access requests:', error);
          console.error('🔴 [UserProfile] Error details:', {
            status: error.response?.status,
            message: error.response?.data?.message,
            url: error.config?.url
          });
          
          // Don't show error if endpoint doesn't exist or table doesn't exist yet
          if (error.response?.status !== 404 && error.response?.status !== 500) {
            this.tprmRequestsError = error.response?.data?.message ||
                                   error.response?.data?.error ||
                                   error.message ||
                                   'Failed to load TPRM access requests. Please try again.';
          } else {
            // Silently fail if table doesn't exist yet
            this.tprmAccessRequests = [];
            console.warn('🔴 [UserProfile] TPRM access requests endpoint returned 404/500, assuming table does not exist yet');
          }
        } finally {
          this.loadingTprmRequests = false;
        }
      },
     
      formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
          const date = new Date(dateString);
          return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        } catch (e) {
          return 'Invalid Date';
        }
      },
     
      viewRequestDetails(request) {
        this.selectedRequest = request;
        this.showRequestDetailsModal = true;
        // Debug: Log the request data to console
        console.log('Viewing request details:', {
          id: request.id,
          request_type: request.request_type,
          audit_trail: request.audit_trail,
          info_type: request.audit_trail?.info_type,
          has_impact_analysis: !!request.audit_trail?.impact_analysis,
          impact_analysis: request.audit_trail?.impact_analysis
        });
      },
     
      closeRequestDetailsModal() {
        this.showRequestDetailsModal = false;
        this.selectedRequest = null;
      },
     
      async handleApproveRequest(requestId) {
        await this.updateRequestStatus(requestId, 'APPROVED', true);
      },
     
      async handleRejectRequest(requestId) {
        await this.updateRequestStatus(requestId, 'REJECTED', false);
      },
     
      async updateRequestStatus(requestId, status, applyChanges = false) {
        this.processingRequestId = requestId;
        try {
          const userId = this.getCurrentUserId();
          if (!userId) {
            throw new Error('User ID not found');
          }
          
          // Check if this is a TPRM request
          const tprmRequest = this.tprmAccessRequests.find(r => r.id === requestId);
          const isTprmRequest = !!tprmRequest;
          
          const { API_BASE_URL, API_ENDPOINTS } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
          
          const endpoint = isTprmRequest 
            ? API_ENDPOINTS.TPRM_UPDATE_ACCESS_REQUEST_STATUS(requestId)
            : `${API_BASE_URL}/api/data-subject-requests/${requestId}/update-status/`;
          
          const requestBody = isTprmRequest
            ? { status: status }
            : {
                status: status,
                user_id: userId,
                apply_changes: applyChanges
              };
          
          const response = await axios.put(
            endpoint,
            requestBody,
            { headers: this.getConsentAuthHeaders() }
          );
          
          if (response.data.status === 'success') {
            // Update the request in the local array
            if (isTprmRequest) {
              const requestIndex = this.tprmAccessRequests.findIndex(r => r.id === requestId);
              if (requestIndex !== -1) {
                this.tprmAccessRequests[requestIndex].status = status;
                this.tprmAccessRequests[requestIndex].status_display = status === 'APPROVED' ? 'Approved' : (status === 'REJECTED' ? 'Rejected' : 'Requested');
                this.tprmAccessRequests[requestIndex].updated_at = new Date().toISOString();
              }
            } else {
              const requestIndex = this.dataSubjectRequests.findIndex(r => r.id === requestId);
              if (requestIndex !== -1) {
                this.dataSubjectRequests[requestIndex].status = status;
                this.dataSubjectRequests[requestIndex].status_display = status === 'APPROVED' ? 'Approved' : (status === 'REJECTED' ? 'Rejected' : 'Requested');
                this.dataSubjectRequests[requestIndex].updated_at = new Date().toISOString();
              }
            }
            
            // Close the modal if open
            if (this.showRequestDetailsModal) {
              this.closeRequestDetailsModal();
            }
            
            // Reload requests to get updated data
            await this.loadDataSubjectRequests();
            if (isTprmRequest) {
              await this.loadTprmAccessRequests();
              
              // If approved, clear frontend permission cache to ensure fresh permission checks
              if (status === 'APPROVED') {
                try {
                  // Clear TPRM permission cache
                  // The permissionsService is in tprm_frontend, which is a sibling directory
                  // From grc_frontend/src/components/Login/ to grc_frontend/tprm_frontend/src/services/
                  // ../../.. = src/components/Login -> src -> grc_frontend
                  const permissionsServiceModule = await import('../../../tprm_frontend/src/services/permissionsService.js');
                  const permissionsService = permissionsServiceModule.default || permissionsServiceModule;
                  
                  if (permissionsService) {
                    // Clear all permission cache
                    if (typeof permissionsService.clearCache === 'function') {
                      permissionsService.clearCache();
                      console.log('🔵 [UserProfile] Cleared TPRM permission cache after approval');
                    }
                    
                    // Also clear any vendor-specific cache for the user who was granted access
                    if (typeof permissionsService.clearCacheForUser === 'function') {
                      const requestUserId = tprmRequest.user_id || tprmRequest.UserId;
                      if (requestUserId) {
                        permissionsService.clearCacheForUser(requestUserId);
                        console.log(`🔵 [UserProfile] Cleared permission cache for user ${requestUserId} after approval`);
                      }
                    }
                  }
                } catch (cacheError) {
                  console.warn('🔵 [UserProfile] Could not clear permission cache (non-critical):', cacheError.message);
                  // Non-critical error, continue - the backend will still work with force_refresh=True
                }
              }
            }
            
            // Show success message
            const statusDisplay = status === 'APPROVED' ? 'approved and changes applied' : (status === 'REJECTED' ? 'rejected' : 'updated');
            this.success = `Request ${statusDisplay} successfully`;
            setTimeout(() => {
              this.success = null;
            }, 3000);
          } else {
            throw new Error(response.data.message || 'Failed to update request');
          }
        } catch (error) {
          console.error(`Error ${status.toLowerCase()}ing request:`, error);
          this.error = error.response?.data?.message ||
                      error.response?.data?.error ||
                      error.message ||
                      `Failed to ${status.toLowerCase()} request. Please try again.`;
          setTimeout(() => {
            this.error = null;
          }, 5000);
        } finally {
          this.processingRequestId = null;
        }
      },
 
      getConsentAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };
      },
      
      // Data Retention Configuration Methods
      onRetentionConfigsSaved(configs) {
        if (configs.modules) {
          this.retentionModuleConfigs = configs.modules;
          console.log('Retention module configs saved:', configs.modules);
        }
        if (configs.pages) {
          this.retentionPageConfigs = configs.pages;
          console.log('Retention page configs saved:', configs.pages);
        }
      },

      // Access Requests Methods
     
     // Edit mode methods
     async enableEditMode(type) {
       if (type === 'personal') {
         // Check if OTP verification is required and not yet verified
         const isVerified = await this.checkProfileEditVerification();
         if (!isVerified) {
           // Show OTP modal
           this.pendingEditType = 'personal';
           this.showOtpModal = true;
           this.otpStep = 'send';
           this.otpError = null;
           this.otpSuccess = null;
           return;
         }
         
         // Store original values
         this.originalPersonalData = {
           firstName: this.form.firstName,
           lastName: this.form.lastName,
           email: this.form.email,
          phone: this.form.phone || '',
          address: this.form.address || ''
         };
         this.editModePersonal = true;
       } else if (type === 'business') {
         // Store original values
         this.originalBusinessData = {
           departmentName: this.businessInfo.departmentName || '',
           businessUnitName: this.businessInfo.businessUnitName || '',
           businessUnitCode: this.businessInfo.businessUnitCode || '',
           entityName: this.businessInfo.entityName || '',
           entityType: this.businessInfo.entityType || '',
           location: this.businessInfo.location || '',
           departmentHead: this.businessInfo.departmentHead || ''
         };
         // Ensure display fields are initialized
         if (!this.businessInfo.businessUnitDisplay) {
           this.businessInfo.businessUnitDisplay = (this.businessInfo.businessUnitName || 'N/A') + ' (' + (this.businessInfo.businessUnitCode || '') + ')';
         }
         if (!this.businessInfo.entityDisplay) {
           this.businessInfo.entityDisplay = (this.businessInfo.entityName || 'N/A') + ' - ' + (this.businessInfo.entityType || '');
         }
         this.editModeBusiness = true;
       }
     },
    
     cancelEditMode(type) {
       if (type === 'personal') {
         // Restore original values
         this.form.firstName = this.originalPersonalData.firstName;
         this.form.lastName = this.originalPersonalData.lastName;
         this.form.email = this.originalPersonalData.email;
         this.form.phone = this.originalPersonalData.phone;
         this.form.address = this.originalPersonalData.address;
         this.editModePersonal = false;
         this.originalPersonalData = {};
       } else if (type === 'business') {
         // Restore original values
         this.businessInfo.departmentName = this.originalBusinessData.departmentName;
         this.businessInfo.businessUnitName = this.originalBusinessData.businessUnitName;
         this.businessInfo.businessUnitCode = this.originalBusinessData.businessUnitCode;
         this.businessInfo.entityName = this.originalBusinessData.entityName;
         this.businessInfo.entityType = this.originalBusinessData.entityType;
         this.businessInfo.location = this.originalBusinessData.location;
         this.businessInfo.departmentHead = this.originalBusinessData.departmentHead;
         this.businessInfo.businessUnitDisplay = this.originalBusinessData.businessUnitName + ' (' + this.originalBusinessData.businessUnitCode + ')';
         this.businessInfo.entityDisplay = this.originalBusinessData.entityName + ' - ' + this.originalBusinessData.entityType;
         this.editModeBusiness = false;
         this.originalBusinessData = {};
       }
     },
    
     hasPersonalChanges() {
       if (!this.editModePersonal) return false;
       return (
         this.form.firstName !== this.originalPersonalData.firstName ||
         this.form.lastName !== this.originalPersonalData.lastName ||
         this.form.email !== this.originalPersonalData.email ||
         (this.form.phone || '') !== (this.originalPersonalData.phone || '') ||
         (this.form.address || '') !== (this.originalPersonalData.address || '')
       );
     },
    
     hasBusinessChanges() {
       if (!this.editModeBusiness) return false;
       // Check if display fields have changed (they contain the editable values)
       const currentDisplay = {
         departmentName: this.businessInfo.departmentName || '',
         businessUnitDisplay: this.businessInfo.businessUnitDisplay || '',
         entityDisplay: this.businessInfo.entityDisplay || '',
         location: this.businessInfo.location || '',
         departmentHead: this.businessInfo.departmentHead || ''
       };
       const originalDisplay = {
         departmentName: this.originalBusinessData.departmentName || '',
         businessUnitDisplay: (this.originalBusinessData.businessUnitName || 'N/A') + ' (' + (this.originalBusinessData.businessUnitCode || '') + ')',
         entityDisplay: (this.originalBusinessData.entityName || 'N/A') + ' - ' + (this.originalBusinessData.entityType || ''),
         location: this.originalBusinessData.location || '',
         departmentHead: this.originalBusinessData.departmentHead || ''
       };
       return (
         currentDisplay.departmentName !== originalDisplay.departmentName ||
         currentDisplay.businessUnitDisplay !== originalDisplay.businessUnitDisplay ||
         currentDisplay.entityDisplay !== originalDisplay.entityDisplay ||
         currentDisplay.location !== originalDisplay.location ||
         currentDisplay.departmentHead !== originalDisplay.departmentHead
       );
     },
    
     getChanges() {
       const changes = {};
       if (this.currentEditType === 'personal' && this.editModePersonal) {
         if (this.form.firstName !== this.originalPersonalData.firstName) {
           changes.firstName = {
             old: this.originalPersonalData.firstName,
             new: this.form.firstName
           };
         }
         if (this.form.lastName !== this.originalPersonalData.lastName) {
           changes.lastName = {
             old: this.originalPersonalData.lastName,
             new: this.form.lastName
           };
         }
         if (this.form.email !== this.originalPersonalData.email) {
           changes.email = {
             old: this.originalPersonalData.email,
             new: this.form.email
           };
         }
         if ((this.form.phone || '') !== (this.originalPersonalData.phone || '')) {
           changes.phone = {
             old: this.originalPersonalData.phone || '',
             new: this.form.phone || ''
           };
         }
         if ((this.form.address || '') !== (this.originalPersonalData.address || '')) {
           changes.address = {
             old: this.originalPersonalData.address || '',
             new: this.form.address || ''
           };
         }
       } else if (this.currentEditType === 'business' && this.editModeBusiness) {
         const current = {
           departmentName: this.businessInfo.departmentName || '',
           businessUnitDisplay: this.businessInfo.businessUnitDisplay || '',
           entityDisplay: this.businessInfo.entityDisplay || '',
           location: this.businessInfo.location || '',
           departmentHead: this.businessInfo.departmentHead || ''
         };
         const original = {
           departmentName: this.originalBusinessData.departmentName || '',
           businessUnitDisplay: (this.originalBusinessData.businessUnitName || 'N/A') + ' (' + (this.originalBusinessData.businessUnitCode || '') + ')',
           entityDisplay: (this.originalBusinessData.entityName || 'N/A') + ' - ' + (this.originalBusinessData.entityType || ''),
           location: this.originalBusinessData.location || '',
           departmentHead: this.originalBusinessData.departmentHead || ''
         };
        
         if (current.departmentName !== original.departmentName) {
           changes.departmentName = {
             old: original.departmentName,
             new: current.departmentName
           };
         }
         if (current.businessUnitDisplay !== original.businessUnitDisplay) {
           changes.businessUnit = {
             old: original.businessUnitDisplay,
             new: current.businessUnitDisplay
           };
         }
         if (current.entityDisplay !== original.entityDisplay) {
           changes.entity = {
             old: original.entityDisplay,
             new: current.entityDisplay
           };
         }
         if (current.location !== original.location) {
           changes.location = {
             old: original.location,
             new: current.location
           };
         }
         if (current.departmentHead !== original.departmentHead) {
           changes.departmentHead = {
             old: original.departmentHead,
             new: current.departmentHead
           };
         }
       }
       return changes;
     },
    
     getInfoTypeClass(infoType) {
       if (!infoType) return 'info-type-personal';
       if (infoType === 'personal') return 'info-type-personal';
       if (infoType === 'business') return 'info-type-business';
       if (infoType === 'risk') return 'info-type-risk';
       if (infoType === 'risk_instance') return 'info-type-risk-instance';
       return 'info-type-personal';
     },
     
     getInfoTypeIcon(infoType) {
       if (!infoType) return 'fas fa-user';
       if (infoType === 'personal') return 'fas fa-user';
       if (infoType === 'business') return 'fas fa-building';
       if (infoType === 'risk') return 'fas fa-exclamation-triangle';
       if (infoType === 'risk_instance') return 'fas fa-file-alt';
       return 'fas fa-user';
     },
     
     getInfoTypeLabel(infoType) {
       if (!infoType) return 'Personal Information';
       if (infoType === 'personal') return 'Personal Information';
       if (infoType === 'business') return 'Business Information';
       if (infoType === 'risk') return 'Risk Information';
       if (infoType === 'risk_instance') return 'Risk Instance Information';
       return 'Personal Information';
     },
     
     formatFieldName(field) {
       const fieldNames = {
         firstName: 'First Name',
         lastName: 'Last Name',
         email: 'Email',
         phone: 'Phone Number',
         departmentName: 'Department',
         businessUnit: 'Business Unit',
         businessUnitName: 'Business Unit Name',
         businessUnitCode: 'Business Unit Code',
         entity: 'Entity',
         entityName: 'Entity Name',
         entityType: 'Entity Type',
         location: 'Location',
         departmentHead: 'Department Head'
       };
       return fieldNames[field] || field;
     },
     
     getRequestRiskLevel(request) {
       if (request.audit_trail?.impact_analysis?.riskLevel) {
         return request.audit_trail.impact_analysis.riskLevel;
       }
       return null;
     },
     
     getRequestRowClass(request) {
       const riskLevel = this.getRequestRiskLevel(request);
       if (!riskLevel) return '';
       return `risk-row-${riskLevel.toLowerCase()}`;
     },
     
     async exportImpactAnalysis() {
       if (!this.selectedRequest || !this.selectedRequest.audit_trail?.impact_analysis) {
         return;
       }
       
       this.exportingImpactAnalysis = true;
       try {
         const impactAnalysis = this.selectedRequest.audit_trail.impact_analysis;
         const request = this.selectedRequest;
         
         // Create HTML content for PDF
         const htmlContent = `
           <!DOCTYPE html>
           <html>
           <head>
             <meta charset="UTF-8">
             <title>Impact Analysis Report - Request ${request.id}</title>
             <style>
               body {
                 font-family: Arial, sans-serif;
                 padding: 40px;
                 color: #1e293b;
                 line-height: 1.6;
               }
               .header {
                 border-bottom: 3px solid #3b82f6;
                 padding-bottom: 20px;
                 margin-bottom: 30px;
               }
               .header h1 {
                 color: #1e293b;
                 margin: 0;
                 font-size: 28px;
               }
               .header-info {
                 margin-top: 10px;
                 color: #6b7280;
                 font-size: 14px;
               }
               .risk-level-badge {
                 display: inline-block;
                 padding: 8px 16px;
                 border-radius: 6px;
                 font-weight: 600;
                 margin: 20px 0;
               }
               .risk-level-high {
                 background: #fee2e2;
                 color: #991b1b;
                 border: 2px solid #dc2626;
               }
               .risk-level-medium {
                 background: #fef3c7;
                 color: #92400e;
                 border: 2px solid #f59e0b;
               }
               .risk-level-low {
                 background: #d1fae5;
                 color: #065f46;
                 border: 2px solid #10b981;
               }
               .section {
                 margin-bottom: 30px;
                 padding: 20px;
                 background: #f9fafb;
                 border-radius: 8px;
                 border-left: 4px solid #3b82f6;
               }
               .section h3 {
                 color: #1e293b;
                 margin-top: 0;
                 font-size: 18px;
                 border-bottom: 2px solid #e5e7eb;
                 padding-bottom: 10px;
               }
               .section ul {
                 margin: 10px 0;
                 padding-left: 20px;
               }
               .section li {
                 margin: 8px 0;
               }
               .report-item {
                 display: flex;
                 justify-content: space-between;
                 padding: 10px;
                 background: white;
                 margin: 5px 0;
                 border-radius: 4px;
               }
               .warning-box {
                 background: #fef3c7;
                 border: 2px solid #fbbf24;
                 padding: 15px;
                 border-radius: 8px;
                 margin: 20px 0;
               }
               .footer {
                 margin-top: 40px;
                 padding-top: 20px;
                 border-top: 2px solid #e5e7eb;
                 text-align: center;
                 color: #6b7280;
                 font-size: 12px;
               }
             </style>
           </head>
           <body>
             <div class="header">
               <h1>Impact Analysis Report</h1>
               <div class="header-info">
                 <strong>Request ID:</strong> ${request.id} | 
                 <strong>Request Type:</strong> ${request.request_type_display} | 
                 <strong>Info Type:</strong> ${request.audit_trail?.info_type || 'N/A'} | 
                 <strong>Generated:</strong> ${new Date().toLocaleString()}
               </div>
             </div>
             
             <div style="text-align: center;">
               <div class="risk-level-badge risk-level-${impactAnalysis.riskLevel?.toLowerCase() || 'medium'}">
                 Risk Level: ${impactAnalysis.riskLevel || 'Medium'}
               </div>
             </div>
             
             ${impactAnalysis.affectedModules && impactAnalysis.affectedModules.length > 0 ? `
             <div class="section">
               <h3>Affected Modules</h3>
               <ul>
                 ${impactAnalysis.affectedModules.map(m => `<li><strong>${m}</strong></li>`).join('')}
               </ul>
             </div>
             ` : ''}
             
             ${impactAnalysis.affectedUsers && impactAnalysis.affectedUsers.length > 0 ? `
             <div class="section">
               <h3>Affected Users</h3>
               <ul>
                 ${impactAnalysis.affectedUsers.map(u => `<li><strong>${u}</strong></li>`).join('')}
               </ul>
             </div>
             ` : ''}
             
             ${impactAnalysis.dependencies && impactAnalysis.dependencies.length > 0 ? `
             <div class="section">
               <h3>Dependencies</h3>
               <ul>
                 ${impactAnalysis.dependencies.map(d => `<li><strong>${d}</strong></li>`).join('')}
               </ul>
             </div>
             ` : ''}
             
             <div class="section">
               <h3>Impact Report</h3>
               <div class="report-item">
                 <span><strong>Affected Components:</strong></span>
                 <span>${impactAnalysis.affectedComponents?.length || 0}</span>
               </div>
               <div class="report-item">
                 <span><strong>Estimated Impact:</strong></span>
                 <span>${impactAnalysis.estimatedImpact || 'N/A'}</span>
               </div>
               <div class="report-item">
                 <span><strong>Risk Assessment:</strong></span>
                 <span>${impactAnalysis.riskAssessment || 'N/A'}</span>
               </div>
             </div>
             
             ${impactAnalysis.recommendations && impactAnalysis.recommendations.length > 0 ? `
             <div class="section">
               <h3>Recommendations</h3>
               <ul>
                 ${impactAnalysis.recommendations.map((r) => `<li>${r}</li>`).join('')}
               </ul>
             </div>
             ` : ''}
             
             ${impactAnalysis.highRiskAreas && impactAnalysis.highRiskAreas.length > 0 ? `
             <div class="warning-box">
               <h3 style="margin-top: 0; color: #92400e;">⚠ High-Risk Areas Detected</h3>
               <ul>
                 ${impactAnalysis.highRiskAreas.map(a => `<li>${a}</li>`).join('')}
               </ul>
             </div>
             ` : ''}
             
             ${impactAnalysis.mitigationSteps && impactAnalysis.mitigationSteps.length > 0 ? `
             <div class="section">
               <h3>Suggested Mitigation Steps</h3>
               <ol>
                 ${impactAnalysis.mitigationSteps.map((s, i) => `<li><strong>Step ${i + 1}:</strong> ${s}</li>`).join('')}
               </ol>
             </div>
             ` : ''}
             
             <div class="footer">
               <p>This report was generated automatically by the GRC System</p>
               <p>For questions or concerns, please contact the system administrator</p>
             </div>
           </body>
           </html>
         `;
         
         // Create blob and download
         const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
         const url = URL.createObjectURL(blob);
         const link = document.createElement('a');
         link.href = url;
         link.download = `impact-analysis-request-${request.id}-${new Date().toISOString().split('T')[0]}.html`;
         document.body.appendChild(link);
         link.click();
         document.body.removeChild(link);
         URL.revokeObjectURL(url);
         
         // Show success message
         this.success = 'Impact Analysis exported successfully!';
         setTimeout(() => {
           this.success = null;
         }, 3000);
       } catch (error) {
         console.error('Error exporting impact analysis:', error);
         this.error = 'Failed to export impact analysis. Please try again.';
         setTimeout(() => {
           this.error = null;
         }, 5000);
       } finally {
         this.exportingImpactAnalysis = false;
       }
     },
    
     openRectificationModal(type) {
       this.currentEditType = type;
       this.showRectificationModal = true;
     },
    
     closeRectificationModal() {
       this.showRectificationModal = false;
     },
    
     async submitRectificationRequest() {
       this.submittingRectification = true;
       try {
         const userId = this.getCurrentUserId();
         if (!userId) {
           this.error = 'User ID not found. Please log in again.';
           return;
         }
        
         const changes = this.getChanges();
         if (Object.keys(changes).length === 0) {
           this.error = 'No changes detected.';
           this.submittingRectification = false;
           return;
         }
        
         const { API_BASE_URL } = await import('../../config/api.js');
         const axios = (await import('axios')).default;
        
         const response = await axios.post(
           `${API_BASE_URL}/api/data-subject-requests/create/`,
           {
             request_type: 'RECTIFICATION',
             info_type: this.currentEditType,
             changes: changes
           },
           { headers: this.getConsentAuthHeaders() }
         );
        
         if (response.data.status === 'success') {
           this.success = 'Rectification request submitted successfully!';
           this.closeRectificationModal();
          
           // Exit edit mode
           if (this.currentEditType === 'personal') {
             this.editModePersonal = false;
             this.originalPersonalData = {};
           } else {
             this.editModeBusiness = false;
             this.originalBusinessData = {};
           }
          
           // Reload requests if on requests tab
           if (this.activeTab === 'requests') {
             this.loadDataSubjectRequests();
        this.loadTprmAccessRequests();
           }
          
           setTimeout(() => {
             this.success = null;
           }, 5000);
         } else {
           throw new Error(response.data.message || 'Failed to submit request');
         }
       } catch (error) {
         console.error('Error submitting rectification request:', error);
         this.error = error.response?.data?.message ||
                     error.response?.data?.error ||
                     error.message ||
                     'Failed to submit rectification request. Please try again.';
         setTimeout(() => {
           this.error = null;
         }, 5000);
       } finally {
         this.submittingRectification = false;
       }
     }
 }
}
</script>



<style scoped>
@import './UserProfile.css';

.password-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.reset-password-section {
  margin-bottom: 1rem;
}

.reset-password-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.reset-password-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.reset-password-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.reset-password-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  flex-shrink: 0;
}

.reset-password-info {
  flex: 1;
}

.reset-password-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.reset-password-info p {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
}

.reset-password-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.reset-password-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.reset-password-btn:active {
  transform: translateY(0);
}

.password-divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 2rem 0;
  color: #9ca3af;
  font-size: 0.875rem;
  font-weight: 500;
}

.password-divider::before,
.password-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #e5e7eb;
}

.password-divider span {
  padding: 0 1rem;
}

.section-subtitle {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.password-requirements {
  margin-top: 8px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.password-requirements.has-errors {
  background: #fef2f2;
  border: 1px solid #fecaca;
}

/* OTP Modal Styles */
.otp-modal {
  max-width: 500px;
}

.otp-description {
  color: #6b7280;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.otp-step {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.otp-instruction {
  color: #374151;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.otp-input-container {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin: 1.5rem 0;
}

.otp-input {
  width: 50px;
  height: 60px;
  text-align: center;
  font-size: 1.5rem;
  font-weight: 600;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.otp-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.otp-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.disabled-input {
  background: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 6px;
}

.requirement-item:last-child {
  margin-bottom: 0;
}

.requirement-item svg {
  flex-shrink: 0;
  color: #9ca3af;
}

.requirement-item.valid {
  color: #10b981;
  font-weight: 500;
}

.requirement-item.valid svg {
  color: #10b981;
  stroke: #10b981;
}

.password-input-wrapper input.invalid {
  border-color: #ef4444;
}
/* All Users List Styles */
.all-users-list-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.all-users-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.all-users-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.all-users-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.users-table-container {
  overflow-x: auto;
  margin-top: 1.5rem;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.users-table thead {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
}

.users-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.users-table td {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.users-table tbody tr:hover {
  background: #f9fafb;
}

.users-table tbody tr.inactive-user {
  opacity: 0.7;
  background: #fef2f2;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.status-toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
  margin-right: 8px;
}

.status-toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.status-toggle-switch .slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #cbd5e1;
  transition: 0.3s;
  border-radius: 24px;
}

.status-toggle-switch .slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.status-toggle-switch input:checked + .slider {
  background-color: #10b981;
}

.status-toggle-switch input:checked + .slider:before {
  transform: translateX(26px);
}

.status-toggle-switch input:disabled + .slider {
  opacity: 0.5;
  cursor: not-allowed;
}

.updating-indicator {
  display: inline-block;
  margin-left: 8px;
  color: #6366f1;
}

.loading-users {
  text-align: center;
  padding: 3rem;
}

.loading-users .spinner {
  border: 3px solid #f3f4f6;
  border-top: 3px solid #6366f1;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-users-message {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.no-users-message i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #d1d5db;
}

.user-management-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

</style>