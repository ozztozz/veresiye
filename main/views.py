import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from.models import Apartment, Transaction
from .forms import TransactionForm


@login_required
def home(request):
    blok_list= ['A', 'B', 'C', 'D', 'E', 'F','G','H','I']
    aka_blok_list= ['AKA-A','AKA-B','AKA-C','AKA-D','AKA-E','AKA-F','AKA-G','AKA-H','AKA-I']
    number_list = [str(i) for i in range(1, 80)]
    context = {
        'blok_list': blok_list, 
        'aka_blok_list': aka_blok_list,
        'number_list': number_list,
    }

    return render(request, 'home.html', context)


def logout_view(request):
    logout(request)
    return redirect('main:home')

@login_required
def apartment_detail(request, apartment_number):
    # Burada blok ve numara bilgisine göre daire detaylarını çekebilirsiniz
    # Örneğin, Apartment modelinizde blok ve numara alanları varsa:
    # apartment = get_object_or_404(Apartment, blok=blok, number=number)
    apartment = Apartment.objects.filter(number=apartment_number).first()
    if not apartment:
        apartment=Apartment.objects.create(number=apartment_number)
    transactions = list(Transaction.objects.filter(apartment=apartment,active=True).order_by('-date'))
    
    # Calculate running balance (from newest to oldest)
    running_balance = apartment.total_balance()
    for transaction in transactions:
        transaction.running_balance = running_balance
        # Subtract this transaction's effect to get previous balance
        if transaction.is_debt:
            running_balance -= transaction.amount
        else:
            running_balance += transaction.amount
    
    apartment.total_debt = apartment.total_debt()
    apartment.total_payment = apartment.total_payment()
    apartment.total_balance = apartment.total_balance()


    context = {
        'apartment': apartment,
        'transactions': transactions,
    }
    
    return render(request, 'apartment_detail.html', context)

@login_required
def payment_waiting(request):
    # Burada ödeme bekleyen daireleri çekebilirsiniz
    apartments = Apartment.objects.annotate(
        calc_balance=Coalesce(
            Sum('transactions__amount', filter=Q(transactions__is_debt=True, transactions__active=True)),
            Value(0, output_field=DecimalField())
        ) - Coalesce(
            Sum('transactions__amount', filter=Q(transactions__is_debt=False, transactions__active=True)),
            Value(0, output_field=DecimalField())
        )
    ).filter(calc_balance__gt=0)
    total_debt = apartments.aggregate(total_debt=Coalesce(Sum('calc_balance'), Value(0, output_field=DecimalField())))['total_debt']
    total_count = apartments.count()      
    
    context = {
        'apartments': apartments,
        'total_debt': total_debt,
        'total_count': total_count,
    }
    
    return render(request, 'payment_waiting.html', context)


@login_required
def last_transactions(request):
    transactions = Transaction.objects.filter(active=True).order_by('-updated_at')[:10]
    context = {
        'transactions': transactions,
    }
    return render(request, 'last_transactions.html', context)

@login_required
def reports(request):
    # Burada raporlar sayfasını oluşturabilirsiniz
    total_debt = Transaction.objects.filter(is_debt=True,active=True,date__date=datetime.date.today()).aggregate(total_debt=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total_debt']
    total_payment = Transaction.objects.filter(is_debt=False,active=True,date__date=datetime.date.today()).aggregate(total_payment=Coalesce(Sum('amount'), Value(0, output_field=DecimalField())))['total_payment']
    total_balance = total_debt - total_payment
    context = {
        'total_debt': total_debt,
        'total_payment': total_payment,
        'total_balance': total_balance,
        'today': datetime.date.today(),
    }
    return render(request, 'reports.html', context)

@login_required
def htmx_apartment_list(request, blok):
    number_list = [str(i) for i in range(1, 80)]
    context = {
        'blok': blok,
        'number_list': number_list,
    }
    return render(request, 'partials/apartment_list.html', context)

@login_required
def htmx_transaction_list(request, apartment_number):
    apartment = get_object_or_404(Apartment, number=apartment_number)
    transactions = list(Transaction.objects.filter(apartment=apartment,active=True).order_by('-date'))
    
    # Calculate running balance (from newest to oldest)
    running_balance = apartment.total_balance()
    for transaction in transactions:
        transaction.running_balance = running_balance
        # Subtract this transaction's effect to get previous balance
        if transaction.is_debt:
            running_balance -= transaction.amount
        else:
            running_balance += transaction.amount
    
    # Calculate totals
    apartment.total_debt = apartment.total_debt()
    apartment.total_payment = apartment.total_payment()
    apartment.total_balance = apartment.total_balance()
    
    context = {
        'apartment': apartment,
        'transactions': transactions,
    }
    return render(request, 'partials/transaction_list_with_total.html', context)


@login_required
def htmx_transaction_create(request, apartment_number,transaction_type):
    apartment = get_object_or_404(Apartment, number=apartment_number)
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.apartment = apartment
            transaction.save()
            return redirect('main:apartment_detail', apartment_number=transaction.apartment.number)
    else:
        form = TransactionForm()

        apartment.total_balance = apartment.total_balance()

    context = {
        'form': form,
        'apartment': apartment,
        'transaction_type': transaction_type,
        
    }
    return render(request, 'partials/modal_transaction.html', context)


@login_required
def htmx_transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    context = {'transaction': transaction}
    return render(request, 'partials/transaction_detail_modal.html', context)


@login_required
def htmx_transaction_update(request, transaction_id,transaction_type):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if request.method == 'POST':
        if transaction_type == 'delete':
            transaction.active = False
            transaction.save()
            return redirect('main:apartment_detail', apartment_number=transaction.apartment.number)
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('main:apartment_detail', apartment_number=transaction.apartment.number)
    else:
        form = TransactionForm(instance=transaction)

    context = {
        'form': form,
        'transaction': transaction,
        'transaction_type': transaction_type,
    }
    return render(request, 'partials/modal_transaction_update.html', context)
