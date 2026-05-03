from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import random
import string
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from mailer import send_mail

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "spamshield_dev_key")

LOG_FILE = "logs/log.txt"
WATCHLIST_FILE = "data/watchlist.json"
BLOCKLIST_FILE = "data/blocklist.json"
USERS_FILE = "data/users.json"
SETTINGS_FILE = "data/settings.json"
LICENSE_FILE = "data/license.json"
LOCALES_DIR = "locales"


def ensure_default_user():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(USERS_FILE):
        users = {
            "admin": {
                "password": generate_password_hash("admin123"),
                "role": "admin",
                "active": True,
                "license_key": "ADMIN-SYSTEM",
                "expires_at": "2099-12-31",
                "email": ""
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)


def ensure_default_settings():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        settings = {
            "notifications_enabled": True,
            "notify_spam": True,
            "notify_supheli": True,
            "min_notify_score": 35
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)


def load_settings():
    ensure_default_settings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "notifications_enabled": True,
            "notify_spam": True,
            "notify_supheli": True,
            "min_notify_score": 35
        }


def save_settings(settings):
    os.makedirs("data", exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def load_mail_settings():
    return {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_pass": os.getenv("SMTP_PASS", "")
    }


def load_locale(lang):
    path = os.path.join(LOCALES_DIR, f"{lang}.json")
    fallback = os.path.join(LOCALES_DIR, "tr.json")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        try:
            with open(fallback, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def get_lang():
    lang = session.get("lang", "tr")
    return lang if lang in ["tr", "en"] else "tr"


def load_users():
    ensure_default_user()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def read_logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if not line or "From:" not in line:
                    continue
                logs.append(line)
    return logs[-300:]


def parse_logs():
    parsed = []
    for line in read_logs():
        item = {
            "raw": line,
            "sender": "",
            "status": "",
            "score": "",
            "category": "",
            "message": line
        }

        parts = [p.strip() for p in line.split("|")]
        for p in parts:
            if p.startswith("From:"):
                item["sender"] = p.replace("From:", "").strip()
            elif p.startswith("Status:"):
                item["status"] = p.replace("Status:", "").strip()
            elif p.startswith("Score:"):
                item["score"] = p.replace("Score:", "").strip()
            elif p.startswith("Category:"):
                item["category"] = p.replace("Category:", "").strip()
            elif p.startswith("Message:"):
                item["message"] = p.replace("Message:", "").strip()

        parsed.append(item)

    return parsed


def load_json_dict(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json_dict(path, data):
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_license():
    if not os.path.exists(LICENSE_FILE):
        return {"active": False, "key": ""}
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active": False, "key": ""}


def save_license(data):
    os.makedirs("data", exist_ok=True)
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def login_required():
    return session.get("logged_in") is True


def admin_required():
    return session.get("role") == "admin"


def get_last_blocked(blocklist):
    if not blocklist:
        return None
    try:
        return list(blocklist.keys())[-1]
    except Exception:
        return None


def is_date_expired(date_str):
    try:
        expiry = datetime.strptime(date_str, "%Y-%m-%d").date()
        return datetime.now().date() > expiry
    except Exception:
        return False


def generate_license_key():
    parts = []
    for _ in range(4):
        part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return "SPAM-" + "-".join(parts)


def get_all_used_license_keys(users):
    used = set()
    for info in users.values():
        key = info.get("license_key", "").strip().upper()
        if key and key != "NONE":
            used.add(key)
    return used


def generate_unique_license_key(users):
    used = get_all_used_license_keys(users)
    while True:
        new_key = generate_license_key()
        if new_key not in used:
            return new_key


@app.route("/api/push-log", methods=["POST"])
def api_push_log():
    api_key = request.headers.get("X-API-KEY", "").strip()
    expected_key = os.getenv("API_PUSH_KEY", "").strip()

    if not expected_key or api_key != expected_key:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    sender = str(data.get("sender", "BİLİNMİYOR")).strip()
    status = str(data.get("status", "TEMİZ")).strip()
    score = str(data.get("score", "0")).strip()
    category = str(data.get("category", "GENEL")).strip()
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"ok": False, "error": "message missing"}), 400

    os.makedirs("logs", exist_ok=True)

    line = (
        f"From: {sender} | Status: {status} | Score: {score} | "
        f"Category: {category} | Message: {message[:160]}"
    )

    print("PUSH_LOG:", line, flush=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return jsonify({"ok": True})


@app.route("/set-language/<lang>")
def set_language(lang):
    if lang in ["tr", "en"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("landing"))


@app.route("/landing")
def landing():
    return render_template("landing.html")


@app.route("/activate", methods=["GET", "POST"])
def activate():
    error = None
    success = None
    t = load_locale(get_lang())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        license_key = request.form.get("license_key", "").strip().upper()

        users = load_users()

        if username not in users:
            error = "Kullanıcı bulunamadı" if get_lang() == "tr" else "User not found"
        else:
            user = users[username]
            saved_key = user.get("license_key", "").strip().upper()

            if not saved_key or saved_key == "NONE":
                error = "Bu kullanıcı için lisans tanımlı değil." if get_lang() == "tr" else "No license assigned for this user."
            elif license_key != saved_key:
                error = "Geçersiz lisans" if get_lang() == "tr" else "Invalid license"
            else:
                users[username]["active"] = True
                if not users[username].get("expires_at"):
                    users[username]["expires_at"] = "2026-12-31"
                save_users(users)
                success = "Hesap aktif edildi!" if get_lang() == "tr" else "Account activated!"

    return render_template("activate.html", error=error, success=success, t=t, lang=get_lang())


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    t = load_locale(get_lang())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        users = load_users()

        if not username:
            error = "Kullanıcı adı boş olamaz." if get_lang() == "tr" else "Username cannot be empty."
        elif not email:
            error = "Mail adresi gerekli." if get_lang() == "tr" else "Email is required."
        elif username in users:
            error = "Bu kullanıcı zaten var." if get_lang() == "tr" else "This user already exists."
        elif len(password) < 6:
            error = "Şifre kısa." if get_lang() == "tr" else "Password is too short."
        else:
            users[username] = {
                "password": generate_password_hash(password),
                "role": "user",
                "active": True,
                "license_key": "NONE",
                "expires_at": "2099-01-01",
                "email": email
            }
            save_users(users)

            # Yeni kayıt olan kullanıcı register ekranında kalmasın;
            # direkt login olmuş şekilde ana panele girsin.
            session["username"] = username
            session["role"] = "user"

            return redirect(url_for("radial"))

    return render_template("register.html", error=error, success=success, t=t, lang=get_lang())


@app.route("/send-license/<target_username>", methods=["POST"])
def send_license(target_username):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    users = load_users()
    mail_cfg = load_mail_settings()

    if target_username not in users:
        print("MAIL_ERROR: kullanıcı bulunamadı ->", target_username, flush=True)
        return redirect(url_for("users"))

    user = users[target_username]
    email = user.get("email", "").strip()

    if not email:
        print("MAIL_ERROR: kullanıcı email yok", flush=True)
        return redirect(url_for("users"))

    current_license = user.get("license_key", "").strip().upper()
    generated_new_license = False

    if not current_license or current_license == "NONE":
        license_key = generate_unique_license_key(users)
        generated_new_license = True
    else:
        license_key = current_license

    expires_at = user.get("expires_at", "").strip() or "2026-12-31"
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8080")

    subject = "SpamShield Lisans Kodunuz"
    body = f"""Merhaba {target_username},

SpamShield lisans kodunuz aşağıdadır:

{license_key}

Aktivasyon için:
- Kullanıcı adınız: {target_username}
- Lisans kodunuz: {license_key}

Aktivasyon sayfası:
{base_url}/activate

SpamShield
"""

    try:
        print("MAIL_DEBUG smtp_host:", mail_cfg["smtp_host"], flush=True)
        print("MAIL_DEBUG smtp_port:", mail_cfg["smtp_port"], flush=True)
        print("MAIL_DEBUG smtp_user:", mail_cfg["smtp_user"], flush=True)
        print("MAIL_DEBUG smtp_pass_set:", bool(mail_cfg["smtp_pass"]), flush=True)
        print("MAIL_DEBUG target_email:", email, flush=True)
        print("MAIL_DEBUG target_username:", target_username, flush=True)
        print("MAIL_DEBUG license_key:", license_key, flush=True)

        send_mail(
            mail_cfg["smtp_host"],
            mail_cfg["smtp_port"],
            mail_cfg["smtp_user"],
            mail_cfg["smtp_pass"],
            email,
            subject,
            body
        )

        if generated_new_license:
            users[target_username]["license_key"] = license_key
            users[target_username]["expires_at"] = expires_at
            save_users(users)

        print("MAIL_SUCCESS gönderildi", flush=True)

    except Exception as e:
        print("MAIL_ERROR:", repr(e), flush=True)

    return redirect(url_for("users"))


    user = users[target_username]
    email = user.get("email", "").strip()

    if not email:
        print("MAIL_ERROR: kullanıcı email yok", flush=True)
        return redirect(url_for("users"))

    license_key = user.get("license_key", "").strip().upper()

    if not license_key or license_key == "NONE":
        license_key = generate_unique_license_key(users)
        users[target_username]["license_key"] = license_key
        if not users[target_username].get("expires_at"):
            users[target_username]["expires_at"] = "2026-12-31"
        save_users(users)

    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8080")

    subject = "SpamShield Lisans Kodunuz"
    body = f"""Merhaba {target_username},

SpamShield lisans kodunuz aşağıdadır:

{license_key}

Aktivasyon için:
- Kullanıcı adınız: {target_username}
- Lisans kodunuz: {license_key}

Aktivasyon sayfası:
{base_url}/activate

SpamShield
"""

    try:
        print("MAIL_DEBUG smtp_host:", mail_cfg["smtp_host"], flush=True)
        print("MAIL_DEBUG smtp_port:", mail_cfg["smtp_port"], flush=True)
        print("MAIL_DEBUG smtp_user:", mail_cfg["smtp_user"], flush=True)
        print("MAIL_DEBUG smtp_pass_set:", bool(mail_cfg["smtp_pass"]), flush=True)
        print("MAIL_DEBUG target_email:", email, flush=True)
        print("MAIL_DEBUG target_username:", target_username, flush=True)
        print("MAIL_DEBUG license_key:", license_key, flush=True)

        send_mail(
            mail_cfg["smtp_host"],
            mail_cfg["smtp_port"],
            mail_cfg["smtp_user"],
            mail_cfg["smtp_pass"],
            email,
            subject,
            body
        )

        print("MAIL_SUCCESS gönderildi", flush=True)

    except Exception as e:
        print("MAIL_ERROR:", repr(e), flush=True)

    return redirect(url_for("users"))


@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_default_user()

    error = None
    t = load_locale(get_lang())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        user = users.get(username)

        if not user:
            error = "Kullanıcı adı veya şifre yanlış." if get_lang() == "tr" else "Username or password is incorrect."
        elif not user.get("active", True):
            error = "Bu kullanıcı pasif durumda." if get_lang() == "tr" else "This user is inactive."
        elif is_date_expired(user.get("expires_at", "2099-12-31")):
            error = "Kullanıcı lisans süresi dolmuş." if get_lang() == "tr" else "User license has expired."
        elif check_password_hash(user["password"], password):
            session["logged_in"] = True
            session["username"] = username
            session["role"] = user.get("role", "user")
            return redirect(url_for("radial"))
        else:
            error = "Kullanıcı adı veya şifre yanlış." if get_lang() == "tr" else "Username or password is incorrect."

    return render_template("login.html", error=error, t=t, lang=get_lang())


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if not login_required():
        return redirect(url_for("login"))

    error = None
    success = None
    username = session.get("username")
    t = load_locale(get_lang())

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        users = load_users()
        user = users.get(username)

        if not user or not check_password_hash(user["password"], current_password):
            error = "Mevcut şifre yanlış." if get_lang() == "tr" else "Current password is incorrect."
        elif len(new_password) < 6:
            error = "Yeni şifre en az 6 karakter olmalı." if get_lang() == "tr" else "New password must be at least 6 characters."
        elif new_password != confirm_password:
            error = "Yeni şifreler eşleşmiyor." if get_lang() == "tr" else "New passwords do not match."
        else:
            users[username]["password"] = generate_password_hash(new_password)
            save_users(users)
            success = "Şifre başarıyla değiştirildi." if get_lang() == "tr" else "Password changed successfully."

    return render_template(
        "change_password.html",
        error=error,
        success=success,
        username=username,
        t=t,
        lang=get_lang()
    )


@app.route("/add-user", methods=["GET", "POST"])
def add_user():
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    error = None
    success = None
    t = load_locale(get_lang())

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "user").strip()
        expires_at = request.form.get("expires_at", "").strip()
        active = request.form.get("active") == "on"

        users = load_users()

        if not username:
            error = "Kullanıcı adı boş olamaz." if get_lang() == "tr" else "Username cannot be empty."
        elif username in users:
            error = "Bu kullanıcı zaten var." if get_lang() == "tr" else "This user already exists."
        elif len(password) < 6:
            error = "Şifre en az 6 karakter olmalı." if get_lang() == "tr" else "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Şifreler eşleşmiyor." if get_lang() == "tr" else "Passwords do not match."
        elif role not in ["admin", "user"]:
            error = "Geçersiz rol." if get_lang() == "tr" else "Invalid role."
        elif not expires_at:
            error = "Bitiş tarihi gerekli." if get_lang() == "tr" else "Expiry date is required."
        else:
            users[username] = {
                "password": generate_password_hash(password),
                "role": role,
                "active": active,
                "license_key": "NONE",
                "expires_at": expires_at,
                "email": email
            }
            save_users(users)
            success = f"{username} kullanıcısı eklendi." if get_lang() == "tr" else f"User {username} added."

    return render_template(
        "add_user.html",
        error=error,
        success=success,
        username=session.get("username", "admin"),
        t=t,
        lang=get_lang()
    )


@app.route("/users")
def users():
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    return render_template(
        "users.html",
        users=load_users(),
        username=session.get("username", "admin"),
        t=load_locale(get_lang()),
        lang=get_lang()
    )


@app.route("/toggle-user/<target_username>", methods=["POST"])
def toggle_user(target_username):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    users = load_users()
    if target_username in users and target_username != "admin":
        users[target_username]["active"] = not users[target_username].get("active", True)
        save_users(users)

    return redirect(url_for("users"))


@app.route("/delete-user/<target_username>", methods=["POST"])
def delete_user(target_username):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    current_user = session.get("username")
    users = load_users()

    if target_username != current_user and target_username in users:
        del users[target_username]
        save_users(users)

    return redirect(url_for("users"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    error = None
    success = None
    settings_data = load_settings()
    t = load_locale(get_lang())

    if request.method == "POST":
        try:
            settings_data["notifications_enabled"] = request.form.get("notifications_enabled") == "on"
            settings_data["notify_spam"] = request.form.get("notify_spam") == "on"
            settings_data["notify_supheli"] = request.form.get("notify_supheli") == "on"
            settings_data["min_notify_score"] = int(request.form.get("min_notify_score", "35"))
            save_settings(settings_data)
            success = "Bildirim ayarları kaydedildi." if get_lang() == "tr" else "Notification settings saved."
        except Exception:
            error = "Ayarlar kaydedilemedi." if get_lang() == "tr" else "Settings could not be saved."

    return render_template(
        "settings.html",
        settings=settings_data,
        error=error,
        success=success,
        username=session.get("username", "admin"),
        t=t,
        lang=get_lang()
    )


@app.route("/")
def index():
    if not login_required():
        return redirect(url_for("login"))

    logs = parse_logs()
    status_filter = request.args.get("status", "").strip().upper()
    category_filter = request.args.get("category", "").strip().upper()
    sender_filter = request.args.get("sender", "").strip().lower()

    filtered = []
    for log in logs:
        if status_filter and log["status"].upper() != status_filter:
            continue
        if category_filter and log["category"].upper() != category_filter:
            continue
        if sender_filter and sender_filter not in log["sender"].lower():
            continue
        filtered.append(log)

    watchlist = load_json_dict(WATCHLIST_FILE)
    blocklist = load_json_dict(BLOCKLIST_FILE)

    summary = {
        "watchlist_count": len(watchlist),
        "blocklist_count": len(blocklist),
        "last_blocked": get_last_blocked(blocklist)
    }

    return render_template(
        "dashboard.html",
        logs=filtered,
        watchlist=watchlist,
        blocklist=blocklist,
        summary=summary,
        status_filter=status_filter,
        category_filter=category_filter,
        sender_filter=sender_filter,
        username=session.get("username", "admin"),
        role=session.get("role", "user"),
        t=load_locale(get_lang()),
        lang=get_lang()
    )


@app.route("/unblock/<sender>", methods=["POST"])
def unblock(sender):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    blocklist = load_json_dict(BLOCKLIST_FILE)
    if sender in blocklist:
        del blocklist[sender]
        save_json_dict(BLOCKLIST_FILE, blocklist)

    return redirect(url_for("index"))


@app.route("/watch-remove/<sender>", methods=["POST"])
def watch_remove(sender):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    watchlist = load_json_dict(WATCHLIST_FILE)
    if sender in watchlist:
        del watchlist[sender]
        save_json_dict(WATCHLIST_FILE, watchlist)

    return redirect(url_for("index"))


@app.route("/watch-block/<sender>", methods=["POST"])
def watch_block(sender):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    watchlist = load_json_dict(WATCHLIST_FILE)
    blocklist = load_json_dict(BLOCKLIST_FILE)

    if sender in watchlist:
        info = watchlist[sender]
        blocklist[sender] = {
            "category": info.get("category", "MANUAL_BLOCK"),
            "score": max(info.get("score", 0), 60),
            "blocked": True
        }
        del watchlist[sender]
        save_json_dict(WATCHLIST_FILE, watchlist)
        save_json_dict(BLOCKLIST_FILE, blocklist)

    return redirect(url_for("index"))


if __name__ == "__main__":
    ensure_default_user()
    ensure_default_settings()
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

@app.route("/activate-license/<target_username>", methods=["POST"])
def activate_license(target_username):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("index"))

    users = load_users()

    if target_username not in users:
        print("LICENSE_ERROR: kullanıcı yok", target_username, flush=True)
        return redirect(url_for("users"))

    user = users[target_username]

    license_key = generate_unique_license_key(users)

    users[target_username]["license_key"] = license_key
    users[target_username]["expires_at"] = "2026-12-31"
    users[target_username]["active"] = True

    save_users(users)

    print("LICENSE_SUCCESS:", target_username, license_key, flush=True)

    return redirect(url_for("users"))



@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password_live():
    t = load_locale(get_lang())

    if request.method == "POST":
        identity = (
            request.form.get("identity")
            or request.form.get("email")
            or request.form.get("username")
            or ""
        ).strip()

        if not identity:
            return render_template(
                "forgot.html",
                success=False,
                message=None,
                reset_link=None,
                reset_code=None,
                error="Lütfen kullanıcı adı veya e-posta girin.",
                t=t,
                lang=get_lang()
            )

        return render_template(
            "forgot.html",
            success=True,
            message="Bu bilgi sistemde varsa sıfırlama bilgisi oluşturuldu.",
            reset_link=None,
            reset_code=None,
            error=None,
            t=t,
            lang=get_lang()
        )

    return render_template(
        "forgot.html",
        success=False,
        message=None,
        reset_link=None,
        reset_code=None,
        error=None,
        t=t,
        lang=get_lang()
    )



@app.route("/radial")
def radial():
    if not login_required():
        return redirect(url_for("login"))

    return render_template("radial_menu.html")


USER_MODULES = {
    "protection": {
        "icon": "🛡️",
        "title": "Koruma Merkezi",
        "description": "SMS tarama, spam filtreleme ve gerçek zamanlı güvenlik motoru tek ekranda.",
        "stats": [
            {"value": "7/24", "label": "Aktif Koruma"},
            {"value": "92", "label": "Güven Skoru"},
            {"value": "AI", "label": "Analiz Motoru"}
        ],
        "cards": [
            {"title": "Anlık SMS Taraması", "text": "Gelen mesajlar risk sinyallerine göre değerlendirilir ve şüpheli içerikler işaretlenir."},
            {"title": "Akıllı Spam Filtresi", "text": "Kampanya, oltalama, sahte ödül ve tehlikeli bağlantı içerikleri ayrıştırılır."},
            {"title": "Koruma Katmanı", "text": "Kullanıcı deneyimini bozmadan sessiz ve güçlü bir güvenlik katmanı sağlar."},
            {"title": "Güvenli Liste", "text": "Güvendiğin kişiler ve servisler için esnek yönetim alanı hazırlanır."}
        ],
        "rows": [
            {"name": "Koruma Durumu", "value": "Aktif"},
            {"name": "AI Motoru", "value": "Hazır"},
            {"name": "Spam Hassasiyeti", "value": "Yüksek"},
            {"name": "Son Kontrol", "value": "Az önce"}
        ],
        "primary_label": "Korumayı Kontrol Et",
        "primary_href": "/radial"
    },
    "reports": {
        "icon": "📈",
        "title": "Raporlar",
        "description": "Günlük, haftalık ve aylık güvenlik özetlerini sade grafiklerle takip et.",
        "stats": [
            {"value": "125", "label": "Toplam SMS"},
            {"value": "24", "label": "Engellenen"},
            {"value": "%98.5", "label": "Koruma Oranı"}
        ],
        "cards": [
            {"title": "Haftalık Özet", "text": "Spam ve güvenli SMS dağılımını tek bakışta gösterir."},
            {"title": "Risk Eğilimi", "text": "Şüpheli mesaj oranındaki artış veya düşüşleri izler."},
            {"title": "Engelleme Performansı", "text": "SpamShield motorunun kaç mesajı yakaladığını gösterir."},
            {"title": "Premium Raporlama", "text": "Gelişmiş rapor alanı için grafik ve dışa aktarma altyapısı hazırlanır."}
        ],
        "rows": [
            {"name": "Güvenli SMS", "value": "%80"},
            {"name": "Spam SMS", "value": "%20"},
            {"name": "Rapor Periyodu", "value": "Haftalık"},
            {"name": "Son Rapor", "value": "1 saat önce"}
        ],
        "primary_label": "Raporları Yenile",
        "primary_href": "/u/reports"
    },
    "blocked": {
        "icon": "⛔",
        "title": "Engellenenler",
        "description": "Spam olarak işaretlenen numaraları ve mesajları güvenli şekilde yönet.",
        "stats": [
            {"value": "24", "label": "Engellendi"},
            {"value": "17", "label": "Blok Listesi"},
            {"value": "5", "label": "Yeni Kayıt"}
        ],
        "cards": [
            {"title": "Blok Listesi", "text": "Engellenen numaralar ve riskli kaynaklar burada toplanır."},
            {"title": "Son Engellenen SMS", "text": "En güncel spam denemeleri hızlıca görüntülenir."},
            {"title": "Yanlış Pozitif Kontrol", "text": "Güvenli mesajlar yanlışlıkla engellendiyse geri alma alanı hazırlanır."},
            {"title": "Kara Liste Yönetimi", "text": "Manuel numara ekleme ve kaldırma modülü için temel hazırdır."}
        ],
        "rows": [
            {"name": "Son Engelleme", "value": "5 dk önce"},
            {"name": "Risk Seviyesi", "value": "Orta"},
            {"name": "Liste Durumu", "value": "Aktif"},
            {"name": "Otomatik Engelleme", "value": "Açık"}
        ],
        "primary_label": "Listeyi Gör",
        "primary_href": "/u/blocked"
    },
    "analysis": {
        "icon": "🔍",
        "title": "AI Analiz",
        "description": "Mesaj içeriğini risk, dil, bağlantı ve dolandırıcılık sinyallerine göre analiz eder.",
        "stats": [
            {"value": "AI", "label": "Aktif"},
            {"value": "92", "label": "Skor"},
            {"value": "4", "label": "Risk Sinyali"}
        ],
        "cards": [
            {"title": "Metin Analizi", "text": "SMS içindeki vaat, tehdit, sahte ödül ve aciliyet ifadelerini inceler."},
            {"title": "Bağlantı Kontrolü", "text": "Şüpheli URL ve yönlendirme işaretlerini yakalamaya hazırlanır."},
            {"title": "Risk Skoru", "text": "Her mesaja anlaşılır bir güvenlik skoru üretir."},
            {"title": "AI Geliştirme Alanı", "text": "Gelecekte daha gelişmiş model tabanlı analiz için genişletilebilir yapı sağlar."}
        ],
        "rows": [
            {"name": "Analiz Motoru", "value": "Çevrim içi"},
            {"name": "Hassasiyet", "value": "Yüksek"},
            {"name": "Son Analiz", "value": "Az önce"},
            {"name": "Güven Skoru", "value": "92/100"}
        ],
        "primary_label": "Analizi Aç",
        "primary_href": "/u/analysis"
    },
    "notifications": {
        "icon": "🔔",
        "title": "Bildirimler",
        "description": "Güvenlik uyarıları, spam yakalamaları ve önemli sistem bildirimlerini takip et.",
        "stats": [
            {"value": "3", "label": "Bildirim"},
            {"value": "2", "label": "Yeni"},
            {"value": "Açık", "label": "Uyarılar"}
        ],
        "cards": [
            {"title": "Anlık Uyarılar", "text": "Önemli güvenlik olayları hızlı şekilde gösterilir."},
            {"title": "Spam Alarmı", "text": "Riskli SMS yakalandığında kullanıcıyı bilgilendirmek için hazırdır."},
            {"title": "Sistem Durumu", "text": "Koruma motoru ve lisans durumu bildirimleri buradan izlenir."},
            {"title": "Sessiz Mod", "text": "Daha sonra kullanıcı tercihine göre bildirim yoğunluğu ayarlanabilir."}
        ],
        "rows": [
            {"name": "Bildirim Durumu", "value": "Açık"},
            {"name": "Yeni Uyarı", "value": "2 adet"},
            {"name": "Spam Uyarısı", "value": "Aktif"},
            {"name": "Son Bildirim", "value": "15 dk önce"}
        ],
        "primary_label": "Bildirimleri Gör",
        "primary_href": "/u/notifications"
    },
    "license": {
        "icon": "🔑",
        "title": "Lisans Merkezi",
        "description": "Premium üyelik, lisans durumu ve hesap yetkilerini tek ekranda yönet.",
        "stats": [
            {"value": "PRO", "label": "Plan"},
            {"value": "Aktif", "label": "Durum"},
            {"value": "2099", "label": "Bitiş"}
        ],
        "cards": [
            {"title": "Premium Durumu", "text": "Hesabın premium özelliklere erişim durumunu gösterir."},
            {"title": "Lisans Anahtarı", "text": "Kullanıcıya özel lisans bilgisi burada yönetilebilir."},
            {"title": "Hesap Yetkisi", "text": "Aktif, pasif veya deneme kullanıcı ayrımı için hazırdır."},
            {"title": "Satın Alma Akışı", "text": "Ödeme ve yükseltme ekranlarına bağlanacak ana merkezdir."}
        ],
        "rows": [
            {"name": "Lisans", "value": "Aktif"},
            {"name": "Plan", "value": "PRO"},
            {"name": "Hesap Tipi", "value": "Kullanıcı"},
            {"name": "Koruma Yetkisi", "value": "Açık"}
        ],
        "primary_label": "Lisansı Kontrol Et",
        "primary_href": "/u/license"
    },
    "settings": {
        "icon": "⚙️",
        "title": "Ayarlar",
        "description": "Koruma hassasiyeti, bildirimler ve hesap tercihlerini düzenle.",
        "stats": [
            {"value": "Açık", "label": "Koruma"},
            {"value": "Yüksek", "label": "Hassasiyet"},
            {"value": "TR", "label": "Dil"}
        ],
        "cards": [
            {"title": "Koruma Ayarı", "text": "Spam filtre hassasiyetini kullanıcının tercihine göre ayarlama alanı."},
            {"title": "Bildirim Tercihleri", "text": "Hangi olaylarda uyarı gösterileceği buradan yönetilebilir."},
            {"title": "Dil ve Görünüm", "text": "Türkçe/İngilizce ve tema tercihleri için altyapı hazırdır."},
            {"title": "Hesap Güvenliği", "text": "Şifre değişimi ve oturum kontrolü için yönlendirme alanıdır."}
        ],
        "rows": [
            {"name": "Koruma", "value": "Açık"},
            {"name": "Bildirim", "value": "Açık"},
            {"name": "Dil", "value": "Türkçe"},
            {"name": "Tema", "value": "Premium Koyu"}
        ],
        "primary_label": "Ayarları Güncelle",
        "primary_href": "/u/settings"
    },
    "community": {
        "icon": "👥",
        "title": "Topluluk",
        "description": "Spam kaynakları, güvenli numaralar ve topluluk katkıları için merkez.",
        "stats": [
            {"value": "Beta", "label": "Durum"},
            {"value": "0", "label": "Katkı"},
            {"value": "Yakında", "label": "Paylaşım"}
        ],
        "cards": [
            {"title": "Topluluk Bildirimi", "text": "Kullanıcıların spam numaraları bildirebileceği alan hazırlanır."},
            {"title": "Güvenli Kaynaklar", "text": "Güvenilir servis numaralarının listelenmesi için uygundur."},
            {"title": "Spam Haritası", "text": "Yoğun spam kaynakları için ileride istatistik alanı eklenebilir."},
            {"title": "Beta Programı", "text": "İlk kullanıcı geri bildirimlerini toplamak için kullanılabilir."}
        ],
        "rows": [
            {"name": "Topluluk Modu", "value": "Beta"},
            {"name": "Paylaşım", "value": "Kapalı"},
            {"name": "Geri Bildirim", "value": "Hazır"},
            {"name": "Durum", "value": "Geliştiriliyor"}
        ],
        "primary_label": "Topluluğu Aç",
        "primary_href": "/u/community"
    },
    "legal": {
        "icon": "⚖️",
        "title": "Telif ve Yasal Bildirim",
        "description": "SpamShield PRO kullanım koşulları, telif bildirimi ve yasal bilgilendirme alanı.",
        "stats": [
            {"value": "2026", "label": "Telif"},
            {"value": "PRO", "label": "Ürün"},
            {"value": "TR", "label": "Bölge"}
        ],
        "cards": [
            {"title": "Telif Hakkı", "text": "SpamShield PRO arayüzü, adı, tasarımı ve yazılım yapısı izinsiz kopyalanamaz."},
            {"title": "Kullanım Sorumluluğu", "text": "Uygulama güvenlik desteği sağlar; kullanıcı kararlarını tamamen devralmaz."},
            {"title": "Veri Güvenliği", "text": "Kullanıcı verilerinin korunması için güvenli akışlar hedeflenir."},
            {"title": "Yasal Bildirim", "text": "Ticari kullanım, dağıtım ve lisanslama sahibinin iznine bağlıdır."}
        ],
        "rows": [
            {"name": "Ürün", "value": "SpamShield PRO"},
            {"name": "Telif", "value": "Tüm hakları saklıdır"},
            {"name": "Sürüm", "value": "Beta"},
            {"name": "Kapsam", "value": "SMS güvenliği"}
        ],
        "primary_label": "Ana Ekrana Dön",
        "primary_href": "/radial"
    }
}


def render_user_module_page(module_key):
    if module_key != "legal" and not login_required():
        return redirect(url_for("login"))

    page = USER_MODULES.get(module_key)
    if not page:
        return redirect(url_for("radial"))

    return render_template("user_module.html", page=page)


@app.route("/u/protection")
def user_protection():
    return render_user_module_page("protection")


@app.route("/u/reports")
def user_reports():
    return render_user_module_page("reports")


@app.route("/u/blocked")
def user_blocked():
    return render_user_module_page("blocked")


@app.route("/u/analysis")
def user_analysis():
    return render_user_module_page("analysis")


@app.route("/u/notifications")
def user_notifications():
    return render_user_module_page("notifications")


@app.route("/u/license")
def user_license():
    return render_user_module_page("license")


@app.route("/u/settings")
def user_settings():
    return render_user_module_page("settings")


@app.route("/u/community")
def user_community():
    return render_user_module_page("community")


@app.route("/u/legal")
def user_legal():
    return render_user_module_page("legal")

