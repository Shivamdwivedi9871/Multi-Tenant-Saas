import uuid
import pytest
from django.test import RequestFactory
from django.http import HttpResponse
from core.models import Tenant
from core.middleware import TenantMiddleware


@pytest.fixture
def dummyresponse():
    """Dummy view handler for middleware initialization."""
    return lambda req: HttpResponse('OK')


@pytest.fixture
def middleware(dummyresponse):
    """Initializes TenantMiddleware instance."""
    return TenantMiddleware(dummyresponse)


@pytest.fixture
def active_tenant(db):
    """Database fixture for an active tenant."""
    return Tenant.objects.create(
        name="Alpha Corp",
        slug="alpha-corp",
        plan="FREE",
        is_active=True
    )


@pytest.mark.django_db
class TenantMiddleware:

    def test_valid_tenant_header_attached_tenant(self, middleware, active_tenant):
        factory = RequestFactory()
        request = factory.get('/api/v1/projects/',
                              HTTP_X_TENANT_ID=active_tenant.id)
        middleware(request)

        assert request.tenant is not None
        assert request.tenant.id == active_tenant.id

    def test_missing_tenant_header(self, middleware):
        factory = RequestFactory()
        request = factory.get('/api/v1/projects/')
        middleware(request)

        assert request.tenant is None

    def test_invalid_tenant_id_return_400(self, middleware):
        factory = RequestFactory()
        random_uuid = str(uuid.uuid4())
        request = factory.get('/api/v1/projects/',
                              HTTP_X_TENANT_ID=random_uuid)

        response = middleware(request)

        assert response.status_code == 400

    def test_exampt_path_skip_tenant(self, middleware):
        factory = RequestFactory()
        request = factory.get('/admin/login')

        response = middleware(request)

        assert response.status_code == 200
        assert request.tenant is None
