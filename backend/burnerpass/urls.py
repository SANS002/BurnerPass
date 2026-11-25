from django.urls import path
from burnerpass.views import BurnAndRevealAPIView, CheckSecretStatusAPIView, CreateSecretAPIView

urlpatterns = [
    path('api/v1/secrets/create/', CreateSecretAPIView.as_view(), name='api-secret-create'),
    path('api/v1/secrets/<uuid:secret_id>/status/', CheckSecretStatusAPIView.as_view(), name='api-secret-status'),
    path('api/v1/secrets/<uuid:secret_id>/burn/', BurnAndRevealAPIView.as_view(), name='api-secret-burn'),
]