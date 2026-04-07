from pathlib import Path
import re

app_path = Path("app.py")
text = app_path.read_text(encoding="utf-8")

marker = "# === LICENSE SYSTEM PHASE 1 START ==="
if marker in text:
    print("Lisans sistemi zaten ekli. Dosya değiştirilmedi.")
    raise SystemExit(0)

block = '''
# === LICENSE SYSTEM PHASE 1 START ===
LICENSES_FILE = "data/licenses.json"

def load_licenses():
    import json
    import os

    if not os.path.exists(LICENSES_FILE):
        with open(LICENSES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    try:
        with open(LICENSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_licenses(data):
    import json
    with open(LICENSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_license_key():
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    while True:
        parts = []
        for _ in range(3):
            parts.append("".join(random.choice(chars) for _ in range(4)))
        key = "SSHD-" + "-".join(parts)
        licenses = load_licenses()
        if key not in licenses:
            return key

def get_current_username():
    try:
        return str(session.get("username", "")).strip()
    except Exception:
        return ""

def days_left_from_expiry(expiry_str):
    from datetime import datetime
    try:
        exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        today = datetime.utcnow().date()
        return (exp - today).days
    except Exception:
        return -1

def sync_user_license(username, license_key, plan, expires_at):
    users = load_users()
    if username not in users:
        return False

    users[username]["license_key"] = license_key
    users[username]["license_type"] = plan
    users[username]["license_expiry"] = expires_at
    save_users(users)
    return True

@app.route("/admin/licenses", methods=["GET", "POST"])
def admin_licenses():
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("dashboard"))

    users = load_users()
    licenses = load_licenses()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        plan = request.form.get("plan", "pro").strip() or "pro"
        duration_days_raw = request.form.get("duration_days", "30").strip()

        if not username:
            return render_template(
                "admin_licenses.html",
                users=users,
                licenses=licenses,
                error="Kullanıcı adı gerekli"
            )

        if username not in users:
            return render_template(
                "admin_licenses.html",
                users=users,
                licenses=licenses,
                error="Kullanıcı bulunamadı"
            )

        try:
            duration_days = int(duration_days_raw)
        except Exception:
            duration_days = 30

        if duration_days < 1:
            duration_days = 1

        from datetime import datetime, timedelta

        license_key = generate_license_key()
        created_at = datetime.utcnow().strftime("%Y-%m-%d")
        expires_at = (datetime.utcnow() + timedelta(days=duration_days)).strftime("%Y-%m-%d")

        licenses[license_key] = {
            "username": username,
            "plan": plan,
            "status": "active",
            "created_at": created_at,
            "expires_at": expires_at
        }
        save_licenses(licenses)
        sync_user_license(username, license_key, plan, expires_at)

        users = load_users()
        licenses = load_licenses()

        return render_template(
            "admin_licenses.html",
            users=users,
            licenses=licenses,
            success="Lisans oluşturuldu",
            new_license_key=license_key
        )

    return render_template("admin_licenses.html", users=users, licenses=licenses)

@app.route("/my-license", methods=["GET"])
def my_license():
    if not login_required():
        return redirect(url_for("login"))

    username = get_current_username()
    users = load_users()
    licenses = load_licenses()

    if username not in users:
        return redirect(url_for("login"))

    user = users[username]
    license_key = str(user.get("license_key", "")).strip()
    license_data = licenses.get(license_key, {}) if license_key else {}
    expiry = str(user.get("license_expiry", "")).strip()
    remaining_days = days_left_from_expiry(expiry) if expiry else -1

    return render_template(
        "my_license.html",
        username=username,
        user=user,
        license_key=license_key,
        license_data=license_data,
        remaining_days=remaining_days
    )

@app.route("/activate-license", methods=["GET", "POST"])
def activate_license():
    if not login_required():
        return redirect(url_for("login"))

    username = get_current_username()
    users = load_users()
    licenses = load_licenses()

    if username not in users:
        return redirect(url_for("login"))

    if request.method == "POST":
        entered_key = request.form.get("license_key", "").strip().upper()

        if not entered_key:
            return render_template("activate_license.html", error="Lisans anahtarı gerekli")

        if entered_key not in licenses:
            return render_template("activate_license.html", error="Lisans anahtarı bulunamadı")

        lic = licenses[entered_key]
        owner = str(lic.get("username", "")).strip()

        if owner and owner != username:
            return render_template("activate_license.html", error="Bu lisans başka kullanıcıya ait")

        if lic.get("status") == "revoked":
            return render_template("activate_license.html", error="Bu lisans iptal edilmiş")

        plan = str(lic.get("plan", "pro")).strip() or "pro"
        expires_at = str(lic.get("expires_at", "")).strip()

        licenses[entered_key]["username"] = username
        licenses[entered_key]["status"] = "active"
        save_licenses(licenses)

        sync_user_license(username, entered_key, plan, expires_at)

        return render_template(
            "activate_license.html",
            success="Lisans başarıyla aktive edildi",
            license_key=entered_key
        )

    return render_template("activate_license.html")
# === LICENSE SYSTEM PHASE 1 END ===
'''

pattern = r'\nif __name__ == "__main__":'
if re.search(pattern, text):
    text = re.sub(pattern, "\n" + block + "\nif __name__ == \"__main__\":", text, count=1)
else:
    text += "\n" + block + "\n"

app_path.write_text(text, encoding="utf-8")
print("OK: app.py içine lisans sistemi eklendi.")
