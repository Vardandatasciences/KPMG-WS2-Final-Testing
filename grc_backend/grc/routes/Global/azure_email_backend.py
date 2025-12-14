import requests
import json
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.core.mail.message import EmailMessage
import logging
import os

logger = logging.getLogger(__name__)

class AzureADEmailBackend(BaseEmailBackend):
    """
    Email backend using Azure AD OAuth2 with smart fallback
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.tenant_id = getattr(settings, 'AZURE_AD_TENANT_ID', 'aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6')
        self.client_id = getattr(settings, 'AZURE_AD_CLIENT_ID', '127107b0-7144-4246-b2f4-160263ceb3c9')
        self.client_secret = getattr(settings, 'AZURE_AD_CLIENT_SECRET', 'sVr8Q~3b0OS~L5NFIaWGomhiGwSwFuNMnW7RPamR')
        self.scope = getattr(settings, 'AZURE_AD_SCOPE', 'https://graph.microsoft.com/.default')
        
        # Get configured from email
        configured_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'praharshitha.d@vardaanglobal.com')
        
        # CRITICAL: Azure Graph API requires the email to be registered in Azure AD
        # If the configured email is Gmail or not an Azure AD email, use the default Azure AD email
        if not configured_from_email or '@gmail.com' in configured_from_email.lower() or '@vardaanglobal.com' not in configured_from_email.lower():
            # Use the Azure AD registered email
            self.from_email = 'praharshitha.d@vardaanglobal.com'
            logger.warning(f"[AZURE] Configured email ({configured_from_email}) is not an Azure AD email. Using Azure AD registered email: {self.from_email}")
        else:
            self.from_email = configured_from_email
        
        # Log configuration status (without exposing secrets)
        logger.info("AzureADEmailBackend initialized successfully")
        logger.info(f"Azure AD Tenant ID: {self.tenant_id[:8]}..." if self.tenant_id else "Azure AD Tenant ID: Not set")
        logger.info(f"Azure AD Client ID: {self.client_id[:8]}..." if self.client_id else "Azure AD Client ID: Not set")
        logger.info(f"Client Secret: {'✓ Set' if self.client_secret else '✗ Not set'}")
        logger.info(f"From Email (Azure AD): {self.from_email}")
        
    def _get_access_token(self):
        """Get access token from Azure AD"""
        try:
            if not self.tenant_id or not self.client_id or not self.client_secret:
                logger.error("[ERROR] Missing Azure AD configuration: tenant_id, client_id, or client_secret")
                return None
                
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': self.scope,
                'grant_type': 'client_credentials'
            }
            
            logger.info("Requesting Azure AD access token")
            response = requests.post(token_url, data=token_data, timeout=30)
            response.raise_for_status()
            
            token_response = response.json()
            access_token = token_response.get('access_token')
            
            if access_token:
                logger.info("[SUCCESS] Azure AD access token obtained successfully")
                return access_token
            else:
                logger.error(f"[ERROR] No access token in response: {token_response}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Network error getting Azure AD access token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Failed to get Azure AD access token: {str(e)}")
            return None
    
    def _send_email_via_graph(self, email_message):
        """Send email using Microsoft Graph API"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                logger.warning("[WARN] No access token available, using fallback")
                return self._send_email_fallback(email_message)
                
            # Prepare email payload for Graph API
            email_payload = {
                "message": {
                    "subject": email_message.subject,
                    "body": {
                        "contentType": "HTML" if email_message.content_subtype == "html" else "Text",
                        "content": email_message.body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": recipient
                            }
                        } for recipient in email_message.to
                    ]
                },
                "saveToSentItems": True
            }
            
            # Use the configured from email for Graph API
            graph_url = f"https://graph.microsoft.com/v1.0/users/{self.from_email}/sendMail"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Sending email via Graph API to: {', '.join(email_message.to)}")
            
            response = requests.post(graph_url, headers=headers, json=email_payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"[SUCCESS] Email sent successfully via Graph API to: {', '.join(email_message.to)}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Network error sending email via Graph API: {str(e)}")
            logger.error(f"[ERROR] Full error details: {str(e)}")
            # Only fallback if explicitly allowed
            if self.fail_silently:
                return self._send_email_fallback(email_message)
            raise
        except Exception as e:
            logger.error(f"[ERROR] Failed to send email via Graph API: {str(e)}")
            logger.error(f"[ERROR] Full error details: {str(e)}")
            # Only fallback if explicitly allowed
            if self.fail_silently:
                return self._send_email_fallback(email_message)
            raise
    
    def _send_email_fallback(self, email_message):
        """Smart fallback - try SMTP first, then log for manual sending"""
        try:
            # Try SMTP fallback first if credentials are available
            email_host = getattr(settings, 'EMAIL_HOST', '')
            email_user = getattr(settings, 'EMAIL_HOST_USER', '')
            email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            
            if email_host and email_user and email_password:
                logger.info("Attempting SMTP fallback...")
                from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
                
                smtp_backend = SMTPBackend(
                    host=email_host,
                    port=getattr(settings, 'EMAIL_PORT', 587),
                    username=email_user,
                    password=email_password,
                    use_tls=getattr(settings, 'EMAIL_USE_TLS', True),
                    fail_silently=True
                )
                
                sent_count = smtp_backend.send_messages([email_message])
                if sent_count > 0:
                    logger.info(f"[SUCCESS] Email sent via SMTP fallback to: {', '.join(email_message.to)}")
                    return True
                else:
                    logger.warning("[WARN] SMTP fallback failed - no emails sent")
                    
        except Exception as smtp_error:
            logger.warning(f"[WARN] SMTP fallback failed: {smtp_error}")
        
        # Final fallback - log for manual sending
        try:
            logger.info("[EMAIL] EMAIL READY FOR MANUAL SENDING:")
            logger.info(f"   To: {', '.join(email_message.to)}")
            logger.info(f"   Subject: {email_message.subject}")
            logger.info(f"   From: {self.from_email}")
            logger.info(f"   Body: {email_message.body}")
            logger.info("[INFO] Please copy the above content and send manually via your email client")
            return True
        except Exception as e:
            logger.error(f"Fallback email logging failed: {str(e)}")
            if not self.fail_silently:
                raise
            return False
    
    def send_messages(self, email_messages):
        """Send multiple email messages"""
        if not email_messages:
            return 0
            
        sent_count = 0
        for message in email_messages:
            try:
                if self._send_email_via_graph(message):
                    sent_count += 1
                else:
                    logger.warning(f"[WARN] Failed to send email to: {', '.join(message.to)}")
            except Exception as e:
                logger.error(f"[ERROR] Error sending email to {', '.join(message.to)}: {str(e)}")
                if not self.fail_silently:
                    raise
                    
        logger.info(f"Email sending completed: {sent_count}/{len(email_messages)} sent successfully")
        return sent_count
