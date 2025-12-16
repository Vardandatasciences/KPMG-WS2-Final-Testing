"""
OTP verification endpoints for profile editing
Requires mobile OTP verification before allowing users to edit their personal information
"""

import random
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from ...models import Users
from ...rbac.utils import RBACUtils

logger = logging.getLogger(__name__)

# In-memory OTP storage for profile editing
profile_edit_otp_storage = {}


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])  # Allow both authenticated and unauthenticated requests
@permission_classes([AllowAny])
def send_profile_edit_otp(request):
    """
    Send OTP to user's mobile phone for profile editing verification
    POST /api/profile-edit-otp/send/
    
    Body: {}
    """
    try:
        # Get current user
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            logger.warning("Profile edit OTP: User not authenticated")
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"Profile edit OTP request from user ID: {user_id}")
        
        # Get user from database (RDS) - refresh to ensure latest data
        try:
            user = Users.objects.get(UserId=user_id)
            # Refresh from database to ensure we have latest phone number
            user.refresh_from_db()
            logger.info(f"Profile edit OTP: Retrieved user {user_id} ({user.UserName}) from RDS database")
        except Users.DoesNotExist:
            logger.error(f"Profile edit OTP: User {user_id} not found in RDS database")
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get phone number directly from RDS database
        phone_number = user.PhoneNumber
        logger.info(f"Profile edit OTP: Phone number retrieved from RDS database (users table) for user {user_id}: '{phone_number}'")
        
        # Also verify with direct SQL query for debugging
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT PhoneNumber FROM users WHERE UserId = %s", [user_id])
                result = cursor.fetchone()
                if result:
                    db_phone = result[0]
                    logger.info(f"Profile edit OTP: Direct SQL query confirms phone number from RDS: '{db_phone}'")
                    if db_phone != phone_number:
                        logger.warning(f"Profile edit OTP: Phone number mismatch! ORM: '{phone_number}', SQL: '{db_phone}' - Using SQL value")
                        phone_number = db_phone
        except Exception as sql_error:
            logger.warning(f"Profile edit OTP: Could not verify phone via direct SQL: {str(sql_error)}")
        
        if not phone_number or not phone_number.strip():
            logger.warning(f"User {user_id} ({user.UserName}) attempted to send OTP but has no phone number in database")
            return Response({
                'success': False,
                'message': 'Phone number not found. Please add a phone number to your profile first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Clean phone number (remove whitespace)
        phone_number = phone_number.strip()
        logger.info(f"Profile edit OTP: Using phone number from RDS database - {phone_number} (masked: {phone_number[:3]}***{phone_number[-4:] if len(phone_number) >= 4 else '****'})")
        
        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store OTP in session with expiration (5 minutes)
        request.session['profile_edit_otp'] = otp
        request.session['profile_edit_user_id'] = str(user_id)
        request.session['profile_edit_otp_expiry'] = datetime.now().timestamp() + 300  # 5 minutes
        request.session.save()
        
        # Also store in memory as fallback
        profile_edit_otp_storage[str(user_id)] = {
            'otp': otp,
            'expiry': datetime.now().timestamp() + 300,  # 5 minutes
            'phone': user.PhoneNumber
        }
        
        # Send OTP via SMS
        sms_sent = False
        
        try:
            from .sms_service import get_sms_service
            
            sms_service = get_sms_service()
            user_name = user.FirstName or user.UserName or 'User'
            
            # Send OTP via SMS to the phone number from RDS database
            logger.info(f"Profile edit OTP: Attempting to send OTP to phone number from RDS database: {phone_number}")
            sms_result = sms_service.send_otp(phone_number, otp, user_name)
            
            if sms_result.get('success'):
                sms_sent = True
                logger.info(f"✅ Profile edit OTP sent via SMS ({sms_result.get('method')}) to phone number from RDS: {phone_number}")
                logger.info(f"📱 Original phone from RDS: {phone_number}, Normalized: {sms_result.get('phone_number')}")
                logger.info(f"🔐 Profile Edit OTP for user {user_id} ({user.UserName}): {otp}")
                logger.info(f"📨 Message ID: {sms_result.get('message_id')}")
                if sms_result.get('note'):
                    logger.warning(f"⚠️ {sms_result.get('note')}")
            else:
                logger.warning(f"Failed to send OTP via SMS: {sms_result.get('error')}")
                if sms_result.get('note'):
                    logger.warning(f"SMS Error Note: {sms_result.get('note')}")
                # Fallback to email if SMS fails
                if user.Email:
                    try:
                        from .notification_service import NotificationService
                        notification_service = NotificationService()
                        notification_data = {
                            'notification_type': 'passwordResetOTP',
                            'email': user.Email,
                            'email_type': 'gmail',
                            'template_data': [
                                user_name,
                                otp,
                                '5 minutes',
                                'GRC Platform'
                            ],
                        }
                        email_result = notification_service.send_multi_channel_notification(notification_data)
                        logger.info(f"Profile edit OTP sent via email (fallback) to {user.Email}")
                    except Exception as email_error:
                        logger.error(f"Failed to send OTP via email fallback: {str(email_error)}")
                        # Log OTP for manual verification in case both SMS and email fail
                        logger.error(f"[MANUAL OTP] User: {user.UserName}, Phone: {phone_number}, OTP: {otp}")
                        print(f"[PROFILE EDIT OTP] User: {user.UserName}, Phone: {phone_number}, OTP: {otp}")
        except ImportError as import_error:
            logger.error(f"SMS service not available: {str(import_error)}")
            # Fallback to email
            if user.Email:
                try:
                    from .notification_service import NotificationService
                    notification_service = NotificationService()
                    notification_data = {
                        'notification_type': 'passwordResetOTP',
                        'email': user.Email,
                        'email_type': 'gmail',
                        'template_data': [
                            user.FirstName or user.UserName or 'User',
                            otp,
                            '5 minutes',
                            'GRC Platform'
                        ],
                    }
                    email_result = notification_service.send_multi_channel_notification(notification_data)
                    logger.info(f"Profile edit OTP sent via email (fallback) to {user.Email}")
                except Exception as email_error:
                    logger.error(f"Failed to send OTP via email: {str(email_error)}")
                    logger.error(f"[MANUAL OTP] User: {user.UserName}, Phone: {phone_number}, OTP: {otp}")
                    print(f"[PROFILE EDIT OTP] User: {user.UserName}, Phone: {phone_number}, OTP: {otp}")
        except Exception as send_error:
            logger.error(f"Error sending profile edit OTP: {str(send_error)}")
            import traceback
            logger.error(traceback.format_exc())
            # Still return success to user (don't reveal if SMS failed)
        
        return Response({
            'success': True,
            'message': f'OTP sent to your mobile number ending in {phone_number[-4:] if len(phone_number) >= 4 else "****"}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in send_profile_edit_otp: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'Failed to send OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])  # Allow both authenticated and unauthenticated requests
@permission_classes([AllowAny])
def verify_profile_edit_otp(request):
    """
    Verify OTP for profile editing
    POST /api/profile-edit-otp/verify/
    
    Body: {
        "otp": "123456"
    }
    """
    try:
        # Get current user
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        data = request.data
        otp = data.get('otp')
        
        if not otp:
            return Response({
                'success': False,
                'message': 'OTP is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check OTP from session
        stored_otp = request.session.get('profile_edit_otp')
        stored_user_id = request.session.get('profile_edit_user_id')
        otp_expiry = request.session.get('profile_edit_otp_expiry')
        
        # If session data is missing, try memory storage
        if not stored_otp or str(user_id) != stored_user_id:
            logger.warning(f"Profile edit OTP - Missing session data, trying memory storage")
            memory_data = profile_edit_otp_storage.get(str(user_id))
            if memory_data:
                stored_otp = memory_data['otp']
                otp_expiry = memory_data['expiry']
                logger.info(f"Profile edit OTP - Found OTP in memory")
            else:
                return Response({
                    'success': False,
                    'message': 'No OTP request found. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if OTP has expired
        if datetime.now().timestamp() > otp_expiry:
            # Clear expired OTP
            if 'profile_edit_otp' in request.session:
                del request.session['profile_edit_otp']
            if 'profile_edit_user_id' in request.session:
                del request.session['profile_edit_user_id']
            if 'profile_edit_otp_expiry' in request.session:
                del request.session['profile_edit_otp_expiry']
            request.session.save()
            
            if str(user_id) in profile_edit_otp_storage:
                del profile_edit_otp_storage[str(user_id)]
            
            return Response({
                'success': False,
                'message': 'OTP has expired. Please request a new OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        if otp == stored_otp:
            # Mark OTP as verified in session
            request.session['profile_edit_verified'] = True
            request.session['profile_edit_verified_at'] = datetime.now().timestamp()
            request.session['profile_edit_verified_user_id'] = str(user_id)
            request.session.save()
            
            # Clean up OTP storage
            if 'profile_edit_otp' in request.session:
                del request.session['profile_edit_otp']
            if 'profile_edit_user_id' in request.session:
                del request.session['profile_edit_user_id']
            if 'profile_edit_otp_expiry' in request.session:
                del request.session['profile_edit_otp_expiry']
            request.session.save()
            
            if str(user_id) in profile_edit_otp_storage:
                del profile_edit_otp_storage[str(user_id)]
            
            logger.info(f"Profile edit OTP verified successfully for user {user_id}")
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully. You can now edit your profile.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Invalid OTP. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in verify_profile_edit_otp: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Failed to verify OTP. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])  # Allow both authenticated and unauthenticated requests
@permission_classes([AllowAny])
def check_profile_edit_verification(request):
    """
    Check if user has verified OTP for profile editing
    GET /api/profile-edit-otp/check/
    """
    try:
        # Get current user
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'verified': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if verified in session
        verified = request.session.get('profile_edit_verified', False)
        verified_user_id = request.session.get('profile_edit_verified_user_id')
        verified_at = request.session.get('profile_edit_verified_at')
        
        # Check if verification is for current user and not expired (15 minutes)
        if verified and str(user_id) == verified_user_id:
            if verified_at and datetime.now().timestamp() - verified_at < 900:  # 15 minutes
                return Response({
                    'success': True,
                    'verified': True,
                    'message': 'Profile edit verification is active'
                }, status=status.HTTP_200_OK)
            else:
                # Verification expired
                request.session['profile_edit_verified'] = False
                request.session.save()
        
        return Response({
            'success': True,
            'verified': False,
            'message': 'Profile edit verification required'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in check_profile_edit_verification: {str(e)}")
        return Response({
            'success': False,
            'verified': False,
            'message': 'Failed to check verification status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# In-memory OTP storage for portability
portability_otp_storage = {}


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def send_portability_otp(request):
    """
    Send OTP to user's mobile phone for data portability verification
    POST /api/portability-otp/send/
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"Portability OTP request from user ID: {user_id}")
        
        try:
            user = Users.objects.get(UserId=user_id)
            user.refresh_from_db()
            logger.info(f"Portability OTP: Retrieved user {user_id} ({user.UserName}) from RDS database")
        except Users.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        phone_number = user.PhoneNumber
        logger.info(f"Portability OTP: Phone number retrieved from RDS: '{phone_number}'")
        
        if not phone_number or not phone_number.strip():
            return Response({
                'success': False,
                'message': 'Phone number not found. Please add a phone number to your profile first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        phone_number = phone_number.strip()
        logger.info(f"Portability OTP: Using phone number: {phone_number}")
        
        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store OTP in session
        request.session['portability_otp'] = otp
        request.session['portability_user_id'] = str(user_id)
        request.session['portability_otp_expiry'] = datetime.now().timestamp() + 300  # 5 minutes
        request.session.save()
        
        # Store in memory as fallback
        portability_otp_storage[str(user_id)] = {
            'otp': otp,
            'expiry': datetime.now().timestamp() + 300,
            'phone': user.PhoneNumber
        }
        
        # Send OTP via SMS
        try:
            from .sms_service import get_sms_service
            sms_service = get_sms_service()
            user_name = user.FirstName or user.UserName or 'User'
            
            sms_result = sms_service.send_otp(phone_number, otp, user_name, purpose='data export')
            
            if sms_result.get('success'):
                logger.info(f"✅ Portability OTP sent via SMS to {phone_number}")
            else:
                logger.warning(f"Failed to send OTP via SMS: {sms_result.get('error')}")
                # Fallback to email
                if user.Email:
                    try:
                        from .notification_service import NotificationService
                        notification_service = NotificationService()
                        notification_data = {
                            'notification_type': 'passwordResetOTP',
                            'email': user.Email,
                            'email_type': 'gmail',
                            'template_data': [
                                user_name,
                                otp,
                                '5 minutes',
                                'GRC Platform'
                            ],
                        }
                        notification_service.send_multi_channel_notification(notification_data)
                        logger.info(f"Portability OTP sent via email (fallback) to {user.Email}")
                    except Exception as email_error:
                        logger.error(f"Failed to send OTP via email: {str(email_error)}")
        except Exception as send_error:
            logger.error(f"Error sending portability OTP: {str(send_error)}")
        
        return Response({
            'success': True,
            'message': f'OTP sent to your mobile number ending in {phone_number[-4:] if len(phone_number) >= 4 else "****"}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in send_portability_otp: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'Failed to send OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def verify_portability_otp(request):
    """
    Verify OTP for data portability
    POST /api/portability-otp/verify/
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        data = request.data
        otp = data.get('otp')
        
        if not otp:
            return Response({
                'success': False,
                'message': 'OTP is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check OTP from session
        stored_otp = request.session.get('portability_otp')
        stored_user_id = request.session.get('portability_user_id')
        otp_expiry = request.session.get('portability_otp_expiry')
        
        # Try memory storage if session data missing
        if not stored_otp or str(user_id) != stored_user_id:
            memory_data = portability_otp_storage.get(str(user_id))
            if memory_data:
                stored_otp = memory_data['otp']
                otp_expiry = memory_data['expiry']
            else:
                return Response({
                    'success': False,
                    'message': 'No OTP request found. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if expired
        if datetime.now().timestamp() > otp_expiry:
            # Clear expired OTP
            if 'portability_otp' in request.session:
                del request.session['portability_otp']
            if 'portability_user_id' in request.session:
                del request.session['portability_user_id']
            if 'portability_otp_expiry' in request.session:
                del request.session['portability_otp_expiry']
            request.session.save()
            
            if str(user_id) in portability_otp_storage:
                del portability_otp_storage[str(user_id)]
            
            return Response({
                'success': False,
                'message': 'OTP has expired. Please request a new OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        if otp == stored_otp:
            # Mark as verified
            request.session['portability_verified'] = True
            request.session['portability_verified_at'] = datetime.now().timestamp()
            request.session['portability_verified_user_id'] = str(user_id)
            request.session.save()
            
            # Clean up OTP storage
            if 'portability_otp' in request.session:
                del request.session['portability_otp']
            if 'portability_user_id' in request.session:
                del request.session['portability_user_id']
            if 'portability_otp_expiry' in request.session:
                del request.session['portability_otp_expiry']
            request.session.save()
            
            if str(user_id) in portability_otp_storage:
                del portability_otp_storage[str(user_id)]
            
            logger.info(f"Portability OTP verified successfully for user {user_id}")
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully. You can now export your data.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Invalid OTP. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in verify_portability_otp: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': 'Failed to verify OTP. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def check_portability_verification(request):
    """
    Check if user has verified OTP for data portability
    GET /api/portability-otp/check/
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return Response({
                'success': False,
                'verified': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        verified = request.session.get('portability_verified', False)
        verified_user_id = request.session.get('portability_verified_user_id')
        verified_at = request.session.get('portability_verified_at')
        
        if verified and str(user_id) == verified_user_id:
            if verified_at and datetime.now().timestamp() - verified_at < 900:  # 15 minutes
                return Response({
                    'success': True,
                    'verified': True,
                    'message': 'Portability verification is active'
                }, status=status.HTTP_200_OK)
            else:
                request.session['portability_verified'] = False
                request.session.save()
        
        return Response({
            'success': True,
            'verified': False,
            'message': 'Portability verification required'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in check_portability_verification: {str(e)}")
        return Response({
            'success': False,
            'verified': False,
            'message': 'Failed to check verification status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

