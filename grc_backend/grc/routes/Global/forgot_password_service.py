import smtplib
import os
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import mysql.connector
import requests
import json

# Load environment variables
load_dotenv()

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("forgot_password_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("forgot_password_service")

class ForgotPasswordService:
    def __init__(self):
        # SMTP Configuration for forgot password
        self.smtp_config = {
            'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', 587)),
            'email': os.getenv('SMTP_EMAIL', 'loukyarao68@gmail.com'),
            'password': os.getenv('SMTP_PASSWORD', 'vafx kqve dwmj mvjv')
        }
        
        # Database connection
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'root'),
            'database': os.getenv('DB_NAME', 'grc')
        }
        
        # From email configuration
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', 'loukyarao68@gmail.com')
        self.from_name = os.getenv('DEFAULT_FROM_NAME', 'GRC System')
        
        # OTP expiry time (in minutes)
        self.otp_expiry_minutes = 10
        
        # Initialize database tables
        self.init_database_tables()
    
    def get_db_connection(self):
        """Establish database connection"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except mysql.connector.Error as err:
            logger.error(f"Database connection error: {err}")
            raise
    
    def init_database_tables(self):
        """Initialize database tables for password reset"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create password reset tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    token VARCHAR(255) NOT NULL,
                    otp VARCHAR(6) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_token (token),
                    INDEX idx_otp (otp),
                    INDEX idx_email (email),
                    INDEX idx_expires (expires_at)
                )
            """)
            
            # Create password reset logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    email VARCHAR(255) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    success BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_action (action),
                    INDEX idx_created (created_at)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database tables: {str(e)}")
            raise
    
    def generate_otp(self, length=6):
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def generate_token(self, length=32):
        """Generate a random token"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def get_user_by_email(self, email):
        """Get user by email address"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = "SELECT UserId, UserName, Email FROM users WHERE Email = %s"
            cursor.execute(query, (email,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'user_name': result[1],
                    'email': result[2]
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            return None
    
    def create_password_reset_token(self, user_id, email):
        """Create a password reset token and OTP"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate token and OTP
            token = self.generate_token()
            otp = self.generate_otp()
            expires_at = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Store in database
            query = """
                INSERT INTO password_reset_tokens 
                (user_id, email, token, otp, expires_at) 
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (user_id, email, token, otp, expires_at))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Password reset token created for user {user_id}")
            
            return {
                'token': token,
                'otp': otp,
                'expires_at': expires_at
            }
            
        except Exception as e:
            logger.error(f"Error creating password reset token: {str(e)}")
            raise
    
    def validate_otp(self, email, otp):
        """Validate OTP for password reset"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT user_id, token, expires_at, used 
                FROM password_reset_tokens 
                WHERE email = %s AND otp = %s AND used = FALSE AND expires_at > NOW()
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            cursor.execute(query, (email, otp))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'valid': True,
                    'user_id': result[0],
                    'token': result[1],
                    'expires_at': result[2]
                }
            else:
                return {'valid': False}
                
        except Exception as e:
            logger.error(f"Error validating OTP: {str(e)}")
            return {'valid': False}
    
    def mark_token_as_used(self, token):
        """Mark a password reset token as used"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s"
            cursor.execute(query, (token,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Token {token} marked as used")
            
        except Exception as e:
            logger.error(f"Error marking token as used: {str(e)}")
            raise
    
    def log_password_reset_action(self, user_id, email, action, success, error_message=None, ip_address=None, user_agent=None):
        """Log password reset actions"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO password_reset_logs 
                (user_id, email, action, success, error_message, ip_address, user_agent) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (user_id, email, action, success, error_message, ip_address, user_agent))
            conn.commit()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging password reset action: {str(e)}")
    
    def send_password_reset_email(self, email, user_name, otp, platform_name="GRC System"):
        """Send password reset email with OTP using Azure email backend with SMTP fallback"""
        try:
            # Try to use Notification Service first (uses Azure AD)
            try:
                from .notification_service import NotificationService
                
                notification_service = NotificationService()
                
                expiry_time = f"{self.otp_expiry_minutes} minutes"
                
                notification_data = {
                    'notification_type': 'passwordResetOTP',
                    'email': email,
                    'email_type': 'gmail',  # Will use Azure if configured, SMTP if not
                    'template_data': [
                        user_name,
                        otp,
                        expiry_time,
                        platform_name
                    ],
                }
                
                email_result = notification_service.send_multi_channel_notification(notification_data)
                
                if email_result.get('success'):
                    method_used = email_result.get('details', {}).get('email', {}).get('method', 'unknown')
                    logger.info(f"Password reset email sent successfully to {email} via {method_used}")
                    return True
                else:
                    logger.warning(f"Notification service failed, falling back to SMTP: {email_result.get('error', 'Unknown error')}")
                    # Fall through to SMTP fallback
                    
            except Exception as notification_error:
                logger.warning(f"Notification service unavailable, using SMTP fallback: {str(notification_error)}")
                # Fall through to SMTP fallback
            
            # SMTP Fallback
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = email
            msg['Subject'] = f"Password Reset OTP - {platform_name}"
            
            # Email template
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <div style="background-color: #3b82f6; padding: 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Password Reset OTP</h1>
                </div>
                <div style="padding: 20px;">
                    <p style="color: #333333; font-size: 16px;">Hello {user_name},</p>
                    <p style="color: #333333; font-size: 16px;">We received a request to reset your password for your {platform_name} account.</p>
                    <p style="color: #333333; font-size: 16px;">Your One-Time Password (OTP) is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background-color: #f8f9fa; border: 2px solid #3b82f6; border-radius: 10px; padding: 20px; display: inline-block;">
                            <span style="font-size: 32px; font-weight: bold; color: #3b82f6; letter-spacing: 5px;">{otp}</span>
                        </div>
                    </div>
                    <p style="color: #333333; font-size: 14px;"><strong>Important:</strong></p>
                    <ul style="color: #333333; font-size: 14px;">
                        <li>This OTP is valid for {self.otp_expiry_minutes} minutes</li>
                        <li>Do not share this OTP with anyone</li>
                        <li>If you didn't request this, please ignore this email</li>
                    </ul>
                    <p style="color: #333333; font-size: 14px; margin-top: 20px;">Best regards,<br>{platform_name} Team</p>
                </div>
            </div>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_config['email'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Password reset email sent successfully to {email} via SMTP (fallback)")
            return True
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    def initiate_password_reset(self, email, ip_address=None, user_agent=None):
        """Initiate password reset process"""
        try:
            # Get user by email
            user = self.get_user_by_email(email)
            if not user:
                self.log_password_reset_action(None, email, 'initiate_reset', False, 'User not found', ip_address, user_agent)
                return {
                    'success': False,
                    'message': 'If an account with this email exists, you will receive a password reset OTP.'
                }
            
            # Create password reset token
            token_data = self.create_password_reset_token(user['user_id'], email)
            
            # Send email with OTP
            email_sent = self.send_password_reset_email(
                email, 
                user['user_name'], 
                token_data['otp']
            )
            
            if email_sent:
                self.log_password_reset_action(
                    user['user_id'], 
                    email, 
                    'initiate_reset', 
                    True, 
                    None, 
                    ip_address, 
                    user_agent
                )
                
                return {
                    'success': True,
                    'message': 'Password reset OTP has been sent to your email address.'
                }
            else:
                self.log_password_reset_action(
                    user['user_id'], 
                    email, 
                    'initiate_reset', 
                    False, 
                    'Failed to send email', 
                    ip_address, 
                    user_agent
                )
                
                return {
                    'success': False,
                    'message': 'Failed to send password reset email. Please try again.'
                }
                
        except Exception as e:
            logger.error(f"Error initiating password reset: {str(e)}")
            self.log_password_reset_action(None, email, 'initiate_reset', False, str(e), ip_address, user_agent)
            
            return {
                'success': False,
                'message': 'An error occurred. Please try again later.'
            }
    
    def verify_otp_and_reset_password(self, email, otp, new_password, ip_address=None, user_agent=None):
        """Verify OTP and reset password"""
        try:
            # Validate OTP
            otp_validation = self.validate_otp(email, otp)
            
            if not otp_validation['valid']:
                self.log_password_reset_action(None, email, 'verify_otp', False, 'Invalid or expired OTP', ip_address, user_agent)
                return {
                    'success': False,
                    'message': 'Invalid or expired OTP. Please request a new one.'
                }
            
            # Update password in database
            from django.contrib.auth.hashers import make_password
            from grc.models import Users, PasswordLog
            from .password_expiry_utils import check_password_history, get_password_history_count
            from django.core.cache import cache
            
            try:
                user = Users.objects.get(UserId=otp_validation['user_id'])
                
                # Check password history to prevent reuse
                is_reused, checked_count = check_password_history(user, new_password)
                if is_reused:
                    history_count = get_password_history_count()
                    self.log_password_reset_action(user.UserId, email, 'reset_password', False, f'Password reuse detected (checked last {checked_count} passwords)', ip_address, user_agent)
                    logger.warning(f"⚠️ Password reuse blocked for user {user.UserName}: new password matches one of the last {history_count} passwords")
                    return {
                        'success': False,
                        'message': f'Password has been used recently. Please choose a different password that is not one of your last {history_count} passwords.'
                    }
                
                # Store old password hash for logging
                old_password_hash = user.Password
                # Hash the new password properly
                user.Password = make_password(new_password)
                user.save(update_fields=['Password'])
                
                # ========================================
                # CRITICAL: Clear account lockout cache after successful password reset
                # This allows the user to login immediately with the new password
                # ========================================
                try:
                    # Clear lockout cache for both JWT and session login systems
                    username_normalized = str(user.UserName).lower().strip()
                    userid_normalized = str(user.UserId).lower().strip()
                    
                    # JWT login cache keys
                    jwt_user_cache_key = f"login_failed_attempts_{username_normalized}"
                    jwt_lockout_cache_key = f"login_locked_until_{username_normalized}"
                    jwt_userid_cache_key = f"login_failed_attempts_{userid_normalized}"
                    jwt_userid_lockout_cache_key = f"login_locked_until_{userid_normalized}"
                    
                    # Session login cache keys
                    session_user_cache_key = f"session_login_failed_attempts_{username_normalized}"
                    session_lockout_cache_key = f"session_login_locked_until_{username_normalized}"
                    session_userid_cache_key = f"session_login_failed_attempts_{userid_normalized}"
                    session_userid_lockout_cache_key = f"session_login_locked_until_{userid_normalized}"
                    
                    # Clear all cache entries
                    cache.delete(jwt_user_cache_key)
                    cache.delete(jwt_lockout_cache_key)
                    cache.delete(jwt_userid_cache_key)
                    cache.delete(jwt_userid_lockout_cache_key)
                    cache.delete(session_user_cache_key)
                    cache.delete(session_lockout_cache_key)
                    cache.delete(session_userid_cache_key)
                    cache.delete(session_userid_lockout_cache_key)
                    
                    logger.info(f"✅ Cleared account lockout cache for user {user.UserName} (ID: {user.UserId}) after password reset")
                except Exception as cache_error:
                    logger.warning(f"⚠️ Failed to clear lockout cache for user {user.UserName}: {str(cache_error)}")
                    # Don't fail password reset if cache clearing fails
                
                # Log password reset to password_logs
                try:
                    logger.info(f"🔄 Attempting to create password log for user {user.UserName} (ID: {user.UserId})")
                    logger.info(f"🔄 Password log data: UserId={user.UserId}, UserName={user.UserName}, ActionType='reset', IPAddress={ip_address}, UserAgent={user_agent[:50] if user_agent else 'None'}...")
                    
                    password_log = PasswordLog.objects.create(
                        UserId=user.UserId,
                        UserName=user.UserName,
                        OldPassword=old_password_hash,  # Previous hashed password
                        NewPassword=user.Password,  # New hashed password
                        ActionType='reset',
                        IPAddress=ip_address or '',
                        UserAgent=user_agent or '',
                        AdditionalInfo={'email': email, 'reset_method': 'forgot_password_service'}
                    )
                    logger.info(f"✅ Password log created successfully with LogId={password_log.LogId} for user: {user.UserName}")
                    
                    # Verify it was saved by querying it back
                    try:
                        verify_log = PasswordLog.objects.filter(UserId=user.UserId, ActionType='reset').order_by('-Timestamp').first()
                        if verify_log:
                            logger.info(f"✅ Password log verified in database: LogId={verify_log.LogId}, Timestamp={verify_log.Timestamp}")
                        else:
                            logger.warning(f"⚠️ Password log not found in verification query for user {user.UserName}")
                    except Exception as verify_error:
                        logger.warning(f"⚠️ Failed to verify password log: {str(verify_error)}")
                        
                except Exception as log_error:
                    logger.error(f"❌ Failed to create password log on reset: {str(log_error)}")
                    logger.error(f"❌ Exception type: {type(log_error).__name__}")
                    logger.error(f"❌ Exception details: {repr(log_error)}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    # Don't fail password reset if logging fails
                
                # Also log password reset to grc_logs
                try:
                    from ...routes.Global.logging_service import send_log
                    send_log(
                        module='Authentication',
                        actionType='PASSWORD_RESET',
                        description=f'User {user.UserName} (ID: {user.UserId}) reset their password via forgot password service',
                        userId=str(user.UserId),
                        userName=user.UserName,
                        logLevel='INFO',
                        ipAddress=ip_address,
                        additionalInfo={'reset_method': 'forgot_password_service', 'email': email},
                        frameworkId=user.FrameworkId.FrameworkId if user.FrameworkId else None
                    )
                    logger.info(f"✅ Password reset logged to grc_logs for user: {user.UserName}")
                except Exception as log_error:
                    logger.error(f"❌ Failed to log password reset to grc_logs: {str(log_error)}")
                    # Don't fail password reset if logging fails
            except Users.DoesNotExist:
                raise Exception(f"User with ID {otp_validation['user_id']} not found")
            
            # Mark token as used
            self.mark_token_as_used(otp_validation['token'])
            
            # Log successful password reset
            self.log_password_reset_action(
                otp_validation['user_id'], 
                email, 
                'reset_password', 
                True, 
                None, 
                ip_address, 
                user_agent
            )
            
            return {
                'success': True,
                'message': 'Password has been reset successfully.'
            }
            
        except Exception as e:
            logger.error(f"Error verifying OTP and resetting password: {str(e)}")
            self.log_password_reset_action(None, email, 'reset_password', False, str(e), ip_address, user_agent)
            
            return {
                'success': False,
                'message': 'An error occurred while resetting password. Please try again.'
            }

# Example usage
if __name__ == "__main__":
    # Initialize forgot password service
    forgot_password_service = ForgotPasswordService()
    
    # Example: Initiate password reset
    result = forgot_password_service.initiate_password_reset('test@example.com')
    print(f"Initiate reset result: {result}")
    
    # Example: Verify OTP and reset password (you would get OTP from email)
    # otp_result = forgot_password_service.verify_otp_and_reset_password(
    #     'test@example.com', 
    #     '123456', 
    #     'newpassword123'
    # )
    # print(f"Reset password result: {otp_result}") 