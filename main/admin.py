from django.contrib import admin
from .models import Transaction, AuditLog


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'model_name', 'object_id', 'user', 'changes_description')
    list_filter = ('action', 'model_name', 'timestamp', 'user')
    search_fields = ('model_name', 'object_id', 'changes_description')
    readonly_fields = ('timestamp', 'action', 'model_name', 'object_id', 'old_values', 'new_values', 'user')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('apartment', 'amount', 'paid', 'payment_method', 'date', 'created_by')
    list_filter = ('paid', 'payment_method', 'date')
    search_fields = ('apartment', 'description')
    readonly_fields = ('date', 'created_by')


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
