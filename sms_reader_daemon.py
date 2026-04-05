import os
import json
import time
import logging
import subprocess

from utils.ai_filter import ai_analyze_message

BASE_DIR = os.path.expanduser("~/spamshield_test_final/spamshield_release")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

SEEN_IDS_FILE = os.path.join(DATA_DIR, "seen_ids.json")
LOG_FILE = os.path.join(LOG_DIR, "sms_daemon.log")
RUNTIME_SETTINGS_FILE = os.path.join(BASE_DIR, "spamshield_runtime_settings.json")

DEFAULT_SETTINGS = {
    "enable_notifications": True,
    "enable_vibration": True,
    "enable_auto_delete": False,
    "sms_limit": 5,
    "poll_interval": 10,
    "spam_threshold": 40
}

WHITELIST_SENDERS = [
    "HALKBANK",
    "HALKBANK.",
    "BURGAN BANK",
    "GARANTI",
    "AKBANK",
    "ZIRAAT",
    "VAKIFBANK",
    "ISBANK",
    "ENPARA",
    "QNB",
    "PTT",
    "TRENDYOL",
    "HEPSIBURADA",
    "YURTICI",
    "ARAS",
    "MNG",
    "PTTKARGO"
]

SPAM_WORDS = [
    "bonus",
    "freebet",
    "casino",
    "bahis",
    "kredi",
    "kampanya",
    "bit.ly",
    "tinyurl",
    "hemen başvur",
    "hemen basvur",
    "tanitim iptali",
    "hoşgeldin bonusu",
    "hosgeldin bonusu",
    "yatırım fırsatı",
    "yatirim firsati",
    "deneme bonusu"
]

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def log_print(msg):
    print(msg, flush=True)
    logging.info(msg)

def load_runtime_settings():
    if not os.path.exists(RUNTIME_SETTINGS_FILE):
        with open(RUNTIME_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=2)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(RUNTIME_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        merged = DEFAULT_SETTINGS.copy()
        if isinstance(data, dict):
            merged.update(data)
        return merged
    except Exception as e:
        log_print(f"⚠️ Ayar dosyası okunamadı: {e}")
        return DEFAULT_SETTINGS.copy()

def load_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    try:
        with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(str(x) for x in data) if isinstance(data, list) else set()
    except Exception:
        return set()

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen_ids)), f, ensure_ascii=False, indent=2)

def get_sms_list(limit=5, timeout=30):
    commands = [
        ["termux-sms-list", "-t", "inbox", "-l", str(limit)],
        ["termux-sms-list", "-l", str(limit)],
    ]

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                continue

            raw = (result.stdout or "").strip()
            if not raw:
                return []

            data = json.loads(raw)
            if isinstance(data, list):
                return data

        except subprocess.TimeoutExpired:
            log_print(f"⚠️ termux-sms-list zaman aşımına uğradı. Komut: {' '.join(cmd)}")
        except json.JSONDecodeError:
            log_print("⚠️ SMS çıktısı JSON olarak parse edilemedi.")
        except Exception as e:
            log_print(f"⚠️ SMS okuma hatası: {e}")

    return []

def is_whitelisted_sender(sender):
    sender_upper = str(sender or "").upper()
    return any(item.upper() in sender_upper for item in WHITELIST_SENDERS)

def keyword_score(body):
    text = (body or "").lower()
    score = 0

    for word in SPAM_WORDS:
        if word in text:
            score += 20

    if "http://" in text or "https://" in text:
        score += 30

    return score

def hybrid_analyze(sender, body, spam_threshold):
    if is_whitelisted_sender(sender):
        return {
            "status": "TEMIZ",
            "score": 0,
            "reason": "WHITELIST",
            "ai_enabled": False,
            "ai_result": "UNKNOWN",
            "ai_error": None
        }

    kw_score = keyword_score(body)
    ai = ai_analyze_message(body)

    total_score = kw_score + ai.get("score", 0)

    if ai.get("enabled") and ai.get("result") == "SPAM":
        total_score += 20

    status = "SPAM" if total_score >= spam_threshold else "TEMIZ"

    return {
        "status": status,
        "score": total_score,
        "reason": f"KW:{kw_score} + AI:{ai.get('score', 0)}",
        "ai_enabled": ai.get("enabled", False),
        "ai_result": ai.get("result", "UNKNOWN"),
        "ai_error": ai.get("error")
    }

def notify_spam(sender, score, body):
    short_sender = str(sender)[:30]
    short_body = (body or "").replace("\n", " ")[:90]

    try:
        subprocess.run(
            [
                "termux-notification",
                "--title", "🚫 SpamShield Uyarı",
                "--content", f"{short_sender} | Skor: {score} | {short_body}"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
    except Exception as e:
        log_print(f"⚠️ Bildirim gönderilemedi: {e}")

def vibrate_alert():
    try:
        subprocess.run(
            ["termux-vibrate", "-d", "300"],
            capture_output=True,
            text=True,
            timeout=5
        )
    except Exception as e:
        log_print(f"⚠️ Titreşim hatası: {e}")

def delete_sms(sms_id):
    try:
        result = subprocess.run(
            ["termux-sms-delete", "-i", str(sms_id)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        log_print(f"⚠️ SMS silme hatası: {e}")
        return False

def main():
    seen_ids = load_seen_ids()
    log_print("📡 SpamShield AI+Hybrid daemon başlatıldı...")

    while True:
        settings = load_runtime_settings()

        enable_notifications = bool(settings.get("enable_notifications", True))
        enable_vibration = bool(settings.get("enable_vibration", True))
        enable_auto_delete = bool(settings.get("enable_auto_delete", False))
        sms_limit = int(settings.get("sms_limit", 5))
        poll_interval = int(settings.get("poll_interval", 10))
        spam_threshold = int(settings.get("spam_threshold", 40))

        messages = get_sms_list(limit=sms_limit, timeout=30)

        for sms in messages:
            sms_id = str(sms.get("_id", ""))
            if not sms_id or sms_id in seen_ids:
                continue

            seen_ids.add(sms_id)

            sender = sms.get("number") or sms.get("address") or "Bilinmiyor"
            received = sms.get("received", "")
            body = sms.get("body", "")

            result = hybrid_analyze(sender, body, spam_threshold)
            status = result["status"]
            score = result["score"]

            log_print("-" * 60)
            log_print(f"Gönderen : {sender}")
            log_print(f"Tarih    : {received}")
            log_print(f"Durum    : {status}")
            log_print(f"Skor     : {score}")
            log_print(f"Neden    : {result.get('reason')}")
            log_print(f"AI       : {result.get('ai_result', 'UNKNOWN')} | aktif={result.get('ai_enabled')}")
            if result.get("ai_error"):
                log_print(f"AI Hata  : {result.get('ai_error')}")
            log_print(f"Mesaj    : {body[:300]}")

            if status == "SPAM":
                if enable_notifications:
                    notify_spam(sender, score, body)

                if enable_vibration:
                    vibrate_alert()

                if enable_auto_delete:
                    deleted = delete_sms(sms_id)
                    if deleted:
                        log_print(f"🗑 SMS silindi: {sms_id}")
                    else:
                        log_print(f"⚠️ SMS silinemedi: {sms_id}")

        save_seen_ids(seen_ids)
        time.sleep(poll_interval)

if __name__ == "__main__":
    main()
