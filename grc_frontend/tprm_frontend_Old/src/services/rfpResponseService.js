import api from '../utils/api_rfp'

const rfpResponseService = {
  // Submit a proposal response
  submitResponse: async (token, responseData) => {
    try {
      const response = await api.post(`/rfp-responses/submit/${token}`, responseData);
      return response.data;
    } catch (error) {
      console.error('Error submitting response:', error);
      throw error;
    }
  },

  // Save draft response
  saveDraft: async (token, draftData) => {
    try {
      const response = await api.post(`/rfp-responses/draft/${token}`, draftData);
      return response.data;
    } catch (error) {
      console.error('Error saving draft:', error);
      throw error;
    }
  },

  // Get response by token
  getResponseByToken: async (token) => {
    try {
      const response = await api.get(`/rfp-responses/token/${token}`);
      return response.data;
    } catch (error) {
      console.error('Error retrieving response:', error);
      throw error;
    }
  },

  // Get all responses for an RFP (admin only)
  getResponsesByRFP: async (rfpId) => {
    try {
      const response = await api.get(`/rfp-responses/rfp/${rfpId}`);
      return response.data;
    } catch (error) {
      console.error('Error retrieving responses:', error);
      throw error;
    }
  },

  // Update response evaluation (admin only)
  updateEvaluation: async (responseId, evaluationData) => {
    try {
      const response = await api.put(`/rfp-responses/evaluate/${responseId}`, evaluationData);
      return response.data;
    } catch (error) {
      console.error('Error updating evaluation:', error);
      throw error;
    }
  },

  // Get response statistics (admin only)
  getResponseStats: async (rfpId) => {
    try {
      const response = await api.get(`/rfp-responses/stats/${rfpId}`);
      return response.data;
    } catch (error) {
      console.error('Error retrieving response statistics:', error);
      throw error;
    }
  }
};

module.exports = rfpResponseService
