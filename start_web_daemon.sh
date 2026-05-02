#!/bin/bash
# Energie-Monitor Web App – als Hintergrund-Dienst starten (überlebt Logout)
# Usage: ./start_web_daemon.sh [stop|status|restart]

APP_DIR="$(dirname "$0")/emgui_web"
PIDFILE="/tmp/emgui_web.pid"
LOGFILE="/tmp/emgui_web.log"

start() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Energie-Monitor läuft bereits (PID $(cat "$PIDFILE"))"
        echo "Log: $LOGFILE"
        return
    fi

    # Create venv if needed
    if [ ! -d "$APP_DIR/venv" ]; then
        echo "Erstelle virtuelle Umgebung..."
        python3 -m venv "$APP_DIR/venv"
        "$APP_DIR/venv/bin/pip" install --upgrade pip
        "$APP_DIR/venv/bin/pip" install flask psycopg2-binary python-dotenv
    fi

    echo "Starte Energie-Monitor Web App im Hintergrund..."
    nohup "$APP_DIR/venv/bin/python" "$APP_DIR/web_app.py" > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "Gestartet (PID $(cat "$PIDFILE"))"
    echo "Log: $LOGFILE"
    echo "URL: http://$(hostname -I | awk '{print $1}'):5000"
}

stop() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm -f "$PIDFILE"
            echo "Gestoppt (PID $PID)"
        else
            rm -f "$PIDFILE"
            echo "Prozess lief nicht mehr."
        fi
    else
        echo "Kein laufender Prozess gefunden."
    fi
}

status() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Energie-Monitor läuft (PID $(cat "$PIDFILE"))"
    else
        echo "Energie-Monitor läuft nicht."
    fi
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 1; start ;;
    status)  status ;;
    *)       echo "Usage: $0 {start|stop|restart|status}" ;;
esac
