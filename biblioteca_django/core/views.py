import sqlite3
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages

DB_PATH = "biblioteca.db"


def get_conn():
    return sqlite3.connect(DB_PATH)

def fetchone(query, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query, params)
    row = c.fetchone()
    conn.close()
    return row

def fetchall(query, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def execute(query, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last = c.lastrowid
    conn.close()
    return last


def require_login(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    wrapped.__name__ = view_func.__name__
    return wrapped


# LOGIN
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        row = fetchone("SELECT id, nombre, password_hash, tipo FROM usuarios WHERE email = ?", (email,))
        if not row:
            messages.error(request, "Usuario no encontrado.")
            return render(request, "core/login.html")

        user_id, nombre, password_hash, tipo = row

        if password != password_hash:
            messages.error(request, "Contraseña incorrecta.")
            return render(request, "core/login.html")

        request.session["user_id"] = user_id
        request.session["user_tipo"] = tipo
        request.session["user_nombre"] = nombre

        if tipo == "admin":
            return redirect("/django-admin/")   # << IR AL PANEL DJANGO ADMIN

        if tipo == "universitario":
            return redirect("uni_menu")

        if tipo == "bibliotecario":
            return redirect("biblio_menu")

        messages.error(request, "Tipo de usuario desconocido.")
        return render(request, "core/login.html")

    return render(request, "core/login.html")


# LOGOUT
def logout_view(request):
    request.session.flush()
    return redirect("login")


# REGISTRO
def register_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        tipo = request.POST.get("tipo", "universitario").strip()
        universidad = request.POST.get("universidad", "").strip()

        if tipo == "admin":
            tipo = "universitario"

        if not nombre or not email or not password:
            return render(request, "core/register.html", {"error": "Completa todos los campos."})

        if fetchone("SELECT id FROM usuarios WHERE email = ?", (email,)):
            return render(request, "core/register.html", {"error": "Email ya registrado."})

        uid = execute(
            "INSERT INTO usuarios (nombre, email, password_hash, tipo) VALUES (?, ?, ?, ?)",
            (nombre, email, password, tipo)
        )

        if tipo == "universitario":
            execute("INSERT INTO universitarios (usuario_id, universidad) VALUES (?, ?)", (uid, universidad))

        elif tipo == "bibliotecario":
            execute("INSERT INTO bibliotecarios (usuario_id, universidad) VALUES (?, ?)", (uid, universidad))

        return redirect("login")

    return render(request, "core/register.html")


# MENÚS
@require_login
def uni_menu(request):
    return render(request, "core/uni_menu.html")

@require_login
def biblio_menu(request):
    return render(request, "core/biblio_menu.html")


# LISTA DE LIBROS
@require_login
def libros_lista(request):
    tipo = request.session.get("user_tipo")

    if tipo == "universitario":
        rows = fetchall("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE cantidad > 0")
    else:
        rows = fetchall("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros")

    libros = [
        {"id": r[0], "titulo": r[1], "autor": r[2], "genero": r[3],
         "año": r[4], "cantidad": r[5], "isbn": r[6]}
        for r in rows
    ]

    return render(request, "core/libros_lista.html", {
        "libros": libros,
        "bibliotecario": tipo == "bibliotecario",
        "universitario": tipo == "universitario"
    })



# AGREGAR LIBRO
@require_login
def libro_add(request):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        autor = request.POST.get("autor", "").strip()
        genero = request.POST.get("genero", "").strip()
        año = int(request.POST.get("año", 0))
        cantidad = int(request.POST.get("cantidad", 0))
        isbn = request.POST.get("isbn", "").strip()

        try:
            execute(
                "INSERT INTO libros (titulo, autor, genero, año, cantidad, isbn) VALUES (?, ?, ?, ?, ?, ?)",
                (titulo, autor, genero, año, cantidad, isbn)
            )
            return redirect("libros_lista")
        except sqlite3.IntegrityError:
            return render(request, "core/libro_form.html",
                          {"error": "ISBN duplicado", "form": request.POST})

    return render(request, "core/libro_form.html")



# EDITAR LIBRO
@require_login
def libro_edit(request, libro_id):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")

    row = fetchone("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE id = ?",
                   (libro_id,))
    if not row:
        return HttpResponse("Libro no encontrado", status=404)

    libro = {
        "id": row[0], "titulo": row[1], "autor": row[2], "genero": row[3],
        "año": row[4], "cantidad": row[5], "isbn": row[6]
    }

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        autor = request.POST.get("autor", "").strip()
        genero = request.POST.get("genero", "").strip()
        año = int(request.POST.get("año", libro["año"]))
        cantidad = int(request.POST.get("cantidad", libro["cantidad"]))
        isbn = request.POST.get("isbn", "").strip()

        try:
            execute(
                "UPDATE libros SET titulo=?, autor=?, genero=?, año=?, cantidad=?, isbn=? WHERE id = ?",
                (titulo, autor, genero, año, cantidad, isbn, libro_id)
            )
            return redirect("libros_lista")
        except sqlite3.IntegrityError:
            return render(request, "core/libro_form.html",
                          {"error": "ISBN duplicado", "form": request.POST, "libro": libro})

    return render(request, "core/libro_form.html", {"libro": libro})



# ELIMINAR LIBRO
@require_login
def libro_delete(request, libro_id):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")

    row = fetchone("SELECT id, titulo FROM libros WHERE id = ?", (libro_id,))
    if not row:
        return HttpResponse("Libro no encontrado", status=404)

    libro = {"id": row[0], "titulo": row[1]}

    if request.method == "POST":
        execute("DELETE FROM libros WHERE id = ?", (libro_id,))
        return redirect("libros_lista")

    return render(request, "core/libro_confirm_delete.html", {"libro": libro})



# PEDIR PRÉSTAMO
@require_login
def pedir_prestamo(request, libro_id):
    if request.session.get("user_tipo") != "universitario":
        return HttpResponseForbidden("Solo universitarios pueden pedir préstamos.")

    uid = request.session.get("user_id")

    row_uni = fetchone("SELECT usuario_id FROM universitarios WHERE usuario_id = ?", (uid,))
    if not row_uni:
        return HttpResponse("Perfil universitario no encontrado", status=400)

    row = fetchone("SELECT id, titulo, cantidad FROM libros WHERE id = ?", (libro_id,))
    if not row:
        return HttpResponse("Libro no encontrado.", status=404)

    libro = {"id": row[0], "titulo": row[1], "cantidad": row[2]}

    if request.method == "POST":
        dias_str = request.POST.get("dias", "")
        try:
            dias = int(dias_str)
        except:
            return render(request, "core/pedir_prestamo.html",
                          {"libro": libro, "error": "Días inválidos"})

        if dias <= 0 or dias > 14:
            return render(request, "core/pedir_prestamo.html",
                          {"libro": libro, "error": "El préstamo debe ser entre 1 y 14 días"})

        fch_p = date.today()
        fch_d = fch_p + timedelta(days=dias)

        execute(
            "INSERT INTO prestamos (universitario_id, libro_id, dias, fch_prestamo, fch_devolucion)"
            " VALUES (?, ?, ?, ?, ?)",
            (uid, libro_id, dias, fch_p.isoformat(), fch_d.isoformat())
        )

        execute("UPDATE libros SET cantidad = cantidad - 1 WHERE id = ?", (libro_id,))

        return redirect("uni_mis_prestamos")

    return render(request, "core/pedir_prestamo.html", {"libro": libro})



# MIS PRÉSTAMOS
@require_login
def uni_mis_prestamos(request):
    uid = request.session.get("user_id")

    rows = fetchall("""
        SELECT prestamos.id, libros.titulo, prestamos.dias,
               prestamos.fch_prestamo, prestamos.fch_devolucion
        FROM prestamos
        JOIN libros ON prestamos.libro_id = libros.id
        WHERE prestamos.universitario_id = ?
    """, (uid,))

    prestamos = [
        {"id": r[0], "libro": r[1], "dias": r[2], "fch_prestamo": r[3], "fch_devolucion": r[4]}
        for r in rows
    ]

    return render(request, "core/mis_prestamos.html", {"prestamos": prestamos})



# VER PRÉSTAMOS (bibliotecario)
@require_login
def biblio_ver_prestamos(request):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")

    rows = fetchall("""
        SELECT prestamos.id, usuarios.nombre, libros.titulo,
               prestamos.fch_prestamo, prestamos.fch_devolucion
        FROM prestamos
        JOIN universitarios ON prestamos.universitario_id = universitarios.usuario_id
        JOIN usuarios ON universitarios.usuario_id = usuarios.id
        JOIN libros ON prestamos.libro_id = libros.id
        ORDER BY prestamos.id DESC
    """)

    prestamos = [
        {"id": r[0], "usuario": r[1], "libro": r[2],
         "fch_prestamo": r[3], "fch_devolucion": r[4]}
        for r in rows
    ]

    return render(request, "core/ver_prestamos.html", {"prestamos": prestamos})



# ADMIN — LISTAR USUARIOS
@require_login
def admin_listar_usuarios(request):
    if request.session.get("user_tipo") != "admin":
        return HttpResponseForbidden("No autorizado")

    rows = fetchall("SELECT id, nombre, email, tipo FROM usuarios")

    usuarios = [
        {"id": r[0], "nombre": r[1], "email": r[2], "tipo": r[3]}
        for r in rows
    ]

    return render(request, "core/admin_usuarios.html", {"usuarios": usuarios})



# ADMIN — EDITAR USUARIO
@require_login
def admin_editar_usuario(request, usuario_id):
    if request.session.get("user_tipo") != "admin":
        return HttpResponseForbidden("No autorizado")

    row = fetchone("SELECT id, nombre, email, tipo FROM usuarios WHERE id = ?", (usuario_id,))
    if not row:
        return HttpResponse("Usuario no encontrado", status=404)

    usuario = {"id": row[0], "nombre": row[1], "email": row[2], "tipo": row[3]}

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        newpass = request.POST.get("password", "").strip()

        if newpass:
            password_hash = newpass
        else:
            row_old = fetchone("SELECT password_hash FROM usuarios WHERE id = ?", (usuario_id,))
            password_hash = row_old[0]

        execute(
            "UPDATE usuarios SET nombre=?, email=?, password_hash=? WHERE id=?",
            (nombre, email, password_hash, usuario_id)
        )

        if usuario["tipo"] in ("universitario", "bibliotecario"):
            universidad = request.POST.get("universidad", "").strip()
            if universidad:
                table = "universitarios" if usuario["tipo"] == "universitario" else "bibliotecarios"
                execute(f"UPDATE {table} SET universidad=? WHERE usuario_id=?", (universidad, usuario_id))

        return redirect("admin_listar_usuarios")

    universidad = ""
    if usuario["tipo"] in ("universitario", "bibliotecario"):
        table = "universitarios" if usuario["tipo"] == "universitario" else "bibliotecarios"
        rowu = fetchone(f"SELECT universidad FROM {table} WHERE usuario_id=?", (usuario_id,))
        universidad = rowu[0] if rowu else ""

    return render(request, "core/admin_user_form.html", {
        "usuario": usuario,
        "universidad": universidad
    })



# ADMIN — ELIMINAR USUARIO
@require_login
def admin_eliminar_usuario(request, usuario_id):
    if request.session.get("user_tipo") != "admin":
        return HttpResponseForbidden("No autorizado")

    row = fetchone("SELECT id, nombre, tipo FROM usuarios WHERE id=?", (usuario_id,))
    if not row:
        return HttpResponse("Usuario no encontrado", status=404)

    if request.method == "POST":
        _, _, tipo = row

        if tipo == "universitario":
            execute("DELETE FROM prestamos WHERE universitario_id=?", (usuario_id,))
            execute("DELETE FROM universitarios WHERE usuario_id=?", (usuario_id,))

        elif tipo == "bibliotecario":
            execute("DELETE FROM bibliotecarios WHERE usuario_id=?", (usuario_id,))

        execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
        return redirect("admin_listar_usuarios")

    usuario = {"id": row[0], "nombre": row[1]}

    return render(request, "core/admin_user_confirm_delete.html", {"usuario": usuario})
