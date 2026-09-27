import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class RoleChoices:
    CHOICES = [
        ('ADMIN', 'admin'),
        ('MANAGER', 'manager'),
        ('MEMBER', 'member')
    ]


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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='membership')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tenant_membership')
    role = models.CharField(
        max_length=200, choices=RoleChoices.CHOICES, default='MEMBER')
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


class Project(TenantAwareModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_projects')

    assigned_members = models.ManyToManyField(
        User, blank=True, related_name='assigned_project')

    def __str__(self):
        return f"[{self.tenant.slug}] {self.title}"


class Invitation(models.Model):
    class Status:
        CHOICES = [
            ('PENDING', 'pending'),
            ('ACCEPTED', 'accepted'),
            ('EXPIRED', 'expired')
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    email = models.EmailField()
    role = models.CharField(max_length=15, choices=RoleChoices.CHOICES)
    token = models.CharField(max_length=255, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=20, choices=Status.CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField()
