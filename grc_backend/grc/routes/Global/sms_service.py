"""
SMS Service for sending OTP and notifications via SMS
Supports AWS SNS and Twilio
"""

import os
import logging
import re
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages"""
    
    def __init__(self):
        # AWS SNS Configuration
        self.aws_region = os.getenv('AWS_REGION', 'ap-south-1')
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', '')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        
        # Twilio Configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '')
        
        # Check which service is configured
        self.aws_configured = bool(self.aws_access_key_id and self.aws_secret_access_key)
        self.twilio_configured = bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number)
    
    def normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize phone number to E.164 format
        Removes all non-digit characters and ensures proper format
        """
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_number)
        
        # If number starts with 0, remove it (common in some countries)
        if digits.startswith('0'):
            digits = digits[1:]
        
        # If number doesn't start with country code, assume it's Indian (+91)
        # You can modify this logic based on your requirements
        if not digits.startswith('+'):
            if len(digits) == 10:
                # Assume Indian number, add +91
                digits = '91' + digits
            elif not digits.startswith('91') and len(digits) == 10:
                digits = '91' + digits
        
        # Ensure it starts with + for E.164 format
        if not digits.startswith('+'):
            digits = '+' + digits
        
        return digits
    
    def send_sms_aws_sns(self, phone_number: str, message: str) -> Dict:
        """
        Send SMS using AWS SNS
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Normalize phone number (from RDS database)
            logger.info(f"SMS Service: Received phone number from database: {phone_number}")
            normalized_phone = self.normalize_phone_number(phone_number)
            logger.info(f"SMS Service: Normalized phone number for AWS SNS: {normalized_phone}")
            
            # Create SNS client
            sns_client = boto3.client(
                'sns',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            
            # Check SMS account attributes to see if we're in sandbox mode
            try:
                sms_attributes = sns_client.get_sms_attributes()
                account_attributes = sms_attributes.get('attributes', {})
                spending_limit = account_attributes.get('MonthlySpendLimit', 'Not set')
                delivery_status_iam_role = account_attributes.get('DeliveryStatusIAMRole', 'Not set')
                logger.info(f"AWS SNS Account Attributes - MonthlySpendLimit: {spending_limit}, DeliveryStatusIAMRole: {delivery_status_iam_role}")
                
                # Check if account is in sandbox (no production access)
                # In sandbox, you can only send to verified numbers
                default_sms_type = account_attributes.get('DefaultSMSType', '')
                logger.info(f"AWS SNS DefaultSMSType: {default_sms_type}")
            except Exception as attr_error:
                logger.warning(f"Could not check AWS SNS account attributes: {str(attr_error)}")
            
            # Send SMS
            response = sns_client.publish(
                PhoneNumber=normalized_phone,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            message_id = response.get('MessageId')
            logger.info(f"SMS sent via AWS SNS to {normalized_phone}. MessageId: {message_id}")
            
            # Check response status
            if 'ResponseMetadata' in response:
                status_code = response['ResponseMetadata'].get('HTTPStatusCode')
                if status_code != 200:
                    logger.warning(f"AWS SNS returned non-200 status: {status_code}")
                else:
                    logger.info(f"AWS SNS accepted SMS with status code: {status_code}")
            
            # Important: AWS SNS in sandbox mode accepts SMS but may not deliver
            # if phone number is not verified. Check CloudWatch for delivery status.
            warning_note = (
                "⚠️ CRITICAL: AWS SNS accepted the SMS (MessageId: {}), "
                "but if your account is in SANDBOX MODE, the SMS will NOT be delivered "
                "unless the phone number ({}) is verified in AWS SNS console. "
                "To send SMS to any phone number from your database, you MUST request "
                "PRODUCTION ACCESS in AWS SNS. "
                "Go to: AWS SNS Console → Text messaging (SMS) → Account preferences → Request production access"
            ).format(message_id, normalized_phone)
            logger.error(warning_note)
            
            return {
                'success': True,
                'method': 'aws_sns',
                'message_id': message_id,
                'phone_number': normalized_phone,
                'note': warning_note,
                'sandbox_warning': True,
                'delivery_note': 'SMS accepted by AWS but may not deliver in sandbox mode. Verify phone in AWS SNS console or request production access.'
            }
            
        except ImportError:
            logger.error("boto3 not installed. Install it with: pip install boto3")
            return {
                'success': False,
                'error': 'boto3 library not installed'
            }
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS SNS error: {error_code} - {error_message}")
            
            # Check for common errors
            if 'OptedOut' in error_code or 'opted out' in error_message.lower():
                error_note = 'Phone number has opted out of SMS. Please verify the number.'
            elif 'InvalidParameter' in error_code or 'invalid' in error_message.lower():
                error_note = 'Invalid phone number format. Please check the number.'
            elif 'Throttling' in error_code:
                error_note = 'SMS sending rate limit exceeded. Please try again later.'
            else:
                error_note = 'If in sandbox mode, verify phone number in AWS SNS console.'
            
            return {
                'success': False,
                'error': f'AWS SNS error: {error_message}',
                'error_code': error_code,
                'note': error_note
            }
        except Exception as e:
            logger.error(f"Error sending SMS via AWS SNS: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_sms_twilio(self, phone_number: str, message: str) -> Dict:
        """
        Send SMS using Twilio
        """
        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException
            
            # Normalize phone number
            normalized_phone = self.normalize_phone_number(phone_number)
            
            # Create Twilio client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Send SMS
            message_obj = client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=normalized_phone
            )
            
            logger.info(f"SMS sent via Twilio to {normalized_phone}. SID: {message_obj.sid}")
            
            return {
                'success': True,
                'method': 'twilio',
                'message_sid': message_obj.sid,
                'phone_number': normalized_phone
            }
            
        except ImportError:
            logger.error("twilio not installed. Install it with: pip install twilio")
            return {
                'success': False,
                'error': 'twilio library not installed'
            }
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e.code} - {e.msg}")
            return {
                'success': False,
                'error': f'Twilio error: {e.msg}',
                'error_code': e.code
            }
        except Exception as e:
            logger.error(f"Error sending SMS via Twilio: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """
        Send SMS using the first available service (Twilio preferred, then AWS SNS)
        """
        if not phone_number:
            return {
                'success': False,
                'error': 'Phone number is required'
            }
        
        # Try Twilio first if configured
        if self.twilio_configured:
            logger.info(f"Attempting to send SMS via Twilio to {phone_number}")
            result = self.send_sms_twilio(phone_number, message)
            if result.get('success'):
                return result
            else:
                logger.warning(f"Twilio SMS failed: {result.get('error')}. Trying AWS SNS...")
        
        # Try AWS SNS if Twilio failed or not configured
        if self.aws_configured:
            logger.info(f"Attempting to send SMS via AWS SNS to {phone_number}")
            result = self.send_sms_aws_sns(phone_number, message)
            if result.get('success'):
                return result
            else:
                logger.warning(f"AWS SNS SMS failed: {result.get('error')}")
        
        # If both failed or not configured
        error_msg = "SMS service not configured. Please configure either Twilio or AWS SNS."
        if not self.twilio_configured and not self.aws_configured:
            logger.error(error_msg)
        else:
            error_msg = "Failed to send SMS via all configured services."
            logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg
        }
    
    def send_otp(self, phone_number: str, otp: str, user_name: str = "User", purpose: str = "profile editing") -> Dict:
        """
        Send OTP via SMS
        """
        purpose_text = {
            "profile editing": "profile editing",
            "data export": "data export",
            "portability": "data export"
        }.get(purpose, purpose)
        
        message = f"Your GRC Platform OTP for {purpose_text} is {otp}. This OTP is valid for 5 minutes. Do not share this OTP with anyone."
        
        return self.send_sms(phone_number, message)


# Singleton instance
_sms_service_instance = None

def get_sms_service() -> SMSService:
    """Get singleton instance of SMS service"""
    global _sms_service_instance
    if _sms_service_instance is None:
        _sms_service_instance = SMSService()
    return _sms_service_instance

