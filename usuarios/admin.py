from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario
import qrcode
from io import BytesIO
import base64
from django import forms

# ↓↓↓ FORMULARIO PERSONALIZADO PARA AÑADIR USUARIOS ↓↓↓
class UsuarioCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        required=False
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'facultad', 'telefono']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        # Si ambos campos están vacíos, no hay problema (se generará contraseña automática)
        if not password1 and not password2:
            return password2
            
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["password1"]:
            user.set_password(self.cleaned_data["password1"])
        elif not user.password:
            # Generar contraseña automática si no se proporcionó
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            user.set_password(temp_password)
        
        if commit:
            user.save()
        return user

# ↓↓↓ FORMULARIO PERSONALIZADO PARA EDITAR USUARIOS ↓↓↓
class UsuarioChangeForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que el campo facultad no sea requerido inicialmente
        self.fields['facultad'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')
        facultad = cleaned_data.get('facultad')
        
        # Validaciones específicas
        if tipo_usuario in ['docente', 'estudiante'] and not facultad:
            self.add_error('facultad', 'La facultad es obligatoria para docentes y estudiantes')
        
        if tipo_usuario == 'admin' and facultad:
            cleaned_data['facultad'] = None
        
        return cleaned_data

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'facultad_display', 'is_active', 'qr_code_preview')
    list_filter = ('tipo_usuario', 'facultad', 'is_active', 'is_staff')
    
    # ↓↓↓ CAMPOS PARA EDITAR USUARIO EXISTENTE ↓↓↓
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
        ('Información adicional', {'fields': ('tipo_usuario', 'telefono', 'foto', 'facultad', 'is_first_login', 'qr_token')}),
    )
    
    # ↓↓↓ CAMPOS PARA AÑADIR NUEVO USUARIO ↓↓↓
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 
                      'tipo_usuario', 'facultad', 'telefono'),
        }),
    )
    
    readonly_fields = ('qr_token', 'qr_code_image', 'last_login', 'date_joined')
    
    # ↓↓↓ MOSTRAR FACULTAD EN LISTA ↓↓↓
    def facultad_display(self, obj):
        return obj.facultad_display
    facultad_display.short_description = 'Facultad'
    
    def save_model(self, request, obj, form, change):
        # Validar facultad según tipo de usuario
        if obj.tipo_usuario == 'admin':
            obj.facultad = None
        elif obj.tipo_usuario in ['docente', 'estudiante'] and not obj.facultad:
            # Asignar una facultad por defecto si es necesario
            obj.facultad = 'ingenieria'
        
        # Si es un nuevo usuario y no tiene contraseña, generar una temporal
        if not change and not obj.password:
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            obj.set_password(temp_password)
        
        super().save_model(request, obj, form, change)
    
    def qr_code_preview(self, obj):
        if obj.qr_token:
            # Generar código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=2,
            )
            qr.add_data(obj.qr_token)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64 para mostrar en admin
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return format_html('<img src="data:image/png;base64,{}" width="50" height="50" />', img_str)
        return "No disponible"
    
    qr_code_preview.short_description = 'Código QR'
    
    def qr_code_image(self, obj):
        return self.qr_code_preview(obj)
    
    qr_code_image.short_description = 'Imagen QR'