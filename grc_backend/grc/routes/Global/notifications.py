from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import connection
from datetime import datetime
import uuid

# Simple in-memory storage for notifications (in production, use database)
notifications_storage = []

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
        print(f"Error getting user email for user_id {user_id}: {e}")
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
                print(f"✅ Stored notification in database: id={db_notification_id}, user_id={user_id_str}, email={user_email}")
        except Exception as db_err:
            print(f"⚠️  Error storing notification in database: {db_err}")
            # Continue to store in memory as fallback
       
        # Also add to in-memory storage for immediate access
        notifications_storage.append(notification_data)
       
        # Keep only last 1000 notifications to prevent memory issues
        if len(notifications_storage) > 1000:
            notifications_storage.pop(0)
       
        print(f"✅ Created notification: user_id={user_id_str}, audit_id={audit_id}, total_stored={len(notifications_storage)}")
        return notification_data
    except Exception as e:
        print(f"Error creating audit completion notification: {e}")
        import traceback
        traceback.print_exc()
        return None
 
 
@csrf_exempt
@require_http_methods(["POST"])
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
        
        # Get user_id from JWT authentication or request data
        user_id = None
        
        # First try to get from authenticated user
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'UserId'):
            user_id = str(request.user.UserId)
        elif hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            user_id = str(request.user.id)
        
        # Fallback to request data
        if not user_id:
            user_id = data.get('user_id', 'default_user')
        
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
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_notifications(request):
    """
    Get all notifications for a user
    """
    try:
        # Get user_id from JWT authentication or query parameter
        user_id = None
         # Debug: Check what's in request.GET
        print(f"📬 DEBUG: request.GET = {dict(request.GET)}")
        print(f"📬 DEBUG: request.GET.get('user_id') = {request.GET.get('user_id')}")
       
        # First try to get from authenticated user (only if it's actually set and not None)
        if hasattr(request, 'user') and request.user:
            if hasattr(request.user, 'UserId') and request.user.UserId is not None:
                user_id = str(request.user.UserId)
                print(f"📬 DEBUG: Got user_id from request.user.UserId = {user_id}")
            elif hasattr(request.user, 'id') and request.user.id is not None:
                user_id = str(request.user.id)
                print(f"📬 DEBUG: Got user_id from request.user.id = {user_id}")
            else:
                print(f"📬 DEBUG: request.user exists but UserId/id is None, will use GET parameter")
       
        # Fallback to query parameter (this should work even if user is authenticated)
        if not user_id:
            # request.GET.get() can return a list if multiple values, so get the first one
            user_id_raw = request.GET.get('user_id')
            if isinstance(user_id_raw, list):
                user_id = user_id_raw[0] if user_id_raw else None
            else:
                user_id = user_id_raw
            print(f"📬 DEBUG: Got user_id from request.GET.get('user_id') = {user_id} (raw: {user_id_raw})")
            if not user_id:
                # Try alternative methods to get user_id
                if hasattr(request, 'query_params'):  # DRF Request
                    user_id = request.query_params.get('user_id')
                    print(f"📬 DEBUG: Got user_id from request.query_params.get('user_id') = {user_id}")
               
                # Try parsing from request path directly as fallback
                if not user_id and hasattr(request, 'get_full_path'):
                    import urllib.parse
                    full_path = request.get_full_path()
                    print(f"📬 DEBUG: request.get_full_path() = {full_path}")
                    parsed = urllib.parse.urlparse(full_path)
                    query_params = urllib.parse.parse_qs(parsed.query)
                    print(f"📬 DEBUG: Parsed query_params = {query_params}")
                    if 'user_id' in query_params:
                        user_id = query_params['user_id'][0] if query_params['user_id'] else None
                        print(f"📬 DEBUG: Got user_id from parsed query string = {user_id}")
               
                # Final fallback
                if not user_id:
                    user_id = 'default_user'
                    print(f"📬 DEBUG: Using default_user as fallback")
       
        # Ensure user_id is a string for comparison
        if user_id is not None:
            user_id = str(user_id)
       
        # Get user email to query database
        user_email = None
        if user_id and user_id != 'default_user':
            try:
                user_email = get_user_email_from_id(int(user_id))
            except (ValueError, TypeError):
                pass
       
        # Query database for notifications
        db_notifications = []
        try:
            with connection.cursor() as cursor:
                if user_email:
                    # Query by email (recipient field)
                    cursor.execute("""
                        SELECT id, recipient, type, channel, success, created_at, FrameworkId
                        FROM notifications
                        WHERE recipient = %s AND type = 'audit_completion' AND channel = 'in_app'
                        ORDER BY created_at DESC
                        LIMIT 100
                    """, (user_email,))
                else:
                    # Fallback: query by user_id pattern in recipient
                    cursor.execute("""
                        SELECT id, recipient, type, channel, success, created_at, FrameworkId
                        FROM notifications
                        WHERE recipient LIKE %s AND type = 'audit_completion' AND channel = 'in_app'
                        ORDER BY created_at DESC
                        LIMIT 100
                    """, (f'user_{user_id}%',))
               
                columns = [col[0] for col in cursor.description]
                for row in cursor.fetchall():
                    db_notif = dict(zip(columns, row))
                    # Transform database format to frontend format
                    db_notifications.append({
                        'id': str(db_notif['id']),
                        'title': 'AI Audit Completed',
                        'message': f'AI audit completed. Click to view details.',
                        'category': 'audit',
                        'priority': 'medium',
                        'createdAt': db_notif['created_at'].isoformat() if db_notif['created_at'] else datetime.now().isoformat(),
                        'status': {
                            'isRead': False,
                            'readAt': None
                        },
                        'user_id': user_id,
                        'metadata': {
                            'type': 'audit_completion',
                            'db_id': db_notif['id']
                        }
                    })
        except Exception as db_err:
            print(f"⚠️  Error querying database notifications: {db_err}")
       
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
       
        # Debug: Show all notifications
        print(f"📬 get_notifications: user_id={user_id}, found {len(all_notifications)} notifications (db: {len(db_notifications)}, memory: {len(memory_notifications)})")
        if all_notifications:
            print(f"📬 Sample notifications:")
            for idx, notif in enumerate(all_notifications[:3]):
                print(f"   [{idx}] id={notif.get('id')}, user_id={notif.get('user_id')}, title={notif.get('title')}")
       
        user_notifications = all_notifications
       
 
        
        return JsonResponse({
            'status': 'success',
            'notifications': user_notifications,
            'user_id': user_id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mark_as_read(request):
    """
    Mark a notification as read
    """
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        # Find and update notification (in production, update database)
        for notification in notifications_storage:
            if notification['id'] == notification_id:
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
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """
    Mark all notifications as read for a user
    EXCEPT acknowledgement notifications - they must be acknowledged first
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 'default_user')
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
            'message': str(e)
        }, status=500) 