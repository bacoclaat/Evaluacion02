from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from init_db import init_db
from flask import jsonify

app = Flask(__name__)
app.secret_key = "FZ_SUPER_SECRET_KEY_2025"   # Requerido para sesiones

# -------- FUNCIÓN: CONEXIÓN A SQLITE --------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    # Activar claves foráneas en SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# -------- VALIDACIONES --------
def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validar_password(password):
    return len(password) >= 6

# -------- RUTA RAÍZ --------
@app.route("/")
def root():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["nombre"]
            print("✔ LOGIN:", email)
            return redirect(url_for("dashboard"))

        error = "Correo o contraseña incorrectos"
    return render_template("login.html", error=error)

# -------- REGISTRO --------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not nombre or not email or not password or not confirm_password:
            error = "Todos los campos son obligatorios"
        elif not validar_email(email):
            error = "Correo inválido"
        elif not validar_password(password):
            error = "La contraseña debe tener al menos 6 caracteres"
        elif password != confirm_password:
            error = "Las contraseñas no coinciden"
        else:
            conn = get_db()
            try:
                password_hash = generate_password_hash(password)
                conn.execute(
                    "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
                    (nombre, email, password_hash)
                )
                conn.commit()
                conn.close()
                print("✔ Usuario registrado:", email)
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "Este correo ya está registrado."

    return render_template("register.html", error=error)

# -------- PANEL PRINCIPAL (PROTEGIDO) --------
@app.route("/finanzas")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("Finanzza.html", usuario=session.get("user_name"))

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------- MANEJO DE ERRORES --------
@app.errorhandler(500)
def server_error(e):
    # Renderiza una plantilla de error amigable
    return render_template("error.html", mensaje="Ocurrió un problema en el servidor. Intenta nuevamente."), 500

# -------- PERFIL DE USUARIO --------
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "user_id" not in session:
        return redirect(url_for("login"))

    error = None
    success = None

    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")

        if not nombre or not email:
            error = "Todos los campos son obligatorios"
        elif not validar_email(email):
            error = "Correo inválido"
        else:
            try:
                conn.execute(
                    "UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?",
                    (nombre, email, session["user_id"])
                )
                conn.commit()
                success = "Perfil actualizado correctamente"
                session["user_name"] = nombre  # actualizar sesión
            except sqlite3.IntegrityError:
                error = "Este correo ya está registrado por otro usuario"

    conn.close()
    return render_template("perfil.html", usuario=user, error=error, success=success)

# -------- CAMBIAR CONTRASEÑA --------
@app.route("/perfil/cambiar-password", methods=["POST"])
def cambiar_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    error = None
    success = None

    actual = request.form.get("actual_password")
    nueva = request.form.get("new_password")
    confirmar = request.form.get("confirm_password")

    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (session["user_id"],)).fetchone()

    if not actual or not nueva or not confirmar:
        error = "Todos los campos son obligatorios"
    elif not check_password_hash(user["password"], actual):
        error = "La contraseña actual es incorrecta"
    elif nueva != confirmar:
        error = "Las contraseñas nuevas no coinciden"
    elif not validar_password(nueva):
        error = "La nueva contraseña debe tener al menos 6 caracteres"
    else:
        nueva_hash = generate_password_hash(nueva)
        conn.execute("UPDATE usuarios SET password = ? WHERE id = ?", (nueva_hash, session["user_id"]))
        conn.commit()
        success = "Contraseña actualizada correctamente"

    conn.close()
    return render_template("perfil.html", usuario=user, error=error, success=success)
    

# -------- API MOVIMIENTOS --------
@app.route("/api/movimientos", methods=["GET"])
def api_listar_movimientos():
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM movimientos WHERE usuario_id = ? ORDER BY fecha DESC, id DESC",
            (session["user_id"],)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route("/api/movimientos", methods=["POST"])
def api_crear_movimiento():
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos inválidos"}), 400

    fecha = data.get("fecha")
    descripcion = data.get("descripcion")
    tipo = data.get("tipo")
    categoria = data.get("categoria")
    monto = data.get("monto")

    if not fecha or not descripcion or not tipo or not categoria or monto is None: # Monto puede ser 0
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    if tipo not in ["Ingreso", "Gasto"]:
        return jsonify({"error": "Tipo inválido"}), 400
    try:
        monto_float = float(monto)
    except ValueError:
        return jsonify({"error": "Monto debe ser numérico"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO movimientos (usuario_id, fecha, descripcion, tipo, categoria, monto) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], fecha, descripcion, tipo, categoria, monto_float)
        )
        conn.commit()
        return jsonify({"ok": True}), 201
    finally:
        conn.close()

@app.route("/api/movimientos/<int:mov_id>", methods=["DELETE"])
def api_eliminar_movimiento(mov_id):
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    try:
        conn.execute("DELETE FROM movimientos WHERE id = ? AND usuario_id = ?", (mov_id, session["user_id"]))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()

# NUEVA RUTA: Borrar todos los movimientos y metas del usuario (Borrar todo)
@app.route("/api/datos", methods=["DELETE"])
def api_borrar_todo():
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    try:
        conn.execute("DELETE FROM movimientos WHERE usuario_id = ?", (session["user_id"],))
        conn.execute("DELETE FROM metas WHERE usuario_id = ?", (session["user_id"],))
        conn.commit()
        print(f"✔ Datos de usuario {session['user_id']} eliminados.")
        return jsonify({"ok": True})
    finally:
        conn.close()

# -------- API METAS --------
@app.route("/api/metas", methods=["GET"])
def api_listar_metas():
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM metas WHERE usuario_id = ? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route("/api/metas", methods=["POST"])
def api_crear_meta():
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos inválidos"}), 400

    nombre = data.get("nombre")
    objetivo = data.get("objetivo")
    actual = data.get("actual", 0)

    if not nombre or objetivo is None:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    try:
        objetivo_float = float(objetivo)
        actual_float = float(actual)
    except ValueError:
        return jsonify({"error": "Objetivo y actual deben ser numéricos"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO metas (usuario_id, nombre, objetivo, actual) VALUES (?, ?, ?, ?)",
            (session["user_id"], nombre, objetivo_float, actual_float)
        )
        conn.commit()
        return jsonify({"ok": True}), 201
    finally:
        conn.close()

@app.route("/api/metas/<int:meta_id>", methods=["PUT"])
def api_actualizar_meta(meta_id):
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos inválidos"}), 400

    # Implementación para solo actualizar campos específicos
    fields = []
    values = []
    
    if 'actual' in data:
        try:
            actual_float = float(data['actual'])
            fields.append("actual = ?")
            values.append(actual_float)
        except ValueError:
            return jsonify({"error": "El monto actual debe ser numérico"}), 400
    
    # Otros campos que se puedan actualizar (ej. nombre, objetivo)
    if 'nombre' in data:
        fields.append("nombre = ?")
        values.append(data['nombre'])

    if 'objetivo' in data:
        try:
            objetivo_float = float(data['objetivo'])
            fields.append("objetivo = ?")
            values.append(objetivo_float)
        except ValueError:
            return jsonify({"error": "El monto objetivo debe ser numérico"}), 400
    
    if not fields:
        return jsonify({"error": "No se proporcionaron campos válidos para actualizar"}), 400

    values.extend([meta_id, session["user_id"]])

    conn = get_db()
    try:
        conn.execute(
            f"UPDATE metas SET {', '.join(fields)} WHERE id = ? AND usuario_id = ?",
            tuple(values)
        )
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()

@app.route("/api/metas/<int:meta_id>", methods=["DELETE"])
def api_eliminar_meta(meta_id):
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    conn = get_db()
    try:
        conn.execute("DELETE FROM metas WHERE id = ? AND usuario_id = ?", (meta_id, session["user_id"]))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()

# -------- INICIO --------
if __name__ == "__main__":
    init_db()   # Solo llamamos a la función de init_db.py
    app.run(debug=True)

