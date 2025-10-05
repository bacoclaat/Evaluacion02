import bcrypt
import logging # Tengo que añadir un log para el error
import re

class Usuario:
    def __init__(self,nombre,email,password):
        patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        patron_nombre = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$' # Solo letras y espacios
        if not re.match(patron_nombre, nombre):
            raise ValueError("El nombre solo puede contener letras y espacios.") # Loggear error
        else:
            self.nombre = nombre
        if not re.match(patron_email, email):
            raise ValueError("El email no tiene un formato válido.") # Loggear error
        else:
            self._email = email
        try:
            if ' ' in password or password == "":
                raise ValueError("La contraseña no puede contener espacios o estar vacia.") # Loggear error
            else:
                self._password_hash = bcrypt.hashpw(password.encode('latin-1'), bcrypt.gensalt())
        except UnicodeEncodeError:
            raise ValueError("La contraseña contiene caracteres no compatibles con latin-1.") # Loggear error
        
    def verificar_password(self, password):
        return bcrypt.checkpw(password.encode('latin-1'), self._password_hash)


# Ejemplo de uso
while True:
    try:
        input_nombre = input("Ingrese su nombre: ")
        input_email = input("Ingrese su email: ")
        input_password = input("Ingrese su contraseña: ")
        usuario = Usuario(input_nombre, input_email, input_password)
    except ValueError as e:
        print(f"Error al crear el usuario: {e}")
        continue
