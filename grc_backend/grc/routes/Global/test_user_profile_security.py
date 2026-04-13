from unittest import TestCase
from unittest.mock import patch

from rest_framework.test import APIRequestFactory, force_authenticate

from grc.routes.Global.user_profile import (
    create_access_request,
    create_data_subject_request,
    get_access_requests,
    get_data_subject_requests,
    update_access_request_status,
    update_data_subject_request_status,
)


class _DummyUser:
    is_authenticated = True
    pk = 1


class _CursorStub:
    def __init__(self, rows, columns):
        self._rows = list(rows)
        self.description = [(col,) for col in columns]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        return None

    def fetchone(self):
        return self._rows.pop(0) if self._rows else None

    def fetchmany(self, _size):
        return []

    def close(self):
        return None


class UserProfileSecurityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = _DummyUser()

    @patch("grc.routes.Global.user_profile.RBACUtils.is_system_admin", return_value=False)
    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=10)
    def test_data_subject_requests_blocks_idor_for_non_admin(self, *_mocks):
        request = self.factory.get("/api/data-subject-requests/99/")
        force_authenticate(request, user=self.user)

        response = get_data_subject_requests(request, 99)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("message"), "Forbidden")

    @patch("grc.routes.Global.user_profile.RBACUtils.is_system_admin", return_value=False)
    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=10)
    def test_access_requests_blocks_idor_for_non_admin(self, *_mocks):
        request = self.factory.get("/api/access-requests/99/")
        force_authenticate(request, user=self.user)

        response = get_access_requests(request, 99)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("message"), "Forbidden")

    @patch("grc.routes.Global.user_profile.connection.cursor")
    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=None)
    def test_update_access_request_status_ignores_spoofed_request_data_user_id(self, _user_mock, cursor_mock):
        cursor_mock.return_value = _CursorStub(
            rows=[(1, 2, "REQUESTED", "End User", "policy.view_all_policy", "{}")],
            columns=["id", "user_id", "status", "requested_role", "required_permission", "audit_trail"],
        )
        request = self.factory.put("/api/access-requests/1/update-status/", {"user_id": 1, "status": "APPROVED"}, format="json")
        force_authenticate(request, user=self.user)

        response = update_access_request_status(request, 1)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("message"), "User not authenticated")

    @patch("grc.routes.Global.user_profile.connection.cursor")
    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=None)
    def test_update_data_subject_status_ignores_spoofed_request_data_user_id(self, _user_mock, cursor_mock):
        cursor_mock.return_value = _CursorStub(
            rows=[(1, 2, "REQUESTED")],
            columns=["id", "user_id", "status"],
        )
        request = self.factory.put("/api/data-subject-requests/1/update-status/", {"user_id": 1, "status": "APPROVED"}, format="json")
        force_authenticate(request, user=self.user)

        response = update_data_subject_request_status(request, 1)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("message"), "User not authenticated")

    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", side_effect=[None, 10])
    def test_create_data_subject_request_enforces_authenticated_object_ownership(self, *_mocks):
        request = self.factory.post(
            "/api/data-subject-requests/create/",
            {"user_id": 99, "request_type": "ACCESS", "info_type": "personal"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = create_data_subject_request(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("message"), "Forbidden")

    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=10)
    def test_create_access_request_rejects_external_url(self, *_mocks):
        request = self.factory.post(
            "/api/access-requests/create/",
            {
                "requested_url": "https://attacker.tld/evil",
                "requested_feature": "feature",
                "required_permission": "policy.view_all_policy",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = create_access_request(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("requested_url", response.data.get("message", ""))

    @patch("grc.routes.Global.user_profile.connection.cursor")
    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=1)
    @patch("grc.routes.Global.user_profile.RBACUtils.is_system_admin", return_value=True)
    def test_update_access_request_rejects_invalid_status_transition(self, _admin_mock, _user_mock, cursor_mock):
        cursor_mock.return_value = _CursorStub(
            rows=[(1, 2, "REQUESTED", "End User", "policy.view_all_policy", "{}")],
            columns=["id", "user_id", "status", "requested_role", "required_permission", "audit_trail"],
        )
        request = self.factory.put("/api/access-requests/1/update-status/", {"status": "REQUESTED"}, format="json")
        force_authenticate(request, user=self.user)

        response = update_access_request_status(request, 1)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status", response.data.get("message", ""))

    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=10)
    def test_create_data_subject_request_rejects_invalid_risk_id_type(self, *_mocks):
        request = self.factory.post(
            "/api/data-subject-requests/create/",
            {"request_type": "RECTIFICATION", "info_type": "risk", "risk_id": "abc"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = create_data_subject_request(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("risk_id", response.data.get("message", ""))

    @patch("grc.routes.Global.user_profile.RBACUtils.get_user_id_from_request", return_value=10)
    def test_create_data_subject_request_rejects_invalid_access_audit_url(self, *_mocks):
        request = self.factory.post(
            "/api/data-subject-requests/create/",
            {
                "request_type": "ACCESS",
                "info_type": "personal",
                "audit_trail": {"requested_url": "https://attacker.tld/evil"},
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = create_data_subject_request(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("requested_url", response.data.get("message", ""))
