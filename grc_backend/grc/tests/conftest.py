import datetime as dt

import pytest
from django.test import RequestFactory
from django.utils import timezone

from grc.models import Incident, Tenant, Users


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def tenant_a(db):
    return Tenant.objects.create(
        name="Tenant A",
        subdomain="tenant-a",
        license_key="tenant-a-license",
        status="active",
    )


@pytest.fixture
def tenant_b(db):
    return Tenant.objects.create(
        name="Tenant B",
        subdomain="tenant-b",
        license_key="tenant-b-license",
        status="active",
    )


def _create_user(*, tenant, username, email):
    return Users.objects.create(
        tenant=tenant,
        UserName=username,
        Password="test-password",
        Email=email,
        FirstName="Test",
        LastName="User",
        IsActive="Y",
        DepartmentId="SEC",
    )


@pytest.fixture
def user_a(db, tenant_a):
    return _create_user(tenant=tenant_a, username="user_a", email="user_a@example.com")


@pytest.fixture
def user_b(db, tenant_b):
    return _create_user(tenant=tenant_b, username="user_b", email="user_b@example.com")


@pytest.fixture
def incident_for_user_a(db, tenant_a, user_a):
    now = timezone.now()
    return Incident.objects.create(
        tenant=tenant_a,
        IncidentTitle="Tenant A Incident",
        Description="Test incident A",
        Date=now.date(),
        Time=now.time().replace(microsecond=0),
        UserId=user_a,
        Origin="Incident",
        Status="Assigned",
        CreatedAt=now,
        AssignedDate=now,
        MitigationDueDate=now + dt.timedelta(days=14),
    )


@pytest.fixture
def incident_for_user_b(db, tenant_b, user_b):
    now = timezone.now()
    return Incident.objects.create(
        tenant=tenant_b,
        IncidentTitle="Tenant B Incident",
        Description="Test incident B",
        Date=now.date(),
        Time=now.time().replace(microsecond=0),
        UserId=user_b,
        Origin="Incident",
        Status="Assigned",
        CreatedAt=now,
        AssignedDate=now,
        MitigationDueDate=now + dt.timedelta(days=14),
    )
