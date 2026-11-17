"""Django email backend for Brevo's transactional email API."""

import base64
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

from .email_limits import reserve_daily_email_slot


class BrevoEmailBackend(BaseEmailBackend):
    """Send Django messages through POST /v3/smtp/email over HTTPS."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '').strip()
        self.api_url = getattr(
            settings,
            'BREVO_API_URL',
            'https://api.brevo.com/v3/smtp/email',
        )
        self.timeout = getattr(settings, 'BREVO_API_TIMEOUT', 15)
        self.session = requests.Session()

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if self.fail_silently:
                return 0
            raise ImproperlyConfigured('BREVO_API_KEY is required to send email.')
        if not self.api_key.startswith('xkeysib-'):
            raise ImproperlyConfigured(
                'BREVO_API_KEY must be a Brevo API key starting with "xkeysib-"; '
                'do not use a Brevo SMTP key or a SendGrid key.'
            )

        self.session.headers.update({
            'api-key': self.api_key,
            'accept': 'application/json',
            'content-type': 'application/json',
        })
        sent = 0
        for message in email_messages:
            try:
                reserve_daily_email_slot(len(message.recipients()))
                response = self.session.post(
                    self.api_url,
                    json=self._build_payload(message),
                    timeout=self.timeout,
                )
                if response.status_code != 201:
                    raise RuntimeError(
                        f'Brevo transactional email returned HTTP '
                        f'{response.status_code}; expected 201: {response.text[:1000]}'
                    )
                sent += 1
            except (requests.RequestException, RuntimeError):
                if not self.fail_silently:
                    raise
        return sent

    @classmethod
    def _build_payload(cls, message):
        sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '')
        sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'UrbanThread')
        parsed_name, parsed_email = parseaddr(message.from_email or '')
        sender_email = sender_email or parsed_email or settings.DEFAULT_FROM_EMAIL
        sender_name = parsed_name or sender_name

        payload = {
            'sender': {'email': sender_email, 'name': sender_name},
            'to': cls._addresses(message.to),
            'subject': message.subject,
        }

        body_type = f'text/{message.content_subtype}'
        body = message.body
        for alternative in getattr(message, 'alternatives', []) or []:
            content, mimetype = cls._alternative_parts(alternative)
            if mimetype == 'text/html':
                body_type, body = mimetype, content
                break
        payload['htmlContent' if body_type == 'text/html' else 'textContent'] = body

        cc = cls._addresses(getattr(message, 'cc', []))
        bcc = cls._addresses(getattr(message, 'bcc', []))
        reply_to = cls._addresses(getattr(message, 'reply_to', []))
        if cc:
            payload['cc'] = cc
        if bcc:
            payload['bcc'] = bcc
        if reply_to:
            payload['replyTo'] = reply_to[0]

        attachments = cls._attachments(getattr(message, 'attachments', []))
        if attachments:
            payload['attachment'] = attachments
        return payload

    @staticmethod
    def _addresses(addresses):
        if isinstance(addresses, str):
            addresses = [addresses]
        result = []
        for address in addresses or []:
            name, email = parseaddr(address)
            if email:
                item = {'email': email}
                if name:
                    item['name'] = name
                result.append(item)
        return result

    @staticmethod
    def _alternative_parts(alternative):
        if hasattr(alternative, 'content') and hasattr(alternative, 'mimetype'):
            return alternative.content, alternative.mimetype
        return alternative[0], alternative[1]

    @staticmethod
    def _attachments(attachments):
        result = []
        for attachment in attachments or []:
            if hasattr(attachment, 'filename'):
                filename = attachment.filename
                content = attachment.content
            else:
                filename, content, _mimetype = attachment
            if isinstance(content, str):
                content = content.encode('utf-8')
            result.append({
                'name': filename,
                'content': base64.b64encode(content).decode('ascii'),
            })
        return result
