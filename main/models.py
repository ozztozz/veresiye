from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
import json
from datetime import datetime

class Apartment(models.Model):

    number = models.CharField(max_length=3)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def clean(self):
        """Validate apartment data"""
        super().clean()
        if not self.number or not self.number.strip():
            raise ValidationError({'number': 'Apartment number cannot be empty.'})
        
        # Validate phone format if provided
        if self.phone and not self.phone.replace('-', '').replace(' ', '').replace('+', '').isdigit():
            raise ValidationError({'phone': 'Phone number must contain only digits, spaces, hyphens, or plus sign.'})

    def total_debt(self):
        total_debt = self.transactions.filter(is_debt=True, active=True).aggregate(models.Sum('amount', default=0))['amount__sum'] or 0
        return total_debt

    def total_payment(self):
        total_payment = self.transactions.filter(is_debt=False, active=True).aggregate(models.Sum('amount', default=0))['amount__sum'] or 0
        return total_payment
    
    def total_balance(self):
        if self.transactions.exists():
            total_balance = self.transactions.filter(is_debt=True, active=True).aggregate(models.Sum('amount', default=0))['amount__sum'] - self.transactions.filter(is_debt=False, active=True).aggregate(models.Sum('amount', default=0))['amount__sum']
            return total_balance
        return 0 
    
    def __str__(self):
        return self.number
    
class Transaction(models.Model):

    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_debt = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_name = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    updated_by_name = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_transactions')

    class Meta:
        indexes = [
            models.Index(fields=['apartment', 'active', '-date']),
            models.Index(fields=['is_debt', 'active']),
            models.Index(fields=['-updated_at']),
        ]

    def clean(self):
        """Validate transaction data"""
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be greater than zero.'})
        
        if self.amount is not None and self.amount > 999999999.99:
            raise ValidationError({'amount': 'Amount is too large.'})

    def save(self, *args, **kwargs):
        """Override save to call clean()"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.apartment.number} - {self.amount} - {'Debt' if self.is_debt else 'Payment'}"
    
