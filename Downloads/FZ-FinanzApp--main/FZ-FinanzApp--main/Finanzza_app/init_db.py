import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.executescript("""
    -- Tabla de Usuarios: Almacena la información de autenticación
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );

    -- Tabla de Movimientos: Registra ingresos y gastos
    CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        tipo TEXT NOT NULL,
        categoria TEXT NOT NULL,
        monto REAL NOT NULL,
        timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Campo añadido
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );

    -- Tabla de Metas: Registra objetivos de ahorro
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        objetivo REAL NOT NULL,
        actual REAL NOT NULL,
        timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Campo añadido
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos creada o verificada correctamente.")

