import bcrypt
import logging # Tengo que añadir un log para el error
import re
from datetime import datetime

# Tengo que añadir prestamos para el Universitario
# Ademas tiene que poder pedir un prestamo, y si el libro esta disponible que lo añada a prestamos

patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
patron_nombre = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$' # Solo letras y espacios
patron_nombre_libro = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9\s]+$' # Solo letras, numeros y espacios
patron_isbn = r'^(?:\d{9}[\dXx]|\d{13}|\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-[\dXx])$'

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
                self._password_hash = bcrypt.hashpw(password.encode('latin-1'), bcrypt.gensalt())
        except UnicodeEncodeError:
            raise ValueError("La contraseña contiene caracteres no compatibles con latin-1.") # Loggear error
        
    def mostrar_info(self):
        print(f"Nombre: {self.nombre}, Email: {self._email}", end="")
        
    def verificar_password(self, password):
        return bcrypt.checkpw(password.encode('latin-1'), self._password_hash)
    
class Bibliotecario(Usuario):
    def __init__(self,nombre,email,password,universidad):
        super().__init__(nombre, email, password)
        if not re.match(patron_nombre, universidad):
            raise ValueError("El nombre de la universidad solo puede contener letras y espacios.") # Loggear error  
        else:
            self.universidad = universidad
    
    def mostrar_info(self):
        super().mostrar_info() 
        print(f", Universidad: {self.universidad}")

class Universitario(Usuario):
    def __init__(self,nombre,email,password,universidad):
        super().__init__(nombre,email,password)
        if not re.match(patron_nombre, universidad):
            raise ValueError("El nombre de la universidad solo puede contener letras y espacios.") # Loggear error  
        else:
            self.universidad = universidad
        self.prestamo = []
        
class Libro:
    def __init__(self,titulo,autor,genero,año,tipo,cantidad,isbn):
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
            raise ValueError(f"Año inválido, debe estar entre 1000 y {año_actual}")
        else:
            self.año = int(año)
        if not re.match(patron_nombre, tipo):
            raise ValueError("El tipo de libro solo puede contener letras y espacios.") # Loggear error
        else:
            self.tipo = tipo
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

class Prestamo:
    def __init__(self,usuario,libro,dias) # Terminar esto


