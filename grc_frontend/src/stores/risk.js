import { defineStore } from 'pinia';
import riskDataService from '@/services/riskService';
import apiService from '@/services/apiService';
import { API_ENDPOINTS } from '@/config/api.js';

const RISK_CACHE_STORAGE_KEY = 'risk_module_pinia_cache_v1';

const loadPersistedCache = () => {
  try {
    const raw = localStorage.getItem(RISK_CACHE_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (error) {
    console.warn('[RiskStore] Failed to load persisted cache:', error);
    return null;
  }
};

const persistCache = (state) => {
  try {
    const dataToPersist = {
      filters: state.filters,
      metrics: state.metrics,
      lastFetch: state.lastFetch
    };
    localStorage.setItem(RISK_CACHE_STORAGE_KEY, JSON.stringify(dataToPersist));
  } catch (error) {
    console.warn('[RiskStore] Failed to persist cache:', error);
  }
};

export const useRiskStore = defineStore('risk', {
  state: () => {
    const persisted = loadPersistedCache();
    return {
      // Core Data
      risks: [],
      riskInstances: [],
      
      // Dashboard Metrics
      metrics: persisted?.metrics || {
        total: 0,
        accepted: 0,
        rejected: 0,
        mitigated: 0,
        inProgress: 0,
        categoryDistribution: { labels: [], datasets: [{ data: [], backgroundColor: [] }] },
        trendData: { labels: [], datasets: [{ data: [] }] }
      },
      
      // Filters
      filters: persisted?.filters || {
        framework: 'all',
        policy: 'all',
        timeRange: 'all',
        category: 'all',
        priority: 'all'
      },
      
      // AI Processing State (for risk_ai.vue)
      aiState: {
        currentStep: 'upload',
        isProcessing: false,
        processingProgress: 0,
        extractedRisks: [],
        selectedFile: null
      },
      
      // Status
      loading: false,
      lastFetch: persisted?.lastFetch || null,
      error: null
    };
  },

  getters: {
    totalRiskCount: (state) => state.metrics.total,
    isDataStale: (state) => {
      if (!state.lastFetch) return true;
      const fiveMinutes = 5 * 60 * 1000;
      return Date.now() - state.lastFetch > fiveMinutes;
    },
    activeFilters: (state) => {
      const active = {};
      Object.keys(state.filters).forEach(key => {
        if (state.filters[key] !== 'all') {
          active[key] = state.filters[key];
        }
      });
      return active;
    }
  },

  actions: {
    setFilter(key, value) {
      this.filters[key] = value;
      persistCache(this);
    },

    async fetchAllRisks(force = false) {
      if (!force && this.risks.length > 0) return;
      
      this.loading = true;
      try {
        await riskDataService.fetchAllRiskData();
        this.risks = riskDataService.getData('risks') || [];
        this.riskInstances = riskDataService.getData('riskInstances') || [];
        this.lastFetch = Date.now();
        persistCache(this);
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },

    async fetchDashboardMetrics(force = false) {
      if (!force && !this.isDataStale && this.metrics.total > 0) return;
      
      this.loading = true;
      try {
        const params = {
          framework_id: this.filters.framework !== 'all' ? this.filters.framework : undefined,
          policy_id: this.filters.policy !== 'all' ? this.filters.policy : undefined,
          timeRange: this.filters.timeRange !== 'all' ? this.filters.timeRange : undefined,
          category: this.filters.category !== 'all' ? this.filters.category : undefined,
          priority: this.filters.priority !== 'all' ? this.filters.priority : undefined
        };

        const response = await apiService.get(API_ENDPOINTS.RISK_DASHBOARD_WITH_FILTERS, params);
        
        if (response && response.success && response.data) {
          const summary = response.data.summary;
          this.metrics.total = summary.total_count || 0;
          this.metrics.accepted = summary.accepted_count || 0;
          this.metrics.rejected = summary.rejected_count || 0;
          this.metrics.mitigated = summary.mitigated_count || 0;
          this.metrics.inProgress = summary.in_progress_count || 0;
          
          if (response.data.category_distribution) {
            this.metrics.categoryDistribution.labels = response.data.category_distribution.map(cat => cat.Category);
            this.metrics.categoryDistribution.datasets[0].data = response.data.category_distribution.map(cat => cat.count);
          }
          
          this.lastFetch = Date.now();
          persistCache(this);
        }
      } catch (err) {
        console.error('[RiskStore] Error fetching metrics:', err);
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },

    async fetchTrendData() {
      try {
        const params = {
          framework_id: this.filters.framework,
          policy_id: this.filters.policy,
          timeRange: this.filters.timeRange,
          category: this.filters.category,
          priority: this.filters.priority
        };
        
        const response = await apiService.get(API_ENDPOINTS.RISK_TREND_OVER_TIME(), params);
        if (response && response.months) {
          this.metrics.trendData.labels = response.months;
          if (response.trendData) {
            this.metrics.trendData.datasets[0].data = response.trendData;
          } else if (response.newRisks?.data) {
            this.metrics.trendData.datasets[0].data = response.newRisks.data;
          }
        }
      } catch (err) {
        console.error('[RiskStore] Error fetching trend data:', err);
      }
    },

    setAiState(newState) {
      this.aiState = { ...this.aiState, ...newState };
    },

    resetAiState() {
      this.aiState = {
        currentStep: 'upload',
        isProcessing: false,
        processingProgress: 0,
        extractedRisks: [],
        selectedFile: null
      };
    }
  }
});
