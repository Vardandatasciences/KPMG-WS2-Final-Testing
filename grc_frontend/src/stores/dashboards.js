/**
 * Pinia store – dashboard KPI summary cache (one slice per module dashboard).
 *
 * Pattern (from State Management teaching material):
 *   1. Check store on mount → if fresh, render immediately (0-ms wait)
 *   2. If stale / empty → show skeleton screen → fetch → store result
 *   3. Background revalidation: show cached data first, silently refresh
 */
import { defineStore } from 'pinia';

const TTL_MS = 5 * 60 * 1000; // 5 minutes
const DASHBOARDS_STORAGE_KEY = 'dashboards_pinia_cache_v1';

const emptySlice = () => ({ data: null, frameworks: null, lastFetched: 0 });

const createDefaultState = () => ({
  policy:     emptySlice(),
  compliance: emptySlice(),
  risk:       emptySlice(),
  audit:      emptySlice(),
  incident:   emptySlice(),
  event:      emptySlice(),
});

const loadPersistedState = () => {
  try {
    const raw = localStorage.getItem(DASHBOARDS_STORAGE_KEY);
    if (!raw) return createDefaultState();
    const parsed = JSON.parse(raw);
    const defaults = createDefaultState();
    if (!parsed || typeof parsed !== 'object') return defaults;
    return { ...defaults, ...parsed };
  } catch (error) {
    console.warn('[DashboardsStore] Failed to load persisted cache:', error?.message || error);
    return createDefaultState();
  }
};

const persistState = (state) => {
  try {
    localStorage.setItem(DASHBOARDS_STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.warn('[DashboardsStore] Failed to persist cache:', error?.message || error);
  }
};

export const useDashboardsStore = defineStore('dashboards', {
  state: () => loadPersistedState(),

  getters: {
    /** true when the cached data exists AND is younger than TTL */
    isFresh: (state) => (domain) => {
      const s = state[domain];
      return !!(s?.data && Date.now() - s.lastFetched < TTL_MS);
    },
    /** true when any cached data exists (may be stale) */
    hasData: (state) => (domain) => !!state[domain]?.data,
  },

  actions: {
    /** Save dashboard KPI summary for a domain */
    set(domain, data) {
      if (!this[domain]) return;
      this[domain].data = data;
      this[domain].lastFetched = Date.now();
      persistState(this.$state);
    },
    /** Save framework list for a domain */
    setFrameworks(domain, frameworks) {
      if (!this[domain]) return;
      this[domain].frameworks = frameworks;
      persistState(this.$state);
    },
    /** Get cached KPI data (may be null) */
    get(domain) { return this[domain]?.data ?? null; },
    /** Get cached framework list (may be null) */
    getFrameworks(domain) { return this[domain]?.frameworks ?? null; },
    /** Invalidate cache for a domain (forces a fresh fetch next visit) */
    clear(domain) {
      if (!this[domain]) return;
      this[domain].data = null;
      this[domain].frameworks = null;
      this[domain].lastFetched = 0;
      persistState(this.$state);
    },
    /** Invalidate ALL dashboard caches (call on logout) */
    clearAll() {
      ['policy', 'compliance', 'risk', 'audit', 'incident', 'event'].forEach((d) => this.clear(d));
    },
  },
});
