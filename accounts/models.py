from django.db import models
from django.contrib.auth.models import User
from encrypted_model_fields.fields import EncryptedCharField


class GoogleAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_account')
    access_token = EncryptedCharField(max_length=2048)
    refresh_token = EncryptedCharField(max_length=2048)
    token_expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"GoogleAccount for {self.user.email}"


class DomainFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='domain_filters')
    domain = models.CharField(max_length=255)
    is_allowed = models.BooleanField(default=True)  # False = blocked
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'domain']
        
    def __str__(self):
        filter_type = "Allowed" if self.is_allowed else "Blocked"
        return f"{filter_type} domain: {self.domain} for {self.user.email}"
