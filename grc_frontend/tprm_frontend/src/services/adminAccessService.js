/**
 * Admin Access Control Service
 * Handles API calls for user permission management
 */
import axios from 'axios';
import { getTprmApiUrl } from '@/utils/backendEnv';

const API_BASE_URL = getTprmApiUrl('admin-access');

const adminAccessService = {
  /**
   * Get all active users with their permission counts
   * @param {Object} params - Query parameters (search, department_id, page, page_size)
   * @returns {Promise} User list with pagination
   */
  async getAllUsers(params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching users:', error);
      throw error;
    }
  },

  /**
   * Get permissions for a specific user
   * @param {number} userId - User ID
   * @returns {Promise} User permissions organized by module
   */
  async getUserPermissions(userId) {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/${userId}/permissions/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching permissions for user ${userId}:`, error);
      throw error;
    }
  },

  /**
   * Update permissions for a user
   * @param {Object} data - { user_id, permissions, role }
   * @returns {Promise} Update result
   */
  async updateUserPermissions(data) {
    try {
      const response = await axios.post(`${API_BASE_URL}/permissions/update/`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating permissions:', error);
      throw error;
    }
  },

  /**
   * Bulk update permissions for multiple users
   * @param {Object} data - { user_ids, permissions, role }
   * @returns {Promise} Bulk update result
   */
  async bulkUpdatePermissions(data) {
    try {
      const response = await axios.post(`${API_BASE_URL}/permissions/bulk-update/`, data);
      return response.data;
    } catch (error) {
      console.error('Error in bulk update:', error);
      throw error;
    }
  },

  /**
   * Get all available permission fields organized by module
   * @returns {Promise} Permission field metadata
   */
  async getPermissionFields() {
    try {
      const response = await axios.get(`${API_BASE_URL}/permissions/fields/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching permission fields:', error);
      throw error;
    }
  }
};

export default adminAccessService;

