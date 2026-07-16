from django.urls import path

from . import views


app_name = 'newsletter'

urlpatterns = [
    path('suscribirse/', views.suscribirse, name='suscribirse'),
    path('cancelar/<uuid:token>/', views.cancelar_confirmacion, name='cancelar'),
    path('cancelar/<uuid:token>/confirmar/', views.cancelar, name='cancelar_confirmar'),
]
