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

CATEGORY_RULES = {
    "BANKA": [
        "iban", "kart", "banka", "hesap", "şifre", "sifre",
        "otp", "işlem", "islem", "ödeme", "odeme"
    ],
    "KARGO": [
        "kargo", "teslimat", "paket", "gönderi", "gonderi",
        "kurye", "takip no", "sipariş", "siparis"
    ],
    "PROMOSYON": [
        "bonus", "kampanya", "promosyon", "indirim", "fırsat",
        "firsat", "bedava", "kupon", "hediye"
    ],
    "DOLANDIRICILIK": [
        "tıkla", "tikla", "hemen", "onayla", "şifre", "sifre",
        "hesap askıya", "hesap askiya", "freebet", "casino", "bahis"
    ]
}


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


def detect_category(message):
    msg = str(message or "").lower()

    scores = {}
    for category, words in CATEGORY_RULES.items():
        scores[category] = sum(1 for w in words if w in msg)

    best_category = "GENEL"
    best_score = 0

    for category, score in scores.items():
        if score > best_score:
            best_category = category
            best_score = score

    return best_category


def calc_confidence(score, ai_used=False, whitelist_used=False):
    if whitelist_used:
        return 100

    if ai_used:
        return 95

    if score >= 80:
        return 96
    if score >= 60:
        return 90
    if score >= 40:
        return 82
    if score >= 30:
        return 74
    if score >= 15:
        return 55

    return 30


def analyze_sms(sender, message):
    sender = str(sender or "")
    message = str(message or "")

    # 1) WHITELIST
    if is_whitelisted_sender(sender):
        return {
            "status": "TEMIZ",
            "score": 0,
            "category": "WHITELIST",
            "reason": "WHITELIST_OVERRIDE",
            "confidence": 100
        }

    # 2) AI
    try:
        ai_result = predict(message)

        if ai_result == "TEMIZ_AI":
            return {
                "status": "TEMIZ",
                "score": 0,
                "category": detect_category(message),
                "reason": "AI_CLEAN",
                "confidence": 95
            }

        if ai_result == "SPAM_AI":
            return {
                "status": "SPAM",
                "score": 80,
                "category": detect_category(message),
                "reason": "AI_SPAM",
                "confidence": 95
            }
    except Exception:
        pass

    # 3) Rule-based
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
    category = detect_category(message)
    confidence = calc_confidence(score)

    return {
        "status": status,
        "score": score,
        "category": category,
        "reason": " + ".join(reasons) if reasons else "CLEAN",
        "confidence": confidence
    }
