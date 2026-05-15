#!/usr/bin/env python3
import urllib.request, urllib.error, urllib.parse, json
from pathlib import Path
from datetime import datetime

BASE = "https://spamshield-peld.onrender.com"

PATHS = [
    "/", "/health", "/app-start", "/login", "/forgot-password",
    "/ss-admin-access", "/admin/dashboard",
    "/u", "/u/home", "/u/protection", "/u/analysis", "/u/blocked",
    "/u/reports", "/u/notifications", "/u/settings", "/u/license",
    "/u/community", "/u/legal", "/privacy", "/terms", "/legal", "/forgot"
]

SENSITIVE_PATHS = [
    "/.env", "/config.json", "/spamshield.db", "/cookies.txt",
    "/data/users.json", "/data/reset_tokens.json",
    "/data/generated_licenses.json", "/data/payment_requests.json",
    "/data/user_quarantine.json", "/data/user_titanium_events.json",
    "/.git/config", "/.git/HEAD", "/logs", "/flask.log", "/ss_server.log",
    "/android_webview_wrapper/keystore/spamshield-release-key.jks"
]

SEC_HEADERS = [
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "Referrer-Policy",
    "Permissions-Policy"
]

RISK_TEXTS = [
    "Traceback", "Internal Server Error", "TemplateNotFound",
    "jinja2.exceptions", "werkzeug", "SECRET_KEY",
    "ADMIN_PASSWORD", "SMTP_PASS", "password_hash", "reset_tokens"
]

def fetch(path):
    url = urllib.parse.urljoin(BASE, path)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "EratGuardSecurityProbe/1.0"},
        method="GET"
    )
    try:
        r = urllib.request.urlopen(req, timeout=20)
        body = r.read().decode("utf-8", errors="replace")
        return {
            "path": path,
            "status": r.getcode(),
            "final_url": r.geturl(),
            "headers": dict(r.headers),
            "body": body[:1200],
            "error": ""
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {
            "path": path,
            "status": e.code,
            "final_url": e.geturl(),
            "headers": dict(e.headers),
            "body": body[:1200],
            "error": str(e)
        }
    except Exception as e:
        return {
            "path": path,
            "status": 0,
            "final_url": url,
            "headers": {},
            "body": "",
            "error": repr(e)
        }

findings = []
results = []

print("=== ERATGUARD SECURITY PROBE ===")
print("Target:", BASE)
print("Mode: defensive / non-destructive")

print("\n=== ROUTES ===")
for p in PATHS:
    r = fetch(p)
    results.append(r)
    print(f"{r['status']:>3} {p} -> {r['final_url']}")
    risks = [x for x in RISK_TEXTS if x.lower() in r["body"].lower()]
    if r["status"] >= 500 or risks:
        findings.append({
            "priority": "P0" if r["status"] >= 500 else "P1",
            "area": "Route",
            "path": p,
            "finding": f"status={r['status']} risks={risks}",
            "recommendation": "Sayfada internal hata, traceback veya secret benzeri metin görünmemeli."
        })

print("\n=== SENSITIVE PATHS ===")
for p in SENSITIVE_PATHS:
    r = fetch(p)
    results.append(r)
    print(f"{r['status']:>3} {p}")
    if r["status"] == 200:
        findings.append({
            "priority": "P0",
            "area": "Sensitive Exposure",
            "path": p,
            "finding": "Sensitive path returned HTTP 200",
            "recommendation": "Bu dosya public erişime kapatılmalı."
        })

print("\n=== SECURITY HEADERS ===")
root = fetch("/")
headers_lower = {k.lower(): v for k, v in root["headers"].items()}
for h in SEC_HEADERS:
    if h.lower() in headers_lower:
        print("OK:", h)
    else:
        print("MISSING:", h)
        findings.append({
            "priority": "P2",
            "area": "Security Header",
            "path": "/",
            "finding": f"Missing {h}",
            "recommendation": "Final öncesi güvenlik header olarak eklenmeli."
        })

findings.extend([
    {
        "priority": "P1",
        "area": "Admin Brute Force",
        "path": "/ss-admin-access",
        "finding": "Admin giriş endpoint’i kritik.",
        "recommendation": "IP/session bazlı deneme limiti ve geçici kilitleme eklenmeli."
    },
    {
        "priority": "P1",
        "area": "User Login",
        "path": "/login",
        "finding": "Kullanıcı login endpoint’i korunmalı.",
        "recommendation": "Login denemeleri rate limit ile sınırlandırılmalı."
    },
    {
        "priority": "P1",
        "area": "Forgot Password",
        "path": "/forgot-password",
        "finding": "Şifre sıfırlama endpoint’i abuse edilebilir.",
        "recommendation": "Rate limit, token süresi ve tek kullanımlık token doğrulanmalı."
    },
    {
        "priority": "P1",
        "area": "Monitoring",
        "path": "logs",
        "finding": "Beta sonrası giriş/hata olayları izlenmeli.",
        "recommendation": "Başarısız login, 500 hata ve şüpheli istekler loglanmalı."
    }
])

summary = {
    "routes_checked": len(PATHS),
    "sensitive_paths_checked": len(SENSITIVE_PATHS),
    "findings_count": len(findings),
    "p0": sum(1 for f in findings if f["priority"] == "P0"),
    "p1": sum(1 for f in findings if f["priority"] == "P1"),
    "p2": sum(1 for f in findings if f["priority"] == "P2")
}

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

json_file = Path(f"ERATGUARD_SECURITY_PROBE_{stamp}.json")
md_file = Path(f"ERATGUARD_SECURITY_PROBE_{stamp}.md")

json_file.write_text(json.dumps({
    "created_at": datetime.now().isoformat(),
    "base": BASE,
    "summary": summary,
    "findings": findings,
    "results": results
}, ensure_ascii=False, indent=2), encoding="utf-8")

md = []
md.append("# EratGuard Security Probe\n\n")
md.append(f"- Target: {BASE}\n")
md.append("- Mode: Defensive / non-destructive\n\n")
md.append("## Summary\n```json\n")
md.append(json.dumps(summary, ensure_ascii=False, indent=2))
md.append("\n```\n\n")
md.append("## Findings\n")
for f in findings:
    md.append(f"### {f['priority']} — {f['area']}\n")
    md.append(f"- Path: `{f['path']}`\n")
    md.append(f"- Finding: {f['finding']}\n")
    md.append(f"- Recommendation: {f['recommendation']}\n\n")

md_file.write_text("".join(md), encoding="utf-8")

print("\n=== SUMMARY ===")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\nJSON report:", json_file)
print("Markdown report:", md_file)

if summary["p0"] > 0:
    raise SystemExit(2)
