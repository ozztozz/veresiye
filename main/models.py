from django.db import models
from django.contrib.contenttypes.models import ContentType
import json
from datetime import datetime

# Create your models here.

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    changes_description = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} {self.model_name} #{self.object_id} by {self.user} on {self.timestamp}"

    def get_changes_summary(self):
        """Generate a human-readable summary of changes."""
        if self.action == 'create':
            return f"Created new {self.model_name.lower()}"
        elif self.action == 'delete':
            return f"Deleted {self.model_name.lower()}"
        else:
            changes = []
            for key in self.new_values:
                if key in self.old_values and self.old_values[key] != self.new_values[key]:
                    old = self.old_values[key]
                    new = self.new_values[key]
                    changes.append(f"{key.replace('_', ' ').title()}: {old} → {new}")
            return "; ".join(changes) if changes else "No changes recorded"


class Transaction(models.Model):
    PAYMENT_METHOD=(
        ('cash', 'Nakit'),
        ('credit_card', 'Kredi Kartı'),
        ('bank_transfer', 'Banka Transferi'),
    )

    apartment = models.CharField(max_length=5)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, null=True, blank=True,choices=PAYMENT_METHOD)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)   
    changed_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='changed_transactions', null=True, blank=True)

    def __str__(self):
        return f"{self.apartment} - {self.amount}"