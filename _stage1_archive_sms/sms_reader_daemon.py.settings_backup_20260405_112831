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

SMS_LIMIT = 5
SMS_TIMEOUT = 30
POLL_INTERVAL = 10

ENABLE_NOTIFICATIONS = True
ENABLE_AUTO_DELETE = False

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
    "PTTKARGO",
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
    "deneme bonusu",
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

def get_sms_list(limit=SMS_LIMIT):
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
                timeout=SMS_TIMEOUT
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

def hybrid_analyze(sender, body):
    if is_whitelisted_sender(sender):
        return {
            "status": "TEMIZ",
            "score": 0,
            "reason": "WHITELIST",
            "ai_enabled": False
        }

    kw_score = keyword_score(body)
    ai = ai_analyze_message(body)

    total_score = kw_score + ai.get("score", 0)

    # AI spam dediyse daha güvenli davran
    if ai.get("enabled") and ai.get("result") == "SPAM":
        total_score += 20

    status = "SPAM" if total_score >= 40 else "TEMIZ"

    return {
        "status": status,
        "score": total_score,
        "reason": f"KW:{kw_score} + AI:{ai.get('score', 0)}",
        "ai_enabled": ai.get("enabled", False),
        "ai_result": ai.get("result", "UNKNOWN"),
        "ai_error": ai.get("error")
    }

def notify_spam(sender, score, body):
    if not ENABLE_NOTIFICATIONS:
        return

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

def delete_sms(sms_id):
    if not ENABLE_AUTO_DELETE:
        return False

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
        messages = get_sms_list(SMS_LIMIT)

        for sms in messages:
            sms_id = str(sms.get("_id", ""))
            if not sms_id or sms_id in seen_ids:
                continue

            seen_ids.add(sms_id)

            sender = sms.get("number") or sms.get("address") or "Bilinmiyor"
            received = sms.get("received", "")
            body = sms.get("body", "")

            result = hybrid_analyze(sender, body)
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
                notify_spam(sender, score, body)

                if ENABLE_AUTO_DELETE:
                    deleted = delete_sms(sms_id)
                    if deleted:
                        log_print(f"🗑 SMS silindi: {sms_id}")
                    else:
                        log_print(f"⚠️ SMS silinemedi: {sms_id}")

        save_seen_ids(seen_ids)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
