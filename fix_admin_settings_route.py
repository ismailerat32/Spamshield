import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Varsa eski admin/settings route'unu temizle
content = re.sub(
    r'@app\.route\("/admin/settings", methods=\["GET", "POST"\]\).*?return render_template\("admin_settings\.html", settings=settings\)\n',
    '',
    content,
    flags=re.DOTALL
)

settings_block = '''
# =========================
# ⚙️ ADMIN SETTINGS
# =========================
RUNTIME_SETTINGS_FILE = "spamshield_runtime_settings.json"

def load_runtime_settings():
    defaults = {
        "enable_notifications": True,
        "enable_vibration": True,
        "enable_auto_delete": False,
        "sms_limit": 5,
        "poll_interval": 10,
        "spam_threshold": 40
    }

    if not os.path.exists(RUNTIME_SETTINGS_FILE):
        with open(RUNTIME_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=2)
        return defaults

    try:
        with open(RUNTIME_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            defaults.update(data)
        return defaults
    except Exception:
        return defaults

def save_runtime_settings(data):
    with open(RUNTIME_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return redirect(url_for("dashboard"))

    settings = load_runtime_settings()

    if request.method == "POST":
        settings["enable_notifications"] = "enable_notifications" in request.form
        settings["enable_vibration"] = "enable_vibration" in request.form
        settings["enable_auto_delete"] = "enable_auto_delete" in request.form

        try:
            settings["sms_limit"] = int(request.form.get("sms_limit", 5))
        except:
            settings["sms_limit"] = 5

        try:
            settings["poll_interval"] = int(request.form.get("poll_interval", 10))
        except:
            settings["poll_interval"] = 10

        try:
            settings["spam_threshold"] = int(request.form.get("spam_threshold", 40))
        except:
            settings["spam_threshold"] = 40

        save_runtime_settings(settings)

    return render_template("admin_settings.html", settings=settings)
'''

content = content.replace(
    'if __name__ == "__main__":',
    settings_block + '\n\nif __name__ == "__main__":'
)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ admin/settings route eklendi")
