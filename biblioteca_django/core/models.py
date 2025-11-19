from django.db import models

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField()
    email = models.TextField(unique=True)
    password_hash = models.TextField()
    tipo = models.TextField()

    class Meta:
        managed = False
        db_table = 'usuarios'

class Universitario(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, db_column='usuario_id', primary_key=True
    )
    universidad = models.TextField()

    class Meta:
        managed = False
        db_table = 'universitarios'

class Bibliotecario(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, db_column='usuario_id', primary_key=True
    )
    universidad = models.TextField()

    class Meta:
        managed = False
        db_table = 'bibliotecarios'

class Admin(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, db_column='usuario_id', primary_key=True
    )

    class Meta:
        managed = False
        db_table = 'admin'

class Libro(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.TextField()
    autor = models.TextField()
    genero = models.TextField()
    año = models.IntegerField()
    cantidad = models.IntegerField()
    isbn = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = 'libros'

class Prestamo(models.Model):
    id = models.AutoField(primary_key=True)
    universitario = models.ForeignKey(
        Universitario, on_delete=models.CASCADE, db_column='universitario_id'
    )
    libro = models.ForeignKey(
        Libro, on_delete=models.CASCADE, db_column='libro_id'
    )
    dias = models.IntegerField()
    fch_prestamo = models.DateField()
    fch_devolucion = models.DateField()

    class Meta:
        managed = False
        db_table = 'prestamos'
