from django.urls import path
from . import views

urlpatterns = [
    # auth
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.register_view, name="register"),

    # menus normales
    path("uni/menu/", views.uni_menu, name="uni_menu"),
    path("biblio/menu/", views.biblio_menu, name="biblio_menu"),

    # libros
    path("libros/", views.libros_lista, name="libros_lista"),
    path("libros/add/", views.libro_add, name="libro_add"),
    path("libros/<int:libro_id>/edit/", views.libro_edit, name="libro_edit"),
    path("libros/<int:libro_id>/delete/", views.libro_delete, name="libro_delete"),

    # préstamos
    path("prestamos/pedir/<int:libro_id>/", views.pedir_prestamo, name="pedir_prestamo"),
    path("prestamos/mios/", views.uni_mis_prestamos, name="uni_mis_prestamos"),
    path("prestamos/todos/", views.biblio_ver_prestamos, name="biblio_ver_prestamos"),

    # admin usuarios
    path("admin/usuarios/", views.admin_listar_usuarios, name="admin_listar_usuarios"),
    path("admin/usuarios/<int:usuario_id>/edit/", views.admin_editar_usuario, name="admin_editar_usuario"),
    path("admin/usuarios/<int:usuario_id>/delete/", views.admin_eliminar_usuario, name="admin_eliminar_usuario"),
]
