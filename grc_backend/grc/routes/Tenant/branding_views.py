"""
Branding API Views - Phase 2.8

Endpoints for per-tenant white-labelling (logo, colours, CSS).
"""

import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from ...models import Tenant, TenantBranding, Users, TenantAuditLog
from ...tenant_utils import require_tenant, get_tenant_id_from_request

logger = logging.getLogger(__name__)


def _log_audit(tenant_id, entity_id, old_value, new_value, request):
    try:
        user = getattr(request, 'user', None)
        performed_by = None
        if user and user.is_authenticated:
            uid = getattr(user, 'UserId', getattr(user, 'id', None))
            if uid:
                performed_by = Users.objects.filter(UserId=uid).first()
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        )
        TenantAuditLog.objects.create(
            tenant_id=tenant_id,
            action_type='UPDATE',
            entity_type='branding',
            entity_id=entity_id,
            entity_name='Branding',
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[branding_views] Audit log failed: {exc}")


def _branding_to_dict(b):
    return {
        'id': b.id,
        'tenant_id': b.tenant_id,
        'logo_url': b.logo_url,
        'favicon_url': b.favicon_url,
        'primary_color': b.primary_color,
        'secondary_color': b.secondary_color,
        'accent_color': b.accent_color,
        'custom_css': b.custom_css,
        'login_page_custom_html': b.login_page_custom_html,
        'email_template_logo': b.email_template_logo,
        'email_footer_text': b.email_footer_text,
        'updated_at': b.updated_at.isoformat() if b.updated_at else None,
    }


def _get_or_create_branding(tenant_id):
    branding, _ = TenantBranding.objects.get_or_create(
        tenant_id=tenant_id,
        defaults={
            'primary_color': '#1976D2',
            'secondary_color': '#424242',
            'accent_color': '#82B1FF',
        },
    )
    return branding


@api_view(['GET', 'PUT'])
@require_tenant
def tenant_branding(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/branding/
    PUT /api/tenants/{tenant_id}/branding/
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
    if not tenant:
        return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

    if request.method == 'GET':
        try:
            b = _get_or_create_branding(tenant_id)
            return JsonResponse({'status': 'success', 'branding': _branding_to_dict(b)})
        except Exception as exc:
            logger.error(f"[branding_views] GET error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # PUT – update
    try:
        data = request.data if hasattr(request, 'data') else {}
        b = _get_or_create_branding(tenant_id)
        old = _branding_to_dict(b)

        updatable = [
            'logo_url', 'favicon_url',
            'primary_color', 'secondary_color', 'accent_color',
            'custom_css', 'login_page_custom_html',
            'email_template_logo', 'email_footer_text',
        ]
        for field in updatable:
            if field in data:
                setattr(b, field, data[field])

        performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
        b.updated_by_id = performer_id
        b.save()

        _log_audit(tenant_id, b.id, old, _branding_to_dict(b), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Branding updated',
            'branding': _branding_to_dict(b),
        })
    except Exception as exc:
        logger.error(f"[branding_views] PUT error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['POST'])
@require_tenant
def upload_logo(request, tenant_id):
    """
    POST /api/tenants/{tenant_id}/branding/upload-logo/
    Accepts multipart: field 'logo' (file) or 'logo_url' (direct URL string).
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        logo_url = request.data.get('logo_url') if hasattr(request, 'data') else None

        if not logo_url and request.FILES.get('logo'):
            # Persist file via S3/storage — delegate to existing s3_functions if available
            try:
                from ..Global.s3_fucntions import upload_file_to_s3
                file_obj = request.FILES['logo']
                s3_key = f"tenant_{tenant_id}/branding/{file_obj.name}"
                logo_url = upload_file_to_s3(file_obj, s3_key)
            except ImportError:
                return JsonResponse(
                    {'status': 'error', 'message': 'File upload not configured'}, status=501
                )

        if not logo_url:
            return JsonResponse(
                {'status': 'error', 'message': 'Provide logo_url or upload a logo file'}, status=400
            )

        b = _get_or_create_branding(tenant_id)
        old = _branding_to_dict(b)
        b.logo_url = logo_url
        performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
        b.updated_by_id = performer_id
        b.save()

        _log_audit(tenant_id, b.id, old, _branding_to_dict(b), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Logo updated',
            'logo_url': logo_url,
        })
    except Exception as exc:
        logger.error(f"[branding_views] upload_logo error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_branding(request, tenant_id):
    """
    GET /api/public/branding/{tenant_id}/
    Returns minimal branding for the login page (no auth required).
    """
    try:
        branding = TenantBranding.objects.filter(tenant_id=tenant_id).first()
        if not branding:
            return JsonResponse({
                'status': 'success',
                'branding': {
                    'primary_color': '#1976D2',
                    'secondary_color': '#424242',
                    'accent_color': '#82B1FF',
                    'logo_url': None,
                    'favicon_url': None,
                },
            })
        return JsonResponse({
            'status': 'success',
            'branding': {
                'primary_color': branding.primary_color,
                'secondary_color': branding.secondary_color,
                'accent_color': branding.accent_color,
                'logo_url': branding.logo_url,
                'favicon_url': branding.favicon_url,
            },
        })
    except Exception as exc:
        logger.error(f"[branding_views] public_branding error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
