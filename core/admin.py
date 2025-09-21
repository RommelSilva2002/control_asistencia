from django.contrib import admin
from .models import Asistencia

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'hora_entrada', 'hora_salida')
    list_filter = ('fecha', 'usuario__tipo_usuario')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    date_hierarchy = 'fecha'
