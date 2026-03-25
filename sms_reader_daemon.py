#!/usr/bin/env python3

import json
import subprocess
import time
import os
from datetime import datetime
from analyzer import analyze_sms

BASE_DIR = os.path.expanduser("~/spamshield_release")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

SEEN_FILE = os.path.join(DATA_DIR, "seen_ids.json")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

SMS_LIMIT = 5
SMS_TIMEOUT = 25
NORMAL_SLEEP = 15
ERROR_SLEEP = 60
MAX_SEEN_IDS = 1000

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

if not os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

_last_error_text = None


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_line(text):
    line = text.strip()
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_error_once(text):
    global _last_error_text
    if text != _last_error_text:
        log_line(text)
        _last_error_text = text


def clear_last_error():
    global _last_error_text
    _last_error_text = None


def load_seen():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_seen(data):
    data = data[-MAX_SEEN_IDS:]
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def notify(title, content):
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", content],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
    except Exception:
        pass


def read_sms():
    try:
        result = subprocess.run(
            ["termux-sms-list", "-l", str(SMS_LIMIT)],
            capture_output=True,
            text=True,
            timeout=SMS_TIMEOUT
        )

        stdout = (result.stdout or "").strip()
        if not stdout:
            return []

        data = json.loads(stdout)
        if isinstance(data, list):
            clear_last_error()
            return data

        log_error_once(f"⚠️ SMS okuma hatası: Beklenmeyen çıktı türü ({type(data).__name__})")
        return []

    except subprocess.TimeoutExpired:
        log_error_once("⚠️ SMS okuma hatası: termux-sms-list zaman aşımına uğradı")
        return []
    except json.JSONDecodeError:
        log_error_once("⚠️ SMS okuma hatası: JSON çözümlenemedi")
        return []
    except Exception as e:
        log_error_once(f"⚠️ SMS okuma hatası: {e}")
        return []


def process_message(msg, seen_ids):
    msg_id = msg.get("_id")
    if not msg_id or msg_id in seen_ids:
        return seen_ids

    sender = msg.get("address") or msg.get("number") or "BİLİNMİYOR"
    body = (msg.get("body") or "").strip()

    if not body:
        seen_ids.append(msg_id)
        return seen_ids

    try:
        status, score, category = analyze_sms(sender, body)
    except Exception as e:
        log_error_once(f"⚠️ Analiz hatası: {e}")
        return seen_ids

    line = (
        f"From: {sender} | Status: {status} | Score: {score} | "
        f"Category: {category} | Message: {body[:160]}"
    )
    log_line(line)

    if status in ["SPAM", "ENGELLENDİ"]:
        notify("🚫 SpamShield - SPAM", f"{sender} → SPAM mesaj")
    elif status == "ŞÜPHELİ":
        notify("⚠️ SpamShield - Şüpheli", f"{sender} → Şüpheli mesaj")

    seen_ids.append(msg_id)
    return seen_ids


def main():
    log_line(f"📡 SpamShield daemon başlatıldı [{now_str()}]")

    while True:
        seen_ids = load_seen()
        messages = read_sms()

        if not messages:
            save_seen(seen_ids)
            time.sleep(ERROR_SLEEP if _last_error_text else NORMAL_SLEEP)
            continue

        for msg in reversed(messages):
            seen_ids = process_message(msg, seen_ids)

        save_seen(seen_ids)
        time.sleep(NORMAL_SLEEP)


if __name__ == "__main__":
    main()
