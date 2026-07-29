"""E-posta gonderimi — ik-otomasyon/src/services/mail.service.js'in Python portu."""
from __future__ import annotations

from django.core.mail import EmailMessage, get_connection

from ..models import HrSettings


def is_configured():
    s = HrSettings.load()
    return bool(s.smtp_host and s.smtp_user and s.smtp_pass and s.recipient_emails)


def send_reminder(subject, html_body):
    s = HrSettings.load()
    if not is_configured():
        raise ValueError("E-posta ayarları eksik. Lütfen ayarlardan SMTP ve alıcı bilgilerini girin.")

    connection = get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=s.smtp_host,
        port=s.smtp_port or 587,
        username=s.smtp_user,
        password=s.smtp_pass,
        use_tls=not s.smtp_secure,
        use_ssl=s.smtp_secure,
    )
    from_addr = s.mail_from or s.sender_email or s.smtp_user

    message = EmailMessage(
        subject=subject, body=html_body, from_email=from_addr,
        to=s.recipient_emails, connection=connection,
    )
    message.content_subtype = "html"
    message.send()
