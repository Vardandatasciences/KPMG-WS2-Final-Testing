/**
 * Framework Comparison Service
 * Handles API calls for framework change management and comparison
 */

import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

const frameworkComparisonService = {
  /**
   * Get all frameworks that have amendments
   */
  async getFrameworksWithAmendments() {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_FRAMEWORKS_WITH_AMENDMENTS, {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching frameworks with amendments:', error);
      throw error;
    }
  },

  /**
   * Get selected framework from backend session
   */
  async getSelectedFramework() {
    try {
      const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED, {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching selected framework from session:', error);
      throw error;
    }
  },

  /**
   * Get all amendments for a specific framework
   */
  async getFrameworkAmendments(frameworkId) {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_FRAMEWORK_AMENDMENTS(frameworkId), {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching amendments for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Get origin (current) framework data with full hierarchy
   */
  async getFrameworkOriginData(frameworkId) {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_FRAMEWORK_ORIGIN(frameworkId), {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching origin data for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Get target (amended) framework data
   */
  async getFrameworkTargetData(frameworkId, amendmentId = null) {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_FRAMEWORK_TARGET(frameworkId, amendmentId), {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching target data for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Get summary statistics for framework comparison
   */
  async getFrameworkComparisonSummary(frameworkId) {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_FRAMEWORK_SUMMARY(frameworkId), {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching comparison summary for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Find best matching origin items for a target control
   * Uses extended timeout when AI matching is enabled
   */
  async findControlMatches(frameworkId, control, useAI = false, topN = 5) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_FIND_MATCHES(frameworkId),
        {
          control,
          use_ai: useAI,
          top_n: topN
        },
        {
          withCredentials: true,
          timeout: useAI ? 300000 : 120000 // 5 minutes for AI, 2 minutes for regular matching
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error finding matches for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Batch match multiple controls
   */
  async batchMatchControls(frameworkId, controls, useAI = false) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_BATCH_MATCH(frameworkId),
        {
          controls,
          use_ai: useAI
        },
        {
          withCredentials: true
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error batch matching controls for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Get migration overview for a framework
   * Returns high-level statistics and recent activity
   */
  async getMigrationOverview(frameworkId) {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_MIGRATION_OVERVIEW(frameworkId), {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching migration overview for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Get gap analysis for migration
   * Returns detailed breakdown of changes needed
   */
  async getGapAnalysis(frameworkId) {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_GAP_ANALYSIS(frameworkId), {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching gap analysis for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Match all compliances from amendments against database compliances
   * Uses AI for better matching accuracy
   * Uses extended timeout (10 minutes) for comprehensive AI matching operations
   * 
   * @param {number} frameworkId - Framework ID
   * @param {boolean} useAI - Whether to use AI for matching (default: true)
   * @param {number} threshold - Minimum similarity score 0.0-1.0 (default: 0.3)
   * @param {boolean} forceRerun - Force re-run even if cached results exist (default: false)
   */
  async matchAmendmentsCompliances(frameworkId, useAI = true, threshold = 0.3, forceRerun = false) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_MATCH_COMPLIANCES(frameworkId),
        {
          use_ai: useAI,
          threshold: threshold,
          force_rerun: forceRerun  // OPTION: Force re-run, bypass cache
        },
        {
          withCredentials: true,
          timeout: 600000 // 10 minutes timeout for comprehensive AI compliance matching
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error matching compliances for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Create policy/subpolicy/compliance entries from an amendment compliance
   */
  async createComplianceFromAmendment(frameworkId, payload) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_ADD_COMPLIANCE(frameworkId),
        payload,
        {
          withCredentials: true
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error adding compliance for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Check if a framework has new amendments available
   */
  async checkFrameworkUpdates(frameworkId) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_CHECK_UPDATES(frameworkId),
        {},
        {
          withCredentials: true
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error checking updates for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Get summary of frameworks that currently have amendments
   */
  async getFrameworkUpdateNotifications() {
    try {
      const response = await axios.get(API_ENDPOINTS.CHANGE_MGMT_UPDATE_NOTIFICATIONS, {
        withCredentials: true
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching framework update notifications:', error);
      throw error;
    }
  },

  /**
   * Get amendment document info for a framework
   */
  async getAmendmentDocumentInfo(frameworkId) {
    try {
      // Add cache-busting parameter to ensure fresh data
      const response = await axios.get(
        API_ENDPOINTS.CHANGE_MGMT_DOCUMENT_INFO(frameworkId),
        {
          withCredentials: true,
          params: {
            _t: Date.now() // Cache buster
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching document info for framework ${frameworkId}:`, error);
      throw error;
    }
  },

  /**
   * Start manual analysis of amendment document
   * Uses extended timeout (10 minutes) for long-running AI analysis operations
   */
  async startAmendmentAnalysis(frameworkId) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_START_ANALYSIS(frameworkId),
        {},
        {
          withCredentials: true,
          timeout: 600000 // 10 minutes timeout for AI analysis operations
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error starting analysis for framework ${frameworkId}:`, error);
      throw error;
    }
  }
  ,
  /**
   * Cancel manual analysis of amendment document
   */
  async cancelAmendmentAnalysis(frameworkId) {
    try {
      const response = await axios.post(
        API_ENDPOINTS.CHANGE_MGMT_CANCEL_ANALYSIS(frameworkId),
        {},
        {
          withCredentials: true,
          timeout: 30000
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Error cancelling analysis for framework ${frameworkId}:`, error);
      throw error;
    }
  }
};

export default frameworkComparisonService;





