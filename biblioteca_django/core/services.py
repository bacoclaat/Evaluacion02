import sqlite3
import bcrypt
import re
from datetime import datetime, timedelta, date

DB = "db.sqlite3"

# PATRONES
patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
patron_nombre = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$'
patron_nombre_libro = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9\s]+$'
patron_isbn = r"^(?:\d{9}[\dXx]|\d{13}|\d{3}-\d{1,5}-\d{1,7}-\d{1,6}-[\dXx])$"


def conectar():
    return sqlite3.connect(DB)


class Usuario:
    def __init__(self, nombre, email, password):
        if not re.match(patron_nombre, nombre):
            raise ValueError("Nombre inválido.")

        if not re.match(patron_email, email):
            raise ValueError("Email inválido.")

        if " " in password or password.strip() == "":
            raise ValueError("Contraseña inválida.")

        self.nombre = nombre
        self.email = email
        self.password_hash = bcrypt.hashpw(password.encode("latin-1"), bcrypt.gensalt())

    def save(self, tipo="usuario"):
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT id FROM usuarios WHERE email = ?", (self.email,))
        if c.fetchone():
            conn.close()
            raise ValueError("El usuario ya existe.")

        c.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, tipo) VALUES (?, ?, ?, ?)",
            (self.nombre, self.email, self.password_hash, tipo)
        )

        self.id = c.lastrowid
        conn.commit()
        conn.close()
        return self.id


class Bibliotecario(Usuario):
    def __init__(self, nombre, email, password, universidad):
        super().__init__(nombre, email, password)

        if not re.match(patron_nombre, universidad):
            raise ValueError("Universidad inválida.")
        
        self.universidad = universidad

    def save(self):
        user_id = super().save(tipo="bibliotecario")

        conn = conectar()
        c = conn.cursor()
        c.execute(
            "INSERT INTO bibliotecarios (usuario_id, universidad) VALUES (?, ?)",
            (user_id, self.universidad)
        )
        conn.commit()
        conn.close()


class Universitario(Usuario):
    def __init__(self, nombre, email, password, universidad):
        super().__init__(nombre, email, password)

        if not re.match(patron_nombre, universidad):
            raise ValueError("Universidad inválida.")
        
        self.universidad = universidad

    def save(self):
        user_id = super().save(tipo="universitario")

        conn = conectar()
        c = conn.cursor()
        c.execute(
            "INSERT INTO universitarios (usuario_id, universidad) VALUES (?, ?)",
            (user_id, self.universidad)
        )
        conn.commit()
        conn.close()


class Admin(Usuario):
    def save(self):
        user_id = super().save(tipo="admin")

        conn = conectar()
        c = conn.cursor()
        c.execute("INSERT INTO admin (usuario_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()


class Libro:
    def __init__(self, titulo, autor, genero, año, cantidad, isbn):
        if not re.match(patron_nombre_libro, titulo):
            raise ValueError("Título inválido.")

        if not re.match(patron_nombre, autor):
            raise ValueError("Autor inválido.")

        if not re.match(patron_nombre, genero):
            raise ValueError("Género inválido.")

        if not (1000 <= int(año) <= datetime.now().year):
            raise ValueError("Año inválido.")

        if not re.match(patron_isbn, isbn):
            raise ValueError("ISBN inválido.")

        self.titulo = titulo
        self.autor = autor
        self.genero = genero
        self.año = int(año)
        self.cantidad = int(cantidad)
        self.isbn = isbn

    def save(self):
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT id FROM libros WHERE isbn = ?", (self.isbn,))
        if c.fetchone():
            conn.close()
            raise ValueError("Libro ya existe.")

        c.execute(
            "INSERT INTO libros (titulo, autor, genero, año, cantidad, isbn) VALUES (?, ?, ?, ?, ?, ?)",
            (self.titulo, self.autor, self.genero, self.año, self.cantidad, self.isbn)
        )

        self.id = c.lastrowid
        conn.commit()
        conn.close()


class Prestamo:
    def __init__(self, universitario_id, libro_id, dias):
        dias = int(dias)
        if dias <= 0 or dias > 14:
            raise ValueError("Días inválidos (1-14).")

        self.universitario_id = universitario_id
        self.libro_id = libro_id
        self.dias = dias
        self.fecha_prestamo = date.today()
        self.fecha_devolucion = self.fecha_prestamo + timedelta(days=dias)

    def save(self):
        conn = conectar()
        c = conn.cursor()

        # Checar disponibilidad
        c.execute("SELECT cantidad FROM libros WHERE id = ?", (self.libro_id,))
        fila = c.fetchone()

        if not fila:
            conn.close()
            raise ValueError("Libro no existe.")

        cantidad = fila[0]
        if cantidad <= 0:
            conn.close()
            raise ValueError("No hay copias disponibles.")

        # Crear préstamo
        c.execute(
            "INSERT INTO prestamos (universitario_id, libro_id, dias, fch_prestamo, fch_devolucion) VALUES (?, ?, ?, ?, ?)",
            (self.universitario_id, self.libro_id, self.dias, self.fecha_prestamo, self.fecha_devolucion)
        )

        # Restar stock
        c.execute("UPDATE libros SET cantidad = cantidad - 1 WHERE id = ?", (self.libro_id,))

        conn.commit()
        conn.close()
