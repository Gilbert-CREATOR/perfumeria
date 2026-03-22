# 🚀 Deploy en Render - Perfumería D.A.R.C.Y.

## 📋 Pasos para Deploy en Render

### 1. 🌐 Subir a GitHub
Asegúrate de que tu proyecto esté en GitHub:
```bash
git add .
git commit -m "Ready for Render deploy"
git push origin main
```

### 2. 🔗 Conectar con Render

#### Opción A: Web Dashboard
1. Ve a [render.com](https://render.com)
2. Crea cuenta o inicia sesión
3. Click en "New +" → "Web Service"
4. Conecta tu repositorio GitHub
5. Selecciona el repositorio `perfumeria`

#### Opción B: Auto-import
1. En GitHub, ve a tu repositorio
2. Click en "Settings" → "Integrations"
3. Agrega "Render"
4. Sigue las instrucciones

### 3. ⚙️ Configuración del Web Service

#### Basic Settings:
- **Name**: `perfumeria-darcy`
- **Environment**: `Python 3`
- **Region**: El más cercano a tus usuarios
- **Branch**: `main`

#### Build Settings:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn perfumeria.wsgi:application`

#### Advanced Settings:
- **Auto-Deploy**: ✅ Enabled
- **Health Check Path**: `/`

### 4. 🗄️ Configurar Base de Datos

1. **Add New** → **PostgreSQL**
2. **Name**: `perfumeria-db`
3. **Plan**: Free
4. **Region**: Same as web service

### 5. 🔧 Environment Variables

Configura estas variables en el Web Service:

#### Django Essentials:
```
DJANGO_SETTINGS_MODULE=perfumeria.settings
SECRET_KEY=[generado automáticamente por Render]
DEBUG=False
ALLOWED_HOSTS=.onrender.com
```

#### Database:
```
DATABASE_URL=[conectar con la base de datos PostgreSQL]
```

#### Email (Opcional):
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

#### PayPal (Opcional):
```
PAYPAL_CLIENT_ID=tu-client-id-paypal
PAYPAL_SECRET=tu-secret-paypal
```

### 6. 📁 Static Files

Agrega este Build Command:
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

Y configura:
- **Static File Directory**: `staticfiles`
- **Mount Path**: `/static`

### 7. 🚀 Deploy

1. **Save** la configuración
2. **Manual Deploy** → "Build and Deploy"
3. Espera a que termine el build

## 🔧 Archivos de Configuración

### `render.yaml` (Opcional)
```yaml
services:
  - type: web
    name: perfumeria-darcy
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn perfumeria.wsgi:application
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: DJANGO_SETTINGS_MODULE
        value: perfumeria.settings
      - key: DEBUG
        value: false
      - key: ALLOWED_HOSTS
        value: .onrender.com
    staticDir: staticfiles
    mountPath: /static
```

### `Procfile`
```
web: gunicorn perfumeria.wsgi:application
```

## 🎯 URL Final

Tu aplicación estará disponible en:
```
https://perfumeria-darcy.onrender.com
```

## 🔍 Verificación

### 1. Health Check
Visita la URL y verifica que:
- ✅ La página carga correctamente
- ✅ Los archivos estáticos (CSS, JS) cargan
- ✅ El carrito funciona
- ✅ El proceso de checkout funciona

### 2. Admin Access
1. Crea un superusuario:
   ```bash
   # En el Render Shell
   python manage.py createsuperuser
   ```
2. Accede a `/admin/`

### 3. Test Features
- 🛒 Agregar productos al carrito
- 💳 Proceso de checkout
- 👥 Registro de usuarios
- 📊 Panel de administración

## ⚠️ Troubleshooting

### Common Issues:

#### 1. Static Files Not Loading
```bash
# Build Command actualizado
pip install -r requirements.txt && python manage.py collectstatic --noinput --clear
```

#### 2. Database Connection
- Verifica que `DATABASE_URL` esté configurada correctamente
- Asegúrate de que la base de datos PostgreSQL esté corriendo

#### 3. ALLOWED_HOSTS Error
- Configura `ALLOWED_HOSTS=.onrender.com`
- O usa tu dominio personalizado

#### 4. Import Errors
- Verifica `requirements.txt`
- Asegúrate de que todas las dependencias estén incluidas

## 🔄 Auto-Deploy

Con auto-deploy habilitado:
- Cada `git push` al branch `main`
- Triggerá un nuevo deploy automáticamente
- El sitio se actualizará sin intervención manual

## 📊 Monitoring

Render incluye:
- 📈 **Logs** en tiempo real
- 🔍 **Metrics** de rendimiento
- 💰 **Usage statistics**
- 📧 **Alerts** por email

## 🎉 Post-Deploy

Una vez en producción:
1. 📧 **Configura email** para notificaciones
2. 💰 **Configura PayPal** para pagos reales
3. 📊 **Monitorea** el rendimiento
4. 🔒 **Configura HTTPS** (incluido por defecto)
5. 📱 **Test en móvil** y tablet

---

**¡Tu perfumería D.A.R.C.Y. estará en producción en minutos!** 🌸✨
