# Copyright (c) 2026 ismail erat
# All rights reserved.

import re

SPAM_KEYWORDS = [
    "kazandın", "ödül", "bedava", "tıkla", "hemen", "şimdi",
    "linke gir", "giriş yap", "şifre", "hesap askıya", "onayla"
]

DANGEROUS_DOMAINS = [
    "bit.ly", "tinyurl", "goo.gl", "t.me",
    "short.link", "grabify"
]

def contains_link(text):
    return re.search(r"http[s]?://", text) is not None

def extract_links(text):
    return re.findall(r"http[s]?://\S+", text)

def analyze_sms(sender, message):
    score = 0
    category = "GENEL"
    status = "TEMİZ"

    msg = message.lower()

    # 1️⃣ Keyword analizi
    for word in SPAM_KEYWORDS:
        if word in msg:
            score += 10

    # 2️⃣ Link analizi
    if contains_link(msg):
        score += 15
        links = extract_links(msg)

        for link in links:
            for bad in DANGEROUS_DOMAINS:
                if bad in link:
                    score += 40
                    category = "PHISHING"
                    status = "SPAM"

    # 3️⃣ Fake banka / kritik pattern
    if "banka" in msg or "kart" in msg:
        if "giriş" in msg or "onayla" in msg:
            score += 25
            category = "BANKA_PHISHING"
            status = "SPAM"

    # 4️⃣ Final karar
    if score >= 60:
        status = "SPAM"
    elif score >= 30:
        status = "ŞÜPHELİ"
    else:
        status = "TEMİZ"

    return status, score, category
