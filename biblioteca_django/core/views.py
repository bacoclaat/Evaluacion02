from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
from datetime import datetime, date
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

from .models import Libro, Prestamo, Universitario, Bibliotecario
from .utils import log_auditoria


#SERIALIZADORES

def is_bibliotecario(user):
    """Verifica si el usuario es un bibliotecario."""
    return Bibliotecario.objects.filter(usuario=user).exists()

def user_serializer(user_instance, role_type):
    """Serializa un objeto User y su rol asociado para el frontend."""
    full_name = user_instance.get_full_name() or user_instance.username
    doc = ""
    
    try:
        if role_type == "Universitario":
            profile = Universitario.objects.get(usuario=user_instance)
            doc = profile.doc
        elif role_type == "Bibliotecario":
            profile = Bibliotecario.objects.get(usuario=user_instance)
            doc = profile.doc or "N/A"
    except ObjectDoesNotExist:
        pass
    
    return {
        'id': user_instance.pk,
        'username': user_instance.username,
        'name': full_name,
        'doc': doc,
        'role': role_type,
    }

def libro_serializer(libro):
    """Serializa un objeto Libro."""
    return {
        'id': libro.pk,
        'titulo': libro.titulo,
        'autor': libro.autor,
        'genero': libro.genero,
        'año': libro.año,
        'cantidad': libro.cantidad,
        'isbn': libro.isbn,
    }

def prestamo_serializer(prestamo):
    """Serializa un objeto Prestamo."""
    try:
        uni_data = user_serializer(prestamo.universitario.usuario, "Universitario")
    except Exception:
        uni_data = {'id': None, 'name': 'Usuario Eliminado', 'doc': 'N/A', 'role': 'Universitario'}
        
    return {
        'id': prestamo.pk,
        'libro': libro_serializer(prestamo.libro),
        'universitario': uni_data,
        'fch_prestamo': prestamo.fch_prestamo.isoformat(),
        'fch_devolucion': prestamo.fch_devolucion.isoformat(),
        'is_activo': prestamo.is_activo,
        'fch_devolucion_real': prestamo.fch_devolucion_real.isoformat() if prestamo.fch_devolucion_real else None,
    }



#VISTAS BASE (HTML)

def index(request):
    """Renderiza la plantilla principal de la aplicación. Asume que está en 'index.html' dentro de 'templates/'"""
    return render(request, 'core/index.html') 



#VISTAS DE AUTENTICACIÓN Y SESIÓN

@require_http_methods(["GET"])
def check_session(request):
    """Verifica si el usuario está autenticado y devuelve sus datos."""
    if request.user.is_authenticated:
        role = "Bibliotecario" if is_bibliotecario(request.user) else "Universitario"
        
        doc = ""
        try:
            profile = Universitario.objects.get(usuario=request.user)
            doc = profile.doc
        except ObjectDoesNotExist:
            try:
                profile = Bibliotecario.objects.get(usuario=request.user)
                doc = profile.doc
            except ObjectDoesNotExist:
                pass

        return JsonResponse({
            'is_authenticated': True,
            'user_id': request.user.pk,
            'role': role,
            'full_name': request.user.get_full_name() or request.user.username,
            'doc': doc or 'N/A',
            'message': 'Sesión activa.'
        })
    return JsonResponse({'is_authenticated': False, 'message': 'No hay sesión activa.'})


@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    """Registra un nuevo usuario y su rol asociado."""
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name').strip()
        doc = data.get('doc').strip()
        email = data.get('email').strip()
        password = data.get('password')
        role = data.get('role')
        username = data.get('username')

        if not all([full_name, email, password, role, username]):
            return JsonResponse({'success': False, 'message': 'Faltan campos obligatorios.'}, status=400)
        
        if role == "Universitario" and not doc:
            return JsonResponse({'success': False, 'message': 'El documento (RUT/DNI) es obligatorio para Universitarios.'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'El nombre de usuario ya existe.'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'El correo electrónico ya está registrado.'}, status=400)
        
        if role == "Universitario" and Universitario.objects.filter(doc=doc).exists():
            return JsonResponse({'success': False, 'message': 'El documento (RUT/DNI) ya está registrado.'}, status=400)

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name.split(' ')[0],
                last_name=' '.join(full_name.split(' ')[1:]),
                is_staff=(role == "Bibliotecario") 
            )

            if role == "Bibliotecario":
                Bibliotecario.objects.create(usuario=user) 
            elif role == "Universitario":
                Universitario.objects.create(usuario=user, doc=doc) 
            
            log_auditoria(user.id, 'REGISTRO', role, f'Usuario {username} registrado con rol {role}.')

        return JsonResponse({'success': True, 'message': f'Usuario {username} registrado exitosamente.'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Formato JSON inválido.'}, status=400)
    except Exception as e:
        print(f"Error en registro: {e}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor al registrar.'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    """Autentica al usuario."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            role = "Bibliotecario" if is_bibliotecario(user) else "Universitario"
            
            doc = ""
            try:
                profile = Universitario.objects.get(usuario=user)
                doc = profile.doc
            except ObjectDoesNotExist:
                 try:
                    profile = Bibliotecario.objects.get(usuario=user)
                    doc = profile.doc
                 except ObjectDoesNotExist:
                    pass

            log_auditoria(user.id, 'LOGIN', role, f'Usuario {username} ha iniciado sesión.')
            
            return JsonResponse({
                'success': True, 
                'message': 'Inicio de sesión exitoso.',
                'user_id': user.pk,
                'role': role,
                'full_name': user.get_full_name() or user.username,
                'doc': doc or 'N/A'
            })
        else:
            return JsonResponse({'success': False, 'message': 'Usuario o contraseña incorrectos.'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Formato JSON inválido.'}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Error interno del servidor.'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    """Cierra la sesión del usuario."""
    if request.user.is_authenticated:
        log_auditoria(request.user.id, 'LOGOUT', 'User', f'Usuario {request.user.username} ha cerrado sesión.')
        logout(request)
        return JsonResponse({'success': True, 'message': 'Sesión cerrada exitosamente.'})
    return JsonResponse({'success': False, 'message': 'No hay sesión para cerrar.'})


#VISTAS DE LIBROS (CRUD)

@require_http_methods(["GET"])
def get_books(request):
    """Devuelve la lista de todos los libros."""
    libros = Libro.objects.all()
    data = [libro_serializer(libro) for libro in libros]
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def add_book(request):
    """Agrega un nuevo libro. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
    
    try:
        data = json.loads(request.body)
        Libro.objects.create(
            titulo=data['titulo'],
            autor=data['autor'],
            genero=data['genero'],
            año=data.get('año', datetime.now().year),
            cantidad=data['cantidad'],
            isbn=data['isbn'],
        )
        log_auditoria(request.user.id, 'LIBRO_ADD', 'Libro', f'Libro {data["titulo"]} agregado.')
        return JsonResponse({'success': True, 'message': 'Libro agregado exitosamente.'}, status=201)
    
    except KeyError as e:
        return JsonResponse({'success': False, 'message': f'Faltan datos obligatorios del libro: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al guardar: {str(e)}'}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_book(request, libro_id):
    """Elimina un libro. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
        
    try:
        libro = Libro.objects.get(pk=libro_id)
        if Prestamo.objects.filter(libro=libro, is_activo=True).exists():
            return JsonResponse({'success': False, 'message': 'No se puede eliminar: tiene préstamos activos.'}, status=400)
        
        log_auditoria(request.user.id, 'LIBRO_DEL', 'Libro', f'Libro {libro.titulo} eliminado.')
        libro.delete()
        return JsonResponse({'success': True, 'message': 'Libro eliminado.'})
        
    except Libro.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Libro no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al eliminar: {str(e)}'}, status=500)



#VISTAS DE USUARIOS

@login_required
@require_http_methods(["GET"])
def get_users(request):
    """Devuelve la lista de universitarios. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
    
    universitarios = Universitario.objects.select_related('usuario').all()
    data = [user_serializer(u.usuario, "Universitario") for u in universitarios]
    
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    """Elimina un usuario (User). Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
        
    try:
        user = User.objects.get(pk=user_id)
        
        if user.pk == request.user.pk:
            return JsonResponse({'success': False, 'message': 'No puedes eliminar tu propia cuenta.'}, status=400)
            
        if Universitario.objects.filter(usuario=user).exists():
             uni = Universitario.objects.get(usuario=user)
             if Prestamo.objects.filter(universitario=uni, is_activo=True).exists():
                 return JsonResponse({'success': False, 'message': 'No se puede eliminar: el usuario tiene préstamos activos.'}, status=400)
        
        log_auditoria(request.user.id, 'USER_DEL', 'User', f'Usuario {user.username} eliminado.')
        user.delete()
        return JsonResponse({'success': True, 'message': 'Usuario y perfil asociado eliminados.'})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al eliminar: {str(e)}'}, status=500)



# VISTAS DE PRÉSTAMOS

@login_required
@require_http_methods(["GET"])
def get_all_loans(request):
    """Devuelve todos los préstamos. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)

    prestamos = Prestamo.objects.select_related('libro', 'universitario__usuario').all().order_by('-is_activo', '-fch_prestamo')
    data = [prestamo_serializer(p) for p in prestamos]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def get_user_loans(request, user_id):
    """Devuelve los préstamos de un usuario específico."""
    if not is_bibliotecario(request.user) and request.user.pk != user_id:
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)

    try:
        universitario = Universitario.objects.get(usuario_id=user_id)
    except Universitario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Perfil de universitario no encontrado.'}, status=404)
        
    prestamos = Prestamo.objects.filter(universitario=universitario).select_related('libro', 'universitario__usuario').order_by('-is_activo', '-fch_prestamo')
    data = [prestamo_serializer(p) for p in prestamos]
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def add_loan(request):
    """Registra un nuevo préstamo (Sin modificar el stock total del libro)."""
    try:
        data = json.loads(request.body)
        libro_id = data.get('libro_id')
        universitario_id = data.get('universitario_id')
        fch_prestamo_str = data.get('fch_prestamo')
        fch_devolucion_str = data.get('fch_devolucion')
        
        if not all([libro_id, universitario_id, fch_prestamo_str, fch_devolucion_str]):
            return JsonResponse({'success': False, 'message': 'Faltan datos.'}, status=400)

        if not is_bibliotecario(request.user) and request.user.pk != universitario_id:
            return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
        
        libro = Libro.objects.get(pk=libro_id)
        universitario = Universitario.objects.get(usuario_id=universitario_id)
        
        if Prestamo.objects.filter(libro=libro, is_activo=True, universitario=universitario).exists():
             return JsonResponse({'success': False, 'message': 'El usuario ya tiene prestado este libro.'}, status=400)

        prestados_actualmente = Prestamo.objects.filter(libro=libro, is_activo=True).count()
        
        if prestados_actualmente >= libro.cantidad:
            return JsonResponse({'success': False, 'message': 'No quedan copias disponibles.'}, status=400)

        fch_prestamo = datetime.strptime(fch_prestamo_str, '%Y-%m-%d').date()
        fch_devolucion = datetime.strptime(fch_devolucion_str, '%Y-%m-%d').date()
        
        if fch_devolucion < fch_prestamo:
            return JsonResponse({'success': False, 'message': 'Fecha de devolución inválida.'}, status=400)

        with transaction.atomic():
            Prestamo.objects.create(
                libro=libro,
                universitario=universitario,
                fch_prestamo=fch_prestamo,
                fch_devolucion=fch_devolucion,
                is_activo=True
            )
        
        log_auditoria(request.user.id, 'PRESTAMO_ADD', 'Prestamo', f'Préstamo de {libro.titulo} a {universitario.usuario.username}.')

        return JsonResponse({'success': True, 'message': 'Préstamo registrado exitosamente.'}, status=201)

    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'message': 'Libro o Usuario no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def return_loan(request, prestamo_id):
    """Registra la devolución (Solo cambia el estado del préstamo)."""
    try:
        prestamo = Prestamo.objects.get(pk=prestamo_id)

        if not is_bibliotecario(request.user) and prestamo.universitario.usuario != request.user:
            return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)

        if not prestamo.is_activo:
            return JsonResponse({'success': False, 'message': 'Este préstamo ya fue devuelto.'}, status=400)

        prestamo.is_activo = False
        prestamo.fch_devolucion_real = date.today()
        prestamo.save()
        
        log_auditoria(request.user.id, 'PRESTAMO_RETURN', 'Prestamo', f'Devolución ID {prestamo.id}.')

        return JsonResponse({'success': True, 'message': 'Libro devuelto exitosamente.'})

    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Préstamo no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_loan(request, prestamo_id):
    """Elimina un registro de préstamo. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)

    try:
        loan = Prestamo.objects.get(pk=prestamo_id)

        with transaction.atomic():
            if loan.is_activo:
                libro = loan.libro
                libro.cantidad = F('cantidad') + 1
                libro.save(update_fields=['cantidad'])
                libro.refresh_from_db()
                
            loan_id = loan.pk
            loan.delete()
        
        log_auditoria(request.user.id, 'PRESTAMO_DEL', 'Prestamo', f'Préstamo ID {loan_id} eliminado (Forzado).')
        return JsonResponse({'success': True, 'message': 'Préstamo eliminado exitosamente.'})
    
    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Préstamo no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno del servidor: {str(e)}'}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def edit_book(request, libro_id):
    """Edita un libro existente. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
    
    try:
        libro = Libro.objects.get(pk=libro_id)
        data = json.loads(request.body)
        
        libro.titulo = data.get('titulo', libro.titulo)
        libro.autor = data.get('autor', libro.autor)
        libro.genero = data.get('genero', libro.genero)
        libro.isbn = data.get('isbn', libro.isbn)
        
        if 'cantidad' in data:
             libro.cantidad = int(data['cantidad'])

        libro.save()
        
        log_auditoria(request.user.id, 'LIBRO_EDIT', 'Libro', f'Libro {libro.titulo} editado.')
        return JsonResponse({'success': True, 'message': 'Libro actualizado exitosamente.'})

    except Libro.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Libro no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al editar: {str(e)}'}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def edit_user(request, user_id):
    """Edita un usuario existente. Solo para bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
    
    try:
        target_user = User.objects.get(pk=user_id)
        data = json.loads(request.body)
        
        full_name = data.get('name', '').strip()
        if full_name:
            parts = full_name.split(' ')
            target_user.first_name = parts[0]
            target_user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        if 'email' in data:
            target_user.email = data['email']
            
        target_user.save()

        if Universitario.objects.filter(usuario=target_user).exists():
            uni = Universitario.objects.get(usuario=target_user)
            if 'doc' in data:
                uni.doc = data['doc']
                uni.save()

        log_auditoria(request.user.id, 'USER_EDIT', 'User', f'Usuario {target_user.username} editado.')
        return JsonResponse({'success': True, 'message': 'Usuario actualizado exitosamente.'})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al editar: {str(e)}'}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def edit_loan(request, prestamo_id):
    """Edita un préstamo activo (ej: extender fecha). Solo bibliotecarios."""
    if not is_bibliotecario(request.user):
        return JsonResponse({'success': False, 'message': 'Permiso denegado.'}, status=403)
    
    try:
        loan = Prestamo.objects.get(pk=prestamo_id)
        data = json.loads(request.body)
        
        if 'fch_prestamo' in data:
            loan.fch_prestamo = datetime.strptime(data['fch_prestamo'], '%Y-%m-%d').date()
        if 'fch_devolucion' in data:
            loan.fch_devolucion = datetime.strptime(data['fch_devolucion'], '%Y-%m-%d').date()
            
        if 'universitario_id' in data and data['universitario_id']:
            from .models import Universitario
            uni = Universitario.objects.get(usuario_id=data['universitario_id'])
            loan.universitario = uni

        loan.save()
        
        log_auditoria(request.user.id, 'LOAN_EDIT', 'Prestamo', f'Préstamo ID {loan.id} editado.')
        return JsonResponse({'success': True, 'message': 'Préstamo actualizado exitosamente.'})

    except Prestamo.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Préstamo no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al editar: {str(e)}'}, status=500)

