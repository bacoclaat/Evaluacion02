import sqlite3
import bcrypt
import re
from datetime import datetime, timedelta, date

# Tengo que añadir prestamos para el Universitario
# Ademas tiene que poder pedir un prestamo, y si el libro esta disponible que lo añada a prestamos

patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
patron_nombre = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$' # Solo letras y espacios
patron_nombre_libro = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9\s]+$' # Solo letras, numeros y espacios
patron_isbn = r"^(?:\d{9}[\dXx]|\d{13}|\d{3}-\d{1,5}-\d{1,7}-\d{1,6}-[\dXx])$" # ISBN (Identificador unico para libros)

class Usuario:
    def __init__(self,nombre,email,password):
        if not re.match(patron_nombre, nombre):
            raise ValueError("El nombre solo puede contener letras y espacios.") 
        else:
            self.nombre = nombre
        if not re.match(patron_email, email):
            raise ValueError("El email no tiene un formato válido.") 
        else:
            self._email = email
        try:
            if ' ' in password or password.strip() == "":
                raise ValueError("La contraseña no puede contener espacios o estar vacia.")
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
            raise ValueError("El nombre de la universidad solo puede contener letras y espacios.") 
        else:
            self.universidad = universidad
    
    def mostrar_info(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        
        c.execute("SELECT id, nombre, email FROM usuarios WHERE email = ? AND tipo = 'bibliotecario'", (self._email,))
        fila = c.fetchone()
        
        if fila:
            id_usuario, nombre, email = fila
            c.execute("SELECT universidad FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
            fila_bib = c.fetchone()
            universidad = fila_bib[0] if fila_bib else "No registrada"
            
            print(f"ID: {id_usuario}")
            print(f"Nombre: {nombre}")
            print(f"Email: {email}")
            print(f"Universidad: {universidad}")
        else:
            print("Usuario no encontrado o no es bibliotecario.")
        
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
        c.execute("SELECT usuario_id FROM bibliotecarios WHERE usuario_id = ?", (usuario_id,))
        if c.fetchone():
            raise ValueError("El usuario ya está registrado.")
        c.execute("INSERT INTO bibliotecarios (usuario_id, universidad) VALUES (?, ?)", (usuario_id, self.universidad))
        c.execute("UPDATE usuarios SET tipo = 'bibliotecario' WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()

class Universitario(Usuario):
    def __init__(self,nombre,email,password,universidad):
        super().__init__(nombre,email,password)
        if not re.match(patron_nombre, universidad):
            raise ValueError("El nombre de la universidad solo puede contener letras y espacios.") 
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
            raise ValueError("El usuario ya está registrado.")
        c.execute("INSERT INTO universitarios (usuario_id, universidad) VALUES (?, ?)", (usuario_id, self.universidad))
        c.execute("UPDATE usuarios SET tipo = 'universitario' WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()




# Tenemos que tener ya una cuenta generica de admin (Ej: Nombre: Admin ,Contraseña: admin123)
class Admin(Usuario):
    def __init__(self,nombre,email,password):
        super().__init__(nombre,email,password) # Prueba

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
            raise ValueError("El usuario ya está registrado.")
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
            raise ValueError("El titulo solo puede contener letras, numeros y espacios.") 
        else:
            self.titulo = titulo
        if not re.match(patron_nombre, autor):
            raise ValueError("El autor solo puede contener letras y espacios.") 
        else:
            self.autor = autor
        if not re.match(patron_nombre, genero):
            raise ValueError("El genero solo puede contener letras y espacios.") 
        else:
            self.genero = genero
        año_actual = datetime.now().year
        if not re.match(r'^\d{4}$', str(año)) or not (1000 <= int(año) <= año_actual):
            raise ValueError(f"Año inválido, debe estar entre 1000 y {año_actual}") 
        else:
            self.año = int(año)
        try:
            self.cantidad = int(cantidad)
        except ValueError:
            raise ValueError("La cantidad tiene que ser un numero entero.")
        if not re.match(patron_isbn, isbn):
            raise ValueError("El ISBN no tiene un formato válido.") 
        else:
            self.isbn = isbn
            
    def mostrar_info(self):
        print(f"Título: {self.titulo}, Autor: {self.autor}, Género: {self.genero}, Año: {self.año}, Tipo: {self.tipo}, Cantidad: {self.cantidad}, ISBN: {self.isbn}") 

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


from datetime import datetime, timedelta, date
import sqlite3

class Prestamo:
    def __init__(self, universitario, libro, dias):
        # Maximo 14 dias de prestamo
        try:
            dias = int(dias)
        except ValueError:
            raise ValueError("La cantidad de días debe ser un número entero.")
        
        if dias <= 0:
            raise ValueError("El préstamo debe ser por al menos 1 día.")
        if dias > 14:
            raise ValueError("El préstamo no puede ser por más de 14 días (2 semanas).")

        self._universitario = universitario
        self._libro = libro
        self._dias = dias
        self._fch_prestamo = date.today().strftime('%Y-%m-%d')
        self._fch_devolucion = (date.today() + timedelta(days=dias)).strftime('%Y-%m-%d')
        self._is_activo = 1 
        self._fch_devolucion_real = None 
        
    def ver_prestamo(self):
        fch_dev_dt = datetime.strptime(self._fch_devolucion, '%Y-%m-%d').date()
        fch_prestamo_dt = datetime.strptime(self._fch_prestamo, '%Y-%m-%d').date()
        
        dias_restantes = (fch_dev_dt - date.today()).days
        
        estado = "ACTIVO"
        if not self._is_activo:
            estado = f"DEVUELTO ({self._fch_devolucion_real})"
        elif dias_restantes < 0:
            estado = "ATRASADO"
        
        print(f"Universitario: {self._universitario.nombre}, Libro: {self._libro.titulo}")
        print(f"Fecha de prestamo: {fch_prestamo_dt}, Vencimiento: {fch_dev_dt}, Estado: {estado}")
        if dias_restantes >= 0 and self._is_activo:
            print(f"Días restantes: {dias_restantes}")


    def save(self):
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        
        # 1. Verificar Universitario
        c.execute("SELECT id FROM usuarios WHERE id = ? AND tipo = 'universitario'", (self._universitario.id,))
        if not c.fetchone():
            conn.close()
            raise ValueError("El universitario no existe en la base de datos.")
            
        # 2. Verificar Libro
        c.execute("SELECT cantidad FROM libros WHERE id = ?", (self._libro.id,))
        fila = c.fetchone()
        if not fila:
            conn.close()
            raise ValueError("El libro no existe.")
        
        cantidad = fila[0]
        if cantidad <= 0:
            conn.close()
            raise ValueError("No hay copias disponibles de este libro.")
            
        # 3. Insertar el préstamo (incluyendo los nuevos campos de estado)
        c.execute("INSERT INTO prestamos (universitario_id, libro_id, dias, fch_prestamo, fch_devolucion, is_activo) VALUES (?, ?, ?, ?, ?, ?)", 
                  (self._universitario.id, self._libro.id, self._dias, self._fch_prestamo, self._fch_devolucion, self._is_activo))
        
        self.id = c.lastrowid
        
        # 4. Actualizar el inventario
        c.execute("UPDATE libros SET cantidad = cantidad - 1 WHERE id = ?", (self._libro.id,))
        
        conn.commit()
        conn.close()
