#!/data/data/com.termux/files/usr/bin/bash
cd ~/spamshield_release || exit 1
if [ -f logs/daemon.pid ]; then
  kill "$(cat logs/daemon.pid)" 2>/dev/null
  rm -f logs/daemon.pid
  echo "🛑 SpamShield durduruldu"
else
  pkill -f spamshield_daemon.py 2>/dev/null
  echo "🛑 Process temizlendi"
fi
