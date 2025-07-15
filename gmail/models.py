from django.db import models
from django.contrib.auth.models import User
from applications.models import Application


class Email(models.Model):
    CATEGORY_CHOICES = [
        ("PROSPECT_SINGLE", "Single Prospect"),
        ("JOB_LINK_LIST", "Job Link List"),
        ("APPLICATION_RESPONSE", "Application Response")
    ]
    
    SUB_CATEGORY_CHOICES = [
        ("DENIAL", "Denial"),
        ("INTERESTED", "Interested")
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, related_name='emails')
    gmail_id = models.CharField(max_length=128, unique=True)
    thread_id = models.CharField(max_length=128)
    subject = models.TextField()
    body_plain = models.TextField()
    body_html = models.TextField(null=True, blank=True)
    sender = models.EmailField()
    recipient = models.EmailField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, null=True, blank=True)
    sub_category = models.CharField(max_length=20, choices=SUB_CATEGORY_CHOICES, null=True, blank=True)
    draft_id = models.CharField(max_length=128, null=True, blank=True)  # Gmail draft ID if created
    has_to_respond_label = models.BooleanField(default=False)
    received_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-received_at']
        
    def __str__(self):
        return f"{self.subject} - {self.category or 'Unclassified'}"


class DiscoveredLink(models.Model):
    CRAWL_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("FETCHED", "Fetched"),
        ("ERROR", "Error")
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discovered_links')
    source_email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='discovered_links')
    url = models.TextField()
    fetched_html = models.TextField(null=True, blank=True)
    fetched_text = models.TextField(null=True, blank=True)  # Extracted text content
    is_valid_listing = models.BooleanField(default=False)
    confidence_score = models.IntegerField(null=True, blank=True)  # 0-100
    extracted_company = models.CharField(max_length=128, null=True, blank=True)
    extracted_role = models.CharField(max_length=128, null=True, blank=True)
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name='discovered_links')
    crawl_status = models.CharField(max_length=20, choices=CRAWL_STATUS_CHOICES, default="PENDING")
    error_message = models.TextField(null=True, blank=True)
    crawled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['source_email', 'url']
        
    def __str__(self):
        return f"{self.url} - {self.crawl_status}"
