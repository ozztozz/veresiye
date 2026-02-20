from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.apps import AppConfig
from .models import Transaction, AuditLog
import json
import logging

logger = logging.getLogger('main.signals')

# Store original values before update
_original_values = {}


@receiver(pre_save, sender=Transaction)
def track_changes_pre_save(sender, instance, **kwargs):
    """Capture original values before save."""
    if instance.pk:
        try:
            original = Transaction.objects.get(pk=instance.pk)
            _original_values[instance.pk] = {
                'apartment': original.apartment,
                'amount': str(original.amount),
                'paid': original.paid,
                'description': original.description,
                'payment_method': original.payment_method,
            }
        except Transaction.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def log_transaction_changes(sender, instance, created, **kwargs):
    """Log Transaction model changes to AuditLog."""
    request = getattr(instance, '_request', None)
    user = request.user if request else None
    
    new_values = {
        'apartment': instance.apartment,
        'amount': str(instance.amount),
        'paid': instance.paid,
        'description': instance.description,
        'payment_method': instance.payment_method,
    }
    
    old_values = _original_values.get(instance.pk, {})
    action = 'create' if created else 'update'
    
    audit = AuditLog.objects.create(
        action=action,
        model_name='Transaction',
        object_id=str(instance.pk),
        user=user,
        old_values=old_values if not created else {},
        new_values=new_values,
        changes_description=f"Transaction #{instance.pk} {action}d"
    )
    
    logger.info(f"{action.upper()} Transaction #{instance.pk}: {audit.get_changes_summary()} by {user}")
    
    # Clean up
    if instance.pk in _original_values:
        del _original_values[instance.pk]


@receiver(post_delete, sender=Transaction)
def log_transaction_deletion(sender, instance, **kwargs):
    """Log Transaction deletion to AuditLog."""
    request = getattr(instance, '_request', None)
    user = request.user if request else None
    
    audit = AuditLog.objects.create(
        action='delete',
        model_name='Transaction',
        object_id=str(instance.pk),
        user=user,
        old_values={
            'apartment': instance.apartment,
            'amount': str(instance.amount),
            'paid': instance.paid,
            'description': instance.description,
            'payment_method': instance.payment_method,
        },
        new_values={},
        changes_description=f"Transaction #{instance.pk} deleted"
    )
    
    logger.info(f"DELETE Transaction #{instance.pk}: Deleted by {user}")
