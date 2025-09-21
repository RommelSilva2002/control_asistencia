from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('registrar-asistencia/<str:token>/', views.registrar_asistencia, name='registrar_asistencia'),
]