import pytest
from rest_framework.test import APIClient
from core.models import User, Tenant, Project, TenantUser
from core.middleware import TenantMiddleware
from core.permissions import IsAdminOrReadOnly, IsMember


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username='test@example.com', email='test@example.com', password='Password123!')
    return user


@pytest.fixture
def tenant(db, user):
    tenant = Tenant.objects.create(
        name='AMC Corp',
        slug='amc-corp',
        plan='FREE',
        is_active=True
    )

    return tenant


@pytest.fixture
def tenant_user(db, user, tenant):
    tenantuser = TenantUser.objects.create(
        tenant=tenant,
        user=user,
        role='ADMIN'
    )
    return tenantuser


@pytest.mark.django_db
def test_successfull_project_creation(api_client, user, tenant, tenant_user):

    api_client.force_authenticate(user=user)

    payload = {
        "title": "AMC Project",
        "description": "AMC Test Description"
    }

    response = api_client.post(
        '/v1/projects/', data=payload, format='json', HTTP_X_TENANT_SLUG=tenant.slug)

    assert response.status_code == 201
