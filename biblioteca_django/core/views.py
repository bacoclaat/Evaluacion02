from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date, timedelta
import bcrypt

from .models import Usuario, Universitario, Bibliotecario, Admin, Libro, Prestamo

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email").strip()
        password = request.POST.get("password").strip()
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
            return redirect("login")

        # password_hash puede ser str o bytes dependiente de cómo se guardó en sqlite
        ph = user.password_hash
        if isinstance(ph, str):
            ph_bytes = ph.encode('latin-1', errors='ignore')
        else:
            ph_bytes = ph

        if not bcrypt.checkpw(password.encode('latin-1'), ph_bytes):
            messages.error(request, "Contraseña incorrecta")
            return redirect("login")

        # setear sesión
        request.session['user_id'] = user.id
        request.session['tipo'] = user.tipo
        if user.tipo == "universitario":
            return redirect("menu_universitario")
        if user.tipo == "bibliotecario":
            return redirect("menu_bibliotecario")
        return redirect("menu_admin")
    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    return redirect("login")

def menu_universitario(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "menu_universitario.html")

def menu_bibliotecario(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "menu_bibliotecario.html")

def menu_admin(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "menu_admin.html")

def ver_libros(request):
    libros = Libro.objects.all()
    return render(request, "libros.html", {"libros": libros})

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
        except Exception:
            messages.error(request, "Ingrese días válidos (1-14)")
            return redirect("prestar", libro_id=libro_id)

        # comprobar disponibilidad
        if libro.cantidad <= 0:
            messages.error(request, "No hay copias disponibles")
            return redirect("ver_libros")

        # crear préstamo
        prestamo = Prestamo(
            universitario=universitario,
            libro=libro,
            dias=dias,
            fch_prestamo=date.today(),
            fch_devolucion=date.today() + timedelta(days=dias)
        )
        prestamo.save()

        # actualizar stock (como las tablas son managed=False, .save() en Libro hace UPDATE)
        libro.cantidad = libro.cantidad - 1
        libro.save()
        messages.success(request, f"Prestado: {libro.titulo} por {dias} días")
        return redirect("ver_prestamos")
    return render(request, "prestar.html", {"libro": libro})

def ver_prestamos(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user = Usuario.objects.get(id=request.session['user_id'])
    if user.tipo == "universitario":
        uni = Universitario.objects.get(usuario=user)
        prestamos = Prestamo.objects.filter(universitario=uni)
    else:
        prestamos = Prestamo.objects.all()
    return render(request, "prestamos.html", {"prestamos": prestamos})
