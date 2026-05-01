
import json, time

def push_client_alert(msg):
    try:
        path = Path("data/client_alert.json")
        old = {}
        if path.exists():
            try:
                old = json.loads(path.read_text(encoding="utf-8"))
            except:
                old = {}

        alert = {
            "id": int(time.time()),
            "type": "spam",
            "title": "Spam Engellendi",
            "message": msg[:120]
        }

        path.write_text(json.dumps(alert, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print("client alert yazılamadı:", e)


import subprocess
import json
from pathlib import Path
from datetime import datetime
from spam_ai import analiz_et

LOG_FILE = Path("data/spam_logs.json")

def smsleri_al():
    try:
        out = subprocess.check_output(
            ["termux-sms-list", "-l", "20"],
            timeout=8
        )
        return json.loads(out.decode("utf-8", errors="ignore"))
    except Exception as e:
        print("SMS okuma hatası:", e)
        return []

def read_logs():
    try:
        if LOG_FILE.exists():
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except:
        pass
    return []

def write_logs(logs):
    LOG_FILE.write_text(
        json.dumps(logs, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def tara():
    smsler = smsleri_al()
    logs = read_logs()

    if not smsler:
        print("SMS bulunamadı veya izin yok.")
        return

    seen = set()
    for x in logs:
        seen.add(str(x.get("number","")) + "|" + str(x.get("body",""))[:80])

    yeni = 0

    for sms in smsler:
        text = sms.get("body", "")
        numara = sms.get("number", "bilinmiyor")
        result = analiz_et(text, numara)
        is_spam = result['spam']

        key = str(numara) + "|" + str(text)[:80]
        if key in seen:
            continue

        logs.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "number": numara,
            "body": text,
            "status": "SPAM" if is_spam else "OK",
            "score": result.get("score", 0),
            "reasons": result.get("reasons", [])
        })

        yeni += 1

        if is_spam:
            push_client_alert(text)
            print(f"[SPAM] {numara}: {text[:60]}")
        else:
            print(f"[OK] {numara}: {text[:40]}")

    logs = logs[:300]
    write_logs(logs)

    print(f"✅ {yeni} yeni SMS analiz edildi")
    print(f"✅ Kayıt dosyası: {LOG_FILE}")

if __name__ == "__main__":
    tara()
