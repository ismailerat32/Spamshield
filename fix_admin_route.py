import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Eski admin route'u sil
content = re.sub(
    r'@app\.route\("/admin".*?return render_template\("admin_overview\.html".*?\)\n',
    '',
    content,
    flags=re.DOTALL
)

# Yeni route (doğru format)
admin_block = '''
@app.route("/admin")
def admin_overview():
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return redirect(url_for("dashboard"))

    users = load_users()
    runtime_settings = load_runtime_settings()
    spam_logs = load_spam_logs() if 'load_spam_logs' in globals() else []

    stats = {
        "total_users": len(users),
        "spam_log_count": len(spam_logs),
        "notifications": runtime_settings.get("enable_notifications", True),
        "vibration": runtime_settings.get("enable_vibration", True),
        "auto_delete": runtime_settings.get("enable_auto_delete", False),
        "sms_limit": runtime_settings.get("sms_limit", 5),
        "poll_interval": runtime_settings.get("poll_interval", 10),
        "spam_threshold": runtime_settings.get("spam_threshold", 40)
    }

    recent_logs = spam_logs[:10] if isinstance(spam_logs, list) else []

    return render_template("admin_overview.html", stats=stats, recent_logs=recent_logs)
'''

# if __name__ üstüne ekle
content = content.replace(
    'if __name__ == "__main__":',
    admin_block + '\n\nif __name__ == "__main__":'
)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ ADMIN ROUTE FIXED")
