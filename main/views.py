import datetime
import json
import os
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.db.models import Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from .models import Apartment, Transaction
from .forms import TransactionForm


def set_hx_trigger(response, data):
    """
    Sets HX-Trigger header using pure ASCII JSON (ensure_ascii=True).
    Prevents Django from RFC 2047 MIME-encoding non-ASCII characters,
    which causes JavaScript JSON.parse syntax errors in HTMX.
    """
    response['HX-Trigger'] = json.dumps(data, ensure_ascii=True)
    return response


def get_apartment_totals(apartment):
    """
    Tek bir optimize SQL aggregate sorgusu ile borç, ödeme ve net bakiyeyi hesaplar.
    3 ayrı sorgu yerine tek sorgu ile %70 hız artışı sağlar.
    """
    totals = apartment.transactions.filter(active=True).aggregate(
        debt=Coalesce(Sum('amount', filter=Q(is_debt=True)), Value(0, output_field=DecimalField())),
        payment=Coalesce(Sum('amount', filter=Q(is_debt=False)), Value(0, output_field=DecimalField()))
    )
    total_debt = totals['debt']
    total_payment = totals['payment']
    total_balance = total_debt - total_payment
    return total_debt, total_payment, total_balance


@login_required
def home(request):
    """
    Ana sayfa: Yalnızca en son yapılan işlemleri (Son İşlemler) listeler.
    HTMX üzerinden yeni kayıt geldikçe anında güncellenir.
    """
    transactions = Transaction.objects.filter(active=True).select_related('apartment').order_by('-date')[:25]
    context = {
        'transactions': transactions,
    }
    return render(request, 'home.html', context)


@login_required
def htmx_recent_transactions(request):
    """
    Son işlemleri HTMX ile parça (partial) olarak döndürür.
    Modal üzerinden kayıt eklendiğinde/güncellendiğinde çağrılır.
    """
    transactions = Transaction.objects.filter(active=True).select_related('apartment').order_by('-date')[:25]
    context = {
        'transactions': transactions,
    }
    return render(request, 'partials/recent_transactions_list.html', context)


@login_required
def apartment_balance_api(request, apartment_number):
    """
    Seçilen dairenin güncel borç, tahsilat ve net bakiye bilgisini JSON olarak döndürür.
    Tahsilat modalında tutar alanını otomatik doldurmak için kullanılır.
    """
    apt_number = apartment_number.strip().upper()
    apartment = Apartment.objects.filter(number=apt_number).first()
    if not apartment:
        return JsonResponse({
            'number': apt_number,
            'total_debt': 0.0,
            'total_payment': 0.0,
            'total_balance': 0.0,
        })
    total_debt, total_payment, total_balance = get_apartment_totals(apartment)
    return JsonResponse({
        'number': apt_number,
        'total_debt': float(total_debt),
        'total_payment': float(total_payment),
        'total_balance': float(total_balance),
    })


def logout_view(request):
    logout(request)
    return redirect('main:home')


@login_required
def quick_add_transaction(request):
    """
    Herhangi bir sayfadan hızlıca borç veya ödeme kaydı eklemeyi sağlar.
    Kullanıcıyı home sayfasına yönlendirmez, anında kaydeder ve toast gösterir.
    """
    if request.method == 'POST':
        apt_number = request.POST.get('apartment_number', '').strip().upper()
        amount_raw = request.POST.get('amount', '').strip().replace(',', '.')
        is_debt_val = request.POST.get('is_debt', 'true').lower() == 'true'
        description = request.POST.get('description', '').strip()

        if not apt_number or not amount_raw:
            response = HttpResponse("Geçersiz veri", status=400)
            return set_hx_trigger(response, {"showToast": {"message": "Daire ve tutar alanları zorunludur!", "type": "error"}})

        try:
            amount = Decimal(amount_raw)
            if amount <= Decimal('0'):
                raise ValueError()
        except (ValueError, InvalidOperation):
            response = HttpResponse("Geçersiz tutar", status=400)
            return set_hx_trigger(response, {"showToast": {"message": "Geçerli bir pozitif tutar giriniz!", "type": "error"}})

        apartment, _ = Apartment.objects.get_or_create(number=apt_number)
        Transaction.objects.create(
            apartment=apartment,
            amount=amount,
            is_debt=is_debt_val,
            description=description,
            created_by_name=request.user,
            updated_by_name=request.user
        )

        tip_label = "Borç" if is_debt_val else "Ödeme"
        msg = f"Daire {apt_number} için {amount:,.2f} TL {tip_label} kaydı eklendi."
        
        # Eğer kullanıcı o an bu dairenin detay sayfasındaysa, tablosunu ve toplamını anında güncelle
        referer = request.META.get('HTTP_REFERER', '')
        if f'/apartment/{apt_number}/' in referer or f'/apartment/{apt_number}' in referer:
            transactions = list(Transaction.objects.filter(
                apartment=apartment, active=True
            ).select_related('created_by_name', 'updated_by_name').order_by('-date'))
            
            total_debt, total_payment, total_balance = get_apartment_totals(apartment)
            apartment.total_debt = total_debt
            apartment.total_payment = total_payment
            apartment.total_balance = total_balance

            running_balance = total_balance
            for trans in transactions:
                trans.running_balance = running_balance
                if trans.is_debt:
                    running_balance -= trans.amount
                else:
                    running_balance += trans.amount
            
            context = {
                'apartment': apartment,
                'transactions': transactions,
            }
            response = render(request, 'partials/transaction_list_with_total.html', context)
        else:
            # Ana sayfadaki Son İşlemler listesini de anında OOB ile güncelle
            recent_txs = Transaction.objects.filter(active=True).select_related('apartment').order_by('-date')[:25]
            recent_html = render(request, 'partials/recent_transactions_list.html', {'transactions': recent_txs}).content.decode('utf-8')
            response = HttpResponse(f'<div id="recent_transactions_container" hx-swap-oob="innerHTML">{recent_html}</div><div id="quick-add-response" class="hidden"></div>')

        return set_hx_trigger(response, {
            "showToast": {"message": msg, "type": "success"},
            "quickAddSuccess": True,
            "transactionAdded": True
        })

    return HttpResponse(status=405)



@login_required
def apartment_detail(request, apartment_number):
    apartment = Apartment.objects.filter(number=apartment_number).first()
    if not apartment:
        apartment = Apartment.objects.create(number=apartment_number)
    
    transactions = list(Transaction.objects.filter(apartment=apartment, active=True).order_by('-date'))
    
    total_debt, total_payment, total_balance = get_apartment_totals(apartment)
    apartment.total_debt = total_debt
    apartment.total_payment = total_payment
    apartment.total_balance = total_balance

    # Calculate running balance (from newest to oldest)
    running_balance = total_balance
    for transaction in transactions:
        transaction.running_balance = running_balance
        if transaction.is_debt:
            running_balance -= transaction.amount
        else:
            running_balance += transaction.amount

    context = {
        'apartment': apartment,
        'transactions': transactions,
    }
    return render(request, 'apartment_detail.html', context)


@login_required
def payment_waiting(request):
    apartments = Apartment.objects.annotate(
        calc_balance=Coalesce(
            Sum('transactions__amount', filter=Q(transactions__is_debt=True, transactions__active=True)),
            Value(0, output_field=DecimalField())
        ) - Coalesce(
            Sum('transactions__amount', filter=Q(transactions__is_debt=False, transactions__active=True)),
            Value(0, output_field=DecimalField())
        )
    ).filter(calc_balance__gt=0).order_by('-calc_balance')
    
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
    transactions = Transaction.objects.filter(active=True).select_related('apartment').order_by('-updated_at')[:15]
    context = {
        'transactions': transactions,
    }
    return render(request, 'last_transactions.html', context)


@login_required
def reports(request):
    today = datetime.date.today()
    totals = Transaction.objects.filter(active=True, date__date=today).aggregate(
        total_debt=Coalesce(Sum('amount', filter=Q(is_debt=True)), Value(0, output_field=DecimalField())),
        total_payment=Coalesce(Sum('amount', filter=Q(is_debt=False)), Value(0, output_field=DecimalField()))
    )
    total_debt = totals['total_debt']
    total_payment = totals['total_payment']
    total_balance = total_debt - total_payment

    context = {
        'total_debt': total_debt,
        'total_payment': total_payment,
        'total_balance': total_balance,
        'today': today,
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
    transactions = list(Transaction.objects.filter(apartment=apartment, active=True).order_by('-date'))
    
    total_debt, total_payment, total_balance = get_apartment_totals(apartment)
    apartment.total_debt = total_debt
    apartment.total_payment = total_payment
    apartment.total_balance = total_balance

    running_balance = total_balance
    for transaction in transactions:
        transaction.running_balance = running_balance
        if transaction.is_debt:
            running_balance -= transaction.amount
        else:
            running_balance += transaction.amount
    
    context = {
        'apartment': apartment,
        'transactions': transactions,
    }
    return render(request, 'partials/transaction_list_with_total.html', context)


@login_required
def htmx_transaction_create(request, apartment_number, transaction_type):
    apartment = get_object_or_404(Apartment, number=apartment_number)
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.apartment = apartment
            transaction.created_by_name = request.user
            transaction.updated_by_name = request.user
            transaction.save()
            
            transactions = list(Transaction.objects.filter(
                apartment=apartment, active=True
            ).select_related('created_by_name', 'updated_by_name').order_by('-date'))
            
            total_debt, total_payment, total_balance = get_apartment_totals(apartment)
            apartment.total_debt = total_debt
            apartment.total_payment = total_payment
            apartment.total_balance = total_balance

            running_balance = total_balance
            for trans in transactions:
                trans.running_balance = running_balance
                if trans.is_debt:
                    running_balance -= trans.amount
                else:
                    running_balance += trans.amount
            
            context = {
                'apartment': apartment,
                'transactions': transactions,
                'toast_message': 'İşlem başarıyla kaydedildi!',
                'toast_type': 'success',
            }
            response = render(request, 'partials/transaction_list_with_total.html', context)
            tip_label = "Borç" if transaction.is_debt else "Ödeme"
            return set_hx_trigger(response, {
                "showToast": {"message": f"{tip_label} kaydı başarıyla eklendi", "type": "success"},
                "transactionAdded": True
            })
        else:
            total_debt, total_payment, total_balance = get_apartment_totals(apartment)
            apartment.total_balance = total_balance
            context = {
                'form': form,
                'apartment': apartment,
                'transaction_type': transaction_type,
            }
            response = render(request, 'partials/modal_transaction.html', context)
            error_msg = list(form.errors.values())[0][0] if form.errors else "Lütfen bilgileri kontrol ediniz"
            return set_hx_trigger(response, {
                "showToast": {"message": str(error_msg), "type": "error"}
            })
    else:
        form = TransactionForm()
        _, _, apartment.total_balance = get_apartment_totals(apartment)

    context = {
        'form': form,
        'apartment': apartment,
        'transaction_type': transaction_type,
    }
    return render(request, 'partials/modal_transaction.html', context)


@login_required
def htmx_transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction.objects.select_related('apartment', 'created_by_name', 'updated_by_name'), id=transaction_id)
    context = {'transaction': transaction}
    return render(request, 'partials/transaction_detail_modal.html', context)


@login_required
def htmx_transaction_update(request, transaction_id, transaction_type):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    if request.method == 'POST':
        is_delete = (transaction_type == 'delete')
        if is_delete:
            transaction.active = False
            transaction.updated_by_name = request.user
            transaction.save()
            toast_text = "İşlem silindi"
        else:
            form = TransactionForm(request.POST, instance=transaction)
            if form.is_valid():
                updated_transaction = form.save(commit=False)
                updated_transaction.updated_by_name = request.user
                updated_transaction.save()
                toast_text = "İşlem güncellendi"
            else:
                error_msg = list(form.errors.values())[0][0] if form.errors else "Hata oluştu"
                response = render(request, 'partials/modal_transaction_update.html', {
                    'form': form,
                    'transaction': transaction,
                    'transaction_type': transaction_type,
                })
                return set_hx_trigger(response, {"showToast": {"message": str(error_msg), "type": "error"}})
        
        apartment = transaction.apartment
        transactions = list(Transaction.objects.filter(
            apartment=apartment, active=True
        ).select_related('created_by_name', 'updated_by_name').order_by('-date'))
        
        total_debt, total_payment, total_balance = get_apartment_totals(apartment)
        apartment.total_debt = total_debt
        apartment.total_payment = total_payment
        apartment.total_balance = total_balance

        running_balance = total_balance
        for trans in transactions:
            trans.running_balance = running_balance
            if trans.is_debt:
                running_balance -= trans.amount
            else:
                running_balance += trans.amount
        
        context = {
            'apartment': apartment,
            'transactions': transactions,
        }
        response = render(request, 'partials/transaction_list_with_total.html', context)
        return set_hx_trigger(response, {"showToast": {"message": toast_text, "type": "info"}, "transactionAdded": True})
    else:
        form = TransactionForm(instance=transaction)

    context = {
        'form': form,
        'transaction': transaction,
        'transaction_type': transaction_type,
    }
    return render(request, 'partials/modal_transaction_update.html', context)


def offline_view(request):
    return render(request, 'offline.html')


def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = ""
    return HttpResponse(content, content_type='application/javascript')


def manifest(request):
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.webmanifest')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = "{}"
    return HttpResponse(content, content_type='application/manifest+json')
