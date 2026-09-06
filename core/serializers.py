from rest_framework import serializers
from .models import (User, Tenant, TenantUser, Project)

# User Serializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

        read_only_fields = ['id']

# Tenant Workspace Serializer


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'plan', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_slug(self, value):
        slug = value.lower().strip()
        if not slug.isalnum() and '-' not in slug:
            raise serializers.ValidationError(
                'SLug can only contains Alphanumeric Characters and Hypens')
        return slug

# Domain Resource Serializer (Tenant Isolation Safeguard)


class TenantUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantUser

        fields = ['id', 'tenant', 'user', 'role', 'created_at']
        read_only_fields = ['id', 'tenant', 'user', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description',
                  'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
