# 🚀 SpamShield

Akıllı SMS spam analiz ve filtreleme sistemi.

## 📌 Özellikler

- 🔍 Gerçek zamanlı SMS izleme (Termux)
- 🤖 Makine öğrenmesi ile spam tespiti
- 🌐 Web dashboard (Flask)
- 👤 Kullanıcı sistemi (admin / user)
- 🔐 Şifreli giriş
- 🌍 Çoklu dil desteği (TR / EN)
- ⚠️ Watchlist (şüpheli takip)
- ⛔ Blocklist (otomatik engelleme)
- 📊 Mesaj analizi ve skor sistemi

---

## 🧠 Nasıl Çalışır?

SpamShield gelen SMS’leri analiz eder:

1. SMS okunur (Termux API)
2. ML modeli ile analiz edilir
3. Skor hesaplanır
4. Sonuç:
   - TEMİZ
   - ŞÜPHELİ
   - SPAM
5. Dashboard’a yansıtılır

---

## ⚙️ Kurulum

```bash
git clone https://github.com/ismailerat32/Spamshield.git
cd Spamshield
pip install -r requirements.txt
