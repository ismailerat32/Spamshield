import subprocess, json, time, os

DATA_DIR = "data"

def load_json(name):
    try:
        with open(f"{DATA_DIR}/{name}") as f:
            return json.load(f)
    except:
        return []

def save_json(name, data):
    with open(f"{DATA_DIR}/{name}", "w") as f:
        json.dump(data, f)

def analyze(msg):
    msg = msg.lower()
    spam_words = ["casino", "bet", "bahis", "bonus", "free", "kazanç"]

    score = 0
    for w in spam_words:
        if w in msg:
            score += 1

    if score >= 2:
        return "spam"
    elif score == 1:
        return "watch"
    else:
        return "clean"

print("🚀 SMS daemon başlatıldı...")

seen_ids = set(load_json("seen_ids.json"))

while True:
    try:
        result = subprocess.check_output(["termux-sms-list"])
        messages = json.loads(result)

        blocklist = load_json("blocklist.json")
        watchlist = load_json("watchlist.json")

        for m in messages:
            mid = str(m.get("read") or m.get("date"))

            if mid in seen_ids:
                continue

            body = m.get("body","")
            result = analyze(body)

            print("📩", body[:50], "->", result)

            if result == "spam":
                blocklist.append(body)
            elif result == "watch":
                watchlist.append(body)

            seen_ids.add(mid)

        save_json("blocklist.json", blocklist)
        save_json("watchlist.json", watchlist)
        save_json("seen_ids.json", list(seen_ids))

    except Exception as e:
        print("HATA:", e)

    time.sleep(10)
