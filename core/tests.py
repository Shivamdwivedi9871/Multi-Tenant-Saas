from django.test import TestCase
from core.models import User, Tenant, Project
from core.serializers import UserSerializer, TenantSerializer, ProjectSerializer

# Create your tests here.


class SeraializerTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='example@example.com',
            username='example@example.com',
            password='Password123!'
        )

        self.tenant = Tenant.objects.create(
            name="Amc Corp",
            slug='amc-corp',
            plan='FREE'
        )

    # -------------------------------------------------------------------
    # 1. TenantSerializer Tests
    # -------------------------------------------------------------------

    def test_tenant_serializer_valid_data(self):
        data = {"name": "Beta Test", "slug": "beta-test", "plan": "PRO"}
        serializer = TenantSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        tenant = serializer.save()
        self.assertEqual(tenant.slug, 'beta-test')

    def test_tenant_serializer_slug_sanitization(self):
        data = {"name": "Big Corp", "slug": "BIG-CORP", "plan": "ENTERPRISE"}
        serializer = TenantSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['slug'], "big-corp")

    def test_tenant_serializer_invalid_slug(self):
        data = {"name": "Big Auto", "slug": "bIg_auto", "plan": "FREE"}
        serializer = TenantSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("slug", serializer.errors)

    # -------------------------------------------------------------------
    # 2. ProjectSerializer Tests
    # -------------------------------------------------------------------

    def test_project_serializer_valid_data(self):
        data = {
            "title": "New Saas Platform",
            "description": "Multi Tenant Saas Platform"
        }

        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_project_serializer_ignore_tenant_injection(self):
        # Attempt to pass Tenant Id in payload must be ignored
        fake_id = "00000000-0000-0000-0000-000000000000"
        data = {
            "title": "Saas Engine Platform",
            "description": "Multi Level Saas Engine Platform",
            "id": fake_id
        }
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Ensure 'tenant' is not present in validated_data
        self.assertNotIn("tenant", serializer.validated_data)

    def test_project_serializer_representaion(self):
        """Verify output serialization structure includes read-only nested fields."""
        project = Project.objects.create(
            title="Read Test",
            description="",
            tenant=self.tenant,
            created_by=self.user
        )

        serializer = ProjectSerializer(project)
        output = serializer.data

        self.assertEqual(output['title'], "Read Test")
        self.assertEqual(output['created_by']['email'], 'example@example.com')
        self.assertIn('id', output)
