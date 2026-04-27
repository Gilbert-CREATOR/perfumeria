from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('registro/', views.registro_usuario, name='register'),
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
    path('perfil/', views.perfil, name='perfil'),
    
    # 🔄 Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='usuarios/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='usuarios/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='usuarios/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/password_reset_complete.html'),
         name='password_reset_complete'),
]
