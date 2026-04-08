import json
import os
import re

AI_FILE = "data/ai_memory.json"


def _default_data():
    return {"spam": [], "clean": []}


def clean_text(text):
    text = str(text or "").lower()
    text = re.sub(r"http[s]?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9ğüşöçıİĞÜŞÖÇ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def similarity(a, b):
    a_words = set(clean_text(a).split())
    b_words = set(clean_text(b).split())

    if not a_words or not b_words:
        return 0.0

    ortak = len(a_words & b_words)
    toplam = len(a_words | b_words)
    return ortak / toplam if toplam else 0.0


def load_ai():
    if not os.path.exists(AI_FILE):
        return _default_data()

    try:
        with open(AI_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return _default_data()

        if "spam" not in data or not isinstance(data["spam"], list):
            data["spam"] = []
        if "clean" not in data or not isinstance(data["clean"], list):
            data["clean"] = []

        return data
    except Exception:
        return _default_data()


def save_ai(data):
    os.makedirs("data", exist_ok=True)
    with open(AI_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def learn(message, label):
    data = load_ai()
    msg = clean_text(message)

    if not msg:
        return

    if label == "spam":
        if msg not in data["spam"]:
            data["spam"].append(msg)
    else:
        if msg not in data["clean"]:
            data["clean"].append(msg)

    save_ai(data)


def predict(message, threshold=0.50):
    data = load_ai()
    msg = clean_text(message)

    if not msg:
        return "UNKNOWN"

    spam_score = 0
    clean_score = 0

    for saved in data["spam"]:
        if similarity(msg, saved) >= threshold:
            spam_score += 1

    for saved in data["clean"]:
        if similarity(msg, saved) >= threshold:
            clean_score += 1

    if clean_score > spam_score and clean_score > 0:
        return "TEMIZ_AI"

    if spam_score > clean_score and spam_score > 0:
        return "SPAM_AI"

    return "UNKNOWN"
