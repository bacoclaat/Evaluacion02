# Evaluacion02
Se necesita diseñar e implementar un sistema para gestionar una biblioteca universitaria donde permita registrar y consultar libros, llevar un control de préstamos y devoluciones realizados por los usuarios para facilitar el control de la biblioteca.

# Flask
Flask (microframework de python)
pip install flask

!!! El flask es una prueba, el index tiene que estar en la carpeta templates. 
# Configuracion Github
 git config --global user.name
 git config --global user.email

# Bcrypt
pip install bcrypt

# Requests
pip install requests

!!! El requests es una prueba

# Base de datos
Aca vamos a usar SQL Lite ya que es ligero y esta integrado en python, es perfecto para usos en aplicaciones pequeñas
- import sqlite3

# Probar calidad de codigo
Usar unititest, para probar las funciones más facil
    import unittest

Usar SonarQube, para ver la calidad del codigo

# Crear Entorno Virtual
python3 -m venv .venv
python -m venv .venv
    ACTIVAR
    .venv\scripts\activate
    DESACTIVAR
    desactivate

# IMPORTANTE
Cuando entreguemos la base de datos hay que dejar por lo menos 1 usuario admin generico, Ejemplo: Nombre: Admin Email: admin@gmail.com Contraseña: admin123