from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Probar la configuración de email'

    def handle(self, *args, **options):
        self.stdout.write("=" * 50)
        self.stdout.write("🧪 PRUEBA DE CONFIGURACIÓN DE EMAIL")
        self.stdout.write("=" * 50)
        
        # Test 1: Email básico
        self.stdout.write("\n1️⃣ Enviando email básico...")
        try:
            subject = '🧪 Test de Email - Perfumería D.A.R.C.Y.'
            message = '''
            Este es un email de prueba para verificar que la configuración SMTP funciona correctamente.
            
            Si recibes este email, significa que:
            ✅ El servidor SMTP está conectado
            ✅ Las credenciales son correctas
            ✅ El email puede enviarse exitosamente
            
            Sistema: Perfumería D.A.R.C.Y.
            Email de prueba enviado desde: {}
            '''.format(settings.EMAIL_HOST_USER)
            
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = ['gilbertandeliz04@gmail.com']
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            
            self.stdout.write("✅ Email básico enviado exitosamente")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al enviar email básico: {str(e)}"))
            return
        
        # Test 2: Email con template
        self.stdout.write("\n2️⃣ Enviando email con template...")
        try:
            context = {
                'pedido_id': 'TEST-001',
                'cliente_nombre': 'Cliente de Prueba',
                'total': 100.00,
                'productos': ['Perfume Test 1', 'Perfume Test 2']
            }
            
            subject = '🧪 Test de Email con Template - Perfumería D.A.R.C.Y.'
            
            html_message = render_to_string('emails/pedido_confirmado_test.html', context)
            
            send_mail(
                subject=subject,
                message=f"Este es un email de prueba con template. Pedido: {context['pedido_id']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['gilbertandeliz04@gmail.com'],
                html_message=html_message,
                fail_silently=False,
            )
            
            self.stdout.write("✅ Email con template enviado exitosamente")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al enviar email con template: {str(e)}"))
        
        # Mostrar configuración
        self.stdout.write("\n📋 Configuración actual:")
        self.stdout.write(f"   Email Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"   Email Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"   Email User: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"   Use TLS: {settings.EMAIL_USE_TLS}")
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("🎯 Pruebas completadas")
        self.stdout.write("📧 Revisa tu bandeja de entrada: gilbertandeliz04@gmail.com")
        self.stdout.write("=" * 50)
