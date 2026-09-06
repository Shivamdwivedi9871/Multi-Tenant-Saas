from rest_framework import viewsets, exceptions


class BaseTenantViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)

        if not tenant:
            raise exceptions.PermissionDenied(
                "Tenant Context is missing from Header")

        return super().get_queryset().filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)

        if not tenant:
            raise exceptions.PermissionDenied(
                'Cannot create resource without valid Tenant Context')

        serializer.save(tenant=tenant, created_by=self.request.user)
