import json
import logging
import os
from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from grc.models import Framework

from .framework_update_checker import run_framework_update_check

logger = logging.getLogger(__name__)


def _to_date(value):
    """Normalize different date representations to a date object."""
    if not value:
        return None
    # If it's already a date object, return it directly
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            # Try multiple date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(value.split()[0], "%Y-%m-%d").date()
                except:
                    continue
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    if isinstance(value, datetime):
        return value.date()
    # Try to get date() method if it exists
    if hasattr(value, "date"):
        try:
            return value.date()
        except:
            pass
    return None


def _get_last_known_update_date(framework):
    """
    Pick the best available date to compare against:
    1) latestAmmendmentDate
    2) latestComparisionCheckDate
    3) CreatedByDate
    """
    for candidate in (
        framework.latestAmmendmentDate,
        framework.latestComparisionCheckDate,
        framework.CreatedByDate,
    ):
        parsed = _to_date(candidate)
        if parsed:
            return parsed.strftime("%Y-%m-%d")
    return "1900-01-01"


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def auto_check_all_frameworks(request):
    """
    Trigger a weekly (7-day) update check for every framework.

    - Uses latestComparisionCheckDate to strictly throttle checks to once per 7 days.
    - Only runs if at least 7 days have passed since the last check (same-day checks are skipped).
    - Runs during login/home load so users always see fresh status.
    - Set `force_run=true` to bypass the 7-day throttle.
    - Set `process_amendment=true` to process immediately (defaults to False).
    """
    api_key = getattr(settings, "PERPLEXITY_API_KEY", "")
    if not api_key:
        return Response(
            {"success": False, "error": "PERPLEXITY_API_KEY not configured."},
            status=500,
        )

    # Handle both DRF request.data and Django request.POST/body
    if hasattr(request, 'data'):
        force_run = bool(request.data.get("force_run", False))
        process_amendment = bool(request.data.get("process_amendment", False))
    else:
        import json
        if request.method == 'POST':
            try:
                if hasattr(request, 'body') and request.body:
                    body_data = json.loads(request.body)
                    force_run = bool(body_data.get("force_run", False))
                    process_amendment = bool(body_data.get("process_amendment", False))
                else:
                    force_run = bool(request.POST.get("force_run", False))
                    process_amendment = bool(request.POST.get("process_amendment", False))
            except:
                force_run = False
                process_amendment = False
        else:
            force_run = False
            process_amendment = False
    today = timezone.now().date()

    frameworks = Framework.objects.all()
    results = []
    skipped = 0
    processed = 0
    errors = 0

    for framework in frameworks:
        # Refresh the framework object from database to ensure we have latest data
        framework.refresh_from_db()
        
        # Also query directly from database to verify the value exists
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT latestComparisionCheckDate FROM frameworks WHERE FrameworkId = %s",
                [framework.FrameworkId]
            )
            row = cursor.fetchone()
            direct_db_value = row[0] if row else None
        
        # Get raw value from ORM - it's already a date object, use it directly
        raw_date_value = framework.latestComparisionCheckDate
        # If it's already a date object, use it directly; otherwise parse it
        if isinstance(raw_date_value, date):
            last_check_date = raw_date_value
        else:
            last_check_date = _to_date(raw_date_value)
        
        # Print detailed database information
        logger.info(
            "📊 DATABASE INFO | Framework id=%s name=%s | Raw ORM value: %s (type: %s) | Parsed date: %s | Today: %s",
            framework.FrameworkId,
            framework.FrameworkName,
            str(raw_date_value),
            type(raw_date_value).__name__,
            last_check_date.isoformat() if last_check_date else "None (first check)",
            today.isoformat(),
        )
        print(f"📊 DATABASE INFO | Framework id={framework.FrameworkId} name={framework.FrameworkName}")
        print(f"   ORM latestComparisionCheckDate: {raw_date_value} (type: {type(raw_date_value).__name__})")
        print(f"   Parsed date: {last_check_date.isoformat() if last_check_date else 'None (first check)'}")
        print(f"   Today: {today.isoformat()}")
        
        # Check date condition BEFORE calling framework update check function
        should_skip = False
        skip_reason = None
        days_since_check = None
        
        if not force_run:
            if last_check_date:
                # CRITICAL CHECK: If checked today, skip immediately (no need to calculate days)
                if last_check_date == today:
                    should_skip = True
                    skip_reason = "same_day"
                    days_since_check = 0
                    next_check_date = (today + timedelta(days=7)).isoformat()
                else:
                    days_since_check = (today - last_check_date).days
                    
                    # CRITICAL: Skip if less than 7 days have passed (1-6 = recent days)
                    # Only run if 7 or more days have passed
                    if days_since_check < 7:
                        should_skip = True
                        skip_reason = "recent_check"
                        next_check_date = (last_check_date + timedelta(days=7)).isoformat()
            else:
                # No last_check_date exists - this is the first check, proceed
                logger.info(
                    "🆕 First check for framework | id=%s name=%s (no previous check date)",
                    framework.FrameworkId,
                    framework.FrameworkName,
                )
        
        # If date check fails (less than 7 days), skip the framework update check
        if should_skip:
            skipped += 1
            status_key = "skipped_same_day" if skip_reason == "same_day" else "skipped_recent"
            message = (
                f"Already checked today ({today.isoformat()}). Next check: {next_check_date} (7 days required)."
                if skip_reason == "same_day"
                else f"Checked {days_since_check} day(s) ago. Next check: {next_check_date} (7 days required)."
            )
            
            results.append(
                {
                    "framework_id": framework.FrameworkId,
                    "framework_name": framework.FrameworkName,
                    "status": status_key,
                    "message": message,
                    "last_check_date": last_check_date.isoformat(),
                    "next_check_date": next_check_date,
                    "days_since_check": days_since_check,
                }
            )
            
            logger.info(
                "⏭️ SKIPPING framework check (%s) | id=%s name=%s last_check=%s today=%s days_since=%s next_check=%s",
                skip_reason.upper(),
                framework.FrameworkId,
                framework.FrameworkName,
                last_check_date.isoformat(),
                today.isoformat(),
                days_since_check,
                next_check_date,
            )
            print(f"⏭️ SKIPPING framework check ({skip_reason.upper()}) | id={framework.FrameworkId} name={framework.FrameworkName} | days_since={days_since_check} | next_check={next_check_date}")
            continue
        
        # Only call framework update check if date condition passes (7+ days or first check)
        last_date_str = _get_last_known_update_date(framework)

        try:
            logger.info(
                "✅ PROCEEDING with framework check | id=%s name=%s last_known=%s last_check_date=%s",
                framework.FrameworkId,
                framework.FrameworkName,
                last_date_str,
                last_check_date.isoformat() if last_check_date else "None (first check)",
            )
            print(f"✅ PROCEEDING with framework check | id={framework.FrameworkId} name={framework.FrameworkName} | last_check_date={last_check_date.isoformat() if last_check_date else 'None (first check)'}")

            # Decrypt framework name before sending to API (FrameworkName is encrypted in database)
            from grc.utils.data_encryption import decrypt_data
            try:
                framework_name = framework.FrameworkName_plain if hasattr(framework, 'FrameworkName_plain') else framework.FrameworkName
                # If still encrypted (no _plain property), try manual decryption
                if framework_name and framework_name.startswith('gAAAAAB'):  # Encrypted data starts with this
                    framework_name = decrypt_data(framework_name)
            except Exception as e:
                print(f"Warning: Failed to decrypt FrameworkName, using as-is: {str(e)}")
                framework_name = framework.FrameworkName
            
            update_info = run_framework_update_check(
                framework_name=framework_name,
                last_updated_date=last_date_str,
                api_key=api_key,
                framework_id=framework.FrameworkId,
                process_amendment=process_amendment,
                store_in_media=True,
            )

            # If we successfully got a document (especially with S3 URL), persist it to Amendment immediately
            try:
                downloaded_path = update_info.get("downloaded_path")
                s3_url = update_info.get("s3_url")
                s3_key = update_info.get("s3_key")
                s3_stored_name = update_info.get("s3_stored_name")
                latest_update_date = update_info.get("latest_update_date") or today.isoformat()

                # Only act if we have either a downloaded file or an S3 URL
                if downloaded_path or s3_url:
                    # Build relative path and document name when local path exists
                    relative_path = None
                    document_name = None
                    if downloaded_path:
                        document_name = os.path.basename(downloaded_path)
                        try:
                            relative_path = os.path.relpath(downloaded_path, settings.MEDIA_ROOT)
                        except Exception:
                            relative_path = None
                    elif s3_stored_name:
                        document_name = s3_stored_name

                    new_amendment = {
                        "amendment_id": 1,
                        "amendment_name": f"{framework.FrameworkName} Amendment - {latest_update_date}",
                        "amendment_date": latest_update_date,
                        "document_path": downloaded_path,
                        "document_relative_path": relative_path,
                        "document_name": document_name,
                        "document_url": update_info.get("document_url"),
                        "s3_url": s3_url,
                        "s3_key": s3_key,
                        "s3_stored_name": s3_stored_name,
                        "downloaded_date": datetime.now().isoformat(),
                        "processed": False,
                        "processed_date": None,
                        "extraction_summary": {},
                        "sections": [],
                        "framework_info": {},
                        "ai_analysis": {},
                    }

                    # Merge with existing amendments (update if same date/name)
                    amendments = framework.Amendment or []
                    if not isinstance(amendments, list):
                        amendments = []

                    matched = False
                    for idx, existing in enumerate(amendments):
                        if (
                            existing.get("amendment_date") == latest_update_date
                            or existing.get("amendment_name") == new_amendment["amendment_name"]
                        ):
                            amendments[idx].update(new_amendment)
                            matched = True
                            break

                    if not matched:
                        amendments.append(new_amendment)

                    framework.Amendment = amendments
                    framework.latestComparisionCheckDate = today
                    framework.save(update_fields=["Amendment", "latestComparisionCheckDate"])
                else:
                    # Even if nothing was saved, still bump comparison date
                    framework.latestComparisionCheckDate = today
                    framework.save(update_fields=["latestComparisionCheckDate"])
            except Exception as save_exc:
                logger.error(
                    "Failed to save amendment/S3 info for framework %s: %s",
                    framework.FrameworkId,
                    str(save_exc),
                )

            # Update the last check date to today (ensuring it's a date object, not datetime)
            framework.latestComparisionCheckDate = today
            framework.save(update_fields=["latestComparisionCheckDate"])
            
            logger.info(
                "Framework check completed | id=%s name=%s last_check_date_set=%s next_check_will_be=%s",
                framework.FrameworkId,
                framework.FrameworkName,
                today.isoformat(),
                (today + timedelta(days=7)).isoformat(),
            )

            processed += 1
            results.append(
                {
                    "framework_id": framework.FrameworkId,
                    "framework_name": framework.FrameworkName,
                    "status": "checked",
                    "has_update": update_info.get("has_update", False),
                    "latest_update_date": update_info.get("latest_update_date"),
                    "document_url": update_info.get("document_url"),
                    "downloaded_path": update_info.get("downloaded_path"),
                    "message": "Update check completed.",
                }
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            errors += 1
            logger.error(
                "Auto framework check failed | id=%s name=%s error=%s",
                framework.FrameworkId,
                framework.FrameworkName,
                str(exc),
            )
            results.append(
                {
                    "framework_id": framework.FrameworkId,
                    "framework_name": framework.FrameworkName,
                    "status": "error",
                    "message": str(exc),
                }
            )

    return Response(
        {
            "success": True,
            "summary": {
                "total": frameworks.count(),
                "processed": processed,
                "skipped": skipped,
                "errors": errors,
                "force_run": force_run,
            },
            "results": results,
        }
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_framework_update_notifications(request):
    """
    Lightweight update summary used by the UI notification bell.

    Reads the Amendment JSON column for every framework and reports:
    - framework_id / framework_name
    - amendment_count
    - has_amendment (bool) - true if amendment exists AND has document
    - has_document (bool) - true if document link (s3_url or document_path) is available
    - document_available (bool) - alias for has_document
    - latest_amendment (if present)
    """
    try:
        # Query the frameworks table directly using Framework model
        frameworks = Framework.objects.all()
        notification_items = []

        for framework in frameworks:
            amendments = framework.Amendment or []
            if not isinstance(amendments, list):
                amendments = []

            amendment_count = len(amendments)
            latest_amendment = amendments[-1] if amendments else None
            
            # Check if document is available (S3 URL or valid document path)
            has_document = False
            document_status = "No amendment yet"
            
            if latest_amendment:
                # Check for S3 URL (preferred) - this is the most reliable indicator
                s3_url = latest_amendment.get('s3_url')
                if s3_url:
                    has_document = True
                    document_status = "Amendment available"
                else:
                    # Check for document path
                    document_path = latest_amendment.get('document_path')
                    if document_path:
                        # Verify file exists if it's a local path
                        if os.path.exists(document_path):
                            has_document = True
                            document_status = "Amendment available"
                        else:
                            # Check if it's a relative path
                            relative_path = latest_amendment.get('document_relative_path')
                            if relative_path:
                                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                                if os.path.exists(full_path):
                                    has_document = True
                                    document_status = "Amendment available"
            
            # Also check metadata files for documents that were downloaded but not yet processed
            # This handles the case where document is downloaded but "Start Analysis" hasn't been clicked yet
            if not has_document:
                try:
                    change_management_dir = os.path.join(settings.MEDIA_ROOT, 'change_management')
                    if os.path.exists(change_management_dir):
                        framework_name_safe = framework.FrameworkName.replace(' ', '_').lower()
                        for filename in os.listdir(change_management_dir):
                            if filename.lower().endswith('_metadata.json'):
                                metadata_file = os.path.join(change_management_dir, filename)
                                try:
                                    with open(metadata_file, 'r', encoding='utf-8') as f:
                                        metadata = json.load(f)
                                    # Check if this metadata is for this framework
                                    if (metadata.get('framework_id') == framework.FrameworkId or
                                        str(metadata.get('framework_name', '')).lower() == framework.FrameworkName.lower() or
                                        framework_name_safe in filename.lower()):
                                        # Check if document has S3 URL or valid path
                                        if metadata.get('s3_url'):
                                            has_document = True
                                            document_status = "Amendment available"
                                            break
                                        elif metadata.get('document_path') and os.path.exists(metadata.get('document_path')):
                                            has_document = True
                                            document_status = "Amendment available"
                                            break
                                except Exception:
                                    continue
                except Exception as e:
                    logger.debug(f"Error checking metadata files for framework {framework.FrameworkId}: {str(e)}")
            
            # has_amendment is true only if amendment exists AND has document
            has_amendment = amendment_count > 0 and has_document
            
            # Format last comparison date from frameworks table
            last_comparison_date = framework.latestComparisionCheckDate
            if last_comparison_date:
                if isinstance(last_comparison_date, str):
                    last_comparison_date_str = last_comparison_date
                else:
                    last_comparison_date_str = last_comparison_date.strftime("%Y-%m-%d")
            else:
                last_comparison_date_str = None

            notification_items.append(
                {
                    "framework_id": framework.FrameworkId,
                    "framework_name": framework.FrameworkName,
                    "amendment_count": amendment_count,
                    "has_amendment": has_amendment,
                    "has_document": has_document,
                    "document_available": has_document,  # Alias for frontend
                    "document_status": document_status,
                    "latest_amendment": latest_amendment,
                    "last_comparison_date": last_comparison_date_str,
                }
            )

        # Count only frameworks with documents available
        updated_count = sum(1 for item in notification_items if item["has_document"])

        return Response(
            {
                "success": True,
                "frameworks": notification_items,
                "updated_count": updated_count,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to fetch framework update notifications: %s", exc)
        return Response(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )
