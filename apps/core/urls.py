from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('emergencia-admin/', views.emergencia_admin, name='emergencia_admin'),
    path('crear-usuario-emergencia/', views.crear_usuario_emergencia, name='crear_usuario_emergencia'),
]
