from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('menu/universitario/', views.menu_universitario, name='menu_universitario'),
    path('menu/bibliotecario/', views.menu_bibliotecario, name='menu_bibliotecario'),
    path('menu/admin/', views.menu_admin, name='menu_admin'),
    path('libros/', views.ver_libros, name='ver_libros'),
    path('libros/<int:libro_id>/prestar/', views.prestar_libro, name='prestar'),
    path('prestamos/', views.ver_prestamos, name='ver_prestamos'),
]
