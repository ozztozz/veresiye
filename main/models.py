from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
import json
from datetime import datetime

class Apartment(models.Model):

    number = models.CharField(max_length=3)
    name = models.CharField(max_length=100 ,blank=True, null=True)
    phone= models.CharField(max_length=20, blank=True, null=True)

    def total_debt(self):
        total_debt = self.transactions.filter(is_debt=True).aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total_debt

    def total_payment(self):
        total_payment = self.transactions.filter(is_debt=False).aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total_payment
    def total_balance(self):
        if self.transactions.exists():
            total_balance=self.transactions.filter(is_debt=True).aggregate(models.Sum('amount'))['amount__sum'] or 0 - self.transactions.filter(is_debt=False).aggregate(models.Sum('amount'))['amount__sum'] or 0
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
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_name = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    updated_by_name = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_transactions')

    def __str__(self):
        return f"{self.apartment.number} - {self.amount} - {'Debt' if self.is_debt else 'Payment'}"
    
