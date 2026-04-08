from pathlib import Path

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = 'app.run(host="0.0.0.0", port=5000, debug=True)'

new = '''import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)'''

if old in text:
    text = text.replace(old, new)
else:
    print("app.run satırı farklı, manuel kontrol et")

p.write_text(text, encoding="utf-8")
print("OK: Render port fix uygulandı")
