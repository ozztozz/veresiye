from django.urls import path
from . import views 

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('apartment/<str:apartment_number>/', views.apartment_detail, name='apartment_detail'),
    path('apartment/<str:apartment_number>/transactions/', views.htmx_transaction_list, name='htmx_transaction_list'),
]