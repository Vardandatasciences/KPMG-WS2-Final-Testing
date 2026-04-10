from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import connection
from ...debug_utils import debug_print
from datetime import datetime
import uuid
import time
from threading import Lock
from collections import defaultdict

# Simple in-memory storage for notifications (in production, use database)
notifications_storage = []

# --- Event notification anti-spam (in-process; shared across workers only within one process) ---
_EVENT_NOTIF_LOCK = Lock()
_EVENT_NOTIF_DEDUP = {}
_EVENT_NOTIF_EMAIL_TIMESTAMPS = defaultdict(list)
_EVENT_NOTIF_INAPP_TIMESTAMPS = defaultdict(list)

EVENT_NOTIF_DEDUP_SECONDS = 120
EVENT_NOTIF_MAX_EMAIL_PER_RECIPIENT_PER_MIN = 20
EVENT_NOTIF_MAX_INAPP_PER_USER_PER_MIN = 40
_EVENT_NOTIF_DEDUP_PRUNE_AT = 8000


def _norm_event_notif_email(email):
    return str(email or "").strip().lower()


def _event_notif_recipient_key(channel, email, user_id):
    if channel == "email":
        return _norm_event_notif_email(email)
    if channel == "whatsapp":
        return str(user_id or email or "").strip()
    return str(user_id or "").strip() or _norm_event_notif_email(email)


def _event_notif_dedup_key(channel, recipient_key, notification_type, event_id, dedup_extra=""):
    return (
        channel,
        recipient_key,
        str(notification_type or ""),
        str(event_id if event_id is not None else ""),
        str(dedup_extra or ""),
    )


def _prune_event_notif_dedup():
    if len(_EVENT_NOTIF_DEDUP) <= _EVENT_NOTIF_DEDUP_PRUNE_AT:
        return
    now = time.time()
    cutoff = now - (EVENT_NOTIF_DEDUP_SECONDS * 3)
    stale = [k for k, v in _EVENT_NOTIF_DEDUP.items() if v < cutoff]
    for k in stale[:4000]:
        del _EVENT_NOTIF_DEDUP[k]


def event_notification_allow(email, user_id, notification_type, event_id, channel, dedup_extra=""):
    """
    Returns (True, None) to send, or (False, reason) to skip (dedup / rate limit).
    channel: 'email' | 'in_app' | 'whatsapp'
    """
    now = time.time()
    recipient_key = _event_notif_recipient_key(channel, email, user_id)
    if not recipient_key:
        return True, None

    dk = _event_notif_dedup_key(channel, recipient_key, notification_type, event_id, dedup_extra)
    with _EVENT_NOTIF_LOCK:
        last = _EVENT_NOTIF_DEDUP.get(dk)
        if last is not None and (now - last) < EVENT_NOTIF_DEDUP_SECONDS:
            return False, "dedup"

        if channel == "email":
            arr = _EVENT_NOTIF_EMAIL_TIMESTAMPS[recipient_key]
            cutoff = now - 60.0
            arr[:] = [t for t in arr if t > cutoff]
            if len(arr) >= EVENT_NOTIF_MAX_EMAIL_PER_RECIPIENT_PER_MIN:
                return False, "email_rate_limit"

        if channel == "in_app":
            arr = _EVENT_NOTIF_INAPP_TIMESTAMPS[recipient_key]
            cutoff = now - 60.0
            arr[:] = [t for t in arr if t > cutoff]
            if len(arr) >= EVENT_NOTIF_MAX_INAPP_PER_USER_PER_MIN:
                return False, "in_app_rate_limit"

        if channel == "whatsapp":
            wa_key = "wa:" + recipient_key
            arr = _EVENT_NOTIF_EMAIL_TIMESTAMPS[wa_key]
            cutoff = now - 60.0
            arr[:] = [t for t in arr if t > cutoff]
            if len(arr) >= EVENT_NOTIF_MAX_EMAIL_PER_RECIPIENT_PER_MIN:
                return False, "whatsapp_rate_limit"

    return True, None


def event_notification_record_sent(email, user_id, notification_type, event_id, channel, dedup_extra=""):
    now = time.time()
    recipient_key = _event_notif_recipient_key(channel, email, user_id)
    if not recipient_key:
        return
    dk = _event_notif_dedup_key(channel, recipient_key, notification_type, event_id, dedup_extra)
    with _EVENT_NOTIF_LOCK:
        _EVENT_NOTIF_DEDUP[dk] = now
        _prune_event_notif_dedup()
        if channel == "email":
            _EVENT_NOTIF_EMAIL_TIMESTAMPS[_norm_event_notif_email(email)].append(now)
        elif channel == "in_app":
            _EVENT_NOTIF_INAPP_TIMESTAMPS[recipient_key].append(now)
        elif channel == "whatsapp":
            _EVENT_NOTIF_EMAIL_TIMESTAMPS["wa:" + recipient_key].append(now)


def send_event_aware_multi_channel(notification_service, notification_data, event_id, recipient_user_id=None, dedup_extra=""):
    """
    Wraps NotificationService.send_multi_channel_notification with event-specific dedup and rate limits.
    Mutates a copy of notification_data only; does not record sends unless a channel actually succeeds.
    """
    ntype = notification_data.get("notification_type")
    nd = dict(notification_data)
    email = nd.get("email")
    wa = nd.get("whatsapp_number")

    if email and nd.get("email_type"):
        ok, reason = event_notification_allow(email, recipient_user_id, ntype, event_id, "email", dedup_extra=dedup_extra)
        if not ok:
            debug_print(
                f"Event notification email suppressed ({reason}): {email} type={ntype} event={event_id}"
            )
            nd["email"] = None
            nd["email_type"] = None

    if wa:
        ok, reason = event_notification_allow(wa, wa, ntype, event_id, "whatsapp", dedup_extra=dedup_extra)
        if not ok:
            debug_print(f"Event notification whatsapp suppressed ({reason}): {wa} type={ntype} event={event_id}")
            nd["whatsapp_number"] = None

    result = notification_service.send_multi_channel_notification(nd)
    if not result.get("success"):
        return result

    det = result.get("details")
    if isinstance(det, dict):
        if det.get("email") and email:
            event_notification_record_sent(email, recipient_user_id, ntype, event_id, "email", dedup_extra=dedup_extra)
        if det.get("whatsapp") and wa:
            event_notification_record_sent(wa, wa, ntype, event_id, "whatsapp", dedup_extra=dedup_extra)

    return result


def append_event_notification_in_app(notification, event_id, notification_type, dedup_extra=""):
    """
    Append to notifications_storage with the same anti-spam rules as outbound event emails.
    """
    uid = notification.get("user_id")
    ok, reason = event_notification_allow(None, uid, notification_type, event_id, "in_app", dedup_extra=dedup_extra)
    if not ok:
        debug_print(
            f"Event in-app notification suppressed ({reason}): user={uid} type={notification_type} event={event_id}"
        )
        return False
    notifications_storage.append(notification)
    if len(notifications_storage) > 1000:
        notifications_storage.pop(0)
    event_notification_record_sent(None, uid, notification_type, event_id, "in_app", dedup_extra=dedup_extra)
    return True

def get_user_email_from_id(user_id):
    """Get user email from user_id"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Email FROM users WHERE UserId = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
        return None
    except Exception as e:
        debug_print(f"Error getting user email for user_id {user_id}: {e}")
        return None
 
def create_audit_completion_notification(audit_id, audit_name, document_count, user_id):
    """
    Create a notification when an AI audit is automatically completed.
    Stores in both database and in-memory storage.
   
    Args:
        audit_id: The audit ID
        audit_name: The name of the audit
        document_count: Number of documents processed
        user_id: User ID to receive the notification (must be numeric UserId, not username)
    """
    try:
        # Ensure user_id is converted to string for consistency with get_notifications
        # user_id should already be numeric UserId from the caller
        user_id_str = str(user_id) if user_id else 'system'
       
        # Get user email for database storage
        user_email = get_user_email_from_id(user_id) if user_id else None
       
        notification_data = {
            'id': str(uuid.uuid4()),
            'title': 'AI Audit Completed',
            'message': f'AI audit performed for {audit_name}. {document_count} document(s) analyzed. Click to view details.',
            'category': 'audit',
            'priority': 'medium',
            'createdAt': datetime.now().isoformat(),
            'status': {
                'isRead': False,
                'readAt': None
            },
            'user_id': user_id_str,
            'metadata': {
                'audit_id': audit_id,
                'document_count': document_count,
                'action_url': f'/audit/{audit_id}/ai-audit',
                'type': 'audit_completion'
            }
        }
       
        # Store in database
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO notifications
                    (recipient, type, channel, success, error, created_at, FrameworkId)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_email or f'user_{user_id}',  # recipient
                    'audit_completion',  # type
                    'in_app',  # channel
                    1,  # success
                    None,  # error
                    datetime.now(),  # created_at
                    None  # FrameworkId (can be NULL)
                ))
                db_notification_id = cursor.lastrowid
                debug_print(f"✅ Stored notification in database: id={db_notification_id}, user_id={user_id_str}, email={user_email}")
        except Exception as db_err:
            debug_print(f"⚠️  Error storing notification in database: {db_err}")
            # Continue to store in memory as fallback
       
        # Also add to in-memory storage for immediate access
        notifications_storage.append(notification_data)
       
        # Keep only last 1000 notifications to prevent memory issues
        if len(notifications_storage) > 1000:
            notifications_storage.pop(0)
       
        debug_print(f"✅ Created notification: user_id={user_id_str}, audit_id={audit_id}, total_stored={len(notifications_storage)}")
        return notification_data
    except Exception as e:
        debug_print(f"Error creating audit completion notification: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_ai_audit_evidence_reminder_notification(audit_id, user_id, framework_id=None, due_days_threshold=15):
    """
    Create an in-app notification when an AI audit has no evidence and due date is within threshold.
    Persists to database so it is visible when the user opens the app (e.g. from scheduler/management command).
    """
    try:
        user_id_str = str(user_id) if user_id else None
        if not user_id_str:
            return None
        user_email = get_user_email_from_id(int(user_id)) if user_id else None
        recipient = user_email or f'user_{user_id}'
        # Store audit_id in error field for get_notifications to build title/message/action_url
        error_payload = f'audit_id:{audit_id}'
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO notifications
                (recipient, type, channel, success, error, created_at, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                recipient,
                'ai_audit_evidence_reminder',
                'in_app',
                1,
                error_payload,
                datetime.now(),
                framework_id,
            ))
        debug_print(f"✅ Stored AI audit evidence reminder in DB: audit_id={audit_id}, user_id={user_id_str}")
        return True
    except Exception as e:
        debug_print(f"Error storing AI audit evidence reminder: {e}")
        import traceback
        traceback.print_exc()
        return None


@csrf_exempt
@require_http_methods(["POST"])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def push_notification(request):
    """
    Simple push notification function that can be called from any frontend operation
    """
    try:
        data = json.loads(request.body)
        
        # Extract notification data
        title = data.get('title', 'New Notification')
        message = data.get('message', 'You have a new notification')
        category = data.get('category', 'common')
        priority = data.get('priority', 'medium')
        
        # SECURE: Always use authenticated user ID
        auth_user = getattr(request, 'user', None)
        if not auth_user or not hasattr(auth_user, 'UserId'):
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = str(auth_user.UserId)
        
        # Create notification object
        notification = {
            'id': str(uuid.uuid4()),
            'title': title,
            'message': message,
            'category': category,
            'priority': priority,
            'createdAt': datetime.now().isoformat(),
            'status': {
                'isRead': False,
                'readAt': None
            },
            'user_id': user_id
        }
        
        # Store notification (in production, save to database)
        notifications_storage.append(notification)
        
        # Keep only last 100 notifications to prevent memory issues
        if len(notifications_storage) > 100:
            notifications_storage.pop(0)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification sent successfully',
            'notification': notification
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get all notifications for a user
    """
    auth_user = getattr(request, 'user', None)
    if not auth_user or not hasattr(auth_user, 'UserId'):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        # IDOR protection: always derive requester from auth context; allow admin override only.
        from ...rbac.utils import RBACUtils

        requester_user_id = RBACUtils.get_user_id_from_request(request)
        if not requester_user_id:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

        requested_user_id = requester_user_id
        user_id_param = request.GET.get('user_id')
        if user_id_param is not None and str(user_id_param).strip() != '':
            try:
                user_id_param_int = int(str(user_id_param))
            except (TypeError, ValueError):
                return JsonResponse({'status': 'error', 'message': 'Invalid user id'}, status=400)

            if int(requester_user_id) != user_id_param_int and not RBACUtils.is_system_admin(requester_user_id):
                return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

            requested_user_id = str(user_id_param_int)

        user_id = str(requested_user_id)
       
        # Get user email to query database
        user_email = None
        if user_id:
            try:
                user_email = get_user_email_from_id(int(user_id))
            except (ValueError, TypeError):
                pass
       
        # Query database for notifications (audit_completion and ai_audit_evidence_reminder)
        db_notifications = []
        try:
            with connection.cursor() as cursor:
                if user_email:
                    cursor.execute("""
                        SELECT id, recipient, type, channel, success, error, created_at, FrameworkId
                        FROM notifications
                        WHERE recipient = %s AND type IN ('audit_completion', 'ai_audit_evidence_reminder') AND channel = 'in_app'
                        ORDER BY created_at DESC
                        LIMIT 100
                    """, (user_email,))
                else:
                    # If we can't map to an email, do not attempt a wildcard lookup (can leak cross-user data).
                    db_notifications = []
                    columns = []
                    return JsonResponse({'status': 'success', 'notifications': [], 'count': 0})
                columns = [col[0] for col in cursor.description]
                for row in cursor.fetchall():
                    db_notif = dict(zip(columns, row))
                    created_at = db_notif['created_at'].isoformat() if db_notif.get('created_at') else datetime.now().isoformat()
                    notif_type = db_notif.get('type') or 'audit_completion'
                    if notif_type == 'ai_audit_evidence_reminder':
                        audit_id = None
                        err = db_notif.get('error') or ''
                        if err.startswith('audit_id:'):
                            try:
                                audit_id = int(err.split(':', 1)[1].strip())
                            except (ValueError, IndexError):
                                pass
                        title = 'Evidence not uploaded for AI Audit'
                        message = f'AI Audit {audit_id or "?"} has no evidence uploaded and due date is within 15 days. Please upload supporting documents.' if audit_id else 'An AI audit has no evidence uploaded. Please upload supporting documents.'
                        db_notifications.append({
                            'id': str(db_notif['id']),
                            'title': title,
                            'message': message,
                            'category': 'ai_audit',
                            'priority': 'medium',
                            'createdAt': created_at,
                            'status': {'isRead': False, 'readAt': None},
                            'user_id': user_id,
                            'metadata': {
                                'type': 'ai_audit_evidence_reminder',
                                'db_id': db_notif['id'],
                                'audit_id': audit_id,
                                'action_url': f'/audit/{audit_id}/ai-audit' if audit_id else None
                            }
                        })
                    else:
                        db_notifications.append({
                            'id': str(db_notif['id']),
                            'title': 'AI Audit Completed',
                            'message': f'AI audit completed. Click to view details.',
                            'category': 'audit',
                            'priority': 'medium',
                            'createdAt': created_at,
                            'status': {'isRead': False, 'readAt': None},
                            'user_id': user_id,
                            'metadata': {'type': 'audit_completion', 'db_id': db_notif['id']}
                        })
        except Exception as db_err:
            debug_print(f"⚠️  Error querying database notifications: {db_err}")
       
        # Also get from in-memory storage
        memory_notifications = [
            n for n in notifications_storage
            if str(n.get('user_id', '')) == str(user_id)
        ]
       
        # Combine and deduplicate (prefer memory notifications as they have full metadata)
        all_notifications = memory_notifications.copy()
        memory_ids = {n.get('id') for n in memory_notifications}
        for db_notif in db_notifications:
            if db_notif['id'] not in memory_ids:
                all_notifications.append(db_notif)
       
        # Sort by createdAt (newest first)
        all_notifications.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
       
        # Debug: Show all notifications (only when ENABLE_DEBUG_LOGGING=true)
        debug_print(f"📬 get_notifications: user_id={user_id}, found {len(all_notifications)} notifications (db: {len(db_notifications)}, memory: {len(memory_notifications)})")
        if all_notifications:
            debug_print(f"📬 Sample notifications:")
            for idx, notif in enumerate(all_notifications[:3]):
                debug_print(f"   [{idx}] id={notif.get('id')}, user_id={notif.get('user_id')}, title={notif.get('title')}")
       
        user_notifications = all_notifications
       
 
        
        return JsonResponse({
            'status': 'success',
            'notifications': user_notifications,
            'user_id': user_id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_read(request):
    """
    Mark a notification as read
    """
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        # SECURE: Get auth user
        auth_user = getattr(request, 'user', None)
        if not auth_user or not hasattr(auth_user, 'UserId'):
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = str(auth_user.UserId)

        # Find and update notification (in production, update database)
        for notification in notifications_storage:
            # SECURE: Check both notification ID and ownership
            if notification['id'] == notification_id and notification['user_id'] == user_id:
                notification['status']['isRead'] = True
                notification['status']['readAt'] = datetime.now().isoformat()
                break
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification marked as read'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """
    Mark all notifications as read for a user
    EXCEPT acknowledgement notifications - they must be acknowledged first
    """
    try:
        # SECURE: Get auth user
        auth_user = getattr(request, 'user', None)
        if not auth_user or not hasattr(auth_user, 'UserId'):
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = str(auth_user.UserId)

        data = json.loads(request.body)
        exclude_acknowledgements = data.get('exclude_acknowledgements', False)
        
        # Mark all user notifications as read (in production, update database)
        # BUT exclude acknowledgement notifications if requested
        marked_count = 0
        skipped_count = 0
        
        for notification in notifications_storage:
            if notification.get('user_id') == user_id and not notification['status'].get('isRead', False):
                # Check if this is an acknowledgement notification
                is_acknowledgement = False
                if exclude_acknowledgements:
                    title = notification.get('title', '')
                    is_acknowledgement = (
                        'Acknowledgement Request' in title or 
                        'Policy Acknowledgement' in title
                    )
                
                # Only mark as read if it's not an acknowledgement notification
                if not is_acknowledgement:
                    notification['status']['isRead'] = True
                    notification['status']['readAt'] = datetime.now().isoformat()
                    marked_count += 1
                else:
                    skipped_count += 1
        
        return JsonResponse({
            'status': 'success',
            'message': f'Marked {marked_count} notifications as read' + 
                      (f' (skipped {skipped_count} acknowledgement notifications)' if skipped_count > 0 else '')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=500) 