# Imagen base
FROM python:3.11-slim

# Evitar archivos .pyc y buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=perfumeria.settings_prod

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar proyecto
COPY . .

# Crear carpeta de static
RUN mkdir -p staticfiles

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 10000


# Comando final (🔥 clave: migraciones + servidor)
CMD ["sh", "-c", "python manage.py migrate && gunicorn perfumeria.wsgi:application --bind 0.0.0.0:10000"]