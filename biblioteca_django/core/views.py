# core/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from . import utils

# ---- AUTH ----
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        user = utils.autenticar_usuario(email, password)
        if not user:
            return render(request, "core/login.html", {"error": "Credenciales incorrectas"})
        # guardar en session
        request.session['user_id'] = user['id']
        request.session['user_nombre'] = user['nombre']
        request.session['user_tipo'] = user['tipo']
        # redirigir según tipo
        if user['tipo'] == 'admin':
            return redirect('menu_admin')
        if user['tipo'] == 'bibliotecario':
            return redirect('menu_bibliotecario')
        return redirect('menu_universitario')
    return render(request, "core/login.html")

def registro_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        tipo = request.POST.get("tipo", "usuario")
        universidad = request.POST.get("universidad", "").strip() or None
        ok, err = utils.registrar_usuario(nombre, email, password, tipo=tipo, universidad=universidad)
        if not ok:
            return render(request, "core/registro.html", {"error": err})
        return redirect('login')
    return render(request, "core/registro.html")

def logout_view(request):
    request.session.flush()
    return redirect('login')

# ---- UNIVERSITARIO ----
def menu_universitario(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "core/menu_universitario.html", {"user": {"nombre": request.session.get('user_nombre'), "tipo": request.session.get('user_tipo')}})

def uni_ver_libros(request):
    if not request.session.get('user_id'):
        return redirect('login')
    libros = utils.listar_libros(todos=False)
    return render(request, "core/uni_libros.html", {"libros": libros})

def uni_pedir_prestamo(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.method == "POST":
        libro_id = int(request.POST.get("libro_id"))
        dias = request.POST.get("dias")
        ok, err = utils.pedir_prestamo(request.session['user_id'], libro_id, dias)
        if not ok:
            libros = utils.listar_libros(False)
            return render(request, "core/uni_libros.html", {"libros": libros, "error": err})
        return redirect('uni_mis_prestamos')
    return redirect('uni_libros')

def uni_mis_prestamos(request):
    if not request.session.get('user_id'):
        return redirect('login')
    prestamos = utils.listar_prestamos_usuario(request.session['user_id'])
    return render(request, "core/uni_prestamos.html", {"prestamos": prestamos})

# ---- BIBLIOTECARIO ----
def menu_bibliotecario(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "core/menu_bibliotecario.html", {"user": {"nombre": request.session.get('user_nombre'), "tipo": request.session.get('user_tipo')}})

def lib_listar_libros(request):
    if not request.session.get('user_id'):
        return redirect('login')
    libros = utils.listar_libros(todos=True)
    return render(request, "core/lib_libros.html", {"libros": libros})

def lib_agregar_libro(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.method == "POST":
        titulo = request.POST.get("titulo","").strip()
        autor = request.POST.get("autor","").strip()
        genero = request.POST.get("genero","").strip()
        año = request.POST.get("año","").strip()
        cantidad = request.POST.get("cantidad","").strip()
        isbn = request.POST.get("isbn","").strip()
        ok, err = utils.add_libro(titulo, autor, genero, año, cantidad, isbn)
        if not ok:
            return render(request, "core/lib_add_edit.html", {"error": err})
        return redirect('lib_listar_libros')
    return render(request, "core/lib_add_edit.html")

def lib_editar_libro(request, libro_id):
    if not request.session.get('user_id'):
        return redirect('login')
    libro = utils.get_libro_por_id(libro_id)
    if not libro:
        return redirect('lib_listar_libros')
    if request.method == "POST":
        titulo = request.POST.get("titulo","").strip()
        autor = request.POST.get("autor","").strip()
        genero = request.POST.get("genero","").strip()
        año = request.POST.get("año","").strip()
        cantidad = request.POST.get("cantidad","").strip()
        isbn = request.POST.get("isbn","").strip()
        ok, err = utils.update_libro(libro_id, titulo, autor, genero, año, cantidad, isbn)
        if not ok:
            libro = utils.get_libro_por_id(libro_id)
            return render(request, "core/lib_add_edit.html", {"libro": libro, "error": err})
        return redirect('lib_listar_libros')
    return render(request, "core/lib_add_edit.html", {"libro": libro})

def lib_eliminar_libro(request, libro_id):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.method == "POST":
        utils.delete_libro(libro_id)
    return redirect('lib_listar_libros')

def lib_ver_prestamos(request):
    if not request.session.get('user_id'):
        return redirect('login')
    prestamos = utils.listar_todos_prestamos()
    return render(request, "core/lib_prestamos.html", {"prestamos": prestamos})

# ---- ADMIN ----
def menu_admin(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, "core/menu_admin.html", {"user": {"nombre": request.session.get('user_nombre'), "tipo": request.session.get('user_tipo')}})

def admin_listar_usuarios(request):
    if not request.session.get('user_id'):
        return redirect('login')
    usuarios = utils.listar_usuarios()
    return render(request, "core/admin_usuarios.html", {"usuarios": usuarios})

def admin_editar_usuario(request, usuario_id):
    if not request.session.get('user_id'):
        return redirect('login')
    usuario = utils.get_usuario(usuario_id)
    if not usuario:
        return redirect('admin_usuarios')
    if request.method == "POST":
        nombre = request.POST.get("nombre","").strip()
        email = request.POST.get("email","").strip()
        password = request.POST.get("password","").strip()
        password = password if password else None
        ok, err = utils.update_usuario(usuario_id, nombre, email, password)
        if not ok:
            return render(request, "core/admin_edit_user.html", {"usuario": usuario, "error": err})
        return redirect('admin_usuarios')
    return render(request, "core/admin_edit_user.html", {"usuario": usuario})

def admin_eliminar_usuario(request, usuario_id):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.method == "POST":
        utils.delete_usuario(usuario_id)
    return redirect('admin_usuarios')
