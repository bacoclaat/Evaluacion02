import clases

uni = clases.Universitario("Ignacio","ingacio@gmail.cl","ignacio123","UdeC")
lib = clases.Libro("El Quijote","Cervantes","Novela",1605,"Tapa Dura",3,"1234567890123")

pr = clases.Prestamo(uni,lib,15)

print(f"Fecha de prestamo: {pr._fch_prestamo}")
print(f"Fecha de devolucion: {pr._fch_devolucion}")
pr.ver_prestamo()