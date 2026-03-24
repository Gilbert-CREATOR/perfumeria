#!/bin/bash

# 🚀 Script de Build para Deploy en Render - Perfumería D.A.R.C.Y.

echo "🌸 Iniciando build de Perfumería D.A.R.C.Y..."

# Activar virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "⚠️ No se encontró el virtualenv, creando uno..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Actualizar pip e instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p media logs staticfiles

# Collect static files
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Migraciones de base de datos
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

# Crear perfiles para usuarios existentes
echo "👥 Creando perfiles de usuario..."
python manage.py crear_perfiles

# Test de configuración
echo "🧪 Verificando configuración..."
python manage.py check --deploy

echo "✅ Build completado exitosamente!"
echo "🌸 Perfumería D.A.R.C.Y. lista para deploy"

echo "👤 Creando superusuario automático..."

# Crear/actualizar superusuario automáticamente
python manage.py shell << END
from django.contrib.auth.models import User

username = "admin"
email = "admin@darcy.com"
password = "Admin12"

# get_or_create asegura que exista
user, created = User.objects.get_or_create(username=username)

# Siempre actualiza email, contraseña y permisos
user.email = email
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.save()
print("✅ Superusuario actualizado o creado correctamente")
END