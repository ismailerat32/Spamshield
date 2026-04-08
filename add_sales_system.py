from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

if 'PAYMENT_REQUESTS_FILE = "data/payment_requests.json"' in text:
    print("Satış sistemi zaten ekli.")
    raise SystemExit(0)

block = '''
PAYMENT_REQUESTS_FILE = "data/payment_requests.json"

def load_payment_requests():
    import json
    import os
    if not os.path.exists(PAYMENT_REQUESTS_FILE):
        with open(PAYMENT_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    try:
        with open(PAYMENT_REQUESTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_payment_requests(data):
    import json
    with open(PAYMENT_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/pricing")
def pricing():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("pricing.html")

@app.route("/buy-license", methods=["GET", "POST"])
def buy_license():
    from datetime import datetime

    if not login_required():
        return redirect(url_for("login"))

    username = session.get("username", "")

    if request.method == "POST":
        plan = request.form.get("plan", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        note = request.form.get("note", "").strip()

        if not plan:
            return render_template("buy_license.html", error="Paket seçmelisin")

        requests_data = load_payment_requests()
        requests_data.insert(0, {
            "username": username,
            "plan": plan,
            "payment_method": payment_method or "manuel",
            "note": note,
            "status": "pending",
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_payment_requests(requests_data)

        return render_template(
            "buy_license.html",
            success="Talebin alındı. Ödeme kontrolünden sonra lisansın tanımlanacak."
        )

    return render_template("buy_license.html")

@app.route("/admin/payment-requests")
def admin_payment_requests():
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("dashboard"))

    requests_data = load_payment_requests()
    return render_template("admin_payment_requests.html", requests=requests_data)
'''

insert_before = 'if __name__ == "__main__":'
if insert_before in text:
    text = text.replace(insert_before, block + "\n\n" + insert_before, 1)
else:
    text += "\n" + block + "\n"

p.write_text(text, encoding="utf-8")
print("OK: satış sistemi route'ları eklendi.")
