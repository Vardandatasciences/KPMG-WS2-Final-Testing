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
              <h2 class="section-title"><i class="fas fa-user"></i> Personal Information</h2>
              <p class="section-helper">Update your personal details and contact information.</p>
              
              <div class="form-row">
                <div class="form-group">
                  <label>First Name:</label>
                  <input type="text" v-model="form.firstName" :disabled="loading" />
                </div>
                <div class="form-group">
                  <label>Last Name:</label>
                  <input type="text" v-model="form.lastName" :disabled="loading" />
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label>Email:</label>
                  <input type="email" v-model="form.email" :disabled="loading" />
                </div>
                <div class="form-group">
                  <label>Phone Number:</label>
                  <input type="text" v-model="form.phone" :disabled="loading" />
                </div>
              </div>
              
              <div class="form-row center">
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
              <h2 class="section-title"><i class="fas fa-building"></i> Business Information</h2>
              <p class="section-helper">View your organizational details and business unit information.</p>
              
              <div class="form-row">
                <div class="form-group">
                  <label>Department:</label>
                  <input type="text" v-model="businessInfo.departmentName" disabled />
                </div>
                <div class="form-group">
                  <label>Business Unit:</label>
                  <input type="text" :value="businessInfo.businessUnitName + ' (' + businessInfo.businessUnitCode + ')'" disabled />
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label>Entity:</label>
                  <input type="text" :value="businessInfo.entityName + ' - ' + businessInfo.entityType" disabled />
                </div>
                <div class="form-group">
                  <label>Location:</label>
                  <input type="text" v-model="businessInfo.location" disabled />
                </div>
              </div>
              
              <div class="form-group">
                <label>Department Head:</label>
                <input type="text" v-model="businessInfo.departmentHead" disabled />
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
        <form class="profile-form password-form" @submit.prevent="updatePassword">
          <h2 class="section-title"><i class="fas fa-key"></i>Update Password</h2>
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
                  Fill in the required information to create a new user account.
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
                  
                  <div class="form-group">
                    <label for="password">Password *</label>
                    <div class="password-input-wrapper">
                      <input 
                        :type="passwordFieldType" 
                        id="password" 
                        v-model="createUserForm.password" 
                        @input="validatePassword"
                        @focus="showPasswordRequirements = true"
                        placeholder="Enter password"
                        required
                        :disabled="createUserLoading"
                        :class="{ 'invalid': passwordErrors.length > 0 && createUserForm.password.length > 0 }"
                      />
                      <button 
                        type="button"
                        @click="togglePasswordVisibility" 
                        class="password-toggle-btn"
                        :disabled="createUserLoading"
                      >
                        <i :class="passwordFieldType === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash'"></i>
                      </button>
                    </div>
                    <!-- Password Requirements -->
                    <div v-show="showPasswordRequirements || createUserForm.password.length > 0" class="password-requirements" :class="{ 'has-errors': passwordErrors.length > 0 && createUserForm.password.length > 0 }">
                      <div style="font-weight: 600; margin-bottom: 8px; color: #374151; font-size: 14px;">Password Requirements:</div>
                      <div class="requirement-item" :class="{ 'valid': createUserForm.password.length >= 8 }">
                        <svg v-if="createUserForm.password.length >= 8" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span>At least 8 characters</span>
                      </div>
                      <div class="requirement-item" :class="{ 'valid': passwordChecks.hasUppercase }">
                        <svg v-if="passwordChecks.hasUppercase" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span>One uppercase letter</span>
                      </div>
                      <div class="requirement-item" :class="{ 'valid': passwordChecks.hasLowercase }">
                        <svg v-if="passwordChecks.hasLowercase" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span>One lowercase letter</span>
                      </div>
                      <div class="requirement-item" :class="{ 'valid': passwordChecks.hasNumber }">
                        <svg v-if="passwordChecks.hasNumber" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span>One number</span>
                      </div>
                      <div class="requirement-item" :class="{ 'valid': passwordChecks.hasSpecialChar }">
                        <svg v-if="passwordChecks.hasSpecialChar" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span>One special character</span>
                      </div>
                    </div>
                  </div>
                  
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
                  
                  <div class="form-group">
                    <label for="isActive">Status</label>
                    <select 
                      id="isActive" 
                      v-model="createUserForm.isActive" 
                      :disabled="createUserLoading"
                    >
                      <option value="Y">Active</option>
                      <option value="N">Inactive</option>
                    </select>
                  </div>
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
                  Consent Management Configuration
                </h2>
                <p class="section-helper">
                  Configure which actions require user consent. Only GRC Administrators can access this section.
                </p>
              </div>
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
        </div>
      </div>
    </div>
  </div>
  

  
</template>

<script>
// import { API_ENDPOINTS } from '@/config/api.js'
import { api } from '../../data/api';
import ConsentManagement from '../Consent/ConsentManagement.vue';

export default {
  name: 'UserProfile',
  components: {
    ConsentManagement
  },
  data() {
    return {
      activeTab: 'account',
      accountInfoType: 'personal', // New property to track which info type is displayed
      consentSubTab: 'my-consents', // Sub-tab within Consent Management: 'my-consents' or 'configuration'
      tabs: [
        { key: 'account', label: 'Account', icon: 'fas fa-user' },
        { key: 'role', label: 'Role', icon: 'fas fa-exchange-alt' },
        { key: 'password', label: 'Password', icon: 'fas fa-key' },
        { key: 'notification', label: 'Notification', icon: 'fas fa-bell' },
        { key: 'user-management', label: 'User Management', icon: 'fas fa-users', adminOnly: true },
        { key: 'consent-config', label: 'Consent Management', icon: 'fas fa-check-circle' }
      ],
      form: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
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
      userPermissions: {
        role: '',
        modules: {}
      },
      expandedModules: [],
      showCreateUserModal: false,
      isGRCAdministrator: false,
             showCreateUserForm: false, // New state for the integrated form
      showManageUsersForm: false, // State for manage users form
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
         password: '',
         email: '',
         firstName: '',
         lastName: '',
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
             this.createUserForm.password && 
             this.passwordErrors.length === 0 &&
             this.createUserForm.email && 
             this.createUserForm.firstName && 
             this.createUserForm.lastName && 
             this.createUserForm.departmentId && 
             this.createUserForm.role;
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
            this.form.firstName = data.firstName;
            this.form.lastName = data.lastName;
            this.form.email = data.email;
            
            // Fetch business info using centralized API with JWT
            console.log('Fetching business info for userId:', userId);
            try {
              const businessResponse = await api.getUserBusinessInfo(userId);
              console.log('Business data received:', businessResponse.data);
              
              if (businessResponse.data.status === 'success') {
                const data = businessResponse.data.data;
                this.businessInfo = {
                  departmentId: data.DepartmentId,
                  departmentName: data.DepartmentName,
                  businessUnitName: data.BusinessUnitName || 'N/A',
                  businessUnitCode: data.BusinessUnitCode || 'N/A',
                  entityName: data.EntityName || 'N/A',
                  entityType: data.EntityType || 'N/A',
                  location: data.Location || 'N/A',
                  departmentHead: data.DepartmentHead || 'N/A'
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

           async createUser() {
        this.createUserLoading = true;
        this.createUserError = null;
        this.createUserSuccess = null;

        try {
          // Validate password before submitting
          this.validatePassword()
          if (this.passwordErrors.length > 0) {
            this.createUserError = 'Password does not meet requirements. Please check the requirements below.';
            return;
          }

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
            password: this.createUserForm.password,
            email: this.createUserForm.email,
            firstName: this.createUserForm.firstName,
            lastName: this.createUserForm.lastName,
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

      getConsentAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };
      }
  }
}
</script>


<style scoped>
@import './UserProfile.css';

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
</style>