import sqlite3
import bcrypt
import logging # Tengo que añadir un log para el error
import re
from datetime import datetime, timedelta, date

# Tengo que añadir prestamos para el Universitario
# Ademas tiene que poder pedir un prestamo, y si el libro esta disponible que lo añada a prestamos

patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
patron_nombre = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$' # Solo letras y espacios
patron_nombre_libro = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9\s]+$' # Solo letras, numeros y espacios
patron_isbn = r'^(?:\d{9}[\dXx]|\d{13}|\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-[\dXx])$' # ISBN (Identificador unico para libros)

class Usuario:
    def __init__(self,nombre,email,password):
        if not re.match(patron_nombre, nombre):
            raise ValueError("El nombre solo puede contener letras y espacios.") # Loggear error
        else:
            self.nombre = nombre
        if not re.match(patron_email, email):
            raise ValueError("El email no tiene un formato válido.") # Loggear error
        else:
            self._email = email
        try:
            if ' ' in password or password.strip() == "":
                raise ValueError("La contraseña no puede contener espacios o estar vacia.") # Loggear error
            else:
                self._password_hash = bcrypt.hashpw(password.encode('latin-1'), bcrypt.gensalt()) # Hasheado con bcrypt, se usa verificar_password y tiene que lanzar un True.
        except UnicodeEncodeError:
            raise ValueError("La contraseña contiene caracteres no compatibles con latin-1.") # Latin-1 solo permite letras acentuadas, signos y simbolos especiales, Loggear error
        
    def mostrar_info(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id, nombre, email from usuarios where email = ?", (self._email,))
        fila = c.fetchone()
        conn.close()

        if fila:
            id_usuario, nombre, email = fila
            print(f"ID: {id_usuario}")
            print(f"Nombre: {nombre}")
            print(f"Email: {email}")
        else:
            print("Usuario no encontrado.")


    def verificar_password(self, password):
        return bcrypt.checkpw(password.encode('latin-1'), self._password_hash)
    
    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id FROM usuarios WHERE email = ?", (self._email,))
        fila = c.fetchone()
        if fila:
            conn.close()
            raise ValueError("El usuario ya está registrado.")
        else:
            c.execute("INSERT INTO usuarios (nombre, email, password_hash, tipo) VALUES (?, ?, ?, 'usuario')", (self.nombre, self._email, self._password_hash))
            self.id = c.lastrowid
            conn.commit()
            conn.close()
    
class Bibliotecario(Usuario):
    def __init__(self,nombre,email,password,universidad):
        super().__init__(nombre, email, password)
        if not re.match(patron_nombre, universidad):
            raise ValueError("El nombre de la universidad solo puede contener letras y espacios.") # Loggear error  
        else:
            self.universidad = universidad
    
    def mostrar_info(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id, nombre, email, universidad from usuarios where email = ?", (self._email,))
        fila = c.fetchone()
        conn.close()

        if fila:
            id_usuario, nombre, email, universidad = fila
            print(f"ID: {id_usuario}")
            print(f"Nombre: {nombre}")
            print(f"Email: {email}")
            print(f"Universidad: {universidad}")
        else:
            print("Usuario no encontrado.")

    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id FROM usuarios WHERE email = ?", (self._email,))
        fila = c.fetchone()
        if not fila:
            super().save()
            usuario_id = self.id
        else:
            usuario_id = fila[0]
        c.execute("SELECT usuario_id FROM bibliotecarios WHERE usuario_id = ?", (usuario_id,))
        if c.fetchone():
            raise ValueError("El usuario ya está registrado como bibliotecario.")
        c.execute("INSERT INTO bibliotecarios (usuario_id, universidad) VALUES (?, ?)", (usuario_id, self.universidad))
        c.execute("UPDATE usuarios SET tipo = 'bibliotecario' WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()

class Universitario(Usuario):
    def __init__(self,nombre,email,password,universidad):
        super().__init__(nombre,email,password)
        if not re.match(patron_nombre, universidad):
            raise ValueError("El nombre de la universidad solo puede contener letras y espacios.") # Loggear error  
        else:
            self.universidad = universidad


    def mostrar_info(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        # Obtenemos datos básicos de la tabla usuarios
        c.execute("SELECT id, nombre, email FROM usuarios WHERE email = ?", (self._email,))
        fila = c.fetchone()
        if fila:
            id_usuario, nombre, email = fila
            # Obtenemos universidad de la tabla universitarios
            c.execute("SELECT universidad FROM universitarios WHERE usuario_id = ?", (id_usuario,))
            fila_uni = c.fetchone()
            universidad = fila_uni[0] if fila_uni else "No registrada"
            print(f"ID: {id_usuario}")
            print(f"Nombre: {nombre}")
            print(f"Email: {email}")
            print(f"Universidad: {universidad}")
        else:
            print("Usuario no encontrado.")
        conn.close()


    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id FROM usuarios WHERE email = ?", (self._email,))
        fila = c.fetchone()
        if not fila:
            super().save()
            usuario_id = self.id
        else:
            usuario_id = fila[0]
        c.execute("SELECT usuario_id FROM universitarios WHERE usuario_id = ?", (usuario_id,))
        if c.fetchone():
            raise ValueError("El usuario ya está registrado como universitario.")
        c.execute("INSERT INTO universitarios (usuario_id, universidad) VALUES (?, ?)", (usuario_id, self.universidad))
        c.execute("UPDATE usuarios SET tipo = 'universitario' WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()



# El admin debe poder modificar los usuarios, eliminar usuarios, modificar usuarios
# Tenemos que tener ya una cuenta generica de admin (Ej: Nombre: Admin ,Contraseña: admin123)
class Admin(Usuario):
    def __init__(self,nombre,password):
        super().__init__(nombre,password)

    def mostrar_info(self):
        return super().mostrar_info()

    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id FROM usuarios WHERE email = ?", (self._email,))
        fila = c.fetchone()
        if not fila:
            super().save()
            usuario_id = self.id
        else:
            usuario_id = fila[0]
        c.execute("SELECT usuario_id FROM admin WHERE usuario_id = ?", (usuario_id,))
        if c.fetchone():
            raise ValueError("El usuario ya está registrado como administrador.")
        c.execute("INSERT INTO admin (usuario_id) VALUES (?)", (usuario_id,))
        c.execute("UPDATE usuarios SET tipo = 'admin' WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()



    def modificar_usuario(self):
        buscar = input("Ingrese el ID del usuario que desea modificar: ").strip()
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id, nombre, email, tipo FROM usuarios WHERE id = ?", (buscar,))
        fila = c.fetchone()
        if not fila:
            conn.close()
            raise ValueError("El usuario no existe.")
        id_usuario, nombre, email, tipo = fila
        print(f"\nID: {id_usuario}\nNombre: {nombre}\nEmail: {email}\nTipo: {tipo}")
        if tipo == "universitario":
            c.execute("SELECT universidad FROM universitarios WHERE usuario_id = ?", (id_usuario,))
            fila_uni = c.fetchone()
            if fila_uni:
                print(f"Universidad: {fila_uni[0]}")
            else:
                print("No se encontró universidad asociada.")
        elif tipo == "bibliotecario":
            c.execute("SELECT universidad FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
            fila_bib = c.fetchone()
            if fila_bib:
                print(f"Universidad: {fila_bib[0]}")
            else:
                print("No se encontró universidad asociada.")
        else:
            print("Este usuario no tiene universidad asociada (tipo admin).")
        conn.close()
        

        
class Libro:
    def __init__(self,titulo,autor,genero,año,cantidad,isbn):
        if not re.match(patron_nombre_libro, titulo):
            raise ValueError("El titulo solo puede contener letras, numeros y espacios.") # Loggear error
        else:
            self.titulo = titulo
        if not re.match(patron_nombre, autor):
            raise ValueError("El autor solo puede contener letras y espacios.") # Loggear error
        else:
            self.autor = autor
        if not re.match(patron_nombre, genero):
            raise ValueError("El genero solo puede contener letras y espacios.") # Loggear error
        else:
            self.genero = genero
        año_actual = datetime.now().year
        if not re.match(r'^\d{4}$', str(año)) or not (1000 <= int(año) <= año_actual):
            raise ValueError(f"Año inválido, debe estar entre 1000 y {año_actual}") # Se asegura que no puedan haber
        else:
            self.año = int(año)
        try:
            self.cantidad = int(cantidad)
        except ValueError:
            raise ValueError("La cantidad tiene que ser un numero entero.")
        if not re.match(patron_isbn, isbn):
            raise ValueError("El ISBN no tiene un formato válido.") # Loggear error
        else:
            self.isbn = isbn
            
    def mostrar_info(self):
        print(f"Título: {self.titulo}, Autor: {self.autor}, Género: {self.genero}, Año: {self.año}, Tipo: {self.tipo}, Cantidad: {self.cantidad}, ISBN: {self.isbn}") # Falta añadir la id que la da la base de datos

    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id FROM libros WHERE isbn = ?", (self.isbn,))
        fila = c.fetchone()
        if fila:
            conn.close()
            raise ValueError("Ya existe un libro con ese ISBN.")
        else:
            c.execute("INSERT INTO libros (titulo, autor, genero, año, cantidad, isbn) VALUES (?, ?, ?, ?, ?, ?)", (self.titulo, self.autor, self.genero, self.año, self.cantidad, self.isbn))
            self.id = c.lastrowid
            conn.commit()
            conn.close()

# Terminar esto, no esta listo
class Prestamo:
    def __init__(self,universitario,libro,dias):
        self._universitario = universitario
        self._libro = libro
        self._dias = dias
        self._fch_prestamo = date.today()
        self._fch_devolucion = self._fch_prestamo + timedelta(days=dias)
        

# Aca la base de datos o el crud tiene que ir actualizando el dia actual, para saber cuando se tiene que devolver el libro
    def ver_prestamo(self):
        dias_restantes = (self._fch_devolucion - date.today()).days
        print(f"Universitario: {self._universitario.nombre}, Libro: {self._libro.titulo}, Fecha de prestamo: {self._fch_prestamo}, Fecha de devolucion: {self._fch_devolucion}, Dias restantes: {dias_restantes}")
        if dias_restantes < 0:
            print("El libro está atrasado.")

    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id FROM universitarios WHERE id = ?", (self._universitario.id,))
        if not c.fetchone():
            conn.close()
            raise ValueError("El universitario no existe en la base de datos.")
        else:
            c.execute("SELECT cantidad FROM libros WHERE id = ?", (self._libro.id,))
            fila = c.fetchone()
        if not fila:
            conn.close()
            raise ValueError("El libro no existe.")
        else:
            cantidad = fila[0]
            if cantidad <= 0:
                conn.close()
                raise ValueError("No hay copias disponibles de este libro.")
            else:
                c.execute("INSERT INTO prestamos (universitario_id, libro_id, dias, fch_prestamo, fch_devolucion) VALUES (?, ?, ?, ?, ?)", (self._universitario.id, self._libro.id, self._dias, self._fch_prestamo, self._fch_devolucion))
                self.id = c.lastrowid
                c.execute("UPDATE libros SET cantidad = cantidad - 1 WHERE id = ?", (self._libro.id,))
                conn.commit()
                conn.close()
        

