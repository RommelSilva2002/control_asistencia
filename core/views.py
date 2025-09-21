from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from .models import Asistencia
from usuarios.models import Usuario
from datetime import datetime

@login_required
def dashboard(request):
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    

    hoy = datetime.now().date()
    
    # Estadísticas para el dashboard
    if request.user.tipo_usuario == 'admin':
        total_usuarios = Usuario.objects.count()
        total_docentes = Usuario.objects.filter(tipo_usuario='docente').count()
        total_estudiantes = Usuario.objects.filter(tipo_usuario='estudiante').count()
        
        # Asistencias de hoy
        asistencias_hoy = Asistencia.objects.filter(fecha=hoy)
        presentes_hoy = asistencias_hoy.count()
        
        context = {
            'total_usuarios': total_usuarios,
            'total_docentes': total_docentes,
            'total_estudiantes': total_estudiantes,
            'presentes_hoy': presentes_hoy,
        }
    else:
        # Obtener las asistencias del usuario actual
        asistencias = Asistencia.objects.filter(usuario=request.user).order_by('-fecha')[:10]
        context = {
            'asistencias': asistencias,
        }
    
    return render(request, 'core/dashboard.html', context)

def registrar_asistencia(request, token):
    try:
        # Buscar usuario por token QR
        usuario = Usuario.objects.get(qr_token=token)
    except Usuario.DoesNotExist:
        error_msg = "Token inválido o usuario no encontrado"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'error': error_msg}, status=400)
        return render(request, 'core/registro_asistencia.html', {
            'error': error_msg,
            'mensaje': 'El código QR no es válido o ha expirado.'
        })
    
    ahora = datetime.now()
    hoy = ahora.date()
    hora_actual = ahora.time()
    
    # USAR TRANSACCIÓN ATÓMICA PARA EVITAR CONDITIONS RACE
    try:
        with transaction.atomic():
            # Intentar obtener un registro existente para hoy
            asistencia = Asistencia.objects.select_for_update().get(
                usuario=usuario, 
                fecha=hoy
            )
            
            # Si existe pero no tiene hora de salida, registrar salida
            if not asistencia.hora_salida:
                asistencia.hora_salida = hora_actual
                asistencia.save()
                mensaje = f"Salida registrada para {usuario.get_full_name()}"
                tipo = "salida"
            else:
                # Ya tiene entrada y salida registradas
                mensaje = f"Ya tiene registrada entrada y salida para hoy"
                tipo = "completo"
                
    except Asistencia.DoesNotExist:
        # No existe registro para hoy, crear uno nuevo
        try:
            with transaction.atomic():
                asistencia = Asistencia.objects.create(
                    usuario=usuario,
                    fecha=hoy,
                    hora_entrada=hora_actual
                )
                mensaje = f"Entrada registrada para {usuario.get_full_name()}"
                tipo = "entrada"
                
        except IntegrityError:
            # Si hay error de integridad, significa que otro proceso creó el registro
            # simultáneamente, así que lo buscamos y manejamos
            asistencia = Asistencia.objects.get(usuario=usuario, fecha=hoy)
            if not asistencia.hora_salida:
                asistencia.hora_salida = hora_actual
                asistencia.save()
                mensaje = f"Salida registrada para {usuario.get_full_name()}"
                tipo = "salida"
            else:
                mensaje = f"Ya tiene registrada entrada y salida para hoy"
                tipo = "completo"
    
    # Preparar datos para la respuesta
    response_data = {
        'status': 'success',
        'message': mensaje,
        'tipo': tipo,
        'usuario': usuario.get_full_name(),
        'fecha': hoy.strftime('%d/%m/%Y'),
        'hora_actual': hora_actual.strftime('%H:%M:%S'),
        'hora_entrada': asistencia.hora_entrada.strftime('%H:%M:%S') if asistencia.hora_entrada else None,
        'hora_salida': asistencia.hora_salida.strftime('%H:%M:%S') if asistencia.hora_salida else None
    }
    
    # Respuesta JSON para aplicaciones que escanean el QR
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse(response_data)
    
    # Para navegadores, mostrar página HTML
    context = {
        'mensaje': mensaje,
        'usuario': usuario,
        'fecha': hoy,
        'hora_actual': ahora,
        'hora_entrada': asistencia.hora_entrada,
        'hora_salida': asistencia.hora_salida,
        'tipo': tipo
    }
    
    return render(request, 'core/registro_asistencia.html', context)
