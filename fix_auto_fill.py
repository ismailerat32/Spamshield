from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = '''username = request.form.get("username", "").strip()
        code = request.form.get("code", "").strip()'''

new = '''username = request.form.get("username") or request.args.get("username", "")
        code = request.form.get("code") or request.args.get("code", "")

        username = username.strip()
        code = code.strip()'''

if old not in text:
    print("HATA: Kod bulunamadı!")
    exit()

text = text.replace(old, new, 1)
p.write_text(text, encoding="utf-8")

print("OK: Otomatik doldurma backend eklendi.")
