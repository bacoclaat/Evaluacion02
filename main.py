import biblioteca_django.core.funciones as funciones


print("Bienvenido a la biblioteca")
while True:
    tipo, usuario_logeado = funciones.reglogin()
    if tipo == "universitario":
        funciones.menu_universitario(usuario_logeado)
    elif tipo == "bibliotecario":
        funciones.menu_bibliotecario(usuario_logeado)
    elif tipo == "admin":
        funciones.menu_admin(usuario_logeado)
    else:
        print("Tipo de usuario no reconocido.")
        break



    