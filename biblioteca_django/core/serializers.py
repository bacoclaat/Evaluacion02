#API REST
from rest_framework import serializers
from .models import Usuario, Universitario, Bibliotecario, Admin, Libro, Prestamo

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class UniversitarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Universitario
        fields = '__all__'

class BibliotecarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bibliotecario
        fields = '__all__'

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class LibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = '__all__'

class PrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestamo
        fields = '__all__'