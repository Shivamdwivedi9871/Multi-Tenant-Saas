import jwt
from datetime import datetime, timezone, timedelta
from django.conf import settings


def create_access_token(user):
    now = datetime.now(timezone.utc)

    access_expiry = now + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRATION)

    payload = {
        'email': user.email,
        'exp': access_expiry,
        'iat': now,
        'type': 'access_token',
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY,
                       algorithm=settings.JWT_ALGORITHM)

    return token


def create_refresh_token(user):
    now = datetime.now(timezone.utc)

    refress_expiry = now + \
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRATION)

    payload = {
        'email': user.email,
        'exp': refress_expiry,
        'iat': now,
        'type': 'refresh_token'
    }

    token = jwt.encode(payload, settings.JWT_SECURITY,
                       algorithm=settings.JWT_ALGORITH)

    return token
