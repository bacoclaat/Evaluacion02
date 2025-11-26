from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date, timedelta
import bcrypt

from .models import Usuario, Universitario, Bibliotecario, Admin, Libro, Prestamo


# ----------------------------
# PÁGINA DE INICIO
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

        if tipo == "universitario":
            Universitario.objects.create(usuario=user, universidad="No asignada")
        elif tipo == "bibliotecario":
            Bibliotecario.objects.create(usuario=user, universidad="No asignada")
        else:
            Admin.objects.create(usuario=user)

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

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
            return redirect("login")

        ph = user.password_hash
        ph_bytes = ph.encode('latin-1') if isinstance(ph, str) else ph

        if not bcrypt.checkpw(password.encode('latin-1'), ph_bytes):
            messages.error(request, "Contraseña incorrecta")
            return redirect("login")

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

    libro = Libro.objects.get(id=libro_id)

    if request.method == "POST":
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

        prestamo = Prestamo(
            universitario=universitario,
            libro=libro,
            dias=dias,
            fch_prestamo=date.today(),
            fch_devolucion=date.today() + timedelta(days=dias)
        )
        prestamo.save()

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

    if user.tipo == "universitario":
        uni = Universitario.objects.get(usuario=user)
        prestamos = Prestamo.objects.filter(universitario=uni)
    else:
        prestamos = Prestamo.objects.all()

    return render(request, "core/prestamos.html", {"prestamos": prestamos})


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

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("admin_user_list")

    return render(request, "core/admin_user_edit.html", {"user": user})


def admin_user_delete(request, user_id):
    if request.session.get('tipo') != "admin":
        return redirect("login")

    user = Usuario.objects.get(id=user_id)
    user.delete()

    messages.success(request, "Usuario eliminado correctamente.")
    return redirect("admin_user_list")
