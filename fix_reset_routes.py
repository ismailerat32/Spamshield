from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old_block = '''@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    users = load_users()

    if request.method == "POST":
        username = request.form.get("username", "").strip()

        if not username:
            return render_template("forgot.html", error="Kullanıcı adı gerekli")

        if username not in users:
            return render_template("forgot.html", error="Kullanıcı bulunamadı")

        reset_code = generate_reset_code()
        users[username]["reset_code"] = reset_code
        save_users(users)

        return render_template(
            "forgot.html",
            success="Şifre sıfırlama kodu oluşturuldu",
            reset_code=reset_code,
            username=username
        )

    return render_template("forgot.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    users = load_users()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        code = request.form.get("code", "").strip()
        new_password = request.form.get("password", "").strip()

        if not username or not code or not new_password:
            return render_template("reset.html", error="Tüm alanları doldur")

        if username not in users:
            return render_template("reset.html", error="Kullanıcı bulunamadı")

        saved_code = users[username].get("reset_code", "").strip()

        if not saved_code or saved_code != code:
            return render_template("reset.html", error="Kod yanlış veya geçersiz")

        users[username]["password"] = new_password
        users[username]["reset_code"] = ""
        save_users(users)

        return render_template("reset.html", success="Şifre başarıyla değiştirildi")

    return render_template("reset.html")'''

new_block = '''@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    import time

    users = load_users()

    if request.method == "POST":
        username = request.form.get("username", "").strip()

        if not username:
            return render_template("forgot.html", error="Kullanıcı adı gerekli")

        if username not in users:
            return render_template("forgot.html", error="Kullanıcı bulunamadı")

        reset_code = generate_reset_code()
        expires_at = int(time.time()) + (15 * 60)

        users[username]["reset_code"] = reset_code
        users[username]["reset_code_expires_at"] = expires_at
        users[username]["reset_code_used"] = False
        save_users(users)

        return render_template(
            "forgot.html",
            success="Şifre sıfırlama kodu oluşturuldu (15 dakika geçerli)",
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
        username = request.form.get("username", "").strip()
        code = request.form.get("code", "").strip()
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

        if not saved_code or saved_code != code:
            return render_template("reset.html", error="Kod yanlış veya geçersiz")

        if used:
            return render_template("reset.html", error="Bu kod daha önce kullanılmış")

        if not expires_at or now_ts > expires_at:
            user["reset_code"] = ""
            user["reset_code_expires_at"] = 0
            user["reset_code_used"] = False
            save_users(users)
            return render_template("reset.html", error="Kodun süresi dolmuş")

        user["password"] = new_password
        user["reset_code_used"] = True
        user["reset_code"] = ""
        user["reset_code_expires_at"] = 0
        save_users(users)

        return render_template("reset.html", success="Şifre başarıyla değiştirildi")

    return render_template("reset.html")'''

if old_block not in text:
    print("HATA: Eski route bloğu birebir bulunamadı. Dosya değiştirilmedi.")
    raise SystemExit(1)

text = text.replace(old_block, new_block, 1)
p.write_text(text, encoding="utf-8")

print("OK: Şifre sıfırlama route'ları süreli ve tek kullanımlık hale getirildi.")
