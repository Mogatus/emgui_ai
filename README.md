# Energie-Monitor

PyQt6-basierte Desktop-GUI zur Visualisierung von Stromdaten aus einer **Neon-PostgreSQL**-Datenbank.

## Features

- **Dashboard** mit Live-KPI-Karten (Verbrauch, PV, Einspeisung, Netzbezug, Autarkie)
- **Linienchart** für den zeitlichen Energieverlauf
- **Balkendiagramm** mit Tagesübersicht in kWh
- **Tabellenansicht** – sortierbar, filterbar
- Dark-Theme UI
- Asynchrone Datenbankabfragen (UI bleibt responsiv)

## Voraussetzungen

- Python 3.11+
- Neon-PostgreSQL-Datenbank mit Tabelle `meter_data`

## Installation

```bash
# Virtualenv erstellen
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Konfiguration

Erstelle eine `.env`-Datei im Projektverzeichnis (Vorlage: `.env.example`):

```
DB_HOST=ep-xxxxx.eu-central-1.aws.neon.tech
DB_PORT=5432
DB_NAME=neondb
DB_USER=your_user
DB_PASSWORD=your_password
DB_SSLMODE=require
```

## Starten

```bash
python main.py
```

## Datenbank-Schema

| Spalte          | Typ              | Beschreibung              |
|-----------------|------------------|---------------------------|
| id              | integer (PK)     | Auto-Increment            |
| loadval         | integer          | Verbrauch in Watt         |
| pv              | integer          | PV-Erzeugung in Watt     |
| grid_feed_in    | integer          | Einspeisung in Watt       |
| grid_purchase   | integer          | Netzbezug in Watt         |
| savetimestamp   | varchar          | Zeitstempel               |

## Tastenkürzel

| Kürzel   | Aktion           |
|----------|------------------|
| F5       | Daten neu laden  |
| Ctrl+Q   | Beenden          |
