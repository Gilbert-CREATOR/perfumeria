# Despliegue seguro en Render

El proyecto usa `perfumeria.settings_prod`, Python 3.12.12 y una base PostgreSQL
externa de Neon. Ninguna contraseña debe escribirse en este repositorio.

## Variables secretas en Render

En **Web Service > Environment** agrega:

```text
DATABASE_URL=<cadena pooled de Neon>
SECRET_KEY=<cadena aleatoria larga>
DJANGO_SUPERUSER_EMAIL=<correo del administrador>
DJANGO_SUPERUSER_PASSWORD=<contraseña robusta>
BREVO_API_KEY=<api key de Brevo>
PAYPAL_CLIENT_ID=<credencial de PayPal>
PAYPAL_SECRET=<secreto de PayPal>
PAYPAL_WEBHOOK_ID=<id del webhook verificado>
```

Las demás variables no secretas están documentadas en `render.yaml`. Para correo
en una instancia gratuita se recomienda Brevo por HTTPS; el SMTP de Gmail puede
estar bloqueado por la red del proveedor.

## Base de datos Neon

1. Copia la URL **pooled** desde Neon.
2. Guárdala como `DATABASE_URL` únicamente en Render.
3. Mantén `sslmode=require`.
4. Rota la contraseña si fue pegada en un chat, captura o archivo.

`build.sh` instala dependencias, aplica migraciones, sincroniza el administrador,
recolecta estáticos y ejecuta `check --deploy`. No crea productos de muestra en
producción.

## PayPal

Configura el webhook en PayPal hacia:

```text
https://perfumeria-darcy.onrender.com/carrito/paypal/webhook/
```

La aplicación rechaza callbacks no verificados. No actives PayPal en vivo hasta
configurar las tres credenciales anteriores y probar un pago sandbox completo.

## Mantenimiento

Ejecuta periódicamente desde un trabajo programado u operación administrativa:

```bash
python manage.py liberar_reservas_vencidas
```

La aplicación también libera lotes pequeños al abrir el carrito o checkout, por
lo que las reservas no quedan bloqueadas si no hay un cron disponible.

## Comprobación posterior

- Abre `/admin/diagnostico/` y envía un correo de prueba.
- Revisa `/admin/auditoria/` y `/admin/stock/movimientos/`.
- Realiza un pedido sandbox y confirma que la notificación PayPal lo marca pagado.
- Cancela otro pedido y verifica que el stock se reintegra una sola vez.
