from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario
import qrcode
from io import BytesIO
import base64

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_active', 'qr_code_preview')
    list_filter = ('tipo_usuario', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('tipo_usuario', 'telefono', 'foto', 'is_first_login', 'qr_token')
        }),
    )
    readonly_fields = ('qr_token', 'qr_code_image')
    
    def save_model(self, request, obj, form, change):
        # Si es un nuevo usuario, generar contraseña temporal
        if not change:
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
