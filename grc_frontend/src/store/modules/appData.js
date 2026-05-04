/**
 * Vuex appData module
 *
 * Central store for all domain data (risks, compliances, audits, events,
 * policies, incidents). Wraps the existing singleton service classes so that:
 *
 *  1. Data is fetched once and stored reactively in Vuex.
 *  2. Any component/page can read from store.state.appData.* instead of
 *     re-fetching or importing individual service singletons.
 *  3. Existing code that reads from service singletons directly still works
 *     without any changes — services are populated as a side-effect of these
 *     actions.
 */

import complianceDataService from '@/services/complianceService';
import auditorDataService    from '@/services/auditorService';
import eventDataService      from '@/services/eventService';
import policyDataService     from '@/services/policyService';
import incidentDataService   from '@/services/incidentService';
import { useIncidentStore } from '@/stores/incident';

export default {
  namespaced: true,

  // ─────────────────────────────────────────────────────────────
  // State
  // ─────────────────────────────────────────────────────────────
  state: {
    // Risks
    risks:             [],
    riskInstances:     [],
    risksLoaded:       false,

    // Compliances
    complianceFrameworks: [],
    compliances:          [],
    compliancesLoaded:    false,

    // Audits
    audits:        [],
    businessUnits: [],
    auditsLoaded:  false,

    // Events
    events:            [],
    integrationEvents: [],
    eventsLoaded:      false,

    // Policies
    frameworksList:    [],
    policyFrameworks:  [],
    explorerFrameworks:[],
    policiesLoaded:    false,

    // Incidents
    incidents:        [],
    incidentsLoaded:  false,

    // Background fetch status
    isFetchingBackground: false,
  },

  // ─────────────────────────────────────────────────────────────
  // Getters — simple accessors so components need only the store
  // ─────────────────────────────────────────────────────────────
  getters: {
    getRisks:             (s) => s.risks,
    getRiskInstances:     (s) => s.riskInstances,
    getCompliances:       (s) => s.compliances,
    getComplianceFrameworks: (s) => s.complianceFrameworks,
    getAudits:            (s) => s.audits,
    getBusinessUnits:     (s) => s.businessUnits,
    getEvents:            (s) => s.events,
    getIntegrationEvents: (s) => s.integrationEvents,
    getPolicyFrameworks:  (s) => s.policyFrameworks,
    getFrameworksList:    (s) => s.frameworksList,
    getExplorerFrameworks:(s) => s.explorerFrameworks,
    getIncidents:         (s) => s.incidents,

    isLoaded: (s) => (domain) => !!s[`${domain}Loaded`],
  },

  // ─────────────────────────────────────────────────────────────
  // Mutations
  // ─────────────────────────────────────────────────────────────
  mutations: {
    SET_RISKS(state, { risks, riskInstances }) {
      state.risks         = risks;
      state.riskInstances = riskInstances;
      state.risksLoaded   = true;
    },
    SET_COMPLIANCES(state, { frameworks, compliances }) {
      state.complianceFrameworks = frameworks;
      state.compliances          = compliances;
      state.compliancesLoaded    = true;
    },
    SET_AUDITS(state, { audits, businessUnits }) {
      state.audits        = audits;
      state.businessUnits = businessUnits;
      state.auditsLoaded  = true;
    },
    SET_EVENTS(state, { events, integrationEvents }) {
      state.events            = events;
      state.integrationEvents = integrationEvents;
      state.eventsLoaded      = true;
    },
    SET_POLICIES(state, { frameworksList, policyFrameworks, explorerFrameworks }) {
      state.frameworksList    = frameworksList;
      state.policyFrameworks  = policyFrameworks;
      state.explorerFrameworks= explorerFrameworks;
      state.policiesLoaded    = true;
    },
    SET_INCIDENTS(state, { incidents }) {
      state.incidents       = incidents;
      state.incidentsLoaded = true;
    },
    SET_FETCHING_BACKGROUND(state, val) {
      state.isFetchingBackground = val;
    },
  },

  // ─────────────────────────────────────────────────────────────
  // Actions — each wraps an existing service and commits to Vuex
  // ─────────────────────────────────────────────────────────────
  actions: {
    async fetchRisks({ commit, state }) {
      // Skip if already loaded into Vuex (Pinia riskStore + riskDataService stay in sync)
      if (state.risksLoaded) return;
      try {
        const { useRiskStore } = await import('@/stores/risk');
        const riskStore = useRiskStore();
        await riskStore.prefetchRiskRegisterAndInstances({ force: false });
        commit('SET_RISKS', {
          risks: [...riskStore.risks],
          riskInstances: [...riskStore.riskInstances],
        });
      } catch (e) {
        console.error('[appData] fetchRisks failed:', e);
        commit('SET_RISKS', { risks: [], riskInstances: [] });
      }
    },

    async fetchCompliances({ commit, state }) {
      if (state.compliancesLoaded) return;
      try {
        await complianceDataService.fetchAllComplianceData();
        commit('SET_COMPLIANCES', {
          frameworks:  complianceDataService.getData('frameworks')  || [],
          compliances: complianceDataService.getData('compliances') || [],
        });
      } catch (e) {
        console.error('[appData] fetchCompliances failed:', e);
        commit('SET_COMPLIANCES', { frameworks: [], compliances: [] });
      }
    },

    async fetchAudits({ commit, state }) {
      if (state.auditsLoaded) return;
      try {
        await auditorDataService.fetchAllAuditorData();
        commit('SET_AUDITS', {
          audits:        auditorDataService.getData('audits')        || [],
          businessUnits: auditorDataService.getData('businessUnits') || [],
        });
      } catch (e) {
        console.error('[appData] fetchAudits failed:', e);
        commit('SET_AUDITS', { audits: [], businessUnits: [] });
      }
    },

    async fetchEvents({ commit, state }) {
      if (state.eventsLoaded) return;
      try {
        await eventDataService.fetchAllEventData();
        commit('SET_EVENTS', {
          events:            eventDataService.getData('events')            || [],
          integrationEvents: eventDataService.getData('integrationEvents') || [],
        });
      } catch (e) {
        console.error('[appData] fetchEvents failed:', e);
        commit('SET_EVENTS', { events: [], integrationEvents: [] });
      }
    },

    async fetchPolicies({ commit, state }) {
      if (state.policiesLoaded) return;
      try {
        await policyDataService.fetchAllPolicyData();
        commit('SET_POLICIES', {
          frameworksList:    policyDataService.getFrameworksList()          || [],
          policyFrameworks:  policyDataService.getAllPoliciesFrameworks()   || [],
          explorerFrameworks:policyDataService.getFrameworkExplorerFrameworks() || [],
        });
      } catch (e) {
        console.error('[appData] fetchPolicies failed:', e);
        commit('SET_POLICIES', { frameworksList: [], policyFrameworks: [], explorerFrameworks: [] });
      }
    },

    async fetchIncidents({ commit, state }) {
      if (state.incidentsLoaded) return;
      try {
        await incidentDataService.fetchAllIncidentData();
        commit('SET_INCIDENTS', {
          incidents: incidentDataService.getData('incidents') || [],
        });
        try {
          useIncidentStore().hydrateListsFromIncidentService();
        } catch (e) {
          console.warn('[vuex:appData] incident Pinia hydrate skipped:', e);
        }
      } catch (e) {
        console.error('[appData] fetchIncidents failed:', e);
        commit('SET_INCIDENTS', { incidents: [] });
      }
    },

    /**
     * fetchAllBackground — dispatch all domain fetches in parallel.
     * Call this AFTER the critical home page data has loaded (phase 2).
     * Each individual action guards against double-fetching (loaded flag).
     */
    async fetchAllBackground({ dispatch, commit }) {
      commit('SET_FETCHING_BACKGROUND', true);
      console.log('[appData] 🚀 Phase 2: starting background fetch for all domains...');
      try {
        await Promise.all([
          dispatch('fetchRisks'),
          dispatch('fetchCompliances'),
          dispatch('fetchAudits'),
          dispatch('fetchEvents'),
          dispatch('fetchPolicies'),
          dispatch('fetchIncidents'),
        ]);
        console.log('[appData] ✅ Phase 2 complete — all domain data stored in Vuex');
      } catch (e) {
        console.error('[appData] ⚠️ Phase 2 partial failure:', e);
      } finally {
        commit('SET_FETCHING_BACKGROUND', false);
      }
    },
  },
};
