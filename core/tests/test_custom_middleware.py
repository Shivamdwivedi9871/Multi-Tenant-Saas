import pytest
from rest_framework.test import APIClient
from core.models import User, Tenant, TenantUser


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db):
    user_a = User.objects.create_user(
        username='testusera@example.com', email='testusera@example.com', password='Password123!')

    user_b = User.objects.create_user(
        username='testuserb@example.com', email='testuserb@example.com', password='Password123!')

    return user_a, user_b


@pytest.fixture
def tenant(db):
    tenant_a = Tenant.objects.create(
        name='AMC CORPS', slug='amc-corp', is_active=True, plan='ENTERPRISE')

    tenant_b = Tenant.objects.create(
        name='SBS INC', slug='sbs-inc', is_active=True, plan='ENTERPRISE')

    tenant_c = Tenant.objects.create(
        name='AMP INC', slug='amp-inc', is_active=False)

    return tenant_a, tenant_b, tenant_c


@pytest.fixture
def tenant_user(db, users, tenants):
    user_a, user_b = users
    tenant_a, tenant_b = tenants
    tenant_user_admin = TenantUser.objects.create(
        tenant=tenant_a,
        user=user_a,
        role='ADMIN',
    )

    tenant_user_member = TenantUser.objects.create(
        tenant=tenant_b,
        user=user_a,
        role='MEMBER',
    )

    tenant_user_b_member = TenantUser.objects.create(
        tenant=tenant_a,
        user=user_b,
        role='MEMBER',
    )

    return tenant_user_admin, tenant_user_member, tenant_user_b_member


@pytest.mark.django_db
def test_unauthenticated_request(api_client, user, tenant):

    # payload = {

    #     "title": "AMC Project",
    #     "description": "AMC Test Description"
    # }

    response = api_client.get('/v1/projects/')

    assert response.status_code == 401
