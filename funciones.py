import clases 



def a():
    while True:
        try:
            a = verificar_datos("nombre")
            email = verificar_datos("correo")
            input_password = input("Ingrese su contraseña: ")
            input_universidad = input("Ingrese su universidad: ")
            usuario = clases.Bibliotecario(a, email, input_password, input_universidad)
        except ValueError as e:
            print(f"Error al crear el usuario: {e}")
            continue
        ooo = input("Ingrese su contraseña para verificar: ")
        if usuario.verificar_password(ooo):
            print("Contraseña verificada correctamente.")
        else:
            print("Contraseña incorrecta.")
        usuario.mostrar_info()


def verificar_datos(dato):
    verificar = input(f"Ingresa el {dato}")
    if verificar == 1:
        print(f"AAAAAAAAAAAAAAAAAA")


a()