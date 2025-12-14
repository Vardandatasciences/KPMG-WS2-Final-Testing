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
                <button
                  v-if="!editModePersonal"
                  type="button"
                  class="edit-btn"
                  @click="enableEditMode('personal')"
                >
                  <i class="fas fa-edit"></i> Edit
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
             
              <div class="form-row">
                <div class="form-group">
                  <label>First Name:</label>
                  <input type="text" v-model="form.firstName" :disabled="!editModePersonal || loading" />
                </div>
                <div class="form-group">
                  <label>Last Name:</label>
                  <input type="text" v-model="form.lastName" :disabled="!editModePersonal || loading" />
                </div>
              </div>
             
              <div class="form-row">
                <div class="form-group">
                  <label>Email:</label>
                  <input type="email" v-model="form.email" :disabled="!editModePersonal || loading" />
                </div>
                <div class="form-group">
                  <label>Phone Number:</label>
                  <input type="text" v-model="form.phone" :disabled="!editModePersonal || loading" />
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
         
          <!-- Loading State -->
          <div v-if="loadingRequests" class="loading-container">
            <div class="spinner"></div>
            <p>Loading requests...</p>
          </div>
         
          <!-- Error State -->
          <div v-else-if="requestsError" class="message error-message">
            <i class="fas fa-exclamation-circle"></i> {{ requestsError }}
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
                  <th>Status</th>
                  <th>Verification Status</th>
                  <th>Created At</th>
                  <th>Updated At</th>
                  <th>Approved By</th>
                  <th v-if="isAdminUser">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="dataSubjectRequests.length === 0">
                  <td :colspan="isAdminUser ? 10 : 9" class="no-requests">
                    <i class="fas fa-inbox"></i>
                    <p>No data subject requests found.</p>
                  </td>
                </tr>
                <tr v-for="request in dataSubjectRequests" :key="request.id">
                  <td>{{ request.id }}</td>
                  <td>{{ request.user_id }}</td>
                  <td>{{ request.user_name }}</td>
                  <td>
                    <span class="request-type-badge" :class="'type-' + request.request_type.toLowerCase()">
                      {{ request.request_type_display }}
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
                <!-- Show ACCESS request specific fields -->
                <div v-if="selectedRequest.request_type === 'ACCESS'" class="info-item">
                  <label>Requested URL:</label>
                  <span class="url-text">{{ selectedRequest.audit_trail?.requested_url || 'N/A' }}</span>
                </div>
                <div v-if="selectedRequest.request_type === 'ACCESS'" class="info-item">
                  <label>Feature:</label>
                  <span>{{ selectedRequest.audit_trail?.requested_feature || 'N/A' }}</span>
                </div>
                <div v-if="selectedRequest.request_type === 'ACCESS'" class="info-item">
                  <label>Required Permission:</label>
                  <span class="permission-badge" v-if="selectedRequest.audit_trail?.required_permission">
                    {{ selectedRequest.audit_trail.required_permission }}
                  </span>
                  <span v-else class="text-muted">N/A</span>
                </div>
                <div v-if="selectedRequest.request_type === 'ACCESS' && selectedRequest.audit_trail?.message" class="info-item">
                  <label>Message:</label>
                  <span>{{ selectedRequest.audit_trail.message }}</span>
                </div>
                <!-- Show info_type for non-ACCESS requests -->
                <div v-if="selectedRequest.request_type !== 'ACCESS'" class="info-item">
                  <label>Requested From:</label>
                  <span class="info-type-badge" :class="selectedRequest.audit_trail?.info_type === 'personal' ? 'info-type-personal' : 'info-type-business'">
                    <i :class="selectedRequest.audit_trail?.info_type === 'personal' ? 'fas fa-user' : 'fas fa-building'"></i>
                    {{ selectedRequest.audit_trail?.info_type === 'personal' ? 'Personal Information' : 'Business Information' }}
                  </span>
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
  </div>
  

  
</template>

<script>
// import { API_ENDPOINTS } from '@/config/api.js'
import { api } from '../../data/api';
import ConsentManagement from '../Consent/ConsentManagement.vue';
import ForgotPassword from './ForgotPassword.vue';

export default {
  name: 'UserProfile',
  components: {
    ConsentManagement,
    ForgotPassword
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
        { key: 'consent-config', label: 'Consent Management', icon: 'fas fa-check-circle' },
        { key: 'requests', label: 'Requests', icon: 'fas fa-file-alt'}
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
      // Data Subject Requests
      dataSubjectRequests: [],
      loadingRequests: false,
      requestsError: null,
      processingRequestId: null,
      // Edit mode states
      editModePersonal: false,
      editModeBusiness: false,
      originalPersonalData: {},
      originalBusinessData: {},
      showRectificationModal: false,
      currentEditType: 'personal', // 'personal' or 'business'
      submittingRectification: false,
      showRequestDetailsModal: false,
      selectedRequest: null,
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
         
          const { API_BASE_URL } = await import('../../config/api.js');
          const axios = (await import('axios')).default;
         
          const response = await axios.put(
            `${API_BASE_URL}/api/data-subject-requests/${requestId}/update-status/`,
            {
              status: status,
              user_id: userId,
              apply_changes: applyChanges
            },
            { headers: this.getConsentAuthHeaders() }
          );
         
          if (response.data.status === 'success') {
            // Update the request in the local array
            const requestIndex = this.dataSubjectRequests.findIndex(r => r.id === requestId);
            if (requestIndex !== -1) {
              this.dataSubjectRequests[requestIndex].status = status;
              this.dataSubjectRequests[requestIndex].status_display = status === 'APPROVED' ? 'Approved' : (status === 'REJECTED' ? 'Rejected' : 'Requested');
              this.dataSubjectRequests[requestIndex].updated_at = new Date().toISOString();
            }
           
            // Close the modal if open
            if (this.showRequestDetailsModal) {
              this.closeRequestDetailsModal();
            }
           
            // Reload requests to get updated data
            await this.loadDataSubjectRequests();
           
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

      // Access Requests Methods
     
     // Edit mode methods
     enableEditMode(type) {
       if (type === 'personal') {
         // Store original values
         this.originalPersonalData = {
           firstName: this.form.firstName,
           lastName: this.form.lastName,
           email: this.form.email,
           phone: this.form.phone || ''
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
         (this.form.phone || '') !== (this.originalPersonalData.phone || '')
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