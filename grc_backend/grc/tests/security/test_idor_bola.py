"""Security regression tests for IDOR/BOLA controls in Incident/Risk/Audit flows."""

from django.http import JsonResponse

import pytest

from grc.middleware import ObjectLevelAuthorizationMiddleware
from grc.routes.Incident.incident_views import get_incident_for_request
from grc.tenant_utils import require_tenant


@pytest.mark.django_db
def test_incident_fetch_blocks_cross_tenant_access(rf, user_a, incident_for_user_b):
    """
    Incident helper must not return an incident from another tenant.
    This is the core anti-IDOR guard used by incident read/update handlers.
    """
    req = rf.get("/api/incidents/")
    req.user = user_a

    with pytest.raises(type(incident_for_user_b).DoesNotExist):
        get_incident_for_request(req, incident_for_user_b.IncidentId)


@pytest.mark.django_db
def test_incident_fetch_allows_same_tenant_access(rf, user_a, incident_for_user_a):
    """Sanity check: same-tenant incident remains accessible to valid requester."""
    req = rf.get("/api/incidents/")
    req.user = user_a

    incident = get_incident_for_request(req, incident_for_user_a.IncidentId)
    assert incident.IncidentId == incident_for_user_a.IncidentId


@pytest.mark.django_db
def test_object_level_middleware_blocks_cross_user_enumeration(rf, monkeypatch, user_a, user_b):
    """
    Middleware-level BOLA protection: user_id in URL/query is denied for non-admins.
    This underpins user-specific reviewer endpoints for incident/risk/audit tasks.
    """
    middleware = ObjectLevelAuthorizationMiddleware(lambda req: JsonResponse({"ok": True}))
    req = rf.get(f"/api/incident-reviewer-tasks/{user_b.UserId}/")
    req.user = user_a

    monkeypatch.setattr("grc.middleware.RBACUtils.get_user_id_from_request", lambda request: user_a.UserId)
    monkeypatch.setattr("grc.middleware.RBACUtils.is_system_admin", lambda _uid: False)

    response = middleware.process_view(
        req,
        view_func=lambda request, user_id: JsonResponse({"ok": True}),
        view_args=(),
        view_kwargs={"user_id": str(user_b.UserId)},
    )
    assert response is not None
    assert response.status_code == 403


@pytest.mark.django_db
def test_require_tenant_rejects_cross_tenant_input(rf, user_a, tenant_b):
    """
    Generic tenant guard must reject client-provided tenant mismatch.
    This is reused in incident, audit and risk routes decorated with require_tenant.
    """
    req = rf.post("/api/secure", data={"tenant_id": tenant_b.tenant_id}, content_type="application/json")
    req.user = user_a

    @require_tenant
    def protected_view(request):
        return JsonResponse({"ok": True})

    response = protected_view(req)
    assert response.status_code == 403
