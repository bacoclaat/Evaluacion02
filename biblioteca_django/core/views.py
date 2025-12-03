from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse # Necesario para las APIs de Mindicador
from datetime import date, timedelta
import bcrypt
import requests
import json
from requests.exceptions import RequestException

# --- Integración con la lógica de auditoría y API externa ---
# Asegúrate de que este archivo exista y contenga log_auditoria y get_valor_uf
from .integracion_bd import log_auditoria, get_valor_uf 

from .models import Usuario, Universitario, Bibliotecario, Admin, Libro, Prestamo

# --- Importaciones de DRF ---
from rest_framework import viewsets
from .serializers import (
    UsuarioSerializer, UniversitarioSerializer, BibliotecarioSerializer,
    AdminSerializer, LibroSerializer, PrestamoSerializer
)


# ----------------------------
# VIEWSETS DRF (API REST GESTIÓN)
# ----------------------------
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class UniversitarioViewSet(viewsets.ModelViewSet):
    queryset = Universitario.objects.all()
    serializer_class = UniversitarioSerializer

class BibliotecarioViewSet(viewsets.ModelViewSet):
    queryset = Bibliotecario.objects.all()
    serializer_class = BibliotecarioSerializer

class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer

class LibroViewSet(viewsets.ModelViewSet):
    queryset = Libro.objects.all()
    serializer_class = LibroSerializer

class PrestamoViewSet(viewsets.ModelViewSet):
    queryset = Prestamo.objects.all()
    serializer_class = PrestamoSerializer


# ----------------------------
# API INDICADORES ECONÓMICOS
# ----------------------------
def indicadores(request):
    url = "https://mindicador.cl/api"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() 
        data = response.json()
        return JsonResponse(data)
    except RequestException as e:
        return JsonResponse({"error": f"Error de conexión con la API externa. Detalle: {e}"}, status=503)
    except json.JSONDecodeError:
        return JsonResponse({"error": "La respuesta de la API no es un JSON válido."}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Error inesperado: {e}"}, status=500)

def indicador(request, nombre):
    url = f"https://mindicador.cl/api/{nombre}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() 

        data = response.json()
        return JsonResponse(data)
    except RequestException as e:
        return JsonResponse({"error": f"No se pudo obtener el indicador o nombre inválido. Detalle: {e}"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "La respuesta de la API no es un JSON válido."}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Error inesperado: {e}"}, status=500)


# ----------------------------
# VISTAS WEB Y AUDITORÍA
# ----------------------------
def inicio_view(request):
    return render(request, "core/inicio.html")


# ----------------------------
# REGISTRO
# ----------------------------
def registro_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip()
        email = request.POST.get("email").strip()
        password = request.POST.get("password")
        tipo = request.POST.get("tipo")

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Este correo ya está registrado.")
            return redirect("registro")

        pwd_hash = bcrypt.hashpw(password.encode("latin-1"), bcrypt.gensalt())

        user = Usuario(
            nombre=nombre,
            email=email,
            password_hash=pwd_hash.decode("latin-1"),
            tipo=tipo
        )
        user.save()
        log_auditoria(user.id, 'REGISTRO', 'usuarios', f'Registro inicial de {user.nombre}')

        if tipo == "universitario":
            Universitario.objects.create(usuario=user, universidad="No asignada")
            log_auditoria(user.id, 'ACTUALIZACION', 'universitarios', 'Perfil creado como universitario')
        elif tipo == "bibliotecario":
            Bibliotecario.objects.create(usuario=user, universidad="No asignada")
            log_auditoria(user.id, 'ACTUALIZACION', 'bibliotecarios', 'Perfil creado como bibliotecario')
        else:
            Admin.objects.create(usuario=user)
            log_auditoria(user.id, 'ACTUALIZACION', 'admin', 'Perfil creado como admin') 


        messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect("login")

    return render(request, "core/registro.html")


# ----------------------------
# LOGIN
# ----------------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email").strip()
        password = request.POST.get("password").strip()
        user = None

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
            return redirect("login")

        ph = user.password_hash
        ph_bytes = ph.encode('latin-1') if isinstance(ph, str) else ph

        if not bcrypt.checkpw(password.encode('latin-1'), ph_bytes):
            log_auditoria(user.id, 'LOGIN_FALLIDO', 'usuarios', 'Contraseña incorrecta') 
            messages.error(request, "Contraseña incorrecta")
            return redirect("login")

        log_auditoria(user.id, 'LOGIN_EXITOSO', 'usuarios', f'Inicio de sesión exitoso como {user.tipo}') 
        request.session['user_id'] = user.id
        request.session['tipo'] = user.tipo

        if user.tipo == "universitario":
            return redirect("menu_universitario")
        if user.tipo == "bibliotecario":
            return redirect("menu_bibliotecario")
        return redirect("menu_admin")

    return render(request, "core/login.html")


# ----------------------------
# LOGOUT
# ----------------------------
def logout_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        log_auditoria(user_id, 'LOGOUT', 'usuarios', 'Cierre de sesión') 
    request.session.flush()
    return redirect("login")


# ----------------------------
# MENÚS
# ----------------------------
def menu_universitario(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "core/menu_universitario.html")


def menu_bibliotecario(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "core/menu_bibliotecario.html")


def menu_admin(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "core/menu_admin.html")


# ----------------------------
# LIBROS
# ----------------------------
def ver_libros(request):
    libros = Libro.objects.all()
    return render(request, "core/libros.html", {"libros": libros})


# ----------------------------
# PRESTAR LIBRO
# ----------------------------
def prestar_libro(request, libro_id):
    if not request.session.get('user_id'):
        return redirect('login')

    user = Usuario.objects.get(id=request.session['user_id'])
    
    try:
        universitario = Universitario.objects.get(usuario=user)
    except Universitario.DoesNotExist:
        messages.error(request, "Solo universitarios pueden pedir préstamos")
        return redirect("ver_libros")

    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        messages.error(request, "Libro no encontrado.")
        return redirect("ver_libros")


    if request.method == "POST":
        user_id = request.session['user_id']
        try:
            dias = int(request.POST.get("dias"))
            if dias <= 0 or dias > 14:
                raise ValueError("Días inválidos")
        except:
            messages.error(request, "Ingrese días válidos (1-14)")
            return redirect("prestar", libro_id=libro_id)

        if libro.cantidad <= 0:
            messages.error(request, "No hay copias disponibles")
            return redirect("ver_libros")

        # --- CREACIÓN DEL PRÉSTAMO CON CAMPOS DE ESTADO ---
        prestamo = Prestamo(
            universitario=universitario,
            libro=libro,
            dias=dias,
            fch_prestamo=date.today(),
            fch_devolucion=date.today() + timedelta(days=dias),
            is_activo=True,
            fch_devolucion_real=None
        )
        prestamo.save()

        # AUDITORÍA
        log_auditoria(user_id, 'PRESTAMO_CREADO', 'prestamos', f'Préstamo ID {prestamo.id} creado para Libro {libro_id}')

        # ACTUALIZACIÓN DE INVENTARIO
        libro.cantidad -= 1
        libro.save()

        messages.success(request, f"Prestado: {libro.titulo} por {dias} días")
        return redirect("ver_prestamos")

    return render(request, "core/prestar.html", {"libro": libro})


# ----------------------------
# VER PRÉSTAMOS
# ----------------------------
def ver_prestamos(request):
    if not request.session.get('user_id'):
        return redirect('login')

    user = Usuario.objects.get(id=request.session['user_id'])
    
    # Filtramos por préstamos activos
    if user.tipo == "universitario":
        try:
            uni = Universitario.objects.get(usuario=user)
            # Solo mostrar préstamos ACTVOS
            prestamos = Prestamo.objects.filter(universitario=uni, is_activo=True)
        except Universitario.DoesNotExist:
            prestamos = Prestamo.objects.none()
            
    else: # Bibliotecario y Admin ven todos los préstamos activos
        prestamos = Prestamo.objects.filter(is_activo=True)

    # Cálculo de días restantes/atraso para la plantilla (template)
    for p in prestamos:
        dias_restantes = (p.fch_devolucion - date.today()).days
        if dias_restantes < 0:
            p.estado_display = f"ATRASADO ({abs(dias_restantes)} días)"
        else:
            p.estado_display = f"{dias_restantes} días restantes"
    
    return render(request, "core/prestamos.html", {"prestamos": prestamos})


# ----------------------------
# REGISTRAR DEVOLUCIÓN
# ----------------------------
def registrar_devolucion(request, prestamo_id):
    if request.session.get('tipo') not in ["bibliotecario", "admin"]:
        messages.error(request, "Permiso denegado.")
        return redirect('ver_prestamos') 
        
    try:
        prestamo = Prestamo.objects.get(id=prestamo_id, is_activo=True)
    except Prestamo.DoesNotExist:
        messages.error(request, "Préstamo no encontrado o ya devuelto.")
        return redirect('ver_prestamos') 

    user_id = request.session['user_id']
    
    # --- PROCESO DE DEVOLUCIÓN ---
    
    # 1. Marcar el préstamo como devuelto
    prestamo.is_activo = False
    prestamo.fch_devolucion_real = date.today()
    prestamo.save()
    
    # 2. Aumentar la cantidad del libro en el inventario
    libro = prestamo.libro
    libro.cantidad += 1
    libro.save()
    
    # 3. Calcular multa (Integración de API)
    dias_retraso = (date.today() - prestamo.fch_devolucion).days
    mensaje_multa = ""

    if dias_retraso > 0:
        VALOR_UF_HOY = get_valor_uf() 
        MULTA_POR_DIA_UF = 0.01 
        multa_total_uf = dias_retraso * MULTA_POR_DIA_UF
        multa_total_clp = multa_total_uf * VALOR_UF_HOY
        
        mensaje_multa = f" **¡MULTA! {dias_retraso} días de retraso.** Total: {multa_total_uf:.2f} UF (${multa_total_clp:,.0f} CLP)"

    # 4. Auditoría
    log_auditoria(user_id, 'DEVOLUCION', 'prestamos', f'Devolución registrada de Préstamo ID {prestamo_id} por {mensaje_multa}')
    
    messages.success(request, f"Devolución exitosa para {libro.titulo}. {mensaje_multa}")
    return redirect("ver_prestamos")


# ----------------------------
# CRUD — ADMINISTRAR USUARIOS
# ----------------------------
def admin_user_list(request):
    if request.session.get('tipo') != "admin":
        return redirect("login")

    usuarios = Usuario.objects.all()
    return render(request, "core/admin_user_list.html", {"usuarios": usuarios})


def admin_user_add(request):
    if request.session.get('tipo') != "admin":
        return redirect("login")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")
        password = request.POST.get("password")
        tipo = request.POST.get("tipo")

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Ese correo ya existe.")
            return redirect("admin_user_add")

        pwd_hash = bcrypt.hashpw(password.encode("latin-1"), bcrypt.gensalt())

        user = Usuario(
            nombre=nombre,
            email=email,
            password_hash=pwd_hash.decode("latin-1"),
            tipo=tipo
        )
        user.save()
        log_auditoria(request.session['user_id'], 'ADMIN_CREAR_USUARIO', 'usuarios', f'Usuario {user.id} ({tipo}) creado por Admin')

        if tipo == "universitario":
            Universitario.objects.create(usuario=user, universidad="No asignada")
        elif tipo == "bibliotecario":
            Bibliotecario.objects.create(usuario=user, universidad="No asignada")
        else:
            Admin.objects.create(usuario=user)

        messages.success(request, "Usuario creado correctamente.")
        return redirect("admin_user_list")

    return render(request, "core/admin_user_add.html")


def admin_user_edit(request, user_id):
    if request.session.get('tipo') != "admin":
        return redirect("login")

    user = Usuario.objects.get(id=user_id)

    if request.method == "POST":
        user.nombre = request.POST.get("nombre")
        user.email = request.POST.get("email")
        user.tipo = request.POST.get("tipo")
        user.save()
        log_auditoria(request.session['user_id'], 'ADMIN_EDITAR_USUARIO', 'usuarios', f'Usuario {user_id} modificado por Admin') 

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("admin_user_list")

    return render(request, "core/admin_user_edit.html", {"user": user})


def admin_user_delete(request, user_id):
    if request.session.get('tipo') != "admin":
        return redirect("login")

    user = Usuario.objects.get(id=user_id)
    
    log_auditoria(request.session['user_id'], 'ADMIN_ELIMINAR_USUARIO', 'usuarios', f'Usuario {user_id} eliminado ({user.nombre}) por Admin')
    
    user.delete() 

    messages.success(request, "Usuario eliminado correctamente.")
    return redirect("admin_user_list")