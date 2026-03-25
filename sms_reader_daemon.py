#!/usr/bin/env python3

import json
import subprocess
import time
import os
from analyzer import analyze_sms

BASE_DIR = os.path.expanduser("~/spamshield_release")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

SEEN_FILE = os.path.join(DATA_DIR, "seen_ids.json")
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

if not os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def log_line(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_seen():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_seen(data):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def notify(title, content):
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", content],
            timeout=5,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except:
        pass

def read_sms():
    try:
        result = subprocess.run(
            ["termux-sms-list", "-l", "20"],
            capture_output=True,
            text=True,
            timeout=25
        )
        return json.loads(result.stdout)
    except Exception as e:
        log_line(f"⚠️ SMS okuma hatası: {e}")
        return []

log_line("📡 SpamShield daemon başlatıldı")

while True:
    seen_ids = load_seen()
    messages = read_sms()

    for msg in reversed(messages):
        msg_id = msg.get("_id")
        if not msg_id or msg_id in seen_ids:
            continue

        sender = msg.get("address") or msg.get("number") or "BİLİNMİYOR"
        body = (msg.get("body") or "").strip()

        if not body:
            seen_ids.append(msg_id)
            continue

        try:
            status, score, category = analyze_sms(sender, body)
        except Exception as e:
            log_line(f"⚠️ Analiz hatası: {e}")
            continue

        line = f"From: {sender} | Status: {status} | Score: {score} | Category: {category} | Message: {body[:120]}"
        log_line(line)

        if status in ["SPAM", "ENGELLENDİ"]:
            notify("🚫 SpamShield - SPAM", f"{sender} → SPAM mesaj")
        elif status == "ŞÜPHELİ":
            notify("⚠️ SpamShield - Şüpheli", f"{sender} → Şüpheli mesaj")

        seen_ids.append(msg_id)

    save_seen(seen_ids)
    time.sleep(5)
