from django.utils import timezone
from rest_framework import viewsets, exceptions
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from .utils import create_access_token, create_refresh_token, decode_token, secret_token, expiry_date
from .models import User, Tenant, TenantUser, Project, Invitation
from .serializers import UserSerializer, TenantSerializer, TenantUserSerializer, ProjectSerializer, InvitationSerializer
from .authentication import CustomJwtAuthentication
from .permissions import IsAdminOrReadOnly, IsMember, IsManager
from .tasks import send_invite_email

# Create your views here.


class UserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        serializer.save()


class JwtToken(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response({"detail": 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        return Response({
            "access_token": access_token,
            "refresh_token": refresh_token
        })


class AccessTokenFromRefreshToken(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({"details": "Invalid Token"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = decode_token(refresh_token)

        if not payload:
            return Response({
                "detail": "Invalid or Expire Signature"
            })

        token_type = payload.get('type')

        if token_type != ('refresh_token'):
            raise exceptions.AuthenticationFailed({'detail': 'invalid token'})

        email = payload.get('email')

        if not email:
            return Response({
                'detail': 'Token missing username'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            return Response(
                {
                    'detail': 'User Not Found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        new_access = create_access_token(user)

        return Response(
            {
                'access_token': f"Bearer {new_access}",
                'token_type': 'bearer'
            },
            status=status.HTTP_201_CREATED
        )


class TenantView(APIView):
    authentication_classes = [CustomJwtAuthentication]
    permission_classes = [IsAuthenticated]
    permission = IsAdminOrReadOnly()

    def post(self, request):
        serializer = TenantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            tenant = serializer.save()
            tenant_user = TenantUser.objects.create(
                tenant=tenant,
                user=request.user,
                role='ADMIN',
            )
        membership_data = TenantUserSerializer(tenant_user).data

        return Response(
            {
                'tenant': TenantSerializer(tenant).data,
                'role': membership_data
            },
            status=status.HTTP_201_CREATED
        )

    def get(self, request):
        tenant_user = TenantUser.objects.select_related(
            'tenant', 'user').filter(user=request.user)

        seralizer = TenantUserSerializer(tenant_user, many=True)

        return Response(seralizer.data, status=status.HTTP_200_OK)


class ProjectView(APIView):
    permission_classes = [IsAuthenticated, IsMember, IsAdminOrReadOnly]
    authentication_classes = [CustomJwtAuthentication]

    def get(self, request):

        if not request.tenant:
            return Response([])

        project = Project.objects.filter(tenant=request.tenat)

        serializer = ProjectSerializer(project, many=True)

        return Response(serializer.data)

    def post(self, request):
        if not request.tenant:
            return Response(
                {
                    'detail': 'Tenant Header Missing'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProjectSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(
            tenant=request.tenant,
            created_by=request.user
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TenantInvitationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly, IsManager]

    def post(self, request):
        if not request.tenant or request.tenant is None:
            return Response('Tenant Context Missing', status=status.HTTP_400_BAD_REQUEST)

        serializer = InvitationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        target_role = serializer.validated_data['role']

        tenantuser = TenantUser.objects.filter(
            tenant=request.tenant, user__email=email)

        if tenantuser.exists():
            return Response('User is already a member of this workspace', status=status.HTTP_400_BAD_REQUEST)

        if Invitation.objects.filter(tenant=request.tenant, email=email, status='PENDING').exists():
            return Response('Invitation already sent/exist for this email', status=status.HTTP_400_BAD_REQUEST)
        token = secret_token()

        with transaction.atomic():
            serializer.save(
                tenant=request.tenant,
                email=email,
                role=target_role,
                token=token,
                invited_by=request.user,
                status='PENDING',
                expiry_at=expiry_date(7)
            )
            transaction.on_commit(
                lambda: send_invite_email.delay(
                    token,
                    email,
                    tenant_name=request.tenant.name
                )
            )

        return Response('Successfully Invitation sent', status=status.HTTP_201_CREATED)


class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('token', None)

        invitation = Invitation.objects.filter(
            token=token, status='PENDING').first()

        if not invitation or invitation.expiry_at < timezone.now():
            if invitation:
                invitation.status = 'EXPIRED'
                invitation.save()
            return Response(
                {
                    'error': 'Invalid or expired invitation token'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.email != invitation.email:
            return Response(
                {
                    'detail': 'This Invitation was sent to different email address'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Idomptancy check
        if TenantUser.objects.filter(tenant=invitation.tenant, user=request.user).exists():
            return Response('You are already a member of this workspace', status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            TenantUser.objects.create(
                tenant=invitation.tenant,
                user=request.user,
                role=invitation.role
            )

            invitation.status = 'ACCEPTED'
            invitation.save()

        return Response('Successfully joined workspace', status=status.HTTP_200_OK)


class ProjectViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsMember]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        tenant_user = getattr(self.request, 'tenant_user', None)
        if not tenant or not tenant_user:
            return Project.objects.none()

        base_project = Project.objects.filter(tenant=tenant)

        if tenant_user.role in ['ADMIN', 'MANAGER']:
            return base_project

        else:
            return base_project.filter(
                Q(created_by=self.request.user) |
                Q(assigned_members=self.request.user)
            ).distinct()

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )


class UserWorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_membership = TenantUser.objects.filter(
            user=request.user).select_related('tenant')

        tenant_list = []

        for member in user_membership:
            if not member.tenant.is_active:
                continue

            tenant_list.append(
                {
                    'tenant_id': member.tenant.id,
                    'name': member.tenant.name,
                    'slug': member.tenant.slug,
                    'plan': member.tenant.plan,
                    'my_role': member.role
                }
            )
        return Response(tenant_list, status=status.HTTP_200_OK)
