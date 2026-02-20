from django.contrib import admin
from .models import Transaction



class TransactionAdmin(admin.ModelAdmin):
    list_display = ('apartment', 'amount', 'payment_method', 'date', 'created_by')
    list_filter = ('payment_method', 'date')
    search_fields = ('apartment', 'description')
    readonly_fields = ('date', 'created_by')


admin.site.register(Transaction, TransactionAdmin)

