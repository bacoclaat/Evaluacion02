from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_view, name='inicio'),

    # login / registro
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.registro_view, name='registro'),

    # menús
    path('menu/universitario/', views.menu_universitario, name='menu_universitario'),
    path('menu/bibliotecario/', views.menu_bibliotecario, name='menu_bibliotecario'),
    path('menu/admin/', views.menu_admin, name='menu_admin'),

    # libros / préstamos
    path('libros/', views.ver_libros, name='ver_libros'),
    path('libros/<int:libro_id>/prestar/', views.prestar_libro, name='prestar'),
    path('prestamos/', views.ver_prestamos, name='ver_prestamos'),

    # --- CRUD de usuarios (ADMIN) ---
    path('admin/users/', views.admin_user_list, name='admin_user_list'),
    path('admin/users/add/', views.admin_user_add, name='admin_user_add'),
    path('admin/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
]

#API REST
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet)
router.register(r'universitarios', views.UniversitarioViewSet)
router.register(r'bibliotecarios', views.BibliotecarioViewSet)
router.register(r'admin', views.AdminViewSet)
router.register(r'libros', views.LibroViewSet)
router.register(r'prestamos', views.PrestamoViewSet)

urlpatterns = [
    # Rutas web existentes
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('menu/universitario/', views.menu_universitario, name='menu_universitario'),
    path('menu/bibliotecario/', views.menu_bibliotecario, name='menu_bibliotecario'),
    path('menu/admin/', views.menu_admin, name='menu_admin'),
    path('libros/', views.ver_libros, name='ver_libros'),
    path('libros/<int:libro_id>/prestar/', views.prestar_libro, name='prestar'),
    path('prestamos/', views.ver_prestamos, name='ver_prestamos'),

    # Rutas API (JSON)
    path('api/', include(router.urls)),
]

#API Indicadores Económicos
from django.urls import path
from . import views

urlpatterns = [
    # Ruta para todos los indicadores (Accesible en /api/indicadores/)
    path('indicadores/', views.indicadores, name='indicadores'),

    # Ruta para un indicador específico (Accesible en /api/indicadores/dolar/)
    path('indicadores/<str:nombre>/', views.indicador, name='indicador'),
]