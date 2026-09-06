import pytest
from unittest.mock import Mock
from rest_framework.test import APIClient
from core.models import TenantUser, Tenant, User
from core.permissions import IsAdminOrReadOnly


# @pytest.fixture
# def tenants(db):
#     tenant_a = Tenant.objects.create(name="Tenant A", slug='tenant-a')
#     tenant_b = Tenant.objects.create(name='Tenant B', slug='tenant-b')

#     return tenant_a, tenant_b


# @pytest.fixture
# def user_role(db, tenant):
#     tenant_a, tenant_b = tenant

#     admin = User.objects.create_user(
#         username='admin@mail.com', password='Password123!')
#     member = User.objects.create_user(
#         username='member@a.com', password='Password123!')
#     outsider = User.objects.create_user(
#         username='member@b.com', password='Password123!')

#     ''''Role in Tenant A'''
#     TenantUser.objects.create(tenant=tenant_a, user=admin, role='ADMIN')
#     TenantUser.objects.create(tenant=tenant_a, user=member, role='MEMBER')

#     '''Role in Tenant B'''
#     TenantUser.objects.create(tenant=tenant_b, user=outsider, role='MEMBER')

#     return {
#         'admin': admin,
#         'member': member,
#         'outsider': outsider,
#         'tenant_a': tenant_a,
#         'tenant_b': tenant_b
#     }
# '''Test for IsAdminOrReadOnly'''

# class TestIsAdminOrReadOnly:

#     def test_member_can_read_tenant_data(self, api_client, user_role):
#         api_client.force_authenticate(user=member)
#         payload = {na}
#         response = api_client.get('/v1/tenant/onboard/', )

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username='test@email.com', password='Password123!')
    return user


@pytest.fixture
def tenant(db, user):
    tenant_a = Tenant.objects.create(
        name='AMC Corp', slug='amc-corp', plan='FREE')
    tenant_user = TenantUser.objects.create(
        tenant=tenant_a,
        user=user,
        role='MEMBER'
    )

    return {
        'user': user,
        'tenant': tenant_a,
        'tenant_user': tenant_user
    }


@pytest.mark.django_db
def test_successful_read_only_permission(api_client, user, tenant):
    api_client.force_authenticate(user=user)

    response = api_client.get('/v1/tenant/onboard/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_non_admin_user_write_protection(user, tenant):
    permission = IsAdminOrReadOnly()

    request = Mock()
    request.method = 'POST'
    request.user = user
    request.tenant = tenant['tenant']

    assert permission.has_permission(request, None) is False
