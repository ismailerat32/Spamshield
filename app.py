from flask import Flask, flash, redirect, render_template, request
import os, json

app = Flask(__name__)

app.secret_key = "spamshield-pro-secret-key"
BASE_DIR = "data"

# =========================
# JSON HELPER
# =========================
def _load_json_list(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return []

def _save_json_list(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def _normalize_message(value):
    if value is None:
        return ""
    return str(value).strip()

def _remove_message_once(items, message):
    target = _normalize_message(message)
    new_items = []
    removed = False
    for item in items:
        if not removed and _normalize_message(item) == target:
            removed = True
            continue
        new_items.append(item)
    return new_items, removed

def _append_if_missing(items, message):
    target = _normalize_message(message)
    if not target:
        return items
    for item in items:
        if _normalize_message(item) == target:
            return items
    items.append(target)
    return items

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("splash.html")

@app.route("/analyze")
def analyze():
    return render_template("analyze.html")

@app.route("/blocked")
def blocked():
    blocked_messages = _load_json_list("data/blocklist.json")
    return render_template("blocked.html", blocked_messages=blocked_messages[::-1])

@app.route("/notifications")
def notifications():
    blocked_messages = _load_json_list("data/blocklist.json")
    watch_messages = _load_json_list("data/watchlist.json")

    items = []

    for msg in reversed(blocked_messages[-20:]):
        items.append({
            "status": "blocked",
            "message": str(msg)
        })

    for msg in reversed(watch_messages[-20:]):
        items.append({
            "status": "watch",
            "message": str(msg)
        })

    stats = get_stats()
    return render_template("notifications.html", items=items[:30], stats=stats)

@app.route("/control")
def control():
    messages = _load_json_list("data/watchlist.json")
    return render_template("control_panel.html", messages=messages[::-1])

@app.route("/message-action", methods=["POST"])
def message_action():
    message = _normalize_message(request.form.get("message", ""))
    source = _normalize_message(request.form.get("source", "watch"))
    action = _normalize_message(request.form.get("action", ""))

    if not message:
        flash("Mesaj alınamadı.")
        return redirect("/notifications")

    blocklist_path = "data/blocklist.json"
    watchlist_path = "data/watchlist.json"
    cleanlist_path = "data/allowlist.json"

    blocklist = _load_json_list(blocklist_path)
    watchlist = _load_json_list(watchlist_path)
    cleanlist = _load_json_list(cleanlist_path)

    blocklist, _ = _remove_message_once(blocklist, message)
    watchlist, _ = _remove_message_once(watchlist, message)
    cleanlist, _ = _remove_message_once(cleanlist, message)

    if action == "spam":
        blocklist = _append_if_missing(blocklist, message)
        flash("Mesaj SPAM listesine taşındı.")
    elif action == "watch":
        watchlist = _append_if_missing(watchlist, message)
        flash("Mesaj inceleme listesine taşındı.")
    elif action == "clean":
        cleanlist = _append_if_missing(cleanlist, message)
        flash("Mesaj temiz listeye taşındı.")
    else:
        flash("Bilinmeyen işlem.")
        return redirect("/notifications")

    _save_json_list(blocklist_path, blocklist)
    _save_json_list(watchlist_path, watchlist)
    _save_json_list(cleanlist_path, cleanlist)

    return redirect("/notifications")

@app.route("/reports")
def reports():
    return render_template("reports.html", stats=get_stats())

@app.route("/settings")
def settings():
    return render_template("settings_page.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/license")
def license_page():
    return render_template("license.html")

@app.route("/protection")
def protection():
    return render_template("protection.html")

# =========================
# STATS
# =========================
def get_stats():
    blocklist = _load_json_list("data/blocklist.json")
    watchlist = _load_json_list("data/watchlist.json")

    total = len(blocklist) + len(watchlist)

    return {
        "blocked_count": len(blocklist),
        "watch_count": len(watchlist),
        "total_count": total
    }

# =========================
# RUN
# =========================

@app.route("/splash")
def splash():
    return render_template("splash.html")

@app.route("/radial")
def radial():
    return render_template("radial_step1.html", stats=get_stats())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

