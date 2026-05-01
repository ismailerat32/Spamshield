import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "spamshield_daemon.log"
INTERVAL = 60  # saniye

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

log("SpamShield daemon başladı")

while True:
    try:
        r = subprocess.run(
            ["python", "sms_ai_reader.py"],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=45
        )

        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()

        if out and "0 yeni SMS" not in out:
            log(out)

        if err:
            log("ERR: " + err)

        if r.returncode != 0:
            log(f"sms_ai_reader çıkış kodu: {r.returncode}")

    except KeyboardInterrupt:
        log("Daemon manuel durduruldu")
        break

    except Exception as e:
        log("Daemon hata: " + str(e))

    time.sleep(INTERVAL)
