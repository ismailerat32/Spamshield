import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_mail(host=None, port=None, user=None, password=None, to_email="", subject="", body=""):
    smtp_host = host or os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(port or os.getenv("SMTP_PORT", "587"))
    smtp_user = user or os.getenv("SMTP_USER", "")
    smtp_pass = password or os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        return False, "SMTP ayarları eksik"

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        return True, "Mail gönderildi"
    except Exception as e:
        return False, f"Mail hatası: {e}"
