import os
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _load_dotenv_fallback():
    """
    Render ortamında gerçek env kullanılır.
    Lokal/Termux ortamında .env varsa SMTP_* değerlerini os.environ içine alır.
    Var olan env değerlerini ezmez.
    """
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue

            key, value = s.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        # Mail gönderimi .env okuma hatası yüzünden uygulamayı düşürmesin.
        pass


def send_mail(host=None, port=None, user=None, password=None, to_email="", subject="", body=""):
    _load_dotenv_fallback()

    smtp_host = host or os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(port or os.getenv("SMTP_PORT", "587"))
    smtp_user = (user or os.getenv("SMTP_USER", "")).strip()
    smtp_pass = (password or os.getenv("SMTP_PASS", "")).strip()

    # Gmail App Password ekranda boşluklu görünebilir; SMTP login için boşluksuz kullanılmalı.
    smtp_pass = smtp_pass.replace(" ", "")

    if not smtp_user or not smtp_pass:
        return False, "SMTP ayarları eksik"

    if not to_email:
        return False, "Alıcı e-posta eksik"

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=25)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()

        return True, "Mail gönderildi"
    except Exception as e:
        return False, f"Mail hatası: {e}"
