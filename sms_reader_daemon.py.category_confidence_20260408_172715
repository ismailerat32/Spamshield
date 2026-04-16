import os
import json
import time
import subprocess
from datetime import datetime
from analyzer import analyze_sms

BASE_DIR = os.path.expanduser("~/spamshield_test_final/spamshield_release")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

SEEN_IDS_FILE = os.path.join(DATA_DIR, "seen_ids.json")
SPAM_LOGS_FILE = os.path.join(DATA_DIR, "spam_logs.json")
WHITELIST_FILE = os.path.join(DATA_DIR, "whitelist.json")
RUNTIME_SETTINGS_FILE = os.path.join(BASE_DIR, "spamshield_runtime_settings.json")
LOG_FILE = os.path.join(LOG_DIR, "sms_daemon.log")

DEFAULT_SETTINGS = {
    "enable_notifications": True,
    "enable_vibration": True,
    "enable_auto_delete": False,
    "sms_limit": 5,
    "poll_interval": 10,
    "spam_threshold": 40
}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def log_print(message):
    print(message, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def load_json_file(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_runtime_settings():
    settings = DEFAULT_SETTINGS.copy()
    data = load_json_file(RUNTIME_SETTINGS_FILE, {})
    if isinstance(data, dict):
        settings.update(data)
    return settings


def load_seen_ids():
    data = load_json_file(SEEN_IDS_FILE, [])
    return set(str(x) for x in data) if isinstance(data, list) else set()


def save_seen_ids(seen_ids):
    save_json_file(SEEN_IDS_FILE, sorted(list(seen_ids)))


def load_spam_logs():
    data = load_json_file(SPAM_LOGS_FILE, [])
    return data if isinstance(data, list) else []


def save_spam_log(entry):
    logs = load_spam_logs()
    logs.insert(0, entry)
    save_json_file(SPAM_LOGS_FILE, logs[:100])


def load_whitelist():
    data = load_json_file(WHITELIST_FILE, [])
    return [str(x).upper() for x in data] if isinstance(data, list) else []


def get_sms_list(limit=5, timeout=20):
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
            log_print("⚠️ SMS çıktısı JSON parse edilemedi.")
        except Exception as e:
            log_print(f"⚠️ SMS okuma hatası: {e}")

    return []


def is_dynamic_whitelisted(sender):
    sender = str(sender or "").upper()
    dynamic_whitelist = load_whitelist()
    return any(item in sender for item in dynamic_whitelist)


def send_notification(title, content):
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", content],
            timeout=5
        )
    except Exception as e:
        log_print(f"Bildirim hatası: {e}")


def vibrate_alert():
    try:
        subprocess.run(["termux-vibrate", "-d", "300"], timeout=5)
    except Exception as e:
        log_print(f"Titreşim hatası: {e}")


def delete_sms(sms_id):
    try:
        subprocess.run(
            ["termux-sms-delete", "-i", str(sms_id)],
            timeout=5
        )
        log_print(f"🗑️ SMS silindi: {sms_id}")
    except Exception as e:
        log_print(f"Silme hatası: {e}")


def normalize_result(result):
    if not isinstance(result, dict):
        return {
            "status": "TEMIZ",
            "score": 0,
            "category": "GENEL",
            "reason": "INVALID_RESULT"
        }

    return {
        "status": str(result.get("status", "TEMIZ")).upper(),
        "score": int(result.get("score", 0)),
        "category": str(result.get("category", "GENEL")),
        "reason": str(result.get("reason", "CLEAN"))
    }


def main():
    seen_ids = load_seen_ids()
    log_print("📡 SpamShield daemon başlatıldı...")

    while True:
        settings = load_runtime_settings()

        enable_notifications = bool(settings.get("enable_notifications", True))
        enable_vibration = bool(settings.get("enable_vibration", True))
        enable_auto_delete = bool(settings.get("enable_auto_delete", False))
        sms_limit = int(settings.get("sms_limit", 5))
        poll_interval = int(settings.get("poll_interval", 10))
        spam_threshold = int(settings.get("spam_threshold", 40))

        messages = get_sms_list(limit=sms_limit, timeout=20)

        for sms in messages:
            sms_id = str(sms.get("_id", ""))
            sender = sms.get("number") or sms.get("address") or "Bilinmiyor"
            body = sms.get("body", "")
            received = sms.get("received", "")

            if not sms_id:
                continue

            if sms_id in seen_ids:
                continue

            seen_ids.add(sms_id)

            # analyzer.py sonucu
            result = normalize_result(analyze_sms(sender, body))

            # Dinamik whitelist varsa her zaman temiz say
            if is_dynamic_whitelisted(sender):
                result = {
                    "status": "TEMIZ",
                    "score": 0,
                    "category": "WHITELIST",
                    "reason": "DYNAMIC_WHITELIST"
                }

            # Runtime threshold uygula
            if result["status"] == "SPAM" and result["score"] < spam_threshold:
                result["status"] = "TEMIZ"

            log_print("-" * 60)
            log_print(f"Gönderen : {sender}")
            log_print(f"Tarih    : {received}")
            log_print(f"Durum    : {result['status']}")
            log_print(f"Skor     : {result['score']}")
            log_print(f"Kategori : {result['category']}")
            log_print(f"Neden    : {result['reason']}")
            log_print(f"Mesaj    : {body[:300]}")

            if result["status"] == "SPAM":
                save_spam_log({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sender": sender,
                    "body": body,
                    "score": result.get("score", 0),
                    "reason": result.get("reason", ""),
                    "category": result.get("category", "GENEL"),
                    "status": result.get("status", "SPAM"),
                    "sms_id": sms_id,
                    "auto_delete": enable_auto_delete
                })

                log_print("🚨 SPAM YAKALANDI")

                if enable_notifications:
                    send_notification(
                        "🚨 SpamShield",
                        f"{sender}\n{body[:60]}"
                    )

                if enable_vibration:
                    vibrate_alert()

                if enable_auto_delete:
                    delete_sms(sms_id)

        save_seen_ids(seen_ids)
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
