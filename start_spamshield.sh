#!/data/data/com.termux/files/usr/bin/bash
cd ~/spamshield_release || exit 1
mkdir -p logs
nohup python spamshield_daemon.py > logs/daemon.out 2>&1 &
echo $! > logs/daemon.pid
echo "✅ SpamShield arka planda başladı"
echo "PID: $(cat logs/daemon.pid)"
