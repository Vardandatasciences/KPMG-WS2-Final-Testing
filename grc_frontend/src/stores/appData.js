import { defineStore } from 'pinia';

import auditorDataService from '@/services/auditorService';
import { useAuditStore } from '@/stores/audit';
import eventDataService from '@/services/eventService';
import policyDataService from '@/services/policyService';
import incidentDataService from '@/services/incidentService';
import { useIncidentStore } from '@/stores/incident';
import apiService from '@/services/apiService';
import { API_ENDPOINTS } from '@/config/api.js';

export const useAppDataStore = defineStore('appData', {
  state: () => ({
    // Risks
    risks: [],
    riskInstances: [],
    risksLoaded: false,

    // Compliances
    complianceFrameworks: [],
    compliances: [],
    compliancesLoaded: false,

    // Audits
    audits: [],
    businessUnits: [],
    auditsLoaded: false,

    // Events
    events: [],
    integrationEvents: [],
    eventsLoaded: false,

    // Policies
    frameworksList: [],
    policyFrameworks: [],
    explorerFrameworks: [],
    policiesLoaded: false,

    // Incidents
    incidents: [],
    incidentsLoaded: false,

    // Dashboard KPI summaries — stored after first successful dashboard API call.
    // These are tiny objects (< 1 KB) that allow instant "Pinia appData" paint on
    // every subsequent visit without waiting for the full domain list to reload.
    policySummary: null,     // { total_policies, total_subpolicies, active_policies, inactive_policies, active_subpolicies, approval_rate }
    complianceSummary: null, // { status_counts, total_count, total_findings, approval_rate }
    auditSummary: null,      // { auditCompletionData, totalAuditsData, openAuditsData, completedAuditsData }

    // Fetch status
    isFetchingBackground: false,
  }),

  getters: {
    isLoaded: (state) => (domain) => !!state[`${domain}Loaded`],
  },

  actions: {
    async fetchRisks(force = false) {
      if (this.risksLoaded && !force) return;
      let success = false;
      try {
        const { useRiskStore } = await import('@/stores/risk');
        const riskStore = useRiskStore();
        await riskStore.prefetchRiskRegisterAndInstances({ force });
        this.risks = [...riskStore.risks];
        this.riskInstances = [...riskStore.riskInstances];
        success = true;
      } catch (e) {
        console.error('[pinia:appData] fetchRisks failed:', e);
        this.risks = [];
        this.riskInstances = [];
      } finally {
        this.risksLoaded = success;
      }
    },

    async fetchCompliances(force = false) {
      if (this.compliancesLoaded && !force) return;
      let fullSuccess = false;
      try {
        // Delegate to complianceStore — single source of truth for compliance data.
        const { useComplianceStore } = await import('@/stores/compliance');
        const complianceStore = useComplianceStore();
        await complianceStore.prefetchComplianceDomain({ force });

        this.complianceFrameworks = complianceStore.frameworks;
        this.compliances = complianceStore.compliances ?? [];
        fullSuccess = true;

        // Also pull in the lightweight dashboard summary if not already populated.
        if (!this.complianceSummary) {
          await complianceStore.fetchComplianceDashboard();
          if (complianceStore.dashboardSummary) {
            const s = complianceStore.dashboardSummary;
            this.complianceSummary = {
              status_counts: s.status_counts || {},
              total_count: s.total_count || 0,
              total_findings: s.total_findings || 0,
              approval_rate: s.approval_rate || 0,
            };
          }
        }
      } catch (e) {
        console.error('[pinia:appData] fetchCompliances failed:', e);
        this.complianceFrameworks = [];
        this.compliances = [];
        this.complianceSummary = null;
      } finally {
        this.compliancesLoaded = fullSuccess;
      }
    },

    async fetchAudits(force = false) {
      if (this.auditsLoaded && !force) return;
      let fullSuccess = false;
      try {
        const auditStore = useAuditStore();
        // Auditor domain prefetch (Pinia-de-duplicated) + fast KPI summary in parallel.
        const [, completionData, totalData, openData, completedData] = await Promise.all([
          auditStore.prefetchAuditDomain({ scope: 'all', force }),
          apiService.get(API_ENDPOINTS.AUDIT_COMPLETION_RATE, {}, { background: true }).catch(() => null),
          apiService.get(API_ENDPOINTS.AUDIT_TOTAL_AUDITS, {}, { background: true }).catch(() => null),
          apiService.get(API_ENDPOINTS.AUDIT_OPEN_AUDITS, {}, { background: true }).catch(() => null),
          apiService.get(API_ENDPOINTS.AUDIT_COMPLETED_AUDITS, {}, { background: true }).catch(() => null),
        ]);

        this.audits = auditStore.audits.length
          ? auditStore.audits
          : (auditorDataService.getData('audits') || []);
        this.businessUnits = auditStore.businessUnits.length
          ? auditStore.businessUnits
          : (auditorDataService.getData('businessUnits') || []);
        fullSuccess = true;

        this.auditSummary = {
          auditCompletionData: {
            current_month_rate:  completionData?.current_month_rate  ?? 0,
            previous_month_rate: completionData?.previous_month_rate ?? 0,
            change_in_rate:      completionData?.change_in_rate      ?? 0,
            is_positive_change:  completionData?.is_positive_change  ?? true,
          },
          totalAuditsData: {
            total_current_month: totalData?.total_current_month ?? 0,
            total_previous_month:totalData?.total_previous_month ?? 0,
            change_in_total:     totalData?.change_in_total     ?? 0,
            is_positive_change:  totalData?.is_positive_change  ?? true,
          },
          openAuditsData: {
            open_this_week:  openData?.open_this_week  ?? 0,
            open_last_week:  openData?.open_last_week  ?? 0,
            change_in_open:  openData?.change_in_open  ?? 0,
            percent_change:  openData?.percent_change   ?? 0,
            is_improvement:  openData?.is_improvement  ?? true,
          },
          completedAuditsData: {
            this_week_count:      completedData?.this_week_count      ?? 0,
            last_week_count:      completedData?.last_week_count      ?? 0,
            change_in_completed:  completedData?.change_in_completed  ?? 0,
            percent_change:       completedData?.percent_change        ?? 0,
            is_improvement:       completedData?.is_improvement       ?? true,
          },
        };
      } catch (e) {
        console.error('[pinia:appData] fetchAudits failed:', e);
        this.audits = [];
        this.businessUnits = [];
        this.auditSummary = null;
      } finally {
        this.auditsLoaded = fullSuccess;
      }
    },

    async fetchEvents(force = false) {
      if (this.eventsLoaded && !force) return;
      let success = false;
      try {
        await eventDataService.fetchAllEventData();
        this.events = eventDataService.getData('events') || [];
        this.integrationEvents = eventDataService.getData('integrationEvents') || [];
        success = true;
      } catch (e) {
        console.error('[pinia:appData] fetchEvents failed:', e);
        this.events = [];
        this.integrationEvents = [];
      } finally {
        this.eventsLoaded = success;
      }
    },

    async fetchPolicies(force = false) {
      if (this.policiesLoaded && !force) return;
      let success = false;
      try {
        // Store complete policy datasets and a lightweight KPI summary in parallel.
        const [fullDataResult, summaryResult] = await Promise.allSettled([
          policyDataService.fetchAllPolicyData(),
          apiService.get(API_ENDPOINTS.POLICY_DASHBOARD_SUMMARY, {}, { background: true }),
        ]);

        if (fullDataResult.status === 'fulfilled') {
          this.frameworksList = policyDataService.getFrameworksList() || [];
          this.policyFrameworks = policyDataService.getAllPoliciesFrameworks() || [];
          this.explorerFrameworks = policyDataService.getFrameworkExplorerFrameworks() || [];
        } else {
          this.frameworksList = [];
          this.policyFrameworks = [];
          this.explorerFrameworks = [];
          throw fullDataResult.reason;
        }

        if (summaryResult.status === 'fulfilled' && summaryResult.value) {
          const s = summaryResult.value;
          this.policySummary = {
            total_policies: s.total_policies || 0,
            total_subpolicies: s.total_subpolicies || 0,
            active_policies: s.active_policies || 0,
            inactive_policies: s.inactive_policies || 0,
            active_subpolicies: s.active_subpolicies || 0,
            approval_rate: s.approval_rate || 0,
          };
        }
        success = true;
      } catch (e) {
        console.error('[pinia:appData] fetchPolicies failed:', e);
        this.frameworksList = [];
        this.policyFrameworks = [];
        this.explorerFrameworks = [];
        this.policySummary = null;
      } finally {
        this.policiesLoaded = success;
      }
    },

    async fetchIncidents(force = false) {
      if (this.incidentsLoaded && !force) return;
      let success = false;
      try {
        // Include full incidents list when building global cache.
        await incidentDataService.fetchAllIncidentData({ includeIncidents: true });
        this.incidents = incidentDataService.getData('incidents') || [];
        try {
          useIncidentStore().hydrateListsFromIncidentService();
        } catch (e) {
          console.warn('[pinia:appData] incident store hydrate skipped:', e);
        }
        success = true;
      } catch (e) {
        console.error('[pinia:appData] fetchIncidents failed:', e);
        this.incidents = [];
      } finally {
        this.incidentsLoaded = success;
      }
    },

    setComplianceSummary(data) {
      this.complianceSummary = data ? { ...data } : null;
    },

    setAuditSummary(data) {
      this.auditSummary = data ? { ...data } : null;
    },

    resetLoadedFlags() {
      this.risksLoaded = false;
      this.compliancesLoaded = false;
      this.auditsLoaded = false;
      this.eventsLoaded = false;
      this.policiesLoaded = false;
      this.incidentsLoaded = false;
    },

    async fetchAllBackground(force = false) {
      if (this.isFetchingBackground) return;
      if (force) {
        this.resetLoadedFlags();
      }
      this.isFetchingBackground = true;
      console.log('[pinia:appData] 🚀 Phase 2: starting background fetch for all domains...');
      try {
        await Promise.all([
          this.fetchRisks(force),
          this.fetchCompliances(force),
          this.fetchAudits(force),
          this.fetchEvents(force),
          this.fetchPolicies(force),
          this.fetchIncidents(force),
        ]);
        console.log('[pinia:appData] ✅ Phase 2 complete — all domain data stored in Pinia');
      } catch (e) {
        console.error('[pinia:appData] ⚠️ Phase 2 partial failure:', e);
      } finally {
        this.isFetchingBackground = false;
      }
    },
  },
});
