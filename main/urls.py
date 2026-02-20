from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='main:login'), name='logout'),
    
    # Transaction HTMX endpoints
    path('transaction/form/', views.transaction_form, name='transaction_form'),
    path('transaction/create/', views.transaction_create, name='transaction_create'),
    path('transaction/list/', views.transaction_list_ajax, name='transaction_list_ajax'),
    path('transaction/<int:transaction_id>/', views.transaction_row, name='transaction_row'),
    path('transaction/<int:transaction_id>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transaction/<int:transaction_id>/edit-row/', views.transaction_row_edit, name='transaction_row_edit'),
    path('transaction/<int:transaction_id>/update/', views.transaction_update, name='transaction_update'),
    path('transaction/<int:transaction_id>/delete/', views.transaction_delete, name='transaction_delete'),
]