

def menu():
    print("""
    1 - Iniciar sesion
    2 - Registrarse
    3 - Salir""")

    while True:
        try:
            ingresar = int(input("Ingresa una opcion: "))
            
            if ingresar == 1:
                continue

            elif ingresar == 2:
                pass

            elif ingresar == 3:
                break
            
            else:
                print("Ingresa un numero valido")
                continue
        except ValueError:
            print("Ingresa algo valido")
            continue

menu()