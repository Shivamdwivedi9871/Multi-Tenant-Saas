from django.urls import path
from .views import UserView, TenantView, JwtToken, AccessTokenFromRefreshToken, ProjectView

urlpatterns = [
    path('crate_user/', UserView.as_view(), name='create-user'),
    path('create_token/', JwtToken.as_view(), name='create_token'),
    path('refresh_token/', AccessTokenFromRefreshToken.as_view(),
         name='access_token_from_refresh'),
    path('tenant/onboard/', TenantView.as_view(), name='create_tenant'),
    path('projects/', ProjectView.as_view(), name='project_view'),
]
