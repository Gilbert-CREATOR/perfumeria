#!/bin/bash

# 🚀 Script de Build para Deploy en Render - Perfumería D.A.R.C.Y.

echo "🌸 Iniciando build de Perfumería D.A.R.C.Y..."

# Instalar dependencias
echo "📦 Instalando dependencias..."
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

# Crear superusuario si no existe (solo para desarrollo)
if [ "$RENDER" != "true" ]; then
    echo "👤 Creando superusuario de desarrollo..."
    python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
else:
    print('✅ Superusuario ya existe')
EOF
fi

# Crear perfiles para usuarios existentes
echo "👥 Creando perfiles de usuario..."
python manage.py crear_perfiles

# Test de configuración
echo "🧪 Verificando configuración..."
python manage.py check --deploy

echo "✅ Build completado exitosamente!"
echo "🌸 Perfumería D.A.R.C.Y. lista para deploy"
