from django.contrib import admin
from .models import User, Tenant, TenantUser, TenantAwareModel

# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'plan',
        'is_active',
        'created_at',
    )


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tenant',
        'user',
        'role',
        'created_at',
    )


# @admin.register(TenantAwareModel)
# class TenantAwareModelAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'tenant',
#         'created_at'
#     )
