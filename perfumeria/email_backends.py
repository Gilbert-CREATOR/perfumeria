import json
import logging
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """Envía los EmailMessage de Django mediante la API HTTPS de Brevo."""

    endpoint = 'https://api.brevo.com/v3/smtp/email'

    def __init__(self, *args, api_key=None, timeout=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key or getattr(settings, 'BREVO_API_KEY', '')
        self.timeout = timeout or getattr(settings, 'EMAIL_TIMEOUT', 15)

    @staticmethod
    def _address(value):
        name, email = parseaddr(value or '')
        result = {'email': email or value}
        if name:
            result['name'] = name
        return result

    def _payload(self, message):
        sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '').strip()
        sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'D.A.R.C.Y.').strip()
        if not sender_email:
            raise ValueError('BREVO_SENDER_EMAIL no está configurado.')

        html_content = ''
        for alternative in getattr(message, 'alternatives', ()):
            content, mimetype = alternative[0], alternative[1]
            if mimetype == 'text/html':
                html_content = content
                break

        payload = {
            'sender': {'name': sender_name, 'email': sender_email},
            'to': [self._address(address) for address in (message.to or [])],
            'subject': message.subject,
            'textContent': message.body or '',
        }
        if html_content:
            payload['htmlContent'] = html_content
        if message.cc:
            payload['cc'] = [self._address(address) for address in message.cc]
        if message.bcc:
            payload['bcc'] = [self._address(address) for address in message.bcc]
        if message.reply_to:
            payload['replyTo'] = self._address(message.reply_to[0])
        return payload

    def _send(self, message):
        if not message.recipients():
            return False
        if not self.api_key:
            raise ValueError('BREVO_API_KEY no está configurado.')
        if message.attachments:
            raise ValueError('El backend de Brevo todavía no admite archivos adjuntos.')

        request = Request(
            self.endpoint,
            data=json.dumps(self._payload(message)).encode('utf-8'),
            headers={
                'accept': 'application/json',
                'api-key': self.api_key,
                'content-type': 'application/json',
            },
            method='POST',
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError(f'Brevo respondió con HTTP {response.status}.')
        except HTTPError as error:
            detail = error.read().decode('utf-8', errors='replace')[:500]
            raise RuntimeError(f'Brevo rechazó el correo (HTTP {error.code}): {detail}') from error
        except URLError as error:
            raise RuntimeError(f'No se pudo conectar con la API de Brevo: {error.reason}') from error
        return True

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        sent = 0
        for message in email_messages:
            try:
                sent += int(self._send(message))
            except Exception:
                logger.exception('No se pudo enviar el correo transaccional mediante Brevo.')
                if not self.fail_silently:
                    raise
        return sent
