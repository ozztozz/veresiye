from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import parse_qs
from .models import Transaction

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required(login_url='main:login')
def home(request):
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'home.html', {'transactions': transactions})

@login_required(login_url='main:login')
@require_http_methods(["GET"])
def transaction_form(request):
    """Render the transaction form modal."""
    return render(request, 'transaction_modal.html')

@login_required(login_url='main:login')
@require_http_methods(["POST"])
def transaction_create(request):
    """Create a new transaction via HTMX."""
    apartment = request.POST.get('apartment')
    amount = request.POST.get('amount')
    payment_method = request.POST.get('payment_method', None)
    paid = request.POST.get('paid') == 'on'
    description = request.POST.get('description', '')
    
    try:
        transaction = Transaction.objects.create(
            apartment=apartment,
            amount=amount,
            payment_method=payment_method if payment_method else None,
            paid=paid,
            description=description,
            created_by=request.user
        )
        # Return the new transaction row HTML
        return render(request, 'transaction_row.html', {'transaction': transaction}, status=201)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=400)

@login_required(login_url='main:login')
@require_http_methods(["GET"])
def transaction_list_ajax(request):
    """Return the updated transaction list for HTMX."""
    transactions = Transaction.objects.all().order_by('-date')
    return render(request, 'transaction_list.html', {'transactions': transactions})

@login_required(login_url='main:login')
@require_http_methods(["GET"])
def transaction_edit(request, transaction_id):
    """Show the edit form for a transaction."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'transaction_modal_edit.html', {'transaction': transaction})

@login_required(login_url='main:login')
@require_http_methods(["POST"])
def transaction_update(request, transaction_id):
    """Update a transaction via HTMX."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    apartment = request.POST.get('apartment')
    amount = request.POST.get('amount')
    payment_method = request.POST.get('payment_method', None)
    paid = request.POST.get('paid') == 'on'
    description = request.POST.get('description', '')
    
    try:
        transaction.apartment = apartment
        transaction.amount = amount
        transaction.payment_method = payment_method if payment_method else None
        transaction.paid = paid
        transaction.description = description
        transaction.changed_by = request.user
        transaction.save()
        return render(request, 'transaction_row.html', {'transaction': transaction})
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=400)

@login_required(login_url='main:login')
@require_http_methods(["GET"])
def transaction_row(request, transaction_id):
    """Get a single transaction row."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'transaction_row.html', {'transaction': transaction})

@login_required(login_url='main:login')
@require_http_methods(["GET"])
def transaction_row_edit(request, transaction_id):
    """Get the edit form for a transaction row."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    return render(request, 'transaction_row_edit.html', {'transaction': transaction})

@login_required(login_url='main:login')
@require_http_methods(["POST"])
def transaction_delete(request, transaction_id):
    """Delete a transaction via HTMX."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.delete()
    return HttpResponse("", status=200)