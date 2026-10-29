from decimal import Decimal
from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'is_debt', 'description']

    def __init__(self, *args, **kwargs):
        if len(args) > 0 and hasattr(args[0], 'copy'):
            data = args[0].copy()
            if 'amount' in data and isinstance(data['amount'], str):
                data['amount'] = data['amount'].replace(',', '.').strip()
            args = (data,) + args[1:]
        elif 'data' in kwargs and hasattr(kwargs['data'], 'copy'):
            data = kwargs['data'].copy()
            if 'amount' in data and isinstance(data['amount'], str):
                data['amount'] = data['amount'].replace(',', '.').strip()
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= Decimal('0'):
            raise forms.ValidationError("Geçerli bir pozitif tutar giriniz.")
        return amount
