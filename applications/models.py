from django.db import models
from django.contrib.auth.models import User


class Application(models.Model):
    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("INTERVIEW", "Interview"),
        ("OFFER", "Offer"),
        ("REJECTED", "Rejected"),
        ("ARCHIVE", "Archive"),
        ("REPLIED", "Replied")
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    company = models.CharField(max_length=128)
    role = models.CharField(max_length=128)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="APPLIED")
    thread_id = models.CharField(max_length=128, unique=True)
    source_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.role} at {self.company} - {self.status}"
