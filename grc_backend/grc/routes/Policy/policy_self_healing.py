"""

Policy self-healing: remind the policy creator (or assigned custodian) on a frequency from StartDate,

and daily during the last 7 days before EndDate. When the creator has left, escalate to Policy Manager.

"""

from __future__ import annotations



import json

import logging

import uuid

from datetime import date

from typing import Optional



from django.conf import settings

from django.db import connection

from django.db.utils import ProgrammingError

from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt



from rest_framework import status

from rest_framework.authentication import BasicAuthentication

from rest_framework.decorators import api_view, authentication_classes, permission_classes

from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.response import Response



from ...jwt_auth import UnifiedJWTAuthentication

from ...models import (

    Policy,

    PolicyApproval,

    PolicyReviewReminderSent,

    PolicySelfHealEscalation,

    RBAC,

    Users,

)

from ...routes.Global.notification_service import NotificationService

from ...routes.Global.notifications import CsrfExemptSessionAuthentication, notifications_storage

from ...tenant_utils import get_tenant_id_from_request, require_tenant, tenant_filter



logger = logging.getLogger(__name__)



_escalation_table_ok: Optional[bool] = None





def _escalation_table_available() -> bool:

    global _escalation_table_ok

    if _escalation_table_ok is not None:

        return _escalation_table_ok

    try:

        with connection.cursor() as cur:

            cur.execute("SELECT 1 FROM policy_self_heal_escalation LIMIT 1")

        _escalation_table_ok = True

    except ProgrammingError:

        logger.warning(

            "policy_self_heal_escalation table missing; escalation features disabled until table exists"

        )

        _escalation_table_ok = False

    except Exception:

        _escalation_table_ok = False

    return _escalation_table_ok





def _today() -> date:

    return timezone.localdate() if settings.USE_TZ else date.today()





def _request_user_id(request) -> Optional[int]:

    uid = getattr(request.user, "UserId", None) or getattr(request.user, "id", None)

    if uid is None:

        return None

    try:

        return int(uid)

    except (TypeError, ValueError):

        return None





def resolve_policy_creator_user_id(policy: Policy) -> Optional[int]:

    """Prefer PolicyApproval submitter UserId; fallback match Users by CreatedByName."""

    pa = (

        PolicyApproval.objects.filter(PolicyId=policy.PolicyId)

        .order_by("-ApprovalId")

        .only("UserId")

        .first()

    )

    if pa and getattr(pa, "UserId", None):

        return int(pa.UserId)

    name = (policy.CreatedByName or "").strip()

    if not name:

        return None

    tenant_id = getattr(policy, "tenant_id", None)

    if tenant_id is not None:

        u = Users.objects.filter(tenant_id=tenant_id, UserName=name).only("UserId").first()

        if u:

            return int(u.UserId)

    # Legacy rows: policy TenantId may not match users.TenantId (e.g. policy=1, user=2).

    u = Users.objects.filter(UserName=name).only("UserId").first()

    if u:

        logger.info(

            "Self-heal: creator %s resolved by username (policy tenant=%s)",

            name,

            tenant_id,

        )

        return int(u.UserId)

    return None





def _user_is_active(user_id: int) -> bool:

    u = Users.objects.filter(UserId=user_id).only("IsActive").first()

    if not u:

        return False

    return bool(u.is_active)





def _is_policy_manager(user_id: int) -> bool:

    """Only Policy Manager (not GRC Administrator or broad edit_policy flags)."""

    rbac = RBAC.objects.filter(user_id=user_id, is_active="Y").first()

    if not rbac:

        return False

    return rbac.role == "Policy Manager"





def _policy_manager_user_ids(tenant_id: Optional[int] = None) -> list[int]:

    qs = RBAC.objects.filter(is_active="Y", role="Policy Manager")

    user_ids = list(qs.values_list("user_id", flat=True).distinct())

    if tenant_id is not None:

        user_ids = list(

            Users.objects.filter(

                UserId__in=user_ids,

                tenant_id=tenant_id,

                IsActive="Y",

            ).values_list("UserId", flat=True)

        )

    else:

        user_ids = list(

            Users.objects.filter(UserId__in=user_ids, IsActive="Y").values_list("UserId", flat=True)

        )

    return user_ids





def _pending_escalation(policy: Policy) -> Optional[PolicySelfHealEscalation]:

    if not _escalation_table_available():

        return None

    try:

        return (

            PolicySelfHealEscalation.objects.filter(

                policy=policy,

                status=PolicySelfHealEscalation.STATUS_PENDING,

            )

            .order_by("-id")

            .first()

        )

    except ProgrammingError:

        return None





def _assigned_escalation(policy: Policy) -> Optional[PolicySelfHealEscalation]:

    if not _escalation_table_available():

        return None

    try:

        return (

            PolicySelfHealEscalation.objects.filter(

                policy=policy,

                status=PolicySelfHealEscalation.STATUS_ASSIGNED,

            )

            .order_by("-assigned_at", "-id")

            .first()

        )

    except ProgrammingError:

        return None





def _assigned_custodian_user_id(policy: Policy) -> Optional[int]:

    esc = _assigned_escalation(policy)

    if esc and esc.assigned_user_id:

        return int(esc.assigned_user_id)

    return None





def _can_perform_self_heal_decision(policy: Policy, request) -> bool:

    uid = _request_user_id(request)

    if uid is None:

        return False

    creator_id = resolve_policy_creator_user_id(policy)

    if creator_id is not None and creator_id == uid:

        return True

    custodian_id = _assigned_custodian_user_id(policy)

    return custodian_id is not None and custodian_id == uid





def _creator_is_request_user(policy: Policy, request) -> bool:

    return _can_perform_self_heal_decision(policy, request)





def policy_should_remind_today(policy: Policy, today: date) -> bool:

    if policy.Status != "Approved":

        return False

    if policy.ActiveInactive not in ("Active", "Scheduled", None, ""):

        return False

    fw = policy.FrameworkId

    if fw is None:

        return False

    if getattr(fw, "Status", None) != "Approved" or getattr(fw, "ActiveInactive", None) != "Active":

        return False

    if policy.StartDate and policy.StartDate > today:

        return False

    if policy.EndDate and policy.EndDate < today:

        return False

    if not policy.EndDate:

        return False

    # Skip policies that use the new pre-scheduled reminder rules (avoid duplicate reminders)
    if hasattr(policy, 'reminder_rules') and policy.reminder_rules.exists():
        return False

    days_since = (today - policy.StartDate).days

    if days_since < 0:

        return False



    days_to_end = (policy.EndDate - today).days

    in_final_week = 0 <= days_to_end <= 7



    freq = max(1, int(policy.ReviewReminderFrequencyDays or 30))

    freq_hit = (days_since % freq) == 0



    return bool(in_final_week or freq_hit)





def _resolve_reminder_target(policy: Policy) -> tuple[str, Optional[int]]:

    """

    Returns (target_kind, user_id).

    target_kind: 'creator' | 'custodian' | 'escalate'

    """

    custodian_id = _assigned_custodian_user_id(policy)

    if custodian_id and _user_is_active(custodian_id):

        return "custodian", custodian_id



    creator_id = resolve_policy_creator_user_id(policy)

    if creator_id and _user_is_active(creator_id):

        return "creator", creator_id



    return "escalate", None





def _insert_db_notification(recipient: str, notif_type: str, policy: Policy, extra_error: str = "") -> Optional[int]:

    err = f"policy_id:{policy.PolicyId}"

    if extra_error:

        err = f"{err};{extra_error}"

    try:

        with connection.cursor() as cur:

            cur.execute(

                """

                INSERT INTO notifications (recipient, type, channel, success, error, created_at, FrameworkId)

                VALUES (%s, %s, %s, %s, %s, %s, %s)

                """,

                (

                    recipient,

                    notif_type,

                    "in_app",

                    1,

                    err,

                    timezone.now(),

                    policy.FrameworkId_id,

                ),

            )

            return cur.lastrowid

    except Exception as e:

        logger.exception("Self-heal DB notification failed policy=%s: %s", policy.PolicyId, e)

        return None





def _append_memory_notification(notification: dict) -> None:

    notifications_storage.append(notification)

    if len(notifications_storage) > 1000:

        notifications_storage.pop(0)





def _self_heal_email_enabled() -> bool:

    raw = getattr(settings, "POLICY_SELF_HEAL_SEND_EMAIL", True)

    if isinstance(raw, str):

        return raw.strip().lower() not in ("0", "false", "no", "")

    return bool(raw)





def _self_heal_max_manager_emails() -> int:

    try:

        return max(0, int(getattr(settings, "POLICY_SELF_HEAL_MAX_MANAGER_EMAILS", 5)))

    except (TypeError, ValueError):

        return 5





def _notify_renewal_user(

    policy: Policy,

    user_id: int,

    today: date,

    service: NotificationService,

    review_path: str,

    *,

    metadata_type: str = "policy_self_heal",

    db_type: str = "policy_review_self_heal",

) -> bool:

    from ...routes.Global.notifications import get_user_email_from_id



    raw_email = get_user_email_from_id(user_id)

    end_s = policy.EndDate.isoformat() if policy.EndDate else ""

    review_url = f"{review_path}?policyId={policy.PolicyId}"

    days_left = (policy.EndDate - today).days if policy.EndDate else None

    pname = (policy.PolicyName or "Policy").strip() or "Policy"

    recipient = (raw_email or "").strip() or f"user_{user_id}"



    did_notify = False

    db_notification_id = _insert_db_notification(recipient, db_type, policy)



    if db_notification_id:

        did_notify = True



    if raw_email and _self_heal_email_enabled():

        try:

            email_result = service.send_multi_channel_notification(

                {

                    "notification_type": "policyReviewSelfHeal",

                    "email": raw_email,

                    "email_type": "gmail",

                    "template_data": [

                        pname,

                        end_s,

                        review_url,

                        str(days_left) if days_left is not None else "",

                    ],

                    "dedup_enabled": False,

                }

            )

            if email_result and email_result.get("success"):

                did_notify = True

        except Exception as e:

            logger.exception("Self-heal email failed policy=%s: %s", policy.PolicyId, e)



    try:

        notif_id = str(db_notification_id) if db_notification_id else str(uuid.uuid4())

        notification = {

            "id": notif_id,

            "title": f'Policy review: "{pname}"',

            "message": (

                f'"{pname}" is due for review before {end_s}. '

                "Open the renewal page to keep the policy as-is or start an update in tailoring."

            ),

            "category": "policy",

            "priority": "high" if days_left is not None and days_left <= 7 else "medium",

            "createdAt": timezone.now().isoformat(),

            "status": {"isRead": False, "readAt": None},

            "user_id": str(user_id),

            "metadata": {

                "type": metadata_type,

                "policy_id": policy.PolicyId,

                "policy_name": pname,

                "framework_id": policy.FrameworkId_id,

                "action_url": (

                    f"/policy/renewal-review?policyId={policy.PolicyId}"

                    + ("&assigned=1" if metadata_type == "policy_self_heal_assigned" else "")

                ),

                "db_id": db_notification_id,

            },

        }

        if did_notify:

            _append_memory_notification(notification)

    except Exception as e:

        logger.exception("Self-heal in-app memory failed policy=%s: %s", policy.PolicyId, e)



    return did_notify





def _ensure_pending_escalation(policy: Policy) -> Optional[PolicySelfHealEscalation]:

    existing = _pending_escalation(policy)

    if existing:

        return existing

    if not _escalation_table_available():

        return None

    try:

        return PolicySelfHealEscalation.objects.create(

            policy=policy,

            status=PolicySelfHealEscalation.STATUS_PENDING,

            original_created_by_name=(policy.CreatedByName or "").strip() or None,

        )

    except ProgrammingError:

        return None





def _notify_policy_managers_escalation(

    policy: Policy,

    manager_ids: list[int],

    service: NotificationService,

    review_path: str,

) -> bool:

    pname = (policy.PolicyName or "Policy").strip() or "Policy"

    creator_name = (policy.CreatedByName or "Unknown").strip()

    end_s = policy.EndDate.isoformat() if policy.EndDate else ""

    dashboard_url = f"{review_path.rsplit('/policy/', 1)[0]}/policy/performance/dashboard?renewalEscalations=1"

    did_any = False



    email_cap = _self_heal_max_manager_emails()

    emails_sent = 0



    for mid in manager_ids:

        from ...routes.Global.notifications import get_user_email_from_id



        raw_email = get_user_email_from_id(mid)

        recipient = f"user:{mid}"

        db_id = _insert_db_notification(

            recipient,

            "policy_self_heal_manager_escalation",

            policy,

            extra_error=f"manager_user_id:{mid};creator:{creator_name}",

        )

        if db_id:

            did_any = True



        if raw_email and _self_heal_email_enabled() and emails_sent < email_cap:

            try:

                emails_sent += 1

                service.send_multi_channel_notification(

                    {

                        "notification_type": "policyReviewSelfHeal",

                        "email": raw_email,

                        "email_type": "gmail",

                        "template_data": [

                            pname,

                            end_s,

                            dashboard_url,

                            f"Creator unavailable ({creator_name}). Assign a custodian on the Policy Dashboard.",

                        ],

                        "dedup_enabled": False,

                    }

                )

            except Exception as e:

                logger.exception("Manager escalation email failed policy=%s manager=%s: %s", policy.PolicyId, mid, e)



        notif_id = str(db_id) if db_id else str(uuid.uuid4())

        _append_memory_notification(

            {

                "id": notif_id,

                "title": f'Assign renewal custodian: "{pname}"',

                "message": (

                    f'The creator ({creator_name}) is no longer active. '

                    f'Assign someone to handle renewal for "{pname}" (due {end_s}).'

                ),

                "category": "policy",

                "priority": "high",

                "createdAt": timezone.now().isoformat(),

                "status": {"isRead": False, "readAt": None},

                "user_id": str(mid),

                "metadata": {

                    "type": "policy_self_heal_manager",

                    "policy_id": policy.PolicyId,

                    "policy_name": pname,

                    "framework_id": policy.FrameworkId_id,

                    "action_url": "/policy/performance/dashboard?renewalEscalations=1",

                    "db_id": db_id,

                },

            }

        )



    return did_any





def auto_inactivate_expired_policies(for_date: Optional[date] = None) -> int:
    """Set ActiveInactive='Inactive' for policies whose EndDate has passed."""
    today = for_date or _today()
    count = Policy.objects.filter(
        EndDate__lt=today,
        ActiveInactive="Active",
    ).update(ActiveInactive="Inactive")
    if count:
        logger.info("Auto-inactivated %s expired policies (EndDate < %s)", count, today)
    return count


def execute_policy_self_heal_reminders(for_date: Optional[date] = None) -> dict:

    """Send at most one notification per policy per calendar day."""

    today = for_date or _today()

    auto_inactivate_expired_policies(for_date=today)

    service = NotificationService()

    base_url = (getattr(settings, "FRONTEND_BASE_URL", None) or "").rstrip("/") or "http://localhost:8080"

    review_path = f"{base_url}/policy/renewal-review"



    qs = (

        Policy.objects.filter(

            Status="Approved",

            FrameworkId__Status="Approved",

            FrameworkId__ActiveInactive="Active",

            StartDate__lte=today,

            EndDate__gte=today,

        )

        .select_related("FrameworkId")

        .order_by("PolicyId")

    )



    sent = 0

    skipped = 0

    escalated = 0

    errors: list[str] = []



    for policy in qs.iterator():

        if not policy_should_remind_today(policy, today):

            skipped += 1

            continue

        if PolicyReviewReminderSent.objects.filter(policy=policy, reminder_date=today).exists():

            skipped += 1

            continue



        target_kind, target_user_id = _resolve_reminder_target(policy)

        did_notify = False



        if target_kind in ("creator", "custodian") and target_user_id:

            try:

                did_notify = _notify_renewal_user(

                    policy,

                    target_user_id,

                    today,

                    service,

                    review_path,

                    metadata_type="policy_self_heal",

                )

            except Exception as e:

                errors.append(f"policy {policy.PolicyId} notify: {e}")

        else:

            tenant_id = getattr(policy, "tenant_id", None)

            manager_ids = _policy_manager_user_ids(tenant_id)

            if not manager_ids:

                logger.warning("Self-heal: no policy managers for policy %s", policy.PolicyId)

                errors.append(f"policy {policy.PolicyId}: no policy managers")

            else:

                try:

                    if _ensure_pending_escalation(policy) is None and not _escalation_table_available():

                        errors.append(f"policy {policy.PolicyId}: escalation table missing")

                    did_notify = _notify_policy_managers_escalation(

                        policy, manager_ids, service, review_path

                    )

                    if did_notify:

                        escalated += 1

                except Exception as e:

                    errors.append(f"policy {policy.PolicyId} escalate: {e}")



        if did_notify:

            PolicyReviewReminderSent.objects.get_or_create(policy=policy, reminder_date=today)

            sent += 1

        else:

            skipped += 1



    return {

        "date": str(today),

        "sent": sent,

        "skipped": skipped,

        "escalated": escalated,

        "errors": errors,

    }





def _parse_self_heal_webhook_body(request) -> dict:

    """Parse POST body without DRF raising ParseError on invalid JSON."""

    raw = getattr(request, "body", None) or b""

    if not raw:

        return {}

    try:

        text = raw.decode("utf-8").strip()

    except UnicodeDecodeError:

        return {}

    if not text:

        return {}

    try:

        parsed = json.loads(text)

        return parsed if isinstance(parsed, dict) else {}

    except json.JSONDecodeError:

        return {}





@csrf_exempt

@api_view(["POST"])

@authentication_classes([])

@permission_classes([AllowAny])

def run_policy_self_heal_reminders(request):

    """

    Called daily by the scheduler microservice (webhook POST).

    Header: X-Policy-Self-Heal-Secret must match settings.POLICY_SELF_HEAL_CRON_SECRET.

    """

    expected = (getattr(settings, "POLICY_SELF_HEAL_CRON_SECRET", None) or "").strip()

    body = _parse_self_heal_webhook_body(request)

    got_header = (request.headers.get("X-Policy-Self-Heal-Secret") or request.META.get("HTTP_X_POLICY_SELF_HEAL_SECRET") or "").strip()

    got_body = ""

    if isinstance(body, dict):

        got_body = (body.get("secret") or body.get("cron_secret") or "").strip()

    got = got_header or got_body

    if not expected:

        logger.error("POLICY_SELF_HEAL_CRON_SECRET is not set in Django settings/.env")

        return Response(

            {"detail": "Cron secret not configured on server"},

            status=status.HTTP_503_SERVICE_UNAVAILABLE,

        )

    if got != expected:

        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    raw = body.get("for_date") or request.query_params.get("for_date")

    for_date = None

    if raw:

        try:

            for_date = date.fromisoformat(str(raw)[:10])

        except ValueError:

            return Response({"error": "Invalid for_date"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        result = execute_policy_self_heal_reminders(for_date=for_date)

        return Response({"success": True, **result})

    except Exception as e:

        logger.exception("policy self-heal reminders failed: %s", e)

        return Response(

            {"success": False, "error": str(e)},

            status=status.HTTP_500_INTERNAL_SERVER_ERROR,

        )



@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def run_single_policy_reminder(request):
    """
    Called by the scheduler microservice for an individual exact_date schedule.
    Body: {"secret": "...", "policy_id": <id>, "rule_id": <id>}
    """
    expected = (getattr(settings, "POLICY_SELF_HEAL_CRON_SECRET", None) or "").strip()
    body = _parse_self_heal_webhook_body(request)
    got = ""
    if isinstance(body, dict):
        got = (body.get("secret") or body.get("cron_secret") or "").strip()
    if not expected:
        logger.error("POLICY_SELF_HEAL_CRON_SECRET is not set in Django settings/.env")
        return Response(
            {"detail": "Cron secret not configured on server"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if got != expected:
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    policy_id = body.get("policy_id")
    rule_id = body.get("rule_id")
    if not policy_id:
        return Response({"error": "policy_id required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        policy = Policy.objects.select_related("FrameworkId").get(PolicyId=policy_id)
    except Policy.DoesNotExist:
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)

    # Resolve target user (creator or assigned custodian)
    target_name, target_uid = _resolve_reminder_target(policy)
    if not target_uid:
        logger.info("Single reminder for policy %s: no active target user", policy_id)
        return Response({"success": False, "error": "No active target user"})

    today = timezone.now().date()
    review_path = f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:8080').rstrip('/')}/policy/renewal-review"
    service = NotificationService()
    did_notify = _notify_renewal_user(
        policy, target_uid, today, service, review_path,
        metadata_type="policy_self_heal",
        db_type="policy_review_self_heal",
    )

    # Mark schedule as sent (use schedule_id from payload to identify the exact schedule)
    from grc.models import PolicyReminderSchedule
    schedule_id = body.get("schedule_id")
    if schedule_id:
        PolicyReminderSchedule.objects.filter(
            policy=policy, schedule_id=schedule_id, status='scheduled'
        ).update(status='sent')
    else:
        # Fallback for schedules created before schedule_id was added to payload
        PolicyReminderSchedule.objects.filter(
            policy=policy, reminder_rule_id=rule_id, status='scheduled'
        ).update(status='sent')

    return Response({"success": True, "notified": did_notify})




@api_view(["GET"])

@authentication_classes([UnifiedJWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication])

@permission_classes([IsAuthenticated])

@require_tenant

@tenant_filter

def list_pending_self_heal_escalations(request):

    """Policy managers: policies needing custodian assignment."""

    uid = _request_user_id(request)

    if uid is None or not _is_policy_manager(uid):

        return Response({"error": "Policy Manager access required"}, status=status.HTTP_403_FORBIDDEN)



    tenant_id = get_tenant_id_from_request(request)

    escalations = (

        PolicySelfHealEscalation.objects.filter(

            status=PolicySelfHealEscalation.STATUS_PENDING,

            policy__tenant_id=tenant_id,

        )

        .select_related("policy", "policy__FrameworkId")

        .order_by("-created_at")

    )



    items = []

    for esc in escalations:

        p = esc.policy

        items.append(

            {

                "escalation_id": esc.id,

                "policy_id": p.PolicyId,

                "policy_name": p.PolicyName,

                "framework_id": p.FrameworkId_id,

                "framework_name": getattr(p.FrameworkId, "FrameworkName", None) if p.FrameworkId else None,

                "end_date": str(p.EndDate) if p.EndDate else None,

                "original_created_by_name": esc.original_created_by_name or p.CreatedByName,

                "created_at": esc.created_at.isoformat() if esc.created_at else None,

            }

        )



    return Response({"success": True, "escalations": items, "count": len(items)})





@api_view(["POST"])

@authentication_classes([UnifiedJWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication])

@permission_classes([IsAuthenticated])

@require_tenant

@tenant_filter

def assign_self_heal_custodian(request, policy_id: int):

    """Policy manager assigns an active user as renewal custodian (updates CreatedByName)."""

    uid = _request_user_id(request)

    if uid is None or not _is_policy_manager(uid):

        return Response({"error": "Policy Manager access required"}, status=status.HTTP_403_FORBIDDEN)



    tenant_id = get_tenant_id_from_request(request)

    try:

        policy = Policy.objects.select_related("FrameworkId").get(PolicyId=policy_id, tenant_id=tenant_id)

    except Policy.DoesNotExist:

        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)



    assignee_raw = request.data.get("assignee_user_id") or request.data.get("user_id")

    if assignee_raw is None:

        return Response({"error": "assignee_user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        assignee_id = int(assignee_raw)

    except (TypeError, ValueError):

        return Response({"error": "Invalid assignee_user_id"}, status=status.HTTP_400_BAD_REQUEST)



    assignee = Users.objects.filter(UserId=assignee_id, tenant_id=tenant_id, IsActive="Y").first()

    if not assignee:

        return Response({"error": "Assignee not found or inactive"}, status=status.HTTP_400_BAD_REQUEST)



    esc = _pending_escalation(policy) or _ensure_pending_escalation(policy)

    if not esc:

        return Response(

            {"error": "Escalation table not available; create policy_self_heal_escalation in MySQL first"},

            status=status.HTTP_503_SERVICE_UNAVAILABLE,

        )



    policy.CreatedByName = assignee.UserName

    policy.save(update_fields=["CreatedByName"])



    esc.status = PolicySelfHealEscalation.STATUS_ASSIGNED

    esc.assigned_user_id = assignee_id

    esc.assigned_by_user_id = uid

    esc.assigned_at = timezone.now()

    esc.save(

        update_fields=[

            "status",

            "assigned_user_id",

            "assigned_by_user_id",

            "assigned_at",

            "updated_at",

        ]

    )



    service = NotificationService()

    base_url = (getattr(settings, "FRONTEND_BASE_URL", None) or "").rstrip("/") or "http://localhost:8080"

    review_path = f"{base_url}/policy/renewal-review"

    today = _today()

    _notify_renewal_user(

        policy,

        assignee_id,

        today,

        service,

        review_path,

        metadata_type="policy_self_heal_assigned",

        db_type="policy_self_heal_assigned",

    )



    return Response(

        {

            "success": True,

            "policy_id": policy.PolicyId,

            "assigned_user_id": assignee_id,

            "assigned_user_name": assignee.UserName,

            "CreatedByName": policy.CreatedByName,

        }

    )





@api_view(["POST"])

@authentication_classes([UnifiedJWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication])

@permission_classes([IsAuthenticated])

@require_tenant

@tenant_filter

def policy_self_heal_decision(request, policy_id: int):

    """

    Creator or assigned custodian. action: 'approve' | 'keep' | 'update'.

    approve/keep: confirm renewal with no content changes (dates unchanged).

    update: redirect to tailoring to create a new version.

    """

    tenant_id = get_tenant_id_from_request(request)

    try:

        policy = Policy.objects.select_related("FrameworkId").get(PolicyId=policy_id, tenant_id=tenant_id)

    except Policy.DoesNotExist:

        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)



    if not _can_perform_self_heal_decision(policy, request):

        return Response(

            {"error": "Only the policy creator or assigned custodian can perform this action"},

            status=status.HTTP_403_FORBIDDEN,

        )



    action = (request.data.get("action") or "").strip().lower()

    if action == "keep":

        action = "approve"

    if action not in ("approve", "update"):

        return Response({"error": 'action must be "approve" or "update"'}, status=status.HTTP_400_BAD_REQUEST)



    if action == "update":

        fw_id = policy.FrameworkId_id

        return Response(

            {

                "success": True,

                "action": "update",

                "redirect_path": f"/create-policy/tailoring?frameworkId={fw_id}&policyId={policy_id}&selfHeal=1",

            }

        )



    return Response(

        {

            "success": True,

            "action": "approve",

            "message": "Policy renewal approved. The current version remains in effect with no date changes.",

            "Status": policy.Status,

            "StartDate": str(policy.StartDate) if policy.StartDate else None,

            "EndDate": str(policy.EndDate) if policy.EndDate else None,

        }

    )

