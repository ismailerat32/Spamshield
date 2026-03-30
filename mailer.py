import os
import requests

def send_mail(host, port, user, password, to_email, subject, body):
    provider = os.getenv("MAIL_PROVIDER", "").strip().lower()

    if provider == "sendgrid":
        api_key = os.getenv("SENDGRID_API_KEY", "").strip()
        from_email = os.getenv("SENDGRID_FROM_EMAIL", "").strip()

        print("MAIL_DEBUG provider: sendgrid", flush=True)
        print("MAIL_DEBUG sendgrid_api_key_set:", bool(api_key), flush=True)
        print("MAIL_DEBUG sendgrid_from_email:", from_email, flush=True)
        print("MAIL_DEBUG target_email:", to_email, flush=True)

        if not api_key:
            raise RuntimeError("SENDGRID_API_KEY eksik")
        if not from_email:
            raise RuntimeError("SENDGRID_FROM_EMAIL eksik")

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [
                    {
                        "to": [{"email": to_email}]
                    }
                ],
                "from": {"email": from_email},
                "subject": subject,
                "content": [
                    {
                        "type": "text/plain",
                        "value": body
                    }
                ]
            },
            timeout=20
        )

        print("MAIL_DEBUG sendgrid_status:", response.status_code, flush=True)

        if response.status_code not in (200, 202):
            print("MAIL_ERROR sendgrid_response:", response.text, flush=True)
            raise RuntimeError(f"SendGrid hata kodu: {response.status_code}")

        print("MAIL_SUCCESS gönderildi", flush=True)
        return

    raise RuntimeError("Geçerli MAIL_PROVIDER ayarlı değil")
