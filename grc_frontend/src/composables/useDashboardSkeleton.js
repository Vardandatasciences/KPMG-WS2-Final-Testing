import { computed, unref } from 'vue'
import { useDashboardsStore } from '@/stores/dashboards'

/**
 * Cold-load skeleton: show only while fetching AND no persisted KPI slice exists yet.
 * Domains: 'policy' | 'compliance' | 'risk' | 'audit' | 'incident' | 'event'
 */
export function useDashboardSkeleton(domain, loadingRef) {
  const dashboardsStore = useDashboardsStore()
  const showSkeleton = computed(() => {
    const loading = unref(loadingRef)
    return !!loading && !dashboardsStore.hasData(domain)
  })
  return { showSkeleton, dashboardsStore }
}

/**
 * Generic list/table: skeleton when loading and no rows yet (cache miss).
 */
export function useListSkeleton(loadingRef, rowsRef) {
  const showSkeleton = computed(() => {
    const loading = unref(loadingRef)
    const rows = unref(rowsRef)
    const len = Array.isArray(rows) ? rows.length : 0
    return !!loading && len === 0
  })
  return { showSkeleton }
}
