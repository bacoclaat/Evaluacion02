# core/views.py
import sqlite3
import bcrypt
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Path a la DB: si en settings apuntaste a BASE_DIR/'biblioteca.db' entonces usar mismo nombre
DB_PATH = "biblioteca.db"

# -----------------------
# Helpers DB
# -----------------------
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

# -----------------------
# AUTH (login / register)
# -----------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email","").strip()
        password = request.POST.get("password","").strip()
        if not email or not password:
            return render(request, "core/login.html", {"error":"Email y contraseña requeridos."})

        row = fetchone("SELECT id, nombre, email, password_hash, tipo FROM usuarios WHERE email = ?", (email,))
        if not row:
            return render(request, "core/login.html", {"error":"Credenciales incorrectas."})
        uid, nombre, email_db, password_hash, tipo = row

        # password_hash puede ser bytes o str
        try:
            # If stored as bytes, python sqlite returns bytes; else string
            stored = password_hash
            if isinstance(stored, str):
                stored_bytes = stored.encode('latin-1', errors='ignore')
            else:
                stored_bytes = stored
            ok = bcrypt.checkpw(password.encode('latin-1'), stored_bytes)
        except Exception:
            ok = False

        if not ok:
            return render(request, "core/login.html", {"error":"Credenciales incorrectas."})

        # set session
        request.session['user_id'] = uid
        request.session['user_nombre'] = nombre
        request.session['user_tipo'] = tipo

        # redirect by role
        if tipo == "admin":
            return redirect("/admin/")   # manda al admin de Django
        if tipo == "bibliotecario":
            return redirect("biblio_menu")
        if tipo == "universitario":
            return redirect("uni_menu")
        return redirect("uni_menu")

    return render(request, "core/login.html")

def logout_view(request):
    request.session.flush()
    return redirect("login")

def register_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre","").strip()
        email = request.POST.get("email","").strip()
        password = request.POST.get("password","").strip()
        tipo = request.POST.get("tipo","universitario").strip()
        universidad = request.POST.get("universidad","").strip()

        # Basic validation (re-use your patterns if you want)
        if not nombre or not email or not password:
            return render(request, "core/registro.html", {"error":"Completa todos los campos."})

        # check unique
        if fetchone("SELECT id FROM usuarios WHERE email = ?", (email,)):
            return render(request, "core/registro.html", {"error":"Email ya registrado."})

        # hash password
        try:
            ph = bcrypt.hashpw(password.encode('latin-1'), bcrypt.gensalt())
        except Exception:
            # fallback to utf-8 if latin-1 fails
            ph = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # insert user
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO usuarios (nombre, email, password_hash, tipo) VALUES (?, ?, ?, ?)", (nombre, email, ph, tipo))
        uid = c.lastrowid

        # perfiles
        if tipo == "bibliotecario":
            c.execute("INSERT INTO bibliotecarios (usuario_id, universidad) VALUES (?, ?)", (uid, universidad))
        elif tipo == "universitario":
            c.execute("INSERT INTO universitarios (usuario_id, universidad) VALUES (?, ?)", (uid, universidad))
        elif tipo == "admin":
            c.execute("INSERT INTO admin (usuario_id) VALUES (?)", (uid,))

        conn.commit()
        conn.close()

        return redirect("login")

    return render(request, "core/registro.html")


# -----------------------
# Decorator simple require_login
# -----------------------
def require_login(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.session.get("user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    wrapped.__name__ = view_func.__name__
    return wrapped

# -----------------------
# Dashboards
# -----------------------
@require_login
def uni_menu(request):
    return render(request, "core/uni_menu.html")

@require_login
def biblio_menu(request):
    return render(request, "core/biblio_menu.html")

@require_login
def admin_menu(request):
    return render(request, "core/admin_menu.html")

# -----------------------
# Libros (list / add / edit / delete)
# -----------------------
@require_login
def libros_lista(request):
    # show all books (bibliotecario) or available books (universitario) depending on role
    tipo = request.session.get("user_tipo")
    if tipo == "universitario":
        rows = fetchall("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE cantidad > 0")
    else:
        rows = fetchall("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros")
    libros = [{"id":r[0],"titulo":r[1],"autor":r[2],"genero":r[3],"año":r[4],"cantidad":r[5],"isbn":r[6]} for r in rows]
    return render(request, "core/libros_lista.html", {"libros":libros, "bibliotecario": tipo=="bibliotecario", "universitario": tipo=="universitario"})

@require_login
def libro_add(request):
    # only bibliotecario
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")
    if request.method == "POST":
        titulo = request.POST.get("titulo","").strip()
        autor = request.POST.get("autor","").strip()
        genero = request.POST.get("genero","").strip()
        año = request.POST.get("año","").strip()
        cantidad = request.POST.get("cantidad","").strip()
        isbn = request.POST.get("isbn","").strip()
        # basic validation
        try:
            año_i = int(año)
            cantidad_i = int(cantidad)
        except:
            return render(request, "core/libro_form.html", {"error":"Año y cantidad deben ser números.", "form":request.POST})
        try:
            execute("INSERT INTO libros (titulo, autor, genero, año, cantidad, isbn) VALUES (?, ?, ?, ?, ?, ?)",
                    (titulo, autor, genero, año_i, cantidad_i, isbn))
            return redirect("libros_lista")
        except sqlite3.IntegrityError:
            return render(request, "core/libro_form.html", {"error":"ISBN duplicado.", "form":request.POST})
    return render(request, "core/libro_form.html")

@require_login
def libro_edit(request, libro_id):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")
    row = fetchone("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE id = ?", (libro_id,))
    if not row:
        return HttpResponse("Libro no encontrado", status=404)
    libro = {"id":row[0],"titulo":row[1],"autor":row[2],"genero":row[3],"año":row[4],"cantidad":row[5],"isbn":row[6]}
    if request.method == "POST":
        titulo = request.POST.get("titulo","").strip()
        autor = request.POST.get("autor","").strip()
        genero = request.POST.get("genero","").strip()
        año = int(request.POST.get("año","").strip() or libro["año"])
        cantidad = int(request.POST.get("cantidad","").strip() or libro["cantidad"])
        isbn = request.POST.get("isbn","").strip()
        try:
            execute("UPDATE libros SET titulo=?, autor=?, genero=?, año=?, cantidad=?, isbn=? WHERE id = ?",
                    (titulo, autor, genero, año, cantidad, isbn, libro_id))
            return redirect("libros_lista")
        except sqlite3.IntegrityError:
            return render(request, "core/libro_form.html", {"error":"ISBN duplicado.", "form":request.POST, "libro":libro})
    return render(request, "core/libro_form.html", {"libro":libro})

@require_login
def libro_delete(request, libro_id):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")
    row = fetchone("SELECT id, titulo FROM libros WHERE id = ?", (libro_id,))
    if not row:
        return HttpResponse("Libro no encontrado", status=404)
    libro = {"id":row[0],"titulo":row[1]}
    if request.method == "POST":
        execute("DELETE FROM libros WHERE id = ?", (libro_id,))
        return redirect("libros_lista")
    return render(request, "core/libro_confirm_delete.html", {"libro":libro})

# -----------------------
# Prestamos
# -----------------------
@require_login
def pedir_prestamo(request, libro_id):
    # only universitario
    if request.session.get("user_tipo") != "universitario":
        return HttpResponseForbidden("Solo universitarios pueden pedir préstamos.")
    uid = request.session.get("user_id")
    # need universitario profile id mapping
    uni_row = fetchone("SELECT usuario_id, universidad FROM universitarios WHERE usuario_id = ?", (uid,))
    if not uni_row:
        return HttpResponse("Perfil universitario no encontrado.", status=400)
    # get libro
    row = fetchone("SELECT id, titulo, cantidad FROM libros WHERE id = ?", (libro_id,))
    if not row:
        return HttpResponse("Libro no encontrado.", status=404)
    libro = {"id":row[0],"titulo":row[1],"cantidad":row[2]}

    if request.method == "POST":
        dias_str = request.POST.get("dias","").strip()
        try:
            dias = int(dias_str)
        except:
            return render(request, "core/pedir_prestamo.html", {"libro":libro, "error":"Días inválidos"})
        if dias <= 0 or dias > 14:
            return render(request, "core/pedir_prestamo.html", {"libro":libro, "error":"Días debe estar entre 1 y 14"})
        if libro["cantidad"] <= 0:
            return render(request, "core/pedir_prestamo.html", {"libro":libro, "error":"No hay copias disponibles"})
        # insert prestamo and decrement
        fch_p = date.today()
        fch_d = fch_p + timedelta(days=dias)
        execute("INSERT INTO prestamos (universitario_id, libro_id, dias, fch_prestamo, fch_devolucion) VALUES (?, ?, ?, ?, ?)",
                (uid, libro_id, dias, fch_p.isoformat(), fch_d.isoformat()))
        execute("UPDATE libros SET cantidad = cantidad - 1 WHERE id = ?", (libro_id,))
        return redirect("uni_mis_prestamos")
    return render(request, "core/pedir_prestamo.html", {"libro":libro})

@require_login
def uni_mis_prestamos(request):
    if request.session.get("user_type") == "bibliotecario":
        return HttpResponseForbidden("No autorizado")
    uid = request.session.get("user_id")
    rows = fetchall("""
        SELECT prestamos.id, libros.titulo, prestamos.dias, prestamos.fch_prestamo, prestamos.fch_devolucion
        FROM prestamos
        JOIN libros ON prestamos.libro_id = libros.id
        WHERE prestamos.universitario_id = ?
    """, (uid,))
    prestamos = [{"id":r[0],"libro":r[1],"dias":r[2],"fch_prestamo":r[3],"fch_devolucion":r[4]} for r in rows]
    return render(request, "core/mis_prestamos.html", {"prestamos":prestamos})

@require_login
def biblio_ver_prestamos(request):
    if request.session.get("user_tipo") != "bibliotecario":
        return HttpResponseForbidden("No autorizado")
    rows = fetchall("""
        SELECT prestamos.id, usuarios.nombre, libros.titulo, prestamos.fch_prestamo, prestamos.fch_devolucion, prestamos.libro_id
        FROM prestamos
        JOIN universitarios ON prestamos.universitario_id = universitarios.usuario_id
        JOIN usuarios ON universitarios.usuario_id = usuarios.id
        JOIN libros ON prestamos.libro_id = libros.id
        ORDER BY prestamos.id DESC
    """)
    prestamos = [{"id":r[0],"usuario":r[1],"libro":r[2],"fch_prestamo":r[3],"fch_devolucion":r[4],"libro_id":r[5]} for r in rows]
    return render(request, "core/ver_prestamos.html", {"prestamos":prestamos})

# -----------------------
# Admin usuarios (list / edit / delete)
# -----------------------
@require_login
def admin_listar_usuarios(request):
    if request.session.get("user_tipo") != "admin":
        return HttpResponseForbidden("No autorizado")
    rows = fetchall("SELECT id, nombre, email, tipo FROM usuarios")
    usuarios = [{"id":r[0],"nombre":r[1],"email":r[2],"tipo":r[3]} for r in rows]
    return render(request, "core/admin_usuarios.html", {"usuarios":usuarios})

@require_login
def admin_editar_usuario(request, usuario_id):
    if request.session.get("user_tipo") != "admin":
        return HttpResponseForbidden("No autorizado")
    row = fetchone("SELECT id, nombre, email, tipo FROM usuarios WHERE id = ?", (usuario_id,))
    if not row:
        return HttpResponse("Usuario no encontrado", status=404)
    usuario = {"id":row[0],"nombre":row[1],"email":row[2],"tipo":row[3]}
    if request.method == "POST":
        nombre = request.POST.get("nombre","").strip()
        email = request.POST.get("email","").strip()
        newpass = request.POST.get("password","").strip()
        if newpass:
            ph = bcrypt.hashpw(newpass.encode('latin-1'), bcrypt.gensalt())
        else:
            # keep existing hash
            row2 = fetchone("SELECT password_hash FROM usuarios WHERE id = ?", (usuario_id,))
            ph = row2[0]
        execute("UPDATE usuarios SET nombre = ?, email = ?, password_hash = ? WHERE id = ?", (nombre, email, ph, usuario_id))
        # update possible profile tables if present
        tipo = usuario["tipo"]
        if tipo == "universitario":
            universidad = request.POST.get("universidad","").strip()
            if universidad:
                execute("UPDATE universitarios SET universidad = ? WHERE usuario_id = ?", (universidad, usuario_id))
        elif tipo == "bibliotecario":
            universidad = request.POST.get("universidad","").strip()
            if universidad:
                execute("UPDATE bibliotecarios SET universidad = ? WHERE usuario_id = ?", (universidad, usuario_id))
        return redirect("admin_listar_usuarios")
    # try fetch universidad if exists
    universidad = None
    if usuario["tipo"] == "universitario":
        rowu = fetchone("SELECT universidad FROM universitarios WHERE usuario_id = ?", (usuario_id,))
        universidad = rowu[0] if rowu else ""
    elif usuario["tipo"] == "bibliotecario":
        rowb = fetchone("SELECT universidad FROM bibliotecarios WHERE usuario_id = ?", (usuario_id,))
        universidad = rowb[0] if rowb else ""
    return render(request, "core/admin_user_form.html", {"usuario":usuario, "universidad":universidad})

@require_login
def admin_eliminar_usuario(request, usuario_id):
    if request.session.get("user_tipo") != "admin":
        return HttpResponseForbidden("No autorizado")
    row = fetchone("SELECT id, nombre FROM usuarios WHERE id = ?", (usuario_id,))
    if not row:
        return HttpResponse("Usuario no encontrado", status=404)
    if request.method == "POST":
        # if universitario delete prestamos first
        rowt = fetchone("SELECT tipo FROM usuarios WHERE id = ?", (usuario_id,))
        tipo = rowt[0] if rowt else None
        if tipo == "universitario":
            execute("DELETE FROM prestamos WHERE universitario_id = ?", (usuario_id,))
            execute("DELETE FROM universitarios WHERE usuario_id = ?", (usuario_id,))
        elif tipo == "bibliotecario":
            execute("DELETE FROM bibliotecarios WHERE usuario_id = ?", (usuario_id,))
        execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        return redirect("admin_listar_usuarios")
    usuario = {"id":row[0],"nombre":row[1]}
    return render(request, "core/admin_user_confirm_delete.html", {"usuario":usuario})
