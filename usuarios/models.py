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
    
     # Opciones para el campo facultad
    FACULTADES = [
        ('', '-- Seleccione Facultad --'),
        ('FIE', 'Facultad de Informática y Electrónica'),
        ('FADE', 'Facultad Administración de Empresas'),
        ('FCS', 'Facultad de Ciencias'),
        ('FCP', 'Facultad de Ciencias Pecuarias'),
        ('FME', 'Facultad de Mecánica'),
        ('FNR', 'Facultad de Recursos Naturales'),
        ('FSP', 'Facultad de Salud Pública'),
    ]
    
    
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO, default='estudiante')
    telefono = models.CharField(max_length=15, blank=True)
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    is_first_login = models.BooleanField(default=True)
    qr_token = models.CharField(max_length=50, unique=True, blank=True)
    
    facultad = models.CharField(
        max_length=20, 
        choices=FACULTADES, 
        blank=True, 
        null=True,
        verbose_name='Facultad'
    )

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

    def clean(self):
            from django.core.exceptions import ValidationError
            
            # Si es docente o estudiante, facultad es obligatoria
            if self.tipo_usuario in ['docente', 'estudiante'] and not self.facultad:
                raise ValidationError({'facultad': 'La facultad es obligatoria para docentes y estudiantes'})
            
            # Si es admin, no debe tener facultad
            if self.tipo_usuario == 'admin' and self.facultad:
                self.facultad = None
    
    @property
    def facultad_display(self):
        if self.facultad:
            return dict(self.FACULTADES).get(self.facultad, '')
        return 'No asignada'