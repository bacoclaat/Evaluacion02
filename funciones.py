import BD
from datetime import datetime, timedelta, date # Importante, para saber cuando se tiene que devolver
import clases 
import sqlite3
import bcrypt
BD.init_db()


def reglogin():
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
                    print("Usuario actualizado a universitario exitosamente.")
                except ValueError as ve:
                    print(f"Error en el registro: {ve}")
                    continue
            elif tipo_usuario == 2:
                try:
                    universidad = input("Ingrese su universidad: ")
                    usuario_bibliotecario = clases.Bibliotecario(nombre, email, password, universidad)
                    usuario_bibliotecario.save()
                    print("Usuario actualizado a bibliotecario exitosamente.")
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
            return tipo, usuario_logeado
        elif opcion == 3:
            print("Saliendo del sistema.")
            exit()


def ver_libros_disponibles():
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()
    c.execute("SELECT id, titulo, autor, cantidad FROM libros WHERE cantidad > 0")
    libros = c.fetchall()
    conn.close()

    if libros:
        print("=== Libros disponibles ===")
        for libro in libros:
            id_libro, titulo, autor, cantidad = libro
            print(f"{id_libro}. {titulo} - {autor} | Copias disponibles: {cantidad}")
        return libros
    else:
        print("No hay libros disponibles.")
        return []


def menu_universitario(usuario_logeado):
    while True:
        print("=== Menú Universitario ===")
        print("1. Ver libros disponibles")
        print("2. Prestamos")
        print("3. Informacion de la cuenta")
        print("4. Cerrar sesión")
        try:
            opcion = int(input("Seleccione una opción: "))
            if opcion == 1:
                    print("1. Ver libros disponibles")
                    print("2. Buscar libro por título")
                    try:
                        input_opcion = int(input("Seleccione una opción: "))
                        if input_opcion == 1:
                            ver_libros_disponibles()
                        elif input_opcion == 2:
                            titulo_buscar = input("Ingrese el título del libro a buscar: ").strip()
                            conn = sqlite3.connect('biblioteca.db')
                            c = conn.cursor()
                            c.execute("SELECT id, titulo, autor, cantidad FROM libros WHERE titulo LIKE ?", ('%' + titulo_buscar + '%',))
                            libros_encontrados = c.fetchall()
                            conn.close()
                            if libros_encontrados:
                                print("=== Resultados de la búsqueda ===")
                                for libro in libros_encontrados:
                                    id_libro, titulo, autor, cantidad = libro
                                    print(f"{id_libro}. {titulo} - {autor} | Copias disponibles: {cantidad}")
                            else:
                                print("No se encontraron libros con ese título.")
                    except ValueError:
                        print("Por favor, ingrese un número válido.")
            elif opcion == 2:
                    print("1. Ver mis préstamos")
                    print("2. Realizar un préstamo")
                    print("3. Volver")
                    opcion_prestamo = int(input("Seleccione una opción: "))
                    if opcion_prestamo == 2:
                        libros = ver_libros_disponibles()
                        if not libros:
                            continue
                        try:
                            id_libro = int(input("Ingrese el ID del libro que desea prestar: "))
                            dias = int(input("Ingrese la cantidad de días del préstamo: "))
                            libro_seleccionado = None
                            for libro in libros:
                                if libro[0] == id_libro:
                                    id_libro, titulo, autor, cantidad = libro
                                    # Traemos todos los datos reales del libro desde la BD
                                    conn = sqlite3.connect("biblioteca.db")
                                    c = conn.cursor()
                                    c.execute("SELECT titulo, autor, genero, año, cantidad, isbn FROM libros WHERE id = ?", (id_libro,))
                                    fila = c.fetchone()
                                    conn.close()
                                    if fila:
                                        titulo, autor, genero, año, cantidad_real, isbn = fila
                                        libro_seleccionado = clases.Libro(titulo, autor, genero, año, cantidad_real, isbn)
                                        libro_seleccionado.id = id_libro
                                    break
                            if not libro_seleccionado:
                                print("ID de libro inválido.")
                                continue
                            prestamo = clases.Prestamo(usuario_logeado, libro_seleccionado, dias)
                            prestamo.save()
                            print(f"Préstamo realizado: {libro_seleccionado.titulo} por {dias} días.")
                        except ValueError as ve:
                            print(f"Error: {ve}")
                    elif opcion_prestamo == 1:
                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("""
                            SELECT libros.titulo, libros.autor, prestamos.fch_prestamo, prestamos.fch_devolucion
                            FROM prestamos
                            JOIN libros ON prestamos.libro_id = libros.id
                            WHERE prestamos.universitario_id = ?
                        """, (usuario_logeado.id,))
                        prestamos = c.fetchall()
                        conn.close()
                        if prestamos:
                            print("=== Mis préstamos ===")
                            for libro, autor, fch_prestamo, fch_devolucion in prestamos:
                                dias_restantes = (datetime.strptime(fch_devolucion, "%Y-%m-%d").date() - date.today()).days
                                estado = "Atrasado" if dias_restantes < 0 else f"{dias_restantes} días restantes"
                                print(f"{libro} - {autor} | Desde: {fch_prestamo} Hasta: {fch_devolucion} | {estado}")
                        else:
                            print("No tienes préstamos activos.")

                    elif opcion_prestamo == 3:
                        break
                    else:
                        print("Opción inválida.")
            elif opcion == 3:
                    usuario_logeado.mostrar_info()
            elif opcion == 4:
                    print("Cerrando sesión.")
                    break
            else:
                    print("Opción inválida.")
        except ValueError:
            print("Por favor, ingrese un número válido.")


def menu_bibliotecario(usuario_logeado):
    while True:
        print("=== Menú Bibliotecario ===")
        print("1. Gestionar libros")
        print("2. Gestionar préstamos")
        print("3. Información de la cuenta")
        print("4. Cerrar sesión")
        input_opcion = int(input("Seleccione una opción: "))
        try:
            input_opcion = int(input("Seleccione una opción: "))

            if input_opcion == 1:
                while True:
                    print("--- Gestión de Libros ---")
                    print("1. Agregar libro")
                    print("2. Ver libros")
                    print("3. Modificar libro")
                    print("4. Eliminar libro")
                    print("5. Volver al menú principal")
                    sub_opcion = int(input("Seleccione una opción: "))

                    if sub_opcion == 1:
                        try:
                            titulo = input("Título: ").strip()
                            autor = input("Autor: ").strip()
                            genero = input("Género: ").strip()
                            año = int(input("Año: "))
                            cantidad = int(input("Cantidad: "))
                            isbn = input("ISBN: ").strip()

                            libro = clases.Libro(titulo, autor, genero, año, cantidad, isbn)
                            libro.save()
                            print(f"Libro '{titulo}' agregado exitosamente.")
                        except ValueError as ve:
                            print(f"Error: {ve}")

                    elif sub_opcion == 2:
                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("SELECT id, titulo, autor, cantidad FROM libros")
                        libros = c.fetchall()
                        conn.close()
                        if libros:
                            print("=== Libros en la biblioteca ===")
                            for id_libro, titulo, autor, cantidad in libros:
                                print(f"{id_libro}. {titulo} - {autor} | Copias: {cantidad}")
                        else:
                            print("No hay libros registrados.")

                    elif sub_opcion == 3:
                        id_libro = int(input("Ingrese el ID del libro a modificar: "))
                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("SELECT titulo, autor, genero, año, cantidad, isbn FROM libros WHERE id = ?", (id_libro,))
                        libro = c.fetchone()
                        if not libro:
                            print("Libro no encontrado.")
                            conn.close()
                            continue
                        print(f"Libro actual: {libro}")
                        titulo = input(f"Título ({libro[0]}): ").strip() or libro[0]
                        autor = input(f"Autor ({libro[1]}): ").strip() or libro[1]
                        genero = input(f"Género ({libro[2]}): ").strip() or libro[2]
                        año = input(f"Año ({libro[3]}): ").strip()
                        año = int(año) if año else libro[3]
                        cantidad = input(f"Cantidad ({libro[4]}): ").strip()
                        cantidad = int(cantidad) if cantidad else libro[4]
                        isbn = input(f"ISBN ({libro[5]}): ").strip() or libro[5]
                        try:
                            c.execute("""
                                UPDATE libros
                                SET titulo = ?, autor = ?, genero = ?, año = ?, cantidad = ?, isbn = ?
                                WHERE id = ?
                            """, (titulo, autor, genero, año, cantidad, isbn, id_libro))
                            conn.commit()
                            print("Libro modificado exitosamente.")
                        except sqlite3.IntegrityError:
                            print("Error: ISBN duplicado.")
                        conn.close()

                    elif sub_opcion == 4:
                        id_libro = int(input("Ingrese el ID del libro a eliminar: "))
                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("SELECT titulo FROM libros WHERE id = ?", (id_libro,))
                        libro = c.fetchone()
                        if not libro:
                            print("Libro no encontrado.")
                            conn.close()
                            continue
                        confirm = input(f"¿Está seguro de eliminar '{libro[0]}'? (s/n): ").lower()
                        if confirm == 's':
                            c.execute("DELETE FROM libros WHERE id = ?", (id_libro,))
                            conn.commit()
                            print("Libro eliminado exitosamente.")
                        conn.close()

                    elif sub_opcion == 5:
                        break
                    else:
                        print("Opción inválida.")

            elif input_opcion == 2:
                while True:
                    print("--- Gestión de Préstamos ---")
                    print("1. Ver todos los préstamos")
                    print("2. Volver al menú principal")
                    sub_opcion = int(input("Seleccione una opción: "))

                    if sub_opcion == 1:
                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("""
                            SELECT prestamos.id, usuarios.nombre, libros.titulo, prestamos.fch_prestamo, prestamos.fch_devolucion
                            FROM prestamos
                            JOIN universitarios ON prestamos.universitario_id = universitarios.usuario_id
                            JOIN usuarios ON universitarios.usuario_id = usuarios.id
                            JOIN libros ON prestamos.libro_id = libros.id
                        """)
                        prestamos = c.fetchall()
                        conn.close()
                        if prestamos:
                            print("=== Todos los préstamos ===")
                            for id_prestamo, nombre, titulo, fch_prestamo, fch_devolucion in prestamos:
                                dias_restantes = (datetime.strptime(fch_devolucion, "%Y-%m-%d").date() - date.today()).days
                                estado = "Atrasado" if dias_restantes < 0 else f"{dias_restantes} días restantes"
                                print(f"{id_prestamo}. {titulo} - {nombre} | Desde: {fch_prestamo} Hasta: {fch_devolucion} | {estado}")
                        else:
                            print("No hay préstamos registrados.")
                    elif sub_opcion == 2:
                        break
                    else:
                        print("Opción inválida.")

            elif input_opcion == 3:
                usuario_logeado.mostrar_info()

            elif input_opcion == 4:
                print("Cerrando sesión.")
                break

            else:
                print("Opción inválida.")

        except ValueError:
            print("Por favor, ingrese un número válido.")


def menu_admin(usuario_logeado):
    while True:
        print("=== Menú Admin ===")
        print("1. Gestionar usuarios")
        print("2. Información de la cuenta")
        print("3. Cerrar sesión")

        try:
            input_opcion = int(input("Seleccione una opción: "))

            if input_opcion == 1:
                while True:
                    print("--- Gestión de Usuarios ---")
                    print("1. Ver todos los usuarios")
                    print("2. Modificar usuario")
                    print("3. Eliminar usuario")
                    print("4. Volver al menú principal")

                    try:
                        sub_opcion = int(input("Seleccione una opción: "))
                    except ValueError:
                        print("Por favor, ingrese un número válido.")
                        continue

                    if sub_opcion == 1:
                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("SELECT id, nombre, email, tipo FROM usuarios")
                        usuarios = c.fetchall()
                        conn.close()
                        if usuarios:
                            print("=== Usuarios registrados ===")
                            for id_usuario, nombre, email, tipo in usuarios:
                                print(f"{id_usuario}. {nombre} - {email} | Tipo: {tipo}")
                        else:
                            print("No hay usuarios registrados.")

                    elif sub_opcion == 2:
                        try:
                            id_usuario = int(input("Ingrese el ID del usuario a modificar: "))
                        except ValueError:
                            print("ID inválido.")
                            continue

                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("SELECT id, nombre, email, tipo FROM usuarios WHERE id = ?", (id_usuario,))
                        usuario = c.fetchone()
                        if not usuario:
                            print("Usuario no encontrado.")
                            conn.close()
                            continue

                        id_u, nombre, email, tipo = usuario
                        print(f"Usuario seleccionado: {nombre} - {email} | Tipo: {tipo}")

                        nuevo_nombre = input(f"Ingrese nuevo nombre (enter para mantener '{nombre}'): ").strip()
                        nuevo_email = input(f"Ingrese nuevo email (enter para mantener '{email}'): ").strip()

                        if nuevo_nombre == "":
                            nuevo_nombre = nombre
                        if nuevo_email == "":
                            nuevo_email = email

                        c.execute("UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?", (nuevo_nombre, nuevo_email, id_usuario))

                        if tipo == "universitario":
                            c.execute("SELECT universidad FROM universitarios WHERE usuario_id = ?", (id_usuario,))
                            fila = c.fetchone()
                            universidad_actual = fila[0] if fila else ""
                            nueva_uni = input(f"Ingrese nueva universidad (enter para mantener '{universidad_actual}'): ").strip()
                            if nueva_uni != "":
                                c.execute("UPDATE universitarios SET universidad = ? WHERE usuario_id = ?", (nueva_uni, id_usuario))
                        elif tipo == "bibliotecario":
                            c.execute("SELECT universidad FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
                            fila = c.fetchone()
                            universidad_actual = fila[0] if fila else ""
                            nueva_uni = input(f"Ingrese nueva universidad (enter para mantener '{universidad_actual}'): ").strip()
                            if nueva_uni != "":
                                c.execute("UPDATE bibliotecarios SET universidad = ? WHERE usuario_id = ?", (nueva_uni, id_usuario))

                        conn.commit()
                        conn.close()
                        print("Usuario modificado correctamente.")

                    elif sub_opcion == 3:
                        try:
                            id_usuario = int(input("Ingrese el ID del usuario a eliminar: "))
                        except ValueError:
                            print("ID inválido.")
                            continue

                        conn = sqlite3.connect("biblioteca.db")
                        c = conn.cursor()
                        c.execute("SELECT nombre, tipo FROM usuarios WHERE id = ?", (id_usuario,))
                        usuario = c.fetchone()
                        if not usuario:
                            print("Usuario no encontrado.")
                            conn.close()
                            continue

                        nombre, tipo = usuario
                        confirm = input(f"¿Está seguro de eliminar '{nombre}'? (s/n): ").lower()
                        if confirm == 's':

                            if tipo == "universitario":
                                c.execute("DELETE FROM prestamos WHERE universitario_id = ?", (id_usuario,))
                                c.execute("DELETE FROM universitarios WHERE usuario_id = ?", (id_usuario,))
                            elif tipo == "bibliotecario":
                                c.execute("DELETE FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))

                            c.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                            conn.commit()
                            print("Usuario eliminado exitosamente.")
                        conn.close()

                    elif sub_opcion == 4:
                        break
                    else:
                        print("Opción inválida.")

            elif input_opcion == 2:
                usuario_logeado.mostrar_info()

            elif input_opcion == 3:
                print("Cerrando sesión.")
                break

            else:
                print("Opción inválida.")

        except ValueError:
            print("Por favor, ingrese un número válido.")