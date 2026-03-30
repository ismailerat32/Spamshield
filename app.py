from flask import Flask, render_template, redirect, url_for, request, session
import json
import os
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.secret_key = "spamshield-secret-key"

USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"
LICENSES_FILE = "licenses.json"

# -----------------------
# LICENSE GENERATOR
# -----------------------
def generate_license_key():
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return "SPM-" + "-".join(parts)

# Demo lisansları
VALID_PRO_LICENSES = {
    "PRO-2026-AAAA-BBBB": 30,
    "PRO-2026-CCCC-DDDD": 90,
    "PRO-2026-EEEE-FFFF": 365
}

# -----------------------
# USERS
# -----------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

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
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# -----------------------
# SETTINGS
# -----------------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    settings = {
        "app_name": "SpamShield Premium",
        "trial_days": 7,
        "license_mode": "trial_pro"
    }
    save_settings(settings)
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

# -----------------------
# LICENSE POOL
# -----------------------
def load_licenses():
    if os.path.exists(LICENSES_FILE):
        with open(LICENSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_licenses(licenses):
    with open(LICENSES_FILE, "w", encoding="utf-8") as f:
        json.dump(licenses, f, ensure_ascii=False, indent=4)

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
# HELPERS
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

def activate_demo_pro_license(username, entered_key):
    entered_key = entered_key.strip().upper()
    users = load_users()

    if username not in users:
        return False, "Kullanıcı bulunamadı."

    if entered_key not in VALID_PRO_LICENSES:
        return False, "Lisans kodu geçersiz."

    extra_days = VALID_PRO_LICENSES[entered_key]
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

    save_users(users)
    return True, f"PRO aktif edildi. +{extra_days} gün eklendi."

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
    return render_template("users.html", users=load_users(), username=current_username())

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
            if not ok:
                ok, msg = activate_demo_pro_license(username, entered_key)

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
if __name__ == "__main__":
    load_users()
    load_settings()
    if not os.path.exists(LICENSES_FILE):
        save_licenses({})
    app.run(host="0.0.0.0", port=5000, debug=True)
