from pathlib import Path

app_path = Path("app.py")
forgot_path = Path("templates/forgot.html")

text = app_path.read_text(encoding="utf-8")

old_forgot_route = '''@app.route("/forgot-password", methods=["GET", "POST"])
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

    return render_template("forgot.html")'''

new_forgot_route = '''@app.route("/forgot-password", methods=["GET", "POST"])
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

if old_forgot_route in text:
    text = text.replace(old_forgot_route, new_forgot_route, 1)
else:
    replacements = [
        ('expires_at = int(time.time()) + (15 * 60)', 'expires_at = now_ts + (3 * 60)'),
        ('success="Şifre sıfırlama kodu oluşturuldu (15 dakika geçerli)"', 'success="Kod hazır!"'),
    ]
    target = '''        reset_code = generate_reset_code()
        expires_at = int(time.time()) + (15 * 60)

        users[username]["reset_code"] = reset_code
        users[username]["reset_code_expires_at"] = expires_at
        users[username]["reset_code_used"] = False
        save_users(users)'''
    replacement = '''        user = users[username]
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
        save_users(users)'''
    if target in text:
        text = text.replace(target, replacement, 1)
    else:
        print("HATA: forgot_password bloğu bulunamadı.")
        raise SystemExit(1)

app_path.write_text(text, encoding="utf-8")

forgot_html = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Şifremi Unuttum</title>
<style>
body {
    background: linear-gradient(135deg, #0f172a, #0b1f5e, #1e3a8a);
    font-family: Arial, sans-serif;
    color: white;
    margin: 0;
    min-height: 100vh;
}
.wrap {
    max-width: 460px;
    margin: 60px auto;
    padding: 24px;
}
.card {
    background: rgba(3, 15, 45, 0.95);
    padding: 28px;
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,.25);
}
h1 {
    margin: 0 0 24px;
    font-size: 42px;
    line-height: 1.1;
}
label {
    display: block;
    margin: 16px 0 8px;
    font-size: 15px;
    color: #cbd5e1;
}
input {
    width: 100%;
    box-sizing: border-box;
    padding: 16px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,.08);
    background: #020b2a;
    color: white;
    font-size: 16px;
    outline: none;
}
button {
    width: 100%;
    margin-top: 18px;
    padding: 16px;
    border: 0;
    border-radius: 18px;
    background: #1db446;
    color: white;
    font-size: 18px;
    font-weight: bold;
}
button:disabled {
    opacity: .65;
}
.msg-ok {
    background: rgba(16, 185, 129, .18);
    border: 1px solid rgba(16, 185, 129, .35);
    color: #d1fae5;
    padding: 16px;
    border-radius: 18px;
    margin-bottom: 18px;
}
.msg-err {
    background: rgba(239, 68, 68, .14);
    border: 1px solid rgba(239, 68, 68, .35);
    color: #fee2e2;
    padding: 16px;
    border-radius: 18px;
    margin-bottom: 18px;
}
.code-box {
    margin-top: 22px;
    padding: 18px;
    border: 1px dashed rgba(255,255,255,.22);
    border-radius: 18px;
    font-size: 26px;
    font-weight: bold;
    letter-spacing: 1px;
    background: rgba(30, 64, 175, .22);
    cursor: pointer;
    user-select: all;
}
.helper {
    margin-top: 10px;
    color: #93c5fd;
    font-size: 14px;
}
.timer {
    margin-top: 14px;
    color: #fde68a;
    font-size: 15px;
    font-weight: bold;
}
.link {
    display: inline-block;
    margin-top: 18px;
    color: #bfdbfe;
    text-decoration: none;
    font-size: 16px;
}
.secondary-btn {
    display: inline-block;
    margin-top: 18px;
    padding: 12px 16px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,.12);
    background: rgba(255,255,255,.06);
    color: white;
    text-decoration: none;
}
.hidden {
    display: none;
}
</style>
</head>
<body>
<div class="wrap">
    <div class="card">
        <h1>Şifremi Unuttum</h1>

        {% if error %}
        <div class="msg-err">{{ error }}</div>
        {% endif %}

        {% if success %}
        <div class="msg-ok">{{ success }}</div>
        {% endif %}

        <form method="POST" id="forgotForm">
            <label>Kullanıcı Adı</label>
            <input type="text" name="username" placeholder="Kullanıcı adını gir" value="{{ username | default('') }}" required>
            <button type="submit" id="generateBtn">Sıfırlama Kodu Oluştur</button>
        </form>

        {% if reset_code %}
        <div class="code-box" onclick="copyCode()">{{ reset_code }}</div>
        <div class="helper" id="copyHelper">Koda dokun, panoya kopyalansın.</div>
        <div id="timer" class="timer"></div>

        <a class="link" href="/reset-password?username={{ username }}&code={{ reset_code }}">Kodum var, şifremi değiştir</a>

        <form method="POST" id="regenForm">
            <input type="hidden" name="username" value="{{ username }}">
            <button type="submit" id="regenBtn" class="hidden">Yeni Kod Oluştur</button>
        </form>

        <script>
        function copyCode() {
            const code = "{{ reset_code }}";
            const helper = document.getElementById("copyHelper");
            navigator.clipboard.writeText(code).then(function() {
                if (helper) helper.innerText = "Kod kopyalandı.";
            }).catch(function() {
                if (helper) helper.innerText = "Kopyalama başarısız. Kodu elle kopyala.";
            });
        }

        let expires = {{ expires_at | default(0) }};
        let expiredShown = false;

        function updateTimer() {
            let now = Math.floor(Date.now() / 1000);
            let remaining = expires - now;
            const timer = document.getElementById("timer");
            const regenBtn = document.getElementById("regenBtn");

            if (!timer) return;

            if (remaining <= 0) {
                timer.innerText = "Kod süresi doldu. Yeni kod oluştur.";
                if (regenBtn) {
                    regenBtn.classList.remove("hidden");
                    regenBtn.innerText = "Yeni Kod Oluştur";
                }
                return;
            }

            let min = Math.floor(remaining / 60);
            let sec = remaining % 60;
            if (sec < 10) sec = "0" + sec;

            timer.innerText = "Kalan süre: " + min + " dk " + sec + " sn";
        }

        setInterval(updateTimer, 1000);
        updateTimer();
        </script>
        {% endif %}
    </div>
</div>
</body>
</html>
"""

forgot_path.write_text(forgot_html, encoding="utf-8")
print("OK: 3 dakika süre, 30 saniye bekleme limiti ve yeni kod akışı eklendi.")
