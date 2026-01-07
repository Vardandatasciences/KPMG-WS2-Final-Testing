<template>
  <div id="vendor_app" class="vendor_min-h-screen vendor_bg-background">
    <!-- Loading State -->
    <div v-if="isLoading" class="vendor_flex vendor_items-center vendor_justify-center vendor_min-h-screen">
      <div class="vendor_text-center">
        <div class="vendor_animate-spin vendor_rounded-full vendor_h-12 vendor_w-12 vendor_border-b-2 vendor_border-primary vendor_mx-auto"></div>
        <p class="vendor_text-muted-foreground vendor_mt-4">Loading...</p>
      </div>
    </div>
    <!-- App Content -->
    <template v-else>
      <VendorLayout v-if="isAuthenticated">
        <router-view />
      </VendorLayout>
      <router-view v-else />
    </template>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth_vendor'
import VendorLayout from '@/components/VendorLayout.vue'

const authStore = useAuthStore()

// Make isAuthenticated and loading reactive
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isLoading = computed(() => authStore.loading)

onMounted(async () => {
  // Initialize authentication state only once
  if (!authStore.isAuthenticated && !authStore.user) {
    await authStore.initializeAuth()
  }
})
</script>

<style scoped>
.vendor_flex {
  display: flex;
}

.vendor_items-center {
  align-items: center;
}

.vendor_justify-center {
  justify-content: center;
}

.vendor_min-h-screen {
  min-height: 100vh;
}

.vendor_text-center {
  text-align: center;
}

.vendor_animate-spin {
  animation: spin 1s linear infinite;
}

.vendor_rounded-full {
  border-radius: 9999px;
}

.vendor_h-12 {
  height: 3rem;
}

.vendor_w-12 {
  width: 3rem;
}

.vendor_border-b-2 {
  border-bottom-width: 2px;
}

.vendor_border-primary {
  border-color: #1d4ed8;
}

.vendor_mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.vendor_mt-4 {
  margin-top: 1rem;
}

.vendor_text-muted-foreground {
  color: #64748b;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
