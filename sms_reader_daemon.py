import json
import subprocess
import time
import os
from analyzer import analyze_sms

LOG_FILE = "logs/log.txt"
BLOCKLIST_FILE = "data/blocklist.json"
WATCHLIST_FILE = "data/watchlist.json"
SETTINGS_FILE = "data/settings.json"

def log(text):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)

def load_json_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json_file(path, data):
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_settings():
    settings = load_json_file(SETTINGS_FILE)
    if not settings:
        settings = {
            "notifications_enabled": True,
            "notify_spam": True,
            "notify_supheli": True,
            "min_notify_score": 35
        }
    return settings

def notify(title, content, status=None, score=0):
    settings = load_settings()

    if not settings.get("notifications_enabled", True):
        return
    if score < int(settings.get("min_notify_score", 35)):
        return
    if status == "SPAM" and not settings.get("notify_spam", True):
        return
    if status == "ŞÜPHELİ" and not settings.get("notify_supheli", True):
        return

    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", content],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
    except:
        pass

def add_to_blocklist(sender, category, score):
    data = load_json_file(BLOCKLIST_FILE)
    data[sender] = {"category": category, "score": score, "blocked": True}
    save_json_file(BLOCKLIST_FILE, data)

def add_to_watchlist(sender, category, score):
    data = load_json_file(WATCHLIST_FILE)
    if sender in data:
        data[sender]["count"] += 1
        data[sender]["score"] = max(data[sender]["score"], score)
        data[sender]["category"] = category
    else:
        data[sender] = {"category": category, "score": score, "count": 1}
    save_json_file(WATCHLIST_FILE, data)
    return data[sender]["count"]

def remove_from_watchlist(sender):
    data = load_json_file(WATCHLIST_FILE)
    if sender in data:
        del data[sender]
        save_json_file(WATCHLIST_FILE, data)

def is_blocked(sender):
    data = load_json_file(BLOCKLIST_FILE)
    return sender in data

def get_latest_sms(limit=10):
    try:
        output = subprocess.check_output(
            ["termux-sms-list", "-l", str(limit)],
            stderr=subprocess.DEVNULL,
            timeout=25
        ).decode("utf-8")
        data = json.loads(output)
        return data if isinstance(data, list) else []
    except subprocess.TimeoutExpired:
        log("⚠️ SMS okuma hatası: termux-sms-list zaman aşımına uğradı")
        return []
    except Exception as e:
        log(f"⚠️ SMS okuma hatası: {e}")
        return []

def main():
    log("📡 SpamShield daemon başlatıldı")
    seen_ids = set()

    while True:
        sms_list = get_latest_sms(10)

        for sms in reversed(sms_list):
            sms_id = str(sms.get("_id", ""))
            if not sms_id or sms_id in seen_ids:
                continue

            seen_ids.add(sms_id)
            sender = sms.get("number") or sms.get("address") or "BİLİNMEYEN"
            message = sms.get("body", "").strip()

            if not message:
                continue

            if is_blocked(sender):
                log(f"From: {sender} | Status: ENGELLENDİ | Score: 100 | Category: BLOCKLIST | Message: {message}")
                notify("⛔ SpamShield - Engellendi", f"{sender} kara listede", status="SPAM", score=100)
                continue

            status, score, category = analyze_sms(sender, message)

            if status == "ŞÜPHELİ":
                count = add_to_watchlist(sender, category, score)
                if count >= 2:
                    status = "SPAM"
                    score = max(score, 60)
                    category = "WATCHLIST_ESCALATED"
                    add_to_blocklist(sender, category, score)
                    remove_from_watchlist(sender)

            log(f"From: {sender} | Status: {status} | Score: {score} | Category: {category} | Message: {message}")

            if status == "SPAM":
                add_to_blocklist(sender, category, score)
                notify("🚨 SpamShield - SPAM", f"{sender} | {category} | Skor: {score}", status="SPAM", score=score)
            elif status == "ŞÜPHELİ":
                notify("⚠️ SpamShield - Şüpheli", f"{sender} | {category} | Skor: {score}", status="ŞÜPHELİ", score=score)

        time.sleep(5)

if __name__ == "__main__":
    main()
