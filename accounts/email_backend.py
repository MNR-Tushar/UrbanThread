"""Django email backend that sends mail through SendGrid's HTTPS API."""

import base64
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

from .email_limits import reserve_daily_email_slot


class SendGridEmailBackend(BaseEmailBackend):
    """Send Django email messages through the SendGrid v3 Mail Send API."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', '').strip()
        self.api_url = getattr(
            settings,
            'SENDGRID_API_URL',
            'https://api.sendgrid.com/v3/mail/send',
        )
        self.timeout = getattr(settings, 'SENDGRID_API_TIMEOUT', 15)
        self.session = requests.Session()

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if self.fail_silently:
                return 0
            raise ImproperlyConfigured('SENDGRID_API_KEY is required to send email.')

        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
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
                if response.status_code != 202:
                    raise RuntimeError(
                        f'SendGrid Mail Send returned HTTP {response.status_code}; '
                        f'expected 202: {response.text[:1000]}'
                    )
                sent += 1
            except (requests.RequestException, RuntimeError):
                if not self.fail_silently:
                    raise
        return sent

    @classmethod
    def _build_payload(cls, message):
        from_name, from_email = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        personalization = {'to': cls._addresses(message.to)}

        cc = cls._addresses(getattr(message, 'cc', []))
        bcc = cls._addresses(getattr(message, 'bcc', []))
        if cc:
            personalization['cc'] = cc
        if bcc:
            personalization['bcc'] = bcc

        payload = {
            'personalizations': [personalization],
            'from': {'email': from_email},
            'subject': message.subject,
            'content': [{
                'type': f'text/{message.content_subtype}',
                'value': message.body,
            }],
        }
        if from_name:
            payload['from']['name'] = from_name

        alternatives = getattr(message, 'alternatives', []) or []
        for alternative in alternatives:
            content, mimetype = cls._alternative_parts(alternative)
            payload['content'].append({'type': mimetype, 'value': content})

        reply_to = cls._addresses(getattr(message, 'reply_to', []))
        if reply_to:
            payload['reply_to'] = reply_to[0]

        attachments = cls._attachments(getattr(message, 'attachments', []))
        if attachments:
            payload['attachments'] = attachments

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
                mimetype = attachment.mimetype
            else:
                filename, content, mimetype = attachment

            if isinstance(content, str):
                content = content.encode('utf-8')
            item = {
                'content': base64.b64encode(content).decode('ascii'),
                'filename': filename,
                'type': mimetype or 'application/octet-stream',
                'disposition': 'attachment',
            }
            result.append(item)
        return result
