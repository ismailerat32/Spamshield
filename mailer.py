import smtplib
from email.mime.text import MIMEText

def send_mail(host, port, user, password, to_email, subject, body):
    print("MAIL_DEBUG send_mail başladı", flush=True)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email

    try:
        print("MAIL_DEBUG SMTP SSL bağlanıyor...", flush=True)

        server = smtplib.SMTP_SSL(host, 465, timeout=10)

        print("MAIL_DEBUG login deneniyor...", flush=True)
        server.login(user, password)

        print("MAIL_DEBUG mail gönderiliyor...", flush=True)
        server.sendmail(user, [to_email], msg.as_string())

        server.quit()

        print("MAIL_SUCCESS gönderildi", flush=True)

    except Exception as e:
        print("MAIL_ERROR:", repr(e), flush=True)
        raise
