import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useVendorDashboardStore = defineStore('vendor_dashboard', () => {
  // State
  const vendor_kpiData = ref([
    {
      title: "Total Vendors",
      value: "247",
      variant: "default",
      trend: { value: "12%", isPositive: true }
    },
    {
      title: "High-Risk Vendors",
      value: "8",
      variant: "destructive",
      trend: { value: "2%", isPositive: false }
    },
    {
      title: "SLA Compliance",
      value: "94.2%",
      variant: "success",
      trend: { value: "3.1%", isPositive: true }
    },
    {
      title: "Avg Risk Score",
      value: "2.4",
      variant: "default",
      trend: { value: "0.3", isPositive: false }
    }
  ])

  const vendor_recentVendors = ref([
    { name: "TechCorp Solutions", status: "pending", riskLevel: "medium", daysActive: 5 },
    { name: "Global Industries", status: "approved", riskLevel: "low", daysActive: 12 },
    { name: "DataStream Inc", status: "review", riskLevel: "high", daysActive: 3 },
    { name: "SecureNet Systems", status: "approved", riskLevel: "low", daysActive: 8 }
  ])

  const vendor_vendorStatusOverview = ref([
    { label: "Active", count: 180, percentage: 73, color: "vendor_bg-success" },
    { label: "Pending Review", count: 45, percentage: 18, color: "vendor_bg-warning" },
    { label: "Suspended", count: 15, percentage: 6, color: "vendor_bg-destructive" },
    { label: "Archived", count: 7, percentage: 3, color: "vendor_bg-muted" }
  ])

  // Getters
  const vendor_getKPIData = computed(() => vendor_kpiData.value)
  const vendor_getRecentVendors = computed(() => vendor_recentVendors.value)
  const vendor_getVendorStatusOverview = computed(() => vendor_vendorStatusOverview.value)

  // Actions
  const vendor_updateKPI = (title, value) => {
    const kpi = vendor_kpiData.value.find(k => k.title === title)
    if (kpi) {
      kpi.value = value
    }
  }

  const vendor_addVendor = (vendor) => {
    vendor_recentVendors.value.unshift(vendor)
    if (vendor_recentVendors.value.length > 10) {
      vendor_recentVendors.value.pop()
    }
  }

  return {
    vendor_kpiData,
    vendor_recentVendors,
    vendor_vendorStatusOverview,
    vendor_getKPIData,
    vendor_getRecentVendors,
    vendor_getVendorStatusOverview,
    vendor_updateKPI,
    vendor_addVendor
  }
})
