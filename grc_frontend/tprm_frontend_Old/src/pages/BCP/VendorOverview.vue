<template>
  <div class="container mx-auto p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between" v-if="vendor">
      <div class="flex items-center gap-4">
        <button class="btn btn--outline" @click="$router.push('/vendor-hub')">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          Back to Vendor Hub
        </button>
        <div class="flex items-center gap-3">
          <svg class="h-8 w-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <div>
            <h1 class="text-3xl font-bold">{{ vendor.name }}</h1>
            <p class="text-muted-foreground">Vendor ID: {{ vendorId }}</p>
          </div>
        </div>
      </div>
      <div class="flex gap-2">
        <button class="btn btn--outline">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          Manage Vendor
        </button>
        <button class="btn btn--outline">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          View KPIs
        </button>
      </div>
    </div>

    <!-- Not Found State -->
    <div v-if="!vendor" class="text-center">
      <h1 class="text-2xl font-bold">Vendor Not Found</h1>
      <button class="btn btn--primary mt-4" @click="$router.push('/vendor-hub')">
        Back to Vendor Hub
      </button>
    </div>

    <!-- Vendor KPIs -->
    <div v-if="vendor" class="kpi-cards-grid">
      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Active Plans</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ vendor.activePlans }}</div>
          <div class="text-xs text-muted-foreground">
            Approved: {{ vendor.approvedPlans }} | Pending: {{ vendor.pendingPlans }} | Rejected: {{ vendor.rejectedPlans }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Testing Assignments</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ vendor.testingAssignments }}</div>
          <div class="text-xs text-muted-foreground">
            In Progress: {{ vendor.inProgressTesting }} | Completed: {{ vendor.completedTesting }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Evaluation Status</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold">{{ vendor.pendingEvaluations + vendor.completedEvaluations }}</div>
          <div class="text-xs text-muted-foreground">
            Pending: {{ vendor.pendingEvaluations }} | Completed: {{ vendor.completedEvaluations }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header pb-2">
          <h3 class="card-title text-sm font-medium text-muted-foreground">Avg Test Pass Rate</h3>
        </div>
        <div class="card-content">
          <div class="text-2xl font-bold text-green-600">{{ vendor.avgPassRate }}%</div>
          <div class="text-xs text-muted-foreground">
            Above average performance
          </div>
        </div>
      </div>
    </div>

    <!-- Key Actions -->
    <div v-if="vendor" class="flex gap-4">
      <button class="btn btn--outline">
        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        View Plans ▶
      </button>
      <button class="btn btn--outline">
        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        </svg>
        View OCR/Extraction ▶
      </button>
      <button class="btn btn--outline">
        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        View Evaluations ▶
      </button>
      <button class="btn btn--outline">
        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
        </svg>
        View Testing ▶
      </button>
    </div>

    <!-- Main Content Tabs -->
    <div v-if="vendor" class="tabs space-y-6">
      <div class="tabs-list grid w-full grid-cols-4">
        <button
          :class="['tabs-trigger', { 'data-state-active': activeTab === 'plans' }]"
          :data-state="activeTab === 'plans' ? 'active' : 'inactive'"
          @click="activeTab = 'plans'"
        >
          Plans Overview
        </button>
        <button
          :class="['tabs-trigger', { 'data-state-active': activeTab === 'ocr' }]"
          :data-state="activeTab === 'ocr' ? 'active' : 'inactive'"
          @click="activeTab = 'ocr'"
        >
          OCR & Extraction
        </button>
        <button
          :class="['tabs-trigger', { 'data-state-active': activeTab === 'evaluations' }]"
          :data-state="activeTab === 'evaluations' ? 'active' : 'inactive'"
          @click="activeTab = 'evaluations'"
        >
          Evaluations
        </button>
        <button
          :class="['tabs-trigger', { 'data-state-active': activeTab === 'testing' }]"
          :data-state="activeTab === 'testing' ? 'active' : 'inactive'"
          @click="activeTab = 'testing'"
        >
          Testing
        </button>
      </div>

      <div v-show="activeTab === 'plans'" class="tabs-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Plans Overview</h3>
          </div>
          <div class="card-content">
            <div class="relative w-full overflow-auto">
              <table class="w-full caption-bottom text-sm">
                <thead class="[&_tr]:border-b">
                  <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan ID</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan Name</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Type</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Status</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Testing Status</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Pass Rate</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Last Updated</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Actions</th>
                  </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                  <tr 
                    v-for="plan in plansData" 
                    :key="plan.id"
                    class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-mono">{{ plan.id }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-medium">{{ plan.name }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span class="badge badge--outline">{{ plan.type }}</span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', getStatusBadge(plan.status)]">{{ plan.status.replace('_', ' ') }}</span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', getStatusBadge(plan.testingStatus)]">{{ plan.testingStatus.replace('_', ' ') }}</span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', plan.passRate >= 80 ? 'badge--default' : 'badge--secondary']">
                        {{ plan.passRate }}%
                      </span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">{{ plan.lastUpdated }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <button class="btn btn--outline btn--sm">
                        View Plan ▶
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'ocr'" class="tabs-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">OCR & Extraction Status</h3>
          </div>
          <div class="card-content">
            <div class="relative w-full overflow-auto">
              <table class="w-full caption-bottom text-sm">
                <thead class="[&_tr]:border-b">
                  <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan ID</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan Name</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">OCR Status</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">OCR By</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">OCR Date</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Actions</th>
                  </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                  <tr 
                    v-for="ocr in ocrData" 
                    :key="ocr.planId"
                    class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-mono">{{ ocr.planId }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-medium">{{ ocr.planName }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', getStatusBadge(ocr.status)]">{{ ocr.status.replace('_', ' ') }}</span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <div class="flex items-center gap-2">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                        </svg>
                        {{ ocr.ocrBy }}
                      </div>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">{{ ocr.ocrDate }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <button class="btn btn--outline btn--sm">
                        View ▶
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'evaluations'" class="tabs-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Evaluations Overview</h3>
          </div>
          <div class="card-content">
            <div class="relative w-full overflow-auto">
              <table class="w-full caption-bottom text-sm">
                <thead class="[&_tr]:border-b">
                  <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan ID</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan Name</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Evaluation Status</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Assigned To</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Completed</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Actions</th>
                  </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                  <tr 
                    v-for="evaluation in evaluationsData" 
                    :key="evaluation.planId"
                    class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-mono">{{ evaluation.planId }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-medium">{{ evaluation.planName }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', getStatusBadge(evaluation.status)]">{{ evaluation.status.replace('_', ' ') }}</span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <div class="flex items-center gap-2">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                        </svg>
                        {{ evaluation.assignedTo }}
                      </div>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', evaluation.completed ? 'badge--default' : 'badge--secondary']">
                        {{ evaluation.completed ? "Yes" : "No" }}
                      </span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <button class="btn btn--outline btn--sm">
                        Review ▶
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'testing'" class="tabs-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Testing Overview</h3>
          </div>
          <div class="card-content">
            <div class="relative w-full overflow-auto">
              <table class="w-full caption-bottom text-sm">
                <thead class="[&_tr]:border-b">
                  <tr class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan ID</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Plan Name</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Testing Status</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Assigned To</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Due Date</th>
                    <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0">Actions</th>
                  </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                  <tr 
                    v-for="test in testingData" 
                    :key="test.planId"
                    class="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-mono">{{ test.planId }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0 font-medium">{{ test.planName }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <span :class="['badge', getStatusBadge(test.status)]">{{ test.status.replace('_', ' ') }}</span>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <div class="flex items-center gap-2">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                        </svg>
                        {{ test.assignedTo }}
                      </div>
                    </td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">{{ test.dueDate }}</td>
                    <td class="p-4 align-middle [&:has([role=checkbox])]:pr-0">
                      <div class="flex gap-2">
                        <button class="btn btn--outline btn--sm">
                          View ▶
                        </button>
                        <button class="btn btn--outline btn--sm">
                          Manage ▶
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
    </div>
  </div>
</template>

<script setup lang="ts">
import './VendorOverview.css'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const route = useRoute()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const vendorId = route.params.vendorId as string
const activeTab = ref("plans")

// Mock vendor data - in real app this would come from API
const vendorData = {
  "V-001": {
    name: "Mau Cloud Services",
    activePlans: 12,
    approvedPlans: 8,
    pendingPlans: 3,
    rejectedPlans: 1,
    testingAssignments: 9,
    inProgressTesting: 6,
    completedTesting: 3,
    pendingEvaluations: 2,
    completedEvaluations: 7,
    avgPassRate: 85
  }
}

const plansData = [
  {
    id: "1042",
    name: "Cloud BCP",
    type: "BCP",
    status: "APPROVED",
    testingStatus: "IN_PROGRESS",
    passRate: 80,
    lastUpdated: "2025-08-14"
  },
  {
    id: "1043", 
    name: "Network DRP",
    type: "DRP",
    status: "UNDER_EVAL",
    testingStatus: "COMPLETED",
    passRate: 90,
    lastUpdated: "2025-08-13"
  },
  {
    id: "1044",
    name: "Branch DRP", 
    type: "DRP",
    status: "OCR_COMPLETED",
    testingStatus: "IN_PROGRESS",
    passRate: 75,
    lastUpdated: "2025-08-11"
  }
]

const ocrData = [
  {
    planId: "1042",
    planName: "Cloud BCP",
    status: "OCR_IN_PROGRESS",
    ocrBy: "User A",
    ocrDate: "2025-08-12"
  },
  {
    planId: "1043",
    planName: "Network DRP", 
    status: "OCR_COMPLETED",
    ocrBy: "User B",
    ocrDate: "2025-08-10"
  },
  {
    planId: "1044",
    planName: "Branch DRP",
    status: "OCR_COMPLETED", 
    ocrBy: "User C",
    ocrDate: "2025-08-11"
  }
]

const evaluationsData = [
  {
    planId: "1042",
    planName: "Cloud BCP",
    status: "IN_PROGRESS",
    assignedTo: "User B",
    completed: false
  },
  {
    planId: "1043",
    planName: "Network DRP",
    status: "SUBMITTED",
    assignedTo: "User C", 
    completed: true
  },
  {
    planId: "1044",
    planName: "Branch DRP",
    status: "IN_PROGRESS",
    assignedTo: "User D",
    completed: false
  }
]

const testingData = [
  {
    planId: "1042",
    planName: "Cloud BCP",
    status: "IN_PROGRESS",
    assignedTo: "User B",
    dueDate: "2025-09-05"
  },
  {
    planId: "1043", 
    name: "Network DRP",
    status: "COMPLETED",
    assignedTo: "User C",
    dueDate: "2025-08-30"
  },
  {
    planId: "1044",
    planName: "Branch DRP", 
    status: "IN_PROGRESS",
    assignedTo: "User D",
    dueDate: "2025-09-05"
  }
]

const vendor = computed(() => {
  const vendorData_result = vendorData[vendorId as keyof typeof vendorData]
  
  // Show notification if vendor not found
  if (!vendorData_result) {
    showError('Vendor Not Found', `Vendor with ID ${vendorId} was not found.`, {
      action: 'vendor_not_found',
      vendor_id: vendorId
    })
    PopupService.error(`Vendor with ID ${vendorId} was not found.`, 'Vendor Not Found')
  } else {
    // Show success notification when vendor is loaded
    showInfo('Vendor Loaded', `Vendor ${vendorData_result.name} details loaded successfully.`, {
      action: 'vendor_loaded',
      vendor_id: vendorId,
      vendor_name: vendorData_result.name
    })
    PopupService.success(`Vendor ${vendorData_result.name} details loaded successfully.`, 'Vendor Loaded')
  }
  
  return vendorData_result
})

const getStatusBadge = (status: string) => {
  const statusColors = {
    APPROVED: "badge--default",
    UNDER_EVAL: "badge--secondary", 
    OCR_COMPLETED: "badge--outline",
    IN_PROGRESS: "badge--secondary",
    COMPLETED: "badge--default",
    SUBMITTED: "badge--default",
    OCR_IN_PROGRESS: "badge--secondary"
  }
  return statusColors[status as keyof typeof statusColors] || "badge--secondary"
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Vendor Overview', vendorId)
})
</script>
