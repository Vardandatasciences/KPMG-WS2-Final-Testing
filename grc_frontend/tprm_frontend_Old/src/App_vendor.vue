<template>
  <div id="vendor_app" class="vendor_min-h-screen vendor_bg-background">
    <VendorLayout v-if="isAuthenticated">
      <router-view />
    </VendorLayout>
    <router-view v-else />
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth_vendor'
import VendorLayout from '@/components/VendorLayout.vue'

const authStore = useAuthStore()

// Make isAuthenticated reactive
const isAuthenticated = computed(() => authStore.isAuthenticated)

onMounted(() => {
  // Initialize authentication state
  authStore.initializeAuth()
})
</script>
