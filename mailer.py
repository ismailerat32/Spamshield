import smtplib
from email.message import EmailMessage

def send_mail(smtp_host, smtp_port, smtp_user, smtp_pass, to_email, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
