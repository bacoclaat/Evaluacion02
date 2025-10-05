import requests

nombre = input("Ingrese nombre pokemon: ")
url = f"https://pokeapi.co/api/v2/pokemon/{nombre.lower()}"
respuesta = requests.get(url)
if respuesta.status_code == 200:
    datos = respuesta.json()
    print(f"Nombre: {datos['name']}")
else:
    print("Pokémon no encontrado.")