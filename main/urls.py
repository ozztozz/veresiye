from django.urls import path
from . import views 

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('quick_add/', views.quick_add_transaction, name='quick_add_transaction'),
    path('apartment/<str:apartment_number>/', views.apartment_detail, name='apartment_detail'),
    path('payment_waiting/', views.payment_waiting, name='payment_waiting'),
    path('last_transactions/', views.last_transactions, name='last_transactions'),
    path('reports/', views.reports, name='reports'),
    path('apartment/<str:apartment_number>/transactions/', views.htmx_transaction_list, name='htmx_transaction_list'),
    path('blok/<str:blok>/apartments/', views.htmx_apartment_list, name='htmx_apartment_list'),
    path('apartment/<str:apartment_number>/add_transaction/<str:transaction_type>/', views.htmx_transaction_create, name='htmx_transaction_create'),
    path('transaction/<int:transaction_id>/detail/', views.htmx_transaction_detail, name='htmx_transaction_detail'),
    path('transaction/<int:transaction_id>/edit/<str:transaction_type>/', views.htmx_transaction_update, name='htmx_transaction_update'),
    path('apartment/<str:apartment_number>/balance/', views.apartment_balance_api, name='apartment_balance_api'),
    path('htmx/recent_transactions/', views.htmx_recent_transactions, name='htmx_recent_transactions'),
]
