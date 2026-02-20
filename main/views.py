from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from.models import Apartment, Transaction


def home(request):
    blok_list= ['A', 'B', 'C', 'D', 'E', 'F','G','H','I']
    number_list = [str(i) for i in range(1, 80)]
    context = {
        'blok_list': blok_list, 
        'number_list': number_list,
    }

    return render(request, 'home.html', context)


def logout_view(request):
    logout(request)
    return redirect('main:home')


def apartment_detail(request, apartment_number):
    # Burada blok ve numara bilgisine göre daire detaylarını çekebilirsiniz
    # Örneğin, Apartment modelinizde blok ve numara alanları varsa:
    # apartment = get_object_or_404(Apartment, blok=blok, number=number)
    apartment = Apartment.objects.filter(number=apartment_number).first()
    if not apartment:
        apartment=Apartment.objects.create(number=apartment_number)
    transactions = Transaction.objects.filter(apartment=apartment).order_by('-updated_at')
    apartment.total_debt = apartment.total_debt()
    apartment.total_payment = apartment.total_payment()
    apartment.total_balance = apartment.total_balance()


    context = {
        'apartment': apartment,
        'transactions': transactions,
    }
    
    return render(request, 'apartment_detail.html', context)

def htmx_transaction_list(request, apartment_number):
    apartment = get_object_or_404(Apartment, number=apartment_number)
    transactions = Transaction.objects.filter(apartment=apartment).order_by('-updated_at')
    
    # Calculate totals
    apartment.total_debt = apartment.total_debt()
    apartment.total_payment = apartment.total_payment()
    apartment.total_balance = apartment.total_balance()
    
    context = {
        'apartment': apartment,
        'transactions': transactions,
    }
    return render(request, 'partials/transaction_list_with_total.html', context)
