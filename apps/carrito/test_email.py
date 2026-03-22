"""
Test de configuración de email para Perfumería D.A.R.C.Y.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def test_email_configuration():
    """
    Prueba la configuración de email enviando un email de prueba
    """
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
        
        # Enviar email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        print("✅ Email de prueba enviado exitosamente a gilbertandeliz04@gmail.com")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email de prueba: {str(e)}")
        return False

def test_email_template():
    """
    Prueba el envío de email con template HTML
    """
    try:
        from django.template import Context
        from django.template.loader import get_template
        
        # Datos de prueba
        context = {
            'pedido_id': 'TEST-001',
            'cliente_nombre': 'Cliente de Prueba',
            'total': 100.00,
            'productos': ['Perfume Test 1', 'Perfume Test 2']
        }
        
        subject = '🧪 Test de Email con Template - Perfumería D.A.R.C.Y.'
        
        # Renderizar template (si existe)
        try:
            html_message = render_to_string('emails/pedido_confirmado_test.html', context)
        except:
            html_message = None
        
        # Enviar email
        send_mail(
            subject=subject,
            message=f"Este es un email de prueba con template. Pedido: {context['pedido_id']}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['gilbertandeliz04@gmail.com'],
            html_message=html_message,
            fail_silently=False,
        )
        
        print("✅ Email con template enviado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email con template: {str(e)}")
        return False

if __name__ == '__main__':
    print("🧪 Iniciando pruebas de email...")
    
    # Test 1: Email básico
    test_email_configuration()
    
    # Test 2: Email con template
    test_email_template()
    
    print("🎯 Pruebas de email completadas")
