import requests
import json
from datetime import datetime

BASE = "http://127.0.0.1:8080"
RESULTS = []

def log(section, status, detail=""):
    icon = "✅" if status else "❌"
    msg = f"{icon} [{section}] {detail}"
    print(msg)
    RESULTS.append({"section": section, "status": status, "detail": detail})

def test_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

# ── KULLANICI TARAFI ──
test_section("KULLANICI TARAFI TESTİ")

s = requests.Session()

# 1. Splash
try:
    r = s.get(f"{BASE}/app-start", timeout=15)
    log("Splash", r.status_code == 200, f"HTTP {r.status_code} | {len(r.text)} byte")
except Exception as e:
    log("Splash", False, str(e))

# 2. Login sayfası
try:
    r = s.get(f"{BASE}/login", timeout=15)
    log("Login Sayfası", r.status_code == 200, f"HTTP {r.status_code}")
except Exception as e:
    log("Login Sayfası", False, str(e))

# 3. Login işlemi
try:
    r = s.post(f"{BASE}/login", data={
        "username": "playtest32",
        "password": "test123"
    }, timeout=5, allow_redirects=True)
    logged_in = "koruma" in r.text.lower() or "eratguard" in r.text.lower() or "modül" in r.text.lower()
    log("Login İşlemi", logged_in, f"HTTP {r.status_code} | Giriş {'başarılı' if logged_in else 'başarısız'}")
except Exception as e:
    log("Login İşlemi", False, str(e))

# 4. Ana sayfa
try:
    r = s.get(f"{BASE}/radial", timeout=15)
    log("Ana Sayfa /radial", r.status_code == 200, f"HTTP {r.status_code} | {len(r.text)} byte")
except Exception as e:
    log("Ana Sayfa", False, str(e))

# 5. Modül sayfaları
modules = [
    ("/u/protection", "Koruma"),
    ("/u/analysis", "Analiz"),
    ("/u/blocked", "Engellenenler"),
    ("/u/reports", "Raporlar"),
    ("/u/notifications", "Bildirimler"),
    ("/u/settings", "Ayarlar"),
    ("/u/community", "Topluluk"),
    ("/u/license", "Lisans"),
]

for path, name in modules:
    try:
        r = s.get(f"{BASE}{path}", timeout=15)
        ok = r.status_code == 200
        log(f"Modül: {name}", ok, f"HTTP {r.status_code} | {len(r.text)} byte")
    except Exception as e:
        log(f"Modül: {name}", False, str(e))

# 6. Spam bildirimi
try:
    r = s.post(f"{BASE}/u/community/spam_report",
        json={"number": "05551234567", "body": "Tebrikler 1000 TL kazandınız!"},
        timeout=15)
    ok = r.status_code == 200
    log("Spam Bildirimi", ok, f"HTTP {r.status_code} | {r.text[:80]}")
except Exception as e:
    log("Spam Bildirimi", False, str(e))

# ── ADMİN TARAFI ──
test_section("ADMİN TARAFI TESTİ")

sa = requests.Session()

# 7. Admin login sayfası
try:
    r = sa.get(f"{BASE}/ss-admin-access", timeout=15)
    log("Admin Login Sayfası", r.status_code == 200, f"HTTP {r.status_code}")
except Exception as e:
    log("Admin Login Sayfası", False, str(e))

# 8. Admin giriş
try:
    r = sa.post(f"{BASE}/ss-admin-access", data={
        "username": "admin",
        "password": "admin123"
    }, timeout=5, allow_redirects=True)
    logged_in = "admin" in r.text.lower() or "kullanıcı" in r.text.lower() or "lisans" in r.text.lower()
    log("Admin Login", logged_in, f"HTTP {r.status_code} | Giriş {'başarılı' if logged_in else 'başarısız'}")
except Exception as e:
    log("Admin Login", False, str(e))

# 9. Admin paneli
try:
    r = sa.get(f"{BASE}/admin/dashboard", timeout=15)
    log("Admin Dashboard", r.status_code == 200, f"HTTP {r.status_code} | {len(r.text)} byte")
except Exception as e:
    log("Admin Dashboard", False, str(e))

# 10. Admin sayfaları
admin_pages = [
    ("/admin/users", "Kullanıcılar"),
    ("/admin/licenses", "Lisanslar"),
    ("/admin/payments", "Ödemeler"),
    ("/admin/spam-logs", "Spam Logları"),
    ("/admin/settings", "Ayarlar"),
]

for path, name in admin_pages:
    try:
        r = sa.get(f"{BASE}{path}", timeout=15)
        ok = r.status_code == 200
        log(f"Admin: {name}", ok, f"HTTP {r.status_code}")
    except Exception as e:
        log(f"Admin: {name}", False, str(e))

# ── ÖZET ──
test_section("TEST ÖZETI")
total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["status"])
failed = total - passed

print(f"\n📊 Toplam Test : {total}")
print(f"✅ Başarılı    : {passed}")
print(f"❌ Başarısız   : {failed}")
print(f"📈 Başarı Oranı: %{int(passed/total*100)}")
print(f"\n⏰ Test Zamanı : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if failed > 0:
    print("\n❌ Başarısız testler:")
    for r in RESULTS:
        if not r["status"]:
            print(f"   - {r['section']}: {r['detail']}")
