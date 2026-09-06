from rest_framework import permissions
from .models import TenantUser


class IsMember(permissions.BasePermission):

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        tenant = getattr(request, 'tenant', None)

        if not tenant:
            return False

        return TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user
        ).exists()


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        tenant = getattr(request, 'tenant', None)

        if not tenant:
            return False

        if request.method in permissions.SAFE_METHODS:
            return TenantUser.objects.filter(
                tenant=tenant,
                user=request.user
            ).exists()

        return TenantUser.objects.filter(
            tenant=request.tenant,
            user=request.user,
            role='ADMIN'
        ).exists()


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        tenant = getattr(request, 'tenant', None)

        if not tenant:
            return False

        return TenantUser.objects.filter(
            tenant=tenant,
            user=request.user,
            role__in=['ADMIN', 'MANAGER']
        ).exists()
