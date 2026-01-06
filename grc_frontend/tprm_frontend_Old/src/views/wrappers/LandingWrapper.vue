<template>
  <MPALayout>
    <div class="text-center py-12">
      <h1 class="text-4xl font-bold text-primary mb-4">RFP Management System</h1>
      <p class="text-lg text-gray-600 mb-8">Welcome to the RFP Management System</p>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <router-link to="/dashboard" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 class="text-xl font-semibold mb-2">Dashboard</h3>
          <p class="text-gray-600">View your RFP overview and statistics</p>
        </router-link>
        
        <router-link to="/rfp-workflow" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 class="text-xl font-semibold mb-2">RFP Workflow</h3>
          <p class="text-gray-600">Manage your RFP processes</p>
        </router-link>
        
        <router-link to="/analytics" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 class="text-xl font-semibold mb-2">Analytics</h3>
          <p class="text-gray-600">View KPIs and reports</p>
        </router-link>
        
        <router-link to="/approval-management" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 class="text-xl font-semibold mb-2">Approval Management</h3>
          <p class="text-gray-600">Create and manage approval workflows</p>
        </router-link>
        
        <router-link to="/draft-manager" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 class="text-xl font-semibold mb-2">Draft Manager</h3>
          <p class="text-gray-600">Manage your RFP drafts</p>
        </router-link>
        
        <router-link to="/my-approvals" class="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
          <h3 class="text-xl font-semibold mb-2">My Approvals</h3>
          <p class="text-gray-600">View your pending approvals</p>
        </router-link>
      </div>
    </div>
  </MPALayout>
</template>

<script setup lang="ts">
import MPALayout from '@/components_rfp/MPALayout.vue'
</script>

