import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email}"


class Tenant(models.Model):

    class Plan:
        CHOICES = [
            ('FREE', 'free'),
            ('PRO', 'pro'),
            ('ENTERPRISE', 'enterprise')
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    plan = models.CharField(
        max_length=150, choices=Plan.CHOICES, default='FREE')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'


class TenantUser(models.Model):
    class Role:
        CHOICES = [
            ('ADMIN', 'admin'),
            ('MANAGER', 'manager'),
            ('MEMBER', 'member')
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='membership')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tenant_membership')
    role = models.CharField(
        max_length=200, choices=Role.CHOICES, default='MEMBER')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'user')


class TenantAwareModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
