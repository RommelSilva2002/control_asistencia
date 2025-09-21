from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .models import Usuario
from django.contrib.auth import logout
from .forms import LoginForm, UserUpdateForm


def login_personalizado(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Redirigir a cambio de contraseña si es primer inicio
                if user.is_first_login:
                    messages.info(request, 'Por favor, cambie su contraseña por seguridad.')
                    return redirect('cambiar_password')
                
                messages.success(request, f'Bienvenido {user.get_full_name()}')
                return redirect('perfil')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

@login_required
def perfil(request):
    from core.models import Asistencia
    from datetime import datetime

    hoy = datetime.now().date()
    asistencias_hoy = Asistencia.objects.filter(usuario=request.user, fecha=hoy).first()
    
    # Generar URL para el código QR
    qr_url = request.build_absolute_uri(f'/registrar-asistencia/{request.user.qr_token}/')
    
    context = {
        'asistencia_hoy': asistencias_hoy,
        'qr_url': qr_url,
    }
    return render(request, 'usuarios/perfil.html', context)

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'usuarios/editar_perfil.html', {'form': form})

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            # Marcar que ya no es el primer inicio
            if hasattr(user, 'is_first_login') and user.is_first_login:
                user.is_first_login = False
                user.save()
            
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'usuarios/cambiar_password.html', {
        'form': form
    })

def logout_personalizado(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    else:
        # Si se accede por GET, mostramos una página de confirmación
        return render(request, 'usuarios/confirmar_logout.html')