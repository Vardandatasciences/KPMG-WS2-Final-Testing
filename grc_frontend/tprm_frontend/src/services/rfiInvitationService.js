/**
 * Service for handling RFI invitation emails
 */
import api from '@/utils/api_rfp.js'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'

const API_BASE = getTprmApiV1BaseUrl()

const rfiInvitationService = {
  /**
   * Send RFI invitation emails via backend
   */
  async sendInvitationEmails(invitations, rfiData) {
    try {
      console.log('📧 [RFI EMAIL DEBUG] Sending real invitation emails...')
      console.log('📧 [RFI EMAIL DEBUG] Invitations:', invitations)
      console.log('📧 [RFI EMAIL DEBUG] RFI Data:', rfiData)
      
      // Call backend endpoint to send emails
      const response = await api.post(`${API_BASE}/rfi-invitations/send-emails/`, {
        invitations: invitations,
        rfiData: rfiData
      })
      
      console.log('✅ [RFI EMAIL DEBUG] Email sending response:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ [RFI EMAIL DEBUG] Error sending emails:', error)
      console.error('❌ [RFI EMAIL DEBUG] Error details:', error.response?.data || error.message)
      
      // Fallback to simulation if backend email sending fails
      console.log('⚠️ [RFI EMAIL DEBUG] Falling back to email simulation...')
      const emailData = invitations.map(invitation => ({
        to: invitation.vendor_email,
        subject: `RFI Invitation: ${rfiData.rfi_title}`,
        body: this.generateEmailBody(invitation, rfiData),
        invitation_url: invitation.invitation_url
      }))
      
      // Log detailed email information for manual sending
      console.log('📧 [RFI EMAIL DEBUG] MANUAL EMAIL SENDING REQUIRED:')
      emailData.forEach((email, index) => {
        console.log(`\n📧 Email ${index + 1}:`)
        console.log(`   To: ${email.to}`)
        console.log(`   Subject: ${email.subject}`)
        console.log(`   🔗 INVITATION URL: ${email.invitation_url}`)
        console.log(`   📝 Body:\n${email.body}`)
        console.log('   ---')
      })
      
      return {
        success: false,
        emails: emailData,
        message: 'Invitation URLs generated. Email sending failed - please send manually.',
        error: error.response?.data?.error || error.message
      }
    }
  },

  /**
   * Generate email body for invitation (simplified for console logging)
   */
  generateEmailBody(invitation, rfiData) {
    return `📋 RFI Invitation - ${rfiData.rfi_title}

Dear ${invitation.vendor_name},

You have been invited to participate in our Request for Information (RFI) process.

📋 RFI Information:
- Title: ${rfiData.rfi_title}
- Number: ${rfiData.rfi_number}
- Deadline: ${rfiData.deadline || 'TBD'}
- Type: ${rfiData.rfi_type || 'General'}

🔗 YOUR UNIQUE INVITATION LINK:
${invitation.invitation_url}

This link is unique to your company and will pre-fill your information.
Click the link above to access the vendor portal directly.

📧 Response Required:
Please respond by clicking one of the buttons in the email:
- ✅ Acknowledge: Accept the invitation and access the portal
- ❌ Decline: Decline the invitation

Best regards,
RFI Team
    `.trim()
  }
}

export default rfiInvitationService
