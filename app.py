# =========================================
# SpamShield © 2026
# Owner: ismail erat
# All rights reserved.
# Unauthorized copying, resale, distribution,
# reverse engineering, or modification of this
# software without permission is prohibited.
# =========================================

from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import json
import os
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-now")
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

def apply_runtime_env_overrides():
    import json
    users_file = globals().get("USERS_FILE", "data/users.json")
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if admin_password and os.path.exists(users_file):
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)

            if "admin" in users:
                users["admin"]["password"] = admin_password
                with open(users_file, "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("ENV_OVERRIDE_ERROR:", e)

apply_runtime_env_overrides()
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-this-now")

USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"
LICENSES_FILE = "licenses.json"
LOGS_FILE = "logs.json"
FEEDBACK_FILE = "feedback.json"

def load_feedback():
    return read_json(FEEDBACK_FILE, [])

def save_feedback(items):
    write_json(FEEDBACK_FILE, items)

def load_logs():
    return read_json(LOGS_FILE, [])

def save_logs(logs):
    write_json(LOGS_FILE, logs)

# -----------------------
# BASIC HELPERS
# -----------------------
def read_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# -----------------------
# LICENSE KEY GENERATORS
# -----------------------
def generate_license_key():
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return "SPM-" + "-".join(parts)


def generate_reset_code():
    import random
    import string
    return "RST-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_pool_license(days=30):
    licenses = load_licenses()

    while True:
        key = "LIC-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        if key not in licenses:
            break

    licenses[key] = {
        "days": int(days),
        "used": False,
        "used_by": "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_licenses(licenses)
    return key

# -----------------------
# USERS
# -----------------------
def load_users():
    users = read_json(USERS_FILE, None)
    if users is not None:
        return users

    users = {
        "admin": {
            "password": "1234",
            "role": "admin",
            "license_type": "pro",
            "license_key": "MASTER-KEY",
            "license_expiry": "2099-01-01"
        }
    }
    save_users(users)
    return users

def save_users(users):
    write_json(USERS_FILE, users)

# -----------------------
# SETTINGS
# -----------------------
def load_settings():
    settings = read_json(SETTINGS_FILE, None)
    if settings is not None:
        return settings

    settings = {
        "app_name": "SpamShield Premium",
        "trial_days": 7,
        "license_mode": "trial_pro"
    }
    save_settings(settings)
    return settings

def save_settings(settings):
    write_json(SETTINGS_FILE, settings)

# -----------------------
# LICENSE POOL
# -----------------------
def load_licenses():
    return read_json(LICENSES_FILE, {})

def save_licenses(licenses):
    write_json(LICENSES_FILE, licenses)

# -----------------------
# SESSION / AUTH HELPERS
# -----------------------
def login_required():
    return session.get("logged_in", False)

def current_username():
    return session.get("username", "")

def current_user():
    return load_users().get(current_username(), {})

def is_admin():
    return current_user().get("role") == "admin"

def admin_required():
    return login_required() and is_admin()

# -----------------------
# LICENSE HELPERS
# -----------------------
def is_license_active(user):
    try:
        expiry = datetime.strptime(user.get("license_expiry", ""), "%Y-%m-%d")
        return expiry >= datetime.now()
    except:
        return False

def days_left(user):
    try:
        expiry = datetime.strptime(user.get("license_expiry", ""), "%Y-%m-%d")
        delta = expiry - datetime.now()
        return max(delta.days, 0)
    except:
        return 0

def activate_pool_license(username, entered_key):
    entered_key = entered_key.strip().upper()
    users = load_users()
    licenses = load_licenses()

    if username not in users:
        return False, "Kullanıcı bulunamadı."

    if entered_key not in licenses:
        return False, "Geçersiz lisans kodu."

    if licenses[entered_key]["used"]:
        return False, "Bu lisans zaten kullanılmış."

    extra_days = int(licenses[entered_key].get("days", 30))
    now = datetime.now()

    current_expiry_raw = users[username].get("license_expiry", "")
    try:
        current_expiry = datetime.strptime(current_expiry_raw, "%Y-%m-%d")
        base_date = current_expiry if current_expiry > now else now
    except:
        base_date = now

    new_expiry = base_date + timedelta(days=extra_days)

    users[username]["license_type"] = "pro"
    users[username]["license_key"] = entered_key
    users[username]["license_expiry"] = new_expiry.strftime("%Y-%m-%d")

    licenses[entered_key]["used"] = True
    licenses[entered_key]["used_by"] = username
    licenses[entered_key]["used_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_users(users)
    save_licenses(licenses)

    return True, f"PRO aktif edildi. +{extra_days} gün eklendi."

# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    if login_required():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()

        users = load_users()

        if username in users and users[username]["password"] == password:
            session["logged_in"] = True
            session["username"] = username

            user = users[username]
            if not is_license_active(user):
                return redirect(url_for("landing"))

            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Kullanıcı adı veya şifre yanlış.")

    return render_template("login.html", error="")

# -----------------------
# REGISTER
# -----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        password2 = request.form.get("password2", "").strip()

        users = load_users()
        settings = load_settings()

        if not username or not password or not password2:
            return render_template("register.html", error="Tüm alanları doldurun.")

        if username in users:
            return render_template("register.html", error="Bu kullanıcı zaten var.")

        if password != password2:
            return render_template("register.html", error="Şifreler eşleşmiyor.")

        expiry = datetime.now() + timedelta(days=settings.get("trial_days", 7))

        users[username] = {
            "password": password,
            "role": "user",
            "license_type": "trial",
            "license_key": "TRIAL",
            "license_expiry": expiry.strftime("%Y-%m-%d")
        }

        save_users(users)
        return redirect(url_for("login"))

    return render_template("register.html", error="")

# -----------------------
# DASHBOARD
# -----------------------
@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    users = load_users()
    settings = load_settings()
    username = current_username()
    user = users.get(username, {})

    if not is_license_active(user):
        return redirect(url_for("landing"))

    return render_template(
        "dashboard.html",
        username=username,
        total_users=len(users),
        app_name=settings.get("app_name", "SpamShield Premium"),
        days_left="∞" if user.get("role") == "admin" else days_left(user),
        license_type=user.get("license_type", "trial"),
        license_key=user.get("license_key", "")
    )

# -----------------------
# USERS
# -----------------------
@app.route("/users")
def users():
    if not admin_required():
        return redirect(url_for("dashboard"))

    return render_template(
        "users.html",
        users=load_users(),
        username=current_username()
    )

# -----------------------
# ADD USER
# -----------------------
@app.route("/add-user", methods=["GET", "POST"])
def add_user():
    if not admin_required():
        return redirect(url_for("dashboard"))

    message = ""
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "user").strip()

        users = load_users()
        settings = load_settings()

        if not username or not password:
            error = "Kullanıcı adı ve şifre zorunlu."
        elif username in users:
            error = "Bu kullanıcı zaten mevcut."
        else:
            expiry = datetime.now() + timedelta(days=settings.get("trial_days", 7))

            users[username] = {
                "password": password,
                "role": role,
                "license_type": "trial",
                "license_key": generate_license_key(),
                "license_expiry": expiry.strftime("%Y-%m-%d")
            }
            save_users(users)
            message = "Kullanıcı + lisans oluşturuldu."

    return render_template("add_user.html", message=message, error=error)

# -----------------------
# DELETE USER
# -----------------------
@app.route("/delete-user/<username>", methods=["POST"])
def delete_user(username):
    if not admin_required():
        return redirect(url_for("dashboard"))

    username = username.strip().lower()
    users = load_users()

    if username == "admin":
        return redirect(url_for("users"))

    if username in users:
        del users[username]
        save_users(users)

    return redirect(url_for("users"))

# -----------------------
# MANAGE LICENSE
# -----------------------
@app.route("/manage-license/<username>", methods=["GET", "POST"])
def manage_license(username):
    if not admin_required():
        return redirect(url_for("dashboard"))

    username = username.strip().lower()
    users = load_users()

    if username not in users:
        return redirect(url_for("users"))

    message = ""
    error = ""
    user = users[username]

    if request.method == "POST":
        action = request.form.get("action", "").strip()

        if action == "extend":
            try:
                extra_days = int(request.form.get("extra_days", "0").strip())
                if extra_days <= 0:
                    error = "Geçerli bir gün sayısı gir."
                else:
                    now = datetime.now()
                    current_expiry_raw = user.get("license_expiry", "")
                    try:
                        current_expiry = datetime.strptime(current_expiry_raw, "%Y-%m-%d")
                        base_date = current_expiry if current_expiry > now else now
                    except:
                        base_date = now

                    new_expiry = base_date + timedelta(days=extra_days)
                    user["license_expiry"] = new_expiry.strftime("%Y-%m-%d")
                    save_users(users)
                    message = f"{username} için +{extra_days} gün eklendi."
            except:
                error = "Gün sayısı hatalı."

        elif action == "make_pro":
            user["license_type"] = "pro"
            if user.get("license_key") in ["", "TRIAL"]:
                user["license_key"] = generate_license_key()
            if not user.get("license_expiry"):
                user["license_expiry"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            save_users(users)
            message = f"{username} PRO yapıldı."

        elif action == "make_trial":
            settings = load_settings()
            user["license_type"] = "trial"
            user["license_key"] = "TRIAL"
            user["license_expiry"] = (datetime.now() + timedelta(days=settings.get("trial_days", 7))).strftime("%Y-%m-%d")
            save_users(users)
            message = f"{username} trial yapıldı."

        elif action == "reset_license":
            user["license_key"] = generate_license_key()
            save_users(users)
            message = f"{username} için lisans kodu yenilendi."

    users = load_users()
    user = users[username]

    return render_template(
        "manage_license.html",
        target_username=username,
        target_user=user,
        message=message,
        error=error,
        days_left=days_left(user)
    )

# -----------------------
# CHANGE PASSWORD
# -----------------------
@app.route("/change", methods=["GET", "POST"])
def change():
    if not login_required():
        return redirect(url_for("login"))

    message = ""
    error = ""

    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        new_password2 = request.form.get("new_password2", "").strip()

        users = load_users()
        username = current_username()

        if username not in users:
            error = "Kullanıcı bulunamadı."
        elif users[username]["password"] != current_password:
            error = "Mevcut şifre yanlış."
        elif not new_password:
            error = "Yeni şifre boş olamaz."
        elif new_password != new_password2:
            error = "Yeni şifreler eşleşmiyor."
        else:
            users[username]["password"] = new_password
            save_users(users)
            message = "Şifre başarıyla değiştirildi."

    return render_template("change.html", message=message, error=error)

# -----------------------
# SETTINGS
# -----------------------
@app.route("/setting", methods=["GET", "POST"])
def setting():
    if not admin_required():
        return redirect(url_for("dashboard"))

    settings = load_settings()
    message = ""

    if request.method == "POST":
        app_name = request.form.get("app_name", "").strip()
        trial_days = request.form.get("trial_days", "").strip()
        license_mode = request.form.get("license_mode", "").strip()

        if app_name:
            settings["app_name"] = app_name

        try:
            settings["trial_days"] = int(trial_days)
        except:
            pass

        if license_mode:
            settings["license_mode"] = license_mode

        save_settings(settings)
        message = "Ayarlar kaydedildi."

    return render_template("setting.html", config=settings, message=message)

# -----------------------
# ACTIVATE LICENSE
# -----------------------
@app.route("/activate-license", methods=["GET", "POST"])
def activate_license():
    if not login_required():
        return redirect(url_for("login"))

    message = ""
    error = ""
    username = current_username()

    if request.method == "POST":
        entered_key = request.form.get("license_key", "").strip()

        if not entered_key:
            error = "Lisans kodu boş olamaz."
        else:
            ok, msg = activate_pool_license(username, entered_key)
            if ok:
                message = msg
            else:
                error = msg

    users = load_users()
    user = users.get(username, {})

    return render_template(
        "activate_license.html",
        message=message,
        error=error,
        current_license=user.get("license_key", ""),
        license_type=user.get("license_type", "trial"),
        days_left="∞" if user.get("role") == "admin" else days_left(user)
    )

# -----------------------
# BUY LICENSE (SIMULATION)
# -----------------------
@app.route("/buy-license")
def buy_license():
    if not login_required():
        return redirect(url_for("login"))

    key = generate_pool_license(30)

    return f"""
    <html>
    <head><meta charset='UTF-8'><title>Satın Alma Başarılı</title></head>
    <body style="background:#0b1220;color:white;font-family:Arial;padding:30px;">
        <h2>Satın alma başarılı</h2>
        <p>Tek kullanımlık lisans kodun:</p>
        <p style="font-size:24px;font-weight:bold;">{key}</p>
        <p>Bu kod bir kez kullanılabilir.</p>
        <a href="/activate-license" style="color:#60a5fa;">Lisansı aktifleştir</a><br><br>
        <a href="/dashboard" style="color:#60a5fa;">Dashboard'a dön</a>
    </body>
    </html>
    """

# -----------------------
# ADMIN LICENSE PANEL
# -----------------------
@app.route("/admin/licenses", methods=["GET", "POST"])
def admin_licenses():
    if not admin_required():
        return redirect(url_for("dashboard"))

    message = ""
    error = ""

    if request.method == "POST":
        try:
            days = int(request.form.get("days", "30").strip())
            if days <= 0:
                error = "Geçerli gün sayısı gir."
            else:
                new_key = generate_pool_license(days)
                message = f"Yeni lisans oluşturuldu: {new_key}"
        except:
            error = "Gün sayısı hatalı."

    licenses = load_licenses()
    license_items = sorted(
        licenses.items(),
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )

    return render_template(
        "admin_licenses.html",
        licenses=license_items,
        message=message,
        error=error
    )

# -----------------------
# LANDING
# -----------------------
@app.route("/landing")
def landing():
    settings = load_settings()
    return render_template(
        "landing.html",
        app_name=settings.get("app_name", "SpamShield Premium")
    )

# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------
# RUN
# -----------------------
# -----------------------
# LOG API
# -----------------------

@app.route("/api/logs")
def api_logs():
    logs = load_logs()
    logs = list(reversed(logs))[:100]
    return jsonify({
        "status": "success",
        "total": len(logs),
        "logs": logs
    })


@app.route("/api/add-log", methods=["POST"])
def api_add_log():
    try:
        data = request.get_json(force=True)

        new_log = {
            "timestamp": data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": data.get("from", "BILINMEYEN"),
            "status": data.get("status", "TEMIZ"),
            "score": data.get("score", 0),
            "message": data.get("message", "")
        }

        logs = load_logs()
        logs.append(new_log)

        if len(logs) > 1000:
            logs = logs[-1000:]

        save_logs(logs)

        return jsonify({
            "status": "success",
            "log": new_log
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# -----------------------
# FEEDBACK API
# -----------------------

@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    try:
        data = request.get_json(force=True)

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "correct": bool(data.get("correct")),
            "log": data.get("log", {})
        }

        items = load_feedback()
        items.append(entry)

        if len(items) > 2000:
            items = items[-2000:]

        save_feedback(items)

        return jsonify({
            "status": "success",
            "feedback": entry
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# -----------------------
# STATS API
# -----------------------

@app.route("/api/stats")
def api_stats():
    try:
        logs = load_logs()

        spam = 0
        temiz = 0

        for log in logs:
            status = str(log.get("status", "")).upper()
            if status == "SPAM":
                spam += 1
            elif status == "TEMIZ":
                temiz += 1

        return jsonify({
            "status": "success",
            "total": len(logs),
            "spam": spam,
            "temiz": temiz
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    import time

    users = load_users()

    if request.method == "POST":
        username = request.form.get("username", "").strip()

        if not username:
            return render_template("forgot.html", error="Kullanıcı adı gerekli")

        if username not in users:
            return render_template("forgot.html", error="Kullanıcı bulunamadı")

        user = users[username]
        now_ts = int(time.time())
        last_request_at = int(user.get("reset_code_last_request_at", 0) or 0)
        wait_seconds = 30 - (now_ts - last_request_at)

        if last_request_at and wait_seconds > 0:
            return render_template(
                "forgot.html",
                error=f"Yeni kod için {wait_seconds} saniye bekle",
                username=username
            )

        reset_code = generate_reset_code()
        expires_at = now_ts + (3 * 60)

        user["reset_code"] = reset_code
        user["reset_code_expires_at"] = expires_at
        user["reset_code_used"] = False
        user["reset_attempts"] = 0
        user["reset_code_last_request_at"] = now_ts
        save_users(users)

        return render_template(
            "forgot.html",
            success="Kod hazır!",
            reset_code=reset_code,
            username=username,
            expires_at=expires_at
        )

    return render_template("forgot.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    import time

    users = load_users()

    if request.method == "POST":
        username = request.form.get("username") or request.args.get("username", "")
        code = request.form.get("code") or request.args.get("code", "")

        username = username.strip()
        code = code.strip()
        new_password = request.form.get("password", "").strip()

        if not username or not code or not new_password:
            return render_template("reset.html", error="Tüm alanları doldur")

        if username not in users:
            return render_template("reset.html", error="Kullanıcı bulunamadı")

        user = users[username]
        saved_code = str(user.get("reset_code", "")).strip()
        expires_at = int(user.get("reset_code_expires_at", 0) or 0)
        used = bool(user.get("reset_code_used", False))
        now_ts = int(time.time())

        attempts = int(user.get("reset_attempts", 0) or 0)
        max_attempts = 5

        if attempts >= max_attempts:
            return render_template("reset.html", error="Çok fazla hatalı deneme yapıldı. Yeni kod oluştur.")

        if not saved_code or saved_code != code:
            user["reset_attempts"] = attempts + 1
            save_users(users)
            kalan = max_attempts - user["reset_attempts"]
            if kalan < 0:
                kalan = 0
            return render_template("reset.html", error=f"Kod yanlış veya geçersiz. Kalan deneme: {kalan}")

        if used:
            return render_template("reset.html", error="Bu kod daha önce kullanılmış")

        if not expires_at or now_ts > expires_at:
            user["reset_code"] = ""
            user["reset_code_expires_at"] = 0
            user["reset_code_used"] = False
            user["reset_attempts"] = 0
            save_users(users)
            return render_template("reset.html", error="Kodun süresi dolmuş")

        user["password"] = new_password
        user["reset_code_used"] = True
        user["reset_code"] = ""
        user["reset_code_expires_at"] = 0
        user["reset_attempts"] = 0
        save_users(users)

        return render_template("reset.html", success="Şifre başarıyla değiştirildi")

    return render_template("reset.html")
if __name__ == "__main__":
    load_users()
    load_settings()
    if not os.path.exists(LICENSES_FILE):
        save_licenses({})
    port = int(os.environ.get("PORT", 5000))
local_debug = os.environ.get("FLASK_DEBUG", "0") == "1"
app.run(host="0.0.0.0", port=port, debug=local_debug)


# -----------------------
# PASSWORD RESET
# -----------------------