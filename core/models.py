from django.db import models
from usuarios.models import Usuario

class Asistencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateField()  # REMOVER auto_now_add=True aquí
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['usuario', 'fecha']
        ordering = ['-fecha', '-hora_entrada']
    
    def __str__(self):
        return f"{self.usuario} - {self.fecha}"
    
    def save(self, *args, **kwargs):
        # Si es un nuevo registro y no tiene fecha, usar la fecha actual
        if not self.fecha:
            from django.utils import timezone
            self.fecha = timezone.now().date()
        super().save(*args, **kwargs)
