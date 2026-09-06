from rest_framework import viewsets, exceptions
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from .utils import create_access_token, create_refresh_token, decode_token
from .models import User, Tenant, TenantUser, Project
from .serializers import UserSerializer, TenantSerializer, TenantUserSerializer, ProjectSerializer
from .authentication import CustomJwtAuthentication
from .permissions import IsAdminOrReadOnly, IsMember
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
