# core/utils.py
import sqlite3
import bcrypt
from . import services

DB = "db.sqlite3"

def conectar():
    return sqlite3.connect(DB)

# ---- Autenticación y registro ----
def autenticar_usuario(email, password):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, nombre, email, password_hash, tipo FROM usuarios WHERE email = ?", (email,))
    fila = c.fetchone(); conn.close()
    if not fila:
        return None
    uid, nombre, email, password_hash, tipo = fila
    if bcrypt.checkpw(password.encode("latin-1"), password_hash):
        return {"id": uid, "nombre": nombre, "email": email, "tipo": tipo}
    return None

def registrar_usuario(nombre, email, password, tipo="usuario", universidad=None):
    # Devuelve (True, None) si ok, (False, mensaje) si falla
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "El email ya está registrado."
    try:
        if tipo == "universitario":
            u = services.Universitario(nombre, email, password, universidad)
            u.save()
        elif tipo == "bibliotecario":
            u = services.Bibliotecario(nombre, email, password, universidad)
            u.save()
        elif tipo == "admin":
            u = services.Admin(nombre, email, password)
            u.save()
        else:
            u = services.Usuario(nombre, email, password)
            u.save()
        return True, None
    except ValueError as e:
        return False, str(e)

# ---- Libros ----
def listar_libros(todos=False):
    """Si todos=False devuelve solo disponibles (cantidad>0), si True devuelve todos."""
    conn = conectar(); c = conn.cursor()
    if todos:
        c.execute("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros")
    else:
        c.execute("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE cantidad > 0")
    filas = c.fetchall(); conn.close()
    libros = []
    for r in filas:
        libros.append({
            "id": r[0], "titulo": r[1], "autor": r[2],
            "genero": r[3], "año": r[4], "cantidad": r[5], "isbn": r[6]
        })
    return libros

def get_libro_por_id(libro_id):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE id = ?", (libro_id,))
    r = c.fetchone(); conn.close()
    if not r: return None
    return {"id": r[0], "titulo": r[1], "autor": r[2], "genero": r[3], "año": r[4], "cantidad": r[5], "isbn": r[6]}

def add_libro(titulo, autor, genero, año, cantidad, isbn):
    try:
        libro = services.Libro(titulo, autor, genero, año, cantidad, isbn)
        libro.save()
        return True, None
    except ValueError as e:
        return False, str(e)

def update_libro(libro_id, titulo, autor, genero, año, cantidad, isbn):
    conn = conectar(); c = conn.cursor()
    # chequeo simple: si isbn pertenece a otro libro -> error
    c.execute("SELECT id FROM libros WHERE isbn = ? AND id != ?", (isbn, libro_id))
    if c.fetchone():
        conn.close()
        return False, "ISBN duplicado."
    try:
        c.execute("""
            UPDATE libros SET titulo = ?, autor = ?, genero = ?, año = ?, cantidad = ?, isbn = ? WHERE id = ?
        """, (titulo, autor, genero, año, cantidad, isbn, libro_id))
        conn.commit(); conn.close()
        return True, None
    except Exception as e:
        conn.close()
        return False, str(e)

def delete_libro(libro_id):
    conn = conectar(); c = conn.cursor()
    c.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
    conn.commit(); conn.close()
    return True

# ---- Préstamos ----
def pedir_prestamo(universitario_id, libro_id, dias):
    try:
        prest = services.Prestamo(universitario_id, libro_id, dias)
        prest.save()
        return True, None
    except ValueError as e:
        return False, str(e)

def listar_prestamos_usuario(universitario_id):
    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT p.id, l.titulo, l.autor, p.fch_prestamo, p.fch_devolucion
        FROM prestamos p JOIN libros l ON p.libro_id = l.id
        WHERE p.universitario_id = ?
    """, (universitario_id,))
    filas = c.fetchall(); conn.close()
    resultados = []
    from datetime import datetime, date
    for (pid, titulo, autor, f1, f2) in filas:
        # f1,f2 may be stored as ISO strings; ensure str
        try:
            fdev = str(f2)
        except:
            fdev = f2
        resultados.append({"id": pid, "titulo": titulo, "autor": autor, "fch_prestamo": f1, "fch_devolucion": fdev})
    return resultados

def listar_todos_prestamos():
    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT p.id, u.nombre, l.titulo, p.fch_prestamo, p.fch_devolucion
        FROM prestamos p
        JOIN universitarios un ON p.universitario_id = un.usuario_id
        JOIN usuarios u ON un.usuario_id = u.id
        JOIN libros l ON p.libro_id = l.id
    """)
    filas = c.fetchall(); conn.close()
    res = []
    for pid, nombre, titulo, f1, f2 in filas:
        res.append({"id": pid, "universitario": nombre, "titulo": titulo, "fch_prestamo": f1, "fch_devolucion": f2})
    return res

# ---- Usuarios (admin) ----
def listar_usuarios():
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, nombre, email, tipo FROM usuarios")
    rows = c.fetchall(); conn.close()
    return [{"id": r[0], "nombre": r[1], "email": r[2], "tipo": r[3]} for r in rows]

def get_usuario(id_usuario):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, nombre, email, tipo FROM usuarios WHERE id = ?", (id_usuario,))
    r = c.fetchone(); conn.close()
    if not r: return None
    return {"id": r[0], "nombre": r[1], "email": r[2], "tipo": r[3]}

def update_usuario(id_usuario, nombre, email, password=None):
    conn = conectar(); c = conn.cursor()
    # si cambió email a uno existente -> error
    c.execute("SELECT id FROM usuarios WHERE email = ? AND id != ?", (email, id_usuario))
    if c.fetchone():
        conn.close()
        return False, "Email duplicado."
    if password:
        ph = bcrypt.hashpw(password.encode("latin-1"), bcrypt.gensalt())
        c.execute("UPDATE usuarios SET nombre = ?, email = ?, password_hash = ? WHERE id = ?", (nombre, email, ph, id_usuario))
    else:
        c.execute("UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?", (nombre, email, id_usuario))
    conn.commit(); conn.close()
    return True, None

def delete_usuario(id_usuario):
    conn = conectar(); c = conn.cursor()
    # eliminar prestamos, relaciones y usuario
    c.execute("DELETE FROM prestamos WHERE universitario_id = ?", (id_usuario,))
    c.execute("DELETE FROM universitarios WHERE usuario_id = ?", (id_usuario,))
    c.execute("DELETE FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
    c.execute("DELETE FROM admin WHERE usuario_id = ?", (id_usuario,))
    c.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
    conn.commit(); conn.close()
    return True
