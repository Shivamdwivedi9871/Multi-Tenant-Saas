import pytest
from rest_framework.test import APIClient
from core.models import User, Tenant, TenantUser

'''-----------Fixture-------------'''


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='admin@example.com', password='Password123!')


'''----------Test-----------'''


@pytest.mark.django_db
def test_successfull_tenat_onboarding(api_client, user):
    api_client.force_authenticate(user=user)

    payload = {"name": "Amc Corp", "slug": "amc-corp", 'role': 'ADMIN'}

    response = api_client.post('/v1/tenant/onboard/', data=payload)

    assert response.status_code == 201
    assert Tenant.objects.filter(slug='amc-corp').exists()
    assert TenantUser.objects.filter(user=user, role='ADMIN').exists()


@pytest.mark.django_db
def test_duplicate_slug_name(api_client, user):
    Tenant.objects.create(name="Existing", slug="amc-corp")

    api_client.force_authenticate(user=user)
    payload = {"name": "New Ace", "slug": 'amc-corp'}
    response = api_client.post('/v1/tenant/onboard/', data=payload)

    assert response.status_code == 400
