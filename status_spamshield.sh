#!/data/data/com.termux/files/usr/bin/bash
cd ~/spamshield_release || exit 1
echo "=== Çalışan daemon ==="
pgrep -af spamshield_daemon.py || echo "Çalışmıyor"
echo ""
echo "=== Son log ==="
tail -n 15 logs/spamshield_daemon.log 2>/dev/null || echo "Log yok"
