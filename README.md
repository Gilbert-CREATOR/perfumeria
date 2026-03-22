# 🌸 Perfumería D.A.R.C.Y.

Sistema completo de e-commerce para perfumería con diseño minimalista y funcionalidades avanzadas.

## 🎯 Características Principales

### 🛒 Sistema de Carrito
- Carrito de compras funcional con AJAX
- Agregar/eliminar productos dinámicamente
- Contador de items en tiempo real
- Validación de stock automática

### 💳 Proceso de Checkout
- Formulario de checkout completo
- Múltiples métodos de pago (PayPal, Stripe, Transferencia, Efectivo)
- Cálculo automático de envío
- Confirmación de pedido con email

### 👥 Gestión de Usuarios
- Sistema de roles (Admin/Empleado/Cliente)
- Panel de control personalizado
- Historial de pedidos completo
- Perfiles de usuario detallados

### 📊 Panel Administrativo
- Gestión completa de empleados
- Estadísticas del sistema
- Debug tools para administración
- Acceso restringido por roles

### 🎨 Diseño Minimalista
- Estilo D.A.R.C.Y. único y elegante
- Fully responsive para todos los dispositivos
- Animaciones sutiles y modernas
- Experiencia de usuario optimizada

## 🚀 Tecnologías Utilizadas

- **Backend**: Django 4.2
- **Frontend**: HTML5, CSS3, JavaScript (ES5)
- **Database**: SQLite (desarrollo)
- **Styling**: CSS Grid, Flexbox
- **AJAX**: Fetch API
- **Authentication**: Django Auth System

## 📁 Estructura del Proyecto

```
perfumeria/
├── apps/
│   ├── carrito/              # Sistema principal de carrito
│   ├── productos/           # Gestión de productos
│   └── usuarios/            # Gestión de usuarios
├── templates/              # Templates HTML
├── static/                  # Archivos estáticos
├── media/                   # Archivos multimedia
├── perfumeria/              # Configuración Django
└── requirements.txt        # Dependencias Python
```

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/Gilbert-CREATOR/perfumeria.git
cd perfumeria
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear superusuario
```bash
python manage.py createsuperuser
```

### 6. Iniciar servidor
```bash
python manage.py runserver
```

## 👤 Roles del Sistema

### 🔑 Administrador
- Acceso completo al sistema
- Puede agregar/editar/eliminar empleados
- Acceso a estadísticas y debug tools
- Gestión total de usuarios y pedidos

### 👤 Empleado
- Puede ver todos los pedidos del sistema
- Acceso a estadísticas del negocio
- Gestión de operaciones diarias
- No puede agregar otros empleados

### 🛍️ Cliente
- Solo puede ver y gestionar sus propios datos
- Carrito de compras personal
- Historial de pedidos propio
- Proceso de checkout completo

## 🌐 Rutas Principales

### Clientes
- `/` - Catálogo de productos
- `/carrito/` - Carrito de compras
- `/carrito/checkout/` - Proceso de pago
- `/carrito/historial/` - Historial de pedidos

### Administración
- `/carrito/panel/` - Panel de control
- `/carrito/empleados/` - Gestión de empleados
- `/carrito/admin/usuarios/` - Todos los usuarios
- `/carrito/debug/` - Herramientas de debug

## 🎨 Características de Diseño

- **Minimalista**: Limpio, elegante y funcional
- **Responsive**: Perfecto en todos los dispositivos
- **Moderno**: Animaciones sutiles y transiciones suaves
- **Accesible**: Navegación intuitiva y clara
- **Profesional**: Imagen corporativa consistente

## 📱 Responsive Design

- **Desktop**: Experiencia completa con todas las funcionalidades
- **Tablet**: Interfaz adaptada con touch-friendly elements
- **Mobile**: Versión optimizada para pantallas pequeñas

## 🔐 Seguridad

- Sistema de autenticación robusto
- Roles y permisos diferenciados
- Protección CSRF en todos los formularios
- Validación de datos en frontend y backend
- Acceso restringido a rutas sensibles

## 📊 Estadísticas y Reportes

- Ventas totales por período
- Productos más vendidos
- Análisis de rentabilidad
- Exportación a CSV/Excel
- Métricas de usuario en tiempo real

## 🚀 Deploy

El proyecto está listo para deploy en:
- **Heroku**: Configurado con Procfile
- **DigitalOcean**: Optimizado para producción
- **Vercel**: Compatible con serverless
- **AWS**: Escalable y seguro

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit los cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📧 Contacto

- **GitHub**: [@Gilbert-CREATOR](https://github.com/Gilbert-CREATOR)
- **Proyecto**: [Perfumería D.A.R.C.Y.](https://github.com/Gilbert-CREATOR/perfumeria)

---

⭐ **Si te gusta el proyecto, no olvides darle una estrella!** ⭐
