import requests

url = "https://spamshield-peld.onrender.com/api/push-log"

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": "spamshield_push_key_123"
}

data = {
    "sender": "TEST-SENDER",
    "status": "SPAM",
    "score": "99",
    "category": "TEST",
    "message": "Cloud sync test mesajı"
}

try:
    r = requests.post(url, json=data, headers=headers, timeout=30)
    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)
except Exception as e:
    print("HATA:", e)
