"""
Configuración de PayPal para Perfumería D.A.R.C.Y.
"""

import os
import paypalrestsdk

def configure_paypal():
    """
    Configura el SDK de PayPal según el entorno
    """
    from django.conf import settings
    
    # Configurar modo (sandbox o live)
    paypal_mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')
    paypal_client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
    paypal_secret = getattr(settings, 'PAYPAL_SECRET', '')
    
    if not paypal_client_id or not paypal_secret:
        print("⚠️ PayPal no configurado: CLIENT_ID o SECRET faltantes")
        return False
    
    # Configurar SDK
    paypalrestsdk.configure({
        "mode": paypal_mode,
        "client_id": paypal_client_id,
        "client_secret": paypal_secret
    })
    
    print(f"✅ PayPal configurado en modo: {paypal_mode}")
    return True

def get_paypal_mode():
    """Retorna el modo actual de PayPal"""
    from django.conf import settings
    return getattr(settings, 'PAYPAL_MODE', 'sandbox')

def is_paypal_configured():
    """Verifica si PayPal está configurado"""
    from django.conf import settings
    client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
    secret = getattr(settings, 'PAYPAL_SECRET', '')
    return bool(client_id and secret)

# URLs de PayPal según el modo
PAYPAL_URLS = {
    'sandbox': {
        'approval_url': 'https://www.sandbox.paypal.com/cgi-bin/webscr',
        'api_url': 'https://api.sandbox.paypal.com'
    },
    'live': {
        'approval_url': 'https://www.paypal.com/cgi-bin/webscr',
        'api_url': 'https://api.paypal.com'
    }
}

def get_paypal_urls():
    """Retorna las URLs de PayPal según el modo"""
    mode = get_paypal_mode()
    return PAYPAL_URLS.get(mode, PAYPAL_URLS['sandbox'])
