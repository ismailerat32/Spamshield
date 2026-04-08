from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

if "def license_required" in text:
    print("Zaten ekli")
    exit()

block = '''

def license_required():
    from datetime import datetime

    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    users = load_users()
    if username not in users:
        return redirect(url_for("login"))

    user = users[username]
    expiry = user.get("license_expiry", "")

    if not expiry:
        return redirect(url_for("activate_license"))

    try:
        exp_date = datetime.strptime(expiry, "%Y-%m-%d")
        if exp_date < datetime.utcnow():
            return redirect(url_for("activate_license"))
    except:
        return redirect(url_for("activate_license"))

    return None
'''

text = block + text

text = text.replace(
    'def dashboard():',
    '''def dashboard():
    lock = license_required()
    if lock:
        return lock
'''
)

p.write_text(text, encoding="utf-8")
print("OK: Paywall eklendi")
