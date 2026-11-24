import uuid
from django.db import models
from django.utils import timezone

class EphemeralSecret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    ciphertext = models.BinaryField()
    created_at  = models.DateTimeField(auto_now_add = True)
    expires_at = models.DateTimeField()
    is_burned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_accessible(self) -> bool:
        return not self.is_burned and timezone.now() < self.expires_at

    def __str__(self):
        return f"Secret {self.id} | Burned: {self.is_burned}"

    
