import sqlite3
import re
import bcrypt
import requests # Importar requests para consumir la API
from requests.exceptions import RequestException
from datetime import datetime, timedelta, date 
from clases import Usuario, Bibliotecario, Universitario, Libro, Prestamo, Admin 

# Patron de busqueda para encontrar prestamos por ID de usuario
patron_id = r'^\d+$'

# --- FUNCIONES DE SOPORTE DE API EXTERNA ---

def get_valor_uf():
    """Obtiene el valor actual de la UF de la API de Mindicador."""
    url = "https://mindicador.cl/api/uf"
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        # El valor de la UF se encuentra en la primera posición del array 'serie'
        if data and 'serie' in data and data['serie']:
            return data['serie'][0]['valor']
        return 0.0
    except RequestException as e:
        print(f"Alerta: Error al conectar con la API de indicadores. Multa calculada en 0. {e}")
        return 0.0
    except Exception:
        return 0.0


# --- FUNCIÓN DE AUDITORÍA ---
def log_auditoria(usuario_id, accion, tabla_afectada, detalle):
    # Uso de 'with' para asegurar que la conexión se cierre automáticamente
    try:
        with sqlite3.connect('biblioteca.db') as conn:
            c = conn.cursor()
            fch_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
            c.execute("INSERT INTO auditoria (usuario_id, accion, tabla_afectada, detalle, fecha) VALUES (?, ?, ?, ?, ?)",
                      (usuario_id, accion, tabla_afectada, detalle, fch_actual))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error al registrar auditoría: {e}")


# --- FUNCIONES DE GESTIÓN DE USUARIO Y LOGIN ---

def reglogin():
    while True:
        try:
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
                    usuario_nuevo = Usuario(nombre, email, password)
                except ValueError as ve:
                    print(f"Error en el registro: {ve}")
                    continue
                print("Usuario registrado exitosamente.")
                log_auditoria(usuario_nuevo.id, 'REGISTRO', 'usuarios', f'Registro inicial de {usuario_nuevo.nombre}')
                
                print("Es usted un universitario o un bibliotecario?")
                print("1. Universitario")
                print("2. Bibliotecario")
                print("3. Volver")
                tipo_usuario = int(input("Seleccione una opción: "))
                if tipo_usuario == 1:
                    try:
                        universidad = input("Ingrese su universidad: ")
                        usuario_universitario = Universitario(nombre, email, password, universidad)
                        usuario_universitario.save()
                        print("Usuario actualizado a universitario exitosamente.")
                        log_auditoria(usuario_universitario.id, 'ACTUALIZACION', 'universitarios', 'Perfil actualizado a universitario')
                    except ValueError as ve:
                        print(f"Error en el registro: {ve}")
                        continue
                elif tipo_usuario == 2:
                    try:
                        universidad = input("Ingrese su universidad: ")
                        usuario_bibliotecario = Bibliotecario(nombre, email, password, universidad)
                        usuario_bibliotecario.save()
                        print("Usuario actualizado a bibliotecario exitosamente.")
                        log_auditoria(usuario_bibliotecario.id, 'ACTUALIZACION', 'bibliotecarios', 'Perfil actualizado a bibliotecario')
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
                    log_auditoria(id_usuario, 'LOGIN_FALLIDO', 'usuarios', f'Intento de login fallido para {email}')
                    continue
                print(f"Bienvenido {nombre}, has iniciado sesión como {tipo}.")
                log_auditoria(id_usuario, 'LOGIN_EXITOSO', 'usuarios', f'Inicio de sesión exitoso como {tipo}')
                universidad = None
                conn = sqlite3.connect('biblioteca.db')
                c = conn.cursor()
                if tipo == "universitario":
                    c.execute("SELECT universidad FROM universitarios WHERE usuario_id = ?", (id_usuario,))
                    fila = c.fetchone()
                    if fila:
                        universidad = fila[0]
                    usuario_logeado = Universitario(nombre, email, "dummy_pass", universidad) 
                elif tipo == "bibliotecario":
                    c.execute("SELECT universidad FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
                    fila = c.fetchone()
                    if fila:
                        universidad = fila[0]
                    usuario_logeado = Bibliotecario(nombre, email, "dummy_pass", universidad) 
                elif tipo == "admin":
                    usuario_logeado = Admin(nombre,email, "dummy_pass") 
                else:
                    usuario_logeado = Usuario(nombre, email, "dummy_pass") 
                conn.close()
                usuario_logeado.id = id_usuario
                usuario_logeado._password_hash = password_hash 
                return tipo, usuario_logeado
            elif opcion == 3:
                print("Saliendo del sistema.")
                exit()
            else:
                print("Opción inválida.")
        except ValueError:
            print("Porfavor ingrese un numero.")


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
            print(f"ID: {id_libro}. {titulo} - {autor} | Copias disponibles: {cantidad}")
        return libros
    else:
        print("No hay libros disponibles.")
        return []


# --- FUNCIONES DE GESTIÓN DE PRÉSTAMOS (CORE) ---

def mostrar_mis_prestamos(universitario_id):
    """
    Muestra todos los préstamos activos de un universitario específico (ACTUALIZADA con is_activo).
    """
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            p.id, l.titulo, p.fch_prestamo, p.fch_devolucion 
        FROM prestamos p
        JOIN libros l ON p.libro_id = l.id
        WHERE p.universitario_id = ? AND p.is_activo = 1
    """, (universitario_id,))
    
    prestamos = c.fetchall()
    conn.close()
    
    if not prestamos:
        print("No tienes préstamos activos actualmente.")
        return
        
    print(f"\n--- Mis Préstamos Activos ---")
    
    for id_prestamo, titulo_libro, fch_prestamo, fch_devolucion in prestamos:
        fch_dev_dt = datetime.strptime(fch_devolucion, '%Y-%m-%d').date()
        dias_restantes = (fch_dev_dt - datetime.now().date()).days
        estado = "Atrasado" if dias_restantes < 0 else f"{dias_restantes} días restantes"
        
        print(f"ID Préstamo: {id_prestamo} | Libro: {titulo_libro} | Prestado: {fch_prestamo} | Devolución límite: {fch_devolucion} | Estado: {estado}")
        
    print("----------------------------------------------------------")


def mostrar_todos_prestamos_activos():
    """
    Muestra TODOS los préstamos activos en la base de datos (para uso administrativo).
    """
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            p.id, u.nombre, l.titulo, p.fch_prestamo, p.fch_devolucion 
        FROM prestamos p
        JOIN usuarios u ON p.universitario_id = u.id
        JOIN libros l ON p.libro_id = l.id
        WHERE p.is_activo = 1
        ORDER BY p.fch_devolucion ASC
    """)
    
    prestamos = c.fetchall()
    conn.close()
    
    if not prestamos:
        print("\nNo hay préstamos activos registrados.")
        return
        
    print("\n--- Todos los Préstamos Activos ---")
    print("{:<15} {:<25} {:<30} {:<15} {:<15} {:<10}".format(
        "ID Préstamo", "Universitario", "Libro", "Fch Préstamo", "Fch Devolución", "Estado"
    ))
    print("-" * 110)
    
    ids_activos = []
    for id_prestamo, nombre_uni, titulo_libro, fch_prestamo, fch_devolucion in prestamos:
        fch_dev_dt = datetime.strptime(fch_devolucion, '%Y-%m-%d').date()
        dias_restantes = (fch_dev_dt - datetime.now().date()).days
        
        if dias_restantes < 0:
            estado = f"ATRASADO ({abs(dias_restantes)} días)"
        elif dias_restantes == 0:
            estado = "HOY"
        else:
            estado = f"{dias_restantes} días"
            
        print("{:<15} {:<25} {:<30} {:<15} {:<15} {:<10}".format(
            id_prestamo, nombre_uni, titulo_libro, fch_prestamo, fch_devolucion, estado
        ))
        ids_activos.append(id_prestamo)
        
    print("-----------------------------------")
    return ids_activos


def realizar_devolucion_admin(prestamo_id, bibliotecario_id):
    """
    Marca un préstamo como devuelto (is_activo=0) y actualiza el stock del libro.
    """
    if not re.match(patron_id, str(prestamo_id)):
        print("Error: El ID de préstamo debe ser un número entero.")
        return False
        
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()
    
    try:
        # 1. Verificar si el préstamo existe y está activo
        c.execute("""
            SELECT p.libro_id, l.titulo, u.nombre, p.fch_devolucion 
            FROM prestamos p
            JOIN libros l ON p.libro_id = l.id
            JOIN usuarios u ON p.universitario_id = u.id
            WHERE p.id = ? AND p.is_activo = 1
        """, (prestamo_id,))
        
        fila = c.fetchone()
        
        if not fila:
            print(f"Error: Préstamo ID {prestamo_id} no encontrado o ya ha sido devuelto.")
            conn.close()
            return False

        libro_id, titulo_libro, nombre_uni, fch_vencimiento_str = fila
        
        # 2. Marcar el préstamo como devuelto (is_activo = 0) y registrar la fecha real de devolución
        fch_devolucion_real = datetime.now().strftime('%Y-%m-%d')
        
        c.execute("""
            UPDATE prestamos 
            SET is_activo = 0, fch_devolucion_real = ? 
            WHERE id = ?
        """, (fch_devolucion_real, prestamo_id))
        
        # 3. Aumentar la cantidad del libro en el inventario
        c.execute("UPDATE libros SET cantidad = cantidad + 1 WHERE id = ?", (libro_id,))
        
        # 4. Verificar retraso (Integración con API para multa)
        fch_vencimiento = datetime.strptime(fch_vencimiento_str, "%Y-%m-%d").date()
        dias_retraso = (datetime.now().date() - fch_vencimiento).days
        
        mensaje_retraso = ""
        if dias_retraso > 0:
            # --- Lógica de cálculo de multa con la API (MEJORA PROPUESTA) ---
            VALOR_UF_HOY = get_valor_uf() # Llamada a la nueva función
            MULTA_POR_DIA_UF = 0.01 # Multa hipotética: 0.01 UF por día
            
            multa_total_uf = dias_retraso * MULTA_POR_DIA_UF
            multa_total_clp = multa_total_uf * VALOR_UF_HOY
            
            mensaje_multa_clp = f"{multa_total_clp:,.0f}" if VALOR_UF_HOY > 0 else "N/A"
            # -------------------------------------------------------------------
            
            mensaje_retraso = f" **¡ATENCIÓN!** Devolución con **{dias_retraso} días de retraso**.\n"
            mensaje_retraso += f"    -> Multa calculada (0.01 UF/día): {multa_total_uf:.2f} UF ({mensaje_multa_clp} CLP)"
        
        conn.commit()
        
        # 5. Auditoría
        log_auditoria(bibliotecario_id, 'DEVOLUCION', 'prestamos', f'Devolución registrada de Préstamo ID {prestamo_id} (Libro: {titulo_libro})')
        
        print(f"\n--- Devolución Exitosa (ID Préstamo: {prestamo_id}) ---")
        print(f"Libro: '{titulo_libro}' por {nombre_uni}.")
        print(f"Fecha de devolución real: {fch_devolucion_real}")
        print(mensaje_retraso) # Imprimir el mensaje de multa
        print("El inventario del libro ha sido actualizado.")
        print("------------------------------------------------")
        return True

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error de base de datos al realizar la devolución: {e}")
        return False
    except Exception as e:
        print(f"Error desconocido: {e}")
        return False
    finally:
        conn.close()


# --- FUNCIÓN MENU UNIVERSITARIO ---
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
                                print(f"ID: {id_libro}. {titulo} - {autor} | Copias disponibles: {cantidad}")
                        else:
                            print("No se encontraron libros con ese título.")
                except ValueError:
                    print("Por favor, ingrese un número válido.")

            elif opcion == 2:
                while True: 
                    print("\n--- Gestión de Préstamos (Universitario) ---")
                    print("1. Ver mis préstamos activos")
                    print("2. Realizar un préstamo")
                    print("3. Volver al menú principal")
                    
                    try:
                        opcion_prestamo = int(input("Seleccione una opción: "))
                        if opcion_prestamo == 1:
                            mostrar_mis_prestamos(usuario_logeado.id) 
                        elif opcion_prestamo == 2:
                            libros = ver_libros_disponibles()
                            if not libros:
                                continue
                            
                            isbn_libro = input("Ingrese el ISBN del libro que desea prestar: ").strip() 
                            dias_str = input("Ingrese la cantidad de días del préstamo (Max 14): ").strip()

                            try:
                                conn = sqlite3.connect('biblioteca.db')
                                c = conn.cursor()
                                c.execute("SELECT id, titulo, autor, genero, año, cantidad, isbn FROM libros WHERE isbn = ?", (isbn_libro,))
                                fila = c.fetchone()
                                conn.close()
                                if not fila:
                                    print("ISBN de libro inválido o libro no encontrado.")
                                    continue
                                
                                libro_id, titulo, autor, genero, año, cantidad_real, isbn = fila
                                
                                libro_seleccionado = Libro(titulo, autor, genero, año, cantidad_real, isbn)
                                libro_seleccionado.id = libro_id
                                
                                prestamo = Prestamo(usuario_logeado, libro_seleccionado, dias_str)
                                prestamo.save()
                                print(f"Préstamo realizado: {libro_seleccionado.titulo} por {dias_str} días.")
                                log_auditoria(usuario_logeado.id, 'PRESTAMO', 'prestamos', f'Nuevo préstamo ID {prestamo.id} de Libro {libro_id}')
                                
                            except ValueError as ve:
                                print(f"Error: {ve}")
                            except Exception as e:
                                print(f"Error desconocido: {e}")
                            
                        elif opcion_prestamo == 3:
                            break 
                        else:
                            print("Opción inválida.")
                    except ValueError:
                        print("Por favor, ingrese un número válido.")
                        continue


            elif opcion == 3:
                usuario_logeado.mostrar_info()
            elif opcion == 4:
                print("Cerrando sesión.")
                break
            else:
                print("Opción inválida.")
        except ValueError:
            print("Por favor, ingrese un número válido.")


# --- FUNCIÓN MENU BIBLIOTECARIO (ACTUALIZADA con Devoluciones y Auditoría) ---
def menu_bibliotecario(usuario_logeado):
    while True:
        print("=== Menú Bibliotecario ===")
        print("1. Gestionar libros")
        print("2. Gestionar préstamos")
        print("3. Información de la cuenta")
        print("4. Cerrar sesión")
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
                            libro = Libro(titulo, autor, genero, año, cantidad, isbn)
                            libro.save()
                            print(f"Libro '{titulo}' agregado exitosamente.")
                            log_auditoria(usuario_logeado.id, 'LIBRO_ADD', 'libros', f'Libro ID {libro.id} agregado')
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
                                print(f"ID: {id_libro}. {titulo} - {autor} | Copias: {cantidad}")
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
                            log_auditoria(usuario_logeado.id, 'LIBRO_MOD', 'libros', f'Libro ID {id_libro} modificado')
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
                            log_auditoria(usuario_logeado.id, 'LIBRO_DEL', 'libros', f'Libro ID {id_libro} eliminado')
                        conn.close()

                    elif sub_opcion == 5:
                        break
                    else:
                        print("Opción inválida.")

            elif input_opcion == 2:
                while True:
                    print("\n--- Gestión de Préstamos ---")
                    print("1. Ver todos los préstamos ACTIVOS")
                    print("2. Registrar una DEVOLUCIÓN (Marcar como Devuelto)")
                    print("3. Modificar un préstamo (Extender fecha)")
                    print("4. Eliminar un préstamo (Cancelación forzosa y actualización de stock)")
                    print("5. Volver al menú principal")
                    
                    try:
                        sub_opcion = int(input("Seleccione una opción: "))

                        if sub_opcion == 1:
                            mostrar_todos_prestamos_activos() 

                        elif sub_opcion == 2: 
                            ids_activos = mostrar_todos_prestamos_activos()
                            if not ids_activos:
                                continue
                            try:
                                id_prestamo = int(input("Ingrese el ID del préstamo a registrar como DEVUELTO: "))
                                realizar_devolucion_admin(id_prestamo, usuario_logeado.id) 
                            except ValueError:
                                print("Por favor, ingrese un número válido para el ID.")
                        
                        elif sub_opcion == 3: 
                            mostrar_todos_prestamos_activos()
                            try:
                                id_prestamo = int(input("Ingrese el ID del préstamo a modificar: "))
                                conn = sqlite3.connect("biblioteca.db")
                                c = conn.cursor()
                                c.execute("SELECT fch_prestamo, fch_devolucion, is_activo FROM prestamos WHERE id = ?", (id_prestamo,))
                                prestamo = c.fetchone()
                                if not prestamo:
                                    print("Préstamo no encontrado.")
                                    conn.close()
                                    continue
                                
                                if not prestamo[2]:
                                    print("Error: El préstamo ya fue devuelto y no puede modificarse.")
                                    conn.close()
                                    continue
                                    
                                print(f"Fecha de préstamo actual: {prestamo[0]} | Vencimiento actual: {prestamo[1]}")
                                dias_extra = int(input("Ingrese días adicionales para extender el préstamo: "))
                                if dias_extra <= 0:
                                    print("Debe ingresar un número positivo.")
                                    conn.close()
                                    continue

                                nueva_fecha_devolucion = datetime.strptime(prestamo[1], "%Y-%m-%d").date() + timedelta(days=dias_extra)
                                c.execute("UPDATE prestamos SET fch_devolucion = ? WHERE id = ?", (nueva_fecha_devolucion, id_prestamo))
                                conn.commit()
                                print(f"Préstamo extendido hasta {nueva_fecha_devolucion}.")
                                log_auditoria(usuario_logeado.id, 'PRESTAMO_MOD', 'prestamos', f'Préstamo ID {id_prestamo} extendido hasta {nueva_fecha_devolucion}')
                            except ValueError:
                                print("Entrada inválida. No se realizó el cambio.")
                            conn.close()

                        elif sub_opcion == 4: 
                            mostrar_todos_prestamos_activos()
                            try:
                                id_prestamo = int(input("Ingrese el ID del préstamo a ELIMINAR/CANCELAR: "))
                            except ValueError:
                                print("ID inválido.")
                                continue

                            conn = sqlite3.connect("biblioteca.db")
                            c = conn.cursor()
                            c.execute("""
                                SELECT prestamos.id, libros.id, libros.titulo, prestamos.is_activo 
                                FROM prestamos 
                                JOIN libros ON prestamos.libro_id = libros.id 
                                WHERE prestamos.id = ?
                            """, (id_prestamo,))
                            fila = c.fetchone()
                            if not fila:
                                print("Préstamo no encontrado.")
                                conn.close()
                                continue
                            
                            _, id_libro, titulo_libro, is_activo = fila
                            
                            if not is_activo:
                                print("Error: Este préstamo ya está marcado como devuelto. No es necesario cancelarlo.")
                                conn.close()
                                continue
                                
                            confirm = input(f"¿Desea ELIMINAR el préstamo ACTIVO del libro '{titulo_libro}'? Esto devolverá el libro al inventario. (s/n): ").lower()
                            if confirm == 's':
                                c.execute("DELETE FROM prestamos WHERE id = ?", (id_prestamo,))
                                c.execute("UPDATE libros SET cantidad = cantidad + 1 WHERE id = ?", (id_libro,))
                                conn.commit()
                                print("Préstamo eliminado y libro devuelto al inventario.")
                                log_auditoria(usuario_logeado.id, 'PRESTAMO_DEL', 'prestamos', f'Préstamo ID {id_prestamo} eliminado forzosamente')
                            conn.close()

                        elif sub_opcion == 5:
                            break
                        else:
                            print("Opción inválida.")
                            
                    except ValueError:
                        print("Por favor, ingrese un número válido.")
                        continue


            elif input_opcion == 3:
                usuario_logeado.mostrar_info()

            elif input_opcion == 4:
                print("Cerrando sesión.")
                break

            else:
                print("Opción inválida.")

        except ValueError:
            print("Por favor, ingrese un número válido.")


# --- FUNCIÓN MENU ADMIN ---
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
                                print(f"ID: {id_usuario}. {nombre} - {email} | Tipo: {tipo}")
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
                        c.execute("SELECT id, nombre, email, tipo, password_hash FROM usuarios WHERE id = ?", (id_usuario,))
                        usuario = c.fetchone()
                        if not usuario:
                            print("Usuario no encontrado.")
                            conn.close()
                            continue

                        id_u, nombre, email, tipo, password_hash = usuario
                        print(f"Usuario seleccionado: {nombre} - {email} | Tipo: {tipo}")

                        nuevo_nombre = input(f"Ingrese nuevo nombre (enter para mantener '{nombre}'): ").strip()
                        nuevo_email = input(f"Ingrese nuevo email (enter para mantener '{email}'): ").strip()
                        if nuevo_nombre == "":
                            nuevo_nombre = nombre
                        if nuevo_email == "":
                            nuevo_email = email

                        cambiar_pass = input("¿Desea cambiar la contraseña? (s/n): ").lower()
                        if cambiar_pass == "s":
                            nueva_pass = input("Ingrese la nueva contraseña: ").strip()
                            if nueva_pass == "":
                                nueva_pass_hash = password_hash
                            else:
                                nueva_pass_hash = bcrypt.hashpw(nueva_pass.encode('latin-1'), bcrypt.gensalt())
                        else:
                            nueva_pass_hash = password_hash

                        c.execute("UPDATE usuarios SET nombre = ?, email = ?, password_hash = ? WHERE id = ?", 
                                  (nuevo_nombre, nuevo_email, nueva_pass_hash, id_usuario))

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
                        log_auditoria(usuario_logeado.id, 'USUARIO_MOD', 'usuarios', f'Usuario ID {id_usuario} modificado')

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
                                c.execute("DELETE FROM universitarios WHERE usuario_id = ?", (id_usuario,))
                            elif tipo == "bibliotecario":
                                c.execute("DELETE FROM bibliotecarios WHERE usuario_id = ?", (id_usuario,))
                            elif tipo == "admin":
                                c.execute("DELETE FROM admin WHERE usuario_id = ?", (id_usuario,))
                            
                            c.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                            conn.commit()
                            print("Usuario eliminado exitosamente.")
                            log_auditoria(usuario_logeado.id, 'USUARIO_DEL', 'usuarios', f'Usuario ID {id_usuario} ({nombre}) eliminado')
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