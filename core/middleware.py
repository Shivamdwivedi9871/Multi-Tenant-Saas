import time
import logging
import uuid
from .models import Tenant, TenantUser
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Skip tenant validation for Django Admin, auth endpoints, or static routes
        example_path = ['/admin/', '/v1/auth/', '/v1/crate_user/',
                        '/v1/create_token/', '/v1/refresh_token/', '/v1/tenant/onboard/']

        if any(request.path.startswith(path) for path in example_path):
            request.tenant = None
            return self.get_response(request)

        tenant_id = request.headers.get('X-Tenant-ID')

        if tenant_id:
            try:
                tenant_id = str(tenant_id)
                uuid_obj = uuid.UUID(tenant_id)
                tenant = Tenant.objects.get(id=uuid_obj, is_active=True)
                request.tenant = tenant
            except (Tenant.DoesNotExist, ValueError):
                return JsonResponse({
                    'detail': 'Invalid or Inactive Tenant Id Provides'
                }, status=400)
        else:
            request.tenant = None

        return self.get_response(request)


class CustomTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        request.tenant_user = None

        user = getattr(request, 'user', None)

        # Skip processing for unauthenticated user and publick endpoints
        if not getattr(user, 'is_authenticated', False):
            return self.get_response(request)

        # Read the tenat header
        tenant_slug = request.META.get(
            'HTTP_X_TENANT_SLUG') or request.headers.get('X-Tenant-Slug')

        if not tenant_slug:
            return self.get_response(request)

        # Verify tenant exist and is_active

        active_tenant = Tenant.objects.filter(
            slug=tenant_slug, is_active=True).first()

        if not active_tenant:
            return self.get_response(request)

        # Validated user Memabership in the tenant

        membership = TenantUser.objects.filter(
            tenant=active_tenant, user=user).first()

        if not membership:
            return self.get_response(request)

        request.tenant = active_tenant
        request.tenant_user = membership

        return self.get_response(request)
