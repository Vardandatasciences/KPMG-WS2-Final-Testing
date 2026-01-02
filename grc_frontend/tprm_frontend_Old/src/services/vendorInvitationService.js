import api from '../utils/api_rfp.js'

const vendorInvitationService = {
  // Get primary contacts for selected vendors
  getPrimaryContacts: async (vendorIds) => {
    try {
      console.log('👥 [DEBUG] vendorInvitationService.getPrimaryContacts called with:', vendorIds);
      
      const response = await api.post('/vendor-invitations/primary-contacts/', {
        vendorIds
      });
      
      console.log('✅ [DEBUG] Primary contacts response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [DEBUG] Error getting primary contacts:', error);
      console.error('❌ [DEBUG] Error response:', error.response?.data);
      throw error;
    }
  },

  // Create vendor invitations for selected vendors
  createInvitations: async (rfpId, vendors, customMessage = null, utmParameters = null) => {
    try {
      console.log('📤 [DEBUG] vendorInvitationService.createInvitations called with:', {
        rfpId,
        vendors,
        customMessage,
        utmParameters
      });
      
      const requestData = {
        vendors,
        customMessage,
        utmParameters
      };
      
      console.log('📤 [DEBUG] Making API request to /vendor-invitations/create/' + rfpId + '/ with data:', requestData);
      
      const response = await api.post(`/vendor-invitations/create/${rfpId}/`, requestData);
      
      console.log('✅ [DEBUG] API response received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [DEBUG] Error creating vendor invitations:', error);
      console.error('❌ [DEBUG] Error response:', error.response?.data);
      console.error('❌ [DEBUG] Error status:', error.response?.status);
      console.error('❌ [DEBUG] Error headers:', error.response?.headers);
      throw error;
    }
  },

  // Send invitation emails
  sendInvitations: async (rfpId, invitations, rfpData) => {
    try {
      console.log('📧 [DEBUG] vendorInvitationService.sendInvitations called with:', {
        rfpId,
        invitations,
        rfpData
      });
      
      const response = await api.post(`/vendor-invitations/send/${rfpId}/`, {
        invitations
      });
      
      console.log('✅ [DEBUG] Send invitations response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ [DEBUG] Error sending invitations:', error);
      throw error;
    }
  },

  // Get all invitations for an RFP
  getInvitationsByRFP: async (rfpId) => {
    try {
      const response = await api.get(`/vendor-invitations/rfp/${rfpId}`);
      return response.data;
    } catch (error) {
      console.error('Error retrieving invitations:', error);
      throw error;
    }
  },

  // Get invitation by token (for external portal)
  getInvitationByToken: async (token) => {
    try {
      const response = await api.get(`/vendor-invitations/token/${token}`);
      return response.data;
    } catch (error) {
      console.error('Error retrieving invitation:', error);
      throw error;
    }
  },

  // Acknowledge invitation
  acknowledgeInvitation: async (token, ipAddress = null, userAgent = null) => {
    try {
      const response = await api.post(`/vendor-invitations/acknowledge/${token}`, {
        ip_address: ipAddress,
        user_agent: userAgent
      });
      return response.data;
    } catch (error) {
      console.error('Error acknowledging invitation:', error);
      throw error;
    }
  },

  // Decline invitation
  declineInvitation: async (token, declinedReason = null, ipAddress = null, userAgent = null) => {
    try {
      const response = await api.post(`/vendor-invitations/decline/${token}`, {
        declined_reason: declinedReason,
        ip_address: ipAddress,
        user_agent: userAgent
      });
      return response.data;
    } catch (error) {
      console.error('Error declining invitation:', error);
      throw error;
    }
  },

  // Resend invitation
  resendInvitation: async (invitationId, rfpData) => {
    try {
      const response = await api.post(`/vendor-invitations/resend/${invitationId}`, {
        rfpData
      });
      return response.data;
    } catch (error) {
      console.error('Error resending invitation:', error);
      throw error;
    }
  },

  // Get invitation statistics
  getInvitationStats: async (rfpId) => {
    try {
      const response = await api.get(`/vendor-invitations/stats/${rfpId}`);
      return response.data;
    } catch (error) {
      console.error('Error retrieving invitation statistics:', error);
      throw error;
    }
  }
};

export default vendorInvitationService
