"""
E-posta gonderimi — ik-otomasyon/src/services/mail.service.js'in Python portu.

PORT / TLS-SSL UYUMU
---------------------
SMTP'de iki farklı, BİRBİRİNE KARIŞTIRILMAMASI gereken şifreleme yolu vardır:
  - Port 587 (submission)  → düz bağlantı + sonradan STARTTLS ile şifrelemeye
                             GEÇİLİR. Django'da bu `use_tls=True, use_ssl=False`.
  - Port 465 (SMTPS)       → bağlantı BAŞTAN İTİBAREN SSL/TLS ile şifrelidir.
                             Django'da bu `use_tls=False, use_ssl=True`.

Bu ikisi birbirinin yerine KULLANILAMAZ: port 587'ye doğrudan SSL handshake
göndermek (ya da port 465'e düz bağlanıp STARTTLS beklemek), istemcinin
gönderdiği baytları sunucunun beklediğinden FARKLI bir protokol olarak
yorumlamasına yol açar — tam olarak "SSL: WRONG_VERSION_NUMBER" hatası
budur. Bu yüzden gönderim denemeden ÖNCE port/ayar uyumu doğrulanır.
"""
from __future__ import annotations

import smtplib
import socket
import ssl

from django.core.mail import EmailMessage, get_connection

from ..models import HrSettings


def is_configured():
    s = HrSettings.load()
    return bool(s.smtp_host and s.smtp_user and s.smtp_pass and s.reminder_recipients())


def validate_port_security(port: int, use_ssl: bool):
    """
    Port ile TLS/SSL seçiminin uyumlu olup olmadığını kontrol eder.
    Uyumsuzsa, kullanıcının tam olarak ne yapması gerektiğini söyleyen bir
    ValueError fırlatır — hiçbir bağlantı denenmeden.
    """
    if port == 587 and use_ssl:
        raise ValueError("Port 587 için STARTTLS seçmelisiniz.")
    if port == 465 and not use_ssl:
        raise ValueError("Port 465 için SSL seçmelisiniz.")


def send_reminder(subject, html_body):
    s = HrSettings.load()
    if not is_configured():
        raise ValueError("E-posta ayarları eksik. Lütfen ayarlardan SMTP ve bildirim e-postası bilgilerini girin.")

    port = s.smtp_port or 587
    use_ssl = bool(s.smtp_secure)
    use_tls = not use_ssl

    # Bağlantıyı hiç açmadan önce port/şifreleme uyumunu doğrula (kural 3-4).
    validate_port_security(port, use_ssl)

    connection = get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=s.smtp_host,
        port=port,
        username=s.smtp_user,
        password=s.smtp_pass,
        use_tls=use_tls,
        use_ssl=use_ssl,
        timeout=15,
    )
    from_addr = s.mail_from or s.sender_email or s.smtp_user

    message = EmailMessage(
        subject=subject, body=html_body, from_email=from_addr,
        to=s.reminder_recipients(), connection=connection,
    )
    message.content_subtype = "html"

    # KURAL 5: Hiçbir SMTP/ağ/SSL istisnası Django hata sayfasına düşmesin —
    # hepsi kullanıcı dostu bir ValueError'a çevrilir (view zaten ValueError'ı
    # yakalayıp ekranda gösteriyor, bkz. views.SendThisMonthReminderView).
    try:
        message.send()
    except ssl.SSLError as exc:
        onerilen = "STARTTLS" if use_ssl else "SSL"
        raise ValueError(
            f"SSL/TLS bağlantı hatası: sunucu port {port} üzerinde beklediğiniz şifreleme türünü "
            f"kullanmıyor olabilir. {onerilen} seçeneğini deneyin. (Ayrıntı: {exc})"
        ) from exc
    except smtplib.SMTPAuthenticationError as exc:
        raise ValueError(
            "SMTP kimlik doğrulama başarısız. Kullanıcı adı/parolayı kontrol edin "
            "(Gmail için normal şifre değil, 'Uygulama Şifresi' gerekir)."
        ) from exc
    except smtplib.SMTPConnectError as exc:
        raise ValueError(f"SMTP sunucusuna bağlanılamadı: {exc}") from exc
    except smtplib.SMTPException as exc:
        raise ValueError(f"E-posta gönderilemedi (SMTP hatası): {exc}") from exc
    except (socket.timeout, TimeoutError):
        raise ValueError(f"SMTP sunucusuna bağlantı zaman aşımına uğradı ({s.smtp_host}:{port}).")
    except OSError as exc:
        raise ValueError(f"E-posta sunucusuna ulaşılamadı: {exc}") from exc
