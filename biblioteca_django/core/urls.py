from django.urls import path
from . import views

urlpatterns = [
    # VISTA PRINCIPAL (HTML)
    path('', views.index, name='index'),

    # --- API DE AUTENTICACIÓN ---
    path('api/check_session/', views.check_session, name='api_check_session'),
    path('api/register/', views.register_user, name='api_register'),
    path('api/login/', views.login_user, name='api_login'),
    path('api/logout/', views.logout_user, name='api_logout'),

    # --- API DE LIBROS ---
    path('api/books/', views.get_books, name='api_get_books'),
    path('api/books/add/', views.add_book, name='api_add_book'),
    path('api/books/<int:libro_id>/edit/', views.edit_book, name='api_edit_book'),
    path('api/books/<int:libro_id>/delete/', views.delete_book, name='api_delete_book'),

    # --- API DE USUARIOS ---
    path('api/users/', views.get_users, name='api_get_users'),
    path('api/users/<int:user_id>/edit/', views.edit_user, name='api_edit_user'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='api_delete_user'),

    # --- API DE PRÉSTAMOS ---
    path('api/loans/all/', views.get_all_loans, name='api_get_all_loans'),
    path('api/loans/user/<int:user_id>/', views.get_user_loans, name='api_get_user_loans'),
    path('api/loans/add/', views.add_loan, name='api_add_loan'),
    path('api/loans/<int:prestamo_id>/edit/', views.edit_loan, name='api_edit_loan'),
    path('api/loans/<int:prestamo_id>/return/', views.return_loan, name='api_return_loan'),
    path('api/loans/<int:prestamo_id>/delete/', views.delete_loan, name='api_delete_loan'),
]