import json
import os
import re
from ai_model import predict

WHITELIST_FILE = "data/whitelist.json"

SPAM_KEYWORDS = [
    "kazandın",
    "ödül",
    "odul",
    "bedava",
    "tıkla",
    "tikla",
    "hemen",
    "şimdi",
    "simdi",
    "bonus",
    "casino",
    "bahis",
    "freebet",
    "promosyon",
    "kampanya",
    "fırsat",
    "firsat",
    "linke gir",
    "giriş yap",
    "giris yap",
    "şifre",
    "sifre",
    "onayla",
    "hesap askıya",
    "hesap askiya"
]

DANGEROUS_DOMAINS = [
    "bit.ly",
    "tinyurl",
    "t.me",
    "goo.gl",
    "grabify",
    "short.link"
]


def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return []

    try:
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def is_whitelisted_sender(sender):
    try:
        whitelist = load_whitelist()
        sender = str(sender or "").upper().strip()
        return any(str(w).upper().strip() in sender for w in whitelist)
    except Exception:
        return False


def contains_link(text):
    return re.search(r"http[s]?://", str(text or "")) is not None


def extract_links(text):
    return re.findall(r"http[s]?://\S+", str(text or ""))


def analyze_sms(sender, message):
    sender = str(sender or "")
    message = str(message or "")

    # 1) WHITELIST her şeyi override eder
    if is_whitelisted_sender(sender):
        return {
            "status": "TEMIZ",
            "score": 0,
            "category": "WHITELIST",
            "reason": "WHITELIST_OVERRIDE"
        }

    # 2) AI öğrenilmiş bilgiye göre karar verir
    try:
        ai_result = predict(message)

        if ai_result == "TEMIZ_AI":
            return {
                "status": "TEMIZ",
                "score": 0,
                "category": "AI",
                "reason": "AI_CLEAN"
            }

        if ai_result == "SPAM_AI":
            return {
                "status": "SPAM",
                "score": 80,
                "category": "AI",
                "reason": "AI_SPAM"
            }
    except Exception:
        pass

    # 3) Rule-based analiz
    score = 0
    reasons = []
    msg = message.lower()

    for word in SPAM_KEYWORDS:
        if word in msg:
            score += 10
            reasons.append(word)

    if contains_link(msg):
        score += 15
        reasons.append("link")

    for link in extract_links(msg):
        low = link.lower()
        for domain in DANGEROUS_DOMAINS:
            if domain in low:
                score += 25
                reasons.append(domain)

    status = "SPAM" if score >= 30 else "TEMIZ"

    return {
        "status": status,
        "score": score,
        "category": "GENEL",
        "reason": " + ".join(reasons) if reasons else "CLEAN"
    }
