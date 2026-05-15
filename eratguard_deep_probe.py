#!/usr/bin/env python3
import getpass
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

BASE_URL = "https://spamshield-peld.onrender.com"
TIMEOUT = 20
MAX_DEPTH = 2
MAX_PAGES = 120

SKIP_WORDS = [
    "logout", "delete", "remove", "drop", "wipe", "clear", "purge",
    "revoke", "ban", "approve", "reject", "deactivate", "download",
    "export", "reset-token"
]

ERROR_WORDS = [
    "Traceback",
    "Internal Server Error",
    "TemplateNotFound",
    "BuildError",
    "UndefinedError",
    "jinja2.exceptions",
    "werkzeug.exceptions",
    "500 Internal",
    "Not Found",
    "Admin girişi başarısız",
    "Giriş başarısız",
    "Login failed"
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "a" and d.get("href"):
            self.links.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()

class Client:
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )

    def abs(self, path):
        return urllib.parse.urljoin(BASE_URL + "/", path)

    def request(self, method, path, data=None):
        url = self.abs(path)
        body = None
        headers = {"User-Agent": "EratGuardDeepProbe/1.0"}

        if data is not None:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        started = time.time()
        try:
            r = self.opener.open(req, timeout=TIMEOUT)
            text = r.read().decode("utf-8", errors="replace")
            return {
                "url": url,
                "final_url": r.geturl(),
                "status": r.getcode(),
                "elapsed": round(time.time() - started, 3),
                "text": text,
                "error": ""
            }
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="replace")
            return {
                "url": url,
                "final_url": e.geturl(),
                "status": e.code,
                "elapsed": round(time.time() - started, 3),
                "text": text,
                "error": str(e)
            }
        except Exception as e:
            return {
                "url": url,
                "final_url": url,
                "status": 0,
                "elapsed": round(time.time() - started, 3),
                "text": "",
                "error": repr(e)
            }

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, data):
        return self.request("POST", path, data)

    def cookie_names(self):
        return [c.name for c in self.cookies]

def parse_page(text):
    p = LinkParser()
    try:
        p.feed(text or "")
    except Exception:
        pass
    errors = [w for w in ERROR_WORDS if w.lower() in (text or "").lower()]
    return p, errors

def should_skip(url):
    low = url.lower()
    return any(w in low for w in SKIP_WORDS)

def same_host(url):
    base = urllib.parse.urlparse(BASE_URL)
    u = urllib.parse.urlparse(url)
    return u.netloc == "" or u.netloc == base.netloc

def make_record(area, source, res):
    parser, errors = parse_page(res["text"])
    return {
        "area": area,
        "source": source,
        "url": res["url"],
        "final_url": res["final_url"],
        "status": res["status"],
        "elapsed": res["elapsed"],
        "title": parser.title[:120],
        "size": len(res["text"] or ""),
        "errors_found": errors,
        "request_error": res["error"]
    }

def crawl(area, client, starts):
    visited = set()
    queue = [(s, 0, "seed") for s in starts]
    records = []

    while queue and len(records) < MAX_PAGES:
        path, depth, source = queue.pop(0)
        full = client.abs(path)

        if full in visited:
            continue
        if not same_host(full):
            continue
        if should_skip(full):
            continue

        visited.add(full)
        res = client.get(path)
        rec = make_record(area, source, res)
        records.append(rec)

        parser, _ = parse_page(res["text"])

        if depth < MAX_DEPTH and res["status"] == 200:
            for href in parser.links:
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue
                if href.startswith("mailto:") or href.startswith("tel:"):
                    continue

                next_url = urllib.parse.urljoin(res["final_url"], href).split("#")[0]
                if not same_host(next_url):
                    continue
                if should_skip(next_url):
                    continue

                parsed = urllib.parse.urlparse(next_url)
                clean = parsed.path or "/"
                if parsed.query:
                    clean += "?" + parsed.query

                if client.abs(clean) not in visited:
                    queue.append((clean, depth + 1, res["final_url"]))

    return records

def summarize(records):
    counts = {}
    bad = []
    warnings = []

    for r in records:
        counts[str(r["status"])] = counts.get(str(r["status"]), 0) + 1

        if r["status"] == 0 or r["status"] >= 400:
            bad.append(r)

        if r["errors_found"]:
            warnings.append(r)

    return {
        "total": len(records),
        "status_counts": counts,
        "bad": bad,
        "warnings": warnings
    }

def recommendations(admin_success, user_success, admin_sum, user_sum):
    recs = []

    if not admin_success:
        recs.append(("P0", "Admin Login", "Admin giriş/session final öncesi kesin düzeltilmeli."))

    if not user_success:
        recs.append(("P0", "User Login", "Gerçek kullanıcı hesabı ile giriş ve ana sayfa akışı doğrulanmalı."))

    if admin_sum["bad"]:
        recs.append(("P0", "Admin Pages", f"{len(admin_sum['bad'])} admin sayfası 4xx/5xx verdi; final öncesi düzeltilmeli."))

    if user_sum["bad"]:
        recs.append(("P0", "User Pages", f"{len(user_sum['bad'])} kullanıcı/public sayfası 4xx/5xx verdi; kullanıcı güveni için düzeltilmeli."))

    if admin_sum["warnings"]:
        recs.append(("P1", "Admin Warnings", f"{len(admin_sum['warnings'])} admin sayfasında hata benzeri metin bulundu; incelenmeli."))

    if user_sum["warnings"]:
        recs.append(("P1", "User Warnings", f"{len(user_sum['warnings'])} kullanıcı sayfasında hata benzeri metin bulundu; beta duyurusu öncesi incelenmeli."))

    recs.append(("P1", "APK", "Final v1.0.0 öncesi debug APK yerine imzalı release APK hazırlanmalı."))
    recs.append(("P1", "Branding", "SpamShield görünen kalıntıları APK, splash, poster, README ve sayfalardan temizlenmeli."))
    recs.append(("P1", "Security", ".env, keystore, token, kullanıcı verisi ve lisans dosyaları tekrar kontrol edilmeli."))
    recs.append(("P2", "UI/UX", "Admin radial menü çalışıyor; kullanıcı radial/pizza menü final yönüne göre geri alınmalı."))
    recs.append(("P2", "README", "README EratGuard PRO beta stratejisine göre güncellenmeli."))
    recs.append(("P2", "Social", "Paylaşımlarda 'v1.0.0-beta yayında' denmeli; final/stable ifadesi kullanılmamalı."))

    if admin_success and user_success and not admin_sum["bad"] and not user_sum["bad"]:
        recs.insert(0, ("OK", "Beta Readiness", "Kontrollü beta duyurusu için ana akışlar makul görünüyor; finali ertelemek doğru."))

    return recs

def md_list(items):
    if not items:
        return "- Yok\n"
    out = ""
    for r in items[:100]:
        out += f"- `{r['status']}` {r['final_url']} | {r['title']} | errors: {', '.join(r['errors_found']) or r['request_error']}\n"
    return out

def main():
    print("=== EratGuard PRO Deep Probe ===")
    print("Şifreler ekranda görünmez.")

    admin_user = input("Admin kullanıcı adı [admin]: ").strip() or "admin"
    admin_pass = getpass.getpass("Admin şifresi: ")

    user_name = input("Kullanıcı adı: ").strip()
    user_pass = getpass.getpass("Kullanıcı şifresi: ")

    health_client = Client()
    health = health_client.get("/health")
    print("\nHealth:", health["status"], health["text"][:120].replace("\n", " "))

    admin_client = Client()
    admin_login = admin_client.post("/ss-admin-access", {
        "username": admin_user,
        "password": admin_pass
    })
    admin_dash = admin_client.get("/admin/dashboard")

    admin_success = (
        admin_dash["status"] == 200
        and "/ss-admin-access" not in admin_dash["final_url"]
        and "Admin girişi başarısız" not in admin_dash["text"]
    )

    print("\nAdmin login POST:", admin_login["status"], admin_login["final_url"])
    print("Admin dashboard:", admin_dash["status"], admin_dash["final_url"])
    print("Admin cookies:", admin_client.cookie_names())
    print("Admin success:", admin_success)

    admin_starts = [
        "/admin", "/admin/dashboard", "/admin/panel", "/admin/licenses",
        "/admin/payment-requests", "/admin/spam-logs", "/admin/overview",
        "/admin/whitelist", "/admin/settings", "/admin/system"
    ]
    admin_records = crawl("admin", admin_client, admin_starts)
    admin_sum = summarize(admin_records)

    user_client = Client()
    user_login = user_client.post("/login", {
        "username": user_name,
        "password": user_pass
    })
    user_home = user_client.get("/app-start")

    user_success = (
        user_home["status"] == 200
        and "Giriş başarısız" not in user_home["text"]
        and "login failed" not in user_home["text"].lower()
    )

    print("\nUser login POST:", user_login["status"], user_login["final_url"])
    print("User app-start:", user_home["status"], user_home["final_url"])
    print("User cookies:", user_client.cookie_names())
    print("User success probable:", user_success)

    user_starts = [
        "/", "/app-start", "/u", "/u/home", "/u/protection",
        "/u/analysis", "/u/blocked", "/u/reports", "/u/notifications",
        "/u/settings", "/u/license", "/u/community",
        "/pricing", "/legal", "/terms", "/privacy", "/contact"
    ]
    user_records = crawl("user", user_client, user_starts)
    user_sum = summarize(user_records)

    recs = recommendations(admin_success, user_success, admin_sum, user_sum)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = Path(f"ERATGUARD_DEEP_PROBE_{stamp}.json")
    md_path = Path(f"ERATGUARD_DEEP_PROBE_{stamp}.md")

    report = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "base_url": BASE_URL,
        "summary": {
            "admin_login_success": admin_success,
            "user_login_probable_success": user_success,
            "admin_pages_tested": admin_sum["total"],
            "user_pages_tested": user_sum["total"],
            "admin_status_counts": admin_sum["status_counts"],
            "user_status_counts": user_sum["status_counts"],
            "admin_bad_pages": len(admin_sum["bad"]),
            "user_bad_pages": len(user_sum["bad"]),
            "admin_warning_pages": len(admin_sum["warnings"]),
            "user_warning_pages": len(user_sum["warnings"]),
            "recommendations_count": len(recs)
        },
        "admin_records": admin_records,
        "user_records": user_records,
        "recommendations": [
            {"priority": p, "area": a, "recommendation": r}
            for p, a, r in recs
        ]
    }

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# EratGuard PRO Deep Probe Report\n\n")
    md.append(f"- Date: {report['created_at']}\n")
    md.append(f"- Base URL: {BASE_URL}\n")
    md.append(f"- Admin login success: `{admin_success}`\n")
    md.append(f"- User login probable success: `{user_success}`\n\n")

    md.append("## Summary\n```json\n")
    md.append(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    md.append("\n```\n\n")

    md.append("## Recommendations\n")
    for p, a, r in recs:
        md.append(f"### {p} — {a}\n- {r}\n\n")

    md.append("## Admin bad pages\n")
    md.append(md_list(admin_sum["bad"]))
    md.append("\n## Admin warning pages\n")
    md.append(md_list(admin_sum["warnings"]))
    md.append("\n## User bad pages\n")
    md.append(md_list(user_sum["bad"]))
    md.append("\n## User warning pages\n")
    md.append(md_list(user_sum["warnings"]))

    md_path.write_text("".join(md), encoding="utf-8")

    print("\n=== FINAL SUMMARY ===")
    print("Admin pages tested:", admin_sum["total"])
    print("User pages tested:", user_sum["total"])
    print("Admin bad pages:", len(admin_sum["bad"]))
    print("User bad pages:", len(user_sum["bad"]))
    print("Admin warning pages:", len(admin_sum["warnings"]))
    print("User warning pages:", len(user_sum["warnings"]))
    print("Recommendations:", len(recs))

    print("\n=== TOP RECOMMENDATIONS ===")
    for p, a, r in recs[:12]:
        print(f"[{p}] {a}: {r}")

    print("\nJSON report:", json_path)
    print("Markdown report:", md_path)

    if admin_sum["bad"] or user_sum["bad"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
