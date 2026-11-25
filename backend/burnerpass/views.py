from datetime import timedelta
import re
from cryptography.fernet import InvalidToken
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .crypto import encrypt_secret, decrypt_secret
from .models import EphemeralSecret
from .serializers import EphemeralSecretSerializer, SecretStatusSerializer


class CreateSecretAPIView(APIView):

    def post(self, request):
        serializer = EphemeralSecretSerializer(data = request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

        raw_text = serializer.validated_data['secret_text']
        ttl_hours = serializer.validated_data['ttl_hours']

        encrypted_payload = encrypt_secret(raw_text)
        expiration = timezone.now()+timedelta(hours = ttl_hours)

        secret = EphemeralSecret.objects.create(
            ciphertext = encrypted_payload,
            expires_at = expiration
        )

        burn_path = reverse('api-secret-burn', kwargs = {'secret_id': secret.id})
        burn_url = request.build_absolute_uri(burn_path)

        deep_link = f"burnerpass://burn?url={burn_url}"

        return Response({
            'secret_id': secret.id,
            'burn_url': burn_url,
            'deep_link': deep_link,
            'expires_at': secret.expires_at,
            'message': 'secret encrypted and stored'
        },
        status = status.HTTP_201_CREATED
        )

class CheckSecretStatusAPIView(APIView):
    def get(self, request, secret_id):
        try:
            secret = EphemeralSecret.objects.get(id = secret_id)

        except EphemeralSecret.DoesNotExist:
            return Response({
                'message': 'Secret not found'
            }, status = status.HTTP_404_NOT_FOUND)

        if not secret.is_accessible:
            return Response({
                'is_accessible': False,
                'details': 'secret not found or has expired'
                
            },
            status = status.HTTP_404_NOT_FOUND
            )

        serializer = SecretStatusSerializer(secret)
        return Response(serializer.data, status = status.HTTP_200_OK)

class BurnAndRevealAPIView(APIView):
    def post(self,request, secret_id):
        with transaction.atomic():
            try:
                secret = EphemeralSecret.objects.select_for_update().get(id = secret_id)
            except EphemeralSecret.DoesNotExist:
                return Response({
                    'details': 'secret not found or has expired'
                }, 
                status = status.HTTP_410_GONE
                )

            if not secret.is_accessible:
                if not secret.is_burned:
                    secret.is_burned = True
                    secret.ciphertext = b""
                    secret.save(update_fields = ['is_burned', 'ciphertext'])
                return Response({
                    'details': 'secret not found or has expired'
                },
                  status = status.HTTP_410_GONE
                )

            try:
                plaintext_payload= decrypt_secret(secret.ciphertext)
            except InvalidToken:
                return Response({
                    'details': 'decryption failed due to currepted data'
                },
                status = status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            secret.is_burned = True
            secret.ciphertext = b"" 
            secret.save(update_fields = ['is_burned', 'ciphertext'])

            return Response({
                'secret_txt': plaintext_payload,
                'details': 'secret burned and revealed'
            },
            status = status.HTTP_200_OK
            )
            
