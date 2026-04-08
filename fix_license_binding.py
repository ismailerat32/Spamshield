from pathlib import Path
import re

p = Path("app.py")
text = p.read_text(encoding="utf-8")

old = 'licenses[license_key] = {'
if old not in text:
    print("HATA: lisans oluşturma bloğu bulunamadı")
    exit()

text = text.replace(
    'licenses[license_key] = {',
    '''licenses[license_key] = {
            "username": username,''')

p.write_text(text, encoding="utf-8")
print("OK: Lisans artık kullanıcıya bağlanacak")
