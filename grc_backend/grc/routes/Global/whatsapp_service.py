"""
WhatsApp Cloud API Integration Service
Handles direct communication with WhatsApp Cloud API
"""
import requests
import os
import logging
import re
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

def _get_logger():
    """Get logger - use Flask's current_app.logger if in Flask context, otherwise use Python logger"""
    try:
        from flask import has_app_context, current_app
        if has_app_context():
            return current_app.logger
    except (ImportError, RuntimeError):
        pass
    return logger

def get_phone_number_id_from_api(access_token: str) -> Optional[str]:
    """
    Get Phone Number ID from WhatsApp Business Account API using access token
    
    Args:
        access_token: WhatsApp API access token
        
    Returns:
        Phone Number ID if found, None otherwise
    """
    try:
        api_version = os.environ.get('WHATSAPP_API_VERSION', 'v20.0')
        base_url = f"https://graph.facebook.com/{api_version}"
        
        # First, try to get the WhatsApp Business Account ID
        # Then get phone numbers from that account
        url = f"{base_url}/me/phone_numbers"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.ok:
            data = response.json()
            phone_numbers = data.get('data', [])
            if phone_numbers and len(phone_numbers) > 0:
                # Get the first verified phone number ID
                phone_number_id = phone_numbers[0].get('id')
                logger.info(f"WhatsApp: Retrieved Phone Number ID from API: {phone_number_id}")
                return phone_number_id
        
        # Alternative: Try to get from WhatsApp Business Account
        url = f"{base_url}/me?fields=whatsapp_business_account"
        response = requests.get(url, headers=headers, timeout=30)
        if response.ok:
            data = response.json()
            waba_id = data.get('whatsapp_business_account', {}).get('id')
            if waba_id:
                # Get phone numbers from WABA
                url = f"{base_url}/{waba_id}/phone_numbers"
                response = requests.get(url, headers=headers, timeout=30)
                if response.ok:
                    data = response.json()
                    phone_numbers = data.get('data', [])
                    if phone_numbers and len(phone_numbers) > 0:
                        phone_number_id = phone_numbers[0].get('id')
                        logger.info(f"WhatsApp: Retrieved Phone Number ID from WABA: {phone_number_id}")
                        return phone_number_id
        
        logger.warning("WhatsApp: Could not retrieve Phone Number ID from API")
        return None
    except Exception as e:
        logger.error(f"Error retrieving Phone Number ID from API: {str(e)}")
        return None

def get_whatsapp_config(product_name: Optional[str] = None) -> Optional[Dict]:
    """
    Get WhatsApp configuration from sys_params table
    
    Args:
        product_name: Optional product name to filter by
        
    Returns:
        Dictionary with accessToken, phoneNumberId (Phone_Number_ID), etc. or None if not found
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            if product_name:
                # Use Phone_Number_ID instead of Waba_ID - Phone_Number_ID is the correct field
                cursor.execute(
                    "SELECT Access_Token, Phone_Number_ID, Phone_Number FROM sys_params WHERE Product_Name = %s LIMIT 1",
                    [product_name]
                )
            else:
                # Get first available config - use Phone_Number_ID instead of Waba_ID
                cursor.execute(
                    "SELECT Access_Token, Phone_Number_ID, Phone_Number FROM sys_params WHERE Access_Token IS NOT NULL AND Access_Token != '' AND Phone_Number_ID IS NOT NULL AND Phone_Number_ID != '' LIMIT 1"
                )
            
            result = cursor.fetchone()
            if result:
                access_token, phone_number_id, phone_number = result
                if access_token:
                    # Clean and trim Phone_Number_ID (remove whitespace, convert to string)
                    if phone_number_id:
                        phone_number_id = str(phone_number_id).strip()
                    
                    # If Phone_Number_ID is missing or seems invalid, try to get it from API
                    if not phone_number_id or len(phone_number_id) < 10:
                        logger.info("WhatsApp: Phone_Number_ID missing or invalid, attempting to retrieve from API...")
                        phone_number_id = get_phone_number_id_from_api(access_token)
                        if phone_number_id:
                            phone_number_id = str(phone_number_id).strip()  # Ensure trimmed
                            # Update sys_params with the retrieved Phone Number ID
                            try:
                                if product_name:
                                    cursor.execute(
                                        "UPDATE sys_params SET Phone_Number_ID = %s WHERE Product_Name = %s",
                                        [phone_number_id, product_name]
                                    )
                                else:
                                    cursor.execute(
                                        "UPDATE sys_params SET Phone_Number_ID = %s WHERE Access_Token = %s LIMIT 1",
                                        [phone_number_id, access_token]
                                    )
                                connection.commit()
                                logger.info(f"WhatsApp: Updated Phone_Number_ID in sys_params to {phone_number_id}")
                            except Exception as update_error:
                                logger.warning(f"WhatsApp: Could not update Phone_Number_ID in sys_params: {str(update_error)}")
                    
                    if phone_number_id and len(phone_number_id) >= 10:
                        return {
                            'accessToken': access_token.strip() if access_token else access_token,
                            'phoneNumberId': phone_number_id,  # Already trimmed
                            'phoneNumber': phone_number.strip() if phone_number else phone_number
                        }
            
            logger.warning("WhatsApp: No valid configuration found in sys_params table")
            return None
    except Exception as e:
        logger.error(f"Error querying sys_params for WhatsApp config: {str(e)}")
        return None

class WhatsAppService:
    """Service class for interacting with WhatsApp Cloud API"""
    
    def __init__(self):
        self.api_version = os.environ.get('WHATSAPP_API_VERSION', 'v20.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.timeout = int(os.environ.get('WHATSAPP_SERVICE_TIMEOUT', '30'))
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None, auth_token: Optional[str] = None) -> Dict:
        """
        Make HTTP request to WhatsApp microservice
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            auth_token: Optional JWT token for authentication
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                headers=headers
            )
            
            # Check for HTTP errors
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as http_err:
                # Try to get error details from response
                error_details = "Unknown error"
                try:
                    error_json = response.json()
                    error_details = error_json.get('error', error_json.get('message', str(error_json)))
                    if isinstance(error_details, dict):
                        error_details = error_details.get('message', str(error_details))
                except:
                    error_details = response.text[:500]  # First 500 chars of error text
                
                error_msg = f"WhatsApp service error ({response.status_code}): {error_details}"
                _get_logger().error(error_msg)
                raise Exception(error_msg) from http_err
            
            # Parse JSON response
            try:
                return response.json()
            except ValueError as json_err:
                error_msg = f"Invalid JSON response from WhatsApp service: {response.text[:500]}"
                _get_logger().error(error_msg)
                raise Exception(error_msg) from json_err
                
        except requests.exceptions.Timeout as timeout_err:
            error_msg = f"WhatsApp service timeout after {self.timeout}s: {str(timeout_err)}"
            _get_logger().error(error_msg)
            raise Exception(error_msg) from timeout_err
        except requests.exceptions.ConnectionError as conn_err:
            error_msg = f"Failed to connect to WhatsApp service at {url}: {str(conn_err)}"
            _get_logger().error(error_msg)
            raise Exception(error_msg) from conn_err
        except Exception as e:
            # Catch-all for any other request errors
            error_msg = f"Failed to communicate with WhatsApp service: {str(e)}"
            _get_logger().error(error_msg)
            raise Exception(error_msg) from e
    
    def send_message(self, phone_number: str, message: str, preview_url: bool = False, product_name: str = None, name: str = None) -> Dict:
        """
        Send a text message via WhatsApp
        
        Args:
            phone_number: Recipient phone number (will be formatted to E.164)
            message: Message text
            preview_url: Whether to show URL preview
            product_name: Optional product name to select specific WhatsApp config
            name: Optional recipient name
            
        Returns:
            Response containing messageId and status
        """
        # Format phone number to E.164 format
        formatted_phone = self._format_phone_number(phone_number)
        
        data = {
            'phone_number': formatted_phone,
            'message': message,
            'preview_url': preview_url
        }
        if product_name:
            data['product'] = product_name
        if name:
            data['name'] = name
            
        return self._make_request(
            'POST',
            '/api/messages/send',
            data=data
        )
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to E.164 format (with + prefix)
        
        Args:
            phone_number: Phone number in any format
            
        Returns:
            Phone number in E.164 format (e.g., +918688087551)
        """
        if not phone_number:
            raise ValueError("Phone number cannot be empty")
        
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # If it already starts with +, return as is (after cleaning)
        if cleaned.startswith('+'):
            # Remove any extra + signs and keep only digits after the first +
            digits = cleaned.replace('+', '')
            return '+' + digits
        
        # If it doesn't start with +, add it
        digits = ''.join(filter(str.isdigit, phone_number))
        if not digits:
            raise ValueError("Phone number must contain at least one digit")
        
        return '+' + digits
    
    def _sanitize_template_param_text(self, value):
        """Sanitize template parameter text according to WhatsApp restrictions"""
        if value is None:
            return value
        s = str(value)
        # Replace newlines/tabs with single spaces, then collapse whitespace runs
        # Keep up to 4 consecutive spaces (WhatsApp limit)
        s = re.sub(r'[\r\n\t]+', ' ', s)
        s = re.sub(r' {5,}', '    ', s)
        s = re.sub(r'\s{2,}', lambda m: m.group(0)[:4] if m.group(0).startswith(' ') else ' ', s)
        return s.strip()
    
    def _sanitize_components(self, components):
        """Sanitize template components"""
        if not isinstance(components, list):
            return components
        
        sanitized = []
        for comp in components:
            if not isinstance(comp, dict):
                sanitized.append(comp)
                continue
            
            next_comp = comp.copy()
            if 'parameters' in next_comp and isinstance(next_comp['parameters'], list):
                next_comp['parameters'] = [
                    {
                        **p,
                        'text': self._sanitize_template_param_text(p.get('text'))
                    } if p.get('type') == 'text' and 'text' in p else p
                    for p in next_comp['parameters']
                ]
            sanitized.append(next_comp)
        
        return sanitized
    
    def send_template(self, phone_number: str, template_name: str, language_code: str = 'en', components: List = None, product_name: str = None, name: str = None, auth_token: Optional[str] = None) -> Dict:
        """
        Send a template message via WhatsApp Cloud API (e.g., authentication templates with OTP)
        
        Args:
            phone_number: Recipient phone number (will be formatted to E.164)
            template_name: Name of the approved template (e.g., 'prosync_otp')
            language_code: Language code (default: 'en')
            components: Template components/parameters (for OTP: [{'type': 'body', 'parameters': [{'type': 'text', 'text': '123456'}]}])
            product_name: Optional product name to select specific WhatsApp config from sys_params
            name: Optional recipient name (not used in API call)
            auth_token: Optional auth token (not used - gets from sys_params)
            
        Returns:
            Response containing messages[0].id (wmid) and status
        """
        # Get WhatsApp config from sys_params
        config = get_whatsapp_config(product_name)
        if not config:
            raise Exception("WhatsApp configuration not found in sys_params table. Please configure Access_Token and Waba_ID.")
        
        access_token = config['accessToken']
        phone_number_id = config['phoneNumberId']
        
        # Clean and trim values (remove any whitespace)
        access_token = access_token.strip() if access_token else access_token
        phone_number_id = phone_number_id.strip() if phone_number_id else phone_number_id
        
        # Validate access token
        if not access_token or len(access_token) < 50:
            raise Exception("Invalid access token: Token is missing or too short. Please check sys_params table.")
        
        # Validate phone number ID
        if not phone_number_id or len(phone_number_id) < 10:
            raise Exception("Invalid Phone Number ID: Missing or too short. Please check sys_params table Phone_Number_ID field.")
        
        # Format phone number to E.164 format
        formatted_phone = self._format_phone_number(phone_number)
        
        # Build template payload according to WhatsApp Cloud API format
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': formatted_phone,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {
                    'code': language_code
                }
            }
        }
        
        # Add components if provided (for authentication templates with OTP codes)
        if components and len(components) > 0:
            payload['template']['components'] = self._sanitize_components(components)
        
        # Build URL (ensure phone_number_id is trimmed)
        url = f"{self.base_url}/{phone_number_id.strip()}/messages"
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Log token info (first/last 10 chars only for security)
        token_preview = f"{access_token[:10]}...{access_token[-10:]}" if len(access_token) > 20 else 'TOO_SHORT'
        _get_logger().info(f"🔑 Using Access Token: {token_preview} (length: {len(access_token)})")
        _get_logger().info(f"📱 Phone Number ID: {phone_number_id}")
        _get_logger().info(f"📤 Sending template '{template_name}' to {formatted_phone}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            if not response.ok:
                error_text = response.text
                error_message = f"WhatsApp API error: {error_text}"
                
                try:
                    error_json = response.json()
                    if error_json.get('error'):
                        error_obj = error_json['error']
                        error_code = error_obj.get('code', 'unknown')
                        error_subcode = error_obj.get('error_subcode')
                        error_message = f"WhatsApp API error ({error_code}): {error_obj.get('message', str(error_obj))}"
                        _get_logger().error(f"❌ Full error response: {error_json}")
                        
                        # Specific handling for different error codes
                        if error_code == 190:
                            _get_logger().error("🔴 Access Token Error: Token is expired or invalid")
                            _get_logger().error("   Solution: Generate a new permanent token from Meta Developer Console")
                            _get_logger().error("   Steps:")
                            _get_logger().error("   1. Go to https://developers.facebook.com/apps/")
                            _get_logger().error("   2. Select your WhatsApp Business App")
                            _get_logger().error("   3. Go to WhatsApp > API Setup")
                            _get_logger().error("   4. Copy the Access Token (or generate a new one)")
                            _get_logger().error("   5. Update Access_Token in sys_params table")
                        elif error_code == 100:
                            if error_subcode == 33:
                                _get_logger().error(f"🔴 Phone Number ID Error: Phone Number ID '{phone_number_id}' does not exist or access token lacks permissions")
                                
                                # Try to automatically retrieve the correct Phone Number ID
                                _get_logger().info("   🔄 Attempting to retrieve correct Phone Number ID from API...")
                                correct_phone_id = get_phone_number_id_from_api(access_token)
                                
                                if correct_phone_id and correct_phone_id != phone_number_id:
                                    _get_logger().info(f"   ✅ Found correct Phone Number ID: {correct_phone_id}")
                                    _get_logger().info("   🔄 Retrying with correct Phone Number ID...")
                                    
                                    # Update the phone_number_id and retry
                                    phone_number_id = correct_phone_id
                                    url = f"{self.base_url}/{phone_number_id}/messages"
                                    
                                    # Retry the request with correct Phone Number ID
                                    try:
                                        retry_response = requests.post(
                                            url,
                                            json=payload,
                                            headers=headers,
                                            timeout=self.timeout
                                        )
                                        
                                        if retry_response.ok:
                                            data = retry_response.json()
                                            message_id = data.get('messages', [{}])[0].get('id') if data.get('messages') else None
                                            
                                            _get_logger().info(f"✅ Template sent successfully with corrected Phone Number ID: {message_id}")
                                            
                                            # Update sys_params with correct Phone Number ID
                                            try:
                                                from django.db import connection
                                                with connection.cursor() as update_cursor:
                                                    if product_name:
                                                        update_cursor.execute(
                                                            "UPDATE sys_params SET Phone_Number_ID = %s WHERE Product_Name = %s",
                                                            [correct_phone_id, product_name]
                                                        )
                                                    else:
                                                        update_cursor.execute(
                                                            "UPDATE sys_params SET Phone_Number_ID = %s WHERE Access_Token = %s LIMIT 1",
                                                            [correct_phone_id, access_token]
                                                        )
                                                    connection.commit()
                                                    _get_logger().info(f"✅ Updated Phone_Number_ID in sys_params to {correct_phone_id}")
                                            except Exception as update_error:
                                                _get_logger().warning(f"⚠️  Could not update Phone_Number_ID in sys_params: {str(update_error)}")
                                            
                                            # Return success
                                            return {
                                                'success': True,
                                                'wmid': message_id,
                                                'messages': data.get('messages', []),
                                                'raw': data
                                            }
                                        else:
                                            _get_logger().error(f"   ❌ Retry also failed with status {retry_response.status_code}")
                                    except Exception as retry_error:
                                        _get_logger().error(f"   ❌ Retry failed: {str(retry_error)}")
                                
                                # If auto-retrieval failed or retry failed, provide manual instructions
                                _get_logger().error("   Possible causes:")
                                _get_logger().error("   1. Phone Number ID in sys_params table is incorrect")
                                _get_logger().error("   2. Access token doesn't have permissions for this Phone Number ID")
                                _get_logger().error("   3. Phone Number ID belongs to a different WhatsApp Business Account")
                                _get_logger().error("   Solution: Get correct Phone Number ID from Meta Business Manager")
                                _get_logger().error("   Steps:")
                                _get_logger().error("   1. Go to https://business.facebook.com/")
                                _get_logger().error("   2. Select your WhatsApp Business Account")
                                _get_logger().error("   3. Go to Settings > Phone Numbers")
                                _get_logger().error("   4. Click on your phone number")
                                _get_logger().error("   5. Copy the Phone Number ID (starts with numbers)")
                                _get_logger().error("   6. Update Phone_Number_ID in sys_params table")
                                _get_logger().error("   OR get it from Developer Console:")
                                _get_logger().error("   1. Go to https://developers.facebook.com/apps/")
                                _get_logger().error("   2. Select your WhatsApp Business App")
                                _get_logger().error("   3. Go to WhatsApp > API Setup")
                                _get_logger().error("   4. Copy the Phone Number ID shown there")
                                _get_logger().error(f"   Current Phone Number ID: {phone_number_id}")
                                _get_logger().error(f"   Current Access Token: {token_preview}")
                            else:
                                _get_logger().error(f"🔴 Graph API Error ({error_code}): {error_obj.get('message')}")
                except:
                    _get_logger().error(f"❌ Error response (non-JSON): {error_text}")
                
                raise Exception(error_message)
            
            # Parse JSON response
            data = response.json()
            message_id = data.get('messages', [{}])[0].get('id') if data.get('messages') else None
            
            _get_logger().info(f"✅ Template sent successfully: {message_id}")
            
            # Return in format expected by calling code
            return {
                'success': True,
                'wmid': message_id,
                'messages': data.get('messages', []),
                'raw': data
            }
            
        except requests.exceptions.Timeout as timeout_err:
            error_msg = f"WhatsApp API timeout after {self.timeout}s: {str(timeout_err)}"
            _get_logger().error(error_msg)
            raise Exception(error_msg) from timeout_err
        except requests.exceptions.ConnectionError as conn_err:
            error_msg = f"Failed to connect to WhatsApp API at {url}: {str(conn_err)}"
            _get_logger().error(error_msg)
            raise Exception(error_msg) from conn_err
        except Exception as e:
            # Re-raise if it's already our formatted exception
            if "WhatsApp API error" in str(e) or "timeout" in str(e).lower() or "Failed to connect" in str(e):
                raise
            # Catch-all for any other request errors
            error_msg = f"Failed to communicate with WhatsApp API: {str(e)}"
            _get_logger().error(error_msg)
            raise Exception(error_msg) from e
    
    def send_media(self, phone_number: str, media_url: str, media_type: str = 'image', caption: str = None, product_name: str = None, name: str = None) -> Dict:
        """
        Send a media message via WhatsApp
        
        Args:
            phone_number: Recipient phone number (will be formatted to E.164)
            media_url: URL of the media file
            media_type: Type of media (image, video, document, audio)
            caption: Optional caption for the media
            product_name: Optional product name to select specific WhatsApp config
            name: Optional recipient name
            
        Returns:
            Response containing messageId and status
        """
        # Format phone number to E.164 format
        formatted_phone = self._format_phone_number(phone_number)
        
        data = {
            'phone_number': formatted_phone,
            'media_url': media_url,
            'media_type': media_type,
            'caption': caption
        }
        if product_name:
            data['product'] = product_name
        if name:
            data['name'] = name
            
        return self._make_request(
            'POST',
            '/api/messages/send-media',
            data=data
        )
    
    def get_message_status(self, message_id: str) -> Dict:
        """
        Get the status of a sent message
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            Message status information
        """
        return self._make_request(
            'GET',
            f'/api/whatsapp/message-status/{message_id}'
        )
    
    def get_conversations(self, phone_number: str, limit: int = 50, offset: int = 0, product: str = None) -> Dict:
        """
        Get conversation history with a phone number
        
        Args:
            phone_number: Phone number to get conversations for
            limit: Number of messages to retrieve
            offset: Pagination offset
            product: Optional product name to filter conversations
            
        Returns:
            List of messages in the conversation
        """
        params = {'limit': limit, 'offset': offset}
        if product:
            params['product'] = product
            
        return self._make_request(
            'GET',
            f'/api/whatsapp/conversations/{phone_number}',
            params=params
        )
    
    def mark_as_read(self, message_id: str) -> Dict:
        """
        Mark an incoming message as read
        
        Args:
            message_id: WhatsApp message ID to mark as read
            
        Returns:
            Success status
        """
        return self._make_request(
            'POST',
            '/api/whatsapp/mark-read',
            data={'messageId': message_id}
        )
    
    def health_check(self) -> Dict:
        """
        Check if WhatsApp microservice is healthy
        
        Returns:
            Health status information
        """
        try:
            return self._make_request('GET', '/health')
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Singleton instance
whatsapp_service = WhatsAppService()
