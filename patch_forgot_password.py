from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

new_func = '''@app.route("/forgot-password", methods=["GET", "POST"])
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
        user["reset_code_last_request_at"] = now_ts
        save_users(users)

        return render_template(
            "forgot.html",
            success="Kod hazır!",
            reset_code=reset_code,
            username=username,
            expires_at=expires_at
        )

    return render_template("forgot.html")'''

pattern = r'@app\.route\("/forgot-password", methods=\["GET", "POST"\]\)\ndef forgot_password\(\):.*?\n\n@app\.route\("/reset-password", methods=\["GET", "POST"\]\)'
m = re.search(pattern, text, flags=re.S)

if not m:
    print("HATA: forgot_password fonksiyonu bulunamadı.")
    raise SystemExit(1)

replacement = new_func + '\n\n@app.route("/reset-password", methods=["GET", "POST"])'
text = re.sub(pattern, replacement, text, count=1, flags=re.S)

p.write_text(text, encoding="utf-8")
print("OK: forgot_password fonksiyonu güncellendi.")
