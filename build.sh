#!/bin/bash

# 🚀 Build & Deploy Script para Render - Perfumería D.A.R.C.Y.

echo "🌸 Iniciando build de Perfumería D.A.R.C.Y..."

# 🔹 Activar virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "⚠️ No se encontró el virtualenv, creando uno..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 🔹 Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 🔹 Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p media logs staticfiles

# 🔹 Migraciones de base de datos
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

# 🔹 Crear productos de ejemplo
echo "�️ Creando productos de ejemplo..."
python manage.py crear_productos

# 🔹 Crear superusuario administrador
echo "� Creando superusuario administrador..."
python manage.py crear_admin

# 🔹 Collect static files
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear
user, created = User.objects.get_or_create(username=username)
user.email = email
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.save()

print("✅ Superusuario actualizado o creado correctamente")
END

# 🔹 Test de configuración
echo "🧪 Verificando configuración..."
python manage.py check --deploy

echo "✅ Build completado exitosamente!"
echo "🌸 Perfumería D.A.R.C.Y. lista para deploy"