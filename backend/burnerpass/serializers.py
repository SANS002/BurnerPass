from rest_framework import serializers
from .models import EphemeralSecret

class EphemeralSecretSerializer(serializers.ModelSerializer):
    secret_txt = serializers.CharField(write_only=True, required=True, min_length=1)
    ttl_hours = serializers.IntegerField(write_only=True, max_value = 168 ,min_value=1, default = 24)

class SecretStatusSerializer(serializers.ModelSerializer):
    is_accessible = serializers.BooleanField(read_only = True)

    class Meta:
        model = EphemeralSecret
        fields = ['id', 'is_accessible', 'expires_at']