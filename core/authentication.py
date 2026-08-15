import jwt
from django.conf import settings
from .models import User
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions, status


class CustomJwtAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_token = request.headers.get(
            'authorization') or request.META.get('HTTP_AUTHORIZATION')

        if not auth_token:
            return None

        parts = auth_token.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed({
                'details': 'Inavlid Token'
            })

        token = parts[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECURITY,
                algorithms=[settings.JWT_ALGORITHM]
            )

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token Expired')

        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid Token')

        types = ['access_token', 'refresh_token']

        token_type = payload.get('type')

        if token_type not in types:
            raise exceptions.AuthenticationFailed('Inavlid Token Provided')

        email = payload.get('email')

        if not email:
            raise exceptions.AuthenticationFailed('Token Missing email')

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('email not found')

        return (user, None)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
