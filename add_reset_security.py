from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

pattern = r'''@app\.route\("/reset-password", methods=\["GET", "POST"\]\)
def reset_password\(\):
.*?
    return render_template\("reset.html"\)'''

new_func = '''@app.route("/reset-password", methods=["GET", "POST"])
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

    return render_template("reset.html")'''

m = re.search(pattern, text, flags=re.S)
if not m:
    print("HATA: reset_password fonksiyonu bulunamadı.")
    raise SystemExit(1)

text = re.sub(pattern, new_func, text, count=1, flags=re.S)

text = text.replace(
    'user["reset_code_used"] = False\n        user["reset_code_last_request_at"] = now_ts',
    'user["reset_code_used"] = False\n        user["reset_attempts"] = 0\n        user["reset_code_last_request_at"] = now_ts'
)

p.write_text(text, encoding="utf-8")
print("OK: reset güvenliği eklendi.")
