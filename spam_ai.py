import re

SPAM_WORDS = {
    "kazan": 2,
    "kazandınız": 3,
    "kazandiniz": 3,
    "ödül": 3,
    "odul": 3,
    "bedava": 3,
    "ücretsiz": 2,
    "ucretsiz": 2,
    "çekiliş": 3,
    "cekilis": 3,
    "kampanya": 2,
    "indirim": 2,
    "fırsat": 2,
    "firsat": 2,
    "kaçırma": 2,
    "kacirma": 2,
    "hediye": 2,
    "kupon": 2,
    "bonus": 2,
    "puan": 2,
    "gb": 1,
    "tl": 1,
    "market": 1,
    "alışveriş": 1,
    "alisveris": 1,
    "anket": 2,
    "katıl": 2,
    "katil": 2,
    "hemen": 1,
    "son gün": 2,
    "son gun": 2,
    "özel": 1,
    "ozel": 1,
}

SAFE_WORDS = {
    "şifre": 4,
    "sifre": 4,
    "şifreniz": 4,
    "sifreniz": 4,
    "doğrulama": 4,
    "dogrulama": 4,
    "kod": 3,
    "kodunuz": 4,
    "tek kullanımlık": 4,
    "tek kullanimlik": 4,
    "kartınızdan": 4,
    "kartinizdan": 4,
    "hesabınızdan": 4,
    "hesabinizdan": 4,
    "dekont": 3,
    "sorgu numarası": 4,
    "sorgu numarasi": 4,
    "ödeme": 3,
    "odeme": 3,
    "işlem": 3,
    "islem": 3,
    "başvuru": 3,
    "basvuru": 3,
}

SAFE_SENDERS = [
    "HALKBANK", "ON.", "TURKTELEKOM", "TT", "GARANTI", "AKBANK",
    "YAPIKREDI", "ISBANK", "ZIRAAT", "VAKIFBANK"
]

PROMO_SENDERS = [
    "MARKET", "COCO", "MEYDAN", "KAZAN", "FIRSAT", "FIDAN", "SOK"
]

def normalize(text):
    text = str(text or "").lower()
    tr = str.maketrans({
        "ı": "i", "İ": "i", "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u", "ş": "s", "Ş": "s",
        "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    })
    text = text.translate(tr)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def analiz_et(text, sender=""):
    raw = str(text or "")
    clean = normalize(raw)
    sender_raw = str(sender or "")
    sender_up = sender_raw.upper()

    score = 0
    reasons = []

    for word, weight in SPAM_WORDS.items():
        if normalize(word) in clean:
            score += weight
            reasons.append(f"spam:{word}+{weight}")

    for word, weight in SAFE_WORDS.items():
        if normalize(word) in clean:
            score -= weight
            reasons.append(f"safe:{word}-{weight}")

    if "http" in clean or "www" in clean or ".com" in clean:
        score += 4
        reasons.append("link+4")

    if "%" in raw:
        score += 2
        reasons.append("yuzde+2")

    if re.search(r"\b\d+\s*(tl|gb)\b", clean):
        score += 2
        reasons.append("para_gb+2")

    if re.search(r"\b\d{4,6}\b", clean) and ("sifre" in clean or "kod" in clean):
        score -= 3
        reasons.append("otp_kod-3")

    if any(x in sender_up for x in PROMO_SENDERS):
        score += 2
        reasons.append("promo_sender+2")

    if any(x in sender_up for x in SAFE_SENDERS):
        if any(normalize(w) in clean for w in SAFE_WORDS):
            score -= 2
            reasons.append("trusted_sender_safe-2")

    # Kısa mesaj ama promosyon kelimesi varsa şüpheli
    if len(clean) < 25 and score > 0:
        score += 1
        reasons.append("kisa_supheli+1")

    # Güvenli banka işlemleri negatifte kalırsa spam olmasın
    is_spam = score >= 3

    return {
        "spam": is_spam,
        "score": score,
        "reasons": reasons[:10]
    }

def spam_mi(text):
    return analiz_et(text)["spam"]
