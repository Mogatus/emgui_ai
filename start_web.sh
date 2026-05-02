#!/bin/bash
# Energie-Monitor Web App – Start script for Raspberry Pi
cd "$(dirname "$0")/emgui_web"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Erstelle virtuelle Umgebung..."
    python3 -m venv venv
    echo "Installiere Abhängigkeiten..."
    venv/bin/pip install --upgrade pip
    venv/bin/pip install flask psycopg2-binary python-dotenv
fi

echo "Starte Energie-Monitor Web App auf Port 5000..."
venv/bin/python web_app.py
