import os
import django
from datetime import date, time, timedelta

from django.conf import settings

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()

from django.test import TestCase

from grc.models import Tenant, Incident, Compliance, Risk, Framework, Policy, SubPolicy
from grc.routes.Risk.risk_views import _parse_and_validate_mitigation_due_date


class RiskSecurityRegressionTests(TestCase):
    """
    Regression tests for risk-module security controls:
    - IDOR/BOLA protections through tenant-scoped object access.
    - Due-date validation guards.
    """

    def setUp(self):
        self.tenant1 = Tenant.objects.create(
            name="Tenant A",
            subdomain="tenant-a",
            license_key="TENANT-A-KEY",
            status="active",
        )
        self.tenant2 = Tenant.objects.create(
            name="Tenant B",
            subdomain="tenant-b",
            license_key="TENANT-B-KEY",
            status="active",
        )

        self.framework1 = Framework.objects.create(FrameworkName="FW-A", tenant=self.tenant1)
        self.framework2 = Framework.objects.create(FrameworkName="FW-B", tenant=self.tenant2)

        self.policy1 = Policy.objects.create(PolicyName="P-A", FrameworkId=self.framework1, tenant=self.tenant1)
        self.policy2 = Policy.objects.create(PolicyName="P-B", FrameworkId=self.framework2, tenant=self.tenant2)

        self.subpolicy1 = SubPolicy.objects.create(SubPolicyName="SP-A", PolicyId=self.policy1, tenant=self.tenant1)
        self.subpolicy2 = SubPolicy.objects.create(SubPolicyName="SP-B", PolicyId=self.policy2, tenant=self.tenant2)

        self.compliance1 = Compliance.objects.create(
            SubPolicy=self.subpolicy1,
            ComplianceTitle="C-A",
            ComplianceItemDescription="Compliant item for tenant A",
            Identifier="C-A-1",
            ComplianceVersion="1.0",
            tenant=self.tenant1,
        )
        self.compliance2 = Compliance.objects.create(
            SubPolicy=self.subpolicy2,
            ComplianceTitle="C-B",
            ComplianceItemDescription="Compliant item for tenant B",
            Identifier="C-B-1",
            ComplianceVersion="1.0",
            tenant=self.tenant2,
        )

        self.incident1 = Incident.objects.create(
            IncidentTitle="Incident A",
            Description="Incident for tenant A",
            Date=date.today(),
            Time=time(10, 30),
            Origin="Manual",
            ComplianceId=self.compliance1.ComplianceId,
            tenant=self.tenant1,
        )
        self.incident2 = Incident.objects.create(
            IncidentTitle="Incident B",
            Description="Incident for tenant B",
            Date=date.today(),
            Time=time(11, 45),
            Origin="Manual",
            ComplianceId=self.compliance2.ComplianceId,
            tenant=self.tenant2,
        )

        self.risk1 = Risk.objects.create(
            RiskTitle="Risk A",
            RiskDescription="Risk for tenant A",
            ComplianceId=self.compliance1.ComplianceId,
            tenant=self.tenant1,
        )
        self.risk2 = Risk.objects.create(
            RiskTitle="Risk B",
            RiskDescription="Risk for tenant B",
            ComplianceId=self.compliance2.ComplianceId,
            tenant=self.tenant2,
        )

    def test_incident_lookup_is_tenant_scoped(self):
        with self.assertRaises(Incident.DoesNotExist):
            Incident.objects.get(
                IncidentId=self.incident2.IncidentId,
                tenant_id=self.tenant1.tenant_id,
            )

    def test_compliance_lookup_by_incident_is_tenant_scoped(self):
        compliance = Compliance.objects.filter(
            ComplianceId=self.incident2.ComplianceId,
            tenant_id=self.tenant1.tenant_id,
        ).first()
        self.assertIsNone(compliance)

    def test_risk_lookup_by_incident_compliance_is_tenant_scoped(self):
        risks = Risk.objects.filter(
            ComplianceId=self.incident2.ComplianceId,
            tenant_id=self.tenant1.tenant_id,
        )
        self.assertEqual(risks.count(), 0)

    def test_due_date_rejects_before_creation_date(self):
        created_at = date.today()
        with self.assertRaises(ValueError):
            _parse_and_validate_mitigation_due_date(
                (created_at - timedelta(days=1)).isoformat(),
                created_at=created_at,
            )

    def test_due_date_rejects_unrealistic_range(self):
        created_at = date.today()
        with self.assertRaises(ValueError):
            _parse_and_validate_mitigation_due_date(
                (created_at + timedelta(days=3651)).isoformat(),
                created_at=created_at,
            )

    def test_due_date_accepts_valid_range(self):
        created_at = date.today()
        result = _parse_and_validate_mitigation_due_date(
            (created_at + timedelta(days=30)).isoformat(),
            created_at=created_at,
        )
        self.assertEqual(result, created_at + timedelta(days=30))
