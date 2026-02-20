from django.db import models
from django.contrib.contenttypes.models import ContentType
import json
from datetime import datetime

class Apartment(models.Model):

    number = models.CharField(max_length=3)
    name = models.CharField(max_length=100)
    phone= models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Transaction(models.Model):

    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_debt = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.apartment.name} - {self.amount} - {'Debt' if self.is_debt else 'Payment'}"