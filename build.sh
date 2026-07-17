#!/bin/bash

set -euo pipefail

echo "🌸 Iniciando build de Perfumería D.A.R.C.Y..."

echo "📦 Instalando dependencias..."
python -m pip install -r requirements.txt

# 🔹 Migraciones de base de datos
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

echo "🔐 Sincronizando administrador..."
python manage.py sync_admin

# 🔹 Collect static files
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# 🔹 Test de configuración
echo "🧪 Verificando configuración..."
python manage.py check --deploy

echo "✅ Build completado exitosamente!"
echo "🌸 Perfumería D.A.R.C.Y. lista para deploy"
