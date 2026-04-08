import re


def is_whitelisted_sender(sender):
    sender = str(sender or "").upper()

    whitelist = [
        "HALKBANK",
        "PARAF",
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
        "HEPSI BURADA",
        "YURTICI",
        "YURTİÇİ",
        "ARAS",
        "MNG",
        "UPS",
        "PTTKARGO",
        "BURGAN BANK"
    ]

    return any(w in sender for w in whitelist)


SPAM_KEYWORDS = [
    "kazandın",
    "ödül",
    "bedava",
    "tikla",
    "tıkla",
    "hemen",
    "şimdi",
    "simdi",
    "linke gir",
    "giriş yap",
    "giris yap",
    "şifre",
    "sifre",
    "hesap askıya",
    "hesap askiya",
    "onayla",
    "bonus",
    "freebet",
    "casino",
    "bahis",
    "kampanya",
    "promosyon",
    "faizsiz kredi",
    "yatırım fırsatı",
    "yatirim firsati",
    "hoşgeldin bonusu",
    "hosgeldin bonusu",
    "deneme bonusu",
    "kazanın",
    "kazanin"
]

DANGEROUS_DOMAINS = [
    "bit.ly",
    "tinyurl",
    "goo.gl",
    "t.me",
    "short.link",
    "grabify"
]


def contains_link(text):
    return re.search(r"http[s]?://", str(text or "")) is not None


def extract_links(text):
    return re.findall(r"http[s]?://\S+", str(text or ""))


def analyze_sms(sender, message):
    # 1) Güvenilir gönderenleri direkt temiz say
    if is_whitelisted_sender(sender):
        return {
            "status": "TEMIZ",
            "score": 0,
            "category": "WHITELIST",
            "reason": "WHITELIST"
        }

    score = 0
    category = "GENEL"
    status = "TEMIZ"
    reasons = []

    msg = str(message or "").lower()

    # 2) Keyword analizi
    for word in SPAM_KEYWORDS:
        if word in msg:
            score += 10
            reasons.append(f"KW:{word}")

    # 3) Link analizi
    if contains_link(msg):
        score += 15
        reasons.append("LINK")

    # 4) Tehlikeli domain analizi
    links = extract_links(msg)
    for link in links:
        low = link.lower()
        for domain in DANGEROUS_DOMAINS:
            if domain in low:
                score += 25
                reasons.append(f"DOMAIN:{domain}")

    # 5) Para / kampanya baskısı
    if "tl" in msg and (
        "kazan" in msg
        or "bonus" in msg
        or "kampanya" in msg
        or "ödül" in msg
        or "odul" in msg
        or "fırsat" in msg
        or "firsat" in msg
    ):
        score += 10
        reasons.append("MONEY")

    # 6) Opt-out / kısa numara
    if "iptal" in msg or "ret" in msg:
        score += 5
        reasons.append("OPT-OUT")

    # 7) Karar
    if score >= 30:
        status = "SPAM"
        category = "OLASI_SPAM"

    return {
        "status": status,
        "score": score,
        "category": category,
        "reason": " + ".join(reasons) if reasons else "CLEAN"
    }


if __name__ == "__main__":
    test_sender = "PARAF"
    test_message = "Paraf ile gıda marketi harcamalarınıza özel 1.250 TL ParafPara! Detay: https://www.paraf.com.tr"
    print(analyze_sms(test_sender, test_message))
