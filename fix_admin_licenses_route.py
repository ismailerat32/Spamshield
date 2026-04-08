from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

new_func = '''@app.route("/admin/licenses", methods=["GET", "POST"])
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

    return render_template(
        "admin_licenses.html",
        users=users,
        licenses=licenses
    )'''

pattern = r'@app\.route\("/admin/licenses", methods=\["GET", "POST"\]\)\ndef admin_licenses\(\):.*?(?=^@app\.route\(|^if __name__ == "__main__":|\Z)'
m = re.search(pattern, text, flags=re.S | re.M)

if not m:
    print("HATA: admin_licenses route bulunamadı.")
    raise SystemExit(1)

text = re.sub(pattern, new_func + "\n\n", text, count=1, flags=re.S | re.M)

p.write_text(text, encoding="utf-8")
print("OK: admin_licenses route düzeltildi.")
