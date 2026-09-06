import time
import logging
import uuid
from .models import Tenant
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
