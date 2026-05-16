#!/data/data/com.termux/files/usr/bin/bash
cd ~/spamshield_release || exit 1
mkdir -p logs

# Daemon başlat
nohup python spamshield_daemon.py > logs/daemon.out 2>&1 &
echo $! > logs/daemon.pid

# Web sunucusu başlat
nohup python3 -c "from dashboard_web import app; app.run(host='0.0.0.0', port=8080)" > logs/web.out 2>&1 &
echo $! > logs/web.pid

echo "✅ EratGuard arka planda başladı"
echo "Daemon PID : $(cat logs/daemon.pid)"
echo "Web PID    : $(cat logs/web.pid)"
echo "URL        : http://127.0.0.1:8080"
