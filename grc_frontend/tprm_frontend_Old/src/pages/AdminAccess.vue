<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="w-full">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Admin Access Control</h1>
        <p class="mt-2 text-gray-600">Manage user permissions and functionality-based access control</p>
      </div>

      <!-- Search and Filters -->
      <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div class="flex gap-4">
          <div class="flex-1">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search users by name, email, or username..."
              class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @input="debouncedSearch"
            />
          </div>
          <button
            @click="loadUsers"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <Search class="h-5 w-5" />
          </button>
        </div>
      </div>

      <!-- User List and Permission Editor Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- User List -->
        <div class="lg:col-span-1 bg-white rounded-lg shadow-sm">
          <div class="p-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">Users</h2>
            <p class="text-sm text-gray-500 mt-1">{{ totalUsers }} users found</p>
          </div>
          
          <div v-if="loading" class="p-8 text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p class="mt-2 text-gray-500">Loading users...</p>
          </div>

          <div v-else-if="users.length === 0" class="p-8 text-center text-gray-500">
            No users found
          </div>

          <div v-else class="overflow-y-auto" style="max-height: 600px">
            <div
              v-for="user in users"
              :key="user.userid"
              @click="selectUser(user)"
              :class="[
                'p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors',
                selectedUser?.userid === user.userid ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
              ]"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h3 class="font-medium text-gray-900">{{ user.full_name }}</h3>
                  <p class="text-sm text-gray-500">{{ user.username }}</p>
                  <p class="text-xs text-gray-400">{{ user.email }}</p>
                </div>
                <div class="text-right">
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {{ user.permission_display || `${user.total_permissions} / 170+` }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="p-4 border-t border-gray-200 flex justify-between items-center">
            <button
              @click="previousPage"
              :disabled="currentPage === 1"
              class="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span class="text-sm text-gray-600">Page {{ currentPage }} of {{ totalPages }}</span>
            <button
              @click="nextPage"
              :disabled="currentPage >= totalPages"
              class="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>

        <!-- Permission Editor -->
        <div class="lg:col-span-2 bg-white rounded-lg shadow-sm">
          <div v-if="!selectedUser" class="p-12 text-center text-gray-500">
            <Users class="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <p class="text-lg">Select a user to manage permissions</p>
          </div>

          <div v-else>
            <!-- User Header -->
            <div class="p-6 border-b border-gray-200">
              <div class="flex items-start justify-between">
                <div>
                  <h2 class="text-2xl font-bold text-gray-900">{{ selectedUser.full_name }}</h2>
                  <p class="text-gray-600">{{ selectedUser.username }} • {{ selectedUser.email }}</p>
                </div>
                <button
                  @click="savePermissions"
                  :disabled="saving"
                  class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Save class="h-4 w-4" />
                  {{ saving ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>

              <!-- Role Selector -->
              <div class="mt-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">User Role</label>
                <input
                  v-model="userRole"
                  type="text"
                  placeholder="Enter role (e.g., Admin, Manager, User)"
                  class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <!-- Permissions -->
            <div v-if="loadingPermissions" class="p-12 text-center">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p class="mt-2 text-gray-500">Loading permissions...</p>
            </div>

            <div v-else class="p-6 overflow-y-auto" style="max-height: 600px">
              <!-- Quick Actions -->
              <div class="mb-6 flex gap-2">
                <button
                  @click="selectAllPermissions"
                  class="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                >
                  Select All
                </button>
                <button
                  @click="deselectAllPermissions"
                  class="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  Deselect All
                </button>
              </div>

              <!-- Permission Modules -->
              <div v-for="(moduleData, moduleName) in permissionFields" :key="moduleName" class="mb-6">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <component :is="getModuleIcon(moduleName)" class="h-5 w-5 text-blue-600" />
                    {{ moduleData.name }}
                  </h3>
                  <button
                    @click="toggleModulePermissions(moduleName)"
                    class="text-sm text-blue-600 hover:text-blue-800"
                  >
                    {{ isModuleFullySelected(moduleName) ? 'Deselect All' : 'Select All' }}
                  </button>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div
                    v-for="permission in moduleData.permissions"
                    :key="permission.field"
                    class="flex items-start gap-3 p-3 border border-gray-200 rounded-md hover:border-blue-300 transition-colors"
                  >
                    <input
                      type="checkbox"
                      :id="permission.field"
                      v-model="userPermissions[permission.field]"
                      class="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label :for="permission.field" class="flex-1 cursor-pointer">
                      <div class="font-medium text-gray-900 text-sm">{{ permission.display }}</div>
                      <div class="text-xs text-gray-500">{{ permission.description }}</div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success/Error Messages -->
      <div v-if="message" class="fixed bottom-4 right-4 max-w-md">
        <div
          :class="[
            'p-4 rounded-lg shadow-lg',
            message.type === 'success' ? 'bg-green-500' : 'bg-red-500',
            'text-white'
          ]"
        >
          <div class="flex items-center gap-2">
            <CheckCircle v-if="message.type === 'success'" class="h-5 w-5" />
            <AlertCircle v-else class="h-5 w-5" />
            <span>{{ message.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { 
  Users, 
  Search, 
  Save, 
  CheckCircle, 
  AlertCircle,
  FileText,
  Building2,
  Shield,
  ClipboardCheck,
  Activity,
  Settings
} from 'lucide-vue-next';
import adminAccessService from '@/services/adminAccessService';

// State
const users = ref([]);
const selectedUser = ref(null);
const userPermissions = ref({});
const userRole = ref('');
const permissionFields = ref({});
const loading = ref(false);
const loadingPermissions = ref(false);
const saving = ref(false);
const searchQuery = ref('');
const currentPage = ref(1);
const totalPages = ref(1);
const totalUsers = ref(0);
const message = ref(null);

// Debounce timer
let searchTimeout = null;

// Methods
const loadUsers = async () => {
  loading.value = true;
  try {
    const response = await adminAccessService.getAllUsers({
      search: searchQuery.value,
      page: currentPage.value,
      page_size: 20
    });
    
    if (response.results) {
      users.value = response.results;
      totalUsers.value = response.count;
      totalPages.value = Math.ceil(response.count / 20);
    } else {
      users.value = response;
      totalUsers.value = response.length;
    }
  } catch (error) {
    showMessage('Failed to load users', 'error');
    console.error('Error loading users:', error);
  } finally {
    loading.value = false;
  }
};

const loadPermissionFields = async () => {
  try {
    permissionFields.value = await adminAccessService.getPermissionFields();
  } catch (error) {
    showMessage('Failed to load permission fields', 'error');
    console.error('Error loading permission fields:', error);
  }
};

const selectUser = async (user) => {
  selectedUser.value = user;
  loadingPermissions.value = true;
  
  try {
    const response = await adminAccessService.getUserPermissions(user.userid);
    userRole.value = response.role || '';
    
    // Flatten permissions from all modules
    userPermissions.value = {};
    if (response.permissions) {
      Object.values(response.permissions).forEach(modulePerms => {
        Object.assign(userPermissions.value, modulePerms);
      });
    }
  } catch (error) {
    showMessage('Failed to load user permissions', 'error');
    console.error('Error loading user permissions:', error);
  } finally {
    loadingPermissions.value = false;
  }
};

const savePermissions = async () => {
  if (!selectedUser.value) return;
  
  saving.value = true;
  try {
    await adminAccessService.updateUserPermissions({
      user_id: selectedUser.value.userid,
      permissions: userPermissions.value,
      role: userRole.value
    });
    
    showMessage('Permissions saved successfully', 'success');
    
    // Reload user list to update permission counts
    await loadUsers();
  } catch (error) {
    showMessage('Failed to save permissions', 'error');
    console.error('Error saving permissions:', error);
  } finally {
    saving.value = false;
  }
};

const selectAllPermissions = () => {
  Object.keys(permissionFields.value).forEach(moduleName => {
    permissionFields.value[moduleName].permissions.forEach(permission => {
      userPermissions.value[permission.field] = true;
    });
  });
};

const deselectAllPermissions = () => {
  Object.keys(userPermissions.value).forEach(key => {
    userPermissions.value[key] = false;
  });
};

const toggleModulePermissions = (moduleName) => {
  const isFullySelected = isModuleFullySelected(moduleName);
  permissionFields.value[moduleName].permissions.forEach(permission => {
    userPermissions.value[permission.field] = !isFullySelected;
  });
};

const isModuleFullySelected = (moduleName) => {
  if (!permissionFields.value[moduleName]) return false;
  return permissionFields.value[moduleName].permissions.every(
    permission => userPermissions.value[permission.field] === true
  );
};

const getModuleIcon = (moduleName) => {
  const iconMap = {
    rfp: FileText,
    contract: FileText,
    vendor: Building2,
    risk: Shield,
    compliance: ClipboardCheck,
    bcp_drp: Shield,
    sla: Activity,
    questionnaire: ClipboardCheck,
    system: Settings
  };
  return iconMap[moduleName] || Settings;
};

const debouncedSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage.value = 1;
    loadUsers();
  }, 500);
};

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
    loadUsers();
  }
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    loadUsers();
  }
};

const showMessage = (text, type = 'success') => {
  message.value = { text, type };
  setTimeout(() => {
    message.value = null;
  }, 3000);
};

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadUsers(),
    loadPermissionFields()
  ]);
});
</script>

<style scoped>
/* Custom scrollbar */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>

