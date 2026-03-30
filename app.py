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
ORDERS_FILE = "orders.json"

PLANS = {
    "pro30": {
        "name": "PRO 30 Gün",
        "days": 30,
        "price": "99 TL"
    },
    "pro90": {
        "name": "PRO 90 Gün",
        "days": 90,
        "price": "249 TL"
    },
    "pro365": {
        "name": "PRO 365 Gün",
        "days": 365,
        "price": "799 TL"
    }
}

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

def generate_order_id():
    return "ORD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

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
# ORDERS
# -----------------------
def load_orders():
    return read_json(ORDERS_FILE, [])

def save_orders(orders):
    write_json(ORDERS_FILE, orders)

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

def issue_paid_license(username, plan_key):
    users = load_users()
    licenses = load_licenses()
    orders = load_orders()

    if username not in users:
        return False, "Kullanıcı bulunamadı.", None

    if plan_key not in PLANS:
        return False, "Geçersiz plan.", None

    plan = PLANS[plan_key]
    days = int(plan["days"])
    now = datetime.now()

    while True:
        license_key = "PAY-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        if license_key not in licenses:
            break

    current_expiry_raw = users[username].get("license_expiry", "")
    try:
        current_expiry = datetime.strptime(current_expiry_raw, "%Y-%m-%d")
        base_date = current_expiry if current_expiry > now else now
    except:
        base_date = now

    new_expiry = base_date + timedelta(days=days)

    users[username]["license_type"] = "pro"
    users[username]["license_key"] = license_key
    users[username]["license_expiry"] = new_expiry.strftime("%Y-%m-%d")

    licenses[license_key] = {
        "days": days,
        "used": True,
        "used_by": username,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "used_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "payment_simulation",
        "plan_key": plan_key
    }

    order_id = generate_order_id()
    orders.append({
        "order_id": order_id,
        "username": username,
        "plan_key": plan_key,
        "plan_name": plan["name"],
        "price": plan["price"],
        "days": days,
        "license_key": license_key,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "paid"
    })

    save_users(users)
    save_licenses(licenses)
    save_orders(orders)

    return True, "Ödeme başarılı, lisans otomatik tanımlandı.", {
        "order_id": order_id,
        "plan_name": plan["name"],
        "price": plan["price"],
        "days": days,
        "license_key": license_key,
        "expiry": new_expiry.strftime("%Y-%m-%d")
    }

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
# PRICING
# -----------------------
@app.route("/pricing")
def pricing():
    if not login_required():
        return redirect(url_for("login"))

    settings = load_settings()
    return render_template(
        "pricing.html",
        app_name=settings.get("app_name", "SpamShield Premium"),
        plans=PLANS,
        username=current_username()
    )

# -----------------------
# BUY PLAN (PAYMENT SIMULATION)
# -----------------------
@app.route("/buy-plan/<plan_key>", methods=["POST"])
def buy_plan(plan_key):
    if not login_required():
        return redirect(url_for("login"))

    ok, msg, order_data = issue_paid_license(current_username(), plan_key)

    if not ok:
        return f"<h2>Hata</h2><p>{msg}</p><a href='/pricing'>Geri dön</a>"

    settings = load_settings()
    return render_template(
        "payment_success.html",
        app_name=settings.get("app_name", "SpamShield Premium"),
        message=msg,
        order=order_data
    )

# -----------------------
# BUY LICENSE OLD ROUTE
# -----------------------
@app.route("/buy-license")
def buy_license():
    return redirect(url_for("pricing"))

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
if __name__ == "__main__":
    load_users()
    load_settings()
    if not os.path.exists(LICENSES_FILE):
        save_licenses({})
    if not os.path.exists(ORDERS_FILE):
        save_orders([])
    app.run(host="0.0.0.0", port=5000, debug=True)
