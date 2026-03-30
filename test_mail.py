from mailer import send_mail

# 🔐 BURAYA APP PASSWORD YAZ (boşluksuz!)
app_password = "BURAYA_APP_PASSWORD".replace(" ", "").replace("\u00a0", "")

send_mail(
    "smtp.gmail.com",
    587,
    "REDACTED_SMTP_USER",
    "REMOVED_SMTP_PASSWORD",
    "REDACTED_SMTP_USER",
    "SpamShield Test",
    "Bu bir test mailidir."
)

print("Mail gönderildi")
