/**
 * Retention Management Service
 * Handles API communication for Retention Policies, Timelines, and Data Processing Agreements
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api';

class RetentionService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api`;
  }

  /**
   * Get authorization headers
   */
  getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  // =====================================================
  // RETENTION POLICY METHODS
  // =====================================================

  /**
   * List all retention policies
   * @param {Object} filters - Optional filters (framework_id, status, retention_type)
   * @returns {Promise}
   */
  async listRetentionPolicies(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.framework_id) params.append('framework_id', filters.framework_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.retention_type) params.append('retention_type', filters.retention_type);

      const response = await axios.get(
        `${this.baseURL}/retention/policies/?${params.toString()}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error listing retention policies:', error);
      throw error;
    }
  }

  /**
   * Get a specific retention policy
   * @param {number} policyId
   * @returns {Promise}
   */
  async getRetentionPolicy(policyId) {
    try {
      const response = await axios.get(
        `${this.baseURL}/retention/policies/${policyId}/`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting retention policy:', error);
      throw error;
    }
  }

  /**
   * Create a new retention policy
   * @param {Object} policyData
   * @returns {Promise}
   */
  async createRetentionPolicy(policyData) {
    try {
      const response = await axios.post(
        `${this.baseURL}/retention/policies/create/`,
        policyData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error creating retention policy:', error);
      throw error;
    }
  }

  /**
   * Update a retention policy
   * @param {number} policyId
   * @param {Object} policyData
   * @returns {Promise}
   */
  async updateRetentionPolicy(policyId, policyData) {
    try {
      const response = await axios.put(
        `${this.baseURL}/retention/policies/${policyId}/update/`,
        policyData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating retention policy:', error);
      throw error;
    }
  }

  /**
   * Delete a retention policy
   * @param {number} policyId
   * @returns {Promise}
   */
  async deleteRetentionPolicy(policyId) {
    try {
      const response = await axios.delete(
        `${this.baseURL}/retention/policies/${policyId}/delete/`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error deleting retention policy:', error);
      throw error;
    }
  }

  // =====================================================
  // RETENTION TIMELINE METHODS
  // =====================================================

  /**
   * List all retention timelines
   * @param {Object} filters - Optional filters (framework_id, status, record_type, record_id, policy_id, expired_only)
   * @returns {Promise}
   */
  async listRetentionTimelines(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.framework_id) params.append('framework_id', filters.framework_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.record_type) params.append('record_type', filters.record_type);
      if (filters.record_id) params.append('record_id', filters.record_id);
      if (filters.retention_policy_id) params.append('retention_policy_id', filters.retention_policy_id);
      if (filters.expired_only) params.append('expired_only', filters.expired_only);

      const response = await axios.get(
        `${this.baseURL}/retention/timelines/?${params.toString()}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error listing retention timelines:', error);
      throw error;
    }
  }

  /**
   * Create a new retention timeline
   * @param {Object} timelineData
   * @returns {Promise}
   */
  async createRetentionTimeline(timelineData) {
    try {
      const response = await axios.post(
        `${this.baseURL}/retention/timelines/create/`,
        timelineData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error creating retention timeline:', error);
      throw error;
    }
  }

  /**
   * Update a retention timeline
   * @param {number} timelineId
   * @param {Object} timelineData
   * @returns {Promise}
   */
  async updateRetentionTimeline(timelineId, timelineData) {
    try {
      const response = await axios.put(
        `${this.baseURL}/retention/timelines/${timelineId}/update/`,
        timelineData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating retention timeline:', error);
      throw error;
    }
  }

  // =====================================================
  // DATA PROCESSING AGREEMENT METHODS
  // =====================================================

  /**
   * List all data processing agreements
   * @param {Object} filters - Optional filters (framework_id, status, expired_only)
   * @returns {Promise}
   */
  async listDataProcessingAgreements(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.framework_id) params.append('framework_id', filters.framework_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.expired_only) params.append('expired_only', filters.expired_only);

      const response = await axios.get(
        `${this.baseURL}/retention/dpa/?${params.toString()}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error listing data processing agreements:', error);
      throw error;
    }
  }

  /**
   * Get a specific data processing agreement
   * @param {number} dpaId
   * @returns {Promise}
   */
  async getDataProcessingAgreement(dpaId) {
    try {
      const response = await axios.get(
        `${this.baseURL}/retention/dpa/${dpaId}/`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting data processing agreement:', error);
      throw error;
    }
  }

  /**
   * Create a new data processing agreement
   * @param {Object} dpaData
   * @returns {Promise}
   */
  async createDataProcessingAgreement(dpaData) {
    try {
      const response = await axios.post(
        `${this.baseURL}/retention/dpa/create/`,
        dpaData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error creating data processing agreement:', error);
      throw error;
    }
  }

  /**
   * Update a data processing agreement
   * @param {number} dpaId
   * @param {Object} dpaData
   * @returns {Promise}
   */
  async updateDataProcessingAgreement(dpaId, dpaData) {
    try {
      const response = await axios.put(
        `${this.baseURL}/retention/dpa/${dpaId}/update/`,
        dpaData,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating data processing agreement:', error);
      throw error;
    }
  }

  /**
   * Delete a data processing agreement
   * @param {number} dpaId
   * @returns {Promise}
   */
  async deleteDataProcessingAgreement(dpaId) {
    try {
      const response = await axios.delete(
        `${this.baseURL}/retention/dpa/${dpaId}/delete/`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error deleting data processing agreement:', error);
      throw error;
    }
  }
}

export default new RetentionService();








