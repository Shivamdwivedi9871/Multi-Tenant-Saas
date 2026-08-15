import time
import logging
from .models import Tenant
from django.http import JsonResponse


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        tenant_id = request.headers.get('X-Tenant_ID')

        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                request.tenant = tenant
            except (Tenant.DoesNotExist, ValueError):
                return JsonResponse({
                    'detail': 'Inavlid or Inactive Tenant Id Provides'
                }, status=400)
        else:
            request.tenant = None

        return self.get_response(request)
