import sqlite3

def init_db():
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()
    # Tabla base de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  tipo TEXT NOT NULL)''')
    # Tabla para bibliotecarios
    c.execute('''CREATE TABLE IF NOT EXISTS bibliotecarios
                 (usuario_id INTEGER PRIMARY KEY,
                  universidad TEXT NOT NULL,
                  FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')
    # Tabla para universitarios
    c.execute('''CREATE TABLE IF NOT EXISTS universitarios
                 (usuario_id INTEGER PRIMARY KEY,
                  universidad TEXT NOT NULL,
                  FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')
    # Tabla para admin
    c.execute('''CREATE TABLE IF NOT EXISTS admin
                 (usuario_id INTEGER PRIMARY KEY,
                  FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')

    # Tabla de libros
    c.execute('''CREATE TABLE IF NOT EXISTS libros
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  titulo TEXT NOT NULL,
                  autor TEXT NOT NULL,
                  genero TEXT NOT NULL,
                  año INTEGER NOT NULL,
                  cantidad INTEGER NOT NULL,
                  isbn TEXT UNIQUE NOT NULL)''')
                  
    # Tabla de prestamos (MODIFICADA: Agregamos is_activo y fch_devolucion_real)
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  universitario_id INTEGER NOT NULL,
                  libro_id INTEGER NOT NULL,
                  dias INTEGER NOT NULL,
                  fch_prestamo DATE NOT NULL,
                  fch_devolucion DATE NOT NULL,
                  is_activo INTEGER NOT NULL DEFAULT 1,         -- NUEVO: 1=Activo, 0=Devuelto
                  fch_devolucion_real DATE,                      -- NUEVO: Fecha en que se devuelve
                  FOREIGN KEY (universitario_id) REFERENCES universitarios (usuario_id),
                  FOREIGN KEY (libro_id) REFERENCES libros (id))''')

     # Tabla de auditoría (funcion de las reservas con registro)
    c.execute('''CREATE TABLE IF NOT EXISTS auditoria
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              usuario_id INTEGER NOT NULL,
              accion TEXT NOT NULL,
              tabla_afectada TEXT NOT NULL,
              detalle TEXT,
              fecha DATE NOT NULL,
              FOREIGN KEY (usuario_id) REFERENCES usuarios (id))''')
              
    conn.commit()
    conn.close()

init_db()
print("Base de datos cargada exitosamente.")