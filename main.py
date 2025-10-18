import BD
from datetime import datetime, timedelta, date # Importante, para saber cuando se tiene que devolver el libro
import sqlite3
import clases
import bcrypt
BD.init_db()


print("Bienvenido a la biblioteca")
while True:
    print("=== Registrar/Login ===")
    print("1. Registrar")
    print("2. Login")
    print("3. Salir")
    opcion = int(input("Seleccione una opción: "))
    if opcion == 1:
        try:
            nombre = input("Ingrese su nombre: ")
            email = input("Ingrese su email: ")
            password = input("Ingrese su contraseña: ")
            usuario_nuevo = clases.Usuario(nombre, email, password)
        except ValueError as ve:
            print(f"Error en el registro: {ve}")
            continue
        print("Usuario registrado exitosamente.")
        print("Es usted un universitario o un bibliotecario?")
        print("1. Universitario")
        print("2. Bibliotecario")
        print("3. Volver")
        tipo_usuario = int(input("Seleccione una opción: "))
        if tipo_usuario == 1:
            try:
                universidad = input("Ingrese su universidad: ")
                usuario_universitario = clases.Universitario(nombre, email, password, universidad)
                usuario_universitario.save()
                print("Usuario universitario registrado exitosamente.")
            except ValueError as ve:
                print(f"Error en el registro: {ve}")
                continue
        elif tipo_usuario == 2:
            try:
                universidad = input("Ingrese su universidad: ")
                usuario_bibliotecario = clases.Bibliotecario(nombre, email, password, universidad)
                usuario_bibliotecario.save()
                print("Usuario bibliotecario registrado exitosamente.")
            except ValueError as ve:
                print(f"Error en el registro: {ve}")
                continue
        elif tipo_usuario == 3:
            continue
        else:
            print("Opción inválida.")
    elif opcion == 2:
        email = input("Ingrese su email: ").strip()
        password = input("Ingrese su contraseña: ").strip()
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        c.execute("SELECT id, nombre, email, password_hash, tipo FROM usuarios WHERE email = ?", (email,))
        fila = c.fetchone()
        if not fila:
            print("Usuario no encontrado.")
            continue
        id_usuario, nombre, email, password_hash, tipo = fila
        if not bcrypt.checkpw(password.encode('latin-1'), password_hash):
            print("Contraseña incorrecta.")
            continue
        print(f"Bienvenido {nombre}, has iniciado sesión como {tipo}.")
        # Esto crea el objeto usuario_logeado adecuado según el tipo, para poder hacer cambios y operaciones correspondientes
        universidad = None
        conn = sqlite3.connect('biblioteca.db')
        c = conn.cursor()
        if tipo == "universitario":
            c.execute("SELECT universidad FROM universitarios WHERE usuario_id = ?", (id_usuario,))
            fila = c.fetchone()
            if fila:
                universidad = fila[0]
            usuario_logeado = clases.Universitario(nombre, email, password, universidad)
        elif tipo == "bibliotecario":
            c.execute("SELECT universidad FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
            fila = c.fetchone()
            if fila:
                universidad = fila[0]
            usuario_logeado = clases.Bibliotecario(nombre, email, password, universidad)
        elif tipo == "admin":
            usuario_logeado = clases.Admin(nombre, password)
        else:
            usuario_logeado = clases.Usuario(nombre, email, password)
        conn.close()
        usuario_logeado.id = id_usuario
        # Aquí se podría agregar el menú específico para cada tipo de usuario
        if tipo == "universitario":
            print("Menú Universitario")
            # Agregar funcionalidades específicas para universitarios
        elif tipo == "bibliotecario":
            print("Menú Bibliotecario")
            # Agregar funcionalidades específicas para bibliotecarios
        elif tipo == "admin":
            print("Menú Admin")
            # Agregar funcionalidades específicas para admin
    elif opcion == 3:
        print("Saliendo del sistema.")
        break



    