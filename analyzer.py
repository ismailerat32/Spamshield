import re

WHITELIST_SENDERS = [
    "halkbank", "qnb", "turktelekom", "ttavantaj",
    "oz burois", "isparta bld", "osmanzabun", "on."
]

GAMBLING_WORDS = [
    "casino", "slot", "bahis", "freebet", "jackpot", "rulet", "kupon"
]

BANK_WORDS = [
    "hesabınız", "hesabiniz", "kartınız", "kartiniz",
    "şifre", "sifre", "doğrulama", "dogrulama",
    "bloke", "askıya", "askiya"
]

AD_WORDS = [
    "indirim", "kampanya", "fırsat", "firsat", "hediye",
    "son gün", "son gun", "davet et"
]

SHORT_LINKS = [
    "bit.ly", "cutt.ly", "tinyurl", "goo.gl", "t.ly"
]

def analyze_sms(sender, message):
    sender_l = (sender or "").lower()
    msg = (message or "").lower()

    score = 0
    category = "GENEL"

    has_link = ("http" in msg or "www" in msg)
    has_short_link = any(link in msg for link in SHORT_LINKS)
    has_bank_words = any(word in msg for word in BANK_WORDS)
    has_gambling = any(word in msg for word in GAMBLING_WORDS)
    has_ads = any(word in msg for word in AD_WORDS)

    # Beyaz liste: gönderici adına göre çalışır
    is_whitelisted = any(w == sender_l for w in WHITELIST_SENDERS)

    # Beyaz listedeyse ve phishing sinyali yoksa temiz say
    if is_whitelisted and not (has_link and has_bank_words):
        return "TEMİZ", 0, "BEYAZ_LISTE"

    # Link
    if has_link:
        score += 20
        category = "LINK"

    # Kısa link
    if has_short_link:
        score += 35
        category = "ZARARLI_LINK"

    # Kumar
    if has_gambling:
        score += 45
        category = "KUMAR"

    # Banka
    if has_bank_words:
        score += 25
        category = "BANKA"

    # Phishing
    if has_link and has_bank_words:
        score += 40
        category = "PHISHING"

    # Reklam / promosyon
    if has_ads:
        score += 15
        if category == "GENEL":
            category = "REKLAM"

    # Para miktarı
    if re.search(r"\d+\s?(tl|try|₺)", msg):
        score += 10
        if category == "GENEL":
            category = "FINANSAL"

    # Büyük harf oranı
    letters = [c for c in message if c.isalpha()]
    if letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.75:
            score += 10
            if category == "GENEL":
                category = "KAMPANYA"

    if score >= 55:
        return "SPAM", score, category
    elif score >= 35:
        return "ŞÜPHELİ", score, category
    else:
        return "TEMİZ", score, "TEMİZ"
