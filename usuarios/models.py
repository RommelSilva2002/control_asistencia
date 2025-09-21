from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
import secrets
import string

class Usuario(AbstractUser):
    TIPO_USUARIO = [
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
        ('estudiante', 'Estudiante'),
    ]
    
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO, default='estudiante')
    telefono = models.CharField(max_length=15, blank=True)
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    is_first_login = models.BooleanField(default=True)
    qr_token = models.CharField(max_length=50, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.qr_token:
            # Generar token único para QR
            self.qr_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
        
        # Si es un nuevo usuario, generar contraseña aleatoria
        if self._state.adding and not self.password:
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            self.set_password(temp_password)
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
