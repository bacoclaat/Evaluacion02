# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # auth
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # universitario
    path('universitario/', views.menu_universitario, name='menu_universitario'),
    path('universitario/libros/', views.uni_ver_libros, name='uni_libros'),
    path('universitario/pedir/', views.uni_pedir_prestamo, name='uni_pedir'),
    path('universitario/mis-prestamos/', views.uni_mis_prestamos, name='uni_mis_prestamos'),

    # bibliotecario
    path('bibliotecario/', views.menu_bibliotecario, name='menu_bibliotecario'),
    path('bibliotecario/libros/', views.lib_listar_libros, name='lib_listar_libros'),
    path('bibliotecario/libros/add/', views.lib_agregar_libro, name='lib_add'),
    path('bibliotecario/libros/edit/<int:libro_id>/', views.lib_editar_libro, name='lib_edit'),
    path('bibliotecario/libros/delete/<int:libro_id>/', views.lib_eliminar_libro, name='lib_delete'),
    path('bibliotecario/prestamos/', views.lib_ver_prestamos, name='lib_prestamos'),

    # admin
    path('admin/', views.menu_admin, name='menu_admin'),
    path('admin/usuarios/', views.admin_listar_usuarios, name='admin_usuarios'),
    path('admin/usuarios/edit/<int:usuario_id>/', views.admin_editar_usuario, name='admin_edit_usuario'),
    path('admin/usuarios/delete/<int:usuario_id>/', views.admin_eliminar_usuario, name='admin_delete_usuario'),
]
